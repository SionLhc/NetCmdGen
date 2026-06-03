"""HTTP/HTTPS 可用性监测 — SSE 流式诊断"""
from __future__ import annotations

import asyncio
import ssl
import time
from typing import AsyncGenerator, Optional
from urllib.parse import urlparse

import certifi
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/http", tags=["diagnostics-http"])


async def _check_http(
    url: str, method: str = "GET", follow_redirects: bool = True,
    check_ssl: bool = True, timeout: float = 5.0,
) -> dict:
    """执行 HTTP 请求检测"""
    import aiohttp

    result = {
        "url": url, "status_code": 0, "rtt_ms": 0, "content_length": 0,
        "server": "", "redirect_chain": [], "tls_version": None,
        "cert_expires": None, "cert_issuer": None, "error": None,
    }

    # 进度阶段
    yield {"type": "progress", "data": {"stage": "dns", "message": f"正在解析域名..."}}

    ssl_ctx = ssl.create_default_context(cafile=certifi.where()) if check_ssl else False

    try:
        t0 = time.monotonic()
        connector = aiohttp.TCPConnector(ssl=ssl_ctx if isinstance(ssl_ctx, ssl.SSLContext) else None)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as session:
            yield {"type": "progress", "data": {"stage": "connect", "message": f"正在连接 {url}..."}}

            async with session.request(
                method, url,
                allow_redirects=follow_redirects,
                ssl=ssl_ctx if check_ssl else False,
            ) as resp:
                result["rtt_ms"] = round((time.monotonic() - t0) * 1000, 1)
                result["status_code"] = resp.status
                result["server"] = resp.headers.get("Server", "")
                content = await resp.read()
                result["content_length"] = len(content)

                # SSL 信息
                if check_ssl and url.startswith("https"):
                    # Progress: ssl check
                    yield {"type": "progress", "data": {"stage": "ssl", "message": "正在检查 SSL 证书..."}}

                    raw_conn = resp.connection.transport
                    if hasattr(raw_conn, 'get_extra_info'):
                        ssl_obj = raw_conn.get_extra_info('ssl_object')
                        if ssl_obj:
                            result["tls_version"] = ssl_obj.version()
                            cert = ssl_obj.getpeercert()
                            if cert:
                                result["cert_expires"] = cert.get("notAfter", "")
                                issuer = cert.get("issuer", None)
                                if issuer:
                                    # Parse issuer tuple
                                    for key, val in dict(issuer).items():
                                        if key == "organizationName":
                                            result["cert_issuer"] = val
                                            break

                # 重定向链
                redirs = resp.history
                for h in redirs:
                    result["redirect_chain"].append(str(h.status) + ": " + str(h.url))

            result["rtt_ms"] = round((time.monotonic() - t0) * 1000, 1)

    except aiohttp.ClientError as e:
        result["error"] = str(e)[:200]
    except asyncio.TimeoutError:
        result["error"] = "请求超时"
    except ImportError:
        result["error"] = "aiohttp 未安装"
    except Exception as e:
        result["error"] = str(e)[:200]

    yield {"type": "progress", "data": result}


http_timeout: Optional[float] = 5.0


@router.get("/stream", summary="HTTP/HTTPS 可用性监测 SSE")
async def http_check_stream(
    url: str = Query(..., description="目标 URL"),
    method: str = Query(default="GET", description="HTTP 方法"),
    follow_redirects: bool = Query(default=True),
    check_ssl: bool = Query(default=True),
    timeout: float = Query(default=10.0, ge=1.0, le=30.0),
):
    async def event_generator() -> AsyncGenerator[str, None]:
        async for event in _check_http(url, method, follow_redirects, check_ssl, timeout):
            if event["type"] == "progress" and "status_code" in event["data"]:
                # Final result
                d = event["data"]
                yield f"""event: progress
data: {{"type":"progress","data":{{"url":"{d['url']}","status_code":{d['status_code']},"rtt_ms":{d['rtt_ms']},"content_length":{d['content_length']},"server":"{d['server']}","redirect_chain":{d['redirect_chain']},"tls_version":"{d.get('tls_version', '') or ''}","cert_expires":"{d.get('cert_expires', '') or ''}","cert_issuer":"{d.get('cert_issuer', '') or ''}","error":"{d.get('error', '') or ''}"}}

"""
            else:
                d = event["data"]
                yield f"""event: progress
data: {{"type":"progress","data":{{"stage":"{d.get('stage','')}","message":"{d.get('message','')}"}}}}

"""
            await asyncio.sleep(0.02)

        yield f"""event: complete
data: {{"type":"complete","status":"done","url":"{url}"}}

"""

    return EventSourceResponse(event_generator())
