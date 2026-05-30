"""NetCmdGen FastAPI 入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router

app = FastAPI(
    title="NetCmdGen API",
    description="多厂商网络配置命令生成与网络工具集",
    version="0.1.0",
)

# 开发期允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    """健康检查"""
    return {"status": "ok", "service": "netcmdgen-api"}
