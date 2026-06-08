"""网络巡检 — SSH 真实执行 + 华为命令解析"""
from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import paramiko
from fastapi import APIRouter, Query, HTTPException

from app.api.inspection_engine import InspectionEngine, MAX_CONCURRENT
from app.api.inspection_parser import parse_item, is_command_error

router = APIRouter(prefix="/health", tags=["health"])

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "health.db"

CHECK_TEMPLATES = [
    # ── 硬件状态 ──
    {"id": "设备基本信息", "name": "设备基本信息", "desc": "设备型号/版本/运行时间", "category": "硬件状态"},
    {"id": "CPU使用率", "name": "CPU 使用率", "desc": "检查CPU是否超阈值", "category": "硬件状态"},
    {"id": "内存使用率", "name": "内存使用率", "desc": "检查内存使用率", "category": "硬件状态"},
    {"id": "温度状态", "name": "温度", "desc": "检查设备温度", "category": "硬件状态"},
    {"id": "风扇状态", "name": "风扇状态", "desc": "检查风扇运转", "category": "硬件状态"},
    {"id": "电源状态", "name": "电源状态", "desc": "检查电源模块", "category": "硬件状态"},
    # ── 接口与网络 ──
    {"id": "接口状态", "name": "接口状态", "desc": "关键接口up/down", "category": "接口与网络"},
    {"id": "接口错包", "name": "接口错包", "desc": "检查接口错误计数", "category": "接口与网络"},
    {"id": "VLAN信息", "name": "VLAN 信息", "desc": "VLAN 配置", "category": "接口与网络"},
    {"id": "路由表", "name": "路由表", "desc": "路由条目统计", "category": "接口与网络"},
    {"id": "ARP表", "name": "ARP 表", "desc": "ARP 条目数", "category": "接口与网络"},
    {"id": "MAC地址表", "name": "MAC 地址表", "desc": "MAC 地址学习数", "category": "接口与网络"},
    # ── 协议状态 ──
    {"id": "STP状态", "name": "STP 状态", "desc": "生成树端口状态", "category": "协议状态"},
    {"id": "链路聚合", "name": "链路聚合", "desc": "Eth-Trunk 状态", "category": "协议状态"},
    {"id": "OSPF状态", "name": "OSPF 邻居", "desc": "OSPF 邻居 Full 状态", "category": "协议状态"},
    {"id": "VRRP状态", "name": "VRRP 状态", "desc": "VRRP 主备状态", "category": "协议状态"},
    # ── 系统信息 ──
    {"id": "日志告警", "name": "日志告警", "desc": "warning/error 日志", "category": "系统信息"},
    {"id": "ACL规则", "name": "ACL 规则", "desc": "ACL 规则数量", "category": "系统信息"},
    {"id": "NTP同步", "name": "NTP 同步", "desc": "时钟同步状态", "category": "系统信息"},
    {"id": "当前配置", "name": "当前配置", "desc": "运行配置快照", "category": "系统信息"},
    # ── 安全合规（10项）──
    {"id": "弱口令检测", "name": "弱口令检测", "desc": "检查是否存在默认密码或弱密码", "category": "安全合规", "severity": "high"},
    {"id": "Telnet启用", "name": "Telnet 启用", "desc": "检查是否启用了明文 Telnet", "category": "安全合规", "severity": "high"},
    {"id": "SSH_V1协议", "name": "SSH V1 协议", "desc": "检查是否支持 SSH V1", "category": "安全合规", "severity": "high"},
    {"id": "SNMP默认团体字", "name": "SNMP 默认团体字", "desc": "检查 public/private 默认团体字", "category": "安全合规", "severity": "medium"},
    {"id": "HTTP管理", "name": "HTTP 管理", "desc": "是否启用明文 HTTP 管理", "category": "安全合规", "severity": "medium"},
    {"id": "ACL管理口", "name": "ACL 管理口", "desc": "管理口是否配置了 ACL 保护", "category": "安全合规", "severity": "medium"},
    {"id": "登录横幅", "name": "登录横幅", "desc": "是否配置登录警告横幅", "category": "安全合规", "severity": "low"},
    {"id": "会话超时", "name": "会话超时", "desc": "闲置会话超时是否配置", "category": "安全合规", "severity": "low"},
    {"id": "日志配置", "name": "日志配置", "desc": "Syslog 远程日志是否配置", "category": "安全合规", "severity": "low"},
    {"id": "NTP配置", "name": "NTP 配置", "desc": "NTP 时间同步是否配置", "category": "安全合规", "severity": "low"},
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT '',
            ip TEXT NOT NULL UNIQUE,
            port INTEGER DEFAULT 22,
            username TEXT DEFAULT 'admin',
            password TEXT DEFAULT ''
        )
    """)
    conn.commit()
    return conn


# ── 设备管理 API ──

@router.get("/devices")
def list_devices():
    """巡检设备列表（返回清单，密码脱敏）"""
    conn = _get_db()
    rows = conn.execute("SELECT id,name,ip,port,username FROM health_devices ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/devices")
def save_device(body: dict):
    """添加/更新巡检设备"""
    name = body.get("name", "") or body.get("ip", "")
    ip = body.get("ip", "")
    port = body.get("port", 22)
    username = body.get("username", "admin")
    password = body.get("password", "")
    if not ip:
        raise HTTPException(400, "设备 IP 必填")

    conn = _get_db()
    existing = conn.execute("SELECT id FROM health_devices WHERE ip=?", (ip,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE health_devices SET name=?,port=?,username=?,password=? WHERE ip=?",
            (name, port, username, password, ip),
        )
    else:
        conn.execute(
            "INSERT INTO health_devices (name,ip,port,username,password) VALUES (?,?,?,?,?)",
            (name, ip, port, username, password),
        )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/devices/delete")
def delete_device(body: dict):
    """删除巡检设备"""
    ip = body.get("ip", "")
    if not ip:
        raise HTTPException(400, "IP 必填")
    conn = _get_db()
    conn.execute("DELETE FROM health_devices WHERE ip=?", (ip,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/reports/delete")
def delete_report(body: dict):
    """删除巡检报告"""
    rid = body.get("id")
    if not rid:
        raise HTTPException(400, "id 必填")
    conn = _get_db()
    conn.execute("DELETE FROM health_reports WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/templates")
def list_templates():
    """巡检模板列表（含命令）"""
    from app.api.inspection_engine import INSPECTION_COMMANDS
    result = []
    for t in CHECK_TEMPLATES:
        t2 = dict(t)
        t2["command"] = INSPECTION_COMMANDS.get(t["id"], "")
        result.append(t2)
    return result


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


# ── SSH 执行器（供巡检引擎调用） ──

async def _ssh_exec_command(host: str, port: int, username: str, password: str, command: str) -> str:
    """异步 SSH 执行单条命令"""
    def _sync():
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=username, password=password,
                       timeout=10, look_for_keys=False, allow_agent=False)
        stdin, stdout, stderr = client.exec_command(command, timeout=30)
        # 等待命令执行完毕
        exit_code = stdout.channel.recv_exit_status()
        result = stdout.read().decode("utf-8", errors="replace")
        if not result:
            result = stderr.read().decode("utf-8", errors="replace")
        client.close()
        return result
    return await asyncio.get_event_loop().run_in_executor(None, _sync)


@router.post("/run")
async def run_health_check(
    device_id: str = Query(...),
    device_name: str = Query(default=""),
    device_ip: str = Query(...),
    device_port: int = Query(default=22),
    username: str = Query(...),
    password: str = Query(...),
    checks: str = Query(default="CPU使用率,内存使用率,接口状态,温度状态,风扇状态,电源状态", description="逗号分隔的巡检项"),
):
    """执行真实 SSH 巡检 — 华为交换机命令解析"""
    items = [c.strip() for c in checks.split(",") if c.strip()]
    valid_items = []
    for item in items:
        tpl = next((t for t in CHECK_TEMPLATES if t["id"] == item), None)
        if tpl:
            valid_items.append(item)

    if not valid_items:
        return {"error": "无有效巡检项", "results": [], "score": 100, "passed": 0, "failed": 0}

    # 巡检引擎
    engine = InspectionEngine(ssh_executor=_ssh_exec_command)

    devices = [{
        "id": device_id,
        "name": device_name or device_ip,
        "ip": device_ip,
        "port": device_port,
        "username": username,
        "password": password,
    }]

    t0 = time.time()
    results = await engine.run(devices, valid_items)
    elapsed = time.time() - t0

    # 统计
    normal = sum(1 for r in results if r["level"] == "normal")
    warning = sum(1 for r in results if r["level"] == "warning")
    error = sum(1 for r in results if r["level"] == "error")
    score = max(0, 100 - warning * 5 - error * 10)

    report = {
        "device_id": device_id,
        "device_name": device_name or device_ip,
        "checks": results,
        "score": score,
        "passed": normal,
        "warning": warning,
        "failed": error,
        "elapsed_ms": round(elapsed * 1000),
    }

    # 保存到数据库
    conn = _get_db()
    conn.execute(
        "INSERT INTO health_reports (device_id, device_name, report, score) VALUES (?,?,?,?)",
        (device_id, device_name or device_ip, json.dumps(report, ensure_ascii=False), score),
    )
    conn.commit()
    conn.close()
    return report
