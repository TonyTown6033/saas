#!/bin/bash

# 系统测试脚本

set -e

echo "======================================"
echo "SAAS 平台系统测试"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 测试函数
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    echo -n "测试 $name ... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")

    if [ "$response" == "$expected_code" ]; then
        echo -e "${GREEN}✓ 通过${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ 失败${NC} (期望: $expected_code, 实际: $response)"
        return 1
    fi
}

passed=0
failed=0

echo "1. 测试基础服务..."
echo "-----------------------------------"

if test_endpoint "API 网关" "http://localhost:8000"; then
    ((passed++))
else
    ((failed++))
fi

if test_endpoint "服务注册中心" "http://localhost:8001"; then
    ((passed++))
else
    ((failed++))
fi

if test_endpoint "核心服务" "http://localhost:8002"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
echo "2. 测试注册中心 API..."
echo "-----------------------------------"

if test_endpoint "服务列表" "http://localhost:8001/api/registry/services"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
echo "3. 测试用户注册和登录..."
echo "-----------------------------------"

# 生成随机用户名
RANDOM_USER="test_$(date +%s)"

echo -n "注册新用户 ... "
register_response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8002/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$RANDOM_USER\",
    \"email\": \"$RANDOM_USER@test.com\",
    \"password\": \"password123\"
  }")

register_code=$(echo "$register_response" | tail -n1)
if [ "$register_code" == "201" ]; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((passed++))
else
    echo -e "${RED}✗ 失败${NC} (HTTP $register_code)"
    ((failed++))
fi

echo -n "用户登录 ... "
login_response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$RANDOM_USER\",
    \"password\": \"password123\"
  }")

login_code=$(echo "$login_response" | tail -n1)
if [ "$login_code" == "200" ]; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((passed++))

    # 提取 token
    TOKEN=$(echo "$login_response" | sed '$d' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")
else
    echo -e "${RED}✗ 失败${NC} (HTTP $login_code)"
    ((failed++))
fi

if [ ! -z "$TOKEN" ]; then
    echo -n "获取当前用户信息 ... "
    me_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/auth/me \
      -H "Authorization: Bearer $TOKEN")

    if [ "$me_response" == "200" ]; then
        echo -e "${GREEN}✓ 通过${NC}"
        ((passed++))
    else
        echo -e "${RED}✗ 失败${NC} (HTTP $me_response)"
        ((failed++))
    fi
fi

echo ""
echo "4. 测试网关路由..."
echo "-----------------------------------"

if test_endpoint "网关服务列表" "http://localhost:8000/gateway/services"; then
    ((passed++))
else
    ((failed++))
fi

# 检查是否有 demo-service
echo -n "检查演示服务 ... "
demo_check=$(curl -s http://localhost:8000/gateway/services | grep -c "demo-service" || echo "0")
if [ "$demo_check" -gt "0" ]; then
    echo -e "${GREEN}✓ 已注册${NC}"
    ((passed++))

    # 测试通过网关访问演示服务
    if test_endpoint "通过网关访问演示服务" "http://localhost:8000/api/demo-service/items"; then
        ((passed++))
    else
        ((failed++))
    fi
else
    echo -e "${RED}✗ 未注册${NC}"
    echo "  提示: 使用 --with-demo 参数启动演示服务"
    ((failed++))
fi

echo ""
echo "======================================"
echo "测试总结"
echo "======================================"
echo -e "通过: ${GREEN}$passed${NC}"
echo -e "失败: ${RED}$failed${NC}"
echo "总计: $((passed + failed))"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 部分测试失败${NC}"
    exit 1
fi
