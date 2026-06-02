#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MikroTik RouterOS 配置生成器

RouterOS CLI 使用层级路径结构：
    /system identity set name=xxx
    /ip address add address=10.0.0.1/24 interface=ether1
    /interface bridge add name=bridge1

支持 V6 / V7 版本区分：V7 重写了路由引擎（OSPF/BGP 语法不同）。
"""

import time
from typing import Any, Dict

from app.engine.vendors.routeros.version_config import RouterOSVersion, get_cmd


class RouterOSConfigGenerator:
    """MikroTik RouterOS 配置生成器"""

    @staticmethod
    def generate_header(config: Dict[str, Any] = None,
                        version: RouterOSVersion = RouterOSVersion.V6) -> str:
        ver_name = "V6" if version == RouterOSVersion.V6 else "V7"
        desc = ""
        if isinstance(config, str):
            # 旧格式：直接传字符串
            desc = config
        elif config and isinstance(config, dict):
            desc = config.get("description", "")
        return f"""#
# MikroTik RouterOS {ver_name} 配置脚本
# 描述: {desc}
# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
#
"""

    @staticmethod
    def generate_basic(config: Dict[str, Any],
                       version: RouterOSVersion = RouterOSVersion.V6) -> str:
        """基础系统配置"""
        lines = ["# === 基础系统配置 ===", ""]
        # 主机名
        hostname = config.get("hostname", "ROS-Router")
        lines.append(get_cmd(version, "hostname", hostname=hostname))
        # DNS
        dns = config.get("dns_servers", "")
        if dns:
            lines.append(get_cmd(version, "dns_server", ip=dns))
        if config.get("dns_cache"):
            lines.append("/ip dns set allow-remote-requests=yes cache-size=2048KiB")
        # NTP
        ntp = config.get("ntp_server", "")
        if ntp:
            if version == RouterOSVersion.V7:
                lines.append(get_cmd(version, "ntp_client", ip=ntp))
            else:
                lines.append(f"/system ntp client set enabled=yes primary-ntp={ntp}")
        # 时区
        tz = config.get("timezone", "")
        if tz:
            lines.append(f"/system clock set time-zone-name={tz}")
        # SSH + 管理服务
        if config.get("enable_ssh") or config.get("enable_ssh") is None:
            port = config.get("ssh_port", 22)
            # 禁用不安全服务
            disabled = config.get("disable_services", ["telnet", "ftp", "www", "api"])
            for svc in disabled:
                lines.append(f"/ip service set {svc} disabled=yes")
            # 启用 SSH
            lines.append(get_cmd(version, "ssh_enable", port=port))
            # SSH IP 限制
            allow_ip = config.get("ssh_allow_ip", "")
            if allow_ip:
                lines.append(f"/ip service set ssh address={allow_ip}")
        # WinBox
        if not config.get("enable_winbox", True):
            lines.append("/ip service set winbox disabled=yes")
        # 用户
        username = config.get("admin_user", "") or config.get("user", {}).get("username", "admin")
        password = config.get("admin_password", "") or config.get("user", {}).get("password", "admin123")
        group = config.get("admin_group", "full")
        lines.append(get_cmd(version, "user_create", user=username, pw=password))
        lines.append(f"/user set {username} group={group}")
        return "\n".join(lines)

    @staticmethod
    def generate_vlan(config: Dict[str, Any],
                      version: RouterOSVersion = RouterOSVersion.V6) -> str:
        """VLAN 配置"""
        lines = ["# === VLAN 配置 ===", ""]
        bridge_name = config.get("bridge", "bridge1")
        # 创建桥
        lines.append(get_cmd(version, "bridge_create", name=bridge_name))
        # 创建 VLAN
        for vlan in config.get("vlans", []):
            vid = vlan.get("id", 1)
            trunk = vlan.get("trunk", "ether1")
            lines.append(get_cmd(version, "vlan_create", vid=vid, trunk=trunk))
        # 桥接端口
        for port in config.get("bridge_ports", []):
            pname = port.get("interface", "ether2")
            lines.append(get_cmd(version, "bridge_port", port=pname, bridge=bridge_name))
        return "\n".join(lines)

    @staticmethod
    def generate_routing(config: Dict[str, Any],
                         version: RouterOSVersion = RouterOSVersion.V6) -> str:
        """路由配置（含 PCC 多线负载均衡）"""
        lines = ["# === 路由配置 ===", ""]
        pcc_enabled = config.get("pccEnabled", False)
        pcc_wans = config.get("pccWans", [])
        # ── PCC 多线负载均衡（对标 WinBox Mangle 标准写法）────
        if pcc_enabled and len(pcc_wans) > 1:
            classifier = config.get("pccClassifier", "both-addresses-and-ports")
            total = sum(w.get("bucketCount", 1) for w in pcc_wans)
            lan = config.get("pccLanInterface", "Lan")
            mark_output = config.get("pccMarkOutput", True)
            lines.append(f"# ═══ PCC 多线负载均衡 ═══")
            lines.append(f"# 分类器: {classifier}, 总 Bucket: {total}, 内网接口: {lan}")
            lines.append(f"# 参考 WinBox: IP → Firewall → Mangle")
            lines.append("")
            # ── 阶段1：统一标记所有新连接（passthrough=yes 让流量继续走后续规则）──
            lines.append("# 1. 统一连接标记（passthrough=yes，继续后续 PCC 规则）")
            lines.append(f"/ip firewall mangle add chain=prerouting in-interface={lan}"
                       f" connection-state=new connection-mark=no-mark"
                       f" action=mark-connection new-connection-mark=new-conn"
                       f" passthrough=yes comment=PCC-MarkConn")
            lines.append("")
            # ── 阶段2：每条线路每个 bucket 一条 PCC 规则（passthrough=no）──
            lines.append(f"# 2. PCC 分流规则（passthrough=no，匹配后停止）")
            for wi, wan in enumerate(pcc_wans):
                mark = wan.get("routingMark", f"Route{wi+1}")
                wan_if = wan.get("interface", f"ether{wi+1}")
                bc = wan.get("bucketCount", 1)
                bs = wan.get("bucketStart", 0)
                lines.append(f"# --- {mark} ({wan_if}, {bc} 个 bucket) ---")
                for bi in range(bc):
                    bucket_num = bs + bi
                    # WinBox 格式: TOTAL/BUCKET（如 2/0, 2/1）
                    pcc_val = f"{classifier}:{total}/{bucket_num}"
                    lines.append(f"/ip firewall mangle add chain=prerouting"
                               f" in-interface={lan} connection-mark=new-conn"
                               f" per-connection-classifier={pcc_val}"
                               f" action=mark-routing new-routing-mark={mark}"
                               f" passthrough=no comment=PCC-{mark}-{bucket_num}")
            lines.append("")
            # ── 阶段3：回程标记（output链）──
            if mark_output:
                lines.append("# 3. 回程标记（output链确保回包走正确线路）")
                for wan in pcc_wans:
                    mark = wan.get("routingMark", "Route1")
                    lines.append(f"/ip firewall mangle add chain=output connection-mark=new-conn"
                               f" action=mark-routing new-routing-mark={mark}"
                               f" comment=Output-{mark}")
                lines.append("")
        # ── 路由表（V7 新架构 vs V6 传统方式）──
        if pcc_enabled:
            if version == RouterOSVersion.V7:
                lines.append("# ═══ V7 路由表+RoutinRule 架构 ═══")
                lines.append("# V7 需要先创建 routing table，再用 routing rule 关联 mark → table")
                for wan in pcc_wans:
                    mark = wan.get("routingMark", "Route1")
                    gw = wan.get("gateway", "")
                    wan_if = wan.get("interface", "ether1")
                    lines.append(f"# --- {mark} ---")
                    # V7 创建路由表
                    lines.append(f"/routing table add name={mark} fib")
                    # V7 创建路由规则（mark → table）
                    lines.append(f"/routing rule add action=lookup-only-in-table table={mark} routing-mark={mark}")
                    # 添加默认路由到该 table
                    if gw:
                        lines.append(f"/ip route add dst-address=0.0.0.0/0 gateway={gw} routing-table={mark}")
                        lines.append(f"# → 内网设备经 {wan_if} ({gw}) 上网")
                    lines.append("")
            else:
                # V6 传统方式：路由打 routing-mark
                lines.append("# ═══ V6 路由标记方式 ═══")
                for wan in pcc_wans:
                    mark = wan.get("routingMark", "Route1")
                    gw = wan.get("gateway", "")
                    if gw:
                        lines.append(get_cmd(version, "static_route", dest="0.0.0.0", prefix="0", gw=gw))
                        lines.append(f"/ip route set [find gateway={gw}] routing-mark={mark}")
        # ── 常规静态路由 ──
        for route in config.get("staticRoutes", []):
            dst = route.get("dst", "")
            prefix = route.get("prefix", "24")
            gw = route.get("gateway", "")
            comment = route.get("comment", "")
            if dst and gw:
                lines.append(get_cmd(version, "static_route", dest=dst, prefix=prefix, gw=gw))
                if comment:
                    lines.append(f"/ip route comment [find where dst-address={dst}/{prefix}] {comment}")
        # ── 策略路由分流（额外条件走指定线路）──
        for pr in config.get("policyRoutes", []):
            src = pr.get("srcAddr", "")
            dst = pr.get("dstAddr", "")
            mark = pr.get("routingMark", "")
            gw = pr.get("gateway", "")
            comment = pr.get("comment", "")
            if src and mark:
                lines.append(f"# 策略路由: {src} → {mark}")
                lines.append(f"/ip firewall mangle add chain=prerouting src-address={src}"
                           f" action=mark-routing new-routing-mark={mark}"
                           f" passthrough=no"
                           f"{' comment=' + comment if comment else ''}")
            if dst and gw and mark:
                if version == RouterOSVersion.V7:
                    lines.append(f"/ip route add dst-address={dst}/24 gateway={gw} routing-table={mark}")
                else:
                    lines.append(get_cmd(version, "static_route", dest=dst, prefix="24", gw=gw))
                    lines.append(f"/ip route set [find gateway={gw}] routing-mark={mark}")
        # ── OSPF ──
        if config.get("ospfEnabled"):
            rid = config.get("ospfRouterId", "1.1.1.1")
            lines.append("# ═══ OSPF 动态路由 ═══")
            lines.append(get_cmd(version, "ospf_instance", rid=rid))
            for net in config.get("ospfNetworks", []):
                addr = net.get("address", "")
                area = net.get("area", "0.0.0.0")
                if addr:
                    lines.append(get_cmd(version, "ospf_network", net=addr, area=area))
        return "\n".join(lines)

    @staticmethod
    def generate_security(config: Dict[str, Any],
                          version: RouterOSVersion = RouterOSVersion.V6) -> str:
        """防火墙 / NAT / 安全配置"""
        lines = ["# === 防火墙 & 安全配置 ===", ""]
        # NAT Masquerade（支持两种格式：旧格式 nat 列表 或 nat + natInterface）
        nat_enabled = config.get("nat", False)
        wan_if = config.get("natInterface", "ether1")
        if isinstance(nat_enabled, list):
            # 旧格式：[{wan_interface}]
            for nat_entry in nat_enabled:
                wan = nat_entry.get("wan_interface", "ether1")
                lines.append(get_cmd(version, "nat_masquerade", wan=wan))
        elif nat_enabled:
            lines.append(get_cmd(version, "nat_masquerade", wan=wan_if))
        # 防火墙规则（支持两种格式：列表 或 多行文本）
        filter_rules = config.get("filter_rules", [])
        if not filter_rules:
            # 新格式：inputRules/forwardRules 多行文本
            input_text = config.get("inputRules", "")
            forward_text = config.get("forwardRules", "")
            for line in input_text.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    lines.append(get_cmd(version, "filter_rule",
                        chain="input", action=parts[0], proto=parts[1], port=parts[2]))
            for line in forward_text.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    lines.append(get_cmd(version, "filter_rule",
                        chain="forward", action=parts[0], proto=parts[1], port=parts[2]))
            # 添加默认规则
            if not input_text:
                lines.append("# 建议：拒绝除 SSH/Ping 之外的外部访问")
                lines.append("/ip firewall filter add chain=input action=accept protocol=tcp dst-port=22 comment=SSH")
        else:
            for rule in filter_rules:
                chain = rule.get("chain", "input")
                action = rule.get("action", "accept")
                proto = rule.get("protocol", "tcp")
                port = rule.get("port", 22)
                lines.append(get_cmd(version, "filter_rule",
                    chain=chain, action=action, proto=proto, port=port))
        # DNAT 端口映射
        dnat_rules = config.get("dnatRules", [])
        for dnat in dnat_rules:
            if dnat.get("publicPort") and dnat.get("internalIp"):
                lines.append(f"/ip firewall nat add chain=dstnat dst-port={dnat['publicPort']} "
                           f"protocol=tcp action=dst-nat to-addresses={dnat['internalIp']} "
                           f"to-ports={dnat.get('internalPort', dnat['publicPort'])}")
        # WireGuard (V7)
        if config.get("wireguard", False) and version == RouterOSVersion.V7:
            lines.append("# WireGuard VPN (V7)")
            lines.append(get_cmd(version, "wireguard_enable"))
        return "\n".join(lines)

    @staticmethod
    def generate_interface(config: Dict[str, Any],
                           version: RouterOSVersion = RouterOSVersion.V6) -> str:
        """接口 / IP / Bridge 配置"""
        lines = ["# === 接口 & IP & Bridge 配置 ===", ""]
        # ── 物理接口 + IP ──
        lines.append("# 物理接口")
        for iface in config.get("interfaces", []):
            name = iface.get("name", "ether2")
            role = iface.get("role", "lan")
            if role == "unused":
                lines.append(f"/interface disable {name}")
                continue
            comment = iface.get("comment", name)
            lines.append(f"/interface set {name} comment=\"{comment}\"")
            ip_raw = iface.get("ip", "")
            if ip_raw:
                # 支持 "192.168.1.1/24" 或 "192.168.1.1,24" 格式
                ip = ip_raw.split("/")[0] if "/" in ip_raw else ip_raw
                mask = ip_raw.split("/")[1] if "/" in ip_raw else "24"
                lines.append(get_cmd(version, "ip_address", ip=ip, mask=mask, interface=name))
            if role == "wan":
                lines.append("# WAN 接口 — 确保默认路由指向此接口")
        # ── Bridge 桥接 ──
        for br in config.get("bridges", []):
            br_name = br.get("name", "bridge1")
            stp = br.get("stp", "none")
            vlan_filter = br.get("vlanFiltering", False)
            lines.append(f"\n# Bridge: {br_name}")
            lines.append(get_cmd(version, "bridge_create", name=br_name))
            if stp != "none":
                lines.append(f"/interface bridge set {br_name} protocol-mode={stp}")
            # 成员端口
            ports_str = br.get("portsStr", "")
            if ports_str:
                for port in [p.strip() for p in ports_str.split(",") if p.strip()]:
                    lines.append(get_cmd(version, "bridge_port", port=port, bridge=br_name))
            # VLAN 过滤 (V7)
            if vlan_filter and version == RouterOSVersion.V7:
                lines.append(f"/interface bridge set {br_name} vlan-filtering=yes")
        return "\n".join(lines)

    @staticmethod
    def generate_qos(config: Dict[str, Any],
                     version: RouterOSVersion = RouterOSVersion.V6) -> str:
        """QoS / Queue Tree 配置"""
        lines = ["# === QoS 带宽管理 ===", ""]
        for queue in config.get("simple_queues", []):
            name = queue.get("name", "QoS")
            target = queue.get("target", "192.168.1.0/24")
            limit = queue.get("limit", "10M/10M")
            lines.append(f"/queue simple add name={name} target={target} max-limit={limit}")
        return "\n".join(lines)

    # ─── 统一入口 ─────────────────────────────────

    @staticmethod
    def generate_all(config: Dict[str, Any],
                     ros_version: str = "v6") -> str:
        """生成完整 RouterOS 配置"""
        version = RouterOSVersion(ros_version) if ros_version in ("v6", "v7") else RouterOSVersion.V6
        sections = [
            RouterOSConfigGenerator.generate_header(config, version),
        ]
        if config.get("basic"):
            sections.append(RouterOSConfigGenerator.generate_basic(config["basic"], version))
        if config.get("interface"):
            sections.append(RouterOSConfigGenerator.generate_interface(config["interface"], version))
        if config.get("vlan"):
            sections.append(RouterOSConfigGenerator.generate_vlan(config["vlan"], version))
        if config.get("routing"):
            sections.append(RouterOSConfigGenerator.generate_routing(config["routing"], version))
        # 安全/NAT：PCC 启用时自动为每条 WAN 生成 masquerade
        sec = config.get("security", {})
        routing = config.get("routing", {})
        if routing.get("pccEnabled") and routing.get("pccWans"):
            # 自动补 NAT masquerade
            auto_nat = []
            for w in routing["pccWans"]:
                if isinstance(w, dict) and w.get("autoNat", True):
                    auto_nat.append({"wan_interface": w.get("interface", "ether1")})
            if auto_nat:
                sec = {**sec, "nat": auto_nat}
        if sec and any(sec.get(k) for k in ["nat", "filter_rules", "inputRules", "wireguard", "dnatRules"]):
            sections.append(RouterOSConfigGenerator.generate_security(sec, version))
        # Firewall NAT for PCC
        if config.get("qos"):
            sections.append(RouterOSConfigGenerator.generate_qos(config["qos"], version))
        return "\n".join(sections)
