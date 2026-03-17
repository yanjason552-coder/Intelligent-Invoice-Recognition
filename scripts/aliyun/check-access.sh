#!/bin/bash
# 检查访问配置和状态

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR=${APP_DIR:-/opt/invoice-app}

echo -e "${BLUE}=========================================="
echo "访问配置检查"
echo "==========================================${NC}"
echo ""

# 加载环境变量
if [ -f "$APP_DIR/.env" ]; then
    set -a
    source "$APP_DIR/.env" 2>/dev/null || true
    set +a
fi

echo -e "${BLUE}[1] 服务运行状态${NC}"

# 检查Docker服务
if systemctl is-active --quiet docker; then
    echo -e "${GREEN}✓ Docker服务: 运行中${NC}"
else
    echo -e "${RED}✗ Docker服务: 未运行${NC}"
fi

# 检查Traefik
if docker ps | grep -q traefik; then
    echo -e "${GREEN}✓ Traefik: 运行中${NC}"
    TRAEFIK_CONTAINER=$(docker ps | grep traefik | awk '{print $1}')
    echo "  容器ID: $TRAEFIK_CONTAINER"
else
    echo -e "${YELLOW}⚠ Traefik: 未运行${NC}"
    echo "  提示: Traefik需要先部署才能通过域名访问"
fi

# 检查应用服务
if [ -f "$APP_DIR/docker-compose.yml" ]; then
    cd "$APP_DIR"
    COMPOSE_FILES="-f docker-compose.yml"
    if [ -f "docker-compose.production.yml" ]; then
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.production.yml"
    fi
    
    echo ""
    echo -e "${BLUE}[2] 应用容器状态${NC}"
    if docker compose $COMPOSE_FILES ps 2>/dev/null | grep -q "Up"; then
        docker compose $COMPOSE_FILES ps
    else
        echo -e "${YELLOW}⚠ 应用服务: 未运行${NC}"
        echo "  提示: 需要先运行部署脚本"
    fi
else
    echo -e "${YELLOW}⚠ docker-compose.yml 文件不存在${NC}"
fi

echo ""
echo -e "${BLUE}[3] 端口监听状态${NC}"

# 检查80端口
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo -e "${GREEN}✓ 80端口: 监听中${NC}"
    netstat -tlnp 2>/dev/null | grep ":80 " | head -1
else
    echo -e "${YELLOW}⚠ 80端口: 未监听${NC}"
fi

# 检查443端口
if netstat -tlnp 2>/dev/null | grep -q ":443 "; then
    echo -e "${GREEN}✓ 443端口: 监听中${NC}"
    netstat -tlnp 2>/dev/null | grep ":443 " | head -1
else
    echo -e "${YELLOW}⚠ 443端口: 未监听${NC}"
fi

# 检查5173端口（开发端口）
if netstat -tlnp 2>/dev/null | grep -q ":5173 "; then
    echo -e "${YELLOW}⚠ 5173端口: 监听中（这是开发端口）${NC}"
    netstat -tlnp 2>/dev/null | grep ":5173 " | head -1
else
    echo -e "${BLUE}○ 5173端口: 未监听（正常，生产环境不使用此端口）${NC}"
fi

echo ""
echo -e "${BLUE}[4] 访问地址${NC}"

if [ -n "$DOMAIN" ]; then
    echo ""
    echo "根据当前配置，应该通过以下地址访问："
    echo ""
    
    if docker ps | grep -q traefik; then
        echo -e "${GREEN}✓ 使用Traefik访问（推荐）:${NC}"
        echo "  前端: http://dashboard.$DOMAIN"
        echo "  前端(HTTPS): https://dashboard.$DOMAIN"
        echo "  API文档: http://api.$DOMAIN/docs"
        echo "  API文档(HTTPS): https://api.$DOMAIN/docs"
        echo "  数据库管理: http://adminer.$DOMAIN"
        echo ""
        echo "  注意: 如果使用IP地址，需要配置hosts文件或DNS解析"
    else
        echo -e "${YELLOW}⚠ Traefik未运行，无法通过域名访问${NC}"
        echo ""
    fi
    
    # 检查是否有直接端口映射
    if [ -f "$APP_DIR/docker-compose.yml" ]; then
        cd "$APP_DIR"
        if docker compose ps 2>/dev/null | grep -q frontend; then
            FRONTEND_PORTS=$(docker compose ps frontend 2>/dev/null | grep -oP '\d+->\d+' | head -1 || echo "")
            if [ -n "$FRONTEND_PORTS" ]; then
                echo -e "${YELLOW}⚠ 直接端口访问（如果配置了端口映射）:${NC}"
                echo "  前端: http://$DOMAIN:${FRONTEND_PORTS%%->*}"
            fi
        fi
    fi
else
    echo -e "${YELLOW}⚠ DOMAIN未配置${NC}"
fi

echo ""
echo -e "${BLUE}[5] 配置建议${NC}"
echo ""

if ! docker ps | grep -q traefik; then
    echo -e "${YELLOW}1. 需要先部署Traefik:${NC}"
    echo "   - 如果使用IP访问，可以修改Traefik配置使用IP而不是域名"
    echo "   - 或者直接映射容器端口到主机端口"
fi

if [ -f "$APP_DIR/docker-compose.yml" ] && ! docker compose -f "$APP_DIR/docker-compose.yml" ps 2>/dev/null | grep -q "Up"; then
    echo -e "${YELLOW}2. 需要部署应用服务:${NC}"
    echo "   bash $APP_DIR/scripts/aliyun/deploy-production.sh"
fi

echo ""
echo -e "${BLUE}=========================================="
echo "检查完成"
echo "==========================================${NC}"
