#!/bin/bash

# 一键启动所有服务的脚本

PROJECT_ROOT="/Users/town/Project/SAAS"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV="$BACKEND_DIR/.venv/bin/activate"

echo "======================================"
echo "启动 SAAS 平台所有服务"
echo "======================================"
echo ""

# 激活虚拟环境并进入 backend 目录
source "$VENV"
cd "$BACKEND_DIR"

# 启动服务注册中心
echo "1. 启动服务注册中心 (端口 8001)..."
uvicorn registry.main:app --host 0.0.0.0 --port 8001 &
REGISTRY_PID=$!
echo "   PID: $REGISTRY_PID"
sleep 3

# 启动 API 网关
echo "2. 启动 API 网关 (端口 8000)..."
uvicorn gateway.main:app --host 0.0.0.0 --port 8000 &
GATEWAY_PID=$!
echo "   PID: $GATEWAY_PID"
sleep 3

# 启动核心服务
echo "3. 启动核心服务 (端口 8002)..."
uvicorn core.main:app --host 0.0.0.0 --port 8002 &
CORE_PID=$!
echo "   PID: $CORE_PID"
sleep 3

# 启动演示服务
echo "4. 启动演示服务 (端口 8003)..."
python "$PROJECT_ROOT/examples/plugins/demo-service/main.py" &
DEMO_PID=$!
echo "   PID: $DEMO_PID"
sleep 3

echo ""
echo "======================================"
echo "✓ 所有服务已启动"
echo "======================================"
echo ""
echo "服务地址:"
echo "  - 注册中心: http://localhost:8001"
echo "  - API 网关:  http://localhost:8000"
echo "  - 核心服务:  http://localhost:8002"
echo "  - 演示服务:  http://localhost:8003"
echo ""
echo "PID 列表:"
echo "  - 注册中心: $REGISTRY_PID"
echo "  - 网关: $GATEWAY_PID"
echo "  - 核心服务: $CORE_PID"
echo "  - 演示服务: $DEMO_PID"
echo ""
echo "停止所有服务:"
echo "  kill $REGISTRY_PID $GATEWAY_PID $CORE_PID $DEMO_PID"
echo ""
echo "保持此终端打开以查看日志..."
wait
