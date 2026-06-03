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
        # ── 策略路由（国内外分流/设备分流/应用分流）──
        if config.get("cnRoute", {}).get("enabled") or config.get("deviceRoutes") or config.get("appRoutes"):
            lines.append(RouterOSConfigGenerator.generate_policy_routes(config, version))
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
        # DNAT 端口映射（公网IP → 内网IP:端口）
        dnat_rules = config.get("dnatRules", [])
        for dnat in dnat_rules:
            if dnat.get("publicPort") and dnat.get("internalIp"):
                # 公网IP：有则指定，无则匹配所有（留空=匹配任意目标IP）
                dst_addr = dnat.get("publicIp", "")
                addr_clause = f" dst-address={dst_addr}" if dst_addr else ""
                lines.append(f"/ip firewall nat add chain=dstnat{addr_clause}"
                           f" protocol={dnat.get('protocol','tcp')} dst-port={dnat['publicPort']}"
                           f" action=dst-nat to-addresses={dnat['internalIp']}"
                           f" to-ports={dnat.get('internalPort', dnat['publicPort'])}"
                           f"{' comment=\"' + dnat['description'] + '\"' if dnat.get('description') else ''}")
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
        """QoS / 带宽管理 — 完整 Mangle + Queue Tree 方案

        用户只需配置总带宽和应用优先级，自动生成：
        1. Mangle 标记（连接/包标记）
        2. Queue Tree（基于标记的分层限速）
        3. Simple Queue（每IP限速后备方案）

        这是小白用户也能用的一站式流控方案。
        """
        lines = ["# === QoS 带宽管理（Mangle + Queue Tree）===", ""]

        wan_interfaces = config.get("wan_interfaces", ["ether1"])
        total_down = config.get("total_bandwidth_down", "100M")
        total_up = config.get("total_bandwidth_up", "20M")
        per_ip_limit = config.get("per_ip_limit", "")
        per_ip_enabled = config.get("per_ip_enabled", False)

        # ── 用户选择的应用优先级 ─────────────────────────────────
        app_priorities = config.get("app_priorities", {})
        voip_enabled = app_priorities.get("voip", True)
        video_enabled = app_priorities.get("video", False)
        http_enabled = app_priorities.get("http", True)
        gaming_enabled = app_priorities.get("gaming", False)
        p2p_enabled = app_priorities.get("p2p", False)
        p2p_limit = app_priorities.get("p2p_limit", "5M/5M")

        lines.append(f"# 总带宽: ↓{total_down} ↑{total_up}")
        if per_ip_enabled and per_ip_limit:
            lines.append(f"# 每IP限速: {per_ip_limit}")
        lines.append("")

        # 所有版本 CLI 均用空格分隔
        lines.append("# --- 1. Mangle 防火墙标记 ---")
        mangle_prefix = "/ip firewall mangle"

        # ── 标记下载（prerouting，流量进入 WAN 口时标记）──
        lines.append(f"# 标记下载连接（流量从 WAN 入）")
        for wan in wan_interfaces:
            lines.append(
                f"{mangle_prefix} add chain=prerouting in-interface={wan} "
                f"connection-mark=no-mark action=mark-connection "
                f"new-connection-mark=download-con passthrough=yes"
            )
        lines.append(
            f"{mangle_prefix} add chain=forward connection-mark=download-con "
            f"action=mark-packet new-packet-mark=down-pkt passthrough=no"
        )
        lines.append("")

        # ── 标记上传（postrouting，流量从 LAN 出 WAN 时标记）──
        lines.append(f"# 标记上传包（流量从 LAN 出 WAN）")
        for wan in wan_interfaces:
            lines.append(
                f"{mangle_prefix} add chain=postrouting out-interface={wan} "
                f"action=mark-packet new-packet-mark=up-pkt passthrough=no"
            )
        lines.append("")

        # ── 应用级别优先级标记 ──
        # VOIP（语音：SIP 5060, RTP 10000-20000, DSCP EF=46）
        if voip_enabled:
            lines.append(f"# VOIP 语音标记（SIP+RTP, DSCP EF=46）")
            lines.append(
                f"{mangle_prefix} add chain=prerouting dst-port=5060,5061,10000-20000 "
                f"protocol=udp action=mark-packet new-packet-mark=voip-pkt passthrough=no"
            )
            lines.append(
                f"{mangle_prefix} add chain=prerouting dscp=46 "
                f"action=mark-packet new-packet-mark=voip-pkt passthrough=no"
            )
            lines.append("")

        # 视频（流媒体：YouTube/抖音/企业视频会议）
        if video_enabled:
            lines.append(f"# 视频流量标记")
            lines.append(
                f"{mangle_prefix} add chain=prerouting dst-port=443,1935,8080 "
                f"layer7-protocol=video action=mark-packet new-packet-mark=video-pkt passthrough=no"
            )
            lines.append("")

        # HTTP/HTTPS（网页浏览）
        if http_enabled:
            lines.append(f"# HTTP/HTTPS 网页浏览标记")
            lines.append(
                f"{mangle_prefix} add chain=prerouting dst-port=80,443,8080,8443 "
                f"protocol=tcp action=mark-packet new-packet-mark=http-pkt passthrough=no"
            )
            lines.append("")

        # 游戏（低延迟）
        if gaming_enabled:
            lines.append(f"# 游戏流量标记（低延迟端口）")
            lines.append(
                f"{mangle_prefix} add chain=prerouting dst-port=3074,27015-27030,27036 "
                f"protocol=udp action=mark-packet new-packet-mark=game-pkt passthrough=no"
            )
            lines.append("")

        # P2P/下载
        if p2p_enabled:
            lines.append(f"# P2P/下载标记（限速处理）")
            lines.append(
                f"{mangle_prefix} add chain=prerouting dst-port=6881-6889,51413,6699 "
                f"p2p=all-p2p action=mark-packet new-packet-mark=p2p-pkt passthrough=no"
            )
            lines.append("")

        # === 第二步：Queue Tree ===
        lines.append("# --- 2. Queue Tree 分层限速 ---")

        if version == RouterOSVersion.V7:
            tree_prefix = "/queue/tree"
        else:
            tree_prefix = "/queue tree"

        # 总带宽队列（parent=global）
        lines.append(f"# 总带宽限制")
        lines.append(f"{tree_prefix} add name=Total-Down parent=global packet-mark=down-pkt max-limit={total_down}")
        lines.append(f"{tree_prefix} add name=Total-Up   parent=global packet-mark=up-pkt   max-limit={total_up}")
        lines.append("")

        # 应用优先级子树（parent=Total-Down/Total-Up）
        priority_map = [
            ("voip", "VOIP语音", 1, voip_enabled),
            ("game", "游戏", 2, gaming_enabled),
            ("video", "视频", 3, video_enabled),
            ("http", "网页", 4, http_enabled),
            ("p2p", "P2P下载", 8, p2p_enabled),
        ]
        for tag, label, prio, enabled in priority_map:
            if not enabled:
                continue
            # 自动计算保证带宽（VOIP至少10%总带宽）
            limit_at = "10M" if prio == 1 else "5M"
            p2p_tag = f" max-limit={p2p_limit}" if tag == "p2p" else ""
            lines.append(f"# {label}（优先级={prio}）")
            lines.append(
                f"{tree_prefix} add name={label}-Down parent=Total-Down "
                f"packet-mark={tag}-pkt priority={prio} limit-at={limit_at}{p2p_tag}"
            )
            lines.append(
                f"{tree_prefix} add name={label}-Up   parent=Total-Up   "
                f"packet-mark={tag}-pkt priority={prio} limit-at={limit_at}{p2p_tag}"
            )
        lines.append("")

        # === 第三步：每IP限速（简化方案） ===
        if per_ip_enabled and per_ip_limit:
            lines.append("# --- 3. 每IP限速（Simple Queue） ---")
            lan_network = config.get("lan_network", "192.168.1.0/24")
            if version == RouterOSVersion.V7:
                sq_prefix = "/queue/simple"
            else:
                sq_prefix = "/queue simple"
            lines.append(
                f"{sq_prefix} add name=Per-IP-Limit target={lan_network} "
                f"max-limit={per_ip_limit} dst={lan_network}"
            )
            lines.append(f"# 提示：如需为个别IP单独限速，复制上面命令改 target=IP 即可")
            lines.append("")

        lines.append("# 提示：Queue Tree 会自动处理所有标记流量，无需手动管理")
        lines.append("# 如需监控：/queue tree print stats")

        return "\n".join(lines)

    # ─── 策略路由 / 国内外分流 ─────────────────────

    @staticmethod
    def generate_policy_routes(config: Dict[str, Any],
                               version: RouterOSVersion = RouterOSVersion.V6) -> str:
        """生成策略路由（国内外分流 / 设备分流 / 应用分流）

        用户只需选择场景，系统自动生成 Mangle + Route 标记 + 地址列表。
        """
        lines = ["# === 策略路由 / 分流 ===", ""]
        # ROS CLI 始终用空格分隔，V6/V7 语法一致
        mangle_prefix = "/ip firewall mangle"
        route_prefix = "/ip route"

        # ─── 场景1：国内外分流 ──────────────────
        cn_route = config.get("cnRoute", {})
        if cn_route.get("enabled"):
            cn_wan = cn_route.get("cnWan", "ether1")
            intl_wan = cn_route.get("intlWan", "ether2")


            lines.append("# --- 国内外智能分流 ---")
            lines.append(f"# 逻辑：目的IP在中��IP列表 → 走国内线路({cn_wan})")
            lines.append(f"#       目的IP不在中国IP列表 → 走海外线路({intl_wan})，不标记=默认路由")
            lines.append(f"# DNAT不在此处配置，如需外网访问内网服务器请到NAT/防火墙标签页")
            lines.append("")

            # 1. 前提：导入中国IP地址列表
            lines.append("# 注：需先导入中国 IP 地址列表 /ip firewall address-list")
            lines.append("# 推荐：https://github.com/17mon/china_ip_list 生成导入脚本")
            lines.append("# 示例导入：/import china-ip.rsc")
            lines.append("")

            # 2. Mangle：匹配目的地址在 CN-IP 列表 → 打标记 cn-route
            lines.append("# 2. Mangle 标记：命中中国IP → routing-mark=cn-route")
            lines.append(f"/ip firewall mangle add chain=prerouting dst-address-list=CN-IP \\")
            lines.append(f"    action=mark-routing new-routing-mark=cn-route passthrough=no \\")
            lines.append(f"    comment=\"国内分流→{cn_wan}\"")
            lines.append("")

            # 3. 路由：cn-route 标记 → 国内线路 / 默认（未标记）→ 海外线路
            lines.append("# 3. 路由表：标记流量走国内线，其余走海外线")
            lines.append(f"/ip route add dst-address=0.0.0.0/0 gateway=$(/ip dhcp-client get [{cn_wan}] gateway) \\")
            lines.append(f"    routing-mark=cn-route distance=1 comment=\"国内默认路由\"")
            lines.append(f"/ip route add dst-address=0.0.0.0/0 gateway=$(/ip dhcp-client get [{intl_wan}] gateway) \\")
            lines.append(f"    distance=2 check-gateway=ping comment=\"海外默认路由（保活）\"")
            lines.append("")

        # ─── 场景2：指定设备走指定WAN ────────────
        device_routes = config.get("deviceRoutes", [])
        if device_routes:
            lines.append("# --- 设备/网段分流 ---")
            for i, dr in enumerate(device_routes):
                src = dr.get("srcAddr", "").strip()
                wan = dr.get("wanInterface", "").strip()
                comment = dr.get("comment", f"规则{i+1}") or f"规则{i+1}"
                srcNatIp = dr.get("srcNatIp", "").strip()
                if not src or not wan:
                    continue
                # Mangle 标记
                tag = f"dr{i+1}"
                lines.append(f"# {comment}: {src} → {wan}")
                lines.append(f"{mangle_prefix} add chain=prerouting src-address={src} action=mark-routing new-routing-mark={tag} passthrough=no comment=\"{comment}\"")
                # V7 路由表关联
                if version == RouterOSVersion.V7:
                    lines.append(f"{route_prefix} add dst-address=0.0.0.0/0 routing-table={tag} gateway=$(/ip dhcp-client get [{wan}] gateway) comment=\"{comment}-RT\"")
                else:
                    lines.append(f"{route_prefix} add dst-address=0.0.0.0/0 gateway=$(/ip dhcp-client get [{wan}] gateway) routing-mark={tag} comment=\"{comment}-RT\"")
                # SNAT：多公网IP时指定出口IP（非masquerade自选）
                if srcNatIp:
                    lines.append(f"/ip firewall nat add chain=srcnat src-address={src} action=src-nat to-addresses={srcNatIp} out-interface={wan} comment=\"{comment}-SNAT\"")
                    lines.append(f"# → 该设备出站使用公网IP {srcNatIp}")
                lines.append("")

        # ─── 场景3：应用分流 ──────────────────
        app_routes = config.get("appRoutes", [])
        if app_routes:
            lines.append("# --- 应用/端口分流 ---")
            # 应用端口映射
            port_map = {
                "web": "80,443",
                "game": "3074,27015-27030",
                "voip": "5060,10000-20000",
                "mail": "25,465,587,993",
            }
            for i, ar in enumerate(app_routes):
                wan = ar.get("wanInterface", "").strip()
                comment = ar.get("comment", "") or f"应用{i+1}"
                ports = ar.get("customPorts", "") or port_map.get(ar.get("appType", ""), "")
                if not ports or not wan:
                    continue
                tag = f"app{i+1}"
                lines.append(f"# {comment}: 端口{ports} → {wan}")
                lines.append(f"{mangle_prefix} add chain=prerouting dst-port={ports} protocol=tcp action=mark-routing new-routing-mark={tag} passthrough=no comment=\"{comment}\"")
                if version == RouterOSVersion.V7:
                    lines.append(f"{route_prefix} add dst-address=0.0.0.0/0 routing-table={tag} gateway=$(/ip dhcp-client get [{wan}] gateway) comment=\"{comment}-RT\"")
                else:
                    lines.append(f"{route_prefix} add dst-address=0.0.0.0/0 gateway=$(/ip dhcp-client get [{wan}] gateway) routing-mark={tag} comment=\"{comment}-RT\"")
            lines.append("")

        return "\n".join(lines).strip() and "\n".join(lines)

    # ─── DHCP 服务 ─────────────────────────────────

    @staticmethod
    def _generate_dhcp(params: Dict[str, Any],
                       version: RouterOSVersion = RouterOSVersion.V6) -> str:
        """生成 RouterOS DHCP Server 配置"""
        lines = ["\n# === DHCP 服务 ===", "/ip pool"]
        # 地址池
        pools = []
        for dhcp in (params.get("dhcpLines") or params.get("lines") or []):
            pool_name = f"dhcp_pool_{len(pools)+1}"
            net = dhcp.get("network", "192.168.88.0")
            mask_bits = dhcp.get("mask", "24")
            start_ip = dhcp.get("rangeStart") or dhcp.get("startIp", "")
            end_ip = dhcp.get("rangeEnd") or dhcp.get("endIp", "")
            pools.append({
                "name": pool_name, "interface": dhcp.get("interface", "bridge1"),
                "network": net, "mask": mask_bits, "gateway": dhcp.get("gateway", ""),
                "dns": dhcp.get("dns", "8.8.8.8"), "range": f"{start_ip}-{end_ip}" if start_ip else "",
                "lease": dhcp.get("lease", "1d"), "staticBindings": dhcp.get("staticBindings", ""),
            })
        for p in pools:
            if p["range"]:
                lines.append(f"add name={p['name']} ranges={p['range']}")
        lines.append("")
        # DHCP Server 实例
        lines.append("/ip dhcp-server")
        for p in pools:
            lines.append(f"add name=dhcp_{p['interface']} interface={p['interface']} address-pool={p['name']} disabled=no")
        lines.append("")
        # DHCP 网络配置
        lines.append("/ip dhcp-server network")
        for p in pools:
            net_addr = p['network']
            gw = p['gateway']
            dns = p['dns']
            lines.append(f"add address={net_addr}/{p['mask']} gateway={gw} dns-server={dns}")
            if p['lease']:
                lines.append(f"# lease-time={p['lease']}")
        lines.append("")
        # 静态绑定
        for p in pools:
            if p.get("staticBindings"):
                lines.append("/ip dhcp-server lease")
                for binding in p["staticBindings"].split(","):
                    binding = binding.strip()
                    if "=" in binding:
                        mac, ip = binding.split("=", 1)
                        lines.append(f"add mac-address={mac.strip()} address={ip.strip()} server=dhcp_{p['interface']} comment=\"static-{p['interface']}\"")
                lines.append("")
        return "\n".join(lines)

    # ─── NAT 端口映射 ────────────────────────────────

    @staticmethod
    def _generate_nat(params: Dict[str, Any],
                      version: RouterOSVersion = RouterOSVersion.V6) -> str:
        """生成 RouterOS NAT 端口映射 (DST-NAT + Masquerade)"""
        lines = ["\n# === NAT 配置 ===", "/ip firewall nat"]
        rules = params.get("rules") or params.get("natRules") or params.get("natList") or []

        # Masquerade
        if params.get("enableMasquerade", True):
            masq_if = params.get("masqInterface", "ether1")
            lines.append(f"add chain=srcnat out-interface={masq_if} action=masquerade comment=\"NAT伪装-{masq_if}\"")

        # DST-NAT 端口映射
        for i, r in enumerate(rules):
            proto = r.get("protocol", "tcp")
            dst_port = r.get("dstPort") or r.get("externalPort") or r.get("ext_port", "")
            to_addr = r.get("toAddress") or r.get("internalIp") or r.get("int_ip", "")
            to_ports = r.get("toPorts") or r.get("internalPort") or r.get("int_port", "")
            in_if = r.get("inInterface", "ether1")
            comment = r.get("comment", f"DNAT-{i+1}")

            cmd_parts = [f"add chain=dstnat protocol={proto} dst-port={dst_port} in-interface={in_if}"]
            if to_ports:
                cmd_parts.append(f"to-addresses={to_addr} to-ports={to_ports}")
            else:
                cmd_parts.append(f"action=dst-nat to-addresses={to_addr}")
            cmd_parts.append(f"comment=\"{comment}\"")
            lines.append(" ".join(cmd_parts))

        lines.append("")
        return "\n".join(lines)

    # ─── IPv6 ─────────────────────────────────

    @staticmethod
    def _generate_ipv6(params: Dict[str, Any], version: RouterOSVersion = RouterOSVersion.V6) -> str:
        lines = ["\n# === IPv6 配置 ===", "/ipv6 address"]
        for iface in (params.get("interfaces") or []):
            intf = iface.get("interface", "bridge1")
            addr = iface.get("ipv6_address", "")
            if addr:
                lines.append(f"add address={addr} interface={intf} advertise={'yes' if iface.get('ipv6_ra',True) else 'no'}")
        lines.append("")
        if any(i.get("ipv6_ra", True) for i in (params.get("interfaces") or [])):
            lines.append("/ipv6 nd")
            for iface in (params.get("interfaces") or []):
                if iface.get("ipv6_ra", True):
                    lines.append(f"set [find interface={iface.get('interface','bridge1')}] ra-interval=30-60 ra-lifetime=1800")
            lines.append("")
        for r in (params.get("ipv6_routes") or []):
            lines.append(f"/ipv6 route add dst-address={r.get('dest','::/0')} gateway={r.get('nexthop','')}")
            lines.append("")
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
        # DHCP 服务（独立 key）
        if config.get("dhcp"):
            sections.append(RouterOSConfigGenerator._generate_dhcp(config["dhcp"], version))
        # NAT 端口映射（独立 key）
        if config.get("nat"):
            sections.append(RouterOSConfigGenerator._generate_nat(config["nat"], version))
        # Firewall NAT for PCC
        if config.get("qos"):
            sections.append(RouterOSConfigGenerator.generate_qos(config["qos"], version))
        if config.get("ipv6"):
            sections.append(RouterOSConfigGenerator._generate_ipv6(config["ipv6"], version))
        # 策略路由（国内外分流 / 设备分流 / 应用分流）
        if config.get("policy_route"):
            sections.append(RouterOSConfigGenerator.generate_policy_routes(config["policy_route"], version))
        return "\n".join(sections)
