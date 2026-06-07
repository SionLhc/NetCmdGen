"""配置备份 — SSH 抓取运行配置 + diff 对比"""
from __future__ import annotations

import difflib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException

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
    """保存一次配置备份"""
    conn = _get_db()
    conn.execute("INSERT INTO backups (device_id, device_name, config) VALUES (?,?,?)", (device_id, device_name, config))
    conn.commit()
    bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"ok": True, "id": bid, "size": len(config)}


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
