"""安全基线检查 — 弱口令 + 端口安全 + 合规扫描"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter(prefix="/security", tags=["security"])

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "security.db"

CHECK_ITEMS = [
    {"id": "weak_password", "name": "弱口令检测", "desc": "检查是否使用默认密码或弱密码", "severity": "high"},
    {"id": "telnet_enabled", "name": "Telnet 启用", "desc": "检查是否启用了明文 Telnet 协议", "severity": "high"},
    {"id": "ssh_v1", "name": "SSH V1 协议", "desc": "检查是否支持不安全的 SSH V1", "severity": "high"},
    {"id": "snmp_public", "name": "SNMP 默认团体字", "desc": "检查是否使用 public/private 默认团体字", "severity": "medium"},
    {"id": "http_enabled", "name": "HTTP 管理", "desc": "检查是否启用了明文 HTTP 管理", "severity": "medium"},
    {"id": "no_acl", "name": "ACL 缺失", "desc": "检查管理接口是否配置了访问控制列表", "severity": "medium"},
    {"id": "no_banner", "name": "登录横幅缺失", "desc": "检查是否配置了登录警告横幅", "severity": "low"},
    {"id": "timeout_absent", "name": "会话超时未配置", "desc": "检查闲置会话超时是否配置", "severity": "low"},
    {"id": "logging_missing", "name": "日志未配置", "desc": "检查是否配置了 syslog 远程日志", "severity": "low"},
    {"id": "ntp_missing", "name": "NTP 未配置", "desc": "检查是否配置了 NTP 时间同步", "severity": "low"},
]


def _get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS security_reports (
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


@router.get("/checks")
def list_checks():
    return CHECK_ITEMS


@router.get("/reports")
def list_reports(device_id: str = Query(default="")):
    conn = _get_db()
    if device_id:
        rows = conn.execute("SELECT * FROM security_reports WHERE device_id=? ORDER BY created_at DESC LIMIT 20", (device_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM security_reports ORDER BY created_at DESC LIMIT 50").fetchall()
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
def run_security_check(
    device_id: str = Query(...),
    device_name: str = Query(default=""),
    checks: str = Query(default="weak_password,telnet_enabled,snmp_public,http_enabled"),
):
    """执行安全基线检查（模拟）"""
    items = [c.strip() for c in checks.split(",") if c.strip()]
    results = {}
    score = 100

    # 预定义模拟结果
    mock_results = {
        "weak_password": {"pass": True, "detail": "未发现弱口令"},
        "telnet_enabled": {"pass": False, "detail": "Telnet 服务已启用，建议关闭"},
        "ssh_v1": {"pass": True, "detail": "SSH V2 正常"},
        "snmp_public": {"pass": False, "detail": "SNMP 使用 public 默认团体字"},
        "http_enabled": {"pass": False, "detail": "HTTP 管理已启用，建议改为 HTTPS"},
        "no_acl": {"pass": True, "detail": "已配置 ACL"},
        "no_banner": {"pass": True, "detail": "已配置登录横幅"},
        "timeout_absent": {"pass": False, "detail": "会话超时未设置"},
        "logging_missing": {"pass": True, "detail": "Syslog 已配置"},
        "ntp_missing": {"pass": False, "detail": "NTP 未配置"},
    }

    for item in items:
        tpl = next((t for t in CHECK_ITEMS if t["id"] == item), None)
        if not tpl:
            continue
        mock = mock_results.get(item, {"pass": True, "detail": "正常"})
        results[item] = {"name": tpl["name"], "status": "pass" if mock["pass"] else "fail", "detail": mock["detail"], "severity": tpl["severity"]}
        if not mock["pass"]:
            score -= 10 if tpl["severity"] == "high" else 5 if tpl["severity"] == "medium" else 2

    report = {
        "device_id": device_id, "device_name": device_name,
        "checks": results, "score": max(0, score),
        "passed": sum(1 for r in results.values() if r["status"] == "pass"),
        "failed": sum(1 for r in results.values() if r["status"] == "fail"),
    }

    conn = _get_db()
    conn.execute("INSERT INTO security_reports (device_id, device_name, report, score) VALUES (?,?,?,?)", (device_id, device_name, json.dumps(results, ensure_ascii=False), score))
    conn.commit()
    conn.close()
    return report
