"""迈普适配器。

结构与锐捷几乎一致：
- MaipuBasicGenerator.generate_basic_all(dict)  ← basic 统一入口
- MaipuVLANGenerator.generate_vlans / generate_interface / generate_vlanif  ← vlan 细粒度
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.engine.base import FeatureNotSupported
from app.engine.vendors.maipu import MaipuBasicGenerator, MaipuVLANGenerator


class MaipuAdapter:
    vendor_code = "maipu"
    vendor_name = "迈普 Maipu"
    supported_features = ("basic", "vlan", "routing", "security", "interface", "service")

    # ── basic ───────────────────────────────────────────────
    def _gen_basic(self, params: Dict[str, Any]) -> str:
        return MaipuBasicGenerator.generate_basic_all(params)

    # ── vlan ────────────────────────────────────────────────
    def _gen_vlan(self, params: Dict[str, Any]) -> str:
        out: List[str] = ["!", "# VLAN配置", "!"]

        if "vlans" in params:
            out.append(MaipuVLANGenerator.generate_vlans(params["vlans"]))

        if "interfaces" in params:
            for iface in params["interfaces"]:
                out.append(MaipuVLANGenerator.generate_interface(
                    iface["interface"],
                    iface.get("type", "access"),
                    iface.get("vlan_id"),
                    iface.get("trunk_vlans"),
                    iface.get("pvid"),
                ))

        if "vlanifs" in params:
            for vf in params["vlanifs"]:
                out.append(MaipuVLANGenerator.generate_vlanif(
                    vf["vlan_id"],
                    vf["ip_address"],
                    vf.get("mask", "255.255.255.0"),
                    vf.get("description"),
                ))

        return "\n".join(out)

    # ── routing / security / interface / service (TODO) ─────
    def _gen_routing(self, params: Dict[str, Any]) -> str:
        return "! routing 模板待接入\n"

    def _gen_security(self, params: Dict[str, Any]) -> str:
        return "! security 模板待接入\n"

    def _gen_interface(self, params: Dict[str, Any]) -> str:
        return "! interface 模板待接入\n"

    def _gen_service(self, params: Dict[str, Any]) -> str:
        return "! service 模板待接入\n"

    # ── 统一入口 ─────────────────────────────────────────────
    _GEN = {
        "basic": _gen_basic,
        "vlan": _gen_vlan,
        "routing": _gen_routing,
        "security": _gen_security,
        "interface": _gen_interface,
        "service": _gen_service,
    }

    def generate(self, feature: str, params: Dict[str, Any]) -> str:
        fn = self._GEN.get(feature)
        if fn is None:
            raise FeatureNotSupported(
                f"迈普暂不支持特性 {feature!r}，可选: {list(self._GEN.keys())}"
            )
        return fn(self, params)

    def generate_full(self, config: Dict[str, Any]) -> str:
        sections = ["!", "# 迈普交换机配置脚本", "!"]
        for key in ("basic", "vlan", "routing", "security", "interface", "service"):
            if key in config:
                sections.append(self.generate(key, config[key]))
        sections.append("end")
        return "\n".join(sections)
