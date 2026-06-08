"""无线检测命令解析器 — 华为/H3C WLAN 输出解析"""
from __future__ import annotations

import re
from typing import Any


# ── 华为 WLAN 命令 ──

def parse_ap_list(output: str) -> list[dict]:
    """解析 display wlan ap all — 返回 AP 列表"""
    aps = []
    if not output or "Error:" in output or "display wlan" not in output.lower():
        return aps

    # 华为 display wlan ap all 表格格式：
    # AP ID  AP Name      AP Type        AP MAC          State     IP Address
    # 0      ap-01        AP7050DN-E     00e0-fc12-3456  normal    192.168.1.10
    for line in output.split("\n"):
        line = line.strip()
        if not line or line.startswith("-") or line.startswith("AP ID") or line.startswith("Total"):
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        # 尝试匹配 MAC 地址
        mac_match = re.search(r"([0-9a-fA-F]{4}[-.][0-9a-fA-F]{4}[-.][0-9a-fA-F]{4})", line)
        ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
        aps.append({
            "ap_id": parts[0],
            "name": parts[1],
            "model": parts[2] if len(parts) > 2 else "",
            "mac": mac_match.group(1) if mac_match else "",
            "status": "online" if "normal" in line.lower() or "nor" in line.lower() else "offline",
            "ip": ip_match.group(1) if ip_match else "",
        })
    return aps


def parse_ap_radio(output: str) -> list[dict]:
    """解析 display wlan ap radio all — 射频参数"""
    radios = []
    for line in output.split("\n"):
        line = line.strip()
        if not line or line.startswith("-"):
            continue
        # 提取 AP 名称 + 射频号 + 信道 + 功率
        # 典型格式: ap-01  Radio 0  2.4G  CH 6  20dBm  on
        parts = line.split()
        if len(parts) < 4:
            continue
        radio = {
            "ap_name": parts[0],
            "radio_id": "",
            "band": "",
            "channel": "",
            "power": "",
            "status": "on",
        }
        # 找 Radio 编号
        for i, p in enumerate(parts):
            if p.lower() == "radio" and i + 1 < len(parts):
                radio["radio_id"] = parts[i + 1]
            if "2.4g" in p.lower() or "2.4" in p.lower():
                radio["band"] = "2.4GHz"
            if "5g" in p.lower() or "5ghz" in p.lower():
                radio["band"] = "5GHz"
            if p.upper().startswith("CH") or p.lower() == "channel" or p.upper().startswith("CH"):
                # 可能是 "CH6" 或 "Ch-149"
                pass
            # 提取信道号
            ch_match = re.search(r"CH[-\s]*(\d+)", line, re.IGNORECASE)
            if ch_match:
                radio["channel"] = ch_match.group(1)
            # 提取功率
            pwr_match = re.search(r"(\d+)\s*dBm", line, re.IGNORECASE)
            if pwr_match:
                radio["power"] = pwr_match.group(1) + "dBm"
            radio["status"] = "off" if "off" in line.lower() else "on"
        radios.append(radio)
    return radios


def parse_client_list(output: str) -> list[dict]:
    """解析 display wlan client / display station all — 客户端列表"""
    clients = []
    for line in output.split("\n"):
        line = line.strip()
        if not line or line.startswith("-") or line.startswith("ST") or "Total" in line:
            continue
        mac_match = re.search(r"([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})", line)
        ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
        # 信号强度 RSSI
        rssi_match = re.search(r"[-](\d{2})\s*dBm", line)
        # 速率 Mbps
        rate_match = re.search(r"(\d+)\s*Mbps", line, re.IGNORECASE)
        if mac_match:
            clients.append({
                "mac": mac_match.group(1),
                "ip": ip_match.group(1) if ip_match else "",
                "rssi": -int(rssi_match.group(1)) if rssi_match else 0,
                "rate": rate_match.group(1) + " Mbps" if rate_match else "",
            })
    return clients


def parse_ssid_list(output: str) -> list[dict]:
    """解析 display wlan ssid — SSID 配置"""
    ssids = []
    current = {}
    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
        # 匹配 SSID 名称行
        ssid_match = re.search(r"SSID\s*[:\s]+(\S+)", line, re.IGNORECASE)
        if ssid_match:
            if current:
                ssids.append(current)
            current = {"ssid": ssid_match.group(1), "security": "", "vlan": "", "hidden": "no"}
            continue
        # 安全策略
        if "security" in line.lower() or "encrypt" in line.lower():
            if "wpa3" in line.lower():
                current["security"] = "WPA3"
            elif "wpa2" in line.lower():
                current["security"] = "WPA2"
            elif "wpa" in line.lower():
                current["security"] = "WPA"
            elif "wep" in line.lower():
                current["security"] = "WEP"
            elif "open" in line.lower():
                current["security"] = "Open"
            else:
                current["security"] = line.split(":")[-1].strip() if ":" in line else line
        # VLAN
        vlan_match = re.search(r"VLAN\s*[:\s]+(\d+)", line, re.IGNORECASE)
        if vlan_match:
            current["vlan"] = vlan_match.group(1)
        # 隐藏
        if "hide" in line.lower() or "hidden" in line.lower():
            current["hidden"] = "yes"
    if current:
        ssids.append(current)
    return ssids


def parse_radio_utilization(output: str) -> list[dict]:
    """解析 display wlan ap radio utilization — 信道利用率/底噪"""
    results = []
    for line in output.split("\n"):
        line = line.strip()
        chan_util = re.search(r"(?:channel\s*util|util|ChUtil)[^\d]*(\d+)\s*%?", line, re.IGNORECASE)
        noise = re.search(r"(?:noise|底噪)[^\d]*[-](\d+)\s*dBm", line, re.IGNORECASE)
        if chan_util:
            results.append({
                "type": "channel_utilization",
                "value": int(chan_util.group(1)),
                "unit": "%",
            })
        if noise:
            results.append({
                "type": "noise_floor",
                "value": -int(noise.group(1)),
                "unit": "dBm",
            })
    return results


# ── 命令 → 解析器映射 ──

WIRELESS_COMMANDS: dict[str, str] = {
    "ap_list": "display wlan ap all",
    "ap_radio": "display wlan ap radio all",
    "client_list": "display wlan client",
    "ssid_list": "display wlan ssid",
    "radio_util": "display wlan ap radio utilization",
}

WIRELESS_PARSERS: dict[str, Any] = {
    "ap_list": parse_ap_list,
    "ap_radio": parse_ap_radio,
    "client_list": parse_client_list,
    "ssid_list": parse_ssid_list,
    "radio_util": parse_radio_utilization,
}

# ── 华三 WLAN 命令（备用） ──

H3C_COMMANDS: dict[str, str] = {
    "ap_list": "display wlan ap all",
    "ap_radio": "display wlan ap all radio",
    "client_list": "display wlan client verbose",
    "ssid_list": "display wlan service-template",
    "radio_util": "display wlan ap all radio",
}
