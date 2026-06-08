"""华为交换机命令输出解析器 — 20 个巡检项
从 SwitchManager (Go) 移植为 Python asyncio 版本
"""

import json
import re
from typing import Any

CMD_ERROR_PATTERNS = [
    re.compile(r"(?i)unrecognized\s+command"),
    re.compile(r"(?i)incomplete\s+command"),
    re.compile(r"(?i)too\s+many\s+parameters"),
    re.compile(r"(?i)wrong\s+parameter"),
    re.compile(r"(?i)invalid\s+input"),
    re.compile(r"(?i)unknown\s+command"),
    re.compile(r"(?i)^%\s*error:"),
    re.compile(r"(?i)ambiguous\s+command"),
    re.compile(r"(?i)no\s+such\s+command"),
    re.compile(r"(?i)command\s+not\s+found"),
]

IFACE_PREFIXES = [
    "GigabitEthernet", "GE", "XGigabitEthernet", "XE",
    "40GE", "100GE", "25GE", "Eth-Trunk",
    "LoopBack", "Vlanif", "MEth", "Tunnel",
    "Ethernet", "10GE", "NULL", "Vbdif", "Nve",
]


def _wrap_raw(output: str, level: str = "normal") -> tuple[str, str, str]:
    return json.dumps({"rawOutput": output}, ensure_ascii=False), level, ""


def _wrap(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _check_threshold(value: float, warn: float, error_th: float) -> tuple[str, str]:
    if value >= error_th:
        return "error", f"{value:.1f} 超过告警阈值 {error_th:.1f}"
    if value >= warn:
        return "warning", f"{value:.1f} 超过预警阈值 {warn:.1f}"
    return "normal", ""


def _is_iface(name: str) -> bool:
    for p in IFACE_PREFIXES:
        if name.startswith(p):
            return True
    return False


def _safe_int(s: str) -> int:
    s = s.strip().strip("()")
    try:
        return int(s)
    except ValueError:
        return 0


def is_command_error(output: str) -> bool:
    for pattern in CMD_ERROR_PATTERNS:
        if pattern.search(output):
            return True
    return False


# ======================== 调度器 ========================

def parse_item(item_name: str, output: str) -> dict:
    """统一调度，返回 {result:str, level:str, message:str}"""
    parsers = {
        "设备基本信息": _parse_version,
        "CPU使用率": _parse_cpu,
        "内存使用率": _parse_memory,
        "温度状态": _parse_temperature,
        "电源状态": _parse_power,
        "风扇状态": _parse_fan,
        "接口状态": _parse_interface,
        "接口错包": _parse_interface_errors,
        "VLAN信息": _parse_vlan,
        "路由表": _parse_routing,
        "ARP表": _parse_arp,
        "MAC地址表": _parse_mac,
        "日志告警": _parse_logbuffer,
        "STP状态": _parse_stp,
        "链路聚合": _parse_eth_trunk,
        "OSPF状态": _parse_ospf,
        "VRRP状态": _parse_vrrp,
        "ACL规则": _parse_acl,
        "NTP同步": _parse_ntp,
        "当前配置": _parse_raw,
        # ── 安全合规（10项）──
        "弱口令检测": _parse_weak_password,
        "Telnet启用": _parse_telnet,
        "SSH_V1协议": _parse_ssh_v1,
        "SNMP默认团体字": _parse_snmp_community,
        "HTTP管理": _parse_http,
        "ACL管理口": _parse_acl_mgmt,
        "登录横幅": _parse_banner,
        "会话超时": _parse_timeout,
        "日志配置": _parse_logging,
        "NTP配置": _parse_ntp_config,
    }
    fn = parsers.get(item_name, _parse_raw)
    result_str, level, message = fn(output)
    return {"result": result_str, "level": level, "message": message}


# ======================== 各解析器 ========================

def _parse_raw(output: str) -> tuple[str, str, str]:
    return _wrap_raw(output, "normal")


def _parse_version(output: str) -> tuple[str, str, str]:
    data = {"model": "", "version": "", "uptime": ""}
    for line in output.split("\n"):
        line = line.strip()
        if "Huawei" in line or "HUAWEI" in line:
            parts = line.split()
            if len(parts) >= 2:
                data["model"] = parts[-1]
        if "VRP" in line:
            parts = line.split()
            for i, p in enumerate(parts):
                if p == "VRP" and i + 2 < len(parts):
                    data["version"] = f"VRP {parts[i+1]} {parts[i+2]}"
        if "uptime" in line.lower():
            idx = line.lower().find("uptime")
            if idx >= 0:
                data["uptime"] = line[idx + 6:].strip()
    return _wrap(data), "normal", ""


def _parse_cpu(output: str) -> tuple[str, str, str]:
    data = {"cpuUsage": "0", "maxUsage": "0"}
    for line in output.split("\n"):
        line = line.strip()
        lower = line.lower()
        if "---" in line or ("cpu" in lower and "usage" in lower and "%" not in line):
            continue
        if "%" in line:
            parts = line.split()
            for p in parts:
                p = p.rstrip("%,.")
                try:
                    val = float(p)
                    if 0 <= val <= 100:
                        data["cpuUsage"] = f"{val:.1f}"
                        lvl, msg = _check_threshold(val, 70, 90)
                        return _wrap(data), lvl, msg
                except ValueError:
                    pass
        if any(kw in lower for kw in ["data", "5s", "1m"]):
            parts = line.split()
            for p in parts:
                p = p.rstrip("%")
                try:
                    val = float(p)
                    if 0 <= val <= 100:
                        data["cpuUsage"] = f"{val:.1f}"
                        lvl, msg = _check_threshold(val, 70, 90)
                        return _wrap(data), lvl, msg
                except ValueError:
                    pass
    return _wrap(data), "normal", ""


def _parse_memory(output: str) -> tuple[str, str, str]:
    data = {"memUsage": "0", "totalMB": "0", "usedMB": "0"}

    def _extract_pct(line: str) -> float:
        for p in line.split():
            p = p.rstrip("%,.")
            try:
                v = float(p)
                if 0 <= v <= 100:
                    return v
            except ValueError:
                pass
        return -1

    def _extract_mb(line: str) -> tuple[int, bool]:
        for p in line.split():
            pl = p.lower()
            if pl.endswith("mb"):
                n = p.rstrip("MBmMbb").strip()
                try:
                    v = int(n)
                    if v > 0:
                        return v, True
                except ValueError:
                    pass
            if pl.endswith("kb"):
                n = p.rstrip("KBkKbb").strip()
                try:
                    return int(n) // 1024, True
                except ValueError:
                    pass
        return 0, False

    total_mb = 0
    used_mb = 0
    for line in output.split("\n"):
        line = line.strip()
        if "---" in line:
            continue
        lower = line.lower()

        if "memory" in lower and "usage" in lower and "%" in line:
            v = _extract_pct(line)
            if v >= 0:
                data["memUsage"] = f"{v:.1f}"
                lvl, msg = _check_threshold(v, 75, 90)
                return _wrap(data), lvl, msg

        if ("mem:" in lower or "memory" in lower) and "%" in line:
            v = _extract_pct(line)
            if v >= 0:
                data["memUsage"] = f"{v:.1f}"
                lvl, msg = _check_threshold(v, 75, 90)
                return _wrap(data), lvl, msg

        if "total" in lower and ("memory" in lower or "mem" in lower):
            mb, ok = _extract_mb(line)
            if ok and total_mb == 0:
                total_mb = mb

        if "used" in lower and "rate" not in lower and "usage" not in lower:
            mb, ok = _extract_mb(line)
            if ok and (total_mb == 0 or mb < total_mb):
                used_mb = mb

    if total_mb > 0 and used_mb > 0:
        usage = used_mb / total_mb * 100
        data["memUsage"] = f"{usage:.1f}"
        data["totalMB"] = str(total_mb)
        data["usedMB"] = str(used_mb)
        lvl, msg = _check_threshold(usage, 75, 90)
        return _wrap(data), lvl, msg

    if total_mb > 0:
        data["totalMB"] = str(total_mb)
    return _wrap(data), "normal", ""


def _parse_temperature(output: str) -> tuple[str, str, str]:
    data = {"temperature": "0", "status": "正常"}
    max_temp = 0.0
    for line in output.split("\n"):
        line = line.strip()
        if "---" in line or ("Temperature" in line and "C" not in line and "℃" not in line):
            continue
        for p in line.split():
            p = p.rstrip("C℃c°")
            try:
                v = float(p)
                if 0 <= v <= 120 and v > max_temp:
                    max_temp = v
            except ValueError:
                pass
    if max_temp > 0:
        data["temperature"] = f"{max_temp:.1f}"
        lvl, msg = _check_threshold(max_temp, 50, 70)
        return _wrap(data), lvl, msg
    return _wrap_raw(output, "normal")


def _parse_power(output: str) -> tuple[str, str, str]:
    slots = []
    has_error = False
    for line in output.split("\n"):
        line = line.strip()
        if "---" in line or ("Power" in line and "ID" in line):
            continue
        parts = line.split()
        if len(parts) >= 3:
            slot = {"slot": parts[0], "status": ""}
            for p in parts[1:]:
                pl = p.lower()
                if pl == "normal":
                    slot["status"] = "Normal"
                elif pl in ("fault", "absent", "disable"):
                    slot["status"] = p
                    has_error = True
            if not slot["status"] and len(parts) >= 3:
                slot["status"] = parts[-1]
            if slot["slot"]:
                slots.append(slot)
    if not slots:
        return _wrap_raw(output, "normal")
    lvl = "error" if has_error else "normal"
    msg = "存在电源异常" if has_error else ""
    return _wrap(slots), lvl, msg


def _parse_fan(output: str) -> tuple[str, str, str]:
    fans = []
    has_error = False
    for line in output.split("\n"):
        line = line.strip()
        if "---" in line or ("Fan" in line and "ID" in line):
            continue
        parts = line.split()
        if len(parts) >= 2:
            fan = {"fanId": parts[0], "status": "", "speed": ""}
            for p in parts[1:]:
                pl = p.lower()
                if pl == "normal":
                    fan["status"] = "Normal"
                elif pl in ("fault", "absent", "disable"):
                    fan["status"] = p
                    has_error = True
                elif "rpm" in pl or "%" in pl:
                    fan["speed"] = p
            if not fan["status"] and len(parts) >= 2:
                fan["status"] = parts[-1]
            if fan["fanId"]:
                fans.append(fan)
    if not fans:
        return _wrap_raw(output, "normal")
    lvl = "error" if has_error else "normal"
    msg = "存在风扇异常" if has_error else ""
    return _wrap(fans), lvl, msg


def _parse_interface(output: str) -> tuple[str, str, str]:
    total = up = down = 0
    for line in output.split("\n"):
        line = line.strip()
        if "---" in line or any(k in line for k in ("Interface", "PHY", "Protocol", "Status")):
            continue
        parts = line.split()
        if parts and _is_iface(parts[0]):
            total += 1
            for p in parts[1:]:
                if p.lower() == "up":
                    up += 1
                    break
                elif p.lower() == "down" or "down" in p.lower():
                    down += 1
                    break
    data = {"total": str(total), "up": str(up), "down": str(down)}
    lvl = "warning" if down > 0 else "normal"
    msg = f"{down} 个接口处于 down 状态" if down > 0 else ""
    return _wrap(data), lvl, msg


def _parse_interface_errors(output: str) -> tuple[str, str, str]:
    errors = []
    has_error = False
    header_line = ""
    for line in output.split("\n"):
        lower = line.lower()
        if "interface" in lower and ("error" in lower or "uti" in lower):
            header_line = line
            break

    def _find_col(header: str, keywords: list) -> int:
        parts = header.split()
        for kw in keywords:
            for i, p in enumerate(parts):
                if kw in p.lower():
                    return i
        return -1

    in_err_idx = _find_col(header_line, ["inerror", "in-error", "ie"])
    out_err_idx = _find_col(header_line, ["outerror", "out-error", "oe"])

    for line in output.split("\n"):
        line = line.strip()
        if "---" in line or "Interface" in line:
            continue
        parts = line.split()
        if parts and _is_iface(parts[0]):
            ie = {"interface": parts[0], "inErrors": "--", "outErrors": "--"}
            if 0 <= in_err_idx < len(parts):
                ie["inErrors"] = parts[in_err_idx]
            if 0 <= out_err_idx < len(parts):
                ie["outErrors"] = parts[out_err_idx]
            if _safe_int(ie["inErrors"]) > 0 or _safe_int(ie["outErrors"]) > 0:
                has_error = True
            errors.append(ie)

    if not errors:
        return _wrap_raw(output, "normal")
    lvl = "warning" if has_error else "normal"
    err_count = sum(1 for e in errors if _safe_int(e["inErrors"]) > 0 or _safe_int(e["outErrors"]) > 0)
    msg = f"{err_count} 个接口存在错包" if has_error else ""
    return _wrap(errors), lvl, msg


def _parse_vlan(output: str) -> tuple[str, str, str]:
    vlans = []
    for line in output.split("\n"):
        line = line.strip()
        if "---" in line:
            continue
        parts = line.split()
        if parts and parts[0].isdigit():
            v = {"id": parts[0], "name": ""}
            if len(parts) >= 2:
                v["name"] = parts[1]
            vlans.append(v)
    if not vlans:
        return _wrap_raw(output, "normal")
    return _wrap(vlans), "normal", f"共 {len(vlans)} 个VLAN"


def _parse_routing(output: str) -> tuple[str, str, str]:
    direct = static = ospf = total = 0
    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("Destination/Mask") or "Routing Tables:" in line or "Route Flags" in line:
            continue
        parts = line.split()
        if parts and ("." in parts[0] or "/" in parts[0]):
            total += 1
            proto = parts[-2].lower() if len(parts) >= 5 else parts[-1].lower() if len(parts) >= 3 else ""
            if proto == "direct":
                direct += 1
            elif proto == "static":
                static += 1
            elif proto == "ospf":
                ospf += 1
    data = {"routeCount": str(total), "directCount": str(direct), "staticCount": str(static), "ospfCount": str(ospf)}
    return _wrap(data), "normal", ""


def _parse_arp(output: str) -> tuple[str, str, str]:
    count = 0
    for line in output.split("\n"):
        line = line.strip()
        if ":" in line and "." in line and "---" not in line:
            parts = line.split()
            if len(parts) >= 2 and "." in parts[0] and "-" in parts[1]:
                count += 1
    return _wrap({"arpCount": str(count)}), "normal", ""


def _parse_mac(output: str) -> tuple[str, str, str]:
    count = 0
    for line in output.split("\n"):
        line = line.strip()
        if "-" in line and "---" not in line:
            for p in line.split():
                if p.count("-") >= 5 and len(p) >= 17:
                    count += 1
                    break
    return _wrap({"macCount": str(count)}), "normal", ""


def _parse_logbuffer(output: str) -> tuple[str, str, str]:
    warnings_list = []
    for line in output.split("\n"):
        line = line.strip()
        lower = line.lower()
        if any(kw in lower for kw in ("warning", "error", "fail")):
            entry = {"content": line}
            entry["level"] = "error" if "error" in lower or "fail" in lower else "warning"
            parts = line.split()
            entry["time"] = parts[0] if parts else ""
            warnings_list.append(entry)
    if not warnings_list:
        return _wrap({"warningCount": "0"}), "normal", ""
    lvl = "warning" if warnings_list else "normal"
    msg = f"发现 {len(warnings_list)} 条告警日志"
    return _wrap(warnings_list), lvl, msg


def _parse_stp(output: str) -> tuple[str, str, str]:
    ports = []
    has_blocking = False
    for line in output.split("\n"):
        line = line.strip()
        if "---" in line or ("Port" in line and "Role" in line):
            continue
        parts = line.split()
        if parts and _is_iface(parts[0]):
            p = {"interface": parts[0], "role": "", "status": ""}
            for w in parts:
                wl = w.lower()
                if wl in ("desi", "root", "msti", "backup"):
                    p["role"] = w
                if wl == "forwarding":
                    p["status"] = "FORWARDING"
                elif wl in ("discarding", "blocking"):
                    p["status"] = w.upper()
                    has_blocking = True
            ports.append(p)
    if not ports:
        return _wrap_raw(output, "normal")
    lvl = "warning" if has_blocking else "normal"
    msg = "存在 STP 阻塞端口" if has_blocking else ""
    return _wrap(ports), lvl, msg


def _parse_eth_trunk(output: str) -> tuple[str, str, str]:
    trunks = []
    for line in output.split("\n"):
        line = line.strip()
        if "---" in line or "Aggregate" in line:
            continue
        parts = line.split()
        if parts and parts[0].startswith("Eth-Trunk"):
            t = {"id": parts[0], "mode": "", "ports": "", "status": ""}
            for i, p in enumerate(parts):
                if "LACP" in p:
                    t["mode"] = parts[i]
                if p in ("Normal", "Up", "Down", "S"):
                    t["status"] = p
            if len(parts) >= 3:
                t["ports"] = parts[-2]
            trunks.append(t)
    if not trunks:
        return _wrap_raw(output, "normal")
    return _wrap(trunks), "normal", f"共 {len(trunks)} 个链路聚合组"


def _parse_ospf(output: str) -> tuple[str, str, str]:
    peers = []
    all_full = True
    for line in output.split("\n"):
        line = line.strip()
        if "---" in line or ("Peer" in line and "State" in line):
            continue
        parts = line.split()
        if len(parts) >= 3 and any("." in p for p in parts):
            peer = {"routerId": "", "address": "", "state": ""}
            for i, p in enumerate(parts):
                if "." in p and not peer["address"]:
                    peer["address"] = p
                if p.lower() == "full":
                    peer["state"] = "Full"
                elif any(s in p.lower() for s in ("init", "attempt", "2-way", "exchange", "loading")):
                    peer["state"] = p
                    all_full = False
                if i == len(parts) - 1 and not peer["routerId"]:
                    peer["routerId"] = p
            if peer["address"]:
                peers.append(peer)
    if not peers:
        return _wrap_raw(output, "normal")
    lvl = "warning" if not all_full else "normal"
    msg = "存在非 Full 状态的 OSPF 邻居" if not all_full else ""
    return _wrap(peers), lvl, msg


def _parse_vrrp(output: str) -> tuple[str, str, str]:
    vrrps = []
    for line in output.split("\n"):
        line = line.strip()
        if "---" in line or "VRID" in line:
            continue
        for p in line.split():
            if p.startswith(("Vlanif", "GigabitEthernet", "GE", "Eth-Trunk")):
                v = {"interface": p, "vrid": "", "state": "", "priority": ""}
                parts = line.split()
                for w in parts:
                    wl = w.lower()
                    if wl == "master":
                        v["state"] = "Master"
                    elif wl == "backup":
                        v["state"] = "Backup"
                    elif wl == "initialize":
                        v["state"] = "Init"
                    try:
                        val = int(w)
                        if 1 <= val <= 255:
                            v["priority"] = w
                    except ValueError:
                        pass
                vrrps.append(v)
    if not vrrps:
        return _wrap_raw(output, "normal")
    return _wrap(vrrps), "normal", f"共 {len(vrrps)} 个VRRP组"


def _parse_acl(output: str) -> tuple[str, str, str]:
    count = 0
    for line in output.split("\n"):
        line = line.strip()
        if (line.startswith("rule") or line.startswith("Rule")) and ("permit" in line or "deny" in line):
            count += 1
    return _wrap({"aclCount": str(count)}), "normal", ""


def _parse_ntp(output: str) -> tuple[str, str, str]:
    data = {"status": "未同步", "server": ""}
    for line in output.split("\n"):
        line = line.strip()
        lower = line.lower()
        if "synchronized" in lower or "sync" in lower:
            data["status"] = "已同步"
        if "clock" in lower and "is" in line:
            data["status"] = "未同步" if "not" in lower else "已同步"
        if "server" in lower or "reference" in lower:
            for p in line.split():
                if "." in p and "clock" not in p:
                    data["server"] = p
    lvl = "warning" if data["status"] == "未同步" else "normal"
    msg = "NTP 时钟未同步" if data["status"] == "未同步" else ""
    return _wrap(data), lvl, msg


# ======================== 安全检查解析器 ========================

def _sec_pass(msg: str, data: dict = None) -> tuple[str, str, str]:
    """安全项通过：合规配置存在或危险配置不存在"""
    return _wrap(data or {"status": "合规"}), "normal", msg


def _sec_fail(msg: str, sev: str, data: dict = None) -> tuple[str, str, str]:
    """安全项不通过，sev: high/medium/low → level: error/warning/normal"""
    lvl = "error" if sev == "high" else "warning" if sev == "medium" else "normal"
    return _wrap(data or {"status": "不合规"}), lvl, msg


def _parse_weak_password(output: str) -> tuple[str, str, str]:
    """检查 local-user 是否使用了弱密码/简单密码"""
    if not output or not output.strip():
        return _sec_pass("未配置本地用户或密码信息不可读取")
    weak_patterns = ["cipher admin", "cipher password", "cipher huawei", "cipher 123",
                     "simple admin", "simple password", "simple huawei", "simple 123",
                     "irreversible-cipher", "cipher %@%", "simple %@%"]
    for p in weak_patterns:
        if p.lower() in output.lower():
            return _sec_fail("检测到弱密码或默认密码配置", "high",
                             {"detail": f"存在疑似弱密码: {p}", "status": "不合规"})
    return _sec_pass("未发现弱密码特征", {"status": "合规"})


def _parse_telnet(output: str) -> tuple[str, str, str]:
    """检查 Telnet 服务是否启用 — 存在 telnet server enable → 不合规"""
    if not output or not output.strip():
        return _sec_pass("Telnet 服务未启用（配置中未找到）", {"status": "合规"})
    if "telnet server enable" in output.lower() or "telnet server enable" in output:
        if "undo telnet" in output.lower():
            return _sec_pass("Telnet 已通过 undo 命令关闭", {"status": "合规"})
        return _sec_fail("Telnet 服务已启用，存在明文传输风险", "high",
                         {"detail": output.strip(), "status": "不合规"})
    return _sec_pass("Telnet 服务未启用", {"status": "合规"})


def _parse_ssh_v1(output: str) -> tuple[str, str, str]:
    """检查 SSH 服务器是否支持 V1 协议"""
    if not output or not output.strip():
        return _sec_pass("SSH 服务状态不可读取（可能未启用）", {"status": "合规"})
    lower = output.lower()
    if "ssh version 1" in lower or "version 1.0" in lower or "v1" in lower:
        return _sec_fail("SSH 服务器支持不安全的 V1 协议", "high",
                         {"detail": output.strip(), "status": "不合规"})
    return _sec_pass("SSH 协议版本安全", {"status": "合规", "detail": output.strip()[:100]})


def _parse_snmp_community(output: str) -> tuple[str, str, str]:
    """检查 SNMP 团体字是否为默认值 public/private"""
    if not output or not output.strip():
        return _sec_pass("未配置 SNMP 团体字", {"status": "合规"})
    lower = output.lower()
    dangerous = []
    for line in output.split("\n"):
        line_lower = line.strip().lower()
        if "public" in line_lower or "private" in line_lower:
            dangerous.append(line.strip()[:80])
    if dangerous:
        return _sec_fail(f"SNMP 使用了默认团体字 public/private", "medium",
                         {"detail": "; ".join(dangerous), "status": "不合规"})
    return _sec_pass("未发现 SNMP 默认团体字", {"status": "合规"})


def _parse_http(output: str) -> tuple[str, str, str]:
    """检查 HTTP 管理是否启用"""
    if not output or not output.strip():
        return _sec_pass("HTTP 管理未启用", {"status": "合规"})
    lower = output.lower()
    if "http server enable" in lower or "http secure-server" in lower:
        if "undo http server enable" in lower or "undo http server" in lower:
            return _sec_pass("HTTP 管理已通过 undo 命令关闭", {"status": "合规"})
        if "http secure-server enable" in lower:
            return _sec_pass("已启用 HTTPS 安全服务", {"status": "合规"})
        return _sec_fail("HTTP 明文管理已启用，建议改为 HTTPS", "medium",
                         {"detail": output.strip()[:100], "status": "不合规"})
    if "http enable" in lower:
        return _sec_fail("HTTP 服务已启用", "medium",
                         {"detail": output.strip()[:100], "status": "不合规"})
    return _sec_pass("HTTP 管理未启用", {"status": "合规"})


def _parse_acl_mgmt(output: str) -> tuple[str, str, str]:
    """检查是否配置了 ACL 规则（管理口保护）"""
    if not output or not output.strip():
        return _sec_fail("未配置任何 ACL 规则，管理口缺乏访问控制", "medium",
                         {"status": "不合规"})
    rule_count = 0
    for line in output.split("\n"):
        if line.strip().startswith("rule") or line.strip().startswith("Rule"):
            if "permit" in line.lower() or "deny" in line.lower():
                rule_count += 1
    if rule_count > 0:
        return _sec_pass(f"已配置 {rule_count} 条 ACL 规则", {"status": "合规", "count": rule_count})
    return _sec_fail("ACL 已定义但无有效规则", "medium", {"status": "不合规"})


def _parse_banner(output: str) -> tuple[str, str, str]:
    """检查是否配置了登录横幅（header login/motd）"""
    if not output or not output.strip():
        return _sec_fail("未配置登录警告横幅", "low",
                         {"status": "不合规", "detail": "建议配置 header login 或 header motd"})
    lower = output.lower()
    if "header login" in lower or "header motd" in lower or "header shell" in lower:
        return _sec_pass("已配置登录横幅", {"status": "合规",
                                             "detail": output.strip().split("\n")[0][:80]})
    return _sec_fail("未配置登录警告横幅", "low", {"status": "不合规"})


def _parse_timeout(output: str) -> tuple[str, str, str]:
    """检查是否配置了会话超时（idle-timeout）"""
    if not output or not output.strip():
        return _sec_fail("未配置会话超时，存在安全风险", "low",
                         {"status": "不合规", "detail": "建议配置 idle-timeout"})
    lower = output.lower()
    if "idle-timeout" in lower or "idle timeout" in lower:
        return _sec_pass("已配置会话超时", {"status": "合规",
                                             "detail": output.strip().split("\n")[0][:80]})
    return _sec_fail("未配置会话超时", "low", {"status": "不合规"})


def _parse_logging(output: str) -> tuple[str, str, str]:
    """检查是否配置了远程日志（info-center / syslog）"""
    if not output or not output.strip():
        return _sec_fail("未配置远程日志（Syslog）", "low",
                         {"status": "不合规", "detail": "建议配置 info-center loghost"})
    lower = output.lower()
    if "info-center" in lower or "syslog" in lower:
        if "info-center enable" in lower or "info-center loghost" in lower:
            return _sec_pass("已配置远程日志", {"status": "合规",
                                                 "detail": output.strip().split("\n")[0][:80]})
        return _sec_pass("检测到日志相关配置", {"status": "合规"})
    return _sec_fail("未配置远程日志", "low", {"status": "不合规"})


def _parse_ntp_config(output: str) -> tuple[str, str, str]:
    """检查 NTP 时间同步是否配置（安全合规视角）"""
    if not output or not output.strip():
        return _sec_fail("NTP 时间同步未配置，日志审计时间不准", "low",
                         {"status": "不合规", "detail": "建议配置 ntp-service"})
    lower = output.lower()
    if "synchronized" in lower or "sync" in lower or "ntp-service server" in lower:
        return _sec_pass("NTP 时间同步已配置", {"status": "合规",
                                                 "detail": output.strip().split("\n")[0][:80]})
    if "status" in lower or "reference" in lower:
        return _sec_pass("检测到 NTP 相关配置", {"status": "合规"})
    return _sec_fail("NTP 时间同步未配置", "low", {"status": "不合规"})
