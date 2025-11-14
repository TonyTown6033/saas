"""
API 网关 - Gateway Service
负责路由请求到注册的微服务
"""
from fastapi import FastAPI, Request, Response, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import sys
import os
from typing import Optional
from datetime import datetime

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_settings

settings = get_settings()

# 创建 FastAPI 应用
app = FastAPI(
    title="API Gateway",
    description="API网关 - 动态路由到注册的微服务",
    version="1.0.0",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ServiceDiscovery:
    """服务发现客户端"""

    def __init__(self):
        self.registry_url = settings.REGISTRY_URL
        self.services_cache = {}
        self.cache_updated_at = None

    async def get_services(self, force_refresh: bool = False):
        """获取所有活跃服务"""
        # 简单的缓存机制（实际生产环境应使用Redis）
        if (
            not force_refresh
            and self.cache_updated_at
            and (datetime.utcnow() - self.cache_updated_at).seconds < 30
        ):
            return self.services_cache

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.registry_url}/api/registry/services")
                if response.status_code == 200:
                    services = response.json()
                    self.services_cache = {s["name"]: s for s in services}
                    self.cache_updated_at = datetime.utcnow()
                    return self.services_cache
            except Exception as e:
                print(f"Error fetching services: {e}")
                return self.services_cache

        return {}

    async def find_service(self, service_name: str):
        """查找服务"""
        services = await self.get_services()
        return services.get(service_name)


# 创建服务发现实例
service_discovery = ServiceDiscovery()


@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "service": "API Gateway",
        "status": "healthy",
        "version": "1.0.0",
        "registry_url": settings.REGISTRY_URL,
    }


@app.get("/gateway/services")
async def list_available_services():
    """列出所有可用服务"""
    services = await service_discovery.get_services(force_refresh=True)
    return {
        "services": list(services.values()),
        "count": len(services),
    }


@app.api_route(
    "/api/{service_name}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def proxy_request(
    service_name: str,
    path: str,
    request: Request,
):
    """
    代理请求到对应的微服务
    路由格式: /api/{service_name}/{path}
    """
    # 查找服务
    service = await service_discovery.find_service(service_name)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found or not available",
        )

    if not service.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service '{service_name}' is not active",
        )

    # 构建目标URL
    service_url = service["url"].rstrip("/")
    target_url = f"{service_url}/{path}"

    # 获取请求体
    body = await request.body()

    # 获取请求头
    headers = dict(request.headers)
    # 移除可能导致问题的头
    headers.pop("host", None)
    headers.pop("content-length", None)

    # 转发请求
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                headers=headers,
                content=body,
            )

            # 返回响应
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Service request timeout",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error connecting to service: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal gateway error: {str(e)}",
            )


@app.post("/gateway/refresh-services")
async def refresh_services():
    """刷新服务缓存"""
    services = await service_discovery.get_services(force_refresh=True)
    return {
        "status": "ok",
        "services_count": len(services),
        "updated_at": service_discovery.cache_updated_at.isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
