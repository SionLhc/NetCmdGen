# NetCmdGen - 多厂商网络配置命令生成器

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.5+-brightgreen.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110+-teal.svg)](https://fastapi.tiangolo.com/)

**"画图勾选 → 一键生成多厂商命令"** —— 把繁琐的命令行工作图形化，降低多厂商配置门槛。

> 🎯 目标用户：网络运维工程师、网络初学者（HCIA/HCIP/CCNA/CCNP）、网络专业学生

🌐 **在线演示**: [待部署] | 📖 **完整文档**: [项目规划.md](项目规划.md)

---

## ✨ 功能特性

### 🔧 核心功能

- **多厂商命令生成**：支持华为、H3C、锐捷、迈普 4 大国产厂商，覆盖基础配置、VLAN、路由、安全、接口、QoS 等场景
- **拓扑可视化编辑器**：基于 AntV X6 的设备拖拽画图，支持路由器、交换机、防火墙、服务器、PC 等设备
- **图形化参数配置**：通过表单勾选生成配置，无需记忆复杂命令
- **中文命令解析**：每条命令附带详细中文注释，降低学习门槛
- **网络工具箱**：子网计算器、Ping、Traceroute、端口扫描、DNS/Whois 查询、MAC 地址查询、IP 转换等 9 大工具
- **命令速查库**：1000+ 条网络命令快速检索，支持多厂商对比

### 🚀 技术亮点

- **Adapter 模式架构**：统一多厂商接口差异，易于扩展新厂商
- **前后端分离**：FastAPI + Vue 3 + TypeScript，现代化技术栈
- **开源核心复用**：基于 [NetOps-toolkit](https://github.com/) (MIT License) 的命令生成内核
- **参数验证体系**：9 类网络参数校验（IP/掩码/VLAN ID/接口名/MAC 等）

---

## 🛠️ 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.10+ | 后端语言 |
| **FastAPI** | 0.110+ | Web 框架 |
| **Uvicorn** | 0.27+ | ASGI 服务器 |
| **Pydantic** | 2.6+ | 数据验证 |
| **python-whois** | 0.9.4+ | Whois 查询 |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| **Vue** | 3.5+ | 前端框架 |
| **TypeScript** | 5.7+ | 类型安全 |
| **Vite** | 6.2+ | 构建工具 |
| **Element Plus** | 2.9+ | UI 组件库 |
| **AntV X6** | 3.1+ | 拓扑图引擎 |
| **Pinia** | 2.3+ | 状态管理 |
| **Vue Router** | 4.5+ | 路由管理 |
| **Axios** | 1.7+ | HTTP 客户端 |
| **Monaco Editor** | 0.55+ | 代码编辑器 |

---

## 📦 快速开始

### 前置要求

- **Python** 3.10 或更高版本
- **Node.js** 18 或更高版本
- **npm** 或 **pnpm** 包管理器

### 1. 克隆项目

```bash
git clone https://github.com/SionLhc/NetCmdGen.git
cd NetCmdGen
```

### 2. 后端启动

```powershell
# 进入后端目录
cd api

# 安装 Python 依赖
pip install -r requirements.txt

# 启动开发服务器（热重载）
uvicorn app.main:app --reload --port 8000
```

启动成功后访问：
- 📊 API 文档：http://127.0.0.1:8000/docs
- ❤️ 健康检查：http://127.0.0.1:8000/api/health
- 🔧 子网计算示例：http://127.0.0.1:8000/api/tools/subnet?ip=192.168.1.10&mask=255.255.255.0

### 3. 前端启动

```powershell
# 进入前端目录
cd web

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

启动成功后访问：http://localhost:5173

### 4. 完整工作流

```
1. 打开前端页面 http://localhost:5173
2. 在拓扑编辑器中拖拽设备（交换机、路由器等）
3. 点击设备配置参数（VLAN、接口、路由等）
4. 选择厂商（华为/H3C/锐捷/迈普）
5. 一键生成配置命令并复制
```

---

## 📡 API 接口示例

### 1. 健康检查

```bash
GET /api/health
```

**响应：**
```json
{
  "status": "ok",
  "service": "netcmdgen-api"
}
```

### 2. 生成配置命令

```bash
POST /api/generate
Content-Type: application/json

{
  "vendor": "h3c",
  "feature": "vlan",
  "params": {
    "vlan_id": 10,
    "vlan_name": "Sales",
    "ports": ["GigabitEthernet0/0/1", "GigabitEthernet0/0/2"]
  }
}
```

**响应：**
```
# VLAN 配置 - H3C
# 生成时间: 2026-05-30 10:30:00

vlan 10
 description Sales
#
interface GigabitEthernet0/0/1
 port link-type access
 port access vlan 10
#
interface GigabitEthernet0/0/2
 port link-type access
 port access vlan 10
#
```

### 3. 子网计算

```bash
GET /api/tools/subnet?ip=192.168.1.0&mask=255.255.255.0
```

**响应：**
```json
{
  "network": "192.168.1.0/24",
  "broadcast": "192.168.1.255",
  "subnet_mask": "255.255.255.0",
  "wildcard_mask": "0.0.0.255",
  "first_host": "192.168.1.1",
  "last_host": "192.168.1.254",
  "total_hosts": 254,
  "subnets": [
    {
      "subnet": "192.168.1.0/25",
      "range": "192.168.1.1 - 192.168.1.126",
      "hosts": 126
    },
    {
      "subnet": "192.168.1.128/25",
      "range": "192.168.1.129 - 192.168.1.254",
      "hosts": 126
    }
  ]
}
```

### 4. Ping 测试

```bash
POST /api/tools/ping
Content-Type: application/json

{
  "target": "8.8.8.8",
  "count": 4
}
```

### 5. 命令速查

```bash
GET /api/manual/huawei?vlan
```

返回华为厂商所有与 VLAN 相关的命令及说明。

### 完整 API 文档

启动后端后访问 **http://127.0.0.1:8000/docs** 查看完整的 Swagger UI 交互式文档。

---

## 📁 项目结构

```
NetCmdGen/
├── api/                        # 后端 FastAPI 项目
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── api/               # 路由层
│   │   │   ├── generate.py    # 命令生成接口
│   │   │   ├── manual.py      # 命令速查接口
│   │   │   ├── tools_extra.py # 网络工具接口
│   │   │   └── tools_subnet.py# 子网计算接口
│   │   ├── core/              # 核心工具
│   │   │   └── validator.py   # 参数验证器（9 类校验）
│   │   ├── tools/             # 网络工具实现
│   │   │   ├── subnet.py      # 子网计算器
│   │   │   ├── ping.py        # Ping 工具
│   │   │   ├── trace.py       # Traceroute 工具
│   │   │   ├── portscan.py    # 端口扫描器
│   │   │   └── dns.py         # DNS/Whois 查询
│   │   ├── data/              # 静态数据
│   │   │   ├── manual/        # 命令速查库（4 厂商）
│   │   │   │   ├── huawei.py
│   │   │   │   ├── h3c.py
│   │   │   │   ├── ruijie.py
│   │   │   │   └── maipu.py
│   │   │   └── cases.py       # 配置案例库
│   │   └── engine/            # 命令生成引擎
│   │       ├── base.py        # 统一接口抽象
│   │       ├── factory.py     # 工厂模式
│   │       ├── adapters/      # 厂商适配器
│   │       │   ├── huawei.py
│   │       │   ├── h3c.py
│   │       │   ├── ruijie.py
│   │       │   └── maipu.py
│   │       └── vendors/       # 厂商原始 Generator
│   │           ├── huawei/    # 华为（6 个模块）
│   │           ├── h3c.py
│   │           ├── ruijie.py
│   │           └── maipu.py
│   ├── tests/                 # 测试用例
│   ├── requirements.txt       # Python 依赖
│   └── LICENSE-NetOps-toolkit # 开源项目许可证
│
├── web/                       # 前端 Vue 3 项目
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   │   ├── TopologyEditor.vue  # 拓扑编辑器
│   │   │   ├── Generator.vue       # 命令生成器
│   │   │   ├── Manual.vue          # 命令速查
│   │   │   └── Tools.vue           # 网络工具
│   │   ├── components/        # 通用组件
│   │   │   └── topology/      # 拓扑相关组件
│   │   ├── stores/            # Pinia 状态管理
│   │   │   ├── topology.ts    # 拓扑状态
│   │   │   └── vendor.ts      # 厂商配置
│   │   ├── api/               # API 请求封装
│   │   ├── router/            # 路由配置
│   │   └── utils/             # 工具函数
│   ├── public/icons/          # 设备图标（SVG）
│   ├── package.json
│   └── vite.config.ts
│
├── opensource/                # 开源项目引用
│   └── NetOps-toolkit/        # NetOps-toolkit（MIT 协议）
│
├── docs/                      # 项目文档
│   ├── NetOps-toolkit复用方案.md
│   └── 开源项目复用分析.md
│
├── scripts/                   # 辅助脚本
│   ├── clone-opensource.ps1   # 克隆开源项目
│   └── sync-from-netops.ps1   # 同步代码到 api/
│
├── templates/                 # 命令模板（待扩展）
├── .gitignore
├── 项目规划.md                # 完整项目规划文档
└── README.md                  # 本文件
```

---

## 🎯 已实现功能

### ✅ 命令生成引擎
- [x] 华为厂商（基础/VLAN/路由/安全/接口/QoS）
- [x] H3C 厂商（基础/VLAN/路由/安全/接口/服务）
- [x] 锐捷厂商（基础/VLAN/路由/安全）
- [x] 迈普厂商（基础/VLAN/路由/安全）
- [x] Adapter 统一接口层
- [x] 工厂模式动态加载

### ✅ 网络工具集
- [x] 子网计算器（支持子网划分）
- [x] Ping 测试
- [x] Traceroute 路由跟踪
- [x] 端口扫描器
- [x] DNS 查询 + Whois 查询
- [x] MAC 地址查询
- [x] IP 地址转换
- [x] 密码生成器
- [x] 编码转换工具

### ✅ 命令速查库
- [x] 华为 1000+ 条命令
- [x] H3C 600+ 条命令
- [x] 锐捷 700+ 条命令
- [x] 迈普 600+ 条命令

### ✅ 前端功能
- [x] 拓扑编辑器（AntV X6）
- [x] 设备拖拽（8 种设备类型）
- [x] 设备连线
- [x] 属性面板配置
- [x] 命令输出展示
- [x] 厂商选择切换
- [x] 网络工具页面
- [x] 命令速查页面

---

## 🚧 待开发功能

### 🔲 命令引擎扩展
- [ ] 思科（Cisco）厂商支持
- [ ] Juniper 厂商支持
- [ ] TP-LINK、烽火、海康等 9 个厂商
- [ ] Jinja2 模板引擎重构
- [ ] VRRP + MSTP 多设备协同
- [ ] OSPF 多设备配置生成

### 🔲 拓扑编辑器增强
- [ ] 自动布局算法
- [ ] 拓扑导入/导出（JSON/PNG）
- [ ] 设备配置模板
- [ ] 拓扑版本管理
- [ ] 多人协作编辑

### 🔲 AI 能力（差异化亮点）
- [ ] 自然语言 → 配置命令
- [ ] 命令解析与风险提示
- [ ] 配置审计与优化建议
- [ ] 故障排查辅助

---

## ⚠️ 已知问题

### 1. 网络工具安全风险
- **问题**：端口扫描器可能被滥用为扫描代理
- **状态**：待解决
- **计划**：添加目标白名单、限频机制、登录鉴权

### 2. Windows/Linux 兼容性
- **问题**：Ping/Traceroute 使用 subprocess 调用系统命令，Docker 部署时需安装额外工具
- **状态**：部分解决
- **计划**：Dockerfile 中添加 `iputils-ping` 和 `traceroute`

### 3. 命令准确性验证
- **问题**：部分厂商命令在不同 OS 版本可能有差异
- **状态**：持续改进
- **计划**：建立真机/模拟器回归测试流程

### 4. 前端跨域问题
- **问题**：开发环境已配置 CORS，生产环境需 Nginx 反向代理
- **状态**：待部署时解决

### 5. X6 拓扑交互优化
- [x] ✅ 设备图标渲染问题已修复
- [x] ✅ 连接桩拖拽交互已修复
- [ ] 端口定位百分比支持待优化

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

### 新增厂商适配器

参考 `docs/NetOps-toolkit复用方案.md` 中的 Adapter 设计模式：

1. 在 `api/app/engine/vendors/` 下创建厂商 Generator
2. 在 `api/app/engine/adapters/` 下创建 Adapter 封装
3. 在 `api/app/engine/factory.py` 中注册新厂商
4. 添加命令速查数据到 `api/app/data/manual/`

---

## 📄 许可证

本项目采用 **MIT License**。

### 第三方开源项目致谢

本项目核心命令生成内核、网络工具、命令速查数据复用自  
[**NetOps-toolkit**](https://github.com/) (MIT License, Copyright © 2026 Flocks NetOps Toolkit)

完整许可证见 [`LICENSE-NetOps-toolkit`](api/LICENSE-NetOps-toolkit)

---

## 📞 联系方式

- **GitHub Issues**: [提交问题与建议](https://github.com/SionLhc/NetCmdGen/issues)
- **项目规划**: [项目规划.md](项目规划.md)
- **技术文档**: [docs/](docs/)

---

## 🌟 Star History

如果这个项目对你有帮助，请给它一个 ⭐️ Star！

---

> **免责声明**：本项目仅供学习研究使用，生产环境使用请自行验证命令准确性。
