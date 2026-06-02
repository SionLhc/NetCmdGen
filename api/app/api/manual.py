"""命令速查 API。

把 NetOps-toolkit 的 `utils/manual/{vendor}_manual.py` 导出的嵌套 dict
扁平化为搜索友好的列表，支持关键词搜索 + 版本过滤 + 层级浏览。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.data.manual.huawei import HUAWEI_COMMANDS
from app.data.manual.h3c import H3C_COMMANDS
from app.data.manual.ruijie import RUIJIE_COMMANDS
from app.data.manual.maipu import MAIPU_COMMANDS
from app.data.manual.routeros import ROUTEROS_COMMANDS

router = APIRouter()

_MANUALS: Dict[str, Dict[str, Any]] = {
    "huawei": HUAWEI_COMMANDS,
    "h3c": H3C_COMMANDS,
    "ruijie": RUIJIE_COMMANDS,
    "maipu": MAIPU_COMMANDS,
    "routeros": ROUTEROS_COMMANDS,
}

# 各厂商可用版本列表
_VENDOR_VERSIONS: Dict[str, List[Dict[str, str]]] = {
    "huawei": [
        {"code": "all", "name": "全部版本"},
        {"code": "v5", "name": "VRP V5"},
        {"code": "v8", "name": "VRP V8"},
        {"code": "v300", "name": "VRP V300"},
    ],
    "h3c": [
        {"code": "all", "name": "全部版本"},
        {"code": "v5", "name": "Comware V5"},
        {"code": "v7", "name": "Comware V7"},
    ],
    "ruijie": [
        {"code": "all", "name": "全部版本"},
        {"code": "v10", "name": "RGOS 10.x"},
        {"code": "v11", "name": "RGOS 11.x/12.x"},
    ],
    "maipu": [
        {"code": "all", "name": "全部版本"},
        {"code": "v5", "name": "MyPower V5"},
        {"code": "v8", "name": "MyPower V8"},
    ],
    "routeros": [
        {"code": "all", "name": "全部版本"},
        {"code": "v6", "name": "RouterOS V6"},
        {"code": "v7", "name": "RouterOS V7"},
    ],
}


def _match_version(entry_versions: Optional[List[str]], filter_version: str) -> bool:
    """判断命令条目是否匹配目标版本。

    规则：
    - 无 versions 字段 → 视为通用（匹配所有版本）
    - versions 包含 "all" → 匹配所有版本
    - versions 包含目标版本 → 匹配
    """
    if not entry_versions:
        return True  # 无标记 = 通用
    if "all" in entry_versions:
        return True
    return filter_version in entry_versions


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
            # 叶子：命令条目（华为/H3C 格式）
            entry = {
                "category": " > ".join(path + [key[:-1] if key.endswith("配置") else key]),
                "name": key,
                **value,
            }
            result.append(entry)
        elif isinstance(value, dict):
            # 中间节点：继续递归
            result.extend(_flatten(value, path + [key]))
    return result


def _flatten_list_format(data: dict, path: List[str] = None) -> List[dict]:
    """扁平化锐捷/迈普格式的嵌套 dict（叶子为 list[dict]）。

    锐捷/迈普的数据结构为 大类 → 子类 → [{name, command, description, example, ...}]
    """
    if path is None:
        path = []
    result: List[dict] = []
    for key, value in data.items():
        if isinstance(value, list):
            # 叶子：命令列表
            for entry in value:
                if isinstance(entry, dict):
                    result.append({
                        "category": " > ".join(path + [key]),
                        **entry,
                    })
        elif isinstance(value, dict):
            # 中间节点：继续递归
            result.extend(_flatten_list_format(value, path + [key]))
    return result


@router.get("/manual/{vendor}", summary="厂商命令速查列表")
def manual_list(
    vendor: str,
    keyword: str = Query(
        "", description="关键词，搜索 名称/命令/描述", max_length=50,
    ),
    version: str = Query(
        "all", description="版本过滤，默认为 all（全部版本）", max_length=20,
    ),
) -> dict:
    """列出某厂商的全部命令速查条目，支持关键词 + 版本过滤。"""
    vendor = vendor.lower()
    data = _MANUALS.get(vendor)
    if data is None:
        raise HTTPException(status_code=404, detail=f"不支持厂商 {vendor!r}")

    # 根据数据结构选择对应的扁平化方法
    # 华为/H3C 使用嵌套 dict 格式（叶子是 command dict）
    # 锐捷/迈普 使用嵌套 dict + list 格式（叶子是 list of dicts）
    if vendor in ("ruijie", "maipu"):
        items = _flatten_list_format(data)
    else:
        items = _flatten(data)

    # 版本过滤（"all" 不过滤）
    if version and version != "all":
        items = [
            it for it in items
            if _match_version(it.get("versions"), version)
        ]

    # 关键词搜索
    if keyword:
        kw = keyword.lower()
        items = [
            it for it in items
            if kw in it.get("name", "").lower()
            or kw in it.get("command", "").lower()
            or kw in it.get("description", "").lower()
        ]

    return {
        "vendor": vendor,
        "version": version,
        "total": len(items),
        "items": items,
    }


@router.get("/manual/{vendor}/versions", summary="厂商可选版本")
def manual_versions(vendor: str) -> dict:
    """返回某厂商支持的版本列表。"""
    vendor = vendor.lower()
    versions = _VENDOR_VERSIONS.get(vendor)
    if versions is None:
        raise HTTPException(status_code=404, detail=f"不支持厂商 {vendor!r}")
    return {"vendor": vendor, "versions": versions}


@router.get("/manual/{vendor}/tree", summary="厂商命令层级树")
def manual_tree(vendor: str) -> dict:
    """返回某厂商的原始嵌套结构（用于前端树形展示）。"""
    vendor = vendor.lower()
    data = _MANUALS.get(vendor)
    if data is None:
        raise HTTPException(status_code=404, detail=f"不支持厂商 {vendor!r}")
    return {"vendor": vendor, "tree": data}
