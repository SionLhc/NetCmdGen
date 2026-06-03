#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""华为 USG 防火墙命令生成器"""


class HuaweiFirewallGenerator:
    @staticmethod
    def generate_zone(config: dict) -> str:
        lines = ["#\n# ===== 安全区域 =====\n#"]
        for z in config.get("zones", []):
            name = z.get("name", "Trust")
            prio = z.get("priority", 85)
            lines.append(f"firewall zone name {name}")
            lines.append(f" set priority {prio}")
            for iface in z.get("ifaces", []):
                lines.append(f" add interface {iface}")
            lines.append(f"# 验证: display zone\n")
        lines.append("# 回滚: undo firewall zone name {zone}\n#")
        return "\n".join(lines)

    @staticmethod
    def generate_policy(config: dict) -> str:
        lines = ["#\n# ===== 安全策略 =====\n#"]
        for i, p in enumerate(config.get("policies", [])):
            fz = p.get("fromZone", "Trust")
            tz = p.get("toZone", "Untrust")
            src = p.get("srcAddr", "192.168.1.0/24")
            dst = p.get("dstAddr", "any")
            svc = p.get("service", "any")
            action = p.get("action", "permit")
            lines.append(f"security-policy")
            lines.append(f" rule name Policy{i+1}")
            lines.append(f"  source-zone {fz}")
            lines.append(f"  destination-zone {tz}")
            if src and src != "any":
                lines.append(f"  source-address {src}")
            if dst and dst != "any":
                lines.append(f"  destination-address {dst}")
            if svc and svc != "any":
                lines.append(f"  service {svc}")
            lines.append(f"  action {action}")
            if p.get("logging"):
                lines.append(f"  logging")
            if p.get("description"):
                lines.append(f"  description {p['description']}")
            lines.append(f"# 验证: display security-policy rule Policy{i+1}")
            lines.append(f"# 回滚: undo security-policy rule name Policy{i+1}")
        lines.append("#")
        return "\n".join(lines)

    @staticmethod
    def generate_nat(config: dict) -> str:
        lines = ["#\n# ===== NAT策略 =====\n#"]
        if not config.get("natEnabled"):
            return ""
        for i, r in enumerate(config.get("natRules", [])):
            sz = r.get("srcZone", "Trust")
            dz = r.get("dstZone", "Untrust")
            src = r.get("srcAddr", "192.168.1.0/24")
            ta = r.get("translatedAddr", "")
            lines.append(f"nat-policy")
            lines.append(f" rule name NAT-Internet{i+1}")
            lines.append(f"  source-zone {sz}")
            lines.append(f"  destination-zone {dz}")
            if src:
                lines.append(f"  source-address {src}")
            if ta:
                lines.append(f"  action source-nat address-group {ta}")
            else:
                lines.append(f"  action source-nat easy-ip")
            lines.append(f"# 验证: display nat-policy rule all")
            lines.append(f"# 回滚: undo nat-policy rule name NAT-Internet{i+1}")
        lines.append("#")
        return "\n".join(lines)

    @staticmethod
    def generate_vpn(config: dict) -> str:
        if not config.get("vpnEnabled"):
            return ""
        lines = ["#\n# ===== IPSec VPN =====\n#"]
        peer = config.get("vpnPeerIp", "203.0.113.1")
        psk = config.get("vpnPsk", "")
        local = config.get("vpnLocalNet", "192.168.1.0/24")
        remote = config.get("vpnRemoteNet", "10.0.0.0/24")
        enc = config.get("vpnEncryption", "aes-256")
        auth = config.get("vpnAuth", "sha2-256")
        lines.append("# IPSec Proposal")
        lines.append("ipsec proposal prop1")
        lines.append(" encapsulation-mode tunnel")
        lines.append(" transform esp")
        lines.append(f" esp authentication-algorithm {auth}")
        lines.append(f" esp encryption-algorithm {enc}")
        lines.append("# IKE Peer")
        lines.append(f"ike peer {peer}")
        lines.append(f" pre-shared-key {psk}")
        lines.append(f" remote-address {peer}")
        lines.append("# IPSec Policy")
        lines.append("ipsec policy policy1 1 isakmp")
        lines.append(" security acl 3000")
        lines.append(f" ike-peer {peer}")
        lines.append(f" proposal prop1")
        lines.append("# ACL 3000 for VPN traffic")
        lines.append("acl 3000")
        lines.append(f" rule 5 permit ip source {local} destination {remote}")
        lines.append(f"# 验证: display ipsec policy")
        lines.append(f"# 验证: display ike sa")
        lines.append(f"# 回滚: undo ipsec policy policy1")
        lines.append("#")
        return "\n".join(lines)

    @staticmethod
    def generate_session(config: dict) -> str:
        lines = ["#\n# ===== 会话管理 =====\n#"]
        tcp = config.get("sessionTcpTimeout", 3600)
        udp = config.get("sessionUdpTimeout", 120)
        icmp = config.get("sessionIcmpTimeout", 15)
        lines.append(f"firewall session aging-time tcp {tcp}")
        lines.append(f"firewall session aging-time udp {udp}")
        lines.append(f"firewall session aging-time icmp {icmp}")
        lines.append(f"# 验证: display firewall session aging-time")
        lines.append(f"# 查看会话: display firewall session table")
        lines.append(f"# 清除会话: reset firewall session table")
        lines.append("#")
        return "\n".join(lines)

    @staticmethod
    def generate_log(config: dict) -> str:
        server = config.get("logServer", "")
        if not server:
            return ""
        lines = ["#\n# ===== 日志/审计 =====\n#"]
        level = config.get("logLevel", "informational")
        lines.append("info-center enable")
        lines.append(f"info-center loghost {server} facility local0")
        lines.append(f"info-center source default channel loghost log level {level}")
        lines.append("firewall log session enable")
        lines.append(f"# 验证: display info-center")
        lines.append(f"# 回滚: undo info-center loghost {server}")
        lines.append("#")
        return "\n".join(lines)

    @staticmethod
    def generate_all(config: dict) -> str:
        sections = [HuaweiFirewallGenerator.generate_zone(config),
                    HuaweiFirewallGenerator.generate_policy(config),
                    HuaweiFirewallGenerator.generate_nat(config),
                    HuaweiFirewallGenerator.generate_vpn(config),
                    HuaweiFirewallGenerator.generate_session(config),
                    HuaweiFirewallGenerator.generate_log(config)]
        return "\n".join(s for s in sections if s)
