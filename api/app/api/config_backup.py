"""配置备份 — SSH/Telnet 抓取运行配置 + diff 对比"""
from __future__ import annotations

import asyncio
import difflib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/backup", tags=["backup"])

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "backup.db"


def _get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            device_name TEXT DEFAULT '',
            config TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


@router.get("")
def list_backups(device_id: str = Query(default="")):
    """获取备份列表"""
    conn = _get_db()
    if device_id:
        rows = conn.execute("SELECT id, device_id, device_name, LENGTH(config) as config_size, created_at FROM backups WHERE device_id=? ORDER BY created_at DESC LIMIT 20", (device_id,)).fetchall()
    else:
        rows = conn.execute("SELECT id, device_id, device_name, LENGTH(config) as config_size, created_at FROM backups ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/{backup_id}")
def get_backup(backup_id: int):
    """获取某次备份的完整配置"""
    conn = _get_db()
    row = conn.execute("SELECT * FROM backups WHERE id=?", (backup_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "备份不存在")
    return dict(row)


@router.post("")
def create_backup(
    device_id: str = Query(...),
    device_name: str = Query(default=""),
    config: str = Query(default=""),
):
    """手动保存一次配置备份（前端传 config 内容）"""
    conn = _get_db()
    conn.execute("INSERT INTO backups (device_id, device_name, config) VALUES (?,?,?)", (device_id, device_name, config))
    conn.commit()
    bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"ok": True, "id": bid, "size": len(config)}


@router.post("/fetch")
async def fetch_and_backup(
    host: str = Query(..., description="设备 IP"),
):
    """
    从设备 SSH/Telnet 抓取运行配置并自动保存
    凭证从巡检设备库自动获取
    """
    import sqlite3
    DB_DIR = Path(__file__).parent.parent / "data"

    # 从巡检设备库获取凭证
    cred_conn = sqlite3.connect(str(DB_DIR / "health.db"))
    cred_conn.row_factory = sqlite3.Row
    row = cred_conn.execute(
        "SELECT name,port,username,password,protocol FROM health_devices WHERE ip=? LIMIT 1",
        (host,),
    ).fetchone()
    cred_conn.close()

    if not row:
        raise HTTPException(404, f"设备 {host} 未在巡检设备库中找到，请先在「网络巡检→设备管理」中添加")

    from app.api.health_check import _ssh_exec_command, _telnet_exec_command
    executor = _telnet_exec_command if row["protocol"] == "telnet" else _ssh_exec_command

    try:
        config = await executor(host, row["port"], row["username"], row["password"],
                                "display current-configuration")
    except Exception as e:
        raise HTTPException(500, f"抓取配置失败: {str(e)}")

    if not config or len(config.strip()) < 10:
        raise HTTPException(500, "抓取到的配置为空或过短，请检查设备连接")

    # 保存到备份库
    device_name = row["name"] or host
    conn = _get_db()
    conn.execute("INSERT INTO backups (device_id, device_name, config) VALUES (?,?,?)",
                 (host, device_name, config))
    conn.commit()
    bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    return {"ok": True, "id": bid, "device_name": device_name, "size": len(config)}


@router.get("/download/{backup_id}")
def download_backup(backup_id: int):
    """下载某次备份的完整配置为文本文件"""
    conn = _get_db()
    row = conn.execute("SELECT * FROM backups WHERE id=?", (backup_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "备份不存在")
    r = dict(row)
    filename = f"{r['device_name'] or r['device_id']}_{r['created_at'][:10].replace('-','')}.cfg"
    return PlainTextResponse(
        content=r["config"],
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/diff")
def diff_backups(id_a: int = Query(...), id_b: int = Query(...)):
    """对比两次备份的差异"""
    conn = _get_db()
    a = conn.execute("SELECT * FROM backups WHERE id=?", (id_a,)).fetchone()
    b = conn.execute("SELECT * FROM backups WHERE id=?", (id_b,)).fetchone()
    conn.close()
    if not a or not b:
        raise HTTPException(404, "备份不存在")

    diff = list(difflib.unified_diff(
        dict(a)["config"].splitlines(),
        dict(b)["config"].splitlines(),
        fromfile=f"{dict(a)['device_name']} @ {dict(a)['created_at']}",
        tofile=f"{dict(b)['device_name']} @ {dict(b)['created_at']}",
        lineterm="",
    ))
    return {"id_a": id_a, "id_b": id_b, "diff": diff, "added": sum(1 for l in diff if l.startswith('+') and not l.startswith('+++')), "removed": sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))}
