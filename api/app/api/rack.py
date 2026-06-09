"""机柜管理 — 区域划分 + 接口座位映射 + 批量导入"""
import json
import sqlite3
from pathlib import Path
from fastapi import APIRouter, Query, HTTPException, UploadFile, File

router = APIRouter(prefix="/rack", tags=["rack"])
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "rack.db"


def _db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # 机柜表（增加 region 字段）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS racks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, location TEXT, region TEXT DEFAULT '',
            rows INTEGER DEFAULT 42,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 设备表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rack_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rack_id INTEGER, name TEXT, vendor TEXT, model TEXT,
            u_start INTEGER DEFAULT 1, u_height INTEGER DEFAULT 1,
            ip TEXT, status TEXT DEFAULT 'online',
            FOREIGN KEY(rack_id) REFERENCES racks(id)
        )
    """)
    # 接口-座位映射表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS port_seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rack_id INTEGER NOT NULL,
            device_id INTEGER NOT NULL,
            device_name TEXT DEFAULT '',
            seat TEXT NOT NULL,
            port TEXT NOT NULL,
            remark TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(rack_id) REFERENCES racks(id),
            FOREIGN KEY(device_id) REFERENCES rack_devices(id)
        )
    """)
    # 迁移：旧表补 region 列
    try:
        conn.execute("ALTER TABLE racks ADD COLUMN region TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    return conn


# ── 区域 ──

@router.get("/regions")
def list_regions():
    """获取所有区域列表"""
    conn = _db()
    rows = conn.execute(
        "SELECT DISTINCT region FROM racks WHERE region != '' ORDER BY region"
    ).fetchall()
    conn.close()
    return [r["region"] for r in rows]


# ── 机柜 CRUD ──

@router.get("/racks")
def list_racks(region: str = Query(default="")):
    """获取机柜列表，支持按区域筛选"""
    conn = _db()
    if region:
        rows = conn.execute(
            "SELECT * FROM racks WHERE region=? ORDER BY name", (region,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM racks ORDER BY region, name").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["devices"] = [
            dict(x)
            for x in conn.execute(
                "SELECT * FROM rack_devices WHERE rack_id=?", (d["id"],)
            ).fetchall()
        ]
        # 附带每个设备的端口映射数量
        for dev in d["devices"]:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM port_seats WHERE device_id=?", (dev["id"],)
            ).fetchone()[0]
            dev["port_seat_count"] = cnt
        result.append(d)
    conn.close()
    return result


@router.post("/racks")
def add_rack(
    name: str = Query(...),
    location: str = Query(default=""),
    rows: int = Query(default=42),
    region: str = Query(default=""),
):
    conn = _db()
    conn.execute(
        "INSERT INTO racks (name,location,rows,region) VALUES (?,?,?,?)",
        (name, location, rows, region),
    )
    conn.commit()
    rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"ok": True, "id": rid}


@router.post("/racks/update")
def update_rack(
    rack_id: int = Query(...),
    name: str = Query(...),
    location: str = Query(default=""),
    rows: int = Query(default=42),
    region: str = Query(default=""),
):
    conn = _db()
    conn.execute(
        "UPDATE racks SET name=?,location=?,rows=?,region=? WHERE id=?",
        (name, location, rows, region, rack_id),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.delete("/racks/{rack_id}")
def del_rack(rack_id: int):
    conn = _db()
    conn.execute("DELETE FROM port_seats WHERE rack_id=?", (rack_id,))
    conn.execute("DELETE FROM rack_devices WHERE rack_id=?", (rack_id,))
    conn.execute("DELETE FROM racks WHERE id=?", (rack_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ── 设备 CRUD ──

@router.post("/devices")
def add_device(
    rack_id: int = Query(...),
    name: str = Query(...),
    vendor: str = Query(""),
    model: str = Query(""),
    u_start: int = Query(default=1),
    u_height: int = Query(default=1),
    ip: str = Query(""),
    status: str = Query(default="online"),
    dev_id: int = Query(default=0),
):
    conn = _db()
    if dev_id:
        conn.execute(
            "UPDATE rack_devices SET rack_id=?,name=?,vendor=?,model=?,u_start=?,u_height=?,ip=?,status=? WHERE id=?",
            (rack_id, name, vendor, model, u_start, u_height, ip, status, dev_id),
        )
    else:
        conn.execute(
            "INSERT INTO rack_devices (rack_id,name,vendor,model,u_start,u_height,ip,status) VALUES (?,?,?,?,?,?,?,?)",
            (rack_id, name, vendor, model, u_start, u_height, ip, status),
        )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.delete("/devices/{dev_id}")
def del_device(dev_id: int):
    conn = _db()
    conn.execute("DELETE FROM port_seats WHERE device_id=?", (dev_id,))
    conn.execute("DELETE FROM rack_devices WHERE id=?", (dev_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ── 座位搜索 ──

@router.get("/search")
def search_seat(q: str = Query(default="", description="搜索关键字：座位号、接口名或设备名")):
    """根据座位号/接口名搜索对应的交换机、机柜、区域"""
    conn = _db()
    kw = f"%{q.strip()}%"
    rows = conn.execute("""
        SELECT ps.*, r.name as rack_name, r.location, r.region,
               d.name as device_name, d.vendor, d.model, d.ip as device_ip,
               d.u_start, d.u_height
        FROM port_seats ps
        JOIN racks r ON r.id = ps.rack_id
        JOIN rack_devices d ON d.id = ps.device_id
        WHERE ps.seat LIKE ? OR ps.port LIKE ? OR d.name LIKE ? OR r.name LIKE ?
        ORDER BY r.region, r.name, ps.seat
    """, (kw, kw, kw, kw)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 接口-座位映射 ──

@router.get("/seats")
def list_seats(rack_id: int = Query(default=0), device_id: int = Query(default=0)):
    """查询接口-座位映射，可按机柜或设备筛选"""
    conn = _db()
    if device_id:
        rows = conn.execute(
            "SELECT * FROM port_seats WHERE device_id=? ORDER BY seat, port",
            (device_id,),
        ).fetchall()
    elif rack_id:
        rows = conn.execute(
            "SELECT * FROM port_seats WHERE rack_id=? ORDER BY seat, port",
            (rack_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM port_seats ORDER BY seat, port"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/seats")
def add_seat(
    rack_id: int = Query(...),
    device_id: int = Query(...),
    device_name: str = Query(default=""),
    seat: str = Query(...),
    port: str = Query(...),
    remark: str = Query(default=""),
):
    """添加单条接口-座位映射"""
    conn = _db()
    conn.execute(
        "INSERT INTO port_seats (rack_id,device_id,device_name,seat,port,remark) VALUES (?,?,?,?,?,?)",
        (rack_id, device_id, device_name, seat, port, remark),
    )
    conn.commit()
    sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"ok": True, "id": sid}


@router.delete("/seats/{seat_id}")
def del_seat(seat_id: int):
    conn = _db()
    conn.execute("DELETE FROM port_seats WHERE id=?", (seat_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/seats/import")
async def import_seats(
    rack_id: int = Query(...),
    device_id: int = Query(...),
    device_name: str = Query(default=""),
    data: str = Query(default=""),
):
    """
    批量导入接口-座位映射
    支持 CSV（带表头）或纯文本格式：
      座位号,接口名,备注
      A01,GE0/0/1,办公区-张三
    """
    conn = _db()
    imported = skipped = 0
    lines = data.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 跳过 CSV 表头行
        first_cell = line.split(",")[0].strip().lower() if "," in line else ""
        if first_cell in ("座位号", "座位", "seat"):
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and parts[0] and parts[1]:
            seat_val = parts[0]
            port_val = parts[1]
            remark_val = parts[2] if len(parts) >= 3 else ""
            # 去重检查
            exist = conn.execute(
                "SELECT id FROM port_seats WHERE device_id=? AND seat=? AND port=?",
                (device_id, seat_val, port_val),
            ).fetchone()
            if exist:
                # 更新备注
                conn.execute(
                    "UPDATE port_seats SET remark=? WHERE id=?",
                    (remark_val, exist["id"]),
                )
                imported += 1
            else:
                conn.execute(
                    "INSERT INTO port_seats (rack_id,device_id,device_name,seat,port,remark) VALUES (?,?,?,?,?,?)",
                    (rack_id, device_id, device_name, seat_val, port_val, remark_val),
                )
                imported += 1
        else:
            skipped += 1

    conn.commit()
    conn.close()
    return {"ok": True, "imported": imported, "skipped": skipped}


@router.get("/export/{rack_id}")
def export_rack(rack_id: int):
    """导出整个机柜的接口-座位映射为 CSV"""
    import csv, io
    conn = _db()
    # 获取机柜信息
    rack = conn.execute("SELECT * FROM racks WHERE id=?", (rack_id,)).fetchone()
    if not rack:
        conn.close()
        return {"error": "机柜不存在"}

    # 获取所有设备及其端口映射
    rows = conn.execute("""
        SELECT ps.seat, ps.port, ps.remark,
               d.name as device_name, d.vendor, d.model, d.ip, d.u_start
        FROM port_seats ps
        JOIN rack_devices d ON d.id = ps.device_id
        WHERE ps.rack_id = ?
        ORDER BY d.name, ps.seat, ps.port
    """, (rack_id,)).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    # 标准模板表头
    writer.writerow(["座位号", "接口名", "备注", "交换机名称", "交换机IP", "U位"])
    for r in rows:
        writer.writerow([
            r["seat"], r["port"], r["remark"] or "",
            r["device_name"], r["ip"] or "", str(r["u_start"] or ""),
        ])
    csv_content = output.getvalue()
    output.close()

    return {
        "ok": True,
        "filename": f"{rack['name']}_{rack['region'] or ''}.csv",
        "data": csv_content,
    }


@router.get("/template")
def download_template():
    """下载标准导入模板 CSV"""
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["座位号", "接口名", "备注"])
    writer.writerow(["示例: A01", "示例: GE0/0/1", "示例: 办公区-张三"])
    writer.writerow(["A01", "GE0/0/1", ""])
    writer.writerow(["A02", "GE0/0/2", ""])
    csv_content = output.getvalue()
    output.close()
    return {"data": csv_content, "filename": "接口座位映射模板.csv"}
