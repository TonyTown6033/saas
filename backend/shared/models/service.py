"""
服务模型 - 热插拔服务注册
"""
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database import Base


class Service(Base):
    """微服务注册信息"""

    __tablename__ = "services"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 服务基本信息
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), nullable=False)

    # 服务实例信息
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    base_path = Column(String(100), default="/")

    # 服务状态
    is_active = Column(Boolean, default=True)
    health_check_url = Column(String(255), nullable=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)

    # 服务元数据
    service_metadata = Column("metadata", JSON, default=dict)  # 自定义元数据
    tags = Column(JSON, default=list)  # 服务标签

    # 认证配置
    requires_auth = Column(Boolean, default=True)
    api_key = Column(String(255), nullable=True)  # 服务间通信的API密钥

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    endpoints = relationship("ServiceEndpoint", back_populates="service", cascade="all, delete-orphan")

    @property
    def url(self):
        """服务完整URL"""
        return f"http://{self.host}:{self.port}{self.base_path}"

    def __repr__(self):
        return f"<Service {self.name} v{self.version}>"


class ServiceEndpoint(Base):
    """服务端点信息"""

    __tablename__ = "service_endpoints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_id = Column(String(36), ForeignKey("services.id"), nullable=False)

    # 端点信息
    path = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE, etc.
    description = Column(Text, nullable=True)

    # 权限配置
    required_roles = Column(JSON, default=list)  # 需要的角色列表
    is_public = Column(Boolean, default=False)  # 是否公开访问

    # 限流配置
    rate_limit = Column(Integer, nullable=True)  # 每分钟请求数限制

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    service = relationship("Service", back_populates="endpoints")

    def __repr__(self):
        return f"<ServiceEndpoint {self.method} {self.path}>"
