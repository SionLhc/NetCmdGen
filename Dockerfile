# ── Stage 1: 构建前端 ──
FROM node:20-alpine AS frontend-builder
WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci --registry=https://registry.npmmirror.com
COPY web/ ./
RUN npx vite build

# ── Stage 2: 运行时镜像 ──
FROM python:3.12-slim
LABEL maintainer="网络运维工具箱"
LABEL description="多厂商网络配置命令生成与网络工具集"

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY api/ ./

# 复制前端构建产物
COPY --from=frontend-builder /app/web/dist ./web/dist

# 创建数据目录
RUN mkdir -p /app/app/data

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health')" || exit 1

# 启动
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
