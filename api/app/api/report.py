"""文档报告生成 — 从拓扑数据一键生成 Markdown 竣工报告"""
from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import PlainTextResponse
from typing import Any

router = APIRouter(prefix="/report", tags=["report"])


@router.post("/generate", summary="生成拓扑报告")
def generate_report(
    topology_data: dict = Body(..., description="完整的拓扑 JSON 数据"),
):
    """输入拓扑 JSON → 输出 Markdown 报告"""
    devices = topology_data.get("devices", []) or topology_data.get("nodes", [])
    edges = topology_data.get("edges", [])
    groups = topology_data.get("groups", [])
    if not devices:
        raise HTTPException(400, "拓扑数据为空")

    lines = []
    lines.append(f"# 网络拓扑竣工报告")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"> 设备总数：{len(devices)} | 连线数目：{len(edges)}")
    lines.append("")

    # 1. 设备清单
    lines.append("## 设备清单")
    lines.append("")
    lines.append("| # | 主机名 | IP 地址 | 类型 | 厂商 | 角色 |")
    lines.append("|---|---|---|---|---|---|")
    for i, d in enumerate(devices, 1):
        name = d.get("hostname", "") or d.get("label", "") or f"Device-{i}"
        mgmt_ip = d.get("mgmtIp", d.get("mgmt_ip", "—"))
        dev_type = d.get("type", d.get("deviceType", "—"))
        vendor = d.get("vendor", "—")
        role = d.get("role", "—")
        lines.append(f"| {i} | {name} | {mgmt_ip} | {dev_type} | {vendor} | {role} |")
    lines.append("")

    # 2. 拓扑连线
    lines.append("## 物理连线")
    lines.append("")
    lines.append("| 源设备 | 目标设备 | 标签 |")
    lines.append("|---|---|---|")
    for e in edges:
        src = e.get("source", {}).get("cell", "")
        tgt = e.get("target", {}).get("cell", "")
        label = e.get("labels", [{}])[0].get("attrs", {}).get("label", {}).get("text", "") if e.get("labels") else ""
        lines.append(f"| {src} | {tgt} | {label} |")
    lines.append("")

    # 3. 分组信息
    if groups:
        lines.append("## 网络分区")
        lines.append("")
        for g in groups:
            name = g.get("label", g.get("name", ""))
            children = g.get("children", [])
            lines.append(f"- **{name}**：包含 {len(children)} 台设备")

    # 底部
    lines.append("")
    lines.append("---")
    lines.append(f"*由 NetCmdGen 自动生成 · {datetime.now().strftime('%Y-%m-%d')}*")

    return PlainTextResponse("\n".join(lines), media_type="text/markdown",
                             headers={"Content-Disposition": "attachment; filename=topology-report.md"})


@router.post("/export/json", summary="导出拓扑 JSON")
def export_json(topology_data: dict = Body(...)):
    """导出完整拓扑为 JSON 文件"""
    return topology_data
