"""MTU 路径发现 — SSE 流式递增包探测"""
from __future__ import annotations

import platform
import re
import subprocess
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/mtu", tags=["diagnostics-mtu"])


def _ping_mtu(host: str, mtu_size: int) -> dict:
    """发送带 DF 标志的指定大小 ping 包"""
    system = platform.system()
    try:
        if system == "Windows":
            # Windows: ping -f -l <size> <host>
            cmd = ["ping", "-n", "1", "-w", "2000", "-f", "-l", str(mtu_size - 28), host]
        else:
            # Linux: ping -M do -s <size> -c 1 <host>
            cmd = ["ping", "-M", "do", "-s", str(mtu_size - 28), "-c", "1", "-W", "2", host]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr

        # 提取 RTT
        rtt = 0.0
        m = re.search(r"time[=<](\d+\.?\d*)\s*ms", output)
        if m:
            rtt = float(m.group(1))

        # 判断成功/失败
        success = result.returncode == 0 and (
            "TTL=" in output.upper()
            or "bytes from" in output.lower()
        )

        # 判断是否 MTU 超限 (需要分片但 DF 已设置)
        fragmented = "frag" in output.lower() or "df" in output.lower()

        return {
            "mtu": mtu_size,
            "success": success and not fragmented,
            "rtt_ms": round(rtt, 1),
            "fragmented": fragmented,
            "error": None if success else ("需要分片" if fragmented else "无响应"),
        }

    except Exception as e:
        return {"mtu": mtu_size, "success": False, "rtt_ms": 0, "fragmented": False, "error": str(e)[:100]}


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
        # 二分搜索
        lo, hi = min_mtu, max_mtu
        best = lo
        scanned = 0
        total_est = 12  # 约 log2(1500-68) 次

        while lo <= hi:
            mid = (lo + hi) // 2
            r = _ping_mtu(target, mid)
            scanned += 1

            yield f"""event: progress
data: {{"type":"progress","data":{{"mtu":{r["mtu"]},"success":{str(r["success"]).lower()},"rtt_ms":{r["rtt_ms"]},"fragmented":{str(r["fragmented"]).lower()},"error":"{r.get('error','') or ''}","current_best":{best},"scanned":{scanned}}},"progress":{scanned},"total":{total_est}}}

"""

            if r["success"]:
                best = max(best, mid)
                lo = mid + 1  # 尝试更大的 MTU
            else:
                hi = mid - 1  # MTU 太大

            await asyncio.sleep(0.5)

        yield f"""event: complete
data: {{"type":"complete","status":"done","path_mtu":{best},"target":"{target}","scanned":{scanned}}}

"""

    return EventSourceResponse(event_generator())
