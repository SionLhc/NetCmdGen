"""TP-LINK JetStream / Omada 交换机配置生成器。

TP-LINK CLI 近似思科 IOS，但有以下差异：
- 端口名称为 gigabitEthernet 1/0/1 格式
- 部分命令缺少思科高级特性（无 EIGRP/PAgP）
- Omada SDN 控制器管理下 CLI 仅基础功能
"""
from __future__ import annotations
from typing import Any, Dict, List


class TPLinkConfigGenerator:

    @staticmethod
    def generate_basic(params: Dict[str, Any]) -> str:
        out = ["!", "# TP-LINK 基础配置", "!"]
        out.append("enable")
        out.append("configure")
        if params.get("hostname"):
            out.append(f"hostname {params['hostname']}")
        if params.get("enable_secret") or params.get("password"):
            pwd = params.get("enable_secret") or params.get("password", {}).get("value", "admin123")
            out.append(f"enable password {pwd}")
        if params.get("enable_ssh"):
            ssh = params.get("ssh", {})
            out.extend([
                "ip ssh server",
                f"ip ssh timeout {ssh.get('timeout', 120)}",
            ])
        if params.get("enable_ssh") or params.get("enable_telnet"):
            out.extend(["line vty 0 4", " login local"])
            out.append(" exit")
        if params.get("user"):
            u = params["user"]
            out.append(f"user name {u.get('username','admin')} privilege {u.get('level',15)} secret 0 {u.get('password','admin123')}")
        if params.get("ntp"):
            for s in (params["ntp"].get("servers") or ["202.120.2.101"]):
                out.append(f"sntp server {s}")
            out.append(f"sntp timezone {params['ntp'].get('timezone','UTC+8')}")
        if params.get("snmp"):
            s = params["snmp"]
            out.append(f"snmp-server community {s.get('community_read','public')} ro")
            if s.get("sys_location"): out.append(f"snmp-server location {s['sys_location']}")
        return "\n".join(out)

    @staticmethod
    def generate_vlan(params: Dict[str, Any]) -> str:
        out = ["!", "# VLAN 配置", "!"]
        for vlan in (params.get("vlans") or []):
            vid = vlan.get("id", vlan.get("vlan_id", ""))
            name = vlan.get("name", f"VLAN{vid}")
            out.extend([f"vlan {vid}", f" name {name}", " exit"])
        for iface in (params.get("interfaces") or []):
            port = iface.get("interface", "")
            t = iface.get("type", "access")
            out.append(f"interface {port}")
            if t == "trunk":
                out.append(" switchport mode trunk")
                vlans = iface.get("trunk_vlans") or iface.get("allowed_vlans")
                if vlans:
                    vlist = vlans if isinstance(vlans, str) else ",".join(str(v) for v in vlans)
                    out.append(f" switchport trunk allowed vlan {vlist}")
            else:
                out.append(" switchport mode access")
                if iface.get("vlan_id"): out.append(f" switchport access vlan {iface['vlan_id']}")
            out.append(" exit")
        return "\n".join(out)

    @staticmethod
    def generate_routing(params: Dict[str, Any]) -> str:
        out = ["!", "# 路由配置", "!"]
        out.append("ip routing")
        for r in (params.get("static_routes") or []):
            out.append(f"ip route {r.get('dest',r.get('network',''))} {r.get('mask','255.255.255.0')} {r.get('nexthop',r.get('gateway',''))}")
        if params.get("default_route"):
            dr = params["default_route"]
            out.append(f"ip route 0.0.0.0 0.0.0.0 {dr.get('nexthop',dr.get('gateway',''))}")
        if params.get("ospf"):
            o = params["ospf"]
            out.extend([f"router ospf {o.get('process_id',1)}"])
            for net in (o.get("networks") or []):
                out.append(f" network {net.get('network','')} {net.get('wildcard','0.0.0.255')} area {net.get('area','0')}")
            out.append(" exit")
        return "\n".join(out)

    @staticmethod
    def generate_security(params: Dict[str, Any]) -> str:
        out = ["!", "# 安全配置", "!"]
        for acl in (params.get("acls") or []):
            for rule in (acl.get("rules") or []):
                out.append(f"access-list {acl.get('number',100)} {rule.get('action','permit')} {rule.get('protocol','ip')} {rule.get('source',rule.get('sourceIp','any'))} {rule.get('destination',rule.get('destIp','any'))}")
        for ps in (params.get("port_security") or []):
            out.extend([
                f"interface {ps['interface']}",
                f" switchport port-security max {ps.get('max_mac',1)}",
                f" switchport port-security violation {ps.get('violation','shutdown')}",
                " exit",
            ])
        return "\n".join(out)

    @staticmethod
    def generate_interface(params: Dict[str, Any]) -> str:
        out = ["!", "# 接口配置", "!"]
        for trunk in (params.get("eth_trunks") or []):
            tid = trunk.get("trunk_id", 1)
            out.append(f"interface range {','.join(trunk.get('members') or [])}")
            out.append(f" channel-group {tid} mode active")
            out.append(" exit")
            out.append(f"interface port-channel {tid}")
            if trunk.get("description"): out.append(f" description {trunk['description']}")
            out.append(" switchport mode trunk")
            out.append(" exit")
        return "\n".join(out)

    @staticmethod
    def generate_wan(params: Dict[str, Any]) -> str:
        out = ["!", "# WAN 上网", "!"]
        t = params.get("connectionType", "static")
        iface = params.get("interface", "gigabitEthernet 1/0/1")
        out.append(f"interface {iface}")
        if t == "pppoe":
            out.append(" pppoe client")
        elif t == "dhcp":
            out.append(" ip address dhcp")
        else:
            out.append(f" ip address {params.get('wanIp','')} {params.get('wanMask','255.255.255.0')}")
        out.append(" exit")
        return "\n".join(out)

    @staticmethod
    def generate_dhcp(params: Dict[str, Any]) -> str:
        out = ["!", "# DHCP", "!"]
        for line in (params.get("dhcpLines") or params.get("lines") or []):
            net, mask = line.get("network", ""), line.get("mask", "255.255.255.0")
            out.extend([
                f"service dhcp server",
                f"ip dhcp server extend-option gateway {line.get('gateway','')}",
                f"ip dhcp server extend-option dns {line.get('dns','8.8.8.8')}",
            ])
        return "\n".join(out)

    @staticmethod
    def generate_ipv6(params: Dict[str, Any]) -> str:
        out = ["# IPv6", "ipv6 enable"]
        for iface in (params.get("interfaces") or []):
            addr = iface.get("ipv6_address", ""); port = iface.get("interface", "gigabitEthernet 1/0/1")
            if addr: out.extend([f"interface {port}", f" ipv6 address {addr}", " exit"])
        return "\n".join(out)

    _MAP = {
        "basic": generate_basic, "vlan": generate_vlan,
        "routing": generate_routing, "security": generate_security,
        "interface": generate_interface, "wan": generate_wan, "dhcp": generate_dhcp,
        "ipv6": generate_ipv6,
    }

    @staticmethod
    def generate_all(config: Dict[str, Any]) -> str:
        hostname = config.get("basic", {}).get("hostname", "TP-LINK")
        sections = [f"! TP-LINK {hostname} Configuration", "!"]
        for key, fn in TPLinkConfigGenerator._MAP.items():
            if config.get(key):
                sections.append(fn(config[key]))
        sections.append("!\nwrite memory")
        return "\n".join(sections)
