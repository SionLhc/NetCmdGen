"""网络运维工具箱 FastAPI 入口"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.router import api_router
from app.api.ros_snmp_monitor import start_collector, stop_collector

# 前端静态文件目录
STATIC_DIR = Path(__file__).parent.parent.parent / "web" / "dist"


@asynccontextmanager
async def lifespan(application: FastAPI):
    """应用生命周期 — 启动/停止后台采集器"""
    start_collector(poll_interval=3.0)
    yield
    stop_collector()


app = FastAPI(
    title="网络运维工具箱",
    description="多厂商网络配置命令生成与网络工具集",
    version="1.0.0",
    lifespan=lifespan,
)

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
    return {"status": "ok", "service": "network-ops-toolkit"}


# ── 生产环境：服务前端静态文件 ──
if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str = ""):
        """SPA fallback：所有非 API 路径返回 index.html"""
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
