#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""华为路由器 WAN / PPPoE / NAT 配置模块"""

from app.engine.vendors.huawei.version_config import VrpVersion, get_cmd


class HuaweiWanGenerator:
    """华为路由器 WAN 广域网配置生成器"""

    @staticmethod
    def generate_pppoe(wan_config: dict) -> str:
        """生成 PPPoE 拨号配置（Dialer 接口 + 物理接口绑定 + NAT + 默认路由）"""
        lines = ["#", "# PPPoE 拨号配置", "#"]
        user = wan_config.get("pppoeUser", "pppoe-user")
        password = wan_config.get("pppoePass", "123456")
        physical = wan_config.get("pppoePhysical", "GigabitEthernet0/0/0")
        mtu = wan_config.get("pppoeMtu", 1492)
        dns1 = wan_config.get("primaryDns", "")
        dns2 = wan_config.get("secondaryDns", "")

        # ACL for NAT（华为官网示例用 2000 号基本 ACL）
        lines.append("acl number 2000")
        lines.append(f" rule 5 permit source {wan_config.get('lanNetwork', '192.168.1.0')} 0.0.0.255")
        lines.append("")
        # Dialer 接口
        lines.append("interface Dialer1")
        lines.append(" link-protocol ppp")
        lines.append(f" ppp chap user {user}")
        lines.append(f" ppp chap password simple {password}")
        lines.append(f" ppp pap local-user {user} password simple {password}")
        lines.append(" ip address ppp-negotiate")
        lines.append(f" dialer user {user}")
        lines.append(" dialer bundle 1")
        lines.append(" dialer-group 1")
        lines.append(" nat outbound 2000")
        if mtu:
            lines.append(f" mtu {mtu}")
            lines.append(f" tcp adjust-mss {mtu - 40}")
        if dns1:
            lines.append(" ppp ipcp dns admit-any")
            lines.append(" ppp ipcp dns request")
        lines.append("")
        # 物理接口绑定
        lines.append(f"interface {physical}")
        lines.append(" pppoe-client dial-bundle-number 1")
        lines.append("")
        # 默认路由
        lines.append("ip route-static 0.0.0.0 0.0.0.0 Dialer1")
        lines.append("#")
        return "\n".join(lines)

    @staticmethod
    def generate_static_ip(wan_config: dict) -> str:
        """生成静态 IP 上网配置"""
        lines = ["#", "# 静态 IP WAN 配置", "#"]
        ip = wan_config.get("staticIp", "")
        mask = wan_config.get("staticMask", "255.255.255.0")
        gateway = wan_config.get("staticGateway", "")
        physical = wan_config.get("staticPhysical", "GigabitEthernet0/0/0")
        if ip:
            lines.append("acl number 2000")
            lines.append(" rule 5 permit ip")
            lines.append("")
            lines.append(f"interface {physical}")
            lines.append(f" ip address {ip} {mask}")
            lines.append(" nat outbound 2000")
            lines.append("")
        if gateway:
            lines.append(f"ip route-static 0.0.0.0 0.0.0.0 {gateway}")
        # DNS
        dns1 = wan_config.get("primaryDns", "")
        dns2 = wan_config.get("secondaryDns", "")
        if dns1:
            lines.append(f"dns resolve")
            lines.append(f"dns server {dns1}")
        if dns2:
            lines.append(f"dns server {dns2}")
        lines.append("#")
        return "\n".join(lines)

    @staticmethod
    def generate_dhcp(wan_config: dict) -> str:
        """生成 DHCP 自动获取 WAN 配置"""
        lines = ["#", "# DHCP WAN 配置", "#"]
        physical = wan_config.get("dhcpPhysical", "GigabitEthernet0/0/0")
        lines.append("acl 3998")
        lines.append(" rule 10 permit ip")
        lines.append("")
        lines.append(f"interface {physical}")
        lines.append(" ip address dhcp-alloc")
        lines.append(" nat outbound 2000")
        lines.append("#")
        return "\n".join(lines)

    @staticmethod
    def generate_dnat(rules: list) -> str:
        """生成 DNAT 端口映射（nat server）"""
        if not rules:
            return ""
        lines = ["#", "# DNAT 端口映射", "#"]
        for rule in rules:
            proto = rule.get("protocol", "tcp")
            port = rule.get("publicPort", 80)
            in_ip = rule.get("internalIp", "")
            in_port = rule.get("internalPort", port)
            desc = rule.get("description", "")
            if in_ip:
                comment = f" description {desc}" if desc else ""
                lines.append(
                    f"nat server protocol {proto} global current-interface {port}"
                    f" inside {in_ip} {in_port}{comment}"
                )
        lines.append("#")
        return "\n".join(lines)

    @staticmethod
    def generate_multi_wan(wan_config: dict) -> str:
        """生成多线负载分担配置（ip load-balance + 策略路由）"""
        lines = ["#", "# 多线负载分担", "#"]
        interfaces = wan_config.get("wanInterfaces", [])
        if not interfaces:
            return ""
        lines.append("# 全局启用负载均衡")
        lines.append("ip load-balance hash src-ip")
        lines.append("")
        for i, iface in enumerate(interfaces):
            ifname = iface.get("interface", f"GE0/0/{i}")
            gw = iface.get("gateway", "")
            desc = iface.get("description", f"WAN{i+1}")
            lines.append(f"# {desc}")
            lines.append(f"interface {ifname}")
            lines.append(" nat outbound 3998")
            lines.append("")
            if gw:
                lines.append(f"ip route-static 0.0.0.0 0.0.0.0 {gw} preference {60 + i * 5}")
        lines.append("#")
        return "\n".join(lines)

    @staticmethod
    def generate_dhcp_server(wan_config: dict) -> str:
        """生成 DHCP Server 配置（LAN侧）"""
        if not wan_config.get("dhcpEnabled"):
            return ""
        lines = ["#", "# DHCP Service (LAN)", "#"]
        iface = wan_config.get("dhcpInterface", "Vlanif1")
        network = wan_config.get("dhcpNetwork", "192.168.1.0")
        mask = wan_config.get("dhcpMask", "255.255.255.0")
        gw = wan_config.get("dhcpGateway", "192.168.1.1")
        start = wan_config.get("dhcpRangeStart", "")
        end = wan_config.get("dhcpRangeEnd", "")
        dns = wan_config.get("dhcpDns", "114.114.114.114")
        lines.append("dhcp enable")
        lines.append("")
        lines.append(f"interface {iface}")
        lines.append(f" ip address {gw} {mask}")
        lines.append(" dhcp select interface")
        lines.append(f" dhcp server dns-list {dns}")
        if start and end:
            lines.append(f" dhcp server ip-range {start} {end}")
        lines.append("#")
        return "\n".join(lines)

    @staticmethod
    def generate_ipv6(ipv6_config: dict) -> str:
        """生成 IPv6 基础配置"""
        out = ["# IPv6 配置", "ipv6"]
        for iface in (ipv6_config.get("interfaces") or []):
            port = iface.get("interface", "GigabitEthernet0/0/1")
            addr = iface.get("ipv6_address", "")
            if addr:
                out.append(f"interface {port}")
                out.append(" ipv6 enable")
                out.append(f" ipv6 address {addr}")
                if iface.get("ipv6_ra", True):
                    out.append(" ipv6 nd ra")
                    out.append(" undo ipv6 nd ra halt")
                out.append("#")
        for r in (ipv6_config.get("ipv6_routes") or []):
            out.append(f"ipv6 route-static {r.get('dest','::/0')} {r.get('nexthop','')}")
        return "\n".join(out)

    @staticmethod
    def generate_wireless(wlan_config: dict) -> str:
        """生成 WLAN 无线配置（SSID + 安全 + AP 组）"""
        out = ["# WLAN 无线配置", "wlan"]
        for ssid in (wlan_config.get("ssids") or []):
            name = ssid.get("name", "OFFICE")
            out.extend([
                f" ssid-profile name {name}",
                f"  ssid {ssid.get('ssid', f'{name}-WiFi')}",
            ])
            sec = ssid.get("security", "wpa2")
            if sec == "wpa2":
                out.append(f" security wpa2 psk pass-phrase {ssid.get('passphrase','admin123')}")
            elif sec == "wpa3":
                out.append(f" security wpa3 sae pass-phrase {ssid.get('passphrase','admin123')}")
            out.append(f"!")
        for radio in (wlan_config.get("radios") or []):
            out.extend([
                f"ap-group name {radio.get('ap_group','DEFAULT')}",
                f" ap-system-profile DEFAULT",
                f" radio {radio.get('radio_id',0)}",
                f"  channel {radio.get('channel',6)}",
                f"  power {radio.get('power',20)}",
                f"!",
            ])
        out.append("#")
        return "\n".join(out)

    @staticmethod
    def generate_wan_all(wan_config: dict) -> str:
        """生成完整的 WAN 配置"""
        if not wan_config:
            return ""
        sections = []
        conn_type = wan_config.get("connectionType", "pppoe")
        if conn_type == "pppoe":
            sections.append(HuaweiWanGenerator.generate_pppoe(wan_config))
        elif conn_type == "static":
            sections.append(HuaweiWanGenerator.generate_static_ip(wan_config))
        elif conn_type == "dhcp":
            sections.append(HuaweiWanGenerator.generate_dhcp(wan_config))
        # NAT
        if wan_config.get("natEnabled", True):
            dnat_rules = wan_config.get("dnatRules", [])
            if dnat_rules:
                sections.append(HuaweiWanGenerator.generate_dnat(dnat_rules))
        # 多线
        if wan_config.get("wanCount", 1) > 1:
            sections.append(HuaweiWanGenerator.generate_multi_wan(wan_config))
        # DHCP Server
        if wan_config.get("dhcpEnabled"):
            sections.append(HuaweiWanGenerator.generate_dhcp_server(wan_config))
        return "\n\n".join(s for s in sections if s)
