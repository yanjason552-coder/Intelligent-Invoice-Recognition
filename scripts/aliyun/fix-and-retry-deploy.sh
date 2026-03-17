#!/bin/bash
# 完整的修复和重新部署脚本
# 在服务器上直接执行此脚本

set -e

SERVER_IP="8.145.33.61"
DB_HOST="8.145.33.61"
DB_PORT="50511"
DB_USER="postgres"
DB_PASSWORD="postgres123"
DB_NAME="invoice_db"
GIT_REPO="https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git"

echo "=========================================="
echo "Docker镜像问题修复和重新部署"
echo "=========================================="
echo ""

# 步骤1: 配置Docker镜像加速器
echo "[1/6] 配置Docker镜像加速器..."
mkdir -p /etc/docker

# 备份现有配置
if [ -f /etc/docker/daemon.json ]; then
    cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
    echo "已备份现有配置"
fi

# 配置镜像加速器（移除不可用的dockerhub.azk8s.cn）
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "max-concurrent-downloads": 10,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# 重启Docker服务
systemctl daemon-reload
systemctl restart docker
echo "等待Docker服务重启..."
sleep 5

# 验证配置
echo "验证Docker配置..."
docker info | grep -A 5 "Registry Mirrors" || echo "配置可能未完全生效，但可以继续"

echo "✓ Docker镜像加速器配置完成"
echo ""

# 步骤2: 测试拉取基础镜像
echo "[2/6] 测试拉取基础镜像..."
echo "拉取python:3.10..."
if docker pull python:3.10; then
    echo "✓ python:3.10拉取成功"
else
    echo "尝试拉取python:3.10-slim..."
    docker pull python:3.10-slim || {
        echo "警告: 基础镜像拉取失败，但可以继续构建"
    }
fi

echo "拉取node:20..."
docker pull node:20 || docker pull node:20-slim || echo "警告: node镜像拉取失败"

echo ""

# 步骤3: 确保项目目录存在
echo "[3/6] 检查项目目录..."
if [ ! -d "/opt/invoice-app" ]; then
    echo "项目目录不存在，克隆项目..."
    cd /opt
    git clone $GIT_REPO invoice-app
else
    echo "项目目录已存在，更新代码..."
    cd /opt/invoice-app
    git pull || echo "Git pull失败，继续使用现有代码"
fi

cd /opt/invoice-app
echo "✓ 项目目录准备完成"
echo ""

# 步骤4: 配置环境变量
echo "[4/6] 配置环境变量..."
if [ ! -f .env ]; then
    echo "创建.env文件..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
    
    cat > .env << EOF
PROJECT_NAME=智能发票识别系统
ENVIRONMENT=production
DOMAIN=$SERVER_IP
STACK_NAME=invoice-app-production
FRONTEND_HOST=dashboard.$SERVER_IP

DOCKER_IMAGE_BACKEND=invoice-app-backend
DOCKER_IMAGE_FRONTEND=invoice-app-frontend
TAG=latest

SECRET_KEY=$SECRET_KEY
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123456

POSTGRES_SERVER=$DB_HOST
POSTGRES_PORT=$DB_PORT
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=$DB_NAME

REDIS_PASSWORD=
BACKEND_CORS_ORIGINS=http://$SERVER_IP:5173,http://localhost:5173,http://$SERVER_IP:8000

TRAEFIK_USERNAME=admin
TRAEFIK_PASSWORD=admin123456
TRAEFIK_EMAIL=admin@example.com
EOF
    echo "✓ 环境变量文件已创建"
else
    echo "✓ 环境变量文件已存在"
fi
echo ""

# 步骤5: 构建Docker镜像
echo "[5/6] 构建Docker镜像..."
echo "构建后端镜像..."
cd backend
if docker build -t invoice-app-backend:latest .; then
    echo "✓ 后端镜像构建成功"
else
    echo "构建失败，尝试清理缓存后重建..."
    docker builder prune -f
    docker build --no-cache -t invoice-app-backend:latest . || {
        echo "警告: 后端镜像构建失败，请检查错误信息"
    }
fi
cd ..

echo "构建前端镜像..."
cd frontend
if docker build --build-arg VITE_API_URL=http://$SERVER_IP:8000 -t invoice-app-frontend:latest .; then
    echo "✓ 前端镜像构建成功"
else
    echo "构建失败，尝试清理缓存后重建..."
    docker builder prune -f
    docker build --no-cache --build-arg VITE_API_URL=http://$SERVER_IP:8000 -t invoice-app-frontend:latest . || {
        echo "警告: 前端镜像构建失败，请检查错误信息"
    }
fi
cd ..

echo ""

# 步骤6: 部署服务
echo "[6/6] 部署服务..."
cd /opt/invoice-app

# 停止旧容器
docker compose -f docker-compose.yml down 2>/dev/null || true

# 创建Docker网络
docker network create traefik-public 2>/dev/null || true

# 确定使用的compose文件
if [ -f docker-compose.production.external-db.yml ]; then
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.production.external-db.yml"
    PROFILE="--profile no-db"
    echo "使用外部数据库配置"
else
    COMPOSE_FILES="-f docker-compose.yml"
    PROFILE=""
    echo "使用标准配置"
fi

# 启动服务
echo "启动服务..."
docker compose $COMPOSE_FILES $PROFILE up -d redis prestart backend frontend adminer || \
docker compose $COMPOSE_FILES up -d redis prestart backend frontend adminer

# 等待服务启动
echo "等待服务启动..."
sleep 15

# 检查服务状态
echo ""
echo "=========================================="
echo "服务状态"
echo "=========================================="
docker compose $COMPOSE_FILES ps || docker compose ps

echo ""
echo "=========================================="
echo "修复和部署完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: http://$SERVER_IP:5173"
echo "  API文档: http://$SERVER_IP:8000/docs"
echo "  API健康检查: http://$SERVER_IP:8000/api/v1/utils/health-check/"
echo ""
echo "查看日志:"
echo "  docker compose logs -f backend"
echo "  docker compose logs -f frontend"
echo ""
echo "=========================================="

