"""拓扑持久化 API — 以 JSON 文件存储到服务器项目本地目录。

存储路径: api/data/topologies/{topo_id}.json
列表索引: api/data/topologies/_index.json
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

# 与 api/ 平级的数据目录
_STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "topologies")
_INDEX_FILE = os.path.join(_STORE_DIR, "_index.json")


def _ensure_store():
    os.makedirs(_STORE_DIR, exist_ok=True)
    if not os.path.exists(_INDEX_FILE):
        with open(_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def _read_index() -> List[dict]:
    _ensure_store()
    with open(_INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_index(data: List[dict]):
    _ensure_store()
    with open(_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class TopoCreate(BaseModel):
    name: str = "未命名拓扑"


class TopoData(BaseModel):
    """拓扑数据（AntV X6 的 graph.toJSON() 结果）"""
    data: dict


# ─── 列表 ───

@router.get("/topologies")
def list_topologies():
    """获取所有拓扑方案列表"""
    items = _read_index()
    # 按时间倒排
    items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return {"items": items}


@router.post("/topologies")
def create_topology(body: TopoCreate):
    """新建拓扑方案（空画布）"""
    topo_id = f"topo_{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()
    item = {"id": topo_id, "name": body.name, "created_at": now, "updated_at": now}

    index = _read_index()
    index.append(item)
    _write_index(index)

    # 写空数据文件
    empty = {"cells": []}
    _save_topo_file(topo_id, empty)

    return {"id": topo_id, "name": body.name}


# ─── 读取 ───

@router.get("/topologies/{topo_id}")
def get_topology(topo_id: str):
    """读取指定拓扑的完整数据"""
    path = _topo_path(topo_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="拓扑方案不存在")
    with open(path, "r", encoding="utf-8") as f:
        return {"id": topo_id, "data": json.load(f)}


# ─── 保存 ───

@router.put("/topologies/{topo_id}")
def save_topology(topo_id: str, body: TopoData):
    """保存拓扑数据（覆盖写入）"""
    index = _read_index()
    item = next((x for x in index if x["id"] == topo_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="拓扑方案不存在")

    _save_topo_file(topo_id, body.data)

    # 更新时间戳
    item["updated_at"] = datetime.now().isoformat()
    _write_index(index)

    return {"ok": True}


# ─── 重命名 ───

@router.patch("/topologies/{topo_id}/rename")
def rename_topology(topo_id: str, new_name: str = Query(..., description="新名称")):
    """重命名拓扑方案"""
    index = _read_index()
    item = next((x for x in index if x["id"] == topo_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="拓扑方案不存在")
    item["name"] = new_name
    item["updated_at"] = datetime.now().isoformat()
    _write_index(index)
    return {"ok": True}


# ─── 删除 ───

@router.delete("/topologies/{topo_id}")
def delete_topology(topo_id: str):
    """删除拓扑方案及数据文件"""
    path = _topo_path(topo_id)
    if os.path.exists(path):
        os.remove(path)

    index = _read_index()
    new_index = [x for x in index if x["id"] != topo_id]
    _write_index(new_index)
    return {"ok": True}


# ─── 导入 ───

@router.post("/topologies/import")
def import_topology(body: TopoData):
    """从 JSON 数据导入拓扑（自动创建新方案）"""
    topo_id = f"topo_{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()
    item = {"id": topo_id, "name": "导入方案", "created_at": now, "updated_at": now}

    index = _read_index()
    index.append(item)
    _write_index(index)

    _save_topo_file(topo_id, body.data)
    return {"id": topo_id, "name": item["name"]}


# ─── 工具函数 ───

def _topo_path(topo_id: str) -> str:
    return os.path.join(_STORE_DIR, f"{topo_id}.json")


def _save_topo_file(topo_id: str, data: dict):
    _ensure_store()
    with open(_topo_path(topo_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
