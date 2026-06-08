"""机柜管理"""
import sqlite3
from pathlib import Path
from fastapi import APIRouter, Query

router = APIRouter(prefix="/rack", tags=["rack"])
DB_DIR = Path(__file__).parent.parent / "data"; DB_PATH = DB_DIR / "rack.db"

def _db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH)); conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS racks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, location TEXT, rows INTEGER DEFAULT 42, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS rack_devices (id INTEGER PRIMARY KEY AUTOINCREMENT, rack_id INTEGER, name TEXT, vendor TEXT, model TEXT, u_start INTEGER DEFAULT 1, u_height INTEGER DEFAULT 1, ip TEXT, status TEXT DEFAULT 'online', FOREIGN KEY(rack_id) REFERENCES racks(id))")
    conn.commit(); return conn

@router.get("/racks")
def list_racks():
    conn = _db(); rows = conn.execute("SELECT * FROM racks ORDER BY name").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["devices"] = [dict(x) for x in conn.execute("SELECT * FROM rack_devices WHERE rack_id=?",(d["id"],)).fetchall()]
        result.append(d)
    conn.close(); return result

@router.post("/racks")
def add_rack(name: str = Query(...), location: str = Query(default=""), rows: int = Query(default=42)):
    conn = _db(); conn.execute("INSERT INTO racks (name,location,rows) VALUES (?,?,?)",(name,location,rows)); conn.commit()
    rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]; conn.close()
    return {"ok":True, "id":rid}

@router.delete("/racks/{rack_id}")
def del_rack(rack_id:int):
    conn = _db(); conn.execute("DELETE FROM rack_devices WHERE rack_id=?",(rack_id,)); conn.execute("DELETE FROM racks WHERE id=?",(rack_id,)); conn.commit(); conn.close()
    return {"ok":True}

@router.post("/devices")
def add_device(rack_id:int=Query(...),name:str=Query(...),vendor:str=Query(""),model:str=Query(""),u_start:int=Query(default=1),u_height:int=Query(default=1),ip:str=Query(""),status:str=Query(default="online"),dev_id:int=Query(default=0)):
    conn = _db()
    if dev_id:
        # 更新已有设备
        conn.execute(
            "UPDATE rack_devices SET rack_id=?,name=?,vendor=?,model=?,u_start=?,u_height=?,ip=?,status=? WHERE id=?",
            (rack_id,name,vendor,model,u_start,u_height,ip,status,dev_id)
        )
    else:
        conn.execute(
            "INSERT INTO rack_devices (rack_id,name,vendor,model,u_start,u_height,ip,status) VALUES (?,?,?,?,?,?,?,?)",
            (rack_id,name,vendor,model,u_start,u_height,ip,status)
        )
    conn.commit(); conn.close()
    return {"ok":True}

@router.delete("/devices/{dev_id}")
def del_device(dev_id:int):
    conn = _db(); conn.execute("DELETE FROM rack_devices WHERE id=?",(dev_id,)); conn.commit(); conn.close()
    return {"ok":True}
