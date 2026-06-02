"""H3C 适配器。

支持 Comware V5 / V7 版本命令区分。
"""
from __future__ import annotations

from typing import Any, Dict

from app.engine.base import FeatureNotSupported
from app.engine.vendors.h3c import H3CConfigGenerator
from app.engine.vendors.h3c_version import ComwareVersion


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

    def generate(self, feature: str, params: Dict[str, Any],
                 version: ComwareVersion = ComwareVersion.V5) -> str:
        fn = self._FEATURE_MAP.get(feature)
        if fn is None:
            raise FeatureNotSupported(
                f"H3C 暂不支持特性 {feature!r}，可选: {list(self._FEATURE_MAP.keys())}"
            )
        # basic 和 security 需要版本参数，其他特性向后兼容
        if feature in ("basic", "security"):
            return fn(params, version)
        return fn(params)

    def generate_full(self, config: Dict[str, Any],
                      comware_version: str = "v5") -> str:
        """生成完整配置，支持 Comware V5/V7 版本区分。"""
        version = ComwareVersion(comware_version) if comware_version in ("v5", "v7") else ComwareVersion.V5
        return H3CConfigGenerator.generate_all(config, version)
