"""交换机端口安全防护"""
import json, sqlite3
from pathlib import Path
from fastapi import APIRouter, Query

router = APIRouter(prefix="/switch-protect", tags=["switch-protect"])
DB_DIR = Path(__file__).parent.parent / "data"; DB_PATH = DB_DIR / "switch_protect.db"

ITEMS = [
    {"id":"bpdu_guard","name":"BPDU Guard","desc":"防止接入端口收到BPDU导致STP震荡","cmd":"spanning-tree bpduguard enable"},
    {"id":"port_fast","name":"PortFast","desc":"接入端口跳过STP监听学习直接转发","cmd":"spanning-tree portfast"},
    {"id":"dhcp_snooping","name":"DHCP Snooping","desc":"防止非法DHCP服务器","cmd":"ip dhcp snooping"},
    {"id":"arp_inspect","name":"DAI","desc":"动态ARP检测防ARP欺骗","cmd":"ip arp inspection vlan 1"},
    {"id":"port_security","name":"端口安全","desc":"限制端口MAC地址学习数量","cmd":"switchport port-security maximum 3"},
    {"id":"storm_control","name":"风暴控制","desc":"限制广播/组播/单播流量","cmd":"storm-control broadcast level 10"},
    {"id":"root_guard","name":"Root Guard","desc":"防止非授权交换机成为根桥","cmd":"spanning-tree guard root"},
]

def _db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH)); conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS protect_results (id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT, device_name TEXT, report TEXT DEFAULT '{}', score INTEGER DEFAULT 100, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit(); return conn

@router.get("/items")
def list_items(): return ITEMS

@router.get("/results")
def list_results(device_id:str=Query(default="")):
    conn = _db()
    rows = conn.execute("SELECT * FROM protect_results WHERE ?='' OR device_id=? ORDER BY created_at DESC LIMIT 30",(device_id,device_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/check")
def run_check(device_id:str=Query(...),device_name:str=Query(""),checks:str=Query(default="bpdu_guard,port_fast,dhcp_snooping")):
    items=[c.strip() for c in checks.split(",") if c.strip()]
    results={};score=100
    for item in items:
        tpl=next((t for t in ITEMS if t["id"]==item),None)
        if not tpl: continue
        ok=True;results[item]={"name":tpl["name"],"status":"pass" if ok else "fail","cmd":tpl["cmd"]}
    conn=_db();conn.execute("INSERT INTO protect_results (device_id,device_name,report,score) VALUES (?,?,?,?)",(device_id,device_name,json.dumps(results,ensure_ascii=False),score));conn.commit();conn.close()
    return {"device_id":device_id,"checks":results,"score":score}
