#!/bin/bash
# 阿里云ECS服务器初始化脚本
# 用于初始化服务器环境，安装Docker和Docker Compose

set -e

echo "=========================================="
echo "开始初始化阿里云ECS服务器..."
echo "=========================================="

# 更新系统
echo "更新系统包..."
apt-get update && apt-get upgrade -y

# 安装必要的工具
echo "安装必要工具..."
apt-get install -y curl wget git vim openssl ufw

# 安装Docker
echo "安装Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "Docker安装完成"
else
    echo "Docker已安装，跳过"
fi

# 安装Docker Compose
echo "安装Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose安装完成"
else
    echo "Docker Compose已安装，跳过"
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p /opt/invoice-app
mkdir -p /opt/invoice-app/uploads
mkdir -p /opt/invoice-app/data/postgres
mkdir -p /opt/invoice-app/data/redis
mkdir -p /opt/invoice-app/backups
mkdir -p /opt/invoice-app/scripts/aliyun
mkdir -p /opt/traefik-public

# 创建Docker网络（如果不存在）
echo "创建Docker网络..."
if ! docker network ls | grep -q traefik-public; then
    docker network create traefik-public
    echo "Docker网络 traefik-public 创建完成"
else
    echo "Docker网络 traefik-public 已存在，跳过"
fi

# 设置防火墙规则
echo "配置防火墙..."
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 22/tcp
    echo "防火墙规则已配置（未启用，请手动启用：ufw enable）"
else
    echo "ufw未安装，跳过防火墙配置"
fi

# 设置Docker开机自启
echo "设置Docker开机自启..."
systemctl enable docker
systemctl start docker

echo "=========================================="
echo "服务器初始化完成！"
echo "=========================================="
echo "下一步："
echo "1. 配置环境变量文件 /opt/invoice-app/.env"
echo "2. 上传项目文件到 /opt/invoice-app"
echo "3. 运行部署脚本 scripts/aliyun/deploy-production.sh"
echo "=========================================="

