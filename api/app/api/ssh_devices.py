"""SSH 设备管理 — 持久化保存连接信息"""

import sqlite3, os, hashlib, base64
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/ssh-devices", tags=["ssh-devices"])
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ssh_devices.db")

def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS ssh_devices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER DEFAULT 22,
            username TEXT DEFAULT 'admin',
            password_enc TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.commit()
    return conn

def _encrypt(text: str) -> str:
    key = hashlib.sha256("NetCmdGen-SSH-2026".encode()).digest()
    from cryptography.fernet import Fernet
    f = Fernet(base64.urlsafe_b64encode(key[:32]))
    return f.encrypt(text.encode()).decode()

def _decrypt(text: str) -> str:
    key = hashlib.sha256("NetCmdGen-SSH-2026".encode()).digest()
    from cryptography.fernet import Fernet
    f = Fernet(base64.urlsafe_b64encode(key[:32]))
    return f.decrypt(text.encode()).decode()


@router.get("", summary="获取保存的 SSH 设备列表")
def list_devices():
    conn = _get_db()
    rows = conn.execute("SELECT id, name, host, port, username, created_at FROM ssh_devices ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.put("", summary="保存或更新 SSH 设备")
def save_device(
    name: str = Query(...),
    host: str = Query(...),
    port: int = Query(default=22),
    username: str = Query(default="admin"),
    password: str = Query(default=""),
):
    import uuid
    conn = _get_db()
    # 检查是否有同 host+username 的设备
    exist = conn.execute(
        "SELECT id FROM ssh_devices WHERE host=? AND username=?", (host, username)
    ).fetchone()
    if exist:
        dev_id = exist["id"]
        conn.execute(
            "UPDATE ssh_devices SET name=?, port=?, password_enc=? WHERE id=?",
            (name, port, _encrypt(password) if password else (exist["password_enc"] if hasattr(exist, 'password_enc') else ''), dev_id)
        )
    else:
        dev_id = uuid.uuid4().hex[:12]
        conn.execute(
            "INSERT INTO ssh_devices (id, name, host, port, username, password_enc) VALUES (?,?,?,?,?,?)",
            (dev_id, name or host, host, port, username, _encrypt(password) if password else "")
        )
    conn.commit()
    conn.close()
    return {"success": True, "id": dev_id}


@router.get("/{device_id}/password", summary="获取设备解密后的密码")
def get_password(device_id: str):
    conn = _get_db()
    r = conn.execute("SELECT password_enc FROM ssh_devices WHERE id=?", (device_id,)).fetchone()
    conn.close()
    if not r:
        raise HTTPException(404, "设备不存在")
    try:
        return {"password": _decrypt(r["password_enc"])} if r["password_enc"] else {"password": ""}
    except Exception:
        return {"password": ""}


@router.delete("/{device_id}", summary="删除 SSH 设备")
def delete_device(device_id: str):
    conn = _get_db()
    conn.execute("DELETE FROM ssh_devices WHERE id=?", (device_id,))
    conn.commit()
    conn.close()
    return {"success": True}
