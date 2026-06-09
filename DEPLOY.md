# 网络运维工具箱 — 部署说明

## 交付文件清单

```
NetCmdGen/                    ← 整个项目目录打包发过去
├── Dockerfile                ← Docker 镜像构建文件
├── k8s-deployment.yaml       ← K8s 部署配置
├── api/                      ← 后端代码 + requirements.txt
├── web/                      ← 前端源码（可忽略，Docker 内自动构建）
└── DEPLOY.md                 ← 本文件
```

---

## 方式一：Docker 部署（推荐）

### 1. 构建镜像

```bash
cd NetCmdGen
docker build -t network-ops-toolkit:v1.0.0 .
```

### 2. 启动容器

```bash
docker run -d \
  --name net-ops-toolkit \
  -p 8000:8000 \
  -v /data/net-ops-toolkit:/app/app/data \
  network-ops-toolkit:v1.0.0
```

### 3. 验证

```
浏览器访问: http://服务器IP:8000
健康检查: curl http://服务器IP:8000/api/health
          返回 → {"status":"ok","service":"network-ops-toolkit"}
```

---

## 方式二：K8s 部署

### 1. 推送镜像到仓库

```bash
docker tag network-ops-toolkit:v1.0.0 harbor.your-company.com/ops/network-ops-toolkit:v1.0.0
docker push harbor.your-company.com/ops/network-ops-toolkit:v1.0.0
```

### 2. 修改 k8s-deployment.yaml 中的镜像地址

```yaml
image: harbor.your-company.com/ops/network-ops-toolkit:v1.0.0
```

### 3. 部署

```bash
kubectl apply -f k8s-deployment.yaml
```

### 4. 暴露服务（二选一）

```bash
# NodePort
kubectl expose deployment network-ops-toolkit --type=NodePort --port=80 --target-port=8000

# Ingress（推荐）
# 创建 ingress.yaml 指向 service: network-ops-toolkit:80
```

---

## 方式三：直接运行（开发/测试）

```bash
# 后端
cd api
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端（开发模式，有热更新）
cd web
npm install --registry=https://registry.npmmirror.com
npm run dev -- --port 3002

# 前端（生产模式，先构建）
npm run build
# 然后 nginx 指向 web/dist 目录
```

---

## 环境要求

| 组件 | 版本 |
|---|---|
| Docker | 20.10+ |
| Kubernetes | 1.24+ |
| Python | 3.12+ |
| Node.js | 20+ |

---

## 端口说明

| 端口 | 用途 |
|---|---|
| 8000 | 唯一对外端口（前端页面 + API 全部由此端口服务） |

---

## 数据持久化

| 路径 | 说明 | 建议 |
|---|---|---|
| `/app/app/data` | SQLite 数据库目录 | 挂载到宿主机或 PVC |

---

## 注意事项

1. **数据库**：项目使用 SQLite，所有数据文件在 `/app/app/data/*.db`
2. **单实例**：SQLite 不支持多副本并发写，K8s 建议 `replicas: 1`
3. **密码加密**：SSH/Telnet 密码明文存储在 SQLite 中（内网环境可用）
4. **SNMP 采集**：启动时自动开启 3 秒间隔的后台采集器
