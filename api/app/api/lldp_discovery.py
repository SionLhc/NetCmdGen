"""LLDP 拓扑自动发现 — SSH 登录设备 → 读取 LLDP 邻居表 → 生成拓扑 JSON"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional

import paramiko
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/lldp", tags=["lldp"])

# 已发现的设备（防止循环）
_discovered = set()


@dataclass
class LLDPNeighbor:
    local_port: str
    remote_device: str
    remote_port: str


@dataclass
class TopoNode:
    id: str
    label: str
    type: str = "switch"
    x: int = 0
    y: int = 0
    mgmtIp: str = ""


@dataclass
class TopoEdge:
    source: str
    target: str
    sourcePort: str = ""
    targetPort: str = ""


def _ssh_exec(host: str, port: int, username: str, password: str, command: str) -> str:
    """执行 SSH 命令并返回输出"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=username, password=password,
                   timeout=10, allow_agent=False, look_for_keys=False)
    stdin, stdout, stderr = client.exec_command(command, timeout=15)
    output = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return output


def _parse_lldp_huawei(output: str) -> list[LLDPNeighbor]:
    """解析华为/华三 LLDP 邻居表"""
    neighbors = []
    # 格式: GigabitEthernet0/0/1     Switch-A         GigabitEthernet0/0/1
    # 或:   GE0/0/1                  192.168.1.1      GE0/0/2
    for line in output.split('\n'):
        line = line.strip()
        if not line or line.startswith(('Local', '--', 'LLDP', 'System', 'Info')):
            continue
        # 尝试匹配 接口名 设备名 接口名 的三列格式
        parts = line.split()
        if len(parts) >= 3:
            local = parts[0]
            remote_dev = parts[1] if len(parts) <= 3 else ' '.join(parts[1:-1])
            remote_port = parts[-1]
            # 过滤表头
            if re.match(r'^[\d\w/\-]+$', local) and re.match(r'^[\d\w/\-]+$', remote_port):
                neighbors.append(LLDPNeighbor(
                    local_port=local,
                    remote_device=remote_dev,
                    remote_port=remote_port,
                ))
    return neighbors


def _parse_lldp_cisco(output: str) -> list[LLDPNeighbor]:
    """解析 Cisco LLDP 邻居表"""
    neighbors = []
    current_dev = ""
    current_port = ""
    for line in output.split('\n'):
        line = line.strip()
        m = re.match(r'Device ID:\s*(.+?)\s*$', line, re.IGNORECASE)
        if m:
            current_dev = m.group(1)
            continue
        m = re.match(r'Port ID:\s*(.+?)\s*$', line, re.IGNORECASE)
        if m:
            current_port = m.group(1)
            continue
        m = re.match(r'Local Intf:\s*(.+?)\s*$', line, re.IGNORECASE)
        if m:
            local = m.group(1)
            neighbors.append(LLDPNeighbor(local_port=local, remote_device=current_dev, remote_port=current_port))
    return neighbors


def _discover(
    host: str, port: int, username: str, password: str,
    nodes: list[TopoNode], edges: list[TopoEdge],
    x_offset: int, y_offset: int, max_depth: int = 3,
) -> None:
    """递归发现 LLDP 邻居"""
    if host in _discovered or max_depth <= 0:
        return
    _discovered.add(host)

    # 尝试获取邻居表
    commands = [
        "display lldp neighbor brief",   # 华为/华三
        "show lldp neighbors",           # Cisco
        "show lldp neighbors brief",     # Juniper
    ]
    neighbors = []
    for cmd in commands:
        try:
            output = _ssh_exec(host, port, username, password, cmd)
            if 'display' in cmd or 'brief' in cmd:
                neighbors = _parse_lldp_huawei(output)
            else:
                neighbors = _parse_lldp_cisco(output)
            if neighbors:
                break
        except Exception:
            continue

    if not neighbors:
        return  # 无 LLDP 信息或设备不支持

    # 当前设备
    current_id = f"node-{host.replace('.', '-')}"
    if not any(n.id == current_id for n in nodes):
        nodes.append(TopoNode(id=current_id, label=host, mgmtIp=host, x=x_offset, y=y_offset))

    # 处理每个邻居
    child_y = y_offset
    for nb in neighbors:
        remote_id = f"node-{nb.remote_device.replace('.', '-')}"
        if not any(n.id == remote_id for n in nodes):
            nodes.append(TopoNode(id=remote_id, label=nb.remote_device, mgmtIp=nb.remote_device,
                                  x=x_offset + 200, y=child_y))

        # 添加连线
        if not any((e.source == current_id and e.target == remote_id) or
                   (e.source == remote_id and e.target == current_id) for e in edges):
            edges.append(TopoEdge(source=current_id, target=remote_id,
                                  sourcePort=nb.local_port, targetPort=nb.remote_port))

        child_y += 100

    # 递归发现邻居（使用相同凭据）
    for nb in neighbors:
        _discover(nb.remote_device, port, username, password, nodes, edges,
                  x_offset + 400, child_y, max_depth - 1)


@router.get("/discover", summary="LLDP 拓扑自动发现")
def lldp_discover(
    host: str = Query(..., description="种子设备 IP"),
    port: int = Query(default=22),
    username: str = Query(..., description="SSH 用户名"),
    password: str = Query(..., description="SSH 密码"),
    max_depth: int = Query(default=2, ge=1, le=5, description="最大发现深度"),
):
    """从种子设备出发，通过 LLDP 自动发现邻居并生成拓扑 JSON"""
    _discovered.clear()
    nodes: list[TopoNode] = []
    edges: list[TopoEdge] = []

    # 连接测试
    try:
        _ssh_exec(host, port, username, password, "display version")
    except paramiko.AuthenticationException:
        raise HTTPException(401, "SSH 认证失败")
    except Exception as e:
        raise HTTPException(500, f"无法连接设备: {e}")

    _discover(host, port, username, password, nodes, edges, x_offset=100, y_offset=100, max_depth=max_depth)

    if len(nodes) < 2 and len(edges) == 0:
        return {"success": False, "message": "未发现 LLDP 邻居（设备可能未启用 LLDP 或不支持）",
                "nodes": [asdict(n) for n in nodes], "edges": [asdict(e) for e in edges]}

    return {
        "success": True,
        "nodes": [asdict(n) for n in nodes],
        "edges": [asdict(e) for e in edges],
        "total": len(nodes),
    }
