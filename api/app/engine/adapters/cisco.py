"""思科 Cisco IOS 适配器。"""
from __future__ import annotations

from typing import Any, Dict

from app.engine.base import FeatureNotSupported
from app.engine.vendors.cisco import CiscoConfigGenerator


class CiscoAdapter:
    vendor_code = "cisco"
    vendor_name = "思科 Cisco"

    _FEATURE_MAP = {
        "basic": CiscoConfigGenerator.generate_basic_config,
        "vlan": CiscoConfigGenerator.generate_vlan_config,
        "routing": CiscoConfigGenerator.generate_routing_config,
        "security": CiscoConfigGenerator.generate_security_config,
        "interface": CiscoConfigGenerator.generate_interface_config,
        "service": CiscoConfigGenerator.generate_dhcp_config,
        "ipv6": CiscoConfigGenerator.generate_ipv6_config,
    }

    @property
    def supported_features(self):
        return tuple(self._FEATURE_MAP.keys())

    def generate(self, feature: str, params: Dict[str, Any]) -> str:
        fn = self._FEATURE_MAP.get(feature)
        if fn is None:
            raise FeatureNotSupported(
                f"Cisco 暂不支持特性 {feature!r}，可选: {list(self._FEATURE_MAP.keys())}"
            )
        return fn(params)

    def generate_full(self, config: Dict[str, Any]) -> str:
        """生成完整思科配置。"""
        device_type = "路由器" if "wan" in config else "交换机"

        # 合并 dhcp/nat/acl 到已有模块
        if "dhcp" in config and not config.get("wan", {}).get("dhcp_enabled"):
            config.setdefault("wan", {})["dhcp_enabled"] = True
        if "nat" in config:
            pass  # NAT 由 generate_all 独立处理
        if "acl" in config and not config.get("security", {}).get("acl_rules"):
            config.setdefault("security", {})["acl_rules"] = config.get("acl", {}).get("rules", [])

        return CiscoConfigGenerator.generate_all(config)
