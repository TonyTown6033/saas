"""
示例插件服务 - Demo Service
展示如何创建一个可热插拔的微服务
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
from typing import Optional

# 创建 FastAPI 应用
app = FastAPI(
    title="Demo Plugin Service",
    description="演示插件服务 - 展示热插拔机制",
    version="1.0.0",
)


# ==================== 服务注册相关 ====================

REGISTRY_URL = "http://localhost:8001"
SERVICE_CONFIG = {
    "name": "demo-service",
    "display_name": "演示服务",
    "description": "这是一个演示如何创建热插拔服务的示例",
    "version": "1.0.0",
    "host": "localhost",
    "port": 8003,
    "base_path": "/",
    "health_check_url": "/health",
    "service_metadata": {
        "author": "SAAS Platform",
        "category": "demo",
    },
    "tags": ["demo", "example"],
    "requires_auth": False,
    "endpoints": [
        {
            "path": "items",
            "method": "GET",
            "description": "获取所有项目",
            "is_public": True,
        },
        {
            "path": "items",
            "method": "POST",
            "description": "创建新项目",
            "is_public": True,
        },
        {
            "path": "items/{item_id}",
            "method": "GET",
            "description": "获取项目详情",
            "is_public": True,
        },
    ],
}


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
                print(f"✗ 服务注册失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"✗ 连接注册中心失败: {e}")


async def send_heartbeat():
    """定期发送心跳"""
    while True:
        await asyncio.sleep(30)  # 每30秒发送一次心跳
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{REGISTRY_URL}/api/registry/heartbeat",
                    json={
                        "service_id": SERVICE_CONFIG["name"],
                        "status": "healthy",
                    },
                )
                if response.status_code == 200:
                    print("♥ 心跳发送成功")
            except Exception as e:
                print(f"✗ 心跳发送失败: {e}")


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

# 简单的内存存储
items_db = {}
item_counter = 1


class Item(BaseModel):
    """项目模型"""

    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float


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


@app.get("/items")
async def get_items():
    """获取所有项目"""
    return {"items": list(items_db.values()), "count": len(items_db)}


@app.post("/items")
async def create_item(item: Item):
    """创建新项目"""
    global item_counter

    item.id = item_counter
    items_db[item_counter] = item.dict()
    item_counter += 1

    return {"status": "created", "item": item}


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """获取项目详情"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")

    return items_db[item_id]


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    """更新项目"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")

    item.id = item_id
    items_db[item_id] = item.dict()

    return {"status": "updated", "item": item}


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """删除项目"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")

    del items_db[item_id]

    return {"status": "deleted", "item_id": item_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=SERVICE_CONFIG["host"],
        port=SERVICE_CONFIG["port"],
    )
