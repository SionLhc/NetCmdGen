"""WiFi 网络工具 — netsh/WMI 本地 Windows WiFi 诊断（从 Wlan 项目移植）"""
from __future__ import annotations

import platform
import re
import subprocess
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

router = APIRouter(tags=["tools"])


# ── netsh 命令封装 ──

def _run_cmd(cmd: str, timeout: int = 8) -> str:
    """执行系统命令，返回 stdout"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return ""
    except Exception:
        return ""


# ── WiFi 状态监控 ──

@router.get("/wifi/status")
def wifi_status():
    """当前 WiFi 连接状态（netsh wlan show interfaces）"""
    if platform.system() != "Windows":
        raise HTTPException(400, "仅支持 Windows")

    output = _run_cmd("netsh wlan show interfaces", timeout=6)

    # 解析
    fields: dict = {}
    for line in output.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip()
            # 信号强度
            if "signal" in key or "信号" in key:
                m = re.search(r"(\d+)", val)
                fields["signal"] = int(m.group(1)) * 2 if m else 0  # 转为百分比
            elif "channel" in key or "信道" in key:
                m = re.search(r"(\d+)", val)
                fields["channel"] = int(m.group(1)) if m else 0
            elif "radio type" in key or "无线电" in key:
                fields["radio"] = val
            elif "ssid" in key.lower():
                fields["ssid"] = val
            elif "bssid" in key.lower():
                fields["bssid"] = val
            elif "state" in key or "状态" in key:
                fields["state"] = val
            elif "receive" in key or "接收" in key:
                m = re.search(r"(\d+)", val)
                fields["rx_rate"] = int(m.group(1)) if m else 0
            elif "transmit" in key or "发送" in key:
                m = re.search(r"(\d+)", val)
                fields["tx_rate"] = int(m.group(1)) if m else 0
            elif "authentication" in key or "身份验证" in key:
                fields["auth"] = val
            elif "cipher" in key or "密码" in key:
                fields["cipher"] = val
            elif "profile" in key or "配置文件" in key:
                fields["profile"] = val

    # 补充：尝试获取网卡驱动信息
    driver_info = _get_wifi_adapter_info()

    return {
        **fields,
        "connected": "connected" in fields.get("state", "").lower() or "已连接" in fields.get("state", ""),
        "adapter": driver_info,
    }


@router.get("/wifi/networks")
def wifi_networks():
    """周围可见 WiFi 网络列表 — 信号强度/信道/加密"""
    if platform.system() != "Windows":
        raise HTTPException(400, "仅支持 Windows")

    output = _run_cmd("netsh wlan show networks mode=bssid", timeout=10)

    networks = []
    current_ssid = ""
    current_auth = ""

    for line in output.split("\n"):
        line = line.strip()
        # SSID 名称行
        ssid_match = re.search(r"SSID\s+\d+\s*:\s*(.+)", line)
        if ssid_match:
            if current_ssid:
                pass  # 不在这保存，在 BSSID 层保存
            current_ssid = ssid_match.group(1).strip()
            current_auth = ""
            continue

        # 认证
        auth_match = re.search(r"Authentication\s*:\s*(.+)", line, re.IGNORECASE)
        if auth_match or re.search(r"身份验证\s*:\s*(.+)", line):
            if auth_match:
                current_auth = auth_match.group(1).strip()
            else:
                current_auth = line.split(":")[-1].strip()
            continue

        # BSSID
        bssid_match = re.search(r"BSSID\s+\d+\s*:\s*([0-9a-fA-F]{2}[:][0-9a-fA-F]{2}[:][0-9a-fA-F]{2}[:][0-9a-fA-F]{2}[:][0-9a-fA-F]{2}[:][0-9a-fA-F]{2})", line)
        if not bssid_match:
            continue

        bssid = bssid_match.group(1)
        network = {
            "ssid": current_ssid,
            "bssid": bssid,
            "auth": current_auth,
            "signal": 0,
            "channel": 0,
            "radio": "",
            "rate": "",
        }

        # 继续读 BSSID 块内信息
        # 简单再扫描整个块（实际实现应该用状态机，这里简化）
        pass

    # 简单正则方式重新解析
    pattern = re.compile(
        r"SSID\s+\d+\s*:\s*(?P<ssid>.*?)\n"
        r".*?BSSID\s+\d+\s*:\s*(?P<bssid>[0-9a-fA-F:]{17})"
        r"[\s\S]*?Signal\s*:\s*(?P<signal>\d+)%"
        r"[\s\S]*?Channel\s*:\s*(?P<channel>\d+)"
        r"[\s\S]*?Radio\s+type\s*:\s*(?P<radio>[^\n]*)"
        r"[\s\S]*?Receive\s+rate\s*:\s*(?P<rate>[^\n]*)",
        re.IGNORECASE,
    )

    for m in pattern.finditer(output):
        networks.append({
            "ssid": m.group("ssid").strip(),
            "bssid": m.group("bssid").strip(),
            "signal": int(m.group("signal")) if m.group("signal") else 0,
            "channel": int(m.group("channel")) if m.group("channel") else 0,
            "radio": m.group("radio").strip() if m.group("radio") else "",
            "rate": m.group("rate").strip() if m.group("rate") else "",
            "auth": current_auth if current_ssid == m.group("ssid").strip() else "",
        })

    return networks


@router.get("/wifi/ipconfig")
def wifi_ipconfig():
    """WiFi 网卡 IP 配置（ipconfig）"""
    if platform.system() != "Windows":
        raise HTTPException(400, "仅支持 Windows")

    output = _run_cmd("ipconfig /all", timeout=5)
    # 只提取无线网卡块
    blocks = re.split(r"(?=Wireless|无线|Wi-Fi|WLAN)", output, flags=re.IGNORECASE)
    if len(blocks) < 2:
        return {"error": "未找到无线网卡", "raw": output[:500]}

    wifi_block = blocks[-1] if len(blocks) > 1 else output

    result: dict = {}
    for line in wifi_block.split("\n"):
        line = line.strip()
        if "IPv4" in line or "IPv4" in line:
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                result["ip"] = m.group(1)
        elif "子网掩码" in line or "Subnet Mask" in line:
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                result["netmask"] = m.group(1)
        elif "默认网关" in line or "Default Gateway" in line:
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                result["gateway"] = m.group(1)
        elif "DHCP Server" in line or "DHCP 服务器" in line:
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                result["dhcp_server"] = m.group(1)
        elif "DNS" in line:
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                if "dns" not in result:
                    result["dns"] = []
                result["dns"].append(m.group(1))
        elif "租约" in line or "Lease" in line:
            result["lease"] = line.split(":")[-1].strip()

    return result


@router.get("/wifi/adapter")
def wifi_adapter():
    """WiFi 网卡驱动信息（wmic）"""
    if platform.system() != "Windows":
        raise HTTPException(400, "仅支持 Windows")

    output = _run_cmd(
        'wmic nic where "NetConnectionID like \'%Wireless%\' or NetConnectionID like \'%Wi-Fi%\' or NetConnectionID like \'%WLAN%\' or NetConnectionID like \'%无线%\'" get Name,Manufacturer,Description /format:csv',
        timeout=5,
    )

    # 简单返回原始文本，前端自行解析
    info = _get_wifi_adapter_info()

    return {
        "name": info.get("name", ""),
        "manufacturer": info.get("manufacturer", ""),
        "description": info.get("description", ""),
    }


def _get_wifi_adapter_info() -> dict:
    """获取 WiFi 网卡基本信息"""
    output = _run_cmd(
        'wmic nic get Name,Manufacturer,NetConnectionID /format:csv', timeout=5
    )
    for line in output.split("\n"):
        if re.search(r"wireless|wi-fi|wlan|无线", line, re.IGNORECASE):
            parts = line.split(",")
            if len(parts) >= 3:
                return {
                    "name": parts[0].strip() if len(parts) > 2 else "",
                    "manufacturer": parts[1].strip() if len(parts) > 2 else "",
                    "description": parts[-1].strip(),
                }
    return {"name": "", "manufacturer": "", "description": ""}


# ── 掉线事件日志查询 ──

@router.get("/wifi/events")
def wifi_events(minutes: int = Query(default=30, ge=1, le=1440)):
    """查询最近 N 分钟 WLAN 事件日志"""
    if platform.system() != "Windows":
        raise HTTPException(400, "仅支持 Windows")

    # 计算时间范围
    from datetime import datetime, timedelta
    start = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S")

    output = _run_cmd(
        f'wevtutil qe "Microsoft-Windows-WLAN-AutoConfig/Operational" /q:"*[System[TimeCreated[@SystemTime>=\'{start}\']]]" /c:20 /f:text /rd:true',
        timeout=10,
    )

    events = []
    lines = output.split("\n")
    current: Optional[dict] = None

    for line in lines:
        line = line.strip()
        # 日期行
        if re.match(r"Date:", line):
            if current:
                events.append(current)
            current = {"time": line.split(":", 1)[-1].strip()}
            continue
        if not current:
            continue
        if "Event ID:" in line:
            m = re.search(r"(\d+)", line)
            current["event_id"] = int(m.group(1)) if m else 0
        elif "Level:" in line:
            current["level"] = line.split(":", 1)[-1].strip()
        elif "Description:" in line:
            current["desc"] = line.split(":", 1)[-1].strip()
        elif "Keyword:" in line:
            current["keyword"] = line.split(":", 1)[-1].strip()
        elif "User:" in line:
            current["user"] = line.split(":", 1)[-1].strip()

    if current:
        events.append(current)

    return events


# ── 优化：批量采集端点 — 一次请求获取全部数据 ──

@router.get("/wifi/batch")
def wifi_batch():
    """一次获取状态+网络列表+网卡信息（减少前端 HTTP 往返）"""
    if platform.system() != "Windows":
        raise HTTPException(400, "仅支持 Windows")

    # netsh 支持用 && 串联命令，一次 subprocess 调用
    cmd = 'netsh wlan show interfaces && netsh wlan show networks mode=bssid'
    output = _run_cmd(cmd, timeout=12)

    # 按分隔符拆成两部分
    parts = output.split("Interface name")
    iface_output = ""
    networks_output = ""

    if len(parts) >= 2:
        # 第二部分是 interfaces 输出
        iface_output = "Interface name" + parts[1]

    # 找 networks 输出起始
    net_start = output.find("SSID 1")
    if net_start > 0:
        networks_output = output[net_start:]

    # 解析状态
    fields = {}
    for line in iface_output.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().lower(); val = val.strip()
            if "signal" in key or "信号" in key:
                m = re.search(r"(\d+)", val)
                fields["signal"] = int(m.group(1)) * 2 if m else 0
            elif "channel" in key or "信道" in key:
                m = re.search(r"(\d+)", val)
                fields["channel"] = int(m.group(1)) if m else 0
            elif "radio type" in key or "无线电" in key:
                fields["radio"] = val
            elif "ssid" in key.lower():
                fields["ssid"] = val
            elif "bssid" in key.lower():
                fields["bssid"] = val
            elif "state" in key or "状态" in key:
                fields["state"] = val
            elif "receive" in key or "接收" in key:
                m = re.search(r"(\d+)", val)
                fields["rx_rate"] = int(m.group(1)) if m else 0
            elif "transmit" in key or "发送" in key:
                m = re.search(r"(\d+)", val)
                fields["tx_rate"] = int(m.group(1)) if m else 0

    # 解析网络列表
    networks = _parse_bssid_list(networks_output)

    return {
        "connected": "connected" in fields.get("state", "").lower() or "已连接" in fields.get("state", ""),
        "ssid": fields.get("ssid", ""),
        "bssid": fields.get("bssid", ""),
        "signal": fields.get("signal", 0),
        "channel": fields.get("channel", 0),
        "radio": fields.get("radio", ""),
        "rx_rate": fields.get("rx_rate", 0),
        "tx_rate": fields.get("tx_rate", 0),
        "networks": networks,
    }


def _parse_bssid_list(output: str) -> list:
    """从 netsh bssid 输出中提取 AP 列表"""
    networks = []
    pattern = re.compile(
        r"SSID\s+\d+\s*:\s*(?P<ssid>.*?)\n"
        r".*?BSSID\s+\d+\s*:\s*(?P<bssid>[0-9a-fA-F:]{17})"
        r"[\s\S]*?Signal\s*:\s*(?P<signal>\d+)%"
        r"[\s\S]*?Channel\s*:\s*(?P<channel>\d+)"
        r"[\s\S]*?Radio\s+type\s*:\s*(?P<radio>[^\n]*)"
        r"[\s\S]*?Receive\s+rate\s*:\s*(?P<rate>[^\n]*)",
        re.IGNORECASE,
    )
    for m in pattern.finditer(output):
        networks.append({
            "ssid": m.group("ssid").strip(),
            "bssid": m.group("bssid").strip(),
            "signal": int(m.group("signal")) if m.group("signal") else 0,
            "channel": int(m.group("channel")) if m.group("channel") else 0,
            "radio": m.group("radio").strip() if m.group("radio") else "",
            "rate": m.group("rate").strip() if m.group("rate") else "",
        })
    return networks
