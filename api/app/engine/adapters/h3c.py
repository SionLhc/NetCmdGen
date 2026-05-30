"""H3C 适配器。

H3C 源码 ``H3CConfigGenerator`` 已经是统一的 ``(config: Dict) -> str`` 接口，
本适配器只做特性码到方法的映射。
"""
from __future__ import annotations

from typing import Any, Dict

from app.engine.base import FeatureNotSupported
from app.engine.vendors.h3c import H3CConfigGenerator


class H3CAdapter:
    vendor_code = "h3c"
    vendor_name = "华三 H3C"

    # 特性码 → H3CConfigGenerator 静态方法
    _FEATURE_MAP = {
        "basic": H3CConfigGenerator.generate_basic_config,
        "vlan": H3CConfigGenerator.generate_vlan_config,
        "routing": H3CConfigGenerator.generate_routing_config,
        "security": H3CConfigGenerator.generate_security_config,
        "interface": H3CConfigGenerator.generate_interface_config,
        "service": H3CConfigGenerator.generate_service_config,
    }

    @property
    def supported_features(self):
        return tuple(self._FEATURE_MAP.keys())

    def generate(self, feature: str, params: Dict[str, Any]) -> str:
        fn = self._FEATURE_MAP.get(feature)
        if fn is None:
            raise FeatureNotSupported(
                f"H3C 暂不支持特性 {feature!r}，可选: {list(self._FEATURE_MAP.keys())}"
            )
        return fn(params)

    def generate_full(self, config: Dict[str, Any]) -> str:
        return H3CConfigGenerator.generate_all(config)
