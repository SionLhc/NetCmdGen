"""华为适配器。

华为 Generator 类（BasicConfigGenerator / VLANConfigGenerator / ...）均为细粒度
静态方法，无统一 dict 入口。本 Adapter 负责将 API 侧的 ``(feature, params)``
映射到具体的方法调用，并组装多段输出。

支持 VRP 版本选择：V5（默认）/ V8 / V300。
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.engine.base import FeatureNotSupported
from app.engine.vendors.huawei.basic import BasicConfigGenerator
from app.engine.vendors.huawei.vlan import VLANConfigGenerator
from app.engine.vendors.huawei.routing import RoutingConfigGenerator
from app.engine.vendors.huawei.security import SecurityConfigGenerator
from app.engine.vendors.huawei.interface import InterfaceConfigGenerator
from app.engine.vendors.huawei.qos import QoSConfigGenerator
from app.engine.vendors.huawei.version_config import VrpVersion


class HuaweiAdapter:
    vendor_code = "huawei"
    vendor_name = "华为 Huawei"
    supported_features = ("basic", "vlan", "routing", "security", "interface", "qos")

    # ── basic ───────────────────────────────────────────────
    def _gen_basic(self, params: Dict[str, Any]) -> str:
        out: List[str] = []
        if "hostname" in params:
            out.append(BasicConfigGenerator.generate_hostname(params["hostname"]))
        if "password" in params:
            p = params["password"]
            out.append(BasicConfigGenerator.generate_password(
                p.get("value", ""), p.get("encrypted", False)
            ))
        if params.get("enable_ssh"):
            ssh = params.get("ssh", {})
            out.append(BasicConfigGenerator.generate_ssh_config(
                port=ssh.get("port", 22),
                timeout=ssh.get("timeout", 60),
                max_auth_tries=ssh.get("max_auth_tries", 5),
                rekey_interval=ssh.get("rekey_interval", 60),
            ))
        if params.get("enable_telnet"):
            out.append(BasicConfigGenerator.generate_telnet_config())
        if "user" in params:
            u = params["user"]
            out.append(BasicConfigGenerator.generate_aaa_user(
                username=u.get("username", "admin"),
                password=u.get("password", ""),
                level=u.get("level", 15),
                encrypted=u.get("encrypted", False),
                service_types=u.get("service_types"),
            ))
        if "ntp" in params:
            ntp = params["ntp"]
            out.append(BasicConfigGenerator.generate_ntp_config(
                servers=ntp.get("servers"),
                timezone=ntp.get("timezone", "UTC+8"),
                broadcast_enable=ntp.get("broadcast_enable", False),
            ))
        if "snmp" in params:
            s = params["snmp"]
            out.append(BasicConfigGenerator.generate_snmp_config(
                version=s.get("version", "v2c"),
                community_read=s.get("community_read"),
                community_write=s.get("community_write"),
                sys_location=s.get("sys_location"),
                sys_contact=s.get("sys_contact"),
                trap_enable=s.get("trap_enable", False),
                trap_host=s.get("trap_host"),
            ))
        if params.get("log"):
            log = params["log"]
            out.append(BasicConfigGenerator.generate_log_config(
                host=log.get("host"),
                log_level=log.get("log_level", "informational"),
            ))
        if not out:
            return ""
        return "\n".join(["\n#\n# 基础配置\n#", ""] + out)

    # ── vlan ────────────────────────────────────────────────
    def _gen_vlan(self, params: Dict[str, Any]) -> str:
        return VLANConfigGenerator.generate_vlan_all(params)

    # ── routing / security / interface / qos ──────────────
    def _gen_routing(self, params: Dict[str, Any]) -> str:
        """生成路由配置（静态路由 / OSPF / BGP / RIP / 默认路由）。"""
        return RoutingConfigGenerator.generate_route_all(params)

    def _gen_security(self, params: Dict[str, Any]) -> str:
        """生成安全配置（ACL / 端口安全 / MAC绑定 / 802.1X / RADIUS / DHCP Snooping 等）。"""
        return SecurityConfigGenerator.generate_security_all(params)

    def _gen_interface(self, params: Dict[str, Any]) -> str:
        """生成接口配置（Eth-Trunk 聚合 / LACP / LLDP / PoE / 端口隔离 / 环路检测 / 限速）。"""
        return InterfaceConfigGenerator.generate_interface_all(params)

    def _gen_qos(self, params: Dict[str, Any]) -> str:
        """生成 QoS 配置（流分类 / 流行为 / 流策略 / 队列调度 / 带宽策略）。"""
        return QoSConfigGenerator.generate_qos_all(params)

    # ── 统一入口 ─────────────────────────────────────────────
    _GEN = {
        "basic": _gen_basic,
        "vlan": _gen_vlan,
        "routing": _gen_routing,
        "security": _gen_security,
        "interface": _gen_interface,
        "qos": _gen_qos,
    }

    def generate(self, feature: str, params: Dict[str, Any]) -> str:
        fn = self._GEN.get(feature)
        if fn is None:
            raise FeatureNotSupported(
                f"华为暂不支持特性 {feature!r}，可选: {list(self._GEN.keys())}"
            )
        return fn(self, params)

    def generate_full(self, config: Dict[str, Any],
                      vrp_version: str = "v5") -> str:
        """生成完整配置，支持 VRP 版本区分。

        Args:
            config: 配置字典，顶层 key 为 basic/vlan/routing/security/interface/qos
            vrp_version: VRP 系统版本（v5 / v8 / v300），默认 v5
        """
        version = VrpVersion(vrp_version) if vrp_version in ("v5", "v8", "v300") else VrpVersion.V5

        sections = [
            "#\n# 华为交换机配置脚本 (VRP {})\n#".format(version.value.upper()),
            f"# 生成时间: {config.get('description', '')}",
            "#\n",
        ]

        for key in ("basic", "vlan", "routing", "security", "interface", "qos"):
            if key in config:
                if key == "basic":
                    # 基础配置使用版本感知的批量生成
                    sections.append(
                        BasicConfigGenerator.generate_basic_all(config[key], version)
                    )
                else:
                    sections.append(self.generate(key, config[key]))

        # V300 不需要 return，V5/V8 保留
        if version != VrpVersion.V300:
            sections.append("\nreturn")
        return "\n".join(sections)
