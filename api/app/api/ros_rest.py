"""RouterOS REST API 代理 — Phase 1 核心模块"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

import httpx
from fastapi import APIRouter, Query, HTTPException

from app.api.ros_models import RosCredentials


router = APIRouter(prefix="/ros", tags=["ros"])

# ─── 凭证存储 (SQLite) ───
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "ros_devices.db"
ENCRYPT_KEY = "netcmdgen-ros-2024"  # 生产环境应使用环境变量


def _get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER DEFAULT 443,
            username TEXT DEFAULT 'admin',
            password_enc TEXT DEFAULT '',
            use_ssl INTEGER DEFAULT 1,
            grp TEXT DEFAULT 'default',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def _encrypt(text: str) -> str:
    """简单 XOR 加密（生产应使用 AES）"""
    key = ENCRYPT_KEY.encode()
    data = text.encode()
    result = bytearray()
    for i, b in enumerate(data):
        result.append(b ^ key[i % len(key)])
    return base64.urlsafe_b64encode(bytes(result)).decode()


def _decrypt(encrypted: str) -> str:
    try:
        data = base64.urlsafe_b64decode(encrypted)
        key = ENCRYPT_KEY.encode()
        result = bytearray()
        for i, b in enumerate(data):
            result.append(b ^ key[i % len(key)])
        return result.decode()
    except Exception:
        return ""


# ─── REST 客户端 ───
async def _ros_request(host: str, port: int, username: str, password: str,
                        path: str, method: str = "GET", data: dict = None,
                        use_ssl: bool = True, timeout: float = 10.0) -> dict:
    """向 RouterOS REST API 发送请求"""
    proto = "https" if use_ssl else "http"
    url = f"{proto}://{host}:{port}/rest/{path}"
    auth = (username, password) if username and password else None

    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        if method == "GET":
            resp = await client.get(url, auth=auth)
        elif method == "PATCH":
            resp = await client.patch(url, json=data, auth=auth)
        elif method == "PUT":
            resp = await client.put(url, json=data, auth=auth)
        elif method == "DELETE":
            resp = await client.delete(url, auth=auth)
        elif method == "POST":
            resp = await client.post(url, json=data, auth=auth)
        else:
            resp = await client.get(url, auth=auth)

        if resp.status_code >= 400:
            raise HTTPException(resp.status_code, f"RouterOS 返回错误: {resp.text[:200]}")
        try:
            return resp.json() if resp.text else {}
        except Exception:
            return {"raw": resp.text}


async def _quick_test(host: str, port: int, username: str, password: str,
                      use_ssl: bool = True) -> dict:
    """快速连接测试，返回含中文提示的诊断信息"""
    try:
        info = await _ros_request(host, port, username, password,
                                  "system/resource", use_ssl=use_ssl, timeout=5)
        return {
            "success": True,
            "version": info.get("version", ""),
            "board_name": info.get("board-name", info.get("board_name", "")),
            "uptime": info.get("uptime", ""),
            "cpu_load": info.get("cpu-load", info.get("cpu_load", "")),
            "free_memory": str(int(info.get("free-memory", info.get("free_memory", "0"))) // 1024 // 1024) + " MB",
            "total_memory": str(int(info.get("total-memory", info.get("total_memory", "0"))) // 1024 // 1024) + " MB",
        }
    except HTTPException as e:
        # 根据状态码给出中文提示
        if e.status_code == 401 or e.status_code == 403:
            msg = "认证失败：用户名或密码错误"
        elif e.status_code == 404:
            msg = "REST API 不可用：请确认 RouterOS ≥ v7.1 且 www-ssl 服务已启用 (/ip service enable www-ssl)"
        else:
            msg = f"HTTP {e.status_code}: {e.detail[:100]}"
        return {"success": False, "error": msg}
    except Exception as e:
        err = str(e)
        if "ConnectionRefused" in err or "connect" in err.lower():
            msg = f"连接被拒绝：请确认 IP/端口正确，设备 WebFig 服务是否启用（默认端口 443，Winbox 端口 8291 不可用）"
        elif "SSL" in err or "ssl" in err.lower() or "certificate" in err.lower():
            msg = "SSL 证书错误：尝试关闭 SSL 开关使用 HTTP 连接（端口改为 80）"
        elif "timeout" in err.lower() or "Timeout" in err:
            msg = "连接超时：设备不可达或端口不通"
        else:
            msg = err[:200]
        return {"success": False, "error": msg}


# ─── API 端点 ───

@router.get("/devices", summary="获取设备列表")
def get_devices():
    conn = _get_db()
    rows = conn.execute("SELECT * FROM devices ORDER BY created_at DESC").fetchall()
    conn.close()
    return [
        {
            "id": r["id"], "name": r["name"], "host": r["host"],
            "port": r["port"], "username": r["username"],
            "use_ssl": bool(r["use_ssl"]), "group": r["grp"],
            "password": "***" if r["password_enc"] else "",
        }
        for r in rows
    ]


@router.put("/devices", summary="保存设备")
def save_device(device: RosCredentials):
    device_id = hashlib.md5(f"{device.host}:{device.port}".encode()).hexdigest()[:12]
    conn = _get_db()
    existing = conn.execute("SELECT id FROM devices WHERE host=? AND port=?", 
                           (device.host, device.port)).fetchone()
    name = existing["name"] if existing else device.host
    conn.execute("""
        INSERT OR REPLACE INTO devices (id, name, host, port, username, password_enc, use_ssl)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (device_id, name, device.host, device.port, device.username,
          _encrypt(device.password), int(device.use_ssl)))
    conn.commit()
    conn.close()
    return {"success": True, "id": device_id}


@router.delete("/devices/{device_id}", summary="删除设备")
def delete_device(device_id: str):
    conn = _get_db()
    conn.execute("DELETE FROM devices WHERE id=?", (device_id,))
    conn.commit()
    conn.close()
    return {"success": True}


@router.patch("/devices/{device_id}", summary="重命名设备")
def rename_device(device_id: str, name: str = Query(...)):
    conn = _get_db()
    conn.execute("UPDATE devices SET name=? WHERE id=?", (name, device_id))
    conn.commit()
    conn.close()
    return {"success": True}


@router.get("/devices/{device_id}/connect", summary="连接设备获取系统信息")
def connect_device(device_id: str):
    conn = _get_db()
    r = conn.execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()
    conn.close()
    if not r:
        raise HTTPException(404, "设备不存在")

    password = _decrypt(r["password_enc"]) if r["password_enc"] else ""
    return asyncio.run(_quick_test(
        r["host"], r["port"], r["username"], password, bool(r["use_ssl"])
    ))


@router.get("/test", summary="测试连接")
def test_connection(
    host: str = Query(...), port: int = Query(default=443),
    username: str = Query(...), password: str = Query(...),
    use_ssl: bool = Query(default=True),
):
    return asyncio.run(_quick_test(host, port, username, password, use_ssl))


@router.get("/system", summary="获取系统资源")
def get_system(device_id: str = Query(...)):
    conn = _get_db()
    r = conn.execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()
    conn.close()
    if not r:
        raise HTTPException(404, "设备不存在")
    password = _decrypt(r["password_enc"]) if r["password_enc"] else ""
    return asyncio.run(_ros_request(
        r["host"], r["port"], r["username"], password,
        "system/resource", use_ssl=bool(r["use_ssl"])
    ))


def _get_device_creds(device_id: str):
    """获取设备凭证的辅助函数"""
    conn = _get_db()
    r = conn.execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()
    conn.close()
    if not r:
        raise HTTPException(404, "设备不存在")
    return {
        "host": r["host"], "port": r["port"], "username": r["username"],
        "password": _decrypt(r["password_enc"]) if r["password_enc"] else "",
        "use_ssl": bool(r["use_ssl"]),
    }


# ─── 通用 REST CRUD 代理（支持任意 RouterOS 菜单路径）───

@router.get("/proxy", summary="通用 REST 查询")
def proxy_get(device_id: str = Query(...), path: str = Query(..., description="菜单路径，如 ip/address")):
    creds = _get_device_creds(device_id)
    return asyncio.run(_ros_request(creds["host"], creds["port"], creds["username"],
                                     creds["password"], path, use_ssl=creds["use_ssl"]))


@router.patch("/proxy", summary="通用 REST 更新")
async def proxy_patch(device_id: str = Query(...), path: str = Query(...), data: str = Query(default="{}")):
    creds = _get_device_creds(device_id)
    import json
    return await _ros_request(creds["host"], creds["port"], creds["username"],
                               creds["password"], path, method="PATCH",
                               data=json.loads(data), use_ssl=creds["use_ssl"])


@router.put("/proxy", summary="通用 REST 创建")
async def proxy_put(device_id: str = Query(...), path: str = Query(...), data: str = Query(default="{}")):
    creds = _get_device_creds(device_id)
    import json
    return await _ros_request(creds["host"], creds["port"], creds["username"],
                               creds["password"], path, method="PUT",
                               data=json.loads(data), use_ssl=creds["use_ssl"])


@router.delete("/proxy", summary="通用 REST 删除")
async def proxy_delete(device_id: str = Query(...), path: str = Query(...)):
    creds = _get_device_creds(device_id)
    return await _ros_request(creds["host"], creds["port"], creds["username"],
                               creds["password"], path, method="DELETE",
                               use_ssl=creds["use_ssl"])


# ─── 已有端点（保留兼容）───

@router.get("/interfaces", summary="获取接口列表")
def get_interfaces(device_id: str = Query(...)):
    creds = _get_device_creds(device_id)
    return asyncio.run(_ros_request(creds["host"], creds["port"], creds["username"],
                                     creds["password"], "interface", use_ssl=creds["use_ssl"]))
