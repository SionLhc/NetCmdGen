# NetCmdGen - 多厂商网络命令生成器

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.5+-brightgreen.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110+-teal.svg)](https://fastapi.tiangolo.com/)
[![Vendors](https://img.shields.io/badge/vendors-8-orange.svg)]()
[![Tools](https://img.shields.io/badge/tools-38-purple.svg)]()

**"画图勾选 → 一键生成多厂商命令"** —— 把繁琐的命令行工作图形化，降低多厂商配置门槛。

> 🎯 目标用户：网络运维工程师、网络初学者（HCIA/HCIP/CCNA/CCNP）、网络专业学生

🌐 **在线演示**: [待部署] | 📖 **完整文档**: [项目规划.md](项目规划.md)

---

## ✨ 功能特性

### 🔧 核心功能

- **8 厂商命令生成**：华为 / H3C / 锐捷 / 迈普 / RouterOS / Cisco / TP-LINK / Juniper，覆盖基础配置/VLAN/路由/安全/接口/QoS/WAN/DHCP/NAT/ACL
- **IPv6 全覆盖**：8 厂商 IPv6 寻址（EUI-64/RA 通告/静态路由）
- **安全增强**：IPSec VPN / 802.1X / DAI / IP Source Guard / 风暴控制 / 端口隔离 / Private VLAN
- **路由增强**：BFD / PBR 策略路由 / BGP 路由策略 / MPLS LDP / VXLAN / GRE 隧道
- **拓扑可视化编辑器**：22 种设备图标 + 4 大分组 + MiniMap + 撤销重做 + 连线标签 + 导出 PNG
- **SSH 配置下发**：生成命令后直接 paramiko 推送到设备
- **图形化参数配置**：通过表单勾选生成配置，无需记忆复杂命令
- **中文命令注释**：每条命令附带详细中文注释，降低学习门槛
- **网络诊断看板**：Ping SSE 实时流 + Traceroute 逐跳追踪 + ECharts 可视化
- **30 套配置模板**：园区核心/接入/路由器/防火墙/RouterOS 开局预设

### 🛠 网络工具集（38 个）

| 分类 | 工具 |
|---|---|
| **子网** (8) | 子网计算器 / VLSM划分 / CIDR汇总 / 通配符掩码 / CIDR对比 / IP格式转换 / 随机IP / 子网掩码速查表 |
| **IPv6** (3) | EUI-64计算器 / IPv6压缩展开 / IPv6类型检测 |
| **诊断** (4) | 端口扫描 / DNS查询 / 端口服务速查 / iPerf3指引 |
| **规划** (5) | PoE功率预算 / WiFi信道规划 / 带宽需求计算 / 光纤功率预算 / 接口速率对照 |
| **配置** (2) | DHCP Option 43 / VLAN端口批量生成 |
| **开发** (2) | 正则测试器 / 哈希计算 |
| **运维** (5) | SSH下发 / SNMP MIB速查 / DNS记录生成 / 配置检查清单 / Syslog解码 |
| **参考** (7) | 交换机选型 / 网络术语速查 / 默认密码速查 / 网线线序 / RIP参考 / 数据包结构 / MAC厂商 |
| **工具** (4) | 时间戳 / Base64 / JSON / Wake-on-LAN |

### 📖 命令速查库

3600+ 条命令，8 厂商，按版本过滤（VRP V5/V8、Comware V5/V7、RouterOS V6/V7）

### 🚀 技术亮点

- **Adapter 模式架构**：统一多厂商接口差异，易于扩展新厂商
- **SSE 实时流**：Ping 逐包推送 + Traceroute 逐跳推送
- **前后端分离**：FastAPI + Vue 3 + TypeScript + Element Plus
- **ECharts 可视化**：延迟波形图 / 丢包率 / 逐跳柱状图
- **30 套预设模板**：一键加载典型网络场景

---

## 🛠️ 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.10+ | 后端语言 |
| **FastAPI** | 0.110+ | Web 框架 |
| **Uvicorn** | 0.27+ | ASGI 服务器 |
| **Pydantic** | 2.6+ | 数据验证 |
| **paramiko** | 3.4+ | SSH 配置下发 |
| **dnspython** | 2.6+ | DNS 查询 |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| **Vue** | 3.5+ | 前端框架 |
| **TypeScript** | 5.7+ | 类型安全 |
| **Vite** | 6.2+ | 构建工具 |
| **Element Plus** | 2.9+ | UI 组件库 |
| **ECharts** | 5.5+ | 图表可视化 |
| **AntV X6** | 3.1+ | 拓扑图引擎 |
| **Pinia** | 2.3+ | 状态管理 |
| **Vue Router** | 4.5+ | 路由管理 |
| **Axios** | 1.7+ | HTTP 客户端 |

---

## 📦 快速开始

### 前置要求

- **Python** 3.10+
- **Node.js** 18+
- **npm** 或 **pnpm**

### 1. 克隆项目

```bash
git clone https://github.com/SionLhc/NetCmdGen.git
cd NetCmdGen
```

### 2. 后端启动

```powershell
cd api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

启动后访问：
- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health

### 3. 前端启动

```powershell
cd web
npm install
npm run dev
```

启动后访问：http://localhost:5173

---

## 📡 API 概览

| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/health` | GET | 健康检查 |
| `/api/generate/full` | POST | 生成多厂商完整配置 |
| `/api/generate/vendors` | GET | 获取厂商列表 |
| `/api/manual/{vendor}` | GET | 命令速查（按厂商+版本过滤） |
| `/api/net/ping/stream` | GET | Ping SSE 实时流 |
| `/api/net/traceroute/stream` | GET | Traceroute SSE 逐跳流 |
| `/api/net/portscan` | GET | TCP 端口扫描 |
| `/api/net/dns` | GET | DNS 多解析器查询 |
| `/api/net/ssh-exec` | POST | SSH 配置下发 |
| `/api/net/subnet` | GET | 子网计算 |
| `/api/net/split-subnet` | GET | VLSM 子网划分 |
| `/api/net/cidr-merge` | GET | CIDR 汇总 |

完整文档：启动后端后访问 **http://127.0.0.1:8000/docs** (Swagger UI)

---

## 📁 项目结构

```
NetCmdGen/
├── api/                        # 后端 FastAPI
│   ├── app/
│   │   ├── main.py            # 入口
│   │   ├── api/               # 路由层
│   │   │   ├── generate.py    # 命令生成
│   │   │   ├── manual.py      # 命令速查（8厂商）
│   │   │   ├── network_tools.py  # 网络工具（SSE流/Ping/Trace/SSH/子网）
│   │   │   ├── router.py      # 路由注册
│   │   │   └── topology.py    # 拓扑存储
│   │   ├── engine/            # 命令生成引擎
│   │   │   ├── base.py        # 统一接口
│   │   │   ├── factory.py     # 工厂模式（8厂商注册）
│   │   │   ├── adapters/      # 厂商适配器（8个）
│   │   │   └── vendors/       # 厂商生成器
│   │   │       ├── huawei/    # 华为（6模块）
│   │   │       ├── h3c.py     # H3C
│   │   │       ├── ruijie.py  # 锐捷
│   │   │       ├── maipu.py   # 迈普
│   │   │       ├── routeros/  # RouterOS
│   │   │       ├── cisco.py   # Cisco IOS
│   │   │       ├── tplink.py  # TP-LINK
│   │   │       └── juniper.py # Juniper Junos
│   │   └── data/              # 静态数据
│   │       ├── manual/        # 8厂商命令速查（3600+条）
│   │       └── cases.py       # 30套配置模板
│   ├── requirements.txt
│   └── LICENSE-NetOps-toolkit
│
├── web/                       # 前端 Vue 3
│   ├── src/
│   │   ├── views/
│   │   │   ├── Home.vue          # 首页
│   │   │   ├── Generator.vue     # 命令工作台
│   │   │   ├── TopologyEditor.vue # 拓扑编辑器
│   │   │   ├── Diagnostics.vue   # 网络诊断看板（06-03新增）
│   │   │   ├── Tools.vue         # 网络工具（38个）
│   │   │   └── Manual.vue        # 命令速查
│   │   ├── components/
│   │   │   ├── diagnostics/      # 诊断组件（PingProbe/TraceMap）
│   │   │   ├── generator/        # 表单组件（15个）
│   │   │   └── topology/         # 拓扑组件
│   │   ├── stores/               # Pinia 状态
│   │   ├── api/                  # API 封装
│   │   └── router/               # 路由配置
│   ├── public/icons/             # 设备图标（SVG）
│   └── package.json
│
├── scripts/                   # 辅助脚本
│   └── sync-docs.ps1          # 文档同步自动化
├── docs/                      # 技术文档
├── 项目规划.md                 # 完整规划文档
└── README.md
```

---

## 🎯 厂商完成度

| 厂商 | Basic | VLAN | Routing | Security | Interface | QoS | IPv6 | WAN+NAT | 完成度 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **华为** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| **H3C** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| **锐捷** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| **迈普** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| **RouterOS** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% |
| **Cisco** | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | 100% |
| **TP-LINK** | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | 100% |
| **Juniper** | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | 100% |

> 增强特性：IPSec VPN（华为/H3C/Cisco）/ BFD+PBR+BGP策略+MPLS+VXLAN+GRE（华为/Cisco）/ 802.1X+DAI+IP Source Guard+风暴控制（华为/H3C/Cisco）

---

## 🚧 路线图

### ✅ v1.0 已完成 (06-03)
- 8 厂商命令引擎 + IPv6 全覆盖
- 38 网络工具 + 网络诊断看板（SSE实时流）
- 安全/路由全特性增强
- SSH 配置下发 + 侧边栏重构
- 30 套配置模板 + 3600+ 命令速查

### 🔲 v2.0 规划中
- 信创 6 厂商（烽火/迪普/浪潮/博达/瑞斯康达/神州数码）
- 内置 SSH 终端（xterm.js）
- 文档报告生成（PDF/Word）
- DevOps 集成（Ansible/Terraform 导出）

### 🔲 v3.0 远期
- 仿真教学（OSPF/STP 状态机可视化）
- AI 审计（LLM 配置风险分析）
- 多人协作 + 离线桌面版

---

## 🤝 贡献指南

### 新增厂商适配器

1. 在 `api/app/engine/vendors/` 下创建厂商 Generator
2. 在 `api/app/engine/adapters/` 下创建 Adapter
3. 在 `api/app/engine/factory.py` 中注册
4. 添加命令速查数据到 `api/app/data/manual/`

### 开发流程

```bash
git checkout -b feature/xxx
# ... 开发 ...
git commit -m 'feat: xxx'
git push origin feature/xxx
# 提交 PR
```

---

## 📄 许可证

MIT License

---

> **免责声明**：本项目仅供学习研究使用，生产环境使用请自行验证命令准确性。
