"""命令生成引擎统一抽象。

所有厂商 Adapter 必须遵循下面的接口，以便 `factory.get_adapter()` 可以
通过 vendor_code 取到统一调用入口。
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Protocol, runtime_checkable


@runtime_checkable
class VendorAdapter(Protocol):
    """厂商适配器协议。"""

    vendor_code: str  # huawei / h3c / ruijie / maipu / cisco ...
    vendor_name: str  # 中文展示名
    supported_features: Iterable[str]  # 支持的特性码集合

    def generate(self, feature: str, params: Dict[str, Any]) -> str:
        """生成单个特性的命令片段。"""
        ...

    def generate_full(self, config: Dict[str, Any]) -> str:
        """生成完整配置脚本。``config`` 顶层 key 通常包含
        description / basic / vlan / routing / security / interface / service 等。
        """
        ...


class FeatureNotSupported(ValueError):
    """请求了厂商不支持的特性码。"""


class VendorNotSupported(ValueError):
    """请求了未注册的厂商。"""
