#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NetOps Toolkit - 路由配置模块
"""


class RoutingConfigGenerator:
    """路由配置生成器"""
    
    @staticmethod
    def generate_static_route(dest_network: str,
                             mask: str,
                             next_hop: str = None,
                             interface: str = None,
                             preference: int = None) -> str:
        """生成静态路由配置"""
        config = f"ip route-static {dest_network} {mask}"
        if next_hop:
            config += f" {next_hop}"
        elif interface:
            config += f" {interface}"
        if preference:
            config += f" preference {preference}"
        return config + "\n"
    
    @staticmethod
    def generate_default_route(next_hop: str = None,
                              interface: str = None) -> str:
        """生成默认路由配置"""
        if next_hop:
            return f"ip route-static 0.0.0.0 0.0.0.0 {next_hop}\n"
        elif interface:
            return f"ip route-static 0.0.0.0 0.0.0.0 {interface}\n"
        return ""
    
    @staticmethod
    def generate_ospf_config(process_id: int = 1,
                             router_id: str = None,
                             area_id: str = "0",
                             networks: list = None,
                             interfaces: list = None,
                             cost: int = None) -> str:
        """生成OSPF配置"""
        config_lines = []
        config_lines.append(f"ospf {process_id}")
        if router_id:
            config_lines.append(f" router-id {router_id}")
        config_lines.append("\n")
        
        if cost:
            config_lines.append(f" default-cost {cost}\n")
        
        config_lines.append(f" area {area_id}\n")
        
        if networks:
            for network in networks:
                net_addr = network.get("address")
                net_mask = network.get("mask", "0.0.0.255")
                if net_addr:
                    config_lines.append(f"  network {net_addr} {net_mask}\n")
        
        if interfaces:
            for iface in interfaces:
                config_lines.append(f"  interface {iface}\n")
        
        config_lines.append("#\n")
        return "".join(config_lines)
    
    @staticmethod
    def generate_ospf_interface(interface: str,
                               cost: int = None,
                               priority: int = None,
                               hello_time: int = 10,
                               dead_time: int = 40,
                               area: str = None) -> str:
        """生成接口OSPF配置"""
        config_lines = []
        config_lines.append(f"interface {interface}\n")
        config_lines.append(" ospf enable 1 area 0\n")
        if cost:
            config_lines.append(f" ospf cost {cost}\n")
        if priority:
            config_lines.append(f" ospf dr-priority {priority}\n")
        config_lines.append(f" ospf timer hello {hello_time}\n")
        config_lines.append(f" ospf timer dead {dead_time}\n")
        config_lines.append("#\n")
        return "".join(config_lines)
    
    @staticmethod
    def generate_bgp_config(as_number: int,
                           router_id: str = None,
                           peer_groups: list = None,
                           networks: list = None,
                           import_routes: list = None) -> str:
        """生成BGP配置"""
        config_lines = []
        config_lines.append(f"bgp {as_number}\n")
        if router_id:
            config_lines.append(f" router-id {router_id}\n")
        
        if peer_groups:
            for peer in peer_groups:
                peer_ip = peer.get("ip")
                peer_as = peer.get("as")
                if peer_ip and peer_as:
                    config_lines.append(f" peer {peer_ip} as-number {peer_as}\n")
        
        config_lines.append(" ipv4-family unicast\n")
        
        if networks:
            for network in networks:
                config_lines.append(f"  network {network}\n")
        
        if import_routes:
            for route in import_routes:
                protocol = route.get("protocol", "ospf")
                process = route.get("process", 1)
                config_lines.append(f"  import-route {protocol} process {process}\n")
        
        if peer_groups:
            for peer in peer_groups:
                peer_ip = peer.get("ip")
                config_lines.append(f"  peer {peer_ip} enable\n")
        
        config_lines.append("#\n")
        return "".join(config_lines)
    
    @staticmethod
    def generate_rip_config(version: int = 2,
                           networks: list = None,
                           import_routes: list = None) -> str:
        """生成RIP配置"""
        config_lines = []
        config_lines.append(f"rip 1\n")
        config_lines.append(f" version {version}\n")
        
        if networks:
            for network in networks:
                config_lines.append(f" network {network}\n")
        
        if import_routes:
            for route in import_routes:
                config_lines.append(f" import-route {route}\n")
        
        config_lines.append("#\n")
        return "".join(config_lines)
    
    @staticmethod
    def generate_vrrp(interface: str, vrid: int, virtual_ip: str,
                     priority: int = 100, preempt: bool = True,
                     advertise_interval: int = 1) -> str:
        """生成 VRRP 配置"""
        lines = [f"interface {interface}"]
        lines.append(f" vrrp vrid {vrid} virtual-ip {virtual_ip}")
        lines.append(f" vrrp vrid {vrid} priority {priority}")
        if not preempt:
            lines.append(f" vrrp vrid {vrid} preempt-mode disable")
        lines.append(f" vrrp vrid {vrid} timer advertise {advertise_interval}")
        lines.append("#\n")
        return "\n".join(lines)

    @staticmethod
    def generate_route_all(config: dict) -> str:
        """生成完整路由配置"""
        config_lines = ["#\n", "# 路由配置\n", "#\n"]

        if "static_routes" in config:
            for route in config["static_routes"]:
                config_lines.append(RoutingConfigGenerator.generate_static_route(
                    route["dest_network"],
                    route["mask"],
                    route.get("next_hop"),
                    route.get("interface"),
                    route.get("preference")
                ))

        if "default_route" in config:
            config_lines.append(RoutingConfigGenerator.generate_default_route(
                config["default_route"].get("next_hop"),
                config["default_route"].get("interface")
            ))

        if "ospf" in config:
            config_lines.append("\n#\n# OSPF配置\n#\n")
            ospf_conf = config["ospf"]
            config_lines.append(RoutingConfigGenerator.generate_ospf_config(
                ospf_conf.get("process_id", 1),
                ospf_conf.get("router_id"),
                ospf_conf.get("area_id", "0"),
                ospf_conf.get("networks"),
                ospf_conf.get("interfaces"),
                ospf_conf.get("cost")
            ))

        if "ospf_interfaces" in config:
            for iface in config["ospf_interfaces"]:
                config_lines.append(RoutingConfigGenerator.generate_ospf_interface(
                    iface["interface"],
                    iface.get("cost"),
                    iface.get("priority"),
                    iface.get("hello_time", 10),
                    iface.get("dead_time", 40)
                ))

        if "bgp" in config:
            config_lines.append("\n#\n# BGP配置\n#\n")
            bgp_conf = config["bgp"]
            config_lines.append(RoutingConfigGenerator.generate_bgp_config(
                bgp_conf["as_number"],
                bgp_conf.get("router_id"),
                bgp_conf.get("peers"),
                bgp_conf.get("networks"),
                bgp_conf.get("import_routes")
            ))

        if "rip" in config:
            config_lines.append("\n#\n# RIP配置\n#\n")
            rip_conf = config["rip"]
            config_lines.append(RoutingConfigGenerator.generate_rip_config(
                rip_conf.get("version", 2),
                rip_conf.get("networks"),
                rip_conf.get("import_routes")
            ))

        if "vrrp" in config:
            config_lines.append("\n#\n# VRRP网关冗余配置\n#\n")
            for v in config["vrrp"]:
                config_lines.append(RoutingConfigGenerator.generate_vrrp(
                    v["interface"],
                    v["vrid"],
                    v["virtual_ip"],
                    v.get("priority", 100),
                    v.get("preempt", True),
                    v.get("advertise_interval", 1)
                ))

        if "bfd" in config:
            config_lines.append("#\n# BFD配置\n#\n")
            bfd = config["bfd"]
            config_lines.append("bfd")
            if bfd.get("ospf_enable"):
                config_lines.append(" ospf bfd enable")
            for s in (bfd.get("sessions") or []):
                config_lines.append(f"bfd {s['name']} bind peer-ip {s['peer_ip']} source-ip {s['source_ip']}")
                config_lines.append(" discriminator local 1 remote 2")
                config_lines.append(" commit\n#")

        if "pbr" in config:
            config_lines.append("#\n# 策略路由PBR\n#\n")
            for r in (config["pbr"].get("rules") or []):
                num = r.get("acl_num", 3000)
                config_lines.append(f"acl number {num}")
                config_lines.append(f" rule 5 permit ip source {r.get('source','any')}\n#")
                config_lines.append(f"traffic classifier PBR-{num}")
                config_lines.append(f" if-match acl {num}")
                config_lines.append(f"traffic behavior PBR-{num}")
                config_lines.append(f" redirect ip-nexthop {r.get('nexthop','')}")
                config_lines.append(f"traffic policy PBR-POLICY")
                config_lines.append(f" classifier PBR-{num} behavior PBR-{num}\n#")

        if "ipsec" in config:
            ipsec = config["ipsec"]
            config_lines.append("#\n# IPSec VPN配置\n#\n")
            config_lines.append("ike proposal 1")
            config_lines.append(" encryption-algorithm aes-256")
            config_lines.append(" dh group14")
            config_lines.append(" authentication-algorithm sha2-256\n#")
            config_lines.append(f"ike peer vpn-peer v1")
            config_lines.append(f" pre-shared-key cipher {ipsec.get('pre_shared_key','vpn-key')}")
            config_lines.append(f" remote-address {ipsec.get('peer_ip','1.2.3.4')}\n#")
            config_lines.append("ipsec proposal vpn-proposal")
            config_lines.append(" transform esp")
            config_lines.append(" esp authentication-algorithm sha2-256")
            config_lines.append(" esp encryption-algorithm aes-256\n#")
            config_lines.append(f"acl number 3000")
            config_lines.append(f" rule 5 permit ip source {ipsec.get('local_net','192.168.1.0')} 0.0.0.255 destination {ipsec.get('remote_net','192.168.2.0')} 0.0.0.255\n#")
            config_lines.append("ipsec policy vpn-policy 10 isakmp")
            config_lines.append(" security acl 3000")
            config_lines.append(" ike-peer vpn-peer")
            config_lines.append(" proposal vpn-proposal")

        if "bgp_policy" in config:
            bp = config["bgp_policy"]
            config_lines.append("#\n# BGP路由策略\n#\n")
            config_lines.append("route-policy BGP-POLICY permit node 10")
            config_lines.append(f" if-match ip-prefix {bp.get('prefix_name','LOCAL')}")
            config_lines.append(f" apply local-preference {bp.get('local_pref',200)}")
            config_lines.append("#")
            for pfx in (bp.get("prefixes") or []):
                config_lines.append(f"ip ip-prefix {bp.get('prefix_name','LOCAL')} index 10 permit {pfx.get('network','192.168.0.0')} {pfx.get('mask_len',16)}")

        if "mpls" in config:
            mpls = config["mpls"]
            config_lines.append("#\n# MPLS配置\n#\n")
            config_lines.append("mpls lsr-id "+mpls.get("lsr_id","1.1.1.1"))
            config_lines.append("mpls")
            config_lines.append("mpls ldp")
            for iface in (mpls.get("interfaces") or []):
                config_lines.append(f"interface {iface}")
                config_lines.append(" mpls")
                config_lines.append(" mpls ldp")
                config_lines.append("#")

        if "vxlan" in config:
            vx = config["vxlan"]
            config_lines.append("#\n# VXLAN配置\n#\n")
            config_lines.append("bridge-domain 1")
            config_lines.append(f" vxlan vni {vx.get('vni',5000)}")
            config_lines.append(f"interface Nve1")
            config_lines.append(f" source {vx.get('source_ip','1.1.1.1')}")
            for peer in (vx.get("peers") or []):
                config_lines.append(f" vni {vx.get('vni',5000)} head-end peer-list protocol bgp")
                config_lines.append(f" vni {vx.get('vni',5000)} head-end peer-list {peer}")
            config_lines.append("#")

        if "gre" in config:
            gre = config["gre"]
            config_lines.append("#\n# GRE隧道配置\n#\n")
            config_lines.append(f"interface Tunnel0/0/1")
            config_lines.append(f" ip address {gre.get('tunnel_ip','10.0.0.1')} {gre.get('tunnel_mask','255.255.255.0')}")
            config_lines.append(" tunnel-protocol gre")
            config_lines.append(f" source {gre.get('source','GigabitEthernet0/0/0')}")
            config_lines.append(f" destination {gre.get('destination','2.2.2.2')}")
            config_lines.append("#")

        return "".join(config_lines)
