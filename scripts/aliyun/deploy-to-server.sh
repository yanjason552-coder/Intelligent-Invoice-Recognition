#!/bin/bash
# 自动化部署脚本
# 用于连接到服务器并执行完整部署流程

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
echo "开始自动化部署"
echo "==========================================${NC}"
echo "服务器: $SERVER_IP:$SSH_PORT"
echo "Git仓库: $GIT_REPO"
echo ""

# 检查sshpass是否安装（用于自动输入密码）
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}警告: sshpass未安装，将需要手动输入密码${NC}"
    echo "安装sshpass:"
    echo "  Ubuntu/Debian: sudo apt-get install sshpass"
    echo "  Mac: brew install sshpass"
    SSH_CMD="ssh"
    SCP_CMD="scp"
else
    SSH_CMD="sshpass -p '$SSH_PASSWORD' ssh -o StrictHostKeyChecking=no -p $SSH_PORT"
    SCP_CMD="sshpass -p '$SSH_PASSWORD' scp -o StrictHostKeyChecking=no -P $SSH_PORT"
fi

# 函数：执行远程命令
remote_exec() {
    if [ -n "$SSH_PASSWORD" ] && command -v sshpass &> /dev/null; then
        sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -p $SSH_PORT $SSH_USER@$SERVER_IP "$@"
    else
        ssh -p $SSH_PORT $SSH_USER@$SERVER_IP "$@"
    fi
}

# 函数：上传文件
remote_copy() {
    local src=$1
    local dst=$2
    if [ -n "$SSH_PASSWORD" ] && command -v sshpass &> /dev/null; then
        sshpass -p "$SSH_PASSWORD" scp -o StrictHostKeyChecking=no -P $SSH_PORT -r "$src" $SSH_USER@$SERVER_IP:"$dst"
    else
        scp -P $SSH_PORT -r "$src" $SSH_USER@$SERVER_IP:"$dst"
    fi
}

echo -e "${YELLOW}步骤1: 测试服务器连接...${NC}"
if remote_exec "echo '连接成功'"; then
    echo -e "${GREEN}✓ 服务器连接成功${NC}"
else
    echo -e "${RED}✗ 服务器连接失败${NC}"
    echo "请检查："
    echo "  1. 服务器IP和端口是否正确"
    echo "  2. 防火墙是否允许SSH连接"
    echo "  3. 密码是否正确"
    exit 1
fi

echo -e "${YELLOW}步骤2: 检查并初始化服务器环境...${NC}"
remote_exec "bash -s" << 'REMOTE_INIT'
# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "Docker未安装，开始安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Docker Compose未安装，开始安装..."
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 创建目录
mkdir -p /opt/invoice-app
mkdir -p /opt/invoice-app/uploads
mkdir -p /opt/invoice-app/data/postgres
mkdir -p /opt/invoice-app/data/redis
mkdir -p /opt/invoice-app/backups
mkdir -p /opt/traefik-public

# 创建Docker网络
docker network create traefik-public 2>/dev/null || true

echo "服务器环境检查完成"
REMOTE_INIT

echo -e "${GREEN}✓ 服务器环境准备完成${NC}"

echo -e "${YELLOW}步骤3: 上传项目文件到服务器...${NC}"
# 创建临时目录用于打包
TEMP_DIR=$(mktemp -d)
echo "临时目录: $TEMP_DIR"

# 复制必要文件到临时目录
mkdir -p "$TEMP_DIR/invoice-app"
cp -r scripts "$TEMP_DIR/invoice-app/"
cp docker-compose.yml "$TEMP_DIR/invoice-app/"
cp docker-compose.production.yml "$TEMP_DIR/invoice-app/" 2>/dev/null || true
cp docker-compose.traefik.yml "$TEMP_DIR/invoice-app/" 2>/dev/null || true
cp -r backend "$TEMP_DIR/invoice-app/" 2>/dev/null || true
cp -r frontend "$TEMP_DIR/invoice-app/" 2>/dev/null || true

# 或者直接在服务器上克隆
echo "在服务器上克隆Git仓库..."
remote_exec "cd /opt && rm -rf invoice-app && git clone $GIT_REPO invoice-app" || {
    echo -e "${YELLOW}Git克隆失败，尝试上传文件...${NC}"
    remote_copy "$TEMP_DIR/invoice-app" /opt/
}

# 清理临时目录
rm -rf "$TEMP_DIR"

echo -e "${GREEN}✓ 项目文件已上传${NC}"

echo -e "${YELLOW}步骤4: 配置环境变量...${NC}"
# 生成安全密钥
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
POSTGRES_PASSWORD_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)

# 创建.env文件
remote_exec "bash -s" << REMOTE_ENV
cd /opt/invoice-app

# 从模板创建.env文件
if [ -f scripts/aliyun/.env.production.template ]; then
    cp scripts/aliyun/.env.production.template .env
else
    # 创建基本.env文件
    cat > .env << EOF
# 项目配置
PROJECT_NAME=智能发票识别系统
ENVIRONMENT=production
DOMAIN=8.145.33.61
STACK_NAME=invoice-app-production
FRONTEND_HOST=dashboard.8.145.33.61

# Docker镜像配置（需要后续配置）
DOCKER_IMAGE_BACKEND=your-registry.cn-hangzhou.aliyuncs.com/invoice/backend
DOCKER_IMAGE_FRONTEND=your-registry.cn-hangzhou.aliyuncs.com/invoice/frontend
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
BACKEND_CORS_ORIGINS=http://8.145.33.61:5173,http://localhost:5173

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
fi

echo "环境变量文件已创建"
cat .env | head -20
REMOTE_ENV

echo -e "${GREEN}✓ 环境变量配置完成${NC}"

echo -e "${YELLOW}步骤5: 检查Docker镜像配置...${NC}"
echo -e "${BLUE}提示: 如果镜像尚未构建，请先运行构建脚本${NC}"
echo "构建镜像命令:"
echo "  export REGISTRY=your-registry.cn-hangzhou.aliyuncs.com"
echo "  export NAMESPACE=invoice"
echo "  bash scripts/aliyun/build-and-push.sh v1.0.0"

read -p "是否已构建并推送镜像？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}请先构建镜像，然后重新运行此脚本${NC}"
    exit 0
fi

echo -e "${YELLOW}步骤6: 部署应用...${NC}"
remote_exec "cd /opt/invoice-app && chmod +x scripts/aliyun/*.sh && bash scripts/aliyun/deploy-production.sh"

echo -e "${GREEN}=========================================="
echo "部署完成！"
echo "==========================================${NC}"
echo "访问地址:"
echo "  前端: http://8.145.33.61:5173 (如果配置了Traefik则为 https://dashboard.8.145.33.61)"
echo "  API文档: http://8.145.33.61:8000/docs"
echo ""
echo "查看服务状态:"
echo "  ssh -p $SSH_PORT $SSH_USER@$SERVER_IP"
echo "  cd /opt/invoice-app"
echo "  docker compose -f docker-compose.yml -f docker-compose.production.yml ps"
echo "=========================================="

