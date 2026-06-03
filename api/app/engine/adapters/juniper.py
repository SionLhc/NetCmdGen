"""Juniper Junos 适配器。"""
from __future__ import annotations
from typing import Any, Dict
from app.engine.base import FeatureNotSupported
from app.engine.vendors.juniper import JuniperConfigGenerator

class JuniperAdapter:
    vendor_code = "juniper"
    vendor_name = "Juniper 瞻博"
    _MAP = {k: getattr(JuniperConfigGenerator, f"generate_{k}") for k in ("basic","vlan","routing","security","interface")}
    @property
    def supported_features(self): return tuple(self._MAP.keys())
    def generate(self, feature: str, params: Dict[str, Any]) -> str:
        fn = self._MAP.get(feature)
        if fn is None: raise FeatureNotSupported(f"Juniper 不支持 {feature!r}")
        return fn(params)
    def generate_full(self, config: Dict[str, Any]) -> str:
        return JuniperConfigGenerator.generate_all(config)
