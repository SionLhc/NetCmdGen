"""诊断系统 Pydantic 数据模型"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── SSE 事件模型 ────────────────────────────────────────

class SseEvent(BaseModel):
    """统一 SSE 事件格式"""
    type: str = Field(..., description="事件类型：progress / complete / error")
    data: Dict[str, Any] = Field(default_factory=dict)
    progress: int = Field(default=0)
    total: int = Field(default=0)


class DnsResult(BaseModel):
    """单次 DNS 解析结果"""
    server: str
    server_name: str
    domain: str
    record_type: str
    records: List[str] = []
    rtt_ms: float = 0
    error: Optional[str] = None


class TcpPortResult(BaseModel):
    """单端口 TCP 连通性结果"""
    port: int
    open: bool = False
    service: str = ""
    rtt_ms: float = 0
    description: str = ""
    risk: str = "low"


class HttpResult(BaseModel):
    """HTTP 检测结果"""
    url: str
    status_code: int = 0
    rtt_ms: float = 0
    content_length: int = 0
    server: str = ""
    redirect_chain: List[str] = []
    tls_version: Optional[str] = None
    cert_expires: Optional[str] = None
    cert_issuer: Optional[str] = None
    error: Optional[str] = None


class MtuResult(BaseModel):
    """MTU 探测结果"""
    mtu: int
    success: bool = False
    rtt_ms: float = 0
    error: Optional[str] = None


class JitterPoint(BaseModel):
    """单个抖动采样点"""
    seq: int
    rtt_ms: float
    jitter_ms: float = 0


# ─── 历史数据模型 ─────────────────────────────────────────

class DiagnosticRecord(BaseModel):
    """诊断历史记录"""
    id: Optional[int] = None
    diagnostic_type: str
    target: str
    result: Dict[str, Any] = {}
    summary: Dict[str, Any] = {}
    status: str = "ok"
    created_at: Optional[str] = None


class HistoryQuery(BaseModel):
    """历史查询参数"""
    targets: List[str] = []
    diagnostic_type: str = "ping"
    days: int = Field(default=7, ge=1, le=90)
