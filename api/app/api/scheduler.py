"""计划任务 — APScheduler 定时备份/巡检"""
from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "scheduler.db"

TASK_TYPES = {
    "backup": {"name": "配置备份", "icon": "💾"},
    "health": {"name": "网络巡检", "icon": "🔍"},
    "report": {"name": "报告导出", "icon": "📄"},
    "custom": {"name": "自定义命令", "icon": "⚙️"},
}


def _get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT '',
            task_type TEXT NOT NULL DEFAULT 'custom',
            cron_expr TEXT DEFAULT '0 3 * * *',
            device_ids TEXT DEFAULT '',
            extra TEXT DEFAULT '{}',
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            status TEXT DEFAULT 'success',
            output TEXT DEFAULT '',
            duration_ms REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)
    conn.commit()
    return conn


@router.get("/tasks")
def list_tasks():
    """任务列表"""
    conn = _get_db()
    rows = conn.execute("SELECT * FROM tasks ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/tasks")
def create_task(
    name: str = Query(...),
    task_type: str = Query(default="custom"),
    cron_expr: str = Query(default="0 3 * * *"),
    device_ids: str = Query(default=""),
    extra: str = Query(default="{}"),
):
    """创建计划任务"""
    conn = _get_db()
    conn.execute("INSERT INTO tasks (name, task_type, cron_expr, device_ids, extra) VALUES (?,?,?,?,?)", (name, task_type, cron_expr, device_ids, extra))
    conn.commit()
    tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"ok": True, "id": tid}


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = _get_db()
    conn.execute("DELETE FROM task_logs WHERE task_id=?", (task_id,))
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.put("/tasks/{task_id}/toggle")
def toggle_task(task_id: int):
    conn = _get_db()
    conn.execute("UPDATE tasks SET enabled = CASE WHEN enabled=1 THEN 0 ELSE 1 END WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/logs")
def list_logs(task_id: int = Query(default=0), limit: int = Query(default=50)):
    """执行日志"""
    conn = _get_db()
    if task_id:
        rows = conn.execute("SELECT * FROM task_logs WHERE task_id=? ORDER BY created_at DESC LIMIT ?", (task_id, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM task_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
