# 故障排查指南

本文档帮助你解决 SAAS 平台常见的构建和运行问题。

## 快速诊断

### 1. 检查 Python 环境

```bash
# 检查 Python 版本（需要 3.11+）
python --version

# 检查是否在虚拟环境中
echo $VIRTUAL_ENV
```

### 2. 测试基础模块

```bash
# 运行基础测试
cd /Users/town/Project/SAAS
python scripts/test-basic.py
```

## 常见问题

### 问题 1: 模块导入错误

**错误信息:**
```
ModuleNotFoundError: No module named 'shared'
ImportError: cannot import name 'xxx'
```

**解决方法:**

1. 确保所有 `__init__.py` 文件都已创建：
```bash
# 检查必需的 __init__.py 文件
ls backend/shared/__init__.py
ls backend/shared/models/__init__.py
ls backend/shared/schemas/__init__.py
ls backend/shared/utils/__init__.py
```

2. 使用正确的启动方式：
```bash
# 方式 1: 使用 run.py 脚本
cd backend/registry
python run.py

# 方式 2: 使用 uvicorn
cd backend
python -m uvicorn registry.main:app --port 8001
```

### 问题 2: Pydantic 版本问题

**错误信息:**
```
TypeError: BaseModel.dict() got an unexpected keyword argument
ValueError: "Config" object has no field "orm_mode"
```

**解决方法:**

我们使用的是 Pydantic v2，配置应该是：
```python
class Config:
    from_attributes = True  # Pydantic v2
    # 而不是 orm_mode = True  # Pydantic v1
```

确保使用正确的依赖版本：
```bash
cd backend
uv pip install pydantic==2.5.3
```

### 问题 3: 数据库连接失败

**错误信息:**
```
sqlalchemy.exc.OperationalError: could not connect to server
psycopg2.OperationalError: connection refused
```

**解决方法:**

1. 启动数据库：
```bash
# 使用 Docker
docker-compose up -d postgres redis

# 或者启动本地 PostgreSQL
brew services start postgresql
```

2. 检查数据库配置：
```bash
# 查看 .env 文件
cat backend/.env

# 测试连接
psql -U saas_user -d saas_platform -c "SELECT 1"
```

3. 创建数据库（如果不存在）：
```bash
psql -U postgres <<EOF
CREATE DATABASE saas_platform;
CREATE USER saas_user WITH PASSWORD 'saas_password';
GRANT ALL PRIVILEGES ON DATABASE saas_platform TO saas_user;
EOF
```

### 问题 4: Docker 构建失败

**错误信息:**
```
Error response from daemon
failed to solve with frontend dockerfile
```

**解决方法:**

1. 检查 Dockerfile 路径：
```bash
ls docker/Dockerfile.backend
ls docker/Dockerfile.plugin
```

2. 清理 Docker 缓存：
```bash
docker system prune -a
docker-compose build --no-cache
```

3. 单独构建服务：
```bash
# 只构建注册中心
docker-compose build registry

# 测试运行
docker-compose up registry
```

### 问题 5: 端口被占用

**错误信息:**
```
OSError: [Errno 48] Address already in use
```

**解决方法:**

1. 查找占用端口的进程：
```bash
# macOS/Linux
lsof -i :8000
lsof -i :8001
lsof -i :8002

# 杀死进程
kill -9 <PID>
```

2. 修改端口配置：

编辑 `docker-compose.yml` 或各服务的启动脚本，使用不同的端口。

### 问题 6: 服务注册失败

**错误信息:**
```
✗ 连接注册中心失败: Connection refused
```

**解决方法:**

1. 确保注册中心已启动：
```bash
curl http://localhost:8001
```

2. 检查注册中心日志：
```bash
# Docker 方式
docker-compose logs registry

# 本地方式
tail -f logs/registry.log
```

3. 验证服务配置：
```python
# 确保 REGISTRY_URL 正确
REGISTRY_URL = "http://localhost:8001"
```

### 问题 7: 依赖安装失败

**错误信息:**
```
ERROR: Could not find a version that satisfies the requirement
```

**解决方法:**

1. 更新 pip 和 uv：
```bash
pip install --upgrade pip
pip install --upgrade uv
```

2. 使用 pip 安装（如果 uv 有问题）：
```bash
cd backend
pip install -r requirements.txt
```

3. 单独安装有问题的包：
```bash
# 如果 psycopg2-binary 有问题
pip install psycopg2-binary==2.9.9

# 如果 cryptography 有问题
pip install python-jose[cryptography]
```

### 问题 8: Bcrypt 版本兼容性问题

**错误信息:**
```
AttributeError: module 'bcrypt' has no attribute '__about__'
ValueError: password cannot be longer than 72 bytes
```

**原因:**
bcrypt 5.0.0+ 与 passlib 1.7.4 不兼容。

**解决方法:**

1. 降级 bcrypt 到 4.1.3：
```bash
cd backend
uv pip install bcrypt==4.1.3
# 或
pip install bcrypt==4.1.3
```

2. 验证安装：
```bash
python -c "import bcrypt; print(bcrypt.__version__)"
# 应该显示 4.1.3
```

### 问题 9: SQLAlchemy metadata 字段冲突

**错误信息:**
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API
```

**原因:**
SQLAlchemy 的 Base 类有内置的 `metadata` 属性。

**解决方法:**

在模型中使用 `service_metadata` 作为列名：
```python
# 正确的方式
service_metadata = Column("metadata", JSON, default=dict)

# 错误的方式（会导致冲突）
metadata = Column(JSON, default=dict)
```

### 问题 10: SOCKS 代理错误

**错误信息:**
```
ImportError: Using SOCKS proxy, but the 'socksio' package is not installed
httpx.ConnectError: [Errno 61] Connection refused
```

**原因:**
系统环境变量中设置了代理，影响了服务间通信。

**解决方法:**

1. 临时清除代理：
```bash
unset ALL_PROXY
unset all_proxy
unset HTTPS_PROXY
unset https_proxy
unset HTTP_PROXY
unset http_proxy
```

2. 在启动脚本中清除代理：
```bash
# 启动服务前
cd examples/plugins/demo-service
unset ALL_PROXY && unset all_proxy && unset HTTPS_PROXY && unset https_proxy
python main.py
```

3. 或在代码中配置：
```python
# 在 httpx 客户端中禁用代理
async with httpx.AsyncClient(proxies=None) as client:
    response = await client.post(url, json=data)
```

### 问题 11: PostgreSQL 角色不存在

**错误信息:**
```
psycopg2.OperationalError: FATAL: role "saas_user" does not exist
```

**原因:**
- 本地 PostgreSQL 正在运行，但没有创建所需的用户
- Docker 和本地 PostgreSQL 端口冲突

**解决方法:**

1. 停止本地 PostgreSQL：
```bash
# macOS
brew services stop postgresql@14

# Linux
sudo systemctl stop postgresql
```

2. 使用 Docker PostgreSQL：
```bash
docker-compose down -v
docker-compose up -d postgres redis
```

3. 或在本地 PostgreSQL 中创建用户：
```bash
psql -U postgres <<EOF
CREATE DATABASE saas_platform;
CREATE USER saas_user WITH PASSWORD 'saas_password';
GRANT ALL PRIVILEGES ON DATABASE saas_platform TO saas_user;
\c saas_platform
GRANT ALL ON SCHEMA public TO saas_user;
EOF
```

### 问题 12: email-validator 缺失

**错误信息:**
```
ModuleNotFoundError: No module named 'email_validator'
```

**原因:**
Pydantic 的 `EmailStr` 类型需要 email-validator 包。

**解决方法:**

```bash
cd backend
uv pip install email-validator==2.3.0
```

### 问题 13: 前端 CORS 错误

**错误信息:**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**原因:**
- 后端 CORS 配置不正确
- 前端直接访问后端而不是通过代理

**解决方法:**

1. 检查前端配置（vite.config.js）：
```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

2. 使用 `/api/` 前缀访问：
```javascript
// 正确
axios.get('/api/demo-service/items')

// 错误（会导致 CORS 错误）
axios.get('http://localhost:8000/api/demo-service/items')
```

3. 检查后端 CORS 配置：
```python
# backend/shared/config.py
CORS_ORIGINS = "http://localhost:5173,http://localhost:3000"
```

## 分步测试

### 步骤 1: 测试基础导入

```bash
cd backend
python -c "from shared.config import get_settings; print('OK')"
python -c "from shared.models import User; print('OK')"
python -c "from shared.schemas.service import ServiceRegister; print('OK')"
```

### 步骤 2: 测试单个服务

```bash
# 测试注册中心
cd backend/registry
python run.py

# 在另一个终端测试
curl http://localhost:8001
```

### 步骤 3: 测试完整流程

```bash
# 1. 启动数据库
docker-compose up -d postgres redis

# 2. 启动服务（3个终端）
cd backend/registry && python run.py
cd backend/gateway && python run.py
cd backend/core && python run.py

# 3. 测试
curl http://localhost:8001/api/registry/services
```

## 日志查看

### Docker 方式

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务
docker-compose logs -f registry
docker-compose logs -f gateway
docker-compose logs -f core

# 查看最近 100 行
docker-compose logs --tail=100 registry
```

### 本地方式

```bash
# 查看日志文件
tail -f logs/registry.log
tail -f logs/gateway.log
tail -f logs/core.log

# 查看所有日志
tail -f logs/*.log
```

## 环境检查清单

- [ ] Python 3.11+ 已安装
- [ ] 虚拟环境已激活
- [ ] 依赖已安装 (`pip list | grep fastapi`)
- [ ] PostgreSQL 正在运行
- [ ] Redis 正在运行（可选）
- [ ] .env 文件已配置
- [ ] 端口 8000-8003 未被占用
- [ ] 所有 __init__.py 文件已创建

## 获取帮助

如果问题仍未解决：

1. **查看详细错误信息**
   ```bash
   # 启动时添加详细日志
   python run.py --log-level debug
   ```

2. **检查依赖版本**
   ```bash
   pip list | grep -E "fastapi|pydantic|sqlalchemy"
   ```

3. **重新安装**
   ```bash
   # 删除虚拟环境
   rm -rf backend/.venv

   # 重新创建
   cd backend
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

4. **使用 Docker（最简单）**
   ```bash
   docker-compose down -v
   docker-compose up --build
   ```

## 性能优化建议

如果服务运行缓慢：

1. **增加数据库连接池**
   ```python
   # backend/shared/database.py
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,  # 增加
       max_overflow=40,  # 增加
   )
   ```

2. **启用 Redis 缓存**
   ```python
   # 在网关中缓存服务信息
   ```

3. **调整 workers 数量**
   ```bash
   uvicorn main:app --workers 4
   ```

## 还原到初始状态

如果需要完全重置：

```bash
# 停止所有服务
docker-compose down -v

# 删除所有数据
rm -rf logs/
rm -rf backend/.venv/

# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 重新开始
docker-compose up --build
```
