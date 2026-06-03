"""历史趋势查询 — SQLite 存储诊断结果"""
from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/history", tags=["diagnostics-history"])

# 数据库路径
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DB_DIR / "diagnostics.db"


def _get_db() -> sqlite3.Connection:
    """获取数据库连接（自动建表）"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS diagnostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            diagnostic_type TEXT NOT NULL,
            target TEXT NOT NULL,
            result TEXT DEFAULT '{}',
            summary TEXT DEFAULT '{}',
            status TEXT DEFAULT 'ok',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_diag_type_target
        ON diagnostics(diagnostic_type, target, created_at DESC)
    """)
    conn.commit()
    return conn


def _save_record(
    diagnostic_type: str, target: str,
    result: Dict[str, Any], summary: Dict[str, Any],
    status: str = "ok",
):
    """保存诊断记录到数据库"""
    try:
        conn = _get_db()
        conn.execute(
            "INSERT INTO diagnostics (diagnostic_type, target, result, summary, status) VALUES (?, ?, ?, ?, ?)",
            (diagnostic_type, target, json.dumps(result), json.dumps(summary), status),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # 历史记录写入失败不应阻断主流程


def _query_history(
    targets: List[str], diagnostic_type: str, days: int = 7,
) -> List[Dict[str, Any]]:
    """查询历史诊断记录"""
    conn = _get_db()
    since = (datetime.now() - timedelta(days=days)).isoformat()
    rows = []
    for target in targets:
        cursor = conn.execute(
            """SELECT * FROM diagnostics
               WHERE diagnostic_type = ? AND target = ?
               AND created_at >= ?
               ORDER BY created_at DESC
               LIMIT 100""",
            (diagnostic_type, target, since),
        )
        for r in cursor.fetchall():
            row = dict(r)
            try:
                row["result"] = json.loads(row.get("result", "{}"))
                row["summary"] = json.loads(row.get("summary", "{}"))
            except (json.JSONDecodeError, TypeError):
                row["result"] = {}
                row["summary"] = {}
            rows.append(row)
    conn.close()
    return rows


@router.get("", summary="历史趋势查询")
def get_history(
    targets: str = Query(..., description="目标列表，逗号分隔"),
    diagnostic_type: str = Query(default="ping", description="诊断类型"),
    days: int = Query(default=7, ge=1, le=90),
):
    """查询指定诊断类型的历史趋势数据"""
    target_list = [t.strip() for t in targets.split(",") if t.strip()]
    if not target_list:
        raise HTTPException(400, "至少需要一个目标")
    if diagnostic_type not in ("ping", "traceroute", "dns", "tcp-port", "http", "jitter"):
        raise HTTPException(400, f"不支持的诊断类型: {diagnostic_type}")

    records = _query_history(target_list, diagnostic_type, days)
    return {"records": records, "targets": target_list, "type": diagnostic_type, "days": days}


@router.get("/save", summary="手动保存诊断记录")
def save_record(
    diagnostic_type: str = Query(...),
    target: str = Query(...),
    avg_rtt: float = Query(default=0),
    loss_percent: float = Query(default=0),
    status: str = Query(default="ok"),
):
    """手动保存一条诊断记录（供前端调用）"""
    _save_record(
        diagnostic_type=diagnostic_type,
        target=target,
        result={"avg_rtt": avg_rtt, "loss_percent": loss_percent},
        summary={"avg_rtt": avg_rtt, "loss_percent": loss_percent, "status": status},
        status=status,
    )
    return {"ok": True}
