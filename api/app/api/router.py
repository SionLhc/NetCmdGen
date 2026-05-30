"""API 路由聚合"""
from fastapi import APIRouter

from app.api import generate, manual, tools_extra, tools_subnet

api_router = APIRouter()

api_router.include_router(tools_subnet.router, prefix="/tools", tags=["tools"])
api_router.include_router(tools_extra.router, prefix="/tools", tags=["tools"])
api_router.include_router(generate.router, tags=["generate"])
api_router.include_router(manual.router, tags=["manual"])
