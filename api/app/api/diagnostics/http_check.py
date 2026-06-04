"""HTTP/HTTPS 可用性监测 — 使用 urllib + 线程池，避免 aiohttp 事件循环卡死"""
from __future__ import annotations

import asyncio
import json
import ssl
import time
from typing import AsyncGenerator

import certifi
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/http", tags=["diagnostics-http"])


async def _http_request(url: str, method: str, timeout: float,
                        check_ssl: bool) -> dict:
    """在后台线程执行同步 HTTP 请求"""
    import urllib.request
    import urllib.error

    def _do():
        result = {
            "url": url, "status_code": 0, "rtt_ms": 0, "content_length": 0,
            "server": "", "redirect_chain": [], "tls_version": None,
            "cert_expires": None, "cert_issuer": None, "error": None,
        }
        context = None
        if url.startswith("https://") and check_ssl:
            context = ssl.create_default_context(cafile=certifi.where())

        try:
            t0 = time.monotonic()
            req = urllib.request.Request(url, method=method)
            resp = urllib.request.urlopen(
                req, timeout=timeout,
                context=context if url.startswith("https://") else None,
            )
            body = resp.read()
            result["rtt_ms"] = round((time.monotonic() - t0) * 1000, 1)
            result["status_code"] = resp.status
            result["content_length"] = len(body)
            result["server"] = resp.headers.get("Server", "") or ""

            # 重定向 URL
            final_url = resp.geturl()
            if final_url != url:
                result["redirect_chain"].append(f"{resp.status}: {final_url}")

            # SSL 证书
            if url.startswith("https://"):
                try:
                    sock = getattr(resp, 'fp', None)
                    if sock and hasattr(sock, 'raw'):
                        ssl_sock = sock.raw._sock
                        result["tls_version"] = ssl_sock.version()
                        cert = ssl_sock.getpeercert()
                        if cert:
                            result["cert_expires"] = cert.get("notAfter", "")
                            issuer = cert.get("issuer", None)
                            if isinstance(issuer, list):
                                for key, val in issuer:
                                    if key == "organizationName":
                                        result["cert_issuer"] = val
                                        break
                except Exception:
                    pass

        except urllib.error.URLError as e:
            result["error"] = f"连接失败: {str(e.reason)[:150]}"
        except Exception as e:
            result["error"] = f"请求出错: {str(e)[:200]}"

        return result

    return await asyncio.to_thread(_do)


@router.get("/stream", summary="HTTP/HTTPS 可用性监测")
async def http_check_stream(
    url: str = Query(..., description="目标 URL"),
    method: str = Query(default="GET"),
    follow_redirects: bool = Query(default=True),
    check_ssl: bool = Query(default=True),
    timeout: float = Query(default=10.0, ge=1.0, le=30.0),
):
    async def event_generator() -> AsyncGenerator[str, None]:
        # 阶段提示
        for msg in ["正在解析域名...", f"正在连接 {url}..."]:
            p = json.dumps({"type": "progress", "data": {"stage": "dns", "message": msg}}, ensure_ascii=False)
            yield f"data: {p}\n\n"

        if check_ssl and url.startswith("https://"):
            p = json.dumps({"type": "progress", "data": {"stage": "ssl", "message": "正在检查 SSL 证书..."}}, ensure_ascii=False)
            yield f"data: {p}\n\n"

        result = await _http_request(url, method, timeout, check_ssl)

        # 最终结果
        p = json.dumps({"type": "progress", "data": result}, ensure_ascii=False)
        yield f"data: {p}\n\n"

        # 完成
        yield f"data: {json.dumps({'type': 'complete', 'status': 'done', 'url': url}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
