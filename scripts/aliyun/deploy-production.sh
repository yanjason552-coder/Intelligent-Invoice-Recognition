#!/bin/bash
# 生产环境部署脚本
# 用于在阿里云ECS上部署应用

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
APP_DIR=${APP_DIR:-/opt/invoice-app}
TRAEFIK_DIR=${TRAEFIK_DIR:-/opt/traefik-public}
DOMAIN=${DOMAIN:-your-domain.com}
STACK_NAME=${STACK_NAME:-invoice-app-production}
TAG=${TAG:-latest}

echo -e "${GREEN}=========================================="
echo "开始部署生产环境"
echo "==========================================${NC}"
echo "应用目录: $APP_DIR"
echo "Traefik目录: $TRAEFIK_DIR"
echo "域名: $DOMAIN"
echo "堆栈名称: $STACK_NAME"
echo "镜像标签: $TAG"
echo ""

# 检查是否以root用户运行
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}错误: 请以root用户运行此脚本${NC}"
    exit 1
fi

# 检查环境变量文件
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${RED}错误: .env 文件不存在于 $APP_DIR${NC}"
    echo "请先创建 .env 文件，参考 scripts/aliyun/.env.production.template"
    exit 1
fi

# 加载环境变量
echo -e "${YELLOW}加载环境变量...${NC}"
set -a
source $APP_DIR/.env
set +a

# 检查必要的环境变量
required_vars=("DOMAIN" "STACK_NAME" "SECRET_KEY" "POSTGRES_PASSWORD" "FIRST_SUPERUSER" "FIRST_SUPERUSER_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}错误: 环境变量 $var 未设置${NC}"
        exit 1
    fi
done

# 部署Traefik（如果尚未部署）
if [ ! -f "$TRAEFIK_DIR/docker-compose.yml" ]; then
    echo -e "${YELLOW}部署Traefik...${NC}"
    mkdir -p $TRAEFIK_DIR
    
    # 复制Traefik配置文件
    if [ -f "$APP_DIR/docker-compose.traefik.yml" ]; then
        cp $APP_DIR/docker-compose.traefik.yml $TRAEFIK_DIR/
    else
        echo -e "${RED}错误: docker-compose.traefik.yml 文件不存在${NC}"
        exit 1
    fi
    
    cd $TRAEFIK_DIR
    
    # 设置Traefik环境变量
    export DOMAIN=$DOMAIN
    export USERNAME=${TRAEFIK_USERNAME:-admin}
    export PASSWORD=${TRAEFIK_PASSWORD:-changethis}
    export HASHED_PASSWORD=$(openssl passwd -apr1 "$PASSWORD")
    export EMAIL=${TRAEFIK_EMAIL:-admin@$DOMAIN}
    
    echo "Traefik配置:"
    echo "  域名: $DOMAIN"
    echo "  用户名: $USERNAME"
    echo "  邮箱: $EMAIL"
    
    docker compose -f docker-compose.traefik.yml up -d
    
    echo -e "${GREEN}Traefik部署完成${NC}"
    sleep 5
else
    echo -e "${BLUE}Traefik已部署，跳过${NC}"
fi

# 部署应用
echo -e "${YELLOW}部署应用服务...${NC}"
cd $APP_DIR

# 检查docker-compose.yml是否存在
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}错误: docker-compose.yml 文件不存在于 $APP_DIR${NC}"
    exit 1
fi

# 检查是否有生产环境配置文件
COMPOSE_FILES="-f docker-compose.yml"
if [ -f "docker-compose.production.yml" ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.production.yml"
    echo -e "${BLUE}使用生产环境配置${NC}"
fi

# 拉取最新镜像
echo -e "${YELLOW}拉取最新镜像...${NC}"
docker compose $COMPOSE_FILES pull

# 停止旧容器（如果存在）
echo -e "${YELLOW}停止旧容器...${NC}"
docker compose $COMPOSE_FILES down || true

# 启动新容器
echo -e "${YELLOW}启动新容器...${NC}"
docker compose $COMPOSE_FILES up -d

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 15

# 检查服务状态
echo -e "${YELLOW}检查服务状态...${NC}"
docker compose $COMPOSE_FILES ps

# 检查服务健康状态
echo -e "${YELLOW}检查服务健康状态...${NC}"
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker compose $COMPOSE_FILES ps | grep -q "Up"; then
        echo -e "${GREEN}服务正在运行...${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "等待服务启动... ($attempt/$max_attempts)"
    sleep 2
done

# 显示服务日志（最近50行）
echo -e "${YELLOW}最近的服务日志:${NC}"
docker compose $COMPOSE_FILES logs --tail=50

echo ""
echo -e "${GREEN}=========================================="
echo "部署完成！"
echo "==========================================${NC}"
echo "访问地址:"
echo "  前端: https://dashboard.$DOMAIN"
echo "  API文档: https://api.$DOMAIN/docs"
echo "  数据库管理: https://adminer.$DOMAIN"
echo "  Traefik面板: https://traefik.$DOMAIN"
echo ""
echo "查看日志: docker compose $COMPOSE_FILES logs -f"
echo "重启服务: docker compose $COMPOSE_FILES restart"
echo "=========================================="

