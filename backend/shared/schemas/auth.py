"""
认证相关的 Pydantic Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础Schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """用户创建Schema"""
    password: str = Field(..., min_length=8)
    tenant_id: Optional[str] = None
    role: str = "user"


class UserResponse(UserBase):
    """用户响应Schema"""
    id: str
    tenant_id: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token响应Schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token数据Schema"""
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求Schema"""
    username: str
    password: str
