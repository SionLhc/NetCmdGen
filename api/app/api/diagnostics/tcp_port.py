"""TCP 端口连通性检测 — SSE 流式逐个端口扫描"""
from __future__ import annotations

import asyncio
import socket
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Query, HTTPException
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/tcp-port", tags=["diagnostics-tcp"])

COMMON_PORTS = {
    22: ("SSH", "加密远程管理，建议修改默认端口", "medium"),
    23: ("Telnet", "明文远程管理，⚠ 不安全", "high"),
    25: ("SMTP", "邮件发送协议", "medium"),
    53: ("DNS", "域名解析服务", "low"),
    80: ("HTTP", "Web 服务，建议跳转 HTTPS", "medium"),
    110: ("POP3", "邮件接收协议", "low"),
    123: ("NTP", "网络时间同步", "low"),
    143: ("IMAP", "邮件接收协议(新版)", "low"),
    161: ("SNMP", "网络设备监控管理", "medium"),
    389: ("LDAP", "目录访问协议", "low"),
    443: ("HTTPS", "加密 Web 服务", "medium"),
    636: ("LDAPS", "加密 LDAP", "low"),
    993: ("IMAPS", "加密邮件接收", "low"),
    995: ("POP3S", "加密邮件接收", "low"),
    1433: ("MSSQL", "Microsoft SQL Server", "high"),
    1521: ("Oracle", "Oracle 数据库", "high"),
    3306: ("MySQL", "开源数据库，⚠ 不应暴露公网", "high"),
    3389: ("RDP", "Windows 远程桌面，⚠ 高危", "high"),
    5432: ("PostgreSQL", "开源数据库", "high"),
    6379: ("Redis", "缓存数据库，⚠ 默认无密码", "high"),
    8080: ("HTTP-Alt", "Web 备用端口", "medium"),
    8443: ("HTTPS-Alt", "加密 Web 备用端口", "medium"),
    9090: ("WebAdmin", "Web 管理界面", "medium"),
    27017: ("MongoDB", "NoSQL 数据库，⚠ 默认无认证", "high"),
}


async def _tcp_connect(host: str, port: int, timeout: float) -> dict:
    """TCP 连接测试，返回端口状态+延迟+服务信息"""
    service_info = COMMON_PORTS.get(port, ("未知", f"端口 {port}", "low"))
    try:
        t0 = time.monotonic()
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        rtt = round((time.monotonic() - t0) * 1000, 1)
        writer.close()
        await writer.wait_closed()
        return {
            "port": port, "open": True, "rtt_ms": rtt,
            "service": service_info[0], "description": service_info[1],
            "risk": service_info[2],
        }
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return {"port": port, "open": False, "rtt_ms": 0,
                "service": service_info[0], "description": service_info[1],
                "risk": service_info[2]}


@router.get("/stream", summary="TCP 端口连通性检测 SSE")
async def tcp_port_stream(
    target: str = Query(..., description="目标 IP 或域名"),
    ports: str = Query(default="22,80,443,3306,3389,6379", description="端口列表"),
    timeout_ms: int = Query(default=3000, ge=500, le=10000, description="超时毫秒"),
):
    port_list = []
    for p in ports.split(","):
        p = p.strip()
        if not p:
            continue
        try:
            port_list.append(int(p))
        except ValueError:
            raise HTTPException(400, f"无效端口: {p}")
    if len(port_list) > 100:
        raise HTTPException(400, "端口数不能超过 100")
    total = len(port_list)
    timeout_s = timeout_ms / 1000.0

    async def event_generator() -> AsyncGenerator[str, None]:
        for i, port in enumerate(port_list):
            r = await _tcp_connect(target, port, timeout_s)
            yield f"""event: progress
data: {{"type":"progress","data":{{"port":{r["port"]},"open":{str(r["open"]).lower()},"rtt_ms":{r["rtt_ms"]},"service":"{r["service"]}","description":"{r["description"]}","risk":"{r["risk"]}"}},"progress":{i+1},"total":{total}}}

"""
            await asyncio.sleep(0.03)

        open_count = sum(1 for p in port_list if True)  # placeholder
        yield f"""event: complete
data: {{"type":"complete","status":"done","total":{total},"target":"{target}"}}

"""

    return EventSourceResponse(event_generator())
