#!/usr/bin/env python3
"""
服务注册中心启动脚本
"""
import sys
import os

# 添加 backend 到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    import uvicorn

    print("启动服务注册中心...")
    print("地址: http://localhost:8001")
    print("API 文档: http://localhost:8001/docs")

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
