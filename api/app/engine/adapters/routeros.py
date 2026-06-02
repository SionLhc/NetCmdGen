"""MikroTik RouterOS 适配器。

支持 RouterOS V6 / V7 版本命令区分。
"""
from __future__ import annotations

from typing import Any, Dict

from app.engine.base import FeatureNotSupported
from app.engine.vendors.routeros import RouterOSConfigGenerator
from app.engine.vendors.routeros.version_config import RouterOSVersion


class RouterOSAdapter:
    vendor_code = "routeros"
    vendor_name = "MikroTik RouterOS"

    _FEATURES = {
        "basic": RouterOSConfigGenerator.generate_basic,
        "vlan": RouterOSConfigGenerator.generate_vlan,
        "routing": RouterOSConfigGenerator.generate_routing,
        "security": RouterOSConfigGenerator.generate_security,
        "interface": RouterOSConfigGenerator.generate_interface,
        "qos": RouterOSConfigGenerator.generate_qos,
    }

    @property
    def supported_features(self):
        return tuple(self._FEATURES.keys())

    def generate(self, feature: str, params: Dict[str, Any],
                 version: RouterOSVersion = RouterOSVersion.V6) -> str:
        fn = self._FEATURES.get(feature)
        if fn is None:
            raise FeatureNotSupported(
                f"RouterOS 暂不支持特性 {feature!r}，可选: {list(self._FEATURES.keys())}"
            )
        return fn(params, version)

    def generate_full(self, config: Dict[str, Any],
                      ros_version: str = "v6") -> str:
        """生成完整 RouterOS 配置，支持 V6/V7 版本区分。"""
        version_str = ros_version if ros_version in ("v6", "v7") else "v6"
        return RouterOSConfigGenerator.generate_all(config, version_str)
