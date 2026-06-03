#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""锐捷交换机 STP/MSTP/LACP/端口镜像/堆叠 增强模块"""


class RuijieSwitchEnhancer:
    """锐捷交换机增强命令生成器（STP/LACP/镜像/堆叠）"""

    @staticmethod
    def generate_stp_mstp(config: dict) -> str:
        lines = ["!", "# 生成树配置", "!"]
        lines.append("spanning-tree")
        mode = config.get("mode", "mstp")
        if mode == "mstp":
            lines.append("spanning-tree mode mstp")
            if config.get("mstp_domain"):
                md = config["mstp_domain"]
                lines.append(f"spanning-tree mst configuration")
                lines.append(f" name {md.get('region_name', 'default')}")
                lines.append(f" revision {md.get('revision_level', 0)}")
                for inst in md.get("instances", []):
                    iid = inst.get("instance_id", 0)
                    vlans = inst.get("vlans", "1")
                    lines.append(f" instance {iid} vlan {vlans}")
                lines.append(" exit")
        elif mode == "rstp":
            lines.append("spanning-tree mode rstp")
        lines.append(f"spanning-tree priority {config.get('priority', 32768)}")
        for iface in config.get("stp_interfaces", []):
            ifname = iface.get("interface", "GigabitEthernet 0/1")
            lines.append(f"interface {ifname}")
            if iface.get("edge_port"):
                lines.append(" spanning-tree portfast")
                lines.append("# 边缘端口：端口快速转发")
            if iface.get("bpdu_protection"):
                lines.append(" spanning-tree bpduguard enable")
                lines.append("# BPDU保护")
            if iface.get("root_protection"):
                lines.append(" spanning-tree guard root")
                lines.append("# 根保护")
            lines.append("!")
        lines.append("# 验证: show spanning-tree summary")
        lines.append("# 回滚: no spanning-tree")
        return "\n".join(lines)

    @staticmethod
    def generate_lacp(config: dict) -> str:
        lines = ["!", "# 链路聚合", "!"]
        for trunk in config:
            tid = trunk.get("trunk_id", 1)
            members = trunk.get("members", [])
            lines.append(f"interface aggregateport {tid}")
            lines.append(f" description {trunk.get('description', 'LACP汇聚')}")
            if trunk.get("mode") == "lacp":
                lines.append(" # 动态LACP")
            lines.append("!")
            for mem in members:
                lines.append(f"interface {mem}")
                lines.append(f" port-group {tid}")
                lines.append("!")
            lines.append(f"# 验证: show aggregateport {tid} summary")
            lines.append(f"# 回滚: no interface aggregateport {tid}")
        return "\n".join(lines)

    @staticmethod
    def generate_port_mirror(config: dict) -> str:
        lines = ["!", "# 端口镜像", "!"]
        for pm in config:
            src = pm.get("source_interface", "GigabitEthernet 0/1")
            dst = pm.get("observe_interface", "GigabitEthernet 0/24")
            lines.append("monitor session 1 source interface " + src + " both")
            lines.append("monitor session 1 destination interface " + dst)
            lines.append("# 验证: show monitor")
            lines.append("# 回滚: no monitor session 1")
        return "\n".join(lines)

    @staticmethod
    def generate_stack(config: dict) -> str:
        lines = ["!", "# 堆叠配置(VSU)", "!"]
        lines.append("switch virtual domain 1")
        for i, dev in enumerate(config.get("devices", [{"id":1,"priority":100}])):
            lines.append(f" switch {dev.get('id', i+1)}")
            lines.append(f" switch {dev.get('id', i+1)} priority {dev.get('priority', 100)}")
        lines.append("!")
        for port in config.get("vsl_ports", []):
            lines.append(f"vsl-port {port.get('id', 1)}")
            lines.append(f" port-member interface {port.get('interface', 'TenGigabitEthernet 0/49')}")
            lines.append("!")
        lines.append("# 验证: show switch virtual")
        lines.append("# 回滚: no switch virtual domain 1")
        return "\n".join(lines)
