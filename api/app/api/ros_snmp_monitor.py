"""
ROS SNMP 流量监控 — 轮询接口字节计数 → 计算速率 → SSE 推流
基于 pysnmp，纯只读操作，不碰设备配置
"""

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

# 接口 OID 模板
IF_IN_OCTETS = "1.3.6.1.2.1.2.2.1.10"    # ifInOctets
IF_OUT_OCTETS = "1.3.6.1.2.1.2.2.1.16"   # ifOutOctets
IF_NAME = "1.3.6.1.2.1.2.2.1.2"            # ifDescr
IF_SPEED = "1.3.6.1.2.1.2.2.1.5"           # ifSpeed


async def _snmp_get(host: str, community: str, oid: str,
                    port: int = 161) -> str:
    """SNMP GET 单个 OID"""
    iterator = get_cmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        await UdpTransportTarget.create((host, port), timeout=2, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    err_ind, err_status, err_idx, var_binds = await iterator
    if err_ind:
        raise ConnectionError(f"SNMP 错误: {err_ind}")
    if err_status:
        raise ConnectionError(f"SNMP 状态错误: {err_status.prettyPrint()}")
    for vb in var_binds:
        return str(vb[1])
    return "0"


async def _snmp_walk(host: str, community: str, base_oid: str,
                     port: int = 161) -> dict[int, str]:
    """SNMP WALK 获取某 OID 下所有接口的值，返回 {ifIndex: value}"""
    
    result = {}
    iterator = next_cmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        await UdpTransportTarget.create((host, port), timeout=3, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(base_oid)),
        lexicographicMode=False,
    )
    async for err_ind, err_status, err_idx, var_binds in iterator:
        if err_ind or err_status:
            break
        for vb in var_binds:
            oid_str = str(vb[0])
            idx = int(oid_str.split(".")[-1]) if "." in oid_str else 0
            result[idx] = str(vb[1])
    return result


@router.get("/interfaces")
async def list_interfaces(
    host: str = Query(...),
    community: str = Query(default="public"),
    port: int = Query(default=161),
):
    """获取设备接口列表及当前速率"""
    try:
        names = await _snmp_walk(host, community, IF_NAME, port)
        speeds = await _snmp_walk(host, community, IF_SPEED, port)
        result = []
        for idx, name in names.items():
            result.append({
                "index": idx,
                "name": name,
                "speed": int(speeds.get(idx, "0")),
                "speed_label": f"{int(speeds.get(idx, '0')) // 1_000_000} Mbps"
                if int(speeds.get(idx, "0")) else "",
            })
        return sorted(result, key=lambda x: x["index"])
    except Exception as e:
        raise HTTPException(500, f"SNMP 查询失败: {e}")


@router.get("/stream")
async def traffic_stream(
    host: str = Query(...),
    if_index: int = Query(default=1, description="接口索引"),
    community: str = Query(default="public"),
    port: int = Query(default=161),
    interval_ms: int = Query(default=1000, ge=200, le=5000),
    duration_s: int = Query(default=60, le=300),
):
    """
    SSE 实时流量推送
    每 interval_ms 毫秒轮询一次 SNMP byte 计数器，计算速率差值
    """
    async def generator() -> AsyncGenerator[str, None]:
        prev_rx = 0
        prev_tx = 0
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

                # 计算带宽 (bytes/s → Mbps)
                elapsed = now_ts - prev_ts
                rx_bytes = max(0, now_rx - prev_rx)  # 处理32位计数器回绕
                tx_bytes = max(0, now_tx - prev_tx)
                rx_mbps = round((rx_bytes * 8) / elapsed / 1_000_000, 2)
                tx_mbps = round((tx_bytes * 8) / elapsed / 1_000_000, 2)

                prev_rx, prev_ts = now_rx, now_ts
                prev_tx = now_tx

                payload = json.dumps({
                    "ts": round(now_ts, 1),
                    "rx_mbps": rx_mbps,
                    "tx_mbps": tx_mbps,
                    "rx_total_bytes": now_rx,
                    "tx_total_bytes": now_tx,
                }, ensure_ascii=False)
                yield f"data: {payload}\n\n"

            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)[:200]}, ensure_ascii=False)}\n\n"
                return

            await asyncio.sleep(interval_ms / 1000)

        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
