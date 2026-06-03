"""厂商适配器工厂。

后续新增厂商只需：
1. 在 ``app/engine/adapters/`` 下新建 Adapter 文件
2. 在本文件 ``_ADAPTERS`` 字典里注册即可
"""
from __future__ import annotations

from typing import Dict

from app.engine.adapters.h3c import H3CAdapter
from app.engine.adapters.huawei import HuaweiAdapter
from app.engine.adapters.maipu import MaipuAdapter
from app.engine.adapters.ruijie import RuijieAdapter
from app.engine.adapters.routeros import RouterOSAdapter
from app.engine.adapters.cisco import CiscoAdapter
from app.engine.adapters.tplink import TPLinkAdapter
from app.engine.adapters.juniper import JuniperAdapter
from app.engine.base import VendorAdapter, VendorNotSupported

# 单例字典；Adapter 都是无状态对象，复用安全
_ADAPTERS: Dict[str, VendorAdapter] = {
    HuaweiAdapter.vendor_code: HuaweiAdapter(),
    H3CAdapter.vendor_code: H3CAdapter(),
    RuijieAdapter.vendor_code: RuijieAdapter(),
    MaipuAdapter.vendor_code: MaipuAdapter(),
    RouterOSAdapter.vendor_code: RouterOSAdapter(),
    CiscoAdapter.vendor_code: CiscoAdapter(),
    TPLinkAdapter.vendor_code: TPLinkAdapter(),
    JuniperAdapter.vendor_code: JuniperAdapter(),
}


def get_adapter(vendor: str) -> VendorAdapter:
    adapter = _ADAPTERS.get(vendor.lower())
    if adapter is None:
        raise VendorNotSupported(
            f"暂不支持厂商 {vendor!r}，可选: {list(_ADAPTERS.keys())}"
        )
    return adapter


def list_vendors() -> list[dict]:
    """列出全部已注册厂商，供前端下拉框使用。"""
    return [
        {
            "code": a.vendor_code,
            "name": a.vendor_name,
            "features": list(a.supported_features),
        }
        for a in _ADAPTERS.values()
    ]
