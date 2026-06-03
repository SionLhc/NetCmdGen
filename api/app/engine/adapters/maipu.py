"""迈普适配器。

结构与锐捷几乎一致：
- MaipuBasicGenerator.generate_basic_all(dict)  ← basic 统一入口
- MaipuVLANGenerator.generate_vlans / generate_interface / generate_vlanif  ← vlan 细粒度
- MaipuRoutingGenerator  ← 静态路由 / OSPF / BGP
- MaipuSecurityGenerator  ← ACL / 端口安全 / 流量过滤
- MaipuInterfaceGenerator  ← Eth-Trunk / LLDP / PoE / 环路检测
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.engine.base import FeatureNotSupported
from app.engine.vendors.maipu import (
    MaipuBasicGenerator,
    MaipuVLANGenerator,
    MaipuRoutingGenerator,
    MaipuSecurityGenerator,
    MaipuInterfaceGenerator,
)


class MaipuAdapter:
    vendor_code = "maipu"
    vendor_name = "迈普 Maipu"
    supported_features = ("basic", "vlan", "routing", "security", "interface", "service")

    # ── basic ───────────────────────────────────────────────
    def _gen_basic(self, params: Dict[str, Any]) -> str:
        return MaipuBasicGenerator.generate_basic_all(params)

    # ── vlan ────────────────────────────────────────────────
    def _gen_vlan(self, params: Dict[str, Any]) -> str:
        out: List[str] = ["!", "# VLAN配置", "!"]

        if "vlans" in params:
            out.append(MaipuVLANGenerator.generate_vlans(params["vlans"]))

        if "interfaces" in params:
            for iface in params["interfaces"]:
                out.append(MaipuVLANGenerator.generate_interface(
                    iface["interface"],
                    iface.get("type", "access"),
                    iface.get("vlan_id"),
                    iface.get("trunk_vlans"),
                    iface.get("pvid"),
                ))

        if "vlanifs" in params:
            for vf in params["vlanifs"]:
                out.append(MaipuVLANGenerator.generate_vlanif(
                    vf["vlan_id"],
                    vf["ip_address"],
                    vf.get("mask", "255.255.255.0"),
                    vf.get("description"),
                ))

        return "\n".join(out)

    # ── routing ────────────────────────────────────────────
    def _gen_routing(self, params: Dict[str, Any]) -> str:
        """生成路由配置（静态路由 / OSPF / BGP）。"""
        out: List[str] = ['!', '# 路由配置', '!']

        if 'static_routes' in params:
            out.append(MaipuRoutingGenerator.generate_static_routes(
                params['static_routes']
            ))

        if 'ospf' in params:
            ospf = params['ospf']
            out.append(MaipuRoutingGenerator.generate_ospf(
                ospf.get('process_id', 1),
                ospf['router_id'],
                ospf['networks']
            ))

        if 'bgp' in params:
            bgp = params['bgp']
            out.append(MaipuRoutingGenerator.generate_bgp(
                bgp['as_number'],
                bgp['router_id'],
                bgp.get('peers', []),
                bgp.get('networks', [])
            ))

        return '\n'.join(out)

    # ── security ───────────────────────────────────────────
    def _gen_security(self, params: Dict[str, Any]) -> str:
        """生成安全配置（ACL / 端口安全 / 流量过滤）。"""
        out: List[str] = ['!', '# 安全配置', '!']

        if 'acls' in params:
            for acl in params['acls']:
                out.append(MaipuSecurityGenerator.generate_acl(
                    acl['number'],
                    acl['rules'],
                    acl.get('description')
                ))

        if 'port_security' in params:
            for ps in params['port_security']:
                out.append(MaipuSecurityGenerator.generate_port_security(
                    ps['interface'],
                    ps.get('max_mac', 1),
                    ps.get('violation', 'shutdown'),
                    ps.get('sticky', False)
                ))

        if 'traffic_filters' in params:
            for tf in params['traffic_filters']:
                out.append(MaipuSecurityGenerator.generate_traffic_filter(
                    tf['interface'],
                    tf['acl_number'],
                    tf.get('direction', 'in')
                ))

        return '\n'.join(out)

    # ── interface ──────────────────────────────────────────
    def _gen_interface(self, params: Dict[str, Any]) -> str:
        """生成接口配置（Eth-Trunk 聚合 / LLDP / PoE / 环路检测 / 限速）。"""
        out: List[str] = ['!', '# 接口配置', '!']

        if 'eth_trunks' in params:
            for trunk in params['eth_trunks']:
                out.append(MaipuInterfaceGenerator.generate_eth_trunk(
                    trunk['trunk_id'],
                    trunk.get('mode', 'lacp'),
                    trunk.get('members'),
                    trunk.get('description')
                ))

        if 'lldp' in params:
            lldp = params['lldp']
            out.append(MaipuInterfaceGenerator.generate_lldp(
                lldp.get('enable', True),
                lldp.get('mode', 'tx_rx'),
                lldp.get('interval', 30),
                lldp.get('holdtime', 120)
            ))

        if 'poe_interfaces' in params:
            for poe in params['poe_interfaces']:
                out.append(MaipuInterfaceGenerator.generate_poe(
                    poe.get('interface'),
                    poe.get('enable', True),
                    poe.get('priority', 'low'),
                    poe.get('power')
                ))

        if 'loop_detect' in params:
            ld = params['loop_detect']
            out.append(MaipuInterfaceGenerator.generate_loop_detect(
                ld.get('enable', True),
                ld.get('interval', 5),
                ld.get('action', 'shutdown')
            ))

        if 'rate_limits' in params:
            for rl in params['rate_limits']:
                out.append(MaipuInterfaceGenerator.generate_rate_limit(
                    rl['interface'],
                    rl.get('rate_in'),
                    rl.get('rate_out')
                ))

        return '\n'.join(out)

    # ── service ────────────────────────────────────────────
    def _gen_service(self, params: Dict[str, Any]) -> str:
        """生成服务配置（DHCP Server / DHCP Relay / DHCP Snooping）。"""
        out: List[str] = ['!', '# 服务配置', '!']

        if 'dhcp_server' in params:
            dhcp = params['dhcp_server']
            out.append('service dhcp')
            if 'pools' in dhcp:
                for pool in dhcp['pools']:
                    out.append(f"ip dhcp pool {pool['name']}")
                    out.append(f" network {pool['network']} {pool['mask']}")
                    if 'default_router' in pool:
                        out.append(f" default-router {pool['default_router']}")
                    if 'dns_servers' in pool:
                        out.append(f" dns-server {' '.join(pool['dns_servers'])}")
                    out.append('!')

        if 'dhcp_relay' in params:
            relay = params['dhcp_relay']
            for iface in relay.get('interfaces', []):
                out.append(f"interface {iface['name']}")
                out.append(f" ip helper-address {iface['server_ip']}")
                out.append('!')

        if 'dhcp_snooping' in params:
            ds = params['dhcp_snooping']
            if ds.get('enable', True):
                out.append('ip dhcp snooping')
                for port in ds.get('trusted_ports', []):
                    out.append(f"interface {port}")
                    out.append(' ip dhcp snooping trust')
                    out.append('!')

        return '\n'.join(out)

    # ── 统一入口 ─────────────────────────────────────────────
    _GEN = {
        "basic": _gen_basic,
        "vlan": _gen_vlan,
        "routing": _gen_routing,
        "security": _gen_security,
        "interface": _gen_interface,
        "service": _gen_service,
    }

    def generate(self, feature: str, params: Dict[str, Any]) -> str:
        fn = self._GEN.get(feature)
        if fn is None:
            raise FeatureNotSupported(
                f"迈普暂不支持特性 {feature!r}，可选: {list(self._GEN.keys())}"
            )
        return fn(self, params)

    def generate_full(self, config: Dict[str, Any]) -> str:
        device_type = "路由器" if "wan" in config else "交换机"
        sections = ["!", f"# 迈普{device_type}配置脚本", "!"]

        for key in ("basic", "vlan", "routing", "security", "interface", "service", "wan", "dhcp", "nat", "acl", "ipv6"):
            if key not in config:
                continue
            params = config[key]

            if key == "wan":
                sections.append(self._gen_wan(params))
            elif key == "ipv6":
                sections.append(self._gen_ipv6(params))
            elif key == "dhcp":
                sections.append(self._gen_dhcp(params))
            elif key == "nat":
                sections.append(self._gen_nat(params))
            elif key == "acl":
                sections.append(self._gen_acl_separate(params))
            else:
                sections.append(self.generate(key, params))

        sections.append("end")
        return "\n".join(sections)

    # ── IPv6 ────────────────────────────────────────────────
    def _gen_ipv6(self, params: Dict[str, Any]) -> str:
        out = ["!", "# IPv6配置", "!", "ipv6"]
        for iface in (params.get("interfaces") or []):
            addr = iface.get("ipv6_address", "")
            if addr:
                out.append(f"interface {iface.get('interface','GigabitEthernet 0/1')}")
                out.append(" ipv6 enable"); out.append(f" ipv6 address {addr}")
                if iface.get("ipv6_ra", True): out.append(" ipv6 nd ra"); out.append("!")
        return "\n".join(out)

    # ── WAN 口上网 ──────────────────────────────────────────
    def _gen_wan(self, params: Dict[str, Any]) -> str:
        """生成迈普 WAN 口上网配置（PPPoE / 静态IP / DHCP）。"""
        out = ["!", "# WAN口上网配置", "!"]
        wan_type = params.get("connectionType", "static")
        iface = params.get("interface", "GigabitEthernet 0/1")
        out.append(f"interface {iface}")
        out.append(f" description WAN-{wan_type.upper()}")

        if wan_type == "pppoe":
            out.append(" pppoe-client dial-bundle-number 1")
            out.append("!")
            out.append("interface Dialer 1")
            out.append(" ip address negotiate")
            out.append(" dialer user {user}".format(user=params.get("pppoeUser", "")))
            out.append(" dialer bundle 1")
            out.append(" dialer-group 1")
            out.append(" ppp chap user {user}".format(user=params.get("pppoeUser", "")))
            out.append(" ppp chap password simple {pwd}".format(pwd=params.get("pppoePassword", "")))
            out.append("!")
            out.append("dialer-list 1 protocol ip permit")
        elif wan_type == "dhcp":
            out.append(" ip address dhcp")
        else:
            out.append(f" ip address {params.get('wanIp', '')} {params.get('wanMask', '255.255.255.0')}")
            if params.get("wanGateway"):
                out.append(f"!ip route 0.0.0.0 0.0.0.0 {params['wanGateway']}")

        out.append("!")
        return "\n".join(out)

    # ── DHCP 服务 ───────────────────────────────────────────
    def _gen_dhcp(self, params: Dict[str, Any]) -> str:
        """生成迈普 DHCP 服务配置（LAN 侧地址池）。"""
        out = ["!", "# DHCP服务", "!"]
        out.append("service dhcp")
        for line in (params.get("dhcpLines") or params.get("lines") or []):
            net = line.get("network", "")
            mask = line.get("mask", "255.255.255.0")
            gw = line.get("gateway", "")
            dns = line.get("dns", "")
            start_ip = line.get("startIp", "") or line.get("start_ip", "")
            end_ip = line.get("endIp", "") or line.get("end_ip", "")
            lease = line.get("lease", "1")
            out.append(f"ip dhcp pool DHCP-{net.split('.')[2] if net else 'LAN'}")
            out.append(f" network {net} {mask}")
            if gw:
                out.append(f" default-router {gw}")
            if dns:
                out.append(f" dns-server {dns}")
            if start_ip and end_ip:
                out.append(f" range {start_ip} {end_ip}")
            out.append(f" lease {lease}")
            out.append("!")
        return "\n".join(out)

    # ── NAT 端口映射 ────────────────────────────────────────
    def _gen_nat(self, params: Dict[str, Any]) -> str:
        """生成迈普 NAT 端口映射配置。"""
        out = ["!", "# NAT端口映射", "!"]
        rules = params.get("rules") or params.get("natList") or params.get("natLines") or []
        for r in rules:
            proto = r.get("protocol", "tcp")
            ext_port = r.get("externalPort") or r.get("ext_port", "")
            int_ip = r.get("internalIp") or r.get("int_ip", "")
            int_port = r.get("internalPort") or r.get("int_port", "")
            out.append(f"ip nat inside source static {proto} {int_ip} {int_port} interface Dialer 1 {ext_port}")
        out.append("!")
        return "\n".join(out)

    # ── ACL 访问控制 ────────────────────────────────────────
    def _gen_acl_separate(self, params: Dict[str, Any]) -> str:
        """生成迈普 ACL 访问控制配置。"""
        out = ["!", "# ACL访问控制", "!"]
        rules = params.get("rules") or params.get("aclList") or []
        for r in rules:
            action = "permit" if r.get("action") == "allow" else "deny"
            src = r.get("sourceIp") or r.get("source", "any")
            dst = r.get("destIp") or r.get("destination", "any")
            out.append(f"ip access-list extended ACL-{r.get('name', 'FILTER')}")
            out.append(f" {action} ip {src} {dst}")
        out.append("!")
        return "\n".join(out)
