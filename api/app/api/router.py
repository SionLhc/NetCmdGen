"""API 路由聚合"""
from fastapi import APIRouter

from app.api import generate, manual, network_tools, tools_extra, tools_subnet, topology
from app.api import collaboration, config_audit, lldp_discovery, report, ssh_terminal
from app.api import ros_rest, ros_mndp
from app.api.diagnostics import dns as diag_dns
from app.api.diagnostics import tcp_port as diag_tcp
from app.api.diagnostics import http_check as diag_http
from app.api.diagnostics import mtu as diag_mtu
from app.api.diagnostics import jitter as diag_jitter
from app.api.diagnostics import history as diag_history

api_router = APIRouter()

api_router.include_router(tools_subnet.router, prefix="/tools", tags=["tools"])
api_router.include_router(tools_extra.router, prefix="/tools", tags=["tools"])
api_router.include_router(network_tools.router)  # /net/* 路由（ping/portscan/traceroute/dns）

# 诊断子系统（/api/v1/diagnostics/*）
api_router.include_router(diag_dns.router, prefix="/diagnostics", tags=["diagnostics"])
api_router.include_router(diag_tcp.router, prefix="/diagnostics", tags=["diagnostics"])
api_router.include_router(diag_http.router, prefix="/diagnostics", tags=["diagnostics"])
api_router.include_router(diag_mtu.router, prefix="/diagnostics", tags=["diagnostics"])
api_router.include_router(diag_jitter.router, prefix="/diagnostics", tags=["diagnostics"])
api_router.include_router(diag_history.router, prefix="/diagnostics", tags=["diagnostics"])

api_router.include_router(generate.router, tags=["generate"])
api_router.include_router(manual.router, tags=["manual"])
api_router.include_router(ros_rest.router, tags=["ros"])
api_router.include_router(ros_mndp.router, tags=["ros"])
api_router.include_router(collaboration.router, tags=["collab"])
api_router.include_router(config_audit.router, tags=["audit"])
api_router.include_router(lldp_discovery.router, tags=["lldp"])
api_router.include_router(report.router, tags=["report"])
api_router.include_router(ssh_terminal.router, prefix="/ssh", tags=["ssh"])
api_router.include_router(topology.router, tags=["topology"])
