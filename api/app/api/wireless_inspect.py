"""无线检测 — SSH 采集 AP/射频/客户端/SSID 信息"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from fastapi import APIRouter, Query, HTTPException

from app.api.health_check import _ssh_exec_command
from app.api.wireless_parser import (
    WIRELESS_COMMANDS,
    WIRELESS_PARSERS,
    H3C_COMMANDS,
)

router = APIRouter(prefix="/wireless", tags=["wireless"])


# ── 采集项定义 ──

INSPECT_ITEMS = [
    {"id": "ap_list", "name": "AP 设备列表", "desc": "所有AP的在线状态/型号/IP"},
    {"id": "ap_radio", "name": "AP 射频状态", "desc": "2.4G/5G射频信道/功率"},
    {"id": "client_list", "name": "客户端列表", "desc": "关联STA的MAC/IP/信号/速率"},
    {"id": "ssid_list", "name": "SSID 配置", "desc": "SSID名称/安全策略/VLAN"},
    {"id": "radio_util", "name": "信道利用率", "desc": "信道占用率/底噪"},
]


@router.get("/items")
def list_items():
    """无线采集项列表"""
    result = []
    for item in INSPECT_ITEMS:
        d = dict(item)
        d["command"] = WIRELESS_COMMANDS.get(item["id"], "")
        result.append(d)
    return result


@router.post("/inspect")
async def inspect_wireless(
    device_ip: str = Query(...),
    device_port: int = Query(default=22),
    username: str = Query(...),
    password: str = Query(...),
    items: str = Query(default="ap_list,ap_radio,client_list,ssid_list,radio_util"),
    vendor: str = Query(default="huawei", description="huawei / h3c"),
):
    """执行无线检测 — SSH登录AC执行WLAN命令并解析"""
    item_ids = [i.strip() for i in items.split(",") if i.strip()]
    # 过滤有效采集项
    valid_ids = [i for i in item_ids if i in WIRELESS_COMMANDS]
    if not valid_ids:
        return {"error": "无有效采集项", "results": {}}

    # 选命令集（华为 / 华三）
    cmds = H3C_COMMANDS if vendor.lower() == "h3c" else WIRELESS_COMMANDS

    results: dict[str, Any] = {}
    t0 = time.time()
    errors = 0

    for item_id in valid_ids:
        command = cmds[item_id]
        try:
            output = await _ssh_exec_command(
                device_ip, device_port, username, password, command
            )
        except Exception as e:
            results[item_id] = {
                "item_name": item_id,
                "level": "error",
                "message": f"SSH 失败: {str(e)[:100]}",
                "data": [],
            }
            errors += 1
            continue

        # 检查命令是否有效（无 WLAN 模块则返回空）
        if not output or "Error:" in output:
            results[item_id] = {
                "item_name": item_id,
                "level": "warning",
                "message": "设备可能无 WLAN 模块或命令不支持",
                "data": [],
            }
            errors += 1
            continue

        # 解析
        parser = WIRELESS_PARSERS.get(item_id)
        if parser:
            try:
                parsed = parser(output)
            except Exception:
                parsed = []
        else:
            parsed = []

        # 统计
        item_info = next((t for t in INSPECT_ITEMS if t["id"] == item_id), None)
        name = item_info["name"] if item_info else item_id
        if item_id == "ap_list":
            online = sum(1 for ap in parsed if ap.get("status") == "online")
            offline = len(parsed) - online
            level = "normal" if offline == 0 else "warning"
            msg = f"共 {len(parsed)} 台 AP，在线 {online}，离线 {offline}"
        elif item_id == "client_list":
            level = "normal"
            msg = f"共 {len(parsed)} 个客户端"
        else:
            level = "normal"
            msg = f"采集到 {len(parsed)} 条记录"

        results[item_id] = {
            "item_name": name,
            "level": level,
            "message": msg,
            "data": parsed,
        }

    elapsed = round((time.time() - t0) * 1000)

    return {
        "device_ip": device_ip,
        "vendor": vendor,
        "results": results,
        "errors": errors,
        "elapsed_ms": elapsed,
    }
