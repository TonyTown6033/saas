#!/usr/bin/env python3
"""
基础测试脚本 - 测试服务能否正常启动
"""
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_imports():
    """测试基础导入"""
    print("测试基础模块导入...")

    try:
        from shared.config import get_settings
        print("✓ 配置模块导入成功")
    except Exception as e:
        print(f"✗ 配置模块导入失败: {e}")
        return False

    try:
        from shared.database import Base, engine
        print("✓ 数据库模块导入成功")
    except Exception as e:
        print(f"✗ 数据库模块导入失败: {e}")
        return False

    try:
        from shared.models import User, Tenant, Service
        print("✓ 数据模型导入成功")
    except Exception as e:
        print(f"✗ 数据模型导入失败: {e}")
        return False

    try:
        from shared.schemas.service import ServiceRegister
        print("✓ Schemas 导入成功")
    except Exception as e:
        print(f"✗ Schemas 导入失败: {e}")
        return False

    try:
        from shared.utils.auth import get_password_hash
        print("✓ 工具函数导入成功")
    except Exception as e:
        print(f"✗ 工具函数导入失败: {e}")
        return False

    return True


def test_fastapi_apps():
    """测试 FastAPI 应用"""
    print("\n测试 FastAPI 应用...")

    try:
        # 测试注册中心
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'registry'))
        from registry.main import app as registry_app
        print("✓ 注册中心应用加载成功")
    except Exception as e:
        print(f"✗ 注册中心应用加载失败: {e}")
        return False

    try:
        # 测试网关
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'gateway'))
        from gateway.main import app as gateway_app
        print("✓ 网关应用加载成功")
    except Exception as e:
        print(f"✗ 网关应用加载失败: {e}")
        return False

    try:
        # 测试核心服务
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'core'))
        from core.main import app as core_app
        print("✓ 核心服务应用加载成功")
    except Exception as e:
        print(f"✗ 核心服务应用加载失败: {e}")
        return False

    return True


if __name__ == "__main__":
    print("=" * 50)
    print("SAAS 平台基础测试")
    print("=" * 50)
    print()

    success = True

    if not test_imports():
        success = False

    if not test_fastapi_apps():
        success = False

    print()
    print("=" * 50)
    if success:
        print("✓ 所有基础测试通过！")
        print("=" * 50)
        sys.exit(0)
    else:
        print("✗ 部分测试失败")
        print("=" * 50)
        sys.exit(1)
