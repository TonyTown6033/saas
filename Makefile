.PHONY: help install dev-start dev-stop docker-up docker-down test clean

help:
	@echo "SAAS 平台 - 可用命令："
	@echo ""
	@echo "  make install      - 安装依赖"
	@echo "  make dev-start    - 启动开发环境（本地）"
	@echo "  make dev-stop     - 停止开发环境（本地）"
	@echo "  make docker-up    - 使用 Docker 启动所有服务"
	@echo "  make docker-down  - 停止 Docker 服务"
	@echo "  make test         - 运行系统测试"
	@echo "  make clean        - 清理临时文件和日志"
	@echo ""

install:
	@echo "安装 Python 依赖..."
	cd backend && uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
	@echo "✓ 依赖安装完成"

dev-start:
	@echo "启动开发环境..."
	./scripts/dev-start.sh --with-demo

dev-stop:
	@echo "停止开发环境..."
	./scripts/dev-stop.sh

docker-up:
	@echo "启动 Docker 服务..."
	docker-compose up -d
	@echo "✓ 服务已启动"
	@echo ""
	@echo "查看日志: docker-compose logs -f"
	@echo "查看状态: docker-compose ps"

docker-down:
	@echo "停止 Docker 服务..."
	docker-compose down
	@echo "✓ 服务已停止"

test:
	@echo "运行系统测试..."
	./scripts/test-system.sh

clean:
	@echo "清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	rm -rf logs/*.log logs/*.pid 2>/dev/null || true
	@echo "✓ 清理完成"
