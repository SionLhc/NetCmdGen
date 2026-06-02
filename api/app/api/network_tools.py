"""网络诊断工具 API — Ping / 端口扫描 / Traceroute / DNS 查询"""
from __future__ import annotations

import re
import socket
import struct

try:
    import dns.resolver
    import dns.rdatatype
    _DNS_AVAILABLE = True
except ImportError:
    _DNS_AVAILABLE = False
import time
import random
import subprocess
import platform
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/net", tags=["网络工具"])

# ─── 通用端口服务识别表 ─────────────────────────────────
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
    993: "IMAPS", 995: "POP3S", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 6379: "Redis", 8080: "HTTP-Alt",
    8443: "HTTPS-Alt", 9090: "Web-Admin", 161: "SNMP",
    162: "SNMP-Trap", 123: "NTP", 389: "LDAP", 636: "LDAPS",
}


def _ping_once(host: str, timeout: float = 2.0) -> Optional[float]:
    """单次 ICMP Ping，返回 RTT（毫秒），超时返回 None。

    优先使用系统 ping 命令（兼容性最好）。
    """
    system = platform.system()
    try:
        if system == "Windows":
            cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
        else:
            cmd = ["ping", "-c", "1", "-W", str(int(timeout)), host]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout + 1,
        )
        if result.returncode == 0:
            # 从输出中提取 time=XXms
            import re
            if system == "Windows":
                match = re.search(r"时间[=<]\s*(\d+)\s*ms", result.stdout)
                if not match:
                    match = re.search(r"time[=<]\s*(\d+)\s*ms", result.stdout)
            else:
                match = re.search(r"time[=<]\s*(\d+\.?\d*)\s*ms", result.stdout)
            if match:
                return float(match.group(1))
        return None
    except Exception:
        return None


def _port_description(port: int, service: str) -> str:
    """生成端口描述信息"""
    desc_map = {
        22: "Secure Shell (SSH) — 加密远程管理，强烈建议修改默认端口",
        23: "Telnet — 明文远程管理，⚠ 不安全，建议禁用改用 SSH",
        25: "SMTP — 邮件发送协议",
        53: "DNS — 域名解析服务",
        80: "HTTP — Web 服务，建议跳转 HTTPS",
        110: "POP3 — 邮件接收协议",
        123: "NTP — 网络时间同步",
        143: "IMAP — 邮件接收协议(新版)",
        161: "SNMP — 网络设备监控管理",
        389: "LDAP — 目录访问协议",
        443: "HTTPS — 加密 Web 服务",
        636: "LDAPS — 加密 LDAP",
        993: "IMAPS — 加密邮件接收",
        995: "POP3S — 加密邮件接收",
        1433: "MSSQL — Microsoft SQL Server",
        1521: "Oracle DB — Oracle 数据库",
        3306: "MySQL/MariaDB — 开源数据库，⚠ 不应暴露公网",
        3389: "RDP — Windows 远程桌面，⚠ 高危端口",
        5432: "PostgreSQL — 开源数据库",
        6379: "Redis — 缓存数据库，⚠ 默认无密码",
        8080: "HTTP-Alt — Web 备用端口（常见代理/管理页）",
        8443: "HTTPS-Alt — 加密 Web 备用端口",
        9090: "Web-Admin — Web 管理界面（常见 Prometheus/Cockpit）",
        27017: "MongoDB — NoSQL 数据库，⚠ 默认无认证",
    }
    return desc_map.get(port, f"{service} 服务 (端口 {port})")


def _port_risk(port: int) -> str:
    """评估端口风险等级"""
    high_risk = [23, 21, 3389, 6379, 27017, 3306, 1433, 1521, 5432]
    medium_risk = [22, 80, 443, 8080, 8443, 25, 110, 161]
    if port in high_risk:
        return "high"
    if port in medium_risk:
        return "medium"
    return "low"


@router.get("/ping", summary="Ping 连通性测试")
def ping_host(
    target: str = Query(..., description="目标 IP 或域名", examples=["8.8.8.8"]),
    count: int = Query(default=4, ge=1, le=50, description="发包次数"),
    timeout: float = Query(default=3.0, ge=0.5, le=10.0, description="超时(秒)"),
):
    """Ping 测试，返回每次 RTT 和统计信息。"""
    # 显式类型转换（兼容 HTTP 调用和直接调用）
    target = str(target) if not isinstance(target, str) else target
    count = int(count.default) if hasattr(count, 'default') else int(count)
    timeout = float(timeout.default) if hasattr(timeout, 'default') else float(timeout)
    results = []
    lost = 0
    for i in range(count):
        rtt = _ping_once(target, timeout)
        results.append({"seq": i + 1, "rtt": round(rtt, 1) if rtt else None, "status": "ok" if rtt else "timeout"})
        if rtt is None:
            lost += 1

    successful = [r["rtt"] for r in results if r["rtt"] is not None]
    return {
        "target": target,
        "count": count,
        "sent": count,
        "received": count - lost,
        "lost": lost,
        "loss_percent": round(lost / count * 100, 1),
        "min_rtt": round(min(successful), 1) if successful else None,
        "max_rtt": round(max(successful), 1) if successful else None,
        "avg_rtt": round(sum(successful) / len(successful), 1) if successful else None,
        "results": results,
    }


@router.get("/portscan", summary="TCP 端口扫描")
def port_scan(
    target: str = Query(..., description="目标 IP 或域名"),
    start_port: int = Query(default=1, ge=1, le=65535),
    end_port: int = Query(default=1024, ge=1, le=65535),
    ports: str = Query(default="", description="离散端口列表，如 22,80,443（优先于范围）"),
    timeout: float = Query(default=1.0, ge=0.1, le=5.0),
):
    """TCP Connect 端口扫描。

    支持两种模式：
    - 离散端口：`ports=22,80,443,3389`（优先使用）
    - 范围扫描：`start_port=1&end_port=1024`

    返回每个开放端口的状态、服务名、描述和 Banner（如能获取）。
    """
    # 解析端口列表
    if ports.strip():
        port_list = []
        for part in ports.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                # 范围如 10000-20000
                rng = part.split("-")
                try:
                    port_list.extend(range(int(rng[0]), int(rng[1]) + 1))
                except ValueError:
                    raise HTTPException(400, f"无效端口范围: {part}")
            else:
                try:
                    port_list.append(int(part))
                except ValueError:
                    raise HTTPException(400, f"无效端口号: {part}")
        if len(port_list) > 500:
            raise HTTPException(400, "离散端口数不能超过 500 个")
    else:
        if start_port > end_port:
            raise HTTPException(400, "start_port 必须 ≤ end_port")
        port_range = end_port - start_port + 1
        if port_range > 200:
            raise HTTPException(400, "端口范围不能超过 200 个（防滥用）。使用 ports 参数传入离散端口列表如 ?ports=22,80,443")
        port_list = list(range(start_port, end_port + 1))

    total = len(port_list)
    open_ports = []
    scanned = 0

    for port in port_list:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            result = sock.connect_ex((target, port))
            scanned += 1
            if result == 0:
                service_name = COMMON_PORTS.get(port, "未知")
                open_ports.append({
                    "port": port,
                    "service": service_name,
                    "description": _port_description(port, service_name),
                    "risk": _port_risk(port),
                })
        except Exception:
            pass
        finally:
            sock.close()

    return {
        "target": target,
        "scanned": scanned,
        "total": total,
        "open_count": len(open_ports),
        "open_ports": open_ports,
        "all_closed": len(open_ports) == 0,
    }


@router.get("/traceroute", summary="路由追踪 Traceroute")
def traceroute(
    target: str = Query(..., description="目标 IP 或域名"),
    max_hops: int = Query(default=15, ge=1, le=30),
    timeout: float = Query(default=2.0, ge=0.5, le=5.0),
):
    """使用系统 traceroute/tracert 命令。"""
    # 显式类型转换（兼容 HTTP 调用和直接调用）
    target = str(target) if not isinstance(target, str) else target
    max_hops = int(max_hops.default) if hasattr(max_hops, 'default') else int(max_hops)
    timeout = float(timeout.default) if hasattr(timeout, 'default') else float(timeout)
    system = platform.system()
    try:
        if system == "Windows":
            cmd = ["tracert", "-d", "-h", str(max_hops), "-w", str(int(timeout * 1000)), target]
        else:
            cmd = ["traceroute", "-n", "-m", str(max_hops), "-w", str(timeout), target]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=float(max_hops) * float(timeout) + 5)
        output = result.stdout or result.stderr

        # 解析输出
        hops = []
        if system == "Windows":
            # tracert 输出格式：1   <1ms   <1ms   <1ms  192.168.1.1
            for line in output.split("\n"):
                match = re.search(r"^\s*(\d+)\s+(.+)$", line.strip())
                if not match:
                    continue
                hop_num = int(match.group(1))
                rest = match.group(2)
                times = re.findall(r"(\d+|<1)\s*ms", rest)
                # 提取 IP（最后一列）
                ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", rest)
                ip = ip_match.group(1) if ip_match else ("超时" if "*" in rest else "未知")

                rtts = []
                for t in times:
                    try:
                        rtts.append(round(float(t) if t != "<1" else 0.5, 1))
                    except ValueError:
                        pass

                hops.append({
                    "hop": hop_num,
                    "ip": ip,
                    "rtts": rtts,
                    "avg_rtt": round(sum(rtts) / len(rtts), 1) if rtts else None,
                })
        else:
            # Linux traceroute
            for line in output.split("\n"):
                match = re.search(r"^\s*(\d+)\s+(.+)$", line.strip())
                if not match:
                    continue
                hop_num = int(match.group(1))
                rest = match.group(2)
                if "*" in rest and "*" * 3 in rest:
                    hops.append({"hop": hop_num, "ip": "超时", "rtts": [], "avg_rtt": None})
                    continue
                times = re.findall(r"(\d+\.?\d*)\s*ms", rest)
                ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", rest)
                ip = ip_match.group(1) if ip_match else "未知"
                rtts = [round(float(t), 1) for t in times if t]
                hops.append({
                    "hop": hop_num,
                    "ip": ip,
                    "rtts": rtts,
                    "avg_rtt": round(sum(rtts) / len(rtts), 1) if rtts else None,
                })

        return {
            "target": target,
            "max_hops": max_hops,
            "total_hops": len(hops),
            "hops": hops,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Traceroute 超时")
    except Exception as e:
        raise HTTPException(500, f"Traceroute 失败: {e}")


@router.get("/dns", summary="DNS 域名解析查询")
def dns_lookup(
    domain: str = Query(..., description="域名", examples=["baidu.com"]),
    record_type: str = Query(default="A", description="记录类型", examples=["A", "AAAA", "MX", "NS", "TXT", "CNAME"]),
    resolver: str = Query(default="", description="指定 DNS 服务器（留空用系统默认）"),
):
    """查询 DNS 记录并对比多个公共解析器（Cloudflare/Google/Quad9/AliDNS）"""
    if not _DNS_AVAILABLE:
        raise HTTPException(500, "DNS 模块未安装，请执行 pip install dnspython")

    rdtypes = {
        "A": dns.rdatatype.A,
        "AAAA": dns.rdatatype.AAAA,
        "MX": dns.rdatatype.MX,
        "NS": dns.rdatatype.NS,
        "TXT": dns.rdatatype.TXT,
        "CNAME": dns.rdatatype.CNAME,
    }
    rt = rdtypes.get(record_type.upper())
    if rt is None:
        raise HTTPException(400, f"不支持的记录类型: {record_type}，可选 A/AAAA/MX/NS/TXT/CNAME")

    results = []
    resolvers = [resolver] if resolver else [
        "",  # 系统默认
        "223.5.5.5",   # AliDNS
        "8.8.8.8",     # Google
        "1.1.1.1",     # Cloudflare
        "9.9.9.9",     # Quad9
    ]

    for rsv in resolvers:
        resolver_name = rsv if rsv else "系统默认"
        answers = []
        try:
            res = dns.resolver.Resolver()
            if rsv:
                res.nameservers = [rsv]
            res.timeout = 5
            res.lifetime = 5
            for ans in res.resolve(domain, rt):
                answers.append(str(ans))
        except Exception as e:
            answers = [f"查询失败: {e}"]

        results.append({
            "resolver": resolver_name,
            "answers": answers,
            "status": "ok" if answers and not str(answers[0]).startswith("查询失败") else "error",
        })

    return {
        "domain": domain,
        "record_type": record_type.upper(),
        "results": results,
    }


@router.get("/service-lookup", summary="通用端口服务查询")
def port_service_lookup():
    """返回已知端口号对应的服务名称表"""
    return {"ports": [{"port": k, "service": v} for k, v in sorted(COMMON_PORTS.items())]}
