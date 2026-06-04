"""MTU 路径发现 — SSE 流式递增包探测"""
from __future__ import annotations

import asyncio
import json
import platform
import re
import subprocess
from typing import AsyncGenerator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/mtu", tags=["diagnostics-mtu"])


def _ping_mtu(host: str, mtu_size: int) -> dict:
    """发送带 DF 标志的指定大小 ping 包"""
    system = platform.system()
    try:
        if system == "Windows":
            cmd = ["ping", "-n", "1", "-w", "2000", "-f", "-l", str(mtu_size - 28), host]
        else:
            cmd = ["ping", "-M", "do", "-s", str(mtu_size - 28), "-c", "1", "-W", "2", host]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr

        rtt = 0.0
        m = re.search(r"time[=<](\d+\.?\d*)\s*ms", output)
        if m:
            rtt = float(m.group(1))

        success = result.returncode == 0 and (
            "TTL=" in output.upper() or "bytes from" in output.lower()
        )
        fragmented = "frag" in output.lower() or "df" in output.lower()

        return {
            "mtu": mtu_size,
            "success": success and not fragmented,
            "rtt_ms": round(rtt, 1),
            "fragmented": fragmented,
            "error": None if success else ("需要分片" if fragmented else "无响应"),
            "current_best": 0,
            "scanned": 0,
        }
    except Exception as e:
        return {
            "mtu": mtu_size, "success": False, "rtt_ms": 0,
            "fragmented": False, "error": str(e)[:100],
            "current_best": 0, "scanned": 0,
        }


@router.get("/stream", summary="MTU 路径发现 SSE")
async def mtu_discovery_stream(
    target: str = Query(..., description="目标 IP 或域名"),
    min_mtu: int = Query(default=68, ge=68, le=1500),
    max_mtu: int = Query(default=1500, ge=68, le=9000),
):
    """通过二分法探测路径 MTU"""
    if min_mtu > max_mtu:
        min_mtu, max_mtu = max_mtu, min_mtu

    async def event_generator() -> AsyncGenerator[str, None]:
        lo, hi = min_mtu, max_mtu
        best = lo
        scanned = 0
        total_est = 12

        while lo <= hi:
            mid = (lo + hi) // 2
            # 线程池执行 ping，不阻塞事件循环
            r = await asyncio.to_thread(_ping_mtu, target, mid)
            scanned += 1
            r["current_best"] = best
            r["scanned"] = scanned

            payload = json.dumps({
                "type": "progress",
                "data": r,
                "progress": scanned,
                "total": total_est,
            }, ensure_ascii=False)
            yield f"data: {payload}\n\n"

            if r["success"]:
                best = max(best, mid)
                lo = mid + 1
            else:
                hi = mid - 1

            await asyncio.sleep(0.5)

        final = json.dumps({
            "type": "complete", "status": "done",
            "path_mtu": best, "target": target, "scanned": scanned,
        }, ensure_ascii=False)
        yield f"data: {final}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
