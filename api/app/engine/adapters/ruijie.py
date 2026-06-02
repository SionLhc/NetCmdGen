"""锐捷适配器。

锐捷 Generator 结构：
- RuijieBasicGenerator.generate_basic_all(dict)  ← basic 统一入口
- RuijieVLANGenerator.generate_vlans / generate_interface / generate_vlanif  ← vlan 细粒度
- RuijieRoutingGenerator  ← 静态路由 / OSPF / BGP
- RuijieSecurityGenerator  ← ACL / 端口安全 / 流量过滤
- RuijieInterfaceGenerator  ← Eth-Trunk / LLDP / PoE / 环路检测
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.engine.base import FeatureNotSupported
from app.engine.vendors.ruijie import (
    RuijieBasicGenerator,
    RuijieVLANGenerator,
    RuijieRoutingGenerator,
    RuijieSecurityGenerator,
    RuijieInterfaceGenerator,
)


class RuijieAdapter:
    vendor_code = "ruijie"
    vendor_name = "锐捷 Ruijie"
    supported_features = ("basic", "vlan", "routing", "security", "interface", "service")

    # ── basic ───────────────────────────────────────────────
    def _gen_basic(self, params: Dict[str, Any]) -> str:
        return RuijieBasicGenerator.generate_basic_all(params)

    # ── vlan ────────────────────────────────────────────────
    def _gen_vlan(self, params: Dict[str, Any]) -> str:
        out: List[str] = ["!", "# VLAN配置", "!"]

        if "vlans" in params:
            out.append(RuijieVLANGenerator.generate_vlans(params["vlans"]))

        if "interfaces" in params:
            for iface in params["interfaces"]:
                out.append(RuijieVLANGenerator.generate_interface(
                    iface["interface"],
                    iface.get("type", "access"),
                    iface.get("vlan_id"),
                    iface.get("trunk_vlans"),
                    iface.get("pvid"),
                ))

        if "vlanifs" in params:
            for vf in params["vlanifs"]:
                out.append(RuijieVLANGenerator.generate_vlanif(
                    vf["vlan_id"],
                    vf["ip_address"],
                    vf.get("mask", "255.255.255.0"),
                    vf.get("description"),
                ))

        return "\n".join(out)

    # ── routing ────────────────────────────────────────────
    def _gen_routing(self, params: Dict[str, Any]) -> str:
        """生成路由配置（静态路由 / OSPF / BGP）。"""
        out: List[str] = ["!", "# 路由配置", "!"]

        if 'static_routes' in params:
            out.append(RuijieRoutingGenerator.generate_static_routes(
                params['static_routes']
            ))

        if 'ospf' in params:
            ospf = params['ospf']
            out.append(RuijieRoutingGenerator.generate_ospf(
                ospf.get('process_id', 1),
                ospf['router_id'],
                ospf['networks']
            ))

        if 'bgp' in params:
            bgp = params['bgp']
            out.append(RuijieRoutingGenerator.generate_bgp(
                bgp['as_number'],
                bgp['router_id'],
                bgp.get('peers', []),
                bgp.get('networks', [])
            ))

        return '\n'.join(out)

    # ── security ───────────────────────────────────────────
    def _gen_security(self, params: Dict[str, Any]) -> str:
        """生成安全配置（ACL / 端口安全 / 流量过滤）。"""
        out: List[str] = ["!", "# 安全配置", "!"]

        if 'acls' in params:
            for acl in params['acls']:
                out.append(RuijieSecurityGenerator.generate_acl(
                    acl['number'],
                    acl['rules'],
                    acl.get('description')
                ))

        if 'port_security' in params:
            for ps in params['port_security']:
                out.append(RuijieSecurityGenerator.generate_port_security(
                    ps['interface'],
                    ps.get('max_mac', 1),
                    ps.get('violation', 'shutdown'),
                    ps.get('sticky', False)
                ))

        if 'traffic_filters' in params:
            for tf in params['traffic_filters']:
                out.append(RuijieSecurityGenerator.generate_traffic_filter(
                    tf['interface'],
                    tf['acl_number'],
                    tf.get('direction', 'in')
                ))

        return '\n'.join(out)

    # ── interface ──────────────────────────────────────────
    def _gen_interface(self, params: Dict[str, Any]) -> str:
        """生成接口配置（Eth-Trunk 聚合 / LLDP / PoE / 环路检测）。"""
        out: List[str] = ["!", "# 接口配置", "!"]

        if 'eth_trunks' in params:
            for trunk in params['eth_trunks']:
                out.append(RuijieInterfaceGenerator.generate_eth_trunk(
                    trunk['trunk_id'],
                    trunk.get('mode', 'lacp'),
                    trunk.get('members'),
                    trunk.get('description')
                ))

        if 'lldp' in params:
            lldp = params['lldp']
            out.append(RuijieInterfaceGenerator.generate_lldp(
                lldp.get('enable', True),
                lldp.get('mode', 'tx_rx'),
                lldp.get('interval', 30),
                lldp.get('holdtime', 120)
            ))

        if 'poe_interfaces' in params:
            for poe in params['poe_interfaces']:
                out.append(RuijieInterfaceGenerator.generate_poe(
                    poe.get('interface'),
                    poe.get('enable', True),
                    poe.get('priority', 'low'),
                    poe.get('power')
                ))

        if 'loop_detect' in params:
            ld = params['loop_detect']
            out.append(RuijieInterfaceGenerator.generate_loop_detect(
                ld.get('enable', True),
                ld.get('interval', 5),
                ld.get('action', 'shutdown')
            ))

        return '\n'.join(out)

    # ── service ────────────────────────────────────────────
    def _gen_service(self, params: Dict[str, Any]) -> str:
        """生成服务配置（DHCP Server / DHCP Relay）。"""
        out: List[str] = ["!", "# 服务配置", "!"]

        if 'dhcp_server' in params:
            dhcp = params['dhcp_server']
            out.append('service dhcp')
            # DHCP 地址池
            if 'pools' in dhcp:
                for pool in dhcp['pools']:
                    out.append(f"ip dhcp pool {pool['name']}")
                    out.append(f" network {pool['network']} {pool['mask']}")
                    if 'default_router' in pool:
                        out.append(f" default-router {pool['default_router']}")
                    if 'dns_servers' in pool:
                        out.append(f" dns-server {' '.join(pool['dns_servers'])}")
                    if 'lease' in pool:
                        out.append(f" lease {pool['lease']}")
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
                f"锐捷暂不支持特性 {feature!r}，可选: {list(self._GEN.keys())}"
            )
        return fn(self, params)

    def generate_full(self, config: Dict[str, Any]) -> str:
        device_type = "路由器" if "wan" in config else "交换机"
        sections = ["!", f"# 锐捷{device_type}配置脚本", "!"]
        for key in ("basic", "vlan", "routing", "security", "interface", "service"):
            if key in config:
                sections.append(self.generate(key, config[key]))
        sections.append("end")
        return "\n".join(sections)
