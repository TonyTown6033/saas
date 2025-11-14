# 快速开始指南

本指南将帮助你快速启动微服务热插拔 SAAS 平台。

## 前置条件

### 使用 Docker（推荐）
- Docker 20.10+
- Docker Compose 2.0+

### 本地开发
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Node.js 18+
- pyenv
- uv (Python 包管理工具)

## 方式一：使用 Docker（推荐）

### 1. 启动所有服务

```bash
# 克隆或进入项目目录
cd SAAS

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 2. 服务地址

启动后，你可以访问：

- **API 网关**: http://localhost:8000
- **服务注册中心**: http://localhost:8001
- **核心服务**: http://localhost:8002
- **演示插件服务**: http://localhost:8003

### 3. 测试服务

```bash
# 检查网关状态
curl http://localhost:8000

# 查看注册的服务列表
curl http://localhost:8001/api/registry/services

# 通过网关访问演示服务
curl http://localhost:8000/api/demo-service/items
```

### 4. 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

## 方式二：本地开发

### 1. 设置 Python 环境

```bash
# 安装 Python 3.11（如果未安装）
pyenv install 3.11

# 设置本地 Python 版本
pyenv local 3.11

# 安装 uv（如果未安装）
pip install uv

# 进入后端目录
cd backend

# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -r requirements.txt
```

### 2. 启动数据库

```bash
# 启动 PostgreSQL 和 Redis
docker-compose up -d postgres redis

# 或者使用本地安装的数据库
# 确保 PostgreSQL 运行在 5432 端口
# 确保 Redis 运行在 6379 端口

# 创建数据库
psql -U postgres -c "CREATE DATABASE saas_platform;"
psql -U postgres -c "CREATE USER saas_user WITH PASSWORD 'saas_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE saas_platform TO saas_user;"
```

### 3. 配置环境变量

```bash
# 复制环境变量示例文件
cp backend/.env.example backend/.env

# 编辑 .env 文件，根据需要修改配置
vim backend/.env
```

### 4. 启动后端服务

打开 3 个终端窗口，分别启动：

**终端 1 - 服务注册中心:**
```bash
cd backend
source .venv/bin/activate
cd registry
python main.py
# 运行在 http://localhost:8001
```

**终端 2 - API 网关:**
```bash
cd backend
source .venv/bin/activate
cd gateway
python main.py
# 运行在 http://localhost:8000
```

**终端 3 - 核心服务:**
```bash
cd backend
source .venv/bin/activate
cd core
python main.py
# 运行在 http://localhost:8002
```

### 5. 启动演示插件服务（可选）

**终端 4 - 演示服务:**
```bash
cd examples/plugins/demo-service
python main.py
# 运行在 http://localhost:8003
# 自动注册到服务注册中心
```

### 6. 测试系统

```bash
# 1. 检查服务注册中心
curl http://localhost:8001

# 2. 查看已注册的服务
curl http://localhost:8001/api/registry/services

# 3. 测试核心服务 - 注册用户
curl -X POST http://localhost:8002/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin12345",
    "role": "super_admin"
  }'

# 4. 测试核心服务 - 登录
curl -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin12345"
  }'

# 5. 通过网关访问演示服务
curl http://localhost:8000/api/demo-service/items

# 6. 通过网关创建项目
curl -X POST http://localhost:8000/api/demo-service/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试项目",
    "description": "这是一个测试",
    "price": 99.99
  }'
```

## API 文档

每个服务都提供了自动生成的 API 文档：

- 服务注册中心: http://localhost:8001/docs
- API 网关: http://localhost:8000/docs
- 核心服务: http://localhost:8002/docs
- 演示服务: http://localhost:8003/docs

## 开发自己的插件服务

查看 `examples/plugins/demo-service/main.py` 了解如何创建新的插件服务。

基本步骤：

1. 创建 FastAPI 应用
2. 定义服务配置（名称、端点等）
3. 在启动时注册到服务注册中心
4. 定期发送心跳保持活跃
5. 在关闭时注销服务

## 常见问题

### 数据库连接错误

确保 PostgreSQL 正在运行，并且 `.env` 文件中的数据库配置正确。

### 服务注册失败

确保服务注册中心 (Registry) 已经启动并运行在正确的端口。

### 端口被占用

检查端口是否被其他程序占用，可以在 `docker-compose.yml` 或服务配置中修改端口。

## 下一步

- 查看 [插件开发指南](./PLUGIN_DEVELOPMENT.md)
- 阅读 [架构设计文档](./ARCHITECTURE.md)
- 了解 [API 使用指南](./API_GUIDE.md)
