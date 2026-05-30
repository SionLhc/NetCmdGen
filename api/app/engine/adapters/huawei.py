"""华为适配器。

华为 Generator 类（BasicConfigGenerator / VLANConfigGenerator / ...）均为细粒度
静态方法，无统一 dict 入口。本 Adapter 负责将 API 侧的 ``(feature, params)``
映射到具体的方法调用，并组装多段输出。
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.engine.base import FeatureNotSupported
from app.engine.vendors.huawei.basic import BasicConfigGenerator
from app.engine.vendors.huawei.vlan import VLANConfigGenerator

# 后续补齐 routing/security/interface/qos 的 import
# from app.engine.vendors.huawei.routing import RoutingConfigGenerator
# from app.engine.vendors.huawei.security import SecurityConfigGenerator


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

    # ── routing / security / interface / qos (TODO) ─────────
    def _gen_routing(self, params: Dict[str, Any]) -> str:
        # 后续 import RoutingConfigGenerator 后实现
        return "# routing 模板待接入\n"

    def _gen_security(self, params: Dict[str, Any]) -> str:
        return "# security 模板待接入\n"

    def _gen_interface(self, params: Dict[str, Any]) -> str:
        return "# interface 模板待接入\n"

    def _gen_qos(self, params: Dict[str, Any]) -> str:
        return "# qos 模板待接入\n"

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

    def generate_full(self, config: Dict[str, Any]) -> str:
        sections = [
            "#\n# 华为交换机配置脚本\n#",
            f"# 生成时间: {config.get('description', '')}",
            "#\n",
        ]
        for key in ("basic", "vlan", "routing", "security", "interface", "qos"):
            if key in config:
                sections.append(self.generate(key, config[key]))
        sections.append("\nreturn")
        return "\n".join(sections)
