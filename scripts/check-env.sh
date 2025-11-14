#!/bin/bash

# 环境检查脚本

echo "======================================"
echo "SAAS 平台环境检查"
echo "======================================"
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

passed=0
failed=0
warnings=0

# 检查 Python
echo "检查 Python..."
if command -v python &> /dev/null; then
    python_version=$(python --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python 已安装: $python_version${NC}"
    ((passed++))

    # 检查版本
    major=$(echo $python_version | cut -d. -f1)
    minor=$(echo $python_version | cut -d. -f2)
    if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
        echo -e "${GREEN}  版本符合要求 (>= 3.11)${NC}"
    else
        echo -e "${RED}  警告: Python 版本过低，建议使用 3.11+${NC}"
        ((warnings++))
    fi
else
    echo -e "${RED}✗ Python 未安装${NC}"
    ((failed++))
fi
echo ""

# 检查虚拟环境
echo "检查虚拟环境..."
if [ -d "backend/.venv" ]; then
    echo -e "${GREEN}✓ 虚拟环境已创建${NC}"
    ((passed++))
else
    echo -e "${YELLOW}⚠ 虚拟环境未创建${NC}"
    echo "  运行: cd backend && uv venv"
    ((warnings++))
fi
echo ""

# 检查 Docker
echo "检查 Docker..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo -e "${GREEN}✓ Docker 已安装: $docker_version${NC}"
    ((passed++))

    # 检查 Docker 是否运行
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✓ Docker 服务正在运行${NC}"
        ((passed++))
    else
        echo -e "${RED}✗ Docker 服务未运行${NC}"
        echo "  请启动 Docker Desktop"
        ((failed++))
    fi
else
    echo -e "${YELLOW}⚠ Docker 未安装（可选，但推荐）${NC}"
    ((warnings++))
fi
echo ""

# 检查 PostgreSQL
echo "检查 PostgreSQL..."
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ psql 客户端已安装${NC}"
    ((passed++))
else
    echo -e "${YELLOW}⚠ psql 未安装（可选）${NC}"
    ((warnings++))
fi

# 尝试连接数据库
if psql -U saas_user -d saas_platform -c "SELECT 1" &> /dev/null; then
    echo -e "${GREEN}✓ 数据库连接成功${NC}"
    ((passed++))
else
    echo -e "${YELLOW}⚠ 无法连接到数据库${NC}"
    echo "  运行: docker-compose up -d postgres"
    ((warnings++))
fi
echo ""

# 检查端口占用
echo "检查端口..."
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠ 端口 $port ($service) 已被占用${NC}"
        lsof -Pi :$port -sTCP:LISTEN | grep LISTEN
        ((warnings++))
    else
        echo -e "${GREEN}✓ 端口 $port ($service) 可用${NC}"
        ((passed++))
    fi
}

check_port 8000 "网关"
check_port 8001 "注册中心"
check_port 8002 "核心服务"
echo ""

# 检查必需文件
echo "检查项目文件..."
files=(
    "backend/shared/__init__.py"
    "backend/shared/models/__init__.py"
    "backend/shared/schemas/__init__.py"
    "backend/registry/main.py"
    "backend/gateway/main.py"
    "backend/core/main.py"
    "backend/requirements.txt"
    "docker-compose.yml"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
        ((passed++))
    else
        echo -e "${RED}✗ $file 缺失${NC}"
        ((failed++))
    fi
done
echo ""

# 检查 Python 依赖
echo "检查 Python 依赖..."
if [ -d "backend/.venv" ]; then
    source backend/.venv/bin/activate 2>/dev/null || true

    deps=("fastapi" "uvicorn" "sqlalchemy" "pydantic")
    for dep in "${deps[@]}"; do
        if python -c "import $dep" 2>/dev/null; then
            echo -e "${GREEN}✓ $dep 已安装${NC}"
            ((passed++))
        else
            echo -e "${RED}✗ $dep 未安装${NC}"
            ((failed++))
        fi
    done
else
    echo -e "${YELLOW}⚠ 跳过依赖检查（虚拟环境未创建）${NC}"
    ((warnings++))
fi
echo ""

# 总结
echo "======================================"
echo "检查总结"
echo "======================================"
echo -e "${GREEN}通过: $passed${NC}"
echo -e "${YELLOW}警告: $warnings${NC}"
echo -e "${RED}失败: $failed${NC}"
echo ""

if [ $failed -eq 0 ]; then
    if [ $warnings -eq 0 ]; then
        echo -e "${GREEN}✓ 环境配置完美！可以开始使用了。${NC}"
        echo ""
        echo "下一步:"
        echo "  1. 启动服务: make dev-start"
        echo "  2. 或使用 Docker: docker-compose up -d"
    else
        echo -e "${YELLOW}⚠ 环境基本正常，但有一些警告${NC}"
        echo "  可以继续使用，但建议解决警告项"
    fi
    exit 0
else
    echo -e "${RED}✗ 环境配置存在问题${NC}"
    echo ""
    echo "请参考 TROUBLESHOOTING.md 解决问题"
    exit 1
fi
