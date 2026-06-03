#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NetOps Toolkit - VLAN配置模块
"""


class VLANConfigGenerator:
    """VLAN配置生成器"""
    
    @staticmethod
    def generate_vlan_batch(vlan_ids: list) -> str:
        """批量生成VLAN"""
        if not vlan_ids:
            return ""
        
        sorted_vlans = sorted(vlan_ids)
        ranges = []
        start = sorted_vlans[0]
        end = sorted_vlans[0]
        
        for i in range(1, len(sorted_vlans)):
            if sorted_vlans[i] == end + 1:
                end = sorted_vlans[i]
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start} to {end}")
                start = sorted_vlans[i]
                end = sorted_vlans[i]
        
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start} to {end}")
        
        return f"vlan batch {' '.join(ranges)}\n"
    
    @staticmethod
    def generate_vlan_single(vlan_id: int, name: str = None, description: str = None) -> str:
        """生成单个VLAN配置"""
        config_lines = []
        config_lines.append(f"vlan {vlan_id}\n")
        if name:
            config_lines.append(f" name {name}\n")
        if description:
            config_lines.append(f" description {description}\n")
        config_lines.append("#\n")
        return "".join(config_lines)
    
    @staticmethod
    def generate_port_vlan(interface: str, 
                          vlan_type: str = "access",
                          vlan_id: int = None,
                          trunk_vlans: list = None,
                          pvid: int = None) -> str:
        """生成接口VLAN配置"""
        config_lines = []
        config_lines.append(f"interface {interface}\n")
        config_lines.append(f" port link-type {vlan_type}\n")
        
        if vlan_type == "access" and vlan_id:
            config_lines.append(f" port default vlan {vlan_id}\n")
        elif vlan_type == "trunk":
            if trunk_vlans:
                config_lines.append(f" port trunk allow-pass vlan {' '.join(map(str, trunk_vlans))}\n")
            if pvid:
                config_lines.append(f" port trunk pvid vlan {pvid}\n")
        elif vlan_type == "hybrid":
            if vlan_id:
                config_lines.append(f" port hybrid pvid vlan {vlan_id}\n")
            if trunk_vlans:
                config_lines.append(f" port hybrid untagged vlan {' '.join(map(str, trunk_vlans))}\n")
        
        config_lines.append("#\n")
        return "".join(config_lines)
    
    @staticmethod
    def generate_vlanif(vlan_id: int, 
                        ip_address: str,
                        mask: str = "255.255.255.0",
                        description: str = None) -> str:
        """生成VLANIF接口配置"""
        config_lines = []
        config_lines.append(f"interface Vlanif{vlan_id}\n")
        if description:
            config_lines.append(f" description {description}\n")
        config_lines.append(f" ip address {ip_address} {mask}\n")
        config_lines.append("#\n")
        return "".join(config_lines)
    
    @staticmethod
    def generate_voice_vlan(interface: str, 
                           vlan_id: int,
                           untagged: bool = True) -> str:
        """生成Voice VLAN配置"""
        config_lines = []
        config_lines.append(f"interface {interface}\n")
        config_lines.append(f" voice-vlan {vlan_id} {'untag' if untagged else 'tag'}\n")
        config_lines.append("#\n")
        return "".join(config_lines)
    
    @staticmethod
    def generate_stp_config(mode: str = "stp",
                            priority: int = 32768,
                            enable: bool = True) -> str:
        """生成STP配置"""
        config_lines = []
        config_lines.append("stp mode {mode}\n")
        config_lines.append(f"stp {'enable' if enable else 'disable'}\n")
        if priority != 32768:
            config_lines.append(f"stp priority {priority}\n")
        return "".join(config_lines)
    
    @staticmethod
    def generate_vlan_all(config: dict) -> str:
        """生成完整VLAN配置"""
        config_lines = ["#\n", "# VLAN配置\n", "#\n"]
        
        if "vlans" in config:
            vlan_ids = [v["id"] if isinstance(v, dict) else v for v in config["vlans"]]
            if len(vlan_ids) > 3:
                config_lines.append(VLANConfigGenerator.generate_vlan_batch(vlan_ids))
            else:
                for vlan in config["vlans"]:
                    if isinstance(vlan, dict):
                        config_lines.append(VLANConfigGenerator.generate_vlan_single(
                            vlan["id"],
                            vlan.get("name"),
                            vlan.get("description")
                        ))
                    else:
                        config_lines.append(VLANConfigGenerator.generate_vlan_single(vlan))
        
        if "interfaces" in config:
            config_lines.append("\n#\n# 接口VLAN配置\n#\n")
            for iface in config["interfaces"]:
                config_lines.append(VLANConfigGenerator.generate_port_vlan(
                    iface["interface"],
                    iface.get("type", "access"),
                    iface.get("vlan_id"),
                    iface.get("trunk_vlans"),
                    iface.get("pvid")
                ))
        
        if "vlanifs" in config:
            config_lines.append("\n#\n# VLANIF配置\n#\n")
            for vlanif in config["vlanifs"]:
                config_lines.append(VLANConfigGenerator.generate_vlanif(
                    vlanif["vlan_id"],
                    vlanif["ip_address"],
                    vlanif.get("mask", "255.255.255.0"),
                    vlanif.get("description")
                ))
        
        if "voice_vlans" in config:
            config_lines.append("\n#\n# Voice VLAN配置\n#\n")
            for voice in config["voice_vlans"]:
                config_lines.append(VLANConfigGenerator.generate_voice_vlan(
                    voice["interface"],
                    voice["vlan_id"],
                    voice.get("untagged", True)
                ))
        
        if "stp" in config:
            stp_conf = config["stp"]
            config_lines.append("\n#\n# STP配置\n#\n")
            config_lines.append(VLANConfigGenerator.generate_stp_config(
                stp_conf.get("mode", "mstp"),
                stp_conf.get("priority", 32768),
                stp_conf.get("enable", True)
            ))
            # MSTP 域配置
            if stp_conf.get("mode") == "mstp" and stp_conf.get("mstp_domain"):
                md = stp_conf["mstp_domain"]
                config_lines.append(f"stp region-configuration\n")
                config_lines.append(f" region-name {md.get('region_name', 'default')}\n")
                config_lines.append(f" revision-level {md.get('revision_level', 0)}\n")
                for inst in md.get("instances", []):
                    iid = inst.get("instance_id", 0)
                    vlans = inst.get("vlans", "1")
                    config_lines.append(f" instance {iid} vlan {vlans}\n")
                config_lines.append(f" active region-configuration\n")
                config_lines.append(f"# 验证: display stp region-configuration\n")
                config_lines.append(f"# 回滚: undo stp region-configuration\n")
                config_lines.append("#\n")
            # 接口级 STP 优化
            for iface in stp_conf.get("stp_interfaces", []):
                ifname = iface.get("interface", "GigabitEthernet0/0/1")
                config_lines.append(f"interface {ifname}\n")
                if iface.get("edge_port"):
                    config_lines.append(f" stp edged-port enable\n")
                    config_lines.append(f"# 边缘端口：直连终端，跳过STP计算，快速进入转发\n")
                if iface.get("bpdu_protection"):
                    config_lines.append(f" stp bpdu-protection\n")
                    config_lines.append(f"# BPDU保护：收到BPDU自动shutdown，防止环路\n")
                if iface.get("root_protection"):
                    config_lines.append(f" stp root-protection\n")
                    config_lines.append(f"# 根保护：防止更优BPDU抢走根桥角色\n")
                config_lines.append(f"# 验证: display stp interface {ifname}\n")
                config_lines.append(f"# 回滚: undo stp edged-port / undo stp bpdu-protection\n")
                config_lines.append("#\n")

        # 端口镜像
        if "port_mirror" in config:
            config_lines.append("\n#\n# 端口镜像配置\n#\n")
            for pm in config["port_mirror"]:
                src = pm.get("source_interface", "GigabitEthernet0/0/1")
                dst = pm.get("observe_interface", "GigabitEthernet0/0/24")
                dir_ = pm.get("direction", "both")
                config_lines.append(f"observe-port 1 interface {dst}\n")
                config_lines.append(f"# 观察口：流量拷贝到此口接分析设备\n")
                config_lines.append(f"interface {src}\n")
                config_lines.append(f" port-mirroring to observe-port 1 {dir_}\n")
                config_lines.append(f"# 镜像方向: {dir_} (both=收发/inbound=入/outbound=出)\n")
                config_lines.append(f"# 验证: display port-mirroring\n")
                config_lines.append(f"# 回滚: undo port-mirroring to observe-port 1\n")
                config_lines.append("#\n")

        # 堆叠/集群（iStack/CSS）
        if "stack" in config:
            config_lines.append("\n#\n# 堆叠/集群配置\n#\n")
            sc = config["stack"]
            if sc.get("mode") == "css":
                config_lines.append(f"# CSS 集群（高端框式 V200R002+）\n")
                config_lines.append(f"css enable\n")
                config_lines.append(f"set css mode {sc.get('css_mode', 'lpu')}\n")
                config_lines.append(f"set css id {sc.get('css_id', 1)}\n")
                config_lines.append(f"set css priority {sc.get('css_priority', 100)}\n")
                config_lines.append(f"# 验证: display css status\n")
                config_lines.append(f"# 回滚: undo css enable\n")
            elif sc.get("mode") == "istack":
                config_lines.append(f"# iStack 堆叠（盒式 S系列）\n")
                config_lines.append(f"stack enable\n")
                if sc.get("domain"):
                    config_lines.append(f"stack domain {sc['domain']}\n")
                if sc.get("slot_id"):
                    config_lines.append(f"stack slot {sc['slot_id']} priority {sc.get('priority', 100)}\n")
                for port in sc.get("stack_ports", []):
                    config_lines.append(f"interface stack-port {port.get('id', '0/1')}\n")
                    for mem in port.get("members", []):
                        config_lines.append(f" port member-group interface {mem}\n")
                    config_lines.append("#\n")
                config_lines.append(f"# 保存后重启生效\n")
                config_lines.append(f"# 验证: display stack\n")
                config_lines.append(f"# 回滚: undo stack enable\n")
            config_lines.append("#\n")

        # LACP/链路聚合
        if "lacp" in config:
            config_lines.append("\n#\n# 链路聚合/Eth-Trunk配置\n#\n")
            for trunk in config["lacp"]:
                tid = trunk.get("trunk_id", 1)
                mode = trunk.get("mode", "static")
                members = trunk.get("members", [])
                config_lines.append(f"interface Eth-Trunk{tid}\n")
                config_lines.append(f" description {trunk.get('description', 'LACP汇聚')}\n")
                if mode == "lacp":
                    config_lines.append(f" mode lacp-static\n")
                    config_lines.append(f"# 动态LACP：自动协商，IEEE 802.3ad标准\n")
                    if trunk.get("lacp_priority"):
                        config_lines.append(f" lacp priority {trunk['lacp_priority']}\n")
                    if trunk.get("max_active"):
                        config_lines.append(f" max active-linknumber {trunk['max_active']}\n")
                        config_lines.append(f"# 最大活跃链路数（M:N备份）\n")
                    if trunk.get("min_active"):
                        config_lines.append(f" least active-linknumber {trunk['min_active']}\n")
                        config_lines.append(f"# 最小活跃链路数（低于此值聚合口down）\n")
                else:
                    config_lines.append(f" mode manual load-balance\n")
                    config_lines.append(f"# 静态LACP：手动指定，不协商\n")
                for mem in members:
                    config_lines.append(f"interface {mem}\n")
                    config_lines.append(f" eth-trunk {tid}\n")
                    config_lines.append(f"#\n")
                config_lines.append(f"# 验证: display eth-trunk {tid}\n")
                config_lines.append(f"# 验证: display interface Eth-Trunk{tid}\n")
                config_lines.append(f"# 回滚: undo interface Eth-Trunk{tid}\n")
                config_lines.append("#\n")
        
        return "".join(config_lines)
