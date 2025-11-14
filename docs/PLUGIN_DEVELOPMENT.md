# 插件开发指南

本指南将教你如何开发一个可热插拔的微服务插件。

## 概述

热插拔插件系统允许你：

- 动态添加新的业务功能
- 独立开发和部署服务
- 服务自动注册和发现
- 通过统一网关访问
- 支持服务版本管理

## 插件架构

```
┌─────────────────────────────────────┐
│   你的插件服务 (FastAPI App)         │
├─────────────────────────────────────┤
│  1. 启动时向注册中心注册             │
│  2. 定期发送心跳保持活跃             │
│  3. 实现业务逻辑端点                 │
│  4. 关闭时注销服务                   │
└─────────────────────────────────────┘
         ↓ 注册               ↑ 访问
┌─────────────────────────────────────┐
│      服务注册中心 (Registry)         │
└─────────────────────────────────────┘
         ↑                    ↓ 路由
┌─────────────────────────────────────┐
│        API 网关 (Gateway)            │
└─────────────────────────────────────┘
```

## 创建你的第一个插件

### 1. 项目结构

```
my-plugin/
├── main.py          # 主应用文件
├── requirements.txt # 依赖
├── models.py        # 数据模型（可选）
└── README.md        # 说明文档
```

### 2. 安装依赖

```bash
# 创建项目目录
mkdir my-plugin
cd my-plugin

# 创建虚拟环境（使用 uv）
uv venv
source .venv/bin/activate

# 安装基础依赖
uv pip install fastapi uvicorn httpx pydantic
```

### 3. 编写主应用（main.py）

```python
"""
我的插件服务
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
from typing import Optional, List

# 创建 FastAPI 应用
app = FastAPI(
    title="My Plugin Service",
    description="我的自定义插件服务",
    version="1.0.0",
)

# ==================== 服务注册配置 ====================

# 配置注册中心地址
REGISTRY_URL = "http://localhost:8001"

# 服务配置
SERVICE_CONFIG = {
    "name": "my-plugin",              # 服务唯一标识
    "display_name": "我的插件服务",    # 显示名称
    "description": "这是我的第一个插件服务",
    "version": "1.0.0",
    "host": "localhost",              # 服务主机
    "port": 8010,                     # 服务端口
    "base_path": "/",                 # 基础路径
    "health_check_url": "/health",    # 健康检查端点
    "metadata": {
        "author": "Your Name",
        "category": "custom",
    },
    "tags": ["plugin", "custom"],
    "requires_auth": False,           # 是否需要认证
    "endpoints": [
        # 定义所有端点
        {
            "path": "hello",
            "method": "GET",
            "description": "问候端点",
            "is_public": True,
        },
        {
            "path": "data",
            "method": "GET",
            "description": "获取数据列表",
            "is_public": True,
        },
        {
            "path": "data",
            "method": "POST",
            "description": "创建数据",
            "is_public": True,
        },
    ],
}


# ==================== 服务注册逻辑 ====================

async def register_service():
    """向注册中心注册服务"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{REGISTRY_URL}/api/registry/register",
                json=SERVICE_CONFIG,
            )
            if response.status_code in [200, 201]:
                print(f"✓ 服务注册成功: {SERVICE_CONFIG['name']}")
                return response.json()
            else:
                print(f"✗ 服务注册失败: {response.status_code}")
        except Exception as e:
            print(f"✗ 连接注册中心失败: {e}")
            print(f"  请确保注册中心运行在 {REGISTRY_URL}")


async def send_heartbeat():
    """定期发送心跳"""
    while True:
        await asyncio.sleep(30)  # 每30秒一次
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{REGISTRY_URL}/api/registry/heartbeat",
                    json={
                        "service_id": SERVICE_CONFIG["name"],
                        "status": "healthy",
                    },
                )
            except Exception:
                pass  # 忽略心跳失败


@app.on_event("startup")
async def startup_event():
    """启动时注册服务并开始心跳"""
    await register_service()
    asyncio.create_task(send_heartbeat())


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时注销服务"""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{REGISTRY_URL}/api/registry/deregister/{SERVICE_CONFIG['name']}"
            )
            print("✓ 服务注销成功")
        except Exception as e:
            print(f"✗ 服务注销失败: {e}")


# ==================== 业务逻辑 ====================

# 数据模型
class DataItem(BaseModel):
    id: Optional[int] = None
    title: str
    content: str


# 内存存储
data_store: List[DataItem] = []
id_counter = 1


@app.get("/")
async def root():
    """根端点"""
    return {
        "service": SERVICE_CONFIG["display_name"],
        "version": SERVICE_CONFIG["version"],
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/hello")
async def hello(name: str = "World"):
    """问候端点"""
    return {"message": f"Hello, {name}!"}


@app.get("/data")
async def get_data():
    """获取所有数据"""
    return {"data": data_store, "count": len(data_store)}


@app.post("/data")
async def create_data(item: DataItem):
    """创建新数据"""
    global id_counter
    item.id = id_counter
    data_store.append(item)
    id_counter += 1
    return {"status": "created", "item": item}


@app.get("/data/{item_id}")
async def get_data_item(item_id: int):
    """获取单个数据"""
    for item in data_store:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


# ==================== 启动服务 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=SERVICE_CONFIG["host"],
        port=SERVICE_CONFIG["port"],
    )
```

### 4. 启动插件

```bash
# 确保服务注册中心和网关正在运行

# 启动你的插件
python main.py
```

你应该看到：
```
✓ 服务注册成功: my-plugin
INFO:     Started server process
INFO:     Uvicorn running on http://localhost:8010
```

### 5. 测试插件

```bash
# 直接访问插件
curl http://localhost:8010/hello?name=Developer

# 通过网关访问（推荐）
curl http://localhost:8000/api/my-plugin/hello?name=Developer

# 创建数据
curl -X POST http://localhost:8000/api/my-plugin/data \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试数据",
    "content": "这是测试内容"
  }'

# 获取数据列表
curl http://localhost:8000/api/my-plugin/data

# 查看服务是否已注册
curl http://localhost:8001/api/registry/services
```

## 高级特性

### 1. 使用数据库

```python
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@localhost/dbname"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class MyModel(Base):
    __tablename__ = "my_table"
    id = Column(Integer, primary_key=True)
    name = Column(String)

# 在端点中使用
@app.get("/db-data")
async def get_db_data():
    db = SessionLocal()
    items = db.query(MyModel).all()
    db.close()
    return items
```

### 2. 添加认证

```python
from fastapi import Depends, HTTPException, Header

async def verify_api_key(x_api_key: str = Header(...)):
    """验证 API 密钥"""
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.get("/protected", dependencies=[Depends(verify_api_key)])
async def protected_endpoint():
    return {"message": "This is protected"}
```

### 3. 调用其他服务

```python
async def call_other_service(service_name: str, path: str):
    """通过网关调用其他服务"""
    gateway_url = "http://localhost:8000"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{gateway_url}/api/{service_name}/{path}"
        )
        return response.json()

@app.get("/aggregate")
async def aggregate_data():
    """聚合多个服务的数据"""
    service1_data = await call_other_service("demo-service", "items")
    service2_data = await call_other_service("another-service", "data")
    return {
        "service1": service1_data,
        "service2": service2_data,
    }
```

### 4. 添加中间件

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. 后台任务

```python
from fastapi import BackgroundTasks
import time

def process_in_background(item_id: int):
    """后台处理任务"""
    time.sleep(10)  # 模拟长时间处理
    print(f"Processing completed for item {item_id}")

@app.post("/process/{item_id}")
async def trigger_processing(item_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_in_background, item_id)
    return {"message": "Processing started"}
```

## 部署

### Docker 部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

构建并运行：

```bash
docker build -t my-plugin:latest .
docker run -d -p 8010:8010 --name my-plugin my-plugin:latest
```

### 生产环境考虑

1. **使用环境变量**
```python
import os

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:8001")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8010"))
```

2. **添加日志**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Service started")
```

3. **错误处理**
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )
```

## 最佳实践

1. **命名规范**: 使用有意义的服务名称，如 `user-management`、`payment-service`
2. **版本管理**: 在服务配置中明确版本号
3. **健康检查**: 实现 `/health` 端点用于监控
4. **文档**: 使用 FastAPI 自动文档功能
5. **测试**: 编写单元测试和集成测试
6. **监控**: 添加日志和指标收集

## 故障排查

### 服务注册失败
- 检查注册中心是否运行
- 验证 REGISTRY_URL 配置
- 查看网络连接

### 无法通过网关访问
- 确认服务已成功注册
- 检查服务名称是否正确
- 验证端点路径配置

### 心跳失败
- 检查注册中心连接
- 确认服务 ID 正确
- 查看网络稳定性

## 示例项目

查看 `examples/plugins/` 目录获取更多示例：

- `demo-service`: 基础 CRUD 服务
- `analytics-service`: 数据分析服务（待添加）
- `notification-service`: 通知服务（待添加）

## 下一步

- 了解 [API 网关配置](./GATEWAY_CONFIG.md)
- 阅读 [服务注册中心 API](./REGISTRY_API.md)
- 学习 [多租户配置](./MULTI_TENANT.md)
