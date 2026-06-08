"""批量命令执行 — 用设备 IP 从巡检设备库取凭证，复用 SSH/Telnet 执行器"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException

from app.api.health_check import _ssh_exec_command, _telnet_exec_command

router = APIRouter(prefix="/batch", tags=["batch"])
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "health.db"


def _get_credentials(host: str) -> dict:
    """从巡检设备库中获取指定 IP 的登录凭证"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT port, username, password, protocol FROM health_devices WHERE ip=? LIMIT 1",
        (host,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, f"设备 {host} 未在巡检设备库中找到")
    return {"host": host, "port": row["port"] or 22, "username": row["username"] or "admin",
            "password": row["password"] or "", "protocol": row["protocol"] or "ssh"}


@router.post("/execute")
async def batch_execute(
    host: str = Query(..., description="设备 IP"),
    commands: str = Query(..., description="多条命令，用换行符分隔"),
):
    """
    在指定设备上执行多条命令（依次执行）
    凭证从巡检设备库自动获取，前端只需传 IP + 命令
    """
    cred = _get_credentials(host)
    executor = _telnet_exec_command if cred["protocol"] == "telnet" else _ssh_exec_command

    cmd_list = [c.strip() for c in commands.strip().split("\n") if c.strip()]
    if not cmd_list:
        return {"ok": False, "output": "无有效命令"}

    outputs = []
    success = True

    for i, cmd in enumerate(cmd_list):
        try:
            result = await executor(cred["host"], cred["port"], cred["username"],
                                    cred["password"], cmd)
            outputs.append(f"--- [{i + 1}] {cmd} ---\n{result.strip()}")
        except Exception as e:
            outputs.append(f"--- [{i + 1}] {cmd} ---\n执行失败: {str(e)}")
            success = False

    return {"ok": success, "output": "\n\n".join(outputs)}
