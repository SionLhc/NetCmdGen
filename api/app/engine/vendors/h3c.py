#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
H3C华三交换机配置生成器

支持 Comware V5 / V7 版本区分：
- V5: acl number, ssh server compatible-ssh1x
- V7: acl basic/advanced, 不需要 compatible-ssh1x
"""

import time
from typing import Dict, List, Optional, Any

from app.engine.vendors.h3c_version import ComwareVersion, get_cmd


class H3CConfigGenerator:
    """H3C华三交换机配置生成器"""

    @staticmethod
    def generate_header(description: str = "",
                       version: ComwareVersion = ComwareVersion.V5,
                       device_type: str = "交换机") -> str:
        """生成配置头部注释（自动识别设备类型）"""
        return f"""#
# H3C华三{device_type}配置脚本 (Comware {version.value.upper()})
# 描述: {description}
# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
# 设备品牌: H3C (Huawei-3Com)
#
"""
    
    @staticmethod
    def generate_basic_config(config: Dict[str, Any],
                              version: ComwareVersion = ComwareVersion.V5) -> str:
        """
        生成基础配置（支持 Comware V5/V7 版本区分）

        Args:
            config: 基础配置字典
            version: Comware 系统版本
        """
        lines = []
        lines.append(f"\n# ==================== 基础配置 (Comware {version.value.upper()}) ====================")
        lines.append("#\n# 设备基本设置\n#")

        if config.get("hostname"):
            lines.append(f"\nsysname {config['hostname']}")

        if config.get("password"):
            pwd_config = config["password"]
            pwd = pwd_config.get("value", "")
            encrypted = pwd_config.get("encrypted", False)

            if encrypted:
                lines.append(f"\nsuper password cipher {pwd}")
            else:
                lines.append(f"\nsuper password simple {pwd}")

        if config.get("mgmt_interface"):
            mgmt = config["mgmt_interface"]
            interface = mgmt.get("interface", "Vlan-interface1")
            ip = mgmt.get("ip_address", "")
            mask = mgmt.get("mask", "255.255.255.0")
            gateway = mgmt.get("gateway", "")

            if ip:
                lines.append(f"\ninterface {interface}")
                lines.append(f" ip address {ip} {mask}")
                lines.append(" quit")

            if gateway:
                lines.append(f"\nip route-static 0.0.0.0 0 {gateway}")

        if config.get("enable_ssh"):
            ssh_config = config.get("ssh", {})
            port = ssh_config.get("port", 22)
            timeout = ssh_config.get("timeout", 60)
            attempts = ssh_config.get("max_auth_attempts", 5)
            ssh_ver = ssh_config.get("version", "2")

            lines.append(f"\n# SSH服务器配置")
            lines.append(get_cmd(version, "ssh_enable"))
            lines.append(f"ssh server port {port}")
            lines.append(f"ssh server timeout {timeout}")
            lines.append(f"ssh server authentication-timeout {timeout}")
            lines.append(f"ssh server max-auth-times {attempts}")
            # V5: ssh server compatible-ssh1-2 disable, V7: 跳过
            compat = get_cmd(version, "ssh_compat", ver=ssh_ver)
            if compat:
                lines.append(compat)

            if config.get("ssh_user"):
                user = config["ssh_user"]
                username = user.get("username", "admin")
                password = user.get("password", "")
                user_type = user.get("type", "password")

                lines.append(f"\nlocal-user {username}")
                lines.append(f" password simple {password}")
                lines.append(f" service-type ssh")
                lines.append(" authorization-attribute level 3")
                lines.append(" quit")
        
        if config.get("enable_telnet"):
            lines.append(f"\n# Telnet服务器配置")
            lines.append(f"telnet server enable")
            lines.append("")
            lines.append("user-interface vty 0 4")
            lines.append(" authentication-mode scheme")
            lines.append(" protocol inbound all")
            lines.append(" quit")
        
        if config.get("user"):
            user = config["user"]
            username = user.get("username", "admin")
            password = user.get("password", "")
            level = user.get("level", 3)
            service = user.get("service", ["ssh", "telnet"])
            
            lines.append(f"\n# 用户管理")
            lines.append(f"local-user {username}")
            lines.append(f" password simple {password}")
            lines.append(f" authorization-attribute level {level}")
            service_str = " ".join(service)
            lines.append(f" service-type {service_str}")
            lines.append(" quit")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_vlan_config(config: Dict[str, Any]) -> str:
        """
        生成VLAN配置
        
        Args:
            config: VLAN配置字典
                - vlans: VLAN列表
                - vlanifs: VLAN接口列表
                - stp: STP配置
                
        Returns:
            配置字符串
        """
        lines = []
        lines.append("\n# ==================== VLAN配置 ====================")
        lines.append("#\n# VLAN及接口配置\n#")
        
        if config.get("vlans"):
            lines.append("\n# 批量创建VLAN")
            vlan_ids = []
            for vlan in config["vlans"]:
                vlan_id = vlan.get("id")
                vlan_name = vlan.get("name", "")
                if vlan_id:
                    if vlan_name:
                        lines.append(f"vlan {vlan_id}")
                        lines.append(f" name {vlan_name}")
                        lines.append(" quit")
                    else:
                        vlan_ids.append(str(vlan_id))
            
            if vlan_ids:
                lines.append(f"vlan {','.join(vlan_ids)}")
                lines.append(" quit")
        
        if config.get("interfaces"):
            lines.append("\n# 接口VLAN配置")
            for intf in config["interfaces"]:
                interface = intf.get("interface", "")
                link_type = intf.get("link_type", "access")
                
                if not interface:
                    continue
                
                lines.append(f"\ninterface {interface}")
                
                if link_type == "access":
                    vlan_id = intf.get("vlan_id", 1)
                    lines.append(f" port link-type access")
                    lines.append(f" port access vlan {vlan_id}")
                
                elif link_type == "trunk":
                    pvid = intf.get("pvid", 1)
                    trunk_vlans = intf.get("trunk_vlans", [])
                    lines.append(f" port link-type trunk")
                    lines.append(f" port trunk pvid vlan {pvid}")
                    if trunk_vlans:
                        vlan_str = ",".join(map(str, trunk_vlans))
                        lines.append(f" port trunk permit vlan {vlan_str}")
                
                elif link_type == "hybrid":
                    pvid = intf.get("pvid", 1)
                    untagged = intf.get("untagged_vlans", [])
                    tagged = intf.get("tagged_vlans", [])
                    lines.append(f" port link-type hybrid")
                    lines.append(f" port hybrid pvid vlan {pvid}")
                    if untagged:
                        lines.append(f" port hybrid vlan {','.join(map(str, untagged))} untagged")
                    if tagged:
                        lines.append(f" port hybrid vlan {','.join(map(str, tagged))} tagged")
                
                lines.append(" quit")
        
        if config.get("vlanifs"):
            lines.append("\n# VLAN接口配置")
            for vlanif in config["vlanifs"]:
                vlan_id = vlanif.get("vlan_id")
                ip = vlanif.get("ip_address", "")
                mask = vlanif.get("mask", "255.255.255.0")
                desc = vlanif.get("description", "")
                
                if vlan_id and ip:
                    lines.append(f"\ninterface Vlan-interface{vlan_id}")
                    if desc:
                        lines.append(f" description {desc}")
                    lines.append(f" ip address {ip} {mask}")
                    lines.append(" quit")
        
        if config.get("stp"):
            stp_config = config["stp"]
            lines.append("\n# ==================== 生成树配置 ====================")
            mode = stp_config.get("mode", "mstp")
            priority = stp_config.get("priority", 32768)
            lines.append(f"stp mode {mode}")
            lines.append(f"stp priority {priority}")
            if stp_config.get("enable", True):
                lines.append("stp global enable")
            # MSTP 域配置
            if mode == "mstp" and stp_config.get("mstp_domain"):
                md = stp_config["mstp_domain"]
                lines.append(f"stp region-configuration")
                lines.append(f" region-name {md.get('region_name', 'default')}")
                lines.append(f" revision-level {md.get('revision_level', 0)}")
                for inst in md.get("instances", []):
                    iid = inst.get("instance_id", 0)
                    vlans = inst.get("vlans", "1")
                    lines.append(f" instance {iid} vlan {vlans}")
                lines.append(f" active region-configuration")
            # 接口级 STP 优化
            for iface in stp_config.get("stp_interfaces", []):
                ifname = iface.get("interface", "GigabitEthernet1/0/1")
                lines.append(f"interface {ifname}")
                if iface.get("edge_port"):
                    lines.append(f" stp edged-port")
                    lines.append(f"# 边缘端口：直连终端，跳过STP计算")
                if iface.get("bpdu_protection"):
                    lines.append(f" stp bpdu-protection")
                    lines.append(f"# BPDU保护：收到BPDU自动shutdown")
                if iface.get("root_protection"):
                    lines.append(f" stp root-protection")
                    lines.append(f"# 根保护：防止更优BPDU抢根桥")
                lines.append(" quit")
            lines.append(f"# 验证: display stp brief")
            lines.append(f"# 验证: display stp region-configuration")
            lines.append(f"# 回滚: undo stp global enable")

        # LACP/链路聚合
        if config.get("lacp"):
            lines.append("\n# ==================== 链路聚合 ====================")
            for trunk in config["lacp"]:
                tid = trunk.get("trunk_id", 1)
                mode = trunk.get("mode", "static")
                members = trunk.get("members", [])
                lines.append(f"interface Bridge-Aggregation{tid}")
                lines.append(f" description {trunk.get('description', 'LACP汇聚')}")
                lines.append(f" link-aggregation mode {'dynamic' if mode=='lacp' else 'static'}")
                if trunk.get("max_active"):
                    lines.append(f" link-aggregation selected-port maximum {trunk['max_active']}")
                    lines.append(f"# 最大活跃链路数")
                if trunk.get("min_active"):
                    lines.append(f" link-aggregation selected-port minimum {trunk['min_active']}")
                    lines.append(f"# 最小活跃链路数（低于此值聚合口down）")
                lines.append(" quit")
                for mem in members:
                    lines.append(f"interface {mem}")
                    lines.append(f" port link-aggregation group {tid}")
                    lines.append(" quit")
                lines.append(f"# 验证: display link-aggregation verbose")
                lines.append(f"# 回滚: undo interface Bridge-Aggregation{tid}")

        # 端口镜像
        if config.get("port_mirror"):
            lines.append("\n# ==================== 端口镜像 ====================")
            for pm in config["port_mirror"]:
                src = pm.get("source_interface", "GigabitEthernet1/0/1")
                dst = pm.get("observe_interface", "GigabitEthernet1/0/24")
                dir_ = pm.get("direction", "both")
                lines.append(f"mirroring-group 1 local")
                lines.append(f"mirroring-group 1 monitor-port {dst}")
                lines.append(f"mirroring-group 1 mirroring-port {src} {dir_}")
                lines.append(f"# 镜像方向: {dir_}")
                lines.append(f"# 验证: display mirroring-group all")
                lines.append(f"# 回滚: undo mirroring-group 1")

        # IRF 堆叠
        if config.get("stack"):
            lines.append("\n# ==================== IRF堆叠 ====================")
            sc = config["stack"]
            lines.append(f"irf member {sc.get('member_id', 1)} priority {sc.get('priority', 1)}")
            for port in sc.get("irf_ports", []):
                lines.append(f"irf-port {port.get('id', '1/1')}")
                lines.append(f" port group interface {port.get('interface', 'Ten-GigabitEthernet1/0/49')}")
                lines.append(" quit")
            lines.append(f"irf-port-configuration active")
            lines.append(f"# 保存后重启生效")
            lines.append(f"# 验证: display irf")
            lines.append(f"# 回滚: undo irf member")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_routing_config(config: Dict[str, Any]) -> str:
        """
        生成路由配置
        
        Args:
            config: 路由配置字典
                - static: 静态路由列表
                - default: 默认路由
                - ospf: OSPF配置
                - bgp: BGP配置
                - rip: RIP配置
                
        Returns:
            配置字符串
        """
        lines = []
        lines.append("\n# ==================== 路由配置 ====================")
        lines.append("#\n# 路由协议配置\n#")
        
        if config.get("static"):
            lines.append("\n# 静态路由")
            for route in config["static"]:
                dest = route.get("destination", "")
                mask = route.get("mask", "")
                next_hop = route.get("next_hop", "")
                preference = route.get("preference", 60)
                
                if dest and next_hop:
                    lines.append(f"ip route-static {dest} {mask} {next_hop} preference {preference}")
        
        if config.get("default"):
            default = config["default"]
            next_hop = default.get("next_hop", "")
            preference = default.get("preference", 60)
            
            if next_hop:
                lines.append(f"\n# 默认路由")
                lines.append(f"ip route-static 0.0.0.0 0.0.0.0 {next_hop} preference {preference}")
        
        if config.get("ospf"):
            ospf = config["ospf"]
            process_id = ospf.get("process_id", 1)
            router_id = ospf.get("router_id", "")
            area_id = ospf.get("area_id", "0")
            networks = ospf.get("networks", [])
            
            lines.append(f"\n# OSPF配置")
            lines.append(f"ospf {process_id} router-id {router_id}")
            lines.append(f" area {area_id}")
            
            for net in networks:
                addr = net.get("address", "")
                mask = net.get("mask", "0.0.0.255")
                if addr:
                    lines.append(f"  network {addr} {mask}")
            
            lines.append("  quit")
            lines.append(" quit")
        
        if config.get("bgp"):
            bgp = config["bgp"]
            as_num = bgp.get("as_number", "")
            router_id = bgp.get("router_id", "")
            neighbors = bgp.get("neighbors", [])
            networks = bgp.get("networks", [])
            
            if as_num:
                lines.append(f"\n# BGP配置")
                lines.append(f"bgp {as_num}")
                if router_id:
                    lines.append(f" router-id {router_id}")
                
                for neighbor in neighbors:
                    ip = neighbor.get("ip", "")
                    remote_as = neighbor.get("remote_as", "")
                    if ip and remote_as:
                        lines.append(f" peer {ip} as-number {remote_as}")
                
                if networks:
                    lines.append(" #")
                    lines.append(" # 网络宣告")
                    for net in networks:
                        addr = net.get("address", "")
                        mask_len = net.get("mask_length", 24)
                        if addr:
                            lines.append(f" network {addr} {mask_len}")
                
                lines.append(" quit")
        
        if config.get("vrrp"):
            lines.append("\n# VRRP网关冗余")
            for v in config["vrrp"]:
                iface = v.get("interface", "Vlan-interface10")
                vrid = v.get("vrid", 1)
                vip = v.get("virtual_ip", "")
                prio = v.get("priority", 100)
                lines.append(f"interface {iface}")
                if vip:
                    lines.append(f" vrrp vrid {vrid} virtual-ip {vip}")
                lines.append(f" vrrp vrid {vrid} priority {prio}")
                lines.append(" quit")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_security_config(config: Dict[str, Any],
                                version: ComwareVersion = ComwareVersion.V5) -> str:
        """
        生成安全配置
        
        Args:
            config: 安全配置字典
                - acls: ACL列表
                - port_security: 端口安全配置
                - mac_binding: MAC绑定配置
                - arp_protection: ARP防护配置
                
        Returns:
            配置字符串
        """
        lines = []
        lines.append("\n# ==================== 安全配置 ====================")
        lines.append("#\n# 安全策略配置\n#")
        
        if config.get("acls"):
            lines.append("\n# ACL配置")
            for acl in config["acls"]:
                acl_num = acl.get("number", 2000)
                acl_type = "basic" if 2000 <= acl_num < 3000 else "advanced"
                rules = acl.get("rules", [])

                # V5: acl number, V7: acl basic / acl advanced
                if acl_type == "basic":
                    lines.append(get_cmd(version, "acl_basic", num=acl_num))
                else:
                    lines.append(get_cmd(version, "acl_advanced", num=acl_num))
                
                for i, rule in enumerate(rules, 1):
                    action = rule.get("action", "permit")
                    src = rule.get("source", "")
                    dst = rule.get("destination", "")
                    sport = rule.get("source_port", "")
                    dport = rule.get("destination_port", "")
                    protocol = rule.get("protocol", "")
                    
                    rule_line = f" rule {i} {action}"
                    
                    if acl_type == "basic":
                        if src:
                            rule_line += f" source {src}"
                    else:  # advanced
                        if protocol:
                            rule_line += f" {protocol}"
                        if src:
                            rule_line += f" source {src}"
                        if dst:
                            rule_line += f" destination {dst}"
                        if dport:
                            rule_line += f" destination-port eq {dport}"
                    
                    lines.append(rule_line)
                
                lines.append(" quit")
        
        if config.get("port_security"):
            lines.append("\n# 端口安全配置")
            for psec in config["port_security"]:
                interface = psec.get("interface", "")
                max_mac = psec.get("max_mac", 1)
                violation = psec.get("violation", "shutdown")
                
                if interface:
                    lines.append(f"\ninterface {interface}")
                    lines.append(" port-security enable")
                    lines.append(f" port-security max-mac-count {max_mac}")
                    lines.append(f" port-security violation {violation}")
                    lines.append(" quit")
        
        if config.get("mac_binding"):
            lines.append("\n# MAC地址绑定")
            for bind in config["mac_binding"]:
                mac = bind.get("mac", "")
                interface = bind.get("interface", "")
                vlan = bind.get("vlan", 1)
                
                if mac and interface:
                    lines.append(f"mac-address static {mac} interface {interface} vlan {vlan}")
        
        if config.get("arp_protection"):
            arp = config["arp_protection"]
            if arp.get("enable"):
                lines.append("\n# ARP防护配置")
                lines.append("arp-check enable")
                
                if arp.get("static_entries"):
                    lines.append(" # 静态ARP条目")
                    for entry in arp["static_entries"]:
                        ip = entry.get("ip", "")
                        mac = entry.get("mac", "")
                        interface = entry.get("interface", "")
                        if ip and mac:
                            lines.append(f"arp static {ip} {mac} {interface}")
        
        # DAI 动态 ARP 检测
        if config.get("arp_detection"):
            ad = config["arp_detection"]
            lines.append("\n# DAI 动态ARP检测")
            for v in (ad.get("vlans") or []): lines.append(f"arp detection vlan {v}")
            lines.append("arp detection validate src-mac dst-mac ip")
            for port in (ad.get("trusted_ports") or []):
                lines.append(f"interface {port}"); lines.append(" arp detection trust"); lines.append("#")

        # IP Source Guard
        if config.get("ip_source_guard"):
            isg = config["ip_source_guard"]
            lines.append("\n# IP Source Guard")
            for port in (isg.get("ports") or []):
                lines.append(f"interface {port}")
                lines.append(" ip verify source ip-address mac-address")
                lines.append("#")

        if config.get("storm_control"):
            sc = config["storm_control"]
            lines.append("\n# 风暴控制")
            for port in (sc.get("ports") or []):
                lines.extend([f"interface {port}",f" broadcast-suppression pps {sc.get('broadcast_pps',1000)}",f" multicast-suppression pps {sc.get('multicast_pps',1000)}","#"])

        if config.get("ipsec"):
            ipsec = config["ipsec"]
            lines.append("\n# IPSec VPN")
            lines.extend(["ike proposal 1"," encryption-algorithm aes-cbc-256"," dh group14"," authentication-algorithm sha256","ike peer vpn-peer"," pre-shared-key cipher "+ipsec.get("pre_shared_key","vpn-key")," remote-address "+ipsec.get("peer_ip","1.2.3.4"),"ipsec transform-set TS"," esp encryption-algorithm aes-cbc-256"," esp authentication-algorithm sha256","acl advanced 3000"," rule 5 permit ip source "+ipsec.get("local_net","192.168.1.0")+" 0.0.0.255 destination "+ipsec.get("remote_net","192.168.2.0")+" 0.0.0.255","ipsec policy vpn-policy 10 isakmp"," transform-set TS"," security acl 3000"," ike-peer vpn-peer"])

        return "\n".join(lines)
    
    @staticmethod
    def generate_interface_config(config: Dict[str, Any]) -> str:
        """
        生成接口配置
        
        Args:
            config: 接口配置字典
                - eth_trunks: Eth-Trunk配置
                - lldp: LLDP配置
                - rate_limit: 速率限制配置
                
        Returns:
            配置字符串
        """
        lines = []
        lines.append("\n# ==================== 接口配置 ====================")
        lines.append("#\n# 接口高级配置\n#")
        
        if config.get("eth_trunks"):
            lines.append("\n# 端口聚合配置")
            for trunk in config["eth_trunks"]:
                trunk_id = trunk.get("trunk_id", 1)
                mode = trunk.get("mode", "lacp-static")
                members = trunk.get("member_ports", [])
                link_type = trunk.get("port_link_type", "trunk")
                trunk_vlans = trunk.get("trunk_vlans", [])
                
                lines.append(f"\ninterface Bridge-Aggregation {trunk_id}")
                lines.append(f" link-aggregation mode {mode}")
                lines.append(f" port link-type {link_type}")
                
                if link_type == "trunk" and trunk_vlans:
                    vlan_str = ",".join(map(str, trunk_vlans))
                    lines.append(f" port trunk permit vlan {vlan_str}")
                
                lines.append(" quit")
                
                if members:
                    for member in members:
                        lines.append(f"\ninterface {member}")
                        lines.append(f" port link-aggregation group {trunk_id}")
                        lines.append(" quit")
        
        if config.get("lldp"):
            lldp = config["lldp"]
            if lldp.get("enable"):
                lines.append("\n# LLDP配置")
                lines.append("lldp global enable")
                mode = lldp.get("mode", "both")
                lines.append(f"lldp work {mode}")
        
        if config.get("rate_limit"):
            lines.append("\n# 接口速率限制")
            for rl in config["rate_limit"]:
                interface = rl.get("interface", "")
                cir = rl.get("cir", 1000)  # kbps
                cbs = rl.get("cbs", 125000)  # bytes
                
                if interface:
                    lines.append(f"\ninterface {interface}")
                    lines.append(f" qos lr outbound cir {cir} cbs {cbs}")
                    lines.append(" quit")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_service_config(config: Dict[str, Any]) -> str:
        """
        生服务配置
        
        Args:
            config: 服务配置字典
                - ntp: NTP配置
                - snmp: SNMP配置
                - log: 日志配置
                
        Returns:
            配置字符串
        """
        lines = []
        lines.append("\n# ==================== 服务配置 ====================")
        lines.append("#\n# 系统服务配置\n#")
        
        if config.get("ntp"):
            ntp = config["ntp"]
            servers = ntp.get("servers", [])
            timezone = ntp.get("timezone", "UTC+8")
            
            lines.append("\n# NTP服务器配置")
            lines.append("ntp-service enable")
            lines.append(f"clock timezone {timezone}")
            
            for server in servers:
                ip = server.get("ip", "")
                prefer = server.get("prefer", False)
                if ip:
                    pref_str = " preference" if prefer else ""
                    lines.append(f"ntp-service unicast-server {ip}{pref_str}")
        
        if config.get("snmp"):
            snmp = config["snmp"]
            version = snmp.get("version", "v2c")
            
            lines.append("\n# SNMP配置")
            lines.append("snmp-agent")
            lines.append(f" snmp-agent sys-info version {version.replace('v', 'v').lower()}")
            
            if version == "v2c":
                community_read = snmp.get("community_read", "public")
                community_write = snmp.get("community_write", "")
                
                lines.append(f" snmp-agent community read {community_read}")
                if community_write:
                    lines.append(f" snmp-agent community write {community_write}")
            
            if snmp.get("trap_enable"):
                trap_host = snmp.get("trap_host", "")
                if trap_host:
                    lines.append(f" snmp-agent target-host trap address udp-domain {trap_host} params securityname {community_read} v2c")
        
        if config.get("log"):
            log = config["log"]
            host = log.get("host", "")
            level = log.get("log_level", "informational")
            
            if host:
                lines.append("\n# 日志配置")
                lines.append("info-center enable")
                lines.append("info-center loghost " + host)
                lines.append(f"info-center source default module default level {level}")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_wan_config(config: Dict[str, Any]) -> str:
        """生成 H3C 路由器 WAN/PPPoE/NAT 配置"""
        if not config:
            return ""
        lines = ["# ==================== WAN 广域网 ===================="]
        conn = config.get("connectionType", "pppoe")
        # PPPoE
        if conn == "pppoe":
            user = config.get("pppoeUser", "vpdnuser")
            passwd = config.get("pppoePass", "user1234")
            physical = config.get("pppoePhysical", "GigabitEthernet0/0/0")
            lines.append("dialer-group 1 rule ip permit")
            lines.append("")
            lines.append("interface Dialer1")
            lines.append(" dialer bundle enable")
            lines.append(" dialer-group 1")
            lines.append(" ip address ppp-negotiate")
            lines.append(f" ppp chap user {user}")
            lines.append(f" ppp chap password simple {passwd}")
            lines.append(" dialer timer idle 0")
            lines.append(" nat outbound")
            lines.append("")
            lines.append(f"interface {physical}")
            lines.append(" pppoe-client dial-bundle-number 1")
            lines.append("")
            lines.append("ip route-static 0.0.0.0 0 Dialer 1")
        # 静态IP
        elif conn == "static":
            physical = config.get("staticPhysical", "GigabitEthernet0/0/0")
            ip = config.get("staticIp", "")
            mask = config.get("staticMask", "255.255.255.0")
            gw = config.get("staticGateway", "")
            if ip:
                lines.append(f"interface {physical}")
                lines.append(f" ip address {ip} {mask}")
                lines.append(" nat outbound")
                lines.append("")
            if gw:
                lines.append(f"ip route-static 0.0.0.0 0 {gw}")
        # DHCP
        elif conn == "dhcp":
            physical = config.get("dhcpPhysical", "GigabitEthernet0/0/0")
            lines.append(f"interface {physical}")
            lines.append(" ip address dhcp-alloc")
            lines.append(" nat outbound")
        # DNAT
        dnat = config.get("dnatRules", [])
        if dnat and config.get("natEnabled", True):
            lines.append("")
            lines.append("# DNAT 端口映射")
            for r in dnat:
                proto = r.get("protocol", "tcp")
                port = r.get("publicPort", 80)
                in_ip = r.get("internalIp", "")
                in_port = r.get("internalPort", port)
                if in_ip:
                    lines.append(f"nat server protocol {proto} global current-interface {port} inside {in_ip} {in_port}")
        # DHCP Server
        if config.get("dhcpEnabled"):
            iface = config.get("dhcpInterface", "Vlanif1")
            net = config.get("dhcpNetwork", "192.168.1.0")
            mask = config.get("dhcpMask", "255.255.255.0")
            gw = config.get("dhcpGateway", "192.168.1.1")
            dns = config.get("dhcpDns", "114.114.114.114")
            lines.append("")
            lines.append("# DHCP Server")
            lines.append("dhcp enable")
            lines.append("dhcp server ip-pool pool1")
            lines.append(f" network {net} mask {mask}")
            lines.append(f" gateway-list {gw}")
            lines.append(f" dns-list {dns}")
            lines.append(" quit")
            lines.append(f"interface {iface}")
            lines.append(f" ip address {gw} {mask}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def generate_all(config: Dict[str, Any],
                    version: ComwareVersion = ComwareVersion.V5) -> str:
        """
        生成完整配置（支持 Comware V5/V7 版本区分）

        Args:
            config: 完整配置字典
            version: Comware 系统版本
        """
        # 根据配置内容自动判断设备类型（用户思维：不让用户手动选）
        device_type = "路由器" if "wan" in config else "交换机"
        device_model = config.get("device_model", "")
        description = config.get("description", "")
        if device_model:
            description = f"{description} · 型号: {device_model}"

        sections = []
        sections.append(H3CConfigGenerator.generate_header(
            description,
            version,
            device_type
        ))

        if config.get("basic"):
            sections.append(H3CConfigGenerator.generate_basic_config(config["basic"], version))

        if config.get("wan"):
            sections.append(H3CConfigGenerator.generate_wan_config(config["wan"]))

        if config.get("vlan"):
            sections.append(H3CConfigGenerator.generate_vlan_config(config["vlan"]))

        if config.get("routing"):
            sections.append(H3CConfigGenerator.generate_routing_config(config["routing"]))

        if config.get("security"):
            sections.append(H3CConfigGenerator.generate_security_config(config["security"], version))

        if config.get("interface"):
            sections.append(H3CConfigGenerator.generate_interface_config(config["interface"]))

        if config.get("service"):
            sections.append(H3CConfigGenerator.generate_service_config(config["service"]))

        if config.get("gre"):
            gre = config["gre"]
            sections.append("\n# GRE隧道\ninterface Tunnel0\n ip address "+gre.get("tunnel_ip","10.0.0.1")+" "+gre.get("tunnel_mask","255.255.255.0")+"\n tunnel-protocol gre\n source "+gre.get("source","GigabitEthernet0/0")+"\n destination "+gre.get("destination","2.2.2.2")+"\n#")

        if config.get("ipv6"):
            sections.append(H3CConfigGenerator.generate_ipv6_config(config["ipv6"]))

        sections.append("\n\nreturn")

        return "\n".join(sections)

    @staticmethod
    def generate_ipv6_config(params: Dict[str, Any]) -> str:
        """生成 H3C IPv6 配置"""
        out = ["\n# H3C IPv6 配置", "ipv6"]
        for iface in (params.get("interfaces") or []):
            port = iface.get("interface", "GigabitEthernet0/0/1")
            addr = iface.get("ipv6_address", "")
            if addr:
                out.append(f"interface {port}")
                out.append(" ipv6 enable")
                out.append(f" ipv6 address {addr}")
                if iface.get("ipv6_ra", True):
                    out.append(" ipv6 nd ra")
                out.append("#")
        for r in (params.get("ipv6_routes") or []):
            out.append(f"ipv6 route-static {r.get('dest','::/0')} {r.get('nexthop','')}")
        return "\n".join(out)
