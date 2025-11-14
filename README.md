# 微服务热插拔 SAAS 平台

基于 Vue + FastAPI + PostgreSQL 的可扩展 SAAS 平台，支持动态服务注册和插拔。

## 架构概览

```
┌─────────────────────────────────────────────┐
│           前端 (Vue Admin)                   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         API 网关 (Gateway)                   │
│  - 路由管理                                   │
│  - 负载均衡                                   │
│  - 认证中间件                                 │
└──────┬────────────────────┬─────────────────┘
       │                    │
┌──────▼─────────┐   ┌──────▼──────────────┐
│  服务注册中心    │   │   核心服务 (Core)   │
│  (Registry)    │   │   - 租户管理         │
│  - 服务发现     │   │   - 配置中心         │
│  - 健康检查     │   │   - 用户管理         │
└────────────────┘   └─────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│        热插拔微服务 (Plugins)                 │
│  - 自定义业务服务                             │
│  - 第三方集成                                 │
│  - 动态注册/注销                              │
└─────────────────────────────────────────────┘
```

## 技术栈

### 后端
- **FastAPI**: 高性能异步 Web 框架
- **PostgreSQL**: 主数据库
- **SQLAlchemy**: ORM
- **Alembic**: 数据库迁移
- **Redis**: 缓存和会话存储
- **uvicorn**: ASGI 服务器

### 前端
- **Vue 3**: 前端框架
- **Vite**: 构建工具
- **Pinia**: 状态管理
- **Vue Router**: 路由管理
- **Element Plus**: UI 组件库

### 环境管理
- **uv**: Python 包管理
- **pyenv**: Python 版本管理

## 核心特性

### 1. 服务注册与发现
- 微服务自动注册到注册中心
- 健康检查和自动下线
- 服务元数据管理

### 2. 动态路由
- 网关根据注册中心动态配置路由
- 支持版本控制和灰度发布
- 自动负载均衡

### 3. 多租户支持
- 租户隔离
- 按租户分配服务
- 租户级配置

### 4. 认证授权
- JWT 认证
- 基于角色的访问控制 (RBAC)
- API 密钥管理

### 5. 插件开发
- 标准化服务接口
- 插件 SDK
- 示例插件模板

## 项目结构

```
SAAS/
├── backend/
│   ├── gateway/           # API 网关
│   ├── registry/          # 服务注册中心
│   ├── core/              # 核心平台服务
│   ├── auth/              # 认证授权服务
│   └── shared/            # 共享代码
│       ├── models/        # 数据模型
│       ├── utils/         # 工具函数
│       └── schemas/       # Pydantic schemas
├── frontend/
│   └── admin/             # 管理后台
├── docker/                # Docker 配置
├── docs/                  # 文档
└── examples/
    └── plugins/           # 示例插件
```

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+（前端开发需要）
- PostgreSQL 14+
- Redis 7+（可选）

### 方式 1: Docker（推荐新手）

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式 2: 本地开发

```bash
# 1. 安装依赖
cd backend
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# 2. 启动数据库（使用 Docker）
docker-compose up -d postgres redis

# 3. 启动服务（开启 3 个终端）
# 终端 1: 注册中心
cd backend/registry
python run.py

# 终端 2: 网关
cd backend/gateway
python run.py

# 终端 3: 核心服务
cd backend/core
python run.py
```

### 方式 3: 使用 Makefile

```bash
# 安装依赖
make install

# 启动开发环境
make dev-start

# 运行测试
make test

# 停止服务
make dev-stop
```

> **遇到问题？** 查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) 获取详细的故障排查指南

### 前端开发

```bash
cd frontend/admin
npm install
npm run dev
```

### Docker 部署

```bash
docker-compose up -d
```

## 开发插件

查看 `examples/plugins/` 目录获取插件开发示例。

## 文档

详细文档请查看 `docs/` 目录。
