#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""迈普交换机 STP/MSTP/LACP/端口镜像/堆叠 增强模块"""


class MaipuSwitchEnhancer:
    """迈普交换机增强命令生成器"""

    @staticmethod
    def generate_stp_mstp(config: dict) -> str:
        lines = ["!", "# 生成树配置", "!"]
        mode = config.get("mode", "mstp")
        lines.append(f"spanning-tree mode {mode}")
        lines.append(f"spanning-tree priority {config.get('priority', 32768)}")
        if config.get("enable", True):
            lines.append("spanning-tree enable")
        for iface in config.get("stp_interfaces", []):
            ifname = iface.get("interface", "gigabitethernet 0/1")
            lines.append(f"interface {ifname}")
            if iface.get("edge_port"):
                lines.append(" spanning-tree portfast")
                lines.append("# 边缘端口")
            if iface.get("bpdu_protection"):
                lines.append(" spanning-tree bpduguard enable")
            lines.append("!")
        lines.append("# 验证: show spanning-tree")
        lines.append("# 回滚: no spanning-tree enable")
        return "\n".join(lines)

    @staticmethod
    def generate_lacp(config: dict) -> str:
        lines = ["!", "# 链路聚合", "!"]
        for trunk in config:
            tid = trunk.get("trunk_id", 1)
            members = trunk.get("members", [])
            mode = trunk.get("mode", "static")
            lines.append(f"interface port-channel {tid}")
            lines.append(f" description {trunk.get('description', 'LACP汇聚')}")
            if mode == "lacp":
                lines.append(" channel-group mode active")
            lines.append("!")
            for mem in members:
                lines.append(f"interface {mem}")
                lines.append(f" channel-group {tid} mode {'active' if mode=='lacp' else 'on'}")
                lines.append("!")
            lines.append(f"# 验证: show interface port-channel {tid}")
            lines.append(f"# 回滚: no interface port-channel {tid}")
        return "\n".join(lines)

    @staticmethod
    def generate_port_mirror(config: dict) -> str:
        lines = ["!", "# 端口镜像", "!"]
        for pm in config:
            src = pm.get("source_interface", "gigabitethernet 0/1")
            dst = pm.get("observe_interface", "gigabitethernet 0/24")
            lines.append(f"monitor session 1 source interface {src}")
            lines.append(f"monitor session 1 destination interface {dst}")
            lines.append("# 验证: show monitor session 1")
            lines.append("# 回滚: no monitor session 1")
        return "\n".join(lines)

    @staticmethod
    def generate_stack(config: dict) -> str:
        lines = ["!", "# 堆叠配置", "!"]
        for dev in config.get("devices", [{"id":1,"priority":100}]):
            lines.append(f"stack member {dev.get('id', 1)} priority {dev.get('priority', 100)}")
        for port in config.get("stack_ports", []):
            lines.append(f"stack-port {port.get('id', '0/1')}")
            lines.append(f" port-member {port.get('interface', 'ten-gigabitethernet 0/49')}")
        lines.append("# 验证: show stack")
        lines.append("# 回滚: no stack enable")
        return "\n".join(lines)
