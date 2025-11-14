"""
API Key 模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import secrets
from ..database import Base


class APIKey(Base):
    """API密钥模型"""

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)

    # API密钥信息
    name = Column(String(100), nullable=False)
    key = Column(String(64), nullable=False, unique=True, default=lambda: secrets.token_urlsafe(48))
    is_active = Column(Boolean, default=True)

    # 权限范围
    scopes = Column(JSON, default=list)  # 允许访问的服务/端点

    # 有效期
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)

    # 关系
    tenant = relationship("Tenant", back_populates="api_keys")

    def is_expired(self):
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<APIKey {self.name}>"
