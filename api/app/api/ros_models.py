"""RouterOS 数据模型"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class RosDevice(BaseModel):
    """RouterOS 设备"""
    id: str = ""
    name: str = "RouterOS"
    host: str = ""
    port: int = 443
    username: str = "admin"
    password: str = ""
    use_ssl: bool = True
    group: str = "default"
    version: str = ""
    model: str = ""


class RosCredentials(BaseModel):
    """连接凭证"""
    host: str
    port: int = 443
    username: str = "admin"
    password: str = ""
    use_ssl: bool = True


class RosSystemInfo(BaseModel):
    """系统信息"""
    cpu_load: str = "0"
    free_memory: str = "0"
    total_memory: str = "0"
    free_hdd: str = "0"
    total_hdd: str = "0"
    uptime: str = ""
    version: str = ""
    board_name: str = ""


class RosInterface(BaseModel):
    """接口信息"""
    name: str = ""
    type: str = ""
    running: str = "false"
    disabled: str = "false"
    mac_address: str = ""
    rx_byte: str = "0"
    tx_byte: str = "0"
    comment: str = ""


class RosTrafficPoint(BaseModel):
    """流量数据点"""
    ts: float
    rx_mbps: float
    tx_mbps: float
    rx_total: str
    tx_total: str


class RosApiResponse(BaseModel):
    """统一 API 响应"""
    success: bool = True
    data: Optional[dict | list] = None
    error: str = ""
