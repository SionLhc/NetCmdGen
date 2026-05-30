"""命令生成 API。

提供两类入口：
- POST /api/generate          根据 vendor + feature + params 生成单段命令片段
- POST /api/generate/full     根据 vendor + config 生成完整配置脚本
- GET  /api/vendors           列出已支持的厂商及其特性码
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.engine.base import FeatureNotSupported, VendorNotSupported
from app.engine.factory import get_adapter, list_vendors

router = APIRouter()


class GenerateRequest(BaseModel):
    vendor: str = Field(..., description="厂商代码：huawei / h3c / ruijie / maipu", examples=["h3c"])
    feature: str = Field(
        ...,
        description="特性码：basic / vlan / routing / security / interface / service",
        examples=["vlan"],
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="特性参数（结构与厂商 Generator 一致）",
    )


class GenerateFullRequest(BaseModel):
    vendor: str = Field(..., examples=["h3c"])
    config: Dict[str, Any] = Field(
        ...,
        description="完整配置字典，顶层 key 通常包含 description/basic/vlan/routing/security/interface/service",
    )
    topology_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="拓扑上下文（用于园区网场景）",
    )
    scene: Optional[str] = Field(
        default=None,
        description="场景类型：campus_core / campus_access / campus_agg",
    )


class GenerateResponse(BaseModel):
    vendor: str
    feature: Optional[str] = None
    output: str


@router.get("/vendors", summary="已支持的厂商列表")
def get_vendors() -> dict:
    return {"vendors": list_vendors()}


@router.post("/generate", summary="生成单个特性的命令片段", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    try:
        adapter = get_adapter(req.vendor)
        output = adapter.generate(req.feature, req.params)
    except VendorNotSupported as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FeatureNotSupported as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"生成失败: {e}")
    return GenerateResponse(vendor=req.vendor, feature=req.feature, output=output)


@router.post("/generate/full", summary="生成完整配置脚本", response_model=GenerateResponse)
def generate_full(req: GenerateFullRequest) -> GenerateResponse:
    try:
        # 园区网场景：使用专用模板
        if req.scene and req.scene.startswith('campus'):
            from app.engine.templates.campus import CampusTemplate
            
            # 合并 config 和 topology_context
            params = {**req.config}
            if req.topology_context:
                params.update(req.topology_context)
            
            if req.scene == 'campus_core':
                output = CampusTemplate.generate_campus_core(params)
            elif req.scene == 'campus_access':
                output = CampusTemplate.generate_campus_access(params)
            elif req.scene == 'campus_agg':
                # 汇聚交换机暂时使用接入交换机模板（后续扩展）
                output = CampusTemplate.generate_campus_access(params)
            else:
                raise ValueError(f"未知的园区网场景: {req.scene}")
        else:
            # 传统方式：使用厂商适配器
            adapter = get_adapter(req.vendor)
            output = adapter.generate_full(req.config)
    except VendorNotSupported as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"生成失败: {e}")
    return GenerateResponse(vendor=req.vendor, output=output)
