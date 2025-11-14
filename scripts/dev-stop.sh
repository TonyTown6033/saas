#!/bin/bash

# 开发环境停止脚本

echo "======================================"
echo "停止 SAAS 平台服务..."
echo "======================================"
echo ""

# 停止服务
if [ -f logs/registry.pid ]; then
    PID=$(cat logs/registry.pid)
    if kill $PID 2>/dev/null; then
        echo "✓ 已停止服务注册中心 (PID: $PID)"
    fi
    rm logs/registry.pid
fi

if [ -f logs/gateway.pid ]; then
    PID=$(cat logs/gateway.pid)
    if kill $PID 2>/dev/null; then
        echo "✓ 已停止 API 网关 (PID: $PID)"
    fi
    rm logs/gateway.pid
fi

if [ -f logs/core.pid ]; then
    PID=$(cat logs/core.pid)
    if kill $PID 2>/dev/null; then
        echo "✓ 已停止核心服务 (PID: $PID)"
    fi
    rm logs/core.pid
fi

if [ -f logs/demo.pid ]; then
    PID=$(cat logs/demo.pid)
    if kill $PID 2>/dev/null; then
        echo "✓ 已停止演示服务 (PID: $PID)"
    fi
    rm logs/demo.pid
fi

echo ""
echo "✓ 所有服务已停止"
echo ""
