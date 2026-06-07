"""IP 地址管理 (IPAM) — 子网管理 + IP 分配 + 冲突检测"""
from __future__ import annotations

import ipaddress
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/ipam", tags=["ipam"])

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "ipam.db"


def _get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subnets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT '',
            network TEXT NOT NULL,
            prefix INTEGER NOT NULL,
            gateway TEXT DEFAULT '',
            vlan_id INTEGER DEFAULT 0,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ip_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subnet_id INTEGER NOT NULL,
            ip TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'free',
            device_name TEXT DEFAULT '',
            user_name TEXT DEFAULT '',
            mac TEXT DEFAULT '',
            note TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subnet_id) REFERENCES subnets(id),
            UNIQUE(subnet_id, ip)
        )
    """)
    conn.commit()
    return conn


def _subnet_info(network: str, prefix: int) -> dict:
    """计算子网详细信息"""
    net = ipaddress.IPv4Network(f"{network}/{prefix}", strict=False)
    hosts = list(net.hosts())
    return {
        "network": str(net.network_address),
        "broadcast": str(net.broadcast_address),
        "netmask": str(net.netmask),
        "total_ips": net.num_addresses,
        "usable_ips": max(0, net.num_addresses - 2),
        "first_ip": str(hosts[0]) if hosts else "",
        "last_ip": str(hosts[-1]) if hosts else "",
        "prefix": prefix,
        "cidr": f"{net.network_address}/{prefix}",
    }


# ─── 子网 CRUD ─────────────────────────────────────────────

@router.get("/subnets")
def list_subnets():
    """获取所有子网"""
    conn = _get_db()
    rows = conn.execute("SELECT * FROM subnets ORDER BY network").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d.update(_subnet_info(d["network"], d["prefix"]))
        # 统计使用率
        used = conn.execute("SELECT COUNT(*) FROM ip_records WHERE subnet_id=? AND status='used'", (d["id"],)).fetchone()[0]
        d["used_ips"] = used
        d["usage_pct"] = round(used / max(1, d["usable_ips"]) * 100, 1) if d["usable_ips"] else 0
        result.append(d)
    conn.close()
    return result


@router.post("/subnets")
def add_subnet(
    network: str = Query(...),
    prefix: int = Query(..., ge=8, le=30),
    name: str = Query(default=""),
    gateway: str = Query(default=""),
    vlan_id: int = Query(default=0),
    description: str = Query(default=""),
):
    """添加子网"""
    try:
        net = ipaddress.IPv4Network(f"{network}/{prefix}", strict=False)
    except ValueError:
        raise HTTPException(400, "无效的子网地址")

    conn = _get_db()
    conn.execute(
        "INSERT INTO subnets (name, network, prefix, gateway, vlan_id, description) VALUES (?,?,?,?,?,?)",
        (name, str(net.network_address), prefix, gateway, vlan_id, description),
    )
    conn.commit()
    sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    # 自动生成 IP 记录
    hosts = list(net.hosts())
    for host in hosts[:512]:  # 最多 512 个 IP（性能限制）
        try:
            conn.execute("INSERT OR IGNORE INTO ip_records (subnet_id, ip, status) VALUES (?,?,?)", (sid, str(host), "free"))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    return {"ok": True, "id": sid, "ips_generated": min(len(hosts), 512)}


@router.delete("/subnets/{subnet_id}")
def delete_subnet(subnet_id: int):
    """删除子网及其 IP 记录"""
    conn = _get_db()
    conn.execute("DELETE FROM ip_records WHERE subnet_id=?", (subnet_id,))
    conn.execute("DELETE FROM subnets WHERE id=?", (subnet_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ─── IP 管理 ────────────────────────────────────────────────

@router.get("/ips")
def list_ips(
    subnet_id: int = Query(...),
    status: str = Query(default="all"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=10, le=512),
):
    """获取子网下的 IP 分配列表"""
    conn = _get_db()
    where = "WHERE subnet_id = ?"
    params = [subnet_id]
    if status != "all":
        where += " AND status = ?"
        params.append(status)

    offset = (page - 1) * limit
    rows = conn.execute(f"SELECT * FROM ip_records {where} ORDER BY ip LIMIT ? OFFSET ?", params + [limit, offset]).fetchall()
    total = conn.execute(f"SELECT COUNT(*) FROM ip_records {where}", params).fetchone()[0]
    # 统计
    used = conn.execute("SELECT COUNT(*) FROM ip_records WHERE subnet_id=? AND status='used'", (subnet_id,)).fetchone()[0]
    free = conn.execute("SELECT COUNT(*) FROM ip_records WHERE subnet_id=? AND status='free'", (subnet_id,)).fetchone()[0]
    conn.close()
    return {
        "ips": [dict(r) for r in rows],
        "total": total,
        "used": used,
        "free": free,
        "page": page,
        "limit": limit,
    }


@router.put("/ips/{ip_id}")
def update_ip(
    ip_id: int,
    status: str = Query(default="used"),
    device_name: str = Query(default=""),
    user_name: str = Query(default=""),
    mac: str = Query(default=""),
    note: str = Query(default=""),
):
    """更新 IP 分配状态"""
    conn = _get_db()
    conn.execute(
        "UPDATE ip_records SET status=?, device_name=?, user_name=?, mac=?, note=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (status, device_name, user_name, mac, note, ip_id),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/ips/batch")
def batch_update_ips(
    ip_ids: str = Query(..., description="逗号分隔的 IP ID"),
    status: str = Query(default="used"),
):
    """批量更新 IP 状态"""
    ids = [int(x.strip()) for x in ip_ids.split(",") if x.strip().isdigit()]
    conn = _get_db()
    for i in ids:
        conn.execute("UPDATE ip_records SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, i))
    conn.commit()
    conn.close()
    return {"ok": True, "updated": len(ids)}


# ─── 冲突检测 ────────────────────────────────────────────────

@router.get("/conflicts")
def detect_conflicts():
    """检测子网重叠冲突"""
    conn = _get_db()
    rows = conn.execute("SELECT id, name, network, prefix FROM subnets").fetchall()
    conn.close()

    conflicts = []
    nets = []
    for r in rows:
        try:
            net = ipaddress.IPv4Network(f"{r['network']}/{r['prefix']}", strict=False)
            nets.append((dict(r), net))
        except ValueError:
            continue

    for i, (a, na) in enumerate(nets):
        for j, (b, nb) in enumerate(nets):
            if j <= i:
                continue
            if na.overlaps(nb):
                conflicts.append({
                    "subnet_a": a["name"] or a["cidr"],
                    "subnet_b": b["name"] or b["cidr"],
                    "overlap": str(na) + " ↔ " + str(nb),
                })

    return {"conflicts": conflicts, "total": len(conflicts)}


# ─── 使用率热力图数据 ────────────────────────────────────────

@router.get("/heatmap")
def usage_heatmap(subnet_id: int = Query(...)):
    """获取子网 IP 使用热力图数据"""
    conn = _get_db()
    rows = conn.execute("SELECT ip, status FROM ip_records WHERE subnet_id=? ORDER BY ip", (subnet_id,)).fetchall()
    conn.close()
    return {
        "subnet_id": subnet_id,
        "data": [{"ip": r["ip"], "status": r["status"]} for r in rows],
        "total": len(rows),
    }
