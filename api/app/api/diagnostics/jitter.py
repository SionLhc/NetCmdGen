"""网络抖动分析 — SSE 流式高频 Ping + Jitter 计算

Jitter 计算基于 RFC 3550：
  J(n) = J(n-1) + (|D(n-1,n)| - J(n-1)) / 16
其中 D(i,j) = RTT(j) - RTT(i)
"""
from __future__ import annotations

import asyncio
import platform
import re
import subprocess
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/jitter", tags=["diagnostics-jitter"])


def _high_freq_ping(host: str, timeout_s: float = 2.0) -> dict:
    """发一次 ping，返回 RTT"""
    system = platform.system()
    try:
        if system == "Windows":
            cmd = ["ping", "-n", "1", "-w", str(int(timeout_s * 1000)), host]
        else:
            cmd = ["ping", "-c", "1", "-W", str(int(timeout_s)), host]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 2)
        output = result.stdout + result.stderr
        m = re.search(r"time[=<](\d+\.?\d*)\s*ms", output)
        if m:
            return {"rtt_ms": float(m.group(1)), "lost": False}
        return {"rtt_ms": 0, "lost": True}
    except Exception:
        return {"rtt_ms": 0, "lost": True}


async def _jitter_calc_async(host: str, packet_count: int = 100, interval_ms: float = 20, seq_offset: int = 0):
    """异步高频 ping 生成器，计算实时 Jitter"""
    from collections import deque

    prev_rtt = None
    jitter = 0.0
    rtts = deque(maxlen=50)  # 用于计算平均值
    total_lost = 0
    total_sent = 0

    for seq in range(seq_offset, seq_offset + packet_count):
        # 用线程池执行同步 ping，避免阻塞事件循环
        r = await asyncio.to_thread(_high_freq_ping, host)
        total_sent += 1

        if r["lost"]:
            total_lost += 1
            yield {
                "seq": seq + 1, "rtt_ms": 0, "jitter_ms": round(jitter, 2),
                "lost": True, "loss_count": total_lost,
                "avg_rtt": round(sum(rtts) / len(rtts), 1) if rtts else 0,
            }
        else:
            rtts.append(r["rtt_ms"])
            if prev_rtt is not None:
                # RFC 3550 Jitter = J + (|D| - J) / 16
                diff = abs(r["rtt_ms"] - prev_rtt)
                jitter = jitter + (diff - jitter) / 16.0

            prev_rtt = r["rtt_ms"]

            yield {
                "seq": seq + 1, "rtt_ms": r["rtt_ms"],
                "jitter_ms": round(jitter, 2),
                "lost": False, "loss_count": total_lost,
                "avg_rtt": round(sum(rtts) / len(rtts), 1),
            }

        # 动态间隔
        await asyncio.sleep(interval_ms / 1000.0)


@router.get("/stream", summary="网络抖动分析 SSE")
async def jitter_analysis_stream(
    target: str = Query(..., description="目标 IP 或域名"),
    packet_count: int = Query(default=100, ge=10, le=500),
    interval_ms: int = Query(default=20, ge=10, le=500, description="发包间隔(ms)"),
    timeout: float = Query(default=2.0, ge=0.5, le=5.0, description="单包超时(s)"),
):
    """高频 Ping 计算网络抖动 + 统计信息"""

    async def event_generator() -> AsyncGenerator[str, None]:
        import json as _json
        async for pt in _jitter_calc_async(target, packet_count, interval_ms):
            payload = _json.dumps({
                "type": "progress",
                "data": {
                    "seq": pt["seq"], "rtt_ms": pt["rtt_ms"],
                    "jitter_ms": pt["jitter_ms"], "lost": pt["lost"],
                    "loss_count": pt["loss_count"], "avg_rtt": pt["avg_rtt"],
                },
                "progress": pt["seq"],
                "total": packet_count,
            }, ensure_ascii=False)
            yield f"data: {payload}\n\n"

        payload = _json.dumps({
            "type": "complete", "status": "done",
            "packet_count": packet_count, "target": target,
        }, ensure_ascii=False)
        yield f"data: {payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
