"""网络巡检 — 模板化巡检 + 报告生成"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter(prefix="/health", tags=["health"])

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "health.db"

CHECK_TEMPLATES = [
    {"id": "ping", "name": "Ping 连通性", "desc": "ICMP Ping 目标地址"},
    {"id": "cpu", "name": "CPU 使用率", "desc": "检查CPU是否超阈值"},
    {"id": "memory", "name": "内存使用率", "desc": "检查内存使用率"},
    {"id": "disk", "name": "磁盘/Flash", "desc": "检查存储空间"},
    {"id": "temperature", "name": "温度", "desc": "检查设备温度"},
    {"id": "fan", "name": "风扇状态", "desc": "检查风扇运转"},
    {"id": "power", "name": "电源状态", "desc": "检查电源模块"},
    {"id": "interface", "name": "接口状态", "desc": "关键接口up/down"},
    {"id": "ospf", "name": "OSPF邻居", "desc": "OSPF邻居状态"},
    {"id": "bgp", "name": "BGP邻居", "desc": "BGP邻居状态"},
]


def _get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT DEFAULT '',
            device_name TEXT DEFAULT '',
            report TEXT DEFAULT '{}',
            score INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


@router.get("/templates")
def list_templates():
    """巡检模板列表"""
    return CHECK_TEMPLATES


@router.get("/reports")
def list_reports(device_id: str = Query(default="")):
    """巡检报告列表"""
    conn = _get_db()
    if device_id:
        rows = conn.execute("SELECT * FROM health_reports WHERE device_id=? ORDER BY created_at DESC LIMIT 20", (device_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM health_reports ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["report"] = json.loads(d.get("report", "{}"))
        except (json.JSONDecodeError, TypeError):
            d["report"] = {}
        result.append(d)
    return result


@router.post("/run")
def run_health_check(
    device_id: str = Query(...),
    device_name: str = Query(default=""),
    checks: str = Query(default="ping,cpu,memory,interface", description="逗号分隔的检查项"),
):
    """执行一次巡检（模拟，实际需SSH）"""
    items = [c.strip() for c in checks.split(",") if c.strip()]
    results = {}
    score = 100

    for item in items:
        tpl = next((t for t in CHECK_TEMPLATES if t["id"] == item), None)
        if not tpl:
            continue
        ok = True  # 模拟：全部通过
        results[item] = {"name": tpl["name"], "status": "pass" if ok else "fail", "detail": "正常" if ok else "异常"}
        if not ok:
            score -= 10

    report = {
        "device_id": device_id,
        "device_name": device_name,
        "checks": results,
        "score": max(0, score),
        "passed": sum(1 for r in results.values() if r["status"] == "pass"),
        "failed": sum(1 for r in results.values() if r["status"] == "fail"),
    }

    conn = _get_db()
    conn.execute("INSERT INTO health_reports (device_id, device_name, report, score) VALUES (?,?,?,?)", (device_id, device_name, json.dumps(results, ensure_ascii=False), score))
    conn.commit()
    conn.close()
    return report
