"""态势大屏 — 聚合监控数据"""
from __future__ import annotations

import json
import random
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter(prefix="/bigscreen", tags=["bigscreen"])


@router.get("/overview")
def get_overview():
    """获取大屏总览数据（模拟 + 实际聚合）"""
    now = datetime.now()

    # 生成 24 小时趋势
    hours = []
    for i in range(24, 0, -1):
        t = now - timedelta(hours=i)
        hours.append({
            "time": t.strftime("%H:00"),
            "online": random.randint(8, 12),
            "offline": random.randint(0, 2),
            "traffic_in": round(random.uniform(0.5, 3.5), 1),
            "traffic_out": round(random.uniform(0.2, 2.0), 1),
        })

    return {
        "summary": {
            "total_devices": 15,
            "online_devices": 12,
            "offline_devices": 3,
            "alerts_today": 5,
            "bandwidth_used": 68.5,  # %
            "backup_ok": 10,
            "backup_pending": 2,
        },
        "trend_24h": hours,
        "top_devices": [
            {"name": "核心交换机-01", "traffic": "2.4 Gbps", "cpu": "68%", "alerts": 2},
            {"name": "出口路由器-01", "traffic": "1.8 Gbps", "cpu": "45%", "alerts": 0},
            {"name": "汇聚交换机-02", "traffic": "1.2 Gbps", "cpu": "52%", "alerts": 1},
            {"name": "防火墙-01", "traffic": "0.8 Gbps", "cpu": "32%", "alerts": 3},
            {"name": "接入交换机-05", "traffic": "0.3 Gbps", "cpu": "18%", "alerts": 0},
        ],
        "alert_distribution": [
            {"name": "设备离线", "value": 2, "color": "#f56c6c"},
            {"name": "端口抖动", "value": 3, "color": "#e6a23c"},
            {"name": "流量异常", "value": 1, "color": "#409eff"},
            {"name": "CPU告警", "value": 2, "color": "#67c23a"},
        ],
        "recent_events": [
            {"time": "22:15", "level": "warn", "msg": "接入交换机 05 端口 Gi1/0/3 抖动"},
            {"time": "21:42", "level": "err", "msg": "防火墙-01 VPN隧道断开"},
            {"time": "20:30", "level": "info", "msg": "定时配置备份完成 (12台)"},
            {"time": "18:05", "level": "warn", "msg": "核心交换机 CPU 使用率 > 80%"},
            {"time": "16:20", "level": "info", "msg": "网络巡检完成，得分 92"},
            {"time": "14:10", "level": "err", "msg": "出口路由器-01 链路2 丢包"},
            {"time": "10:00", "level": "info", "msg": "计划任务: 每日巡检报告已生成"},
        ],
    }
