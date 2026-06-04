"""MNDP 设备发现 — UDP 广播扫描局域网 RouterOS 设备"""
from __future__ import annotations

import json
import socket
import struct
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter(prefix="/ros", tags=["ros-mndp"])

# MNDP 数据包格式 (简化为发现请求)
MNDP_PORT = 5678
MNDP_MULTICAST = "255.255.255.255"


def _parse_mndp(data: bytes) -> Optional[dict]:
    """解析 MNDP 响应包，提取设备信息"""
    try:
        # 跳过 MAC 头 (MNDP 在 UDP 数据中)
        offset = 0
        if len(data) < 4:
            return None

        # 简易 TLV 解析
        result = {"ip": "", "identity": "", "version": "", "platform": "", "mac": ""}
        pos = 4
        while pos + 4 <= len(data):
            try:
                tlv_type = struct.unpack(">H", data[pos:pos+2])[0]
                tlv_len = struct.unpack(">H", data[pos+2:pos+4])[0]
                pos += 4
                if pos + tlv_len > len(data):
                    break
                value = data[pos:pos+tlv_len].decode("utf-8", errors="ignore").strip("\x00")
                pos += tlv_len

                if tlv_type == 1:
                    result["mac"] = ":".join(f"{b:02x}" for b in value.encode()[:6]) if len(value) >= 6 else value
                elif tlv_type == 5:
                    result["identity"] = value
                elif tlv_type == 7:
                    result["version"] = value
                elif tlv_type == 8:
                    result["platform"] = value
            except Exception:
                break

        return result if result["identity"] else None
    except Exception:
        return None


def _scan_network(timeout: float = 3.0) -> list[dict]:
    """发送 MNDP 广播并收集响应"""
    devices = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)

    # MNDP 发现请求 (简单格式)
    mndp_request = bytes([0, 0, 0, 0])

    try:
        sock.sendto(mndp_request, (MNDP_MULTICAST, MNDP_PORT))

        while True:
            try:
                data, addr = sock.recvfrom(4096)
                info = _parse_mndp(data)
                if info:
                    info["ip"] = addr[0]
                    # 去重
                    if not any(d["ip"] == info["ip"] for d in devices):
                        devices.append(info)
            except socket.timeout:
                break
    except Exception:
        pass
    finally:
        sock.close()

    return devices


@router.get("/discover", summary="MNDP 扫描局域网 RouterOS 设备")
def mndp_discover(
    timeout: float = Query(default=3.0, ge=1.0, le=10.0),
):
    """UDP 广播 MNDP 协议发现局域网内的 RouterOS 设备"""
    try:
        devices = _scan_network(timeout)
        return {"success": True, "devices": devices, "total": len(devices)}
    except Exception as e:
        return {"success": False, "error": str(e), "devices": []}
