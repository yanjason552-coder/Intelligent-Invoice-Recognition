#!/bin/bash
# 部署准备脚本
# 在服务器上运行，准备部署所需的所有配置

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR=${APP_DIR:-/opt/invoice-app}

echo -e "${BLUE}=========================================="
echo "部署准备脚本"
echo "==========================================${NC}"
echo ""

# 检查是否以root用户运行
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}错误: 请以root用户运行此脚本${NC}"
    exit 1
fi

# 1. 创建必要的目录
echo -e "${YELLOW}[1] 创建必要的目录...${NC}"
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/uploads"
mkdir -p "$APP_DIR/data/postgres"
mkdir -p "$APP_DIR/data/redis"
mkdir -p "$APP_DIR/backups"
mkdir -p "$APP_DIR/scripts/aliyun"
mkdir -p /opt/traefik-public
echo -e "${GREEN}✓ 目录创建完成${NC}"
echo ""

# 2. 创建Docker网络
echo -e "${YELLOW}[2] 创建Docker网络...${NC}"
if ! docker network ls | grep -q traefik-public; then
    docker network create traefik-public
    echo -e "${GREEN}✓ Docker网络 traefik-public 创建完成${NC}"
else
    echo -e "${BLUE}✓ Docker网络 traefik-public 已存在${NC}"
fi
echo ""

# 3. 检查并创建 .env 文件
echo -e "${YELLOW}[3] 检查环境变量文件...${NC}"
if [ ! -f "$APP_DIR/.env" ]; then
    if [ -f "$APP_DIR/scripts/aliyun/.env.production.template" ]; then
        cp "$APP_DIR/scripts/aliyun/.env.production.template" "$APP_DIR/.env"
        echo -e "${GREEN}✓ 已从模板创建 .env 文件${NC}"
        echo -e "${YELLOW}⚠ 请编辑 $APP_DIR/.env 文件，配置所有必需的环境变量${NC}"
    else
        echo -e "${YELLOW}⚠ .env 文件不存在，模板文件也不存在${NC}"
        echo -e "${YELLOW}  请手动创建 .env 文件${NC}"
    fi
else
    echo -e "${BLUE}✓ .env 文件已存在${NC}"
fi
echo ""

# 4. 生成安全密钥（如果.env中存在changethis）
if [ -f "$APP_DIR/.env" ]; then
    echo -e "${YELLOW}[4] 检查并生成安全密钥...${NC}"
    
    # 加载环境变量
    set -a
    source "$APP_DIR/.env" 2>/dev/null || true
    set +a
    
    UPDATED=false
    
    # 检查并生成SECRET_KEY
    if [ "$SECRET_KEY" = "changethis" ] || [ -z "$SECRET_KEY" ]; then
        NEW_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
        sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$NEW_SECRET_KEY|" "$APP_DIR/.env"
        echo -e "${GREEN}✓ 已生成新的 SECRET_KEY${NC}"
        UPDATED=true
    fi
    
    # 检查并生成POSTGRES_PASSWORD
    if [ "$POSTGRES_PASSWORD" = "changethis" ] || [ -z "$POSTGRES_PASSWORD" ]; then
        NEW_POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
        sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$NEW_POSTGRES_PASSWORD|" "$APP_DIR/.env"
        echo -e "${GREEN}✓ 已生成新的 POSTGRES_PASSWORD${NC}"
        UPDATED=true
    fi
    
    if [ "$UPDATED" = false ]; then
        echo -e "${BLUE}✓ 密钥已配置${NC}"
    fi
    echo ""
fi

# 5. 配置Docker镜像源（如果未配置）
echo -e "${YELLOW}[5] 检查Docker镜像源配置...${NC}"
if [ ! -f /etc/docker/daemon.json ] || ! grep -q "registry-mirrors" /etc/docker/daemon.json 2>/dev/null; then
    echo -e "${YELLOW}⚠ Docker镜像源未配置，建议配置以加速镜像下载${NC}"
    echo -e "${YELLOW}  可以运行以下命令配置：${NC}"
    echo "  bash ~/scripts/configure_docker_mirrors.sh"
else
    echo -e "${GREEN}✓ Docker镜像源已配置${NC}"
fi
echo ""

# 6. 检查防火墙配置
echo -e "${YELLOW}[6] 检查防火墙配置...${NC}"
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        if ufw status | grep -q "80/tcp" && ufw status | grep -q "443/tcp"; then
            echo -e "${GREEN}✓ 防火墙规则已配置${NC}"
        else
            echo -e "${YELLOW}⚠ 防火墙已启用，但80或443端口未开放${NC}"
            echo -e "${YELLOW}  运行以下命令开放端口：${NC}"
            echo "  ufw allow 80/tcp"
            echo "  ufw allow 443/tcp"
        fi
    else
        echo -e "${BLUE}✓ 防火墙未启用（可选）${NC}"
    fi
else
    echo -e "${BLUE}✓ ufw未安装（可选）${NC}"
fi
echo ""

echo -e "${GREEN}=========================================="
echo "部署准备完成！"
echo "==========================================${NC}"
echo ""
echo "下一步："
echo "1. 编辑环境变量文件: vim $APP_DIR/.env"
echo "2. 运行部署检查: bash $APP_DIR/scripts/aliyun/check-deployment.sh"
echo "3. 运行部署脚本: bash $APP_DIR/scripts/aliyun/deploy-production.sh"
echo ""
