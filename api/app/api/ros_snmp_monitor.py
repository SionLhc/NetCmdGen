"""ROS SNMP 流量监控 — pysnmp 7.x 适配"""

import asyncio
import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from pysnmp.hlapi.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, get_cmd, next_cmd,
)

router = APIRouter(prefix="/ros/traffic", tags=["ros-traffic"])

IF_IN_OCTETS = "1.3.6.1.2.1.2.2.1.10"
IF_OUT_OCTETS = "1.3.6.1.2.1.2.2.1.16"
IF_NAME = "1.3.6.1.2.1.2.2.1.2"
IF_SPEED = "1.3.6.1.2.1.2.2.1.5"


async def _snmp_get(host: str, community: str, oid: str,
                    port: int = 161) -> str:
    """SNMP GET — pysnmp 7.x 返回 (err_ind, err_status, err_idx, var_binds) tuple"""
    result = await get_cmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        await UdpTransportTarget.create((host, port), timeout=3, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    err_ind, err_status, err_idx, var_binds = result
    if err_ind:
        raise ConnectionError(f"SNMP error: {err_ind}")
    if err_status:
        raise ConnectionError(f"SNMP status: {err_status.prettyPrint()}")
    for vb in var_binds:
        return str(vb[1])
    return "0"


async def _snmp_walk(host: str, community: str, base_oid: str,
                     port: int = 161) -> dict[int, str]:
    """SNMP WALK — 逐个 GET 前 30 个接口"""
    result = {}
    for i in range(1, 31):
        try:
            val = await _snmp_get(host, community, f"{base_oid}.{i}", port)
            if val and val.strip():
                result[i] = val
        except Exception:
            break  # 到达末位接口
    return result


@router.get("/interfaces")
async def list_interfaces(
    host: str = Query(...),
    community: str = Query(default="public"),
    port: int = Query(default=161),
):
    """获取设备接口列表"""
    try:
        names = await _snmp_walk(host, community, IF_NAME, port)
        speeds = await _snmp_walk(host, community, IF_SPEED, port)
        result = []
        for idx, name in names.items():
            spd = int(speeds.get(idx, "0"))
            result.append({
                "index": idx,
                "name": name,
                "speed": spd,
                "speed_label": f"{spd // 1_000_000} Mbps" if spd else "",
            })
        return sorted(result, key=lambda x: x["index"])
    except Exception as e:
        raise HTTPException(500, f"SNMP 查询失败: {str(e)[:200]}")


@router.get("/stream")
async def traffic_stream(
    host: str = Query(...),
    if_index: int = Query(default=1),
    community: str = Query(default="public"),
    port: int = Query(default=161),
    interval_ms: int = Query(default=1000, ge=200, le=5000),
    duration_s: int = Query(default=60, le=300),
):
    """SSE 实时流量推送"""
    async def generator() -> AsyncGenerator[str, None]:
        prev_rx = prev_tx = 0
        prev_ts = time.time()
        first = True
        end_time = time.time() + duration_s

        while time.time() < end_time:
            try:
                rx_str = await _snmp_get(
                    host, community, f"{IF_IN_OCTETS}.{if_index}", port)
                tx_str = await _snmp_get(
                    host, community, f"{IF_OUT_OCTETS}.{if_index}", port)
                now_ts = time.time()
                now_rx = int(rx_str)
                now_tx = int(tx_str)

                if first:
                    prev_rx, prev_tx = now_rx, now_tx
                    prev_ts = now_ts
                    first = False
                    await asyncio.sleep(interval_ms / 1000)
                    continue

                elapsed = now_ts - prev_ts
                rx_bytes = max(0, now_rx - prev_rx)
                tx_bytes = max(0, now_tx - prev_tx)
                rx_mbps = round((rx_bytes * 8) / elapsed / 1_000_000, 2)
                tx_mbps = round((tx_bytes * 8) / elapsed / 1_000_000, 2)

                prev_rx, prev_tx = now_rx, now_tx
                prev_ts = now_ts

                payload = json.dumps({
                    "ts": round(now_ts, 1),
                    "rx_mbps": rx_mbps,
                    "tx_mbps": tx_mbps,
                }, ensure_ascii=False)
                yield f"data: {payload}\n\n"

            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)[:200]})}\n\n"
                return

            await asyncio.sleep(interval_ms / 1000)

        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# 内存缓存：记录上次查询的快照值，用于差分计算
_snapshot_cache: dict[str, tuple[int, int, float]] = {}  # key -> (last_rx, last_tx, last_ts)


@router.get("/snapshot")
async def traffic_snapshot(
    host: str = Query(...),
    if_index: int = Query(default=1),
    community: str = Query(default="public"),
    port: int = Query(default=161),
):
    """单次 SNMP 快照 — 前端每 5 分钟轮询，内部自动计算差分速率"""
    try:
        rx_str = await _snmp_get(host, community, f"{IF_IN_OCTETS}.{if_index}", port)
        tx_str = await _snmp_get(host, community, f"{IF_OUT_OCTETS}.{if_index}", port)
        now_ts = time.time()
        now_rx = int(rx_str)
        now_tx = int(tx_str)

        cache_key = f"{host}:{if_index}"
        rx_mbps = 0.0
        tx_mbps = 0.0

        if cache_key in _snapshot_cache:
            last_rx, last_tx, last_ts = _snapshot_cache[cache_key]
            elapsed = now_ts - last_ts
            if elapsed > 0:
                rx_bytes = max(0, now_rx - last_rx)
                tx_bytes = max(0, now_tx - last_tx)
                # 处理 32-bit 计数器回绕（约 4.3 GB）
                if now_rx < last_rx:
                    rx_bytes = (2**32 - last_rx) + now_rx
                if now_tx < last_tx:
                    tx_bytes = (2**32 - last_tx) + now_tx
                rx_mbps = round((rx_bytes * 8) / elapsed / 1_000_000, 2)
                tx_mbps = round((tx_bytes * 8) / elapsed / 1_000_000, 2)

        # 更新缓存
        _snapshot_cache[cache_key] = (now_rx, now_tx, now_ts)

        return {
            "ts": round(now_ts, 1),
            "rx_mbps": rx_mbps,
            "tx_mbps": tx_mbps,
            "rx_bytes": now_rx,
            "tx_bytes": now_tx,
        }
    except Exception as e:
        raise HTTPException(500, f"SNMP 查询失败: {str(e)[:200]}")
