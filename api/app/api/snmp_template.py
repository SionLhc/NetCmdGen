"""SNMP OID 采集模板管理"""
import json, sqlite3
from pathlib import Path
from fastapi import APIRouter, Query

router = APIRouter(prefix="/snmp-template", tags=["snmp-template"])
DB_DIR = Path(__file__).parent.parent / "data"; DB_PATH = DB_DIR / "snmp_template.db"

PRESETS = [
    {"oid":"1.3.6.1.2.1.2.2.1.10","name":"ifInOctets","desc":"接口输入字节数","unit":"bytes"},
    {"oid":"1.3.6.1.2.1.2.2.1.16","name":"ifOutOctets","desc":"接口输出字节数","unit":"bytes"},
    {"oid":"1.3.6.1.2.1.2.2.1.2","name":"ifName","desc":"接口名称","unit":""},
    {"oid":"1.3.6.1.2.1.2.2.1.5","name":"ifSpeed","desc":"接口速率","unit":"bps"},
    {"oid":"1.3.6.1.4.1.2021.10.1.3.1","name":"cpuLoad1","desc":"CPU 1分钟负载","unit":"%"},
    {"oid":"1.3.6.1.4.1.2021.4.5.0","name":"memTotal","desc":"内存总量","unit":"KB"},
    {"oid":"1.3.6.1.4.1.2021.4.6.0","name":"memFree","desc":"可用内存","unit":"KB"},
    {"oid":"1.3.6.1.2.1.1.3.0","name":"sysUpTime","desc":"系统运行时间","unit":"timeticks"},
    {"oid":"1.3.6.1.2.1.1.5.0","name":"sysName","desc":"系统名称","unit":""},
    {"oid":"1.3.6.1.2.1.25.2.3.1.6","name":"diskUsed","desc":"磁盘已用","unit":"KB"},
]

def _db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH)); conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS templates (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, oid TEXT, description TEXT, unit TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    # 初始化预设
    for p in PRESETS:
        conn.execute("INSERT OR IGNORE INTO templates (name,oid,description,unit) VALUES (?,?,?,?)",(p["name"],p["oid"],p["desc"],p["unit"]))
    conn.commit(); return conn

@router.get("/templates")
def list_templates():
    conn = _db(); rows = conn.execute("SELECT * FROM templates ORDER BY name").fetchall(); conn.close()
    return [dict(r) for r in rows]

@router.post("/templates")
def add_template(name:str=Query(...),oid:str=Query(...),description:str=Query(""),unit:str=Query("")):
    conn = _db(); conn.execute("INSERT INTO templates (name,oid,description,unit) VALUES (?,?,?,?)",(name,oid,description,unit)); conn.commit(); conn.close()
    return {"ok":True}

@router.delete("/templates/{tid}")
def del_template(tid:int):
    conn = _db(); conn.execute("DELETE FROM templates WHERE id=?",(tid,)); conn.commit(); conn.close()
    return {"ok":True}
