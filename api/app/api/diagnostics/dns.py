"""DNS 解析诊断 — SSE 流式多解析器对比"""
from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.diagnostics.models import DnsResult

router = APIRouter(prefix="/dns", tags=["diagnostics-dns"])

DNS_SERVERS = {
    "8.8.8.8": "Google", "8.8.4.4": "Google",
    "1.1.1.1": "Cloudflare", "9.9.9.9": "Quad9",
    "208.67.222.222": "OpenDNS", "114.114.114.114": "114DNS",
    "223.5.5.5": "AliDNS", "119.29.29.29": "DNSPod",
}
RECORD_TYPES = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA", "SRV"]


async def _resolve(server: str, domain: str, rdtype: str) -> DnsResult:
    result = DnsResult(server=server, server_name=DNS_SERVERS.get(server, server),
                       domain=domain, record_type=rdtype)
    try:
        import dns.resolver
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
    except Exception as e:
        result.error = str(e)[:100]
    return result


@router.get("/stream", summary="DNS 解析诊断 SSE")
async def dns_diagnostic_stream(
    target: str = Query(..., description="目标域名"),
    record_types: str = Query(default="A,AAAA,CNAME,MX,NS,TXT"),
    dns_servers: str = Query(default="8.8.8.8,114.114.114.114,223.5.5.5"),
):
    types = [t.strip().upper() for t in record_types.split(",") if t.strip()]
    servers = [s.strip() for s in dns_servers.split(",") if s.strip()]
    total = len(servers) * len(types)

    async def event_generator() -> AsyncGenerator[str, None]:
        done = 0
        for rdtype in types:
            if rdtype not in RECORD_TYPES:
                continue
            tasks = [_resolve(s, target, rdtype) for s in servers]
            batch = await asyncio.gather(*tasks, return_exceptions=True)
            for r in batch:
                done += 1
                if isinstance(r, Exception):
                    r = DnsResult(server="", server_name="",
                                  domain=target, record_type=rdtype,
                                  error=str(r)[:100])
                payload = json.dumps({
                    "type": "progress",
                    "data": {
                        "server": r.server, "server_name": r.server_name,
                        "domain": r.domain, "record_type": r.record_type,
                        "records": r.records, "rtt_ms": r.rtt_ms,
                        "error": r.error or "",
                    },
                    "progress": done,
                    "total": total,
                }, ensure_ascii=False)
                yield f"data: {payload}\n\n"
        payload = json.dumps({
            "type": "complete", "status": "done",
            "total_dns": total, "domain": target,
        }, ensure_ascii=False)
        yield f"data: {payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
