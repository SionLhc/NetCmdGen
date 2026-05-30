# NetCmdGen API

NetCmdGen 后端服务，基于 FastAPI。命令生成内核、网络工具、命令速查均依托
[Flocks NetOps-toolkit](../opensource/NetOps-toolkit)（MIT 协议）的核心模块复用而来，
具体复用清单见 [`docs/NetOps-toolkit复用方案.md`](../docs/NetOps-toolkit复用方案.md)。

## 启动

```powershell
# 1. 把 NetOps-toolkit 的可复用代码同步到 api/app
pwsh ../scripts/sync-from-netops.ps1

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

启动后访问：
- 健康检查：http://127.0.0.1:8000/api/health
- 子网计算：http://127.0.0.1:8000/api/tools/subnet?ip=192.168.1.10&mask=255.255.255.0
- 接口文档：http://127.0.0.1:8000/docs

## 目录约定

```
api/
├── app/
│   ├── main.py            FastAPI 入口
│   ├── api/               路由层
│   ├── core/              通用工具（validator 等）
│   ├── tools/             网络工具（subnet/ping/trace/portscan/dns）
│   ├── data/              静态数据（命令速查 manual、案例库 cases）
│   └── engine/            命令生成引擎
│       ├── vendors/       各厂商原始 Generator（来自 NetOps-toolkit）
│       └── adapters/      统一接口的 Adapter 层
├── requirements.txt
└── LICENSE-NetOps-toolkit
```

## 致谢

本项目核心命令生成内核、网络工具、命令速查数据复用自
[Flocks NetOps-toolkit](https://github.com/) (MIT License, Copyright (c) 2026 Flocks NetOps Toolkit)。
完整许可证见 `LICENSE-NetOps-toolkit`。
