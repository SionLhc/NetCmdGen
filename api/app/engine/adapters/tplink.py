"""TP-LINK 适配器。"""
from __future__ import annotations
from typing import Any, Dict
from app.engine.base import FeatureNotSupported
from app.engine.vendors.tplink import TPLinkConfigGenerator


class TPLinkAdapter:
    vendor_code = "tplink"
    vendor_name = "TP-LINK"

    _MAP: Dict[str, Any] = {
        "basic": TPLinkConfigGenerator.generate_basic,
        "vlan": TPLinkConfigGenerator.generate_vlan,
        "routing": TPLinkConfigGenerator.generate_routing,
        "security": TPLinkConfigGenerator.generate_security,
        "interface": TPLinkConfigGenerator.generate_interface,
    }

    @property
    def supported_features(self): return tuple(self._MAP.keys())

    def generate(self, feature: str, params: Dict[str, Any]) -> str:
        fn = self._MAP.get(feature)
        if fn is None: raise FeatureNotSupported(f"TP-LINK 不支持 {feature!r}")
        return fn(params)

    def generate_full(self, config: Dict[str, Any]) -> str:
        if "nat" in config: config.setdefault("wan", {})["nat_rules"] = config["nat"].get("rules", [])
        if "acl" in config: config.setdefault("security", {})["acl_rules"] = config.get("acl", {}).get("rules", [])
        return TPLinkConfigGenerator.generate_all(config)
