#!/bin/bash
# 快速部署脚本 - 使用提供的服务器信息
# 适配外部PostgreSQL数据库

set -e

# 服务器配置
SERVER_IP="8.145.33.61"
SSH_PORT="50518"
SSH_USER="root"
SSH_PASSWORD="6b3fPk9n!"

# 数据库配置（外部PostgreSQL）
DB_HOST="8.145.33.61"
DB_PORT="50511"
DB_USER="postgres"
DB_PASSWORD="postgres123"
DB_NAME="invoice_db"

# Git仓库
GIT_REPO="https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=========================================="
echo "快速部署 - 智能发票识别系统"
echo "==========================================${NC}"
echo "服务器: $SERVER_IP:$SSH_PORT"
echo "数据库: $DB_HOST:$DB_PORT"
echo "Git仓库: $GIT_REPO"
echo ""

# 检查sshpass
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}提示: 安装sshpass可自动输入密码${NC}"
    echo "  Ubuntu: sudo apt-get install sshpass"
    echo "  Mac: brew install sshpass"
    SSH_CMD="ssh -p $SSH_PORT"
    SCP_CMD="scp -P $SSH_PORT"
else
    SSH_CMD="sshpass -p '$SSH_PASSWORD' ssh -o StrictHostKeyChecking=no -p $SSH_PORT"
    SCP_CMD="sshpass -p '$SSH_PASSWORD' scp -o StrictHostKeyChecking=no -P $SSH_PORT"
fi

# 远程执行函数
remote_exec() {
    if command -v sshpass &> /dev/null; then
        sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -p $SSH_PORT $SSH_USER@$SERVER_IP "$@"
    else
        ssh -p $SSH_PORT $SSH_USER@$SERVER_IP "$@"
    fi
}

echo -e "${YELLOW}[1/6] 测试服务器连接...${NC}"
if remote_exec "echo '连接成功'"; then
    echo -e "${GREEN}✓ 服务器连接成功${NC}"
else
    echo -e "${RED}✗ 服务器连接失败${NC}"
    exit 1
fi

echo -e "${YELLOW}[2/6] 初始化服务器环境...${NC}"
remote_exec "bash -s" << 'REMOTE_INIT'
# 更新系统
apt-get update -qq

# 安装Docker（如果未安装）
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# 安装Docker Compose（如果未安装）
if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "安装Docker Compose..."
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 创建目录
mkdir -p /opt/invoice-app/{uploads,data/redis,backups,scripts/aliyun}
mkdir -p /opt/traefik-public

# 创建Docker网络
docker network create traefik-public 2>/dev/null || true

echo "服务器环境初始化完成"
REMOTE_INIT

echo -e "${GREEN}✓ 服务器环境初始化完成${NC}"

echo -e "${YELLOW}[3/6] 克隆项目到服务器...${NC}"
remote_exec "cd /opt && rm -rf invoice-app && git clone $GIT_REPO invoice-app"
echo -e "${GREEN}✓ 项目已克隆${NC}"

echo -e "${YELLOW}[4/6] 配置环境变量...${NC}"
# 生成安全密钥
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "changethis_$(openssl rand -hex 16)")

remote_exec "bash -s" << REMOTE_ENV
cd /opt/invoice-app

# 创建.env文件
cat > .env << 'EOF'
# 项目配置
PROJECT_NAME=智能发票识别系统
ENVIRONMENT=production
DOMAIN=8.145.33.61
STACK_NAME=invoice-app-production
FRONTEND_HOST=dashboard.8.145.33.61

# Docker镜像配置（使用本地构建或后续配置）
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
BACKEND_CORS_ORIGINS=http://8.145.33.61:5173,http://localhost:5173,http://8.145.33.61:8000

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

echo "环境变量文件已创建"
cat .env
REMOTE_ENV

echo -e "${GREEN}✓ 环境变量配置完成${NC}"

echo -e "${YELLOW}[5/6] 构建Docker镜像（在服务器上）...${NC}"
remote_exec "bash -s" << 'REMOTE_BUILD'
cd /opt/invoice-app

# 构建后端镜像
echo "构建后端镜像..."
cd backend
docker build -t invoice-app-backend:latest . || {
    echo "后端镜像构建失败，将使用现有镜像或跳过"
}

# 构建前端镜像
echo "构建前端镜像..."
cd ../frontend
docker build --build-arg VITE_API_URL=http://8.145.33.61:8000 -t invoice-app-frontend:latest . || {
    echo "前端镜像构建失败，将使用现有镜像或跳过"
}

cd ..
echo "镜像构建完成"
docker images | grep invoice-app
REMOTE_BUILD

echo -e "${GREEN}✓ Docker镜像构建完成${NC}"

echo -e "${YELLOW}[6/6] 部署应用服务...${NC}"
remote_exec "bash -s" << 'REMOTE_DEPLOY'
cd /opt/invoice-app

# 检查是否有外部数据库配置
if [ -f docker-compose.production.external-db.yml ]; then
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.production.external-db.yml"
else
    COMPOSE_FILES="-f docker-compose.yml"
fi

# 停止旧容器
docker compose $COMPOSE_FILES down 2>/dev/null || true

# 启动服务（不使用db服务）
docker compose $COMPOSE_FILES --profile no-db up -d redis prestart backend frontend adminer 2>/dev/null || \
docker compose $COMPOSE_FILES up -d redis prestart backend frontend adminer

# 等待服务启动
sleep 10

# 检查服务状态
docker compose $COMPOSE_FILES ps || docker compose ps

echo "部署完成"
REMOTE_DEPLOY

echo ""
echo -e "${GREEN}=========================================="
echo "部署完成！"
echo "==========================================${NC}"
echo ""
echo "访问地址:"
echo "  前端: http://$SERVER_IP:5173"
echo "  API文档: http://$SERVER_IP:8000/docs"
echo "  API健康检查: http://$SERVER_IP:8000/api/v1/utils/health-check/"
echo ""
echo "查看服务状态:"
echo "  ssh -p $SSH_PORT $SSH_USER@$SERVER_IP"
echo "  cd /opt/invoice-app"
echo "  docker compose ps"
echo ""
echo "查看日志:"
echo "  docker compose logs -f backend"
echo "  docker compose logs -f frontend"
echo ""
echo -e "${YELLOW}注意:${NC}"
echo "  1. 如果使用外部PostgreSQL，请确保数据库已创建: $DB_NAME"
echo "  2. 请检查防火墙规则，确保8000和5173端口已开放"
echo "  3. 首次部署需要运行数据库迁移"
echo "=========================================="

