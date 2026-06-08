"""巡检引擎 — asyncio 并发调度 + SNMP优先/SSH降级
从 SwitchManager (Go goroutine + semaphore) 移植为 Python asyncio
"""

import asyncio
import json
import logging
import time
from typing import Callable, Optional

from app.api.inspection_parser import parse_item, is_command_error

logger = logging.getLogger("inspection")

# 华为交换机巡检命令映射（20 项）
INSPECTION_COMMANDS = {
    "设备基本信息": "display version",
    "CPU使用率": "display cpu-usage",
    "内存使用率": "display memory-usage",
    "温度状态": "display temperature",
    "电源状态": "display power",
    "风扇状态": "display fan",
    "接口状态": "display interface brief",
    "接口错包": "display interface brief",
    "VLAN信息": "display vlan",
    "路由表": "display ip routing-table",
    "ARP表": "display arp",
    "MAC地址表": "display mac-address",
    "日志告警": "display logbuffer",
    "STP状态": "display stp brief",
    "链路聚合": "display eth-trunk",
    "OSPF状态": "display ospf peer brief",
    "VRRP状态": "display vrrp",
    "ACL规则": "display acl all",
    "NTP同步": "display ntp-status",
    "当前配置": "display current-configuration",
}

# SNMP 可替代的 8 个巡检项（避免 SSH 命令开销）
SNMP_ITEMS = {
    "CPU使用率", "内存使用率", "接口状态", "接口错包",
    "温度状态", "电源状态", "风扇状态", "设备基本信息",
}

MAX_CONCURRENT = 5  # 最多同时巡检 5 台设备


class InspectionResult:
    """单条巡检结果"""
    def __init__(self, device_id: str, device_name: str, device_ip: str,
                 item_name: str, command: str, raw_output: str,
                 parse_result: str, level: str, message: str,
                 source: str = "SSH"):
        self.device_id = device_id
        self.device_name = device_name
        self.device_ip = device_ip
        self.item_name = item_name
        self.command = command
        self.raw_output = raw_output
        self.parse_result = parse_result
        self.level = level
        self.message = message
        self.source = source
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_ip": self.device_ip,
            "item_name": self.item_name,
            "command": self.command,
            "raw_output": self.raw_output,
            "parse_result": self.parse_result,
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp,
        }


class InspectionEngine:
    """异步巡检引擎"""

    def __init__(self, ssh_executor: Callable = None, snmp_getter: Callable = None):
        """
        :param ssh_executor: async fn(host, port, username, password, command) -> str
        :param snmp_getter: async fn(host, community, port, oid) -> str
        """
        self.ssh_exec = ssh_executor
        self.snmp_get = snmp_getter
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        self._progress_callback: Optional[Callable] = None

    def on_progress(self, cb: Callable):
        self._progress_callback = cb

    async def run(self, devices: list[dict], items: list[str]) -> list[dict]:
        """执行巡检
        :param devices: [{"id":"", "name":"", "ip":"", "port":22, "username":"", "password":"", ...}, ...]
        :param items: ["CPU使用率", "接口状态", ...]
        :return: 所有巡检结果字典列表
        """
        if not devices or not items:
            return []

        sem = self.semaphore
        results_lock = asyncio.Lock()
        all_results: list[dict] = []

        async def inspect_one(dev: dict):
            async with sem:
                dev_results = await self._inspect_device(dev, items)
                async with results_lock:
                    all_results.extend(dev_results)

        tasks = [inspect_one(d) for d in devices]
        await asyncio.gather(*tasks)
        return all_results

    async def _inspect_device(self, dev: dict, items: list[str]) -> list[dict]:
        """单设备巡检：SNMP 优先 → SSH 降级"""
        results = []
        ssh_output_cache = {}  # 同一命令只执行一次
        has_snmp = bool(dev.get("snmp_enabled") and dev.get("snmp_community"))
        has_ssh = bool(dev.get("username") and dev.get("ip"))

        for item_name in items:
            command = INSPECTION_COMMANDS.get(item_name, "")
            source = "SSH"
            raw_output = ""
            level = "normal"
            message = ""
            parse_result = ""

            # 尝试 SNMP（仅支持 8 项）
            if has_snmp and item_name in SNMP_ITEMS and self.snmp_get:
                try:
                    snmp_result = await self._do_snmp(dev, item_name)
                    if snmp_result:
                        raw_output = snmp_result["raw"]
                        parse_result = snmp_result["parsed"]["result"]
                        level = snmp_result["parsed"]["level"]
                        message = snmp_result["parsed"]["message"]
                        source = "SNMP"
                        results.append(InspectionResult(
                            dev.get("id", ""), dev.get("name", ""), dev.get("ip", ""),
                            item_name, command, raw_output, parse_result, level, message, source,
                        ).to_dict())
                        self._notify(dev, item_name)
                        continue
                except Exception as e:
                    logger.warning(f"SNMP {item_name} ({dev.get('ip')}): {e}")

            # SSH 降级
            if not has_ssh or not self.ssh_exec:
                results.append(InspectionResult(
                    dev.get("id", ""), dev.get("name", ""), dev.get("ip", ""),
                    item_name, command, "", "{}", "error", "无 SSH 连接能力", "SSH",
                ).to_dict())
                continue

            try:
                # 缓存复用：同一个命令只执行一次
                if command in ssh_output_cache:
                    raw_output = ssh_output_cache[command]
                else:
                    raw_output = await self.ssh_exec(
                        dev["ip"], dev.get("port", 22),
                        dev["username"], dev["password"],
                        command,
                    )
                    ssh_output_cache[command] = raw_output

                # 检测命令错误
                if is_command_error(raw_output):
                    parsed = {"result": _wrap_raw(raw_output), "level": "warning", "message": "命令不被设备支持"}
                else:
                    parsed = parse_item(item_name, raw_output)

                parse_result = parsed["result"]
                level = parsed["level"]
                message = parsed["message"]
            except Exception as e:
                raw_output = str(e)
                parse_result = "{}"
                level = "error"
                message = f"SSH 执行失败: {e}"

            results.append(InspectionResult(
                dev.get("id", ""), dev.get("name", ""), dev.get("ip", ""),
                item_name, command, raw_output, parse_result, level, message, source,
            ).to_dict())
            self._notify(dev, item_name)

        return results

    async def _do_snmp(self, dev: dict, item_name: str) -> Optional[dict]:
        """SNMP 巡检单个项目"""
        if not self.snmp_get:
            return None
        host = dev["ip"]
        community = dev.get("snmp_community", "public")
        port = dev.get("snmp_port", 161)

        # 各巡检项的 SNMP OID 和简单解析
        snmp_map = {
            "CPU使用率": ("1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5.1", lambda v: f"{{'cpuUsage': '{v}'}}"),
            "内存使用率": ("1.3.6.1.4.1.2011.5.25.31.1.1.1.1.7.1", lambda v: f"{{'memUsage': '{v}'}}"),
            "温度状态": ("1.3.6.1.2.1.2.2.1.8.1", lambda v: _wrap_raw(str(v))),
            "设备基本信息": ("1.3.6.1.2.1.1.5.0", lambda v: f"{{'sysName': '{v}'}}"),
        }

        if item_name not in snmp_map:
            return None

        oid, formatter = snmp_map[item_name]
        value = await self.snmp_get(host, community, port, oid)
        if value is None:
            return None

        try:
            num_val = float(value)
        except ValueError:
            num_val = 0

        # 阈值判断
        thresholds = {
            "CPU使用率": (70, 90),
            "内存使用率": (75, 90),
        }
        if item_name in thresholds:
            warn, err_th = thresholds[item_name]
            if num_val >= err_th:
                level, msg = "error", f"{num_val:.1f} 超过告警阈值 {err_th:.1f}"
            elif num_val >= warn:
                level, msg = "warning", f"{num_val:.1f} 超过预警阈值 {warn:.1f}"
            else:
                level, msg = "normal", ""
        else:
            level, msg = "normal", ""

        return {
            "raw": value,
            "parsed": {"result": formatter(num_val), "level": level, "message": msg},
        }

    def _notify(self, dev: dict, item_name: str):
        if self._progress_callback:
            self._progress_callback({
                "device_id": dev.get("id", ""),
                "device_name": dev.get("name", ""),
                "item_name": item_name,
                "status": "completed",
            })


def _wrap_raw(output: str) -> str:
    return json.dumps({"rawOutput": output}, ensure_ascii=False)
