# 开始使用

恭喜！你已经拥有一个功能完整的微服务热插拔 SAAS 平台。

## 项目已完成的功能

### ✅ 核心架构
- [x] 服务注册中心 - 管理所有微服务的注册和发现
- [x] API 网关 - 统一入口和动态路由
- [x] 核心服务 - 用户、租户、认证管理
- [x] 热插拔机制 - 支持动态添加和移除微服务

### ✅ 认证和权限
- [x] JWT 认证
- [x] 用户注册和登录
- [x] 多租户系统
- [x] 角色权限控制（RBAC）
- [x] API 密钥管理

### ✅ 开发工具
- [x] Docker 容器化
- [x] 开发启动脚本
- [x] 系统测试脚本
- [x] 完整文档

### ✅ 示例插件
- [x] 演示服务（CRUD 示例）
- [x] 插件开发模板

## 快速开始（3 种方式）

### 方式 1: 使用 Docker（最简单）

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 访问服务
# - API 网关: http://localhost:8000
# - 注册中心: http://localhost:8001
# - 核心服务: http://localhost:8002
# - 演示服务: http://localhost:8003
```

### 方式 2: 使用启动脚本

```bash
# 1. 安装依赖
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 2. 启动数据库
docker-compose up -d postgres redis

# 3. 启动所有服务（包括演示服务）
cd ..
./scripts/dev-start.sh --with-demo

# 4. 测试系统
./scripts/test-system.sh

# 5. 停止服务
./scripts/dev-stop.sh
```

### 方式 3: 手动启动（最灵活）

```bash
# 终端 1 - 启动数据库
docker-compose up postgres redis

# 终端 2 - 服务注册中心
cd backend/registry
python main.py

# 终端 3 - API 网关
cd backend/gateway
python main.py

# 终端 4 - 核心服务
cd backend/core
python main.py

# 终端 5 - 演示服务（可选）
cd examples/plugins/demo-service
python main.py
```

## 测试系统

### 1. 基础健康检查

```bash
# 检查网关
curl http://localhost:8000

# 检查注册中心
curl http://localhost:8001

# 查看已注册的服务
curl http://localhost:8001/api/registry/services
```

### 2. 测试用户认证

```bash
# 注册用户
curl -X POST http://localhost:8002/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'

# 登录获取 Token
curl -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 3. 测试演示服务

```bash
# 通过网关访问演示服务
curl http://localhost:8000/api/demo-service/items

# 创建项目
curl -X POST http://localhost:8000/api/demo-service/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试项目",
    "description": "这是一个测试",
    "price": 99.99
  }'

# 获取项目列表
curl http://localhost:8000/api/demo-service/items
```

### 4. 运行自动化测试

```bash
./scripts/test-system.sh
```

## 查看 API 文档

每个服务都提供了交互式 API 文档（Swagger UI）：

- **网关**: http://localhost:8000/docs
- **注册中心**: http://localhost:8001/docs
- **核心服务**: http://localhost:8002/docs
- **演示服务**: http://localhost:8003/docs

## 开发你的第一个插件

### 1. 创建插件目录

```bash
mkdir -p my-first-plugin
cd my-first-plugin
```

### 2. 复制演示服务作为模板

```bash
cp ../examples/plugins/demo-service/main.py .
```

### 3. 修改服务配置

编辑 `main.py`，修改 `SERVICE_CONFIG`：

```python
SERVICE_CONFIG = {
    "name": "my-first-plugin",
    "display_name": "我的第一个插件",
    "version": "1.0.0",
    "port": 8100,  # 使用不同的端口
    # ... 其他配置
}
```

### 4. 实现业务逻辑

添加你自己的端点和业务逻辑。

### 5. 启动插件

```bash
python main.py
```

插件会自动注册到服务注册中心！

### 6. 通过网关访问

```bash
curl http://localhost:8000/api/my-first-plugin/your-endpoint
```

详细的插件开发指南请查看：[docs/PLUGIN_DEVELOPMENT.md](./docs/PLUGIN_DEVELOPMENT.md)

## 项目结构说明

```
SAAS/
├── backend/                    # 后端服务
│   ├── gateway/               # API 网关
│   │   └── main.py           # 网关主程序
│   ├── registry/              # 服务注册中心
│   │   └── main.py           # 注册中心主程序
│   ├── core/                  # 核心服务
│   │   └── main.py           # 核心服务主程序
│   ├── shared/                # 共享代码
│   │   ├── models/           # 数据模型
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── utils/            # 工具函数
│   │   ├── config.py         # 配置
│   │   ├── database.py       # 数据库连接
│   │   └── dependencies.py   # FastAPI 依赖
│   ├── requirements.txt       # Python 依赖
│   └── .env.example          # 环境变量示例
│
├── frontend/                  # 前端（待开发）
│   └── admin/                # 管理后台
│
├── docker/                    # Docker 配置
│   ├── Dockerfile.backend    # 后端 Dockerfile
│   └── Dockerfile.plugin     # 插件 Dockerfile
│
├── docs/                      # 文档
│   ├── QUICKSTART.md         # 快速开始
│   ├── PLUGIN_DEVELOPMENT.md # 插件开发指南
│   └── ARCHITECTURE.md       # 架构文档
│
├── examples/                  # 示例
│   └── plugins/              # 插件示例
│       └── demo-service/     # 演示服务
│
├── scripts/                   # 脚本
│   ├── dev-start.sh          # 启动脚本
│   ├── dev-stop.sh           # 停止脚本
│   └── test-system.sh        # 测试脚本
│
├── docker-compose.yml         # Docker Compose 配置
├── README.md                  # 项目说明
└── GETTING_STARTED.md        # 本文件
```

## 核心概念

### 服务注册与发现
1. 微服务启动时向注册中心注册
2. 注册中心维护所有服务的信息
3. 网关从注册中心获取服务列表
4. 请求通过网关路由到具体服务

### 热插拔机制
- 服务可以在运行时动态添加
- 服务可以在运行时动态移除
- 无需重启网关或其他服务
- 通过心跳机制自动监控服务健康

### 多租户隔离
- 每个租户有独立的数据空间
- 租户可以启用不同的服务
- 用户归属于特定租户
- 基于租户的权限控制

## 常见问题

### 端口被占用？
修改 `docker-compose.yml` 或服务配置中的端口号。

### 数据库连接失败？
确保 PostgreSQL 正在运行，检查 `.env` 文件中的数据库配置。

### 服务注册失败？
确保注册中心已启动并运行在正确的端口（默认 8001）。

### 如何查看日志？
- Docker 方式: `docker-compose logs -f [service-name]`
- 脚本方式: `tail -f logs/[service-name].log`

## 下一步

- [ ] 阅读[架构文档](./docs/ARCHITECTURE.md)了解系统设计
- [ ] 学习[插件开发指南](./docs/PLUGIN_DEVELOPMENT.md)创建自定义服务
- [ ] 开发前端管理界面
- [ ] 添加更多插件服务
- [ ] 配置生产环境部署

## 技术支持

- 查看 [README.md](./README.md) 了解项目概述
- 阅读 `docs/` 目录下的详细文档
- 查看 `examples/` 目录下的示例代码

## 贡献

欢迎贡献代码、报告问题或提出建议！

---

**祝你使用愉快！🚀**
