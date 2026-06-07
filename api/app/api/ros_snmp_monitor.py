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
    """SNMP GET — pysnmp 7.x 返回 tuple, timeout 改为 1.5 秒"""
    result = await get_cmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        await UdpTransportTarget.create((host, port), timeout=1.5, retries=0),
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
    """SNMP WALK — 小批次并行查询"""
    async def fetch_one(idx: int) -> tuple[int, str]:
        try:
            val = await _snmp_get(host, community, f"{base_oid}.{idx}", port)
            if val and val.strip():
                return (idx, val)
        except Exception:
            pass
        return (idx, "")

    # 每批 5 个并发，批间休息 0.3 秒，避免压垮设备
    result = {}
    for batch_start in range(1, 31, 5):
        batch_indices = list(range(batch_start, min(batch_start + 5, 31)))
        tasks = [fetch_one(i) for i in batch_indices]
        results = await asyncio.gather(*tasks)
        hit = False
        for idx, val in results:
            if val:
                result[idx] = val
                hit = True
        # 连续两批都没结果 → 已到尾
        if not hit and batch_start > 5:
            break
        await asyncio.sleep(0.3)

    return result


@router.get("/interfaces")
async def list_interfaces(
    host: str = Query(...),
    community: str = Query(default="public"),
    port: int = Query(default=161),
):
    """获取设备接口列表 — 并行查询 name + speed"""
    try:
        # name 和 speed 并行查询
        names, speeds = await asyncio.gather(
            _snmp_walk(host, community, IF_NAME, port),
            _snmp_walk(host, community, IF_SPEED, port),
        )
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

# ─── 后台自治轮询 — 取代前端驱动的 setInterval ────────────────
# 设计思路：后端自主采集，前端只被动读缓存，彻底解决浏览器 Tab 后台冻结导致图表停更的问题

_collector_task: asyncio.Task | None = None
_collector_registry: dict[str, dict] = {}  # device_id -> {host, community, port, interfaces:[idx]}


class SnmpCollectorStats:
    """采集器统计信息"""
    total_devices: int = 0
    total_polls: int = 0
    errors: int = 0
    last_poll_ts: float = 0


_collector_stats = SnmpCollectorStats()


async def _poll_all_devices():
    """对所有已注册设备执行一轮 SNMP 采集"""
    global _collector_stats
    now_ts = time.time()

    for device_id, cfg in list(_collector_registry.items()):
        host = cfg["host"]
        community = cfg.get("community", "public")
        port = cfg.get("port", 161)
        if_indices = cfg.get("interfaces", [1])

        for if_idx in if_indices:
            try:
                rx_str = await _snmp_get(host, community, f"{IF_IN_OCTETS}.{if_idx}", port)
                tx_str = await _snmp_get(host, community, f"{IF_OUT_OCTETS}.{if_idx}", port)
                now_rx = int(rx_str) if rx_str else 0
                now_tx = int(tx_str) if tx_str else 0

                cache_key = f"{host}:{if_idx}"
                if cache_key in _snapshot_cache:
                    last_rx, last_tx, last_ts = _snapshot_cache[cache_key]
                    elapsed = now_ts - last_ts
                    if elapsed > 0:
                        rx_bytes = max(0, now_rx - last_rx)
                        tx_bytes = max(0, now_tx - last_tx)
                        if now_rx < last_rx:
                            rx_bytes = (2**32 - last_rx) + now_rx
                        if now_tx < last_tx:
                            tx_bytes = (2**32 - last_tx) + now_tx
                        # 存入最新速率值
                        cfg.setdefault("latest", {})
                        cfg["latest"][if_idx] = {
                            "ts": round(now_ts, 1),
                            "rx_mbps": round((rx_bytes * 8) / elapsed / 1_000_000, 2),
                            "tx_mbps": round((tx_bytes * 8) / elapsed / 1_000_000, 2),
                            "rx_bytes": now_rx,
                            "tx_bytes": now_tx,
                        }

                _snapshot_cache[cache_key] = (now_rx, now_tx, now_ts)
                _collector_stats.total_polls += 1

            except Exception:
                _collector_stats.errors += 1

    _collector_stats.last_poll_ts = now_ts


async def _collector_loop(poll_interval: float = 3.0):
    """采集主循环 — 持久运行，永不停止"""
    global _collector_stats
    while True:
        try:
            await _poll_all_devices()
        except Exception:
            pass
        await asyncio.sleep(poll_interval)


def start_collector(poll_interval: float = 3.0):
    """启动后台采集任务"""
    global _collector_task
    if _collector_task and not _collector_task.done():
        return
    _collector_task = asyncio.create_task(_collector_loop(poll_interval))
    print(f"[SNMP Collector] 后台采集已启动，间隔 {poll_interval}s")


def stop_collector():
    """停止后台采集任务"""
    global _collector_task
    if _collector_task:
        _collector_task.cancel()
        _collector_task = None
        print("[SNMP Collector] 后台采集已停止")


@router.post("/collector/register")
async def register_device(
    device_id: str = Query(...),
    host: str = Query(...),
    community: str = Query(default="public"),
    port: int = Query(default=161),
    interfaces: str = Query(default="1", description="逗号分隔的接口索引"),
):
    """注册设备到后台采集器"""
    if_list = [int(x.strip()) for x in interfaces.split(",") if x.strip()]
    _collector_registry[device_id] = {
        "host": host, "community": community, "port": port,
        "interfaces": if_list, "latest": {},
    }
    return {"ok": True, "device_id": device_id, "interfaces": len(if_list)}


@router.post("/collector/unregister")
async def unregister_device(device_id: str = Query(...)):
    """从采集器移除设备"""
    if device_id in _collector_registry:
        del _collector_registry[device_id]
    return {"ok": True}


@router.get("/collector/stats")
async def collector_stats():
    """采集器统计"""
    return {
        "devices": len(_collector_registry),
        "total_polls": _collector_stats.total_polls,
        "errors": _collector_stats.errors,
        "last_poll_ts": _collector_stats.last_poll_ts,
        "running": _collector_task is not None and not _collector_task.done(),
    }


@router.get("/collector/snapshot")
async def collector_snapshot(device_id: str = Query(...)):
    """从采集器缓存读取最新快照（前端被动读）"""
    cfg = _collector_registry.get(device_id)
    if not cfg:
        return {"ok": False, "error": "设备未注册"}
    return {"ok": True, "data": cfg.get("latest", {}), "ts": _collector_stats.last_poll_ts}


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
