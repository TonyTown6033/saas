"""
租户模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database import Base


class Tenant(Base):
    """租户模型"""

    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)

    # 租户配置（JSON格式）
    config = Column(JSON, default=dict)

    # 租户可用的服务列表（服务ID列表）
    enabled_services = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    users = relationship("User", back_populates="tenant")
    api_keys = relationship("APIKey", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant {self.name}>"
