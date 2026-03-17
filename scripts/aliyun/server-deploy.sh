#!/bin/bash
# 服务器端部署脚本
# 在ECS服务器上直接执行此脚本

set -e

# 服务器配置
SERVER_IP="8.145.33.61"
SSH_PORT="50518"

# 数据库配置（外部PostgreSQL）
DB_HOST="8.145.33.61"
DB_PORT="50511"
DB_USER="postgres"
DB_PASSWORD="postgres123"
DB_NAME="invoice_db"

# Git仓库
GIT_REPO="https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git"

echo "=========================================="
echo "开始部署智能发票识别系统"
echo "=========================================="
echo "服务器: $SERVER_IP"
echo "数据库: $DB_HOST:$DB_PORT"
echo "Git仓库: $GIT_REPO"
echo ""

# 步骤1: 更新系统并安装Docker
echo "[1/7] 更新系统并安装Docker..."
apt-get update -qq
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # 配置Docker镜像加速器（阿里云）
    echo "配置Docker镜像加速器..."
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << 'DOCKER_DAEMON'
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
DOCKER_DAEMON
    
    # 重启Docker服务使配置生效
    systemctl daemon-reload
    systemctl restart docker
    echo "Docker镜像加速器配置完成"
else
    # 即使Docker已安装，也检查并配置镜像加速器
    if [ ! -f /etc/docker/daemon.json ]; then
        echo "配置Docker镜像加速器..."
        mkdir -p /etc/docker
        cat > /etc/docker/daemon.json << 'DOCKER_DAEMON'
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
DOCKER_DAEMON
        systemctl daemon-reload
        systemctl restart docker
        echo "Docker镜像加速器配置完成"
    fi
fi

if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "安装Docker Compose..."
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 步骤2: 创建目录
echo "[2/7] 创建目录结构..."
mkdir -p /opt/invoice-app/{uploads,data/redis,backups,scripts/aliyun}
mkdir -p /opt/traefik-public
docker network create traefik-public 2>/dev/null || true

# 步骤3: 克隆项目
echo "[3/7] 克隆项目..."
cd /opt
rm -rf invoice-app
git clone $GIT_REPO invoice-app
cd invoice-app

# 步骤4: 配置环境变量
echo "[4/7] 配置环境变量..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)

cat > .env << EOF
# 项目配置
PROJECT_NAME=智能发票识别系统
ENVIRONMENT=production
DOMAIN=$SERVER_IP
STACK_NAME=invoice-app-production
FRONTEND_HOST=dashboard.$SERVER_IP

# Docker镜像配置
DOCKER_IMAGE_BACKEND=invoice-app-backend
DOCKER_IMAGE_FRONTEND=invoice-app-frontend
TAG=latest

# 安全配置
SECRET_KEY=$SECRET_KEY
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123456

# 数据库配置（外部PostgreSQL）
POSTGRES_SERVER=$DB_HOST
POSTGRES_PORT=$DB_PORT
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=$DB_NAME

# Redis配置
REDIS_PASSWORD=

# CORS配置
BACKEND_CORS_ORIGINS=http://$SERVER_IP:5173,http://localhost:5173,http://$SERVER_IP:8000

# 邮件配置（可选）
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=

# Sentry配置（可选）
SENTRY_DSN=

# Traefik配置
TRAEFIK_USERNAME=admin
TRAEFIK_PASSWORD=admin123456
TRAEFIK_EMAIL=admin@example.com
EOF

echo "环境变量已配置"

# 步骤5: 配置Docker镜像加速器（如果尚未配置）
echo "[5/8] 配置Docker镜像加速器..."
if [ ! -f /etc/docker/daemon.json ] || ! grep -q "registry-mirrors" /etc/docker/daemon.json 2>/dev/null; then
    echo "配置Docker镜像加速器..."
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << 'DOCKER_DAEMON'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://dockerhub.azk8s.cn"
  ],
  "max-concurrent-downloads": 10,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
DOCKER_DAEMON
    systemctl daemon-reload
    systemctl restart docker
    echo "等待Docker服务重启..."
    sleep 5
    echo "✓ Docker镜像加速器配置完成"
else
    echo "✓ Docker镜像加速器已配置"
fi

# 步骤6: 构建Docker镜像
echo "[6/8] 构建Docker镜像..."
echo "先测试拉取Python基础镜像..."
docker pull python:3.10 || {
    echo "警告: 无法拉取python:3.10镜像，尝试使用python:3.10-slim..."
    docker pull python:3.10-slim || {
        echo "错误: 无法拉取Python镜像，请检查网络连接或Docker镜像加速器配置"
        echo "可以手动执行修复脚本: bash scripts/aliyun/fix-docker-mirror.sh"
        exit 1
    }
    # 如果使用slim版本，需要修改Dockerfile
    echo "使用python:3.10-slim作为基础镜像"
}

echo "构建后端镜像..."
cd backend
# 尝试使用标准Dockerfile
docker build -t invoice-app-backend:latest . || {
    echo "标准构建失败，尝试使用国内镜像源..."
    # 如果标准构建失败，可以尝试修改Dockerfile第一行为: FROM python:3.10-slim
    docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t invoice-app-backend:latest . || {
        echo "后端镜像构建失败，请检查错误信息"
        echo "提示: 可以尝试手动构建或使用预构建镜像"
    }
}
cd ..

echo "构建前端镜像..."
cd frontend
docker build --build-arg VITE_API_URL=http://$SERVER_IP:8000 -t invoice-app-frontend:latest . || {
    echo "前端镜像构建失败，请检查错误信息"
    echo "提示: 可以尝试手动构建或使用预构建镜像"
}
cd ..

# 步骤7: 部署服务
echo "[7/8] 部署服务..."
# 停止旧容器
docker compose -f docker-compose.yml down 2>/dev/null || true

# 如果存在外部数据库配置，使用它
if [ -f docker-compose.production.external-db.yml ]; then
    echo "使用外部数据库配置..."
    docker compose -f docker-compose.yml -f docker-compose.production.external-db.yml --profile no-db up -d redis prestart backend frontend adminer
else
    echo "使用标准配置..."
    docker compose -f docker-compose.yml up -d redis prestart backend frontend adminer
fi

# 等待服务启动
echo "等待服务启动..."
sleep 15

# 步骤8: 检查服务状态
echo "[8/8] 检查服务状态..."
docker compose ps

echo ""
echo "=========================================="
echo "部署完成！"
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
echo "重启服务:"
echo "  docker compose restart"
echo ""
echo "=========================================="

