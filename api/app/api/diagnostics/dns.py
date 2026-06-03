"""DNS 解析诊断 — SSE 流式多解析器对比"""
from __future__ import annotations

import asyncio
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Query, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.api.diagnostics.models import DnsResult

router = APIRouter(prefix="/dns", tags=["diagnostics-dns"])

# 公共 DNS 解析器
DNS_SERVERS = {
    "8.8.8.8": "Google",
    "8.8.4.4": "Google",
    "1.1.1.1": "Cloudflare",
    "9.9.9.9": "Quad9",
    "208.67.222.222": "OpenDNS",
    "114.114.114.114": "114DNS",
    "223.5.5.5": "AliDNS",
    "119.29.29.29": "DNSPod",
}

RECORD_TYPES = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA", "SRV"]

# SSH 远程端口列表（供 SSH 场景扫描）
COMMON_PORTS = {
    22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP",
    110: "POP3", 123: "NTP", 143: "IMAP", 161: "SNMP", 389: "LDAP",
    443: "HTTPS", 636: "LDAPS", 993: "IMAPS", 995: "POP3S",
    1433: "MSSQL", 1521: "Oracle", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 6379: "Redis", 8080: "HTTP-Alt",
    8443: "HTTPS-Alt", 9090: "WebAdmin", 27017: "MongoDB",
}


async def _resolve(server: str, domain: str, rdtype: str) -> DnsResult:
    """使用指定 DNS 服务器解析域名"""
    result = DnsResult(
        server=server,
        server_name=DNS_SERVERS.get(server, server),
        domain=domain,
        record_type=rdtype,
    )
    try:
        import dns.resolver
        import dns.rdatatype
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [server]
        resolver.timeout = 3
        resolver.lifetime = 5
        t0 = time.monotonic()
        answers = resolver.resolve(domain, rdtype)
        result.rtt_ms = round((time.monotonic() - t0) * 1000, 1)
        result.records = [str(r) for r in answers]
    except dns.resolver.NXDOMAIN:
        result.error = "域名不存在"
    except dns.resolver.NoAnswer:
        result.error = "无该类型记录"
    except dns.resolver.Timeout:
        result.error = "DNS 超时"
    except ImportError:
        result.error = "dnspython 未安装"
    except Exception as e:
        result.error = str(e)[:100]
    return result


@router.get("/stream", summary="DNS 解析诊断 SSE")
async def dns_diagnostic_stream(
    target: str = Query(..., description="目标域名"),
    record_types: str = Query(default="A,AAAA,CNAME,MX,NS,TXT", description="记录类型"),
    dns_servers: str = Query(
        default="8.8.8.8,114.114.114.114,223.5.5.5",
        description="DNS 服务器列表",
    ),
    timeout: float = Query(default=5.0, ge=1.0, le=30.0),
):
    """对目标域名进行多 DNS 服务器多记录类型解析"""
    # 先检查依赖
    try:
        import dns.resolver  # noqa: F401
    except ImportError:
        raise HTTPException(500, "dnspython 未安装")

    types = [t.strip().upper() for t in record_types.split(",") if t.strip()]
    servers = [s.strip() for s in dns_servers.split(",") if s.strip()]
    total = len(servers) * len(types)
    done = 0

    async def event_generator() -> AsyncGenerator[str, None]:
        nonlocal done
        for rdtype in types:
            if rdtype not in RECORD_TYPES:
                continue
            # 并发查询所有 DNS 服务器（同类型）
            tasks = [_resolve(s, target, rdtype) for s in servers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                done += 1
                if isinstance(r, Exception):
                    r = DnsResult(
                        server="", server_name="", domain=target,
                        record_type=rdtype, error=str(r)[:100],
                    )
                yield f"""event: progress
data: {{"type":"progress","data":{{"server":"{r.server}","server_name":"{r.server_name}","domain":"{r.domain}","record_type":"{r.record_type}","records":{r.records},"rtt_ms":{r.rtt_ms},"error":"{r.error or ''}"}},"progress":{done},"total":{total}}}

"""
                await asyncio.sleep(0.02)

        # 完成
        yield f"""event: complete
data: {{"type":"complete","status":"done","total_dns":{total},"domain":"{target}"}}

"""

    return EventSourceResponse(event_generator())
