"""Juniper Junos OS 配置生成器。

Junos 使用层级化 set/delete 命令，完全不同于 IOS。
- 接口: ge-0/0/0 格式
- VLAN: set vlans <name> vlan-id <id>
- 路由: set protocols ospf 等
"""
from __future__ import annotations
from typing import Any, Dict, List


class JuniperConfigGenerator:

    @staticmethod
    def generate_basic(params: Dict[str, Any]) -> str:
        out: List[str] = ["# 基础配置"]
        out.append("configure")
        if params.get("hostname"): out.append(f"set system host-name {params['hostname']}")
        if params.get("password"): out.append(f"set system root-authentication plain-text-password")
        out.append("set system login user admin class super-user")
        if params.get("user"):
            u = params["user"]
            out.append(f"set system login user {u.get('username','admin')} authentication plain-text-password")
        if params.get("enable_ssh"):
            ssh = params.get("ssh", {})
            out.extend(["set system services ssh", f"set system services ssh protocol-version v2"])
        if params.get("ntp"):
            for s in (params["ntp"].get("servers") or ["202.120.2.101"]):
                out.append(f"set system ntp server {s}")
        if params.get("snmp"):
            s = params["snmp"]
            out.append(f"set snmp community {s.get('community_read','public')} authorization read-only")
            if s.get("sys_location"): out.append(f"set snmp location {s['sys_location']}")
        if params.get("syslog"):
            out.append(f"set system syslog host {params['syslog'].get('host','')} any info")
        return "\n".join(out)

    @staticmethod
    def generate_vlan(params: Dict[str, Any]) -> str:
        out = ["# VLAN 配置"]
        for vlan in (params.get("vlans") or []):
            vid = vlan.get("id", vlan.get("vlan_id", ""))
            name = vlan.get("name", f"VLAN{vid}")
            out.append(f"set vlans {name} vlan-id {vid}")
        for iface in (params.get("interfaces") or []):
            port = iface.get("interface", "").replace("GigabitEthernet","ge-").replace("/","/")
            t = iface.get("type", "access")
            out.append(f"set interfaces {port} unit 0 family ethernet-switching")
            if t == "trunk":
                out[-1] += " port-mode trunk"
                vlans = iface.get("trunk_vlans") or iface.get("allowed_vlans")
                if vlans:
                    vlist = vlans if isinstance(vlans, str) else ",".join(str(v) for v in vlans)
                    out.append(f"set interfaces {port} unit 0 family ethernet-switching vlan members [ {vlist} ]")
            else:
                vid = iface.get("vlan_id", "")
                out.append(f"set interfaces {port} unit 0 family ethernet-switching vlan members {f'VLAN{vid}' if vid else 'default'}")
        return "\n".join(out)

    @staticmethod
    def generate_routing(params: Dict[str, Any]) -> str:
        out = ["# 路由配置"]
        for r in (params.get("static_routes") or []):
            dest = r.get("dest", r.get("network", ""))
            mask = r.get("mask", "255.255.255.0")
            gw = r.get("nexthop", r.get("gateway", ""))
            cidr = sum(bin(int(x)).count('1') for x in mask.split('.'))
            out.append(f"set routing-options static route {dest}/{cidr} next-hop {gw}")
        if params.get("default_route"):
            out.append(f"set routing-options static route 0.0.0.0/0 next-hop {params['default_route'].get('nexthop','')}")
        if params.get("ospf"):
            o = params["ospf"]
            for net in (o.get("networks") or []):
                out.append(f"set protocols ospf area {net.get('area','0')} interface {net.get('network','ge-0/0/0')}")
        if params.get("bgp"):
            bgp = params["bgp"]
            asn = bgp.get("as_number", 65001)
            rid = bgp.get("router_id", "")
            out.append(f"set protocols bgp group EBGP type external")
            if rid: out.append(f"set routing-options router-id {rid}")
            for peer in (bgp.get("peers") or []):
                out.append(f"set protocols bgp group EBGP neighbor {peer.get('ip','')} peer-as {peer.get('asn',65001)}")
        return "\n".join(out)

    @staticmethod
    def generate_security(params: Dict[str, Any]) -> str:
        out = ["# 安全配置"]
        for acl in (params.get("acls") or []):
            for rule in (acl.get("rules") or []):
                action = rule.get("action", "permit")
                src = rule.get("sourceIp", rule.get("source", "any"))
                dst = rule.get("destIp", rule.get("destination", "any"))
                out.append(f"set firewall family inet filter ACL term rule1 from source-address {src}")
                out.append(f"set firewall family inet filter ACL term rule1 from destination-address {dst}")
                out.append(f"set firewall family inet filter ACL term rule1 then {action}")
        for ps in (params.get("port_security") or []):
            out.append(f"set interfaces {ps['interface']} unit 0 family ethernet-switching port-security")
            out.append(f"set interfaces {ps['interface']} unit 0 family ethernet-switching port-security maximum-mac-count {ps.get('max_mac',1)}")
        return "\n".join(out)

    @staticmethod
    def generate_interface(params: Dict[str, Any]) -> str:
        out = ["# 接口配置"]
        for trunk in (params.get("eth_trunks") or []):
            tid = trunk.get("trunk_id", 1)
            out.append(f"set interfaces ae{tid} aggregated-ether-options lacp active")
            out.append(f"set interfaces ae{tid} unit 0 family ethernet-switching port-mode trunk")
            for member in (trunk.get("members") or []):
                out.append(f"set interfaces {member} ether-options 802.3ad ae{tid}")
        if params.get("lldp", {}).get("enable", True):
            out.extend(["set protocols lldp interface all"])
        return "\n".join(out)

    @staticmethod
    def generate_wan(params: Dict[str, Any]) -> str:
        out = ["# WAN 上网"]
        t = params.get("connectionType", "static")
        iface = params.get("interface", "ge-0/0/0")
        out.append(f"set interfaces {iface} unit 0")
        if t == "pppoe":
            out.append(f"set interfaces pp0 unit 0 pppoe-options underlying-interface {iface}")
            out.append(f"set interfaces pp0 unit 0 family inet negotiate-address")
        elif t == "dhcp":
            out.append(f"set interfaces {iface} unit 0 family inet dhcp")
        else:
            out.append(f"set interfaces {iface} unit 0 family inet address {params.get('wanIp','')}/24")
        return "\n".join(out)

    @staticmethod
    def generate_dhcp(params: Dict[str, Any]) -> str:
        out = ["# DHCP"]
        for line in (params.get("dhcpLines") or params.get("lines") or []):
            net, mask = line.get("network", ""), line.get("mask", "24")
            out.extend([
                f"set system services dhcp-local-server group DHCP interface {line.get('interface','irb.0')}",
                f"set access address-assignment pool DHCP-POOL family inet network {net}/{mask}",
            ])
            if line.get("gateway"): out.append(f"set access address-assignment pool DHCP-POOL family inet dhcp-attributes router {line['gateway']}")
        return "\n".join(out)

    @staticmethod
    def generate_ipv6(params: Dict[str, Any]) -> str:
        out = ["# IPv6 配置"]
        for iface in (params.get("interfaces") or []):
            port = iface.get("interface", "ge-0/0/1")
            addr = iface.get("ipv6_address", "")
            if addr:
                out.append(f"set interfaces {port} unit 0 family inet6 address {addr}")
                if iface.get("ipv6_ra", True):
                    out.append(f"set protocols router-advertisement interface {port} max-advertisement-interval 30")
        return "\n".join(out)

    _MAP = {
        "basic": generate_basic, "vlan": generate_vlan,
        "routing": generate_routing, "security": generate_security,
        "interface": generate_interface, "wan": generate_wan, "dhcp": generate_dhcp,
        "ipv6": generate_ipv6,
        "gre": lambda p: f"# GRE\nset interfaces gr-0/0/0 unit 0 tunnel source {p.get('source','ge-0/0/0')}\nset interfaces gr-0/0/0 unit 0 tunnel destination {p.get('destination','2.2.2.2')}\nset interfaces gr-0/0/0 unit 0 family inet address {p.get('tunnel_ip','10.0.0.1')}/30",
    }

    @staticmethod
    def generate_all(config: Dict[str, Any]) -> str:
        hostname = config.get("basic", {}).get("hostname", "JUNIPER")
        sections = [f"# Juniper {hostname} Configuration\n# Generated by NetCmdGen\n"]
        for key, fn in JuniperConfigGenerator._MAP.items():
            if config.get(key): sections.append(fn(config[key]))
        return "\n".join(sections + ["# commit confirm\n# commit"])
