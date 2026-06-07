"""企业微信/DingTalk Webhook 告警推送"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter(prefix="/alert", tags=["alert"])

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "alert.db"


def _get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alert_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT '',
            alert_type TEXT NOT NULL DEFAULT 'device_offline',
            target TEXT DEFAULT '',
            threshold TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1,
            webhook_url TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER NOT NULL,
            rule_name TEXT DEFAULT '',
            message TEXT DEFAULT '',
            level TEXT DEFAULT 'warning',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


ALERT_TYPES = [
    {"id": "device_offline", "name": "设备离线", "icon": "🔴"},
    {"id": "port_flap", "name": "端口抖动", "icon": "🟡"},
    {"id": "traffic_spike", "name": "流量异常", "icon": "📈"},
    {"id": "cpu_high", "name": "CPU过载", "icon": "⚡"},
    {"id": "memory_high", "name": "内存不足", "icon": "🧠"},
    {"id": "config_change", "name": "配置变更", "icon": "📝"},
]


@router.get("/types")
def list_alert_types():
    return ALERT_TYPES


@router.get("/rules")
def list_rules():
    conn = _get_db()
    rows = conn.execute("SELECT * FROM alert_rules ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/rules")
def create_rule(
    name: str = Query(...),
    alert_type: str = Query(default="device_offline"),
    target: str = Query(default=""),
    threshold: str = Query(default=""),
    webhook_url: str = Query(default=""),
):
    conn = _get_db()
    conn.execute("INSERT INTO alert_rules (name, alert_type, target, threshold, webhook_url) VALUES (?,?,?,?,?)", (name, alert_type, target, threshold, webhook_url))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int):
    conn = _get_db()
    conn.execute("DELETE FROM alert_rules WHERE id=?", (rule_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/history")
def list_history(limit: int = Query(default=50)):
    conn = _get_db()
    rows = conn.execute("SELECT * FROM alert_history ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/test")
def test_webhook(webhook_url: str = Query(...), message: str = Query(default="这是 NetCmdGen 告警测试")):
    """测试 Webhook 推送"""
    import json as j
    payload = {
        "msgtype": "text",
        "text": {"content": f"[NetCmdGen 告警]\n{message}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
    }
    # 实际调用 HTTP POST
    try:
        import urllib.request
        req = urllib.request.Request(webhook_url, data=j.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
        return {"ok": True, "message": "推送成功"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
