"""命令速查 API。

把 NetOps-toolkit 的 `utils/manual/{vendor}_manual.py` 导出的嵌套 dict
扁平化为搜索友好的列表，支持关键词搜索 + 层级浏览。
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from app.data.manual.huawei import HUAWEI_COMMANDS
from app.data.manual.h3c import H3C_COMMANDS
from app.data.manual.ruijie import RUIJIE_COMMANDS
from app.data.manual.maipu import MAIPU_COMMANDS

router = APIRouter()

_MANUALS: Dict[str, Dict[str, Any]] = {
    "huawei": HUAWEI_COMMANDS,
    "h3c": H3C_COMMANDS,
    "ruijie": RUIJIE_COMMANDS,
    "maipu": MAIPU_COMMANDS,
}


def _flatten(data: dict, path: List[str] = None) -> List[dict]:
    """递归扁平化嵌套 dict → 列表。

    每个叶子节点（包含 command/description/example）会被转成：
        {"category": "基础配置 > 系统管理", "name": "进入系统视图", "command": "...", ...}
    """
    if path is None:
        path = []
    result: List[dict] = []
    for key, value in data.items():
        if isinstance(value, dict) and "command" in value:
            # 叶子：命令条目
            result.append({
                "category": " > ".join(path + [key[:-1] if key.endswith("配置") else key]),
                "name": key,
                **value,
            })
        elif isinstance(value, dict):
            # 中间节点：继续递归
            result.extend(_flatten(value, path + [key]))
    return result


@router.get("/manual/{vendor}", summary="厂商命令速查列表")
def manual_list(
    vendor: str,
    keyword: str = Query(
        "", description="关键词，搜索 名称/命令/描述", max_length=50,
    ),
) -> dict:
    """列出某厂商的全部命令速查条目，支持关键词过滤。"""
    vendor = vendor.lower()
    data = _MANUALS.get(vendor)
    if data is None:
        raise HTTPException(status_code=404, detail=f"不支持厂商 {vendor!r}")

    items = _flatten(data)
    if keyword:
        kw = keyword.lower()
        items = [
            it for it in items
            if kw in it.get("name", "").lower()
            or kw in it.get("command", "").lower()
            or kw in it.get("description", "").lower()
        ]
    return {"vendor": vendor, "total": len(items), "items": items}


@router.get("/manual/{vendor}/tree", summary="厂商命令层级树")
def manual_tree(vendor: str) -> dict:
    """返回某厂商的原始嵌套结构（用于前端树形展示）。"""
    vendor = vendor.lower()
    data = _MANUALS.get(vendor)
    if data is None:
        raise HTTPException(status_code=404, detail=f"不支持厂商 {vendor!r}")
    return {"vendor": vendor, "tree": data}
