"""
核心服务 - Core Service
提供租户管理、用户管理、认证等核心功能
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_settings
from shared.database import get_db, Base, engine
from shared.models import User, Tenant
from shared.schemas.auth import UserCreate, UserResponse, LoginRequest, Token
from shared.utils.auth import verify_password, get_password_hash, create_access_token, create_refresh_token
from shared.dependencies import get_current_user

settings = get_settings()

# 创建 FastAPI 应用
app = FastAPI(
    title="Core Service",
    description="核心平台服务",
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
        "service": "Core Service",
        "status": "healthy",
        "version": "1.0.0",
    }


# ==================== 认证相关 ====================


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        tenant_id=user_data.tenant_id,
        role=user_data.role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@app.post("/auth/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()

    # 生成令牌
    token_data = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "role": user.role,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


# ==================== 用户管理 ====================


@app.get("/users", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户列表"""
    users = db.query(User).all()
    return users


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


# ==================== 租户管理 ====================


@app.post("/tenants", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    name: str,
    display_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建租户"""
    # 检查租户名是否已存在
    if db.query(Tenant).filter(Tenant.name == name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant name already exists",
        )

    tenant = Tenant(name=name, display_name=display_name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return tenant


@app.get("/tenants")
async def list_tenants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取租户列表"""
    tenants = db.query(Tenant).all()
    return tenants


@app.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取租户详情"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return tenant


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
