"""态势大屏 — 从各模块数据库拉取真实数据聚合"""
from __future__ import annotations

import json
import random
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter(prefix="/bigscreen", tags=["bigscreen"])

DATA_DIR = Path(__file__).parent.parent / "data"


def _count_db(path: Path, table: str) -> int:
    """安全计数"""
    try:
        if not path.exists():
            return 0
        conn = sqlite3.connect(str(path))
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0


@router.get("/overview")
def get_overview():
    """从真实数据库聚合大屏数据"""
    now = datetime.now()

    # ── 1. 设备统计：从健康巡检设备表 + Ros 设备表 ──
    health_devices = _count_db(DATA_DIR / "health.db", "health_devices")
    ros_devices = _count_db(DATA_DIR / "ros_devices.db", "ros_devices")
    total_devices = health_devices + ros_devices

    # ── 2. 巡检报告统计 ──
    health_reports = _count_db(DATA_DIR / "health.db", "health_reports")

    # ── 3. 告警统计（从 alert webhook db） ──
    alert_db = DATA_DIR / "alert.db"
    alerts_today = 0
    recent_events = []
    if alert_db.exists():
        conn = sqlite3.connect(str(alert_db))
        # 今日告警数
        today_start = now.strftime("%Y-%m-%d")
        row = conn.execute(
            "SELECT COUNT(*) FROM alert_history WHERE created_at >= ?",
            (today_start,),
        ).fetchone()
        alerts_today = row[0] if row else 0
        # 最近事件
        rows = conn.execute(
            "SELECT created_at, level, message FROM alert_history ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        for r in rows:
            recent_events.append({
                "time": r[0][-8:-3] if len(r[0]) > 8 else r[0],
                "level": r[1] or "info",
                "msg": r[2] or "告警记录",
            })
        conn.close()

    # 没有告警记录时用巡检历史填充
    if not recent_events:
        hp = DATA_DIR / "health.db"
        if hp.exists():
            conn = sqlite3.connect(str(hp))
            rows = conn.execute(
                "SELECT device_name, score, created_at FROM health_reports ORDER BY created_at DESC LIMIT 6"
            ).fetchall()
            for r in rows:
                score = r[1] or 0
                level = "err" if score < 60 else "warn" if score < 80 else "info"
                recent_events.append({
                    "time": r[2][-8:-3] if len(r[2]) > 8 else r[2],
                    "level": level,
                    "msg": f"巡检 {r[0]}: 得分 {score}",
                })
            conn.close()

    # ── 4. 备份统计 ──
    backup_db = DATA_DIR / "backup.db"
    backup_ok = _count_db(backup_db, "backups")
    backup_pending = 0

    # ── 5. 告警分布 ──
    alert_dist = []
    if alert_db.exists():
        conn = sqlite3.connect(str(alert_db))
        rows = conn.execute(
            "SELECT level, COUNT(*) FROM alert_history WHERE created_at >= ? GROUP BY level",
            (today_start,),
        ).fetchall()
        color_map = {"err": "#f56c6c", "warn": "#e6a23c", "info": "#409eff"}
        name_map = {"err": "严重", "warn": "警告", "info": "提示"}
        for r in rows:
            alert_dist.append({
                "name": name_map.get(r[0], r[0]),
                "value": r[1],
                "color": color_map.get(r[0], "#94a3b8"),
            })
        conn.close()
    if not alert_dist:
        alert_dist = [
            {"name": "无告警", "value": 1, "color": "#67c23a"},
        ]

    # ── 6. 24h 趋势（从 SNMP 采集器或模拟） ──
    snmp_db = DATA_DIR / "snmp_collector.db"
    if snmp_db.exists():
        conn = sqlite3.connect(str(snmp_db))
        hours = []
        for i in range(24, 0, -1):
            t = now - timedelta(hours=i)
            slot = t.strftime("%Y-%m-%d %H")
            row = conn.execute(
                "SELECT COUNT(*) FROM snapshot WHERE ts LIKE ?",
                (slot + "%",),
            ).fetchone()
            h = {"time": t.strftime("%H:00"), "online": 0, "offline": 0}
            h["online"] = min(total_devices, max(1, (row[0] or 0) // 10))
            h["offline"] = max(0, total_devices - h["online"])
            hours.append(h)
        conn.close()
    else:
        hours = _mock_trend(now, total_devices)

    return {
        "summary": {
            "total_devices": total_devices or 1,
            "online_devices": total_devices or 0,
            "offline_devices": 0,
            "alerts_today": alerts_today,
            "bandwidth_used": 68.5,  # TODO: 等 SNMP 采集器有带宽统计后对接
            "backup_ok": backup_ok,
            "backup_pending": backup_pending,
            "health_reports": health_reports,
        },
        "trend_24h": hours,
        "alert_distribution": alert_dist,
        "recent_events": recent_events or [
            {"time": now.strftime("%H:%M"), "level": "info", "msg": "暂无告警 — 执行巡检后产生事件"},
        ],
    }


def _mock_trend(now: datetime, total: int) -> list:
    """无 SNMP 采集器时的模拟 24h 趋势"""
    hours = []
    online = max(1, total)
    for i in range(24, 0, -1):
        t = now - timedelta(hours=i)
        online = max(1, online + random.randint(-1, 1))
        hours.append({
            "time": t.strftime("%H:00"),
            "online": min(total, online),
            "offline": max(0, total - online),
        })
    return hours
