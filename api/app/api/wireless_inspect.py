"""无线检测 — SSH 连接复用 + 命令并发执行（优化版）"""
from __future__ import annotations

import asyncio
import time
from typing import Any

import paramiko
from fastapi import APIRouter, Query, HTTPException

from app.api.wireless_parser import (
    WIRELESS_COMMANDS, WIRELESS_PARSERS, H3C_COMMANDS,
)

router = APIRouter(prefix="/wireless", tags=["wireless"])


INSPECT_ITEMS = [
    {"id": "ap_list", "name": "AP 设备列表", "desc": "所有AP的在线状态/型号/IP"},
    {"id": "ap_radio", "name": "AP 射频状态", "desc": "2.4G/5G射频信道/功率"},
    {"id": "client_list", "name": "客户端列表", "desc": "关联STA的MAC/IP/信号/速率"},
    {"id": "ssid_list", "name": "SSID 配置", "desc": "SSID名称/安全策略/VLAN"},
    {"id": "radio_util", "name": "信道利用率", "desc": "信道占用率/底噪"},
]


# ── 优化核心：单连接多命令并发 ──

async def _ssh_exec_batch(
    host: str, port: int, username: str, password: str,
    commands: list[str],
) -> list[str]:
    """
    一次 SSH 连接执行多条命令，结果顺序与 commands 一致。
    相比旧方案（每条命令建一次连接），减少 5×TCP+认证开销。
    """
    def _sync_batch() -> list[str]:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            host, port=port, username=username, password=password,
            timeout=10, look_for_keys=False, allow_agent=False,
        )
        results: list[str] = []
        try:
            for cmd in commands:
                try:
                    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
                    exit_code = stdout.channel.recv_exit_status()
                    out = stdout.read().decode("utf-8", errors="replace")
                    if not out:
                        out = stderr.read().decode("utf-8", errors="replace")
                    results.append(out)
                except Exception:
                    results.append("")
        finally:
            client.close()
        return results

    return await asyncio.get_event_loop().run_in_executor(None, _sync_batch)


@router.get("/items")
def list_items():
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
    vendor: str = Query(default="huawei"),
):
    """执行无线检测 — SSH 连接复用 + 命令批量执行"""
    item_ids = [i.strip() for i in items.split(",") if i.strip()]
    valid_ids = [i for i in item_ids if i in WIRELESS_COMMANDS]
    if not valid_ids:
        return {"error": "无有效采集项", "results": {}}

    cmds = H3C_COMMANDS if vendor.lower() == "h3c" else WIRELESS_COMMANDS
    commands = [cmds[i] for i in valid_ids]

    t0 = time.time()
    results: dict[str, Any] = {}
    errors = 0

    # 批量执行：一次 SSH 连接做完全部命令
    try:
        outputs = await _ssh_exec_batch(
            device_ip, device_port, username, password, commands,
        )
    except Exception as e:
        # 连接失败 → 所有项标记 error
        for item_id in valid_ids:
            results[item_id] = {
                "item_name": item_id, "level": "error",
                "message": f"SSH 连接失败: {str(e)[:100]}", "data": [],
            }
        return {
            "device_ip": device_ip, "vendor": vendor,
            "results": results, "errors": len(valid_ids),
            "elapsed_ms": round((time.time() - t0) * 1000),
        }

    # 解析每条命令的输出
    for i, item_id in enumerate(valid_ids):
        output = outputs[i] if i < len(outputs) else ""

        if not output or "Error:" in output:
            results[item_id] = {
                "item_name": item_id, "level": "warning",
                "message": "设备可能无 WLAN 模块或命令不支持", "data": [],
            }
            errors += 1
            continue

        parser = WIRELESS_PARSERS.get(item_id)
        try:
            parsed = parser(output) if parser else []
        except Exception:
            parsed = []

        item_info = next((t for t in INSPECT_ITEMS if t["id"] == item_id), None)
        name = item_info["name"] if item_info else item_id

        if item_id == "ap_list":
            online = sum(1 for ap in parsed if ap.get("status") == "online")
            level = "normal" if online == len(parsed) else "warning"
            msg = f"共 {len(parsed)} 台 AP，在线 {online}"
        elif item_id == "client_list":
            level = "normal"
            msg = f"共 {len(parsed)} 个客户端"
        else:
            level = "normal"
            msg = f"采集到 {len(parsed)} 条记录"

        results[item_id] = {
            "item_name": name, "level": level,
            "message": msg, "data": parsed,
        }

    return {
        "device_ip": device_ip, "vendor": vendor,
        "results": results, "errors": errors,
        "elapsed_ms": round((time.time() - t0) * 1000),
    }
