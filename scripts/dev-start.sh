#!/bin/bash

# 开发环境启动脚本

set -e

echo "======================================"
echo "SAAS 平台 - 开发环境启动脚本"
echo "======================================"
echo ""

# 检查 Python 版本
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python 版本: $python_version"

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠ 警告: 未检测到虚拟环境"
    echo "  建议运行: cd backend && uv venv && source .venv/bin/activate"
    echo ""
    read -p "是否继续？ (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查依赖
echo ""
echo "检查依赖..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠ 未安装依赖，正在安装..."
    cd backend
    uv pip install -r requirements.txt
    cd ..
fi

# 检查数据库连接
echo ""
echo "检查数据库连接..."
if command -v psql &> /dev/null; then
    if psql -U saas_user -d saas_platform -c "SELECT 1" &> /dev/null; then
        echo "✓ 数据库连接成功"
    else
        echo "⚠ 无法连接到数据库"
        echo "  请确保 PostgreSQL 正在运行"
        echo "  或者运行: docker-compose up -d postgres redis"
    fi
else
    echo "⚠ 未安装 psql，跳过数据库检查"
fi

# 创建日志目录
mkdir -p logs

# 启动服务
echo ""
echo "======================================"
echo "启动服务..."
echo "======================================"
echo ""

# 启动服务注册中心
echo "启动服务注册中心 (端口 8001)..."
cd backend/registry
python main.py > ../../logs/registry.log 2>&1 &
REGISTRY_PID=$!
echo "  PID: $REGISTRY_PID"
cd ../..

sleep 2

# 启动 API 网关
echo "启动 API 网关 (端口 8000)..."
cd backend/gateway
python main.py > ../../logs/gateway.log 2>&1 &
GATEWAY_PID=$!
echo "  PID: $GATEWAY_PID"
cd ../..

sleep 2

# 启动核心服务
echo "启动核心服务 (端口 8002)..."
cd backend/core
python main.py > ../../logs/core.log 2>&1 &
CORE_PID=$!
echo "  PID: $CORE_PID"
cd ../..

sleep 2

# 启动演示服务（可选）
if [ "$1" == "--with-demo" ]; then
    echo "启动演示服务 (端口 8003)..."
    cd examples/plugins/demo-service
    python main.py > ../../../logs/demo.log 2>&1 &
    DEMO_PID=$!
    echo "  PID: $DEMO_PID"
    cd ../../..
fi

# 保存 PID
echo "$REGISTRY_PID" > logs/registry.pid
echo "$GATEWAY_PID" > logs/gateway.pid
echo "$CORE_PID" > logs/core.pid
[ ! -z "$DEMO_PID" ] && echo "$DEMO_PID" > logs/demo.pid

echo ""
echo "======================================"
echo "✓ 所有服务已启动"
echo "======================================"
echo ""
echo "服务地址:"
echo "  - API 网关:        http://localhost:8000"
echo "  - 服务注册中心:    http://localhost:8001"
echo "  - 核心服务:        http://localhost:8002"
[ ! -z "$DEMO_PID" ] && echo "  - 演示服务:        http://localhost:8003"
echo ""
echo "API 文档:"
echo "  - 网关文档:        http://localhost:8000/docs"
echo "  - 注册中心文档:    http://localhost:8001/docs"
echo "  - 核心服务文档:    http://localhost:8002/docs"
echo ""
echo "查看日志:"
echo "  tail -f logs/gateway.log"
echo "  tail -f logs/registry.log"
echo "  tail -f logs/core.log"
echo ""
echo "停止服务:"
echo "  ./scripts/dev-stop.sh"
echo ""
