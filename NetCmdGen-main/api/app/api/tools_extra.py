"""网络工具 API 路由（Ping / 端口扫描 / 路由跟踪 / DNS / Whois）"""
from fastapi import APIRouter, HTTPException, Query
from app.tools.ping import PingTool
from app.tools.portscan import PortScanner
from app.tools.trace import TraceRoute
from app.tools.dns import DNSTool

router = APIRouter()


# ── Ping ─────────────────────────────────────────────────
@router.get("/ping", summary="Ping 测试")
def api_ping(
    host: str = Query(..., description="目标 IP 或域名"),
    count: int = Query(4, ge=1, le=20, description="Ping 次数"),
    timeout: int = Query(2, ge=1, le=10, description="超时秒数"),
) -> dict:
    result = PingTool.ping(host, count=count, timeout=timeout)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error") or "Ping 失败")
    return result


# ── 端口扫描 ─────────────────────────────────────────────
@router.get("/portscan", summary="端口扫描")
def api_portscan(
    host: str = Query(..., description="目标 IP 或域名"),
    ports: str = Query("22,80,443,3389", description="逗号分隔的端口列表"),
    timeout: float = Query(1.0, ge=0.5, le=5.0, description="单端口超时秒数"),
) -> dict:
    try:
        port_list = [int(p.strip()) for p in ports.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="端口格式错误")
    result = PortScanner.scan_ports(host, port_list, timeout=timeout)
    return result


# ── 路由跟踪 ─────────────────────────────────────────────
@router.get("/trace", summary="路由跟踪")
def api_trace(
    host: str = Query(..., description="目标 IP 或域名"),
    max_hops: int = Query(30, ge=1, le=50, description="最大跳数"),
    timeout: int = Query(2, ge=1, le=10, description="超时秒数"),
) -> dict:
    result = TraceRoute.traceroute(host, max_hops=max_hops, timeout=timeout)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error") or "Traceroute 失败")
    return result


# ── DNS ──────────────────────────────────────────────────
@router.get("/dns", summary="DNS 查询")
def api_dns(
    domain: str = Query(..., description="域名"),
    record_type: str = Query("A", description="记录类型 A/AAAA/MX/NS/TXT/CNAME"),
) -> dict:
    result = DNSTool.lookup(domain, record_type=record_type)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error") or "DNS 查询失败")
    return result


# ── Whois ────────────────────────────────────────────────
@router.get("/whois", summary="Whois 查询")
def api_whois(
    domain: str = Query(..., description="域名或 IP"),
) -> dict:
    try:
        import whois
        w = whois.whois(domain)
        return {"success": True, "domain": domain, "info": dict(w) if w else {}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Whois 查询失败: {e}")
