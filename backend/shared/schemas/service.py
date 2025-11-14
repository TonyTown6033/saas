"""
服务相关的 Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ServiceEndpointBase(BaseModel):
    """服务端点基础Schema"""
    path: str
    method: str
    description: Optional[str] = None
    required_roles: List[str] = Field(default_factory=list)
    is_public: bool = False
    rate_limit: Optional[int] = None


class ServiceEndpointCreate(ServiceEndpointBase):
    """创建服务端点Schema"""
    pass


class ServiceEndpointResponse(ServiceEndpointBase):
    """服务端点响应Schema"""
    id: str
    service_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceBase(BaseModel):
    """服务基础Schema"""
    name: str
    display_name: str
    description: Optional[str] = None
    version: str


class ServiceRegister(ServiceBase):
    """服务注册Schema"""
    host: str
    port: int
    base_path: str = "/"
    health_check_url: Optional[str] = None
    service_metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    requires_auth: bool = True
    api_key: Optional[str] = None
    endpoints: List[ServiceEndpointCreate] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class ServiceUpdate(BaseModel):
    """服务更新Schema"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    service_metadata: Optional[Dict[str, Any]] = Field(default=None)
    tags: Optional[List[str]] = None

    class Config:
        populate_by_name = True


class ServiceResponse(ServiceBase):
    """服务响应Schema"""
    id: str
    host: str
    port: int
    base_path: str
    url: str
    is_active: bool
    health_check_url: Optional[str]
    last_heartbeat: datetime
    service_metadata: Dict[str, Any]
    tags: List[str]
    requires_auth: bool
    created_at: datetime
    updated_at: datetime
    endpoints: List[ServiceEndpointResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
        populate_by_name = True


class ServiceHeartbeat(BaseModel):
    """服务心跳Schema"""
    service_id: str
    status: str = "healthy"
    service_metadata: Optional[Dict[str, Any]] = Field(default=None)

    class Config:
        populate_by_name = True
