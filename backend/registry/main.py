"""
服务注册中心 - Registry Service
负责微服务的注册、发现和健康检查
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_settings
from shared.database import get_db, Base, engine
from shared.models import Service, ServiceEndpoint
from shared.schemas.service import (
    ServiceRegister,
    ServiceResponse,
    ServiceHeartbeat,
    ServiceUpdate,
)

settings = get_settings()

# 创建 FastAPI 应用
app = FastAPI(
    title="Service Registry",
    description="微服务注册与发现中心",
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


@app.on_event("startup")
async def startup_event():
    """启动时创建数据库表"""
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "service": "Service Registry",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.post("/api/registry/register", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def register_service(
    service_data: ServiceRegister,
    db: Session = Depends(get_db),
):
    """
    注册新服务
    """
    # 检查服务是否已存在
    existing_service = db.query(Service).filter(Service.name == service_data.name).first()

    if existing_service:
        # 更新已存在的服务
        for key, value in service_data.dict(exclude={"endpoints"}).items():
            setattr(existing_service, key, value)
        existing_service.last_heartbeat = datetime.now(timezone.utc)
        existing_service.is_active = True

        # 删除旧的端点
        db.query(ServiceEndpoint).filter(ServiceEndpoint.service_id == existing_service.id).delete()

        # 添加新端点
        for endpoint_data in service_data.endpoints:
            endpoint = ServiceEndpoint(
                service_id=existing_service.id,
                **endpoint_data.dict(),
            )
            db.add(endpoint)

        db.commit()
        db.refresh(existing_service)
        return existing_service

    # 创建新服务
    service = Service(**service_data.dict(exclude={"endpoints"}))
    db.add(service)
    db.commit()
    db.refresh(service)

    # 添加端点
    for endpoint_data in service_data.endpoints:
        endpoint = ServiceEndpoint(
            service_id=service.id,
            **endpoint_data.dict(),
        )
        db.add(endpoint)

    db.commit()
    db.refresh(service)
    return service


@app.post("/api/registry/heartbeat")
async def service_heartbeat(
    heartbeat: ServiceHeartbeat,
    db: Session = Depends(get_db),
):
    """
    服务心跳
    """
    service = db.query(Service).filter(Service.id == heartbeat.service_id).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    service.last_heartbeat = datetime.now(timezone.utc)
    service.is_active = True

    if heartbeat.metadata:
        service.service_metadata.update(heartbeat.metadata)

    db.commit()

    return {"status": "ok", "message": "Heartbeat received"}


@app.post("/api/registry/deregister/{service_id}")
async def deregister_service(
    service_id: str,
    db: Session = Depends(get_db),
):
    """
    注销服务
    """
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    service.is_active = False
    db.commit()

    return {"status": "ok", "message": "Service deregistered"}


@app.get("/api/registry/services", response_model=List[ServiceResponse])
async def list_services(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """
    获取所有服务列表
    """
    query = db.query(Service)

    if active_only:
        query = query.filter(Service.is_active == True)

    services = query.all()
    return services


@app.get("/api/registry/services/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str,
    db: Session = Depends(get_db),
):
    """
    获取服务详情
    """
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    return service


@app.get("/api/registry/services/by-name/{service_name}", response_model=ServiceResponse)
async def get_service_by_name(
    service_name: str,
    db: Session = Depends(get_db),
):
    """
    根据名称获取服务
    """
    service = db.query(Service).filter(Service.name == service_name).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    return service


@app.put("/api/registry/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    service_update: ServiceUpdate,
    db: Session = Depends(get_db),
):
    """
    更新服务信息
    """
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    update_data = service_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(service, key, value)

    db.commit()
    db.refresh(service)

    return service


@app.delete("/api/registry/services/{service_id}")
async def delete_service(
    service_id: str,
    db: Session = Depends(get_db),
):
    """
    删除服务
    """
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    db.delete(service)
    db.commit()

    return {"status": "ok", "message": "Service deleted"}


@app.get("/api/registry/health")
async def check_stale_services(db: Session = Depends(get_db)):
    """
    检查过期服务（超过5分钟未发送心跳）
    """
    threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
    stale_services = db.query(Service).filter(
        Service.is_active == True,
        Service.last_heartbeat < threshold,
    ).all()

    # 标记为不活跃
    for service in stale_services:
        service.is_active = False

    db.commit()

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "stale_services_count": len(stale_services),
        "stale_services": [{"id": s.id, "name": s.name} for s in stale_services],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
