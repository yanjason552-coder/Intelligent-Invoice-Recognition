#!/bin/bash
# 部署状态检查脚本
# 检查当前部署状态和运行情况

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR=${APP_DIR:-/opt/invoice-app}

echo -e "${BLUE}=========================================="
echo "部署状态检查"
echo "==========================================${NC}"
echo ""

# 1. 检查Docker服务状态
echo -e "${BLUE}[1] Docker服务状态${NC}"
if systemctl is-active --quiet docker; then
    echo -e "${GREEN}✓ Docker服务: 运行中${NC}"
else
    echo -e "${RED}✗ Docker服务: 未运行${NC}"
fi
echo ""

# 2. 检查Traefik状态
echo -e "${BLUE}[2] Traefik服务状态${NC}"
if docker ps | grep -q traefik; then
    TRAEFIK_CONTAINER=$(docker ps | grep traefik | awk '{print $1}')
    echo -e "${GREEN}✓ Traefik: 运行中 (容器ID: $TRAEFIK_CONTAINER)${NC}"
    docker ps | grep traefik
else
    echo -e "${YELLOW}⚠ Traefik: 未运行${NC}"
fi
echo ""

# 3. 检查应用服务状态
echo -e "${BLUE}[3] 应用服务状态${NC}"
if [ -f "$APP_DIR/.env" ]; then
    cd "$APP_DIR"
    set -a
    source .env 2>/dev/null || true
    set +a
    
    COMPOSE_FILES="-f docker-compose.yml"
    if [ -f "docker-compose.production.yml" ]; then
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.production.yml"
    fi
    
    if docker compose $COMPOSE_FILES ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}✓ 应用服务: 运行中${NC}"
        docker compose $COMPOSE_FILES ps
    else
        echo -e "${YELLOW}⚠ 应用服务: 未运行或部分运行${NC}"
        docker compose $COMPOSE_FILES ps 2>/dev/null || echo "无法获取服务状态"
    fi
else
    echo -e "${YELLOW}⚠ 无法检查应用服务状态（.env文件不存在）${NC}"
fi
echo ""

# 4. 检查容器健康状态
echo -e "${BLUE}[4] 容器健康状态${NC}"
if [ -f "$APP_DIR/.env" ]; then
    cd "$APP_DIR"
    set -a
    source .env 2>/dev/null || true
    set +a
    
    COMPOSE_FILES="-f docker-compose.yml"
    if [ -f "docker-compose.production.yml" ]; then
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.production.yml"
    fi
    
    # 检查各个服务的健康状态
    services=("db" "redis" "backend" "frontend")
    for service in "${services[@]}"; do
        if docker compose $COMPOSE_FILES ps 2>/dev/null | grep -q "$service"; then
            HEALTH=$(docker inspect $(docker compose $COMPOSE_FILES ps -q $service 2>/dev/null | head -1) 2>/dev/null | grep -o '"Health".*"Status":"[^"]*"' | grep -o '"Status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
            if [ "$HEALTH" = "healthy" ]; then
                echo -e "${GREEN}✓ $service: 健康${NC}"
            elif [ "$HEALTH" = "starting" ]; then
                echo -e "${YELLOW}⚠ $service: 启动中${NC}"
            elif [ "$HEALTH" = "unhealthy" ]; then
                echo -e "${RED}✗ $service: 不健康${NC}"
            else
                echo -e "${BLUE}○ $service: 状态未知${NC}"
            fi
        fi
    done
fi
echo ""

# 5. 检查端口监听
echo -e "${BLUE}[5] 端口监听状态${NC}"
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo -e "${GREEN}✓ 80端口: 监听中${NC}"
    netstat -tlnp 2>/dev/null | grep ":80 "
else
    echo -e "${YELLOW}⚠ 80端口: 未监听${NC}"
fi

if netstat -tlnp 2>/dev/null | grep -q ":443 "; then
    echo -e "${GREEN}✓ 443端口: 监听中${NC}"
    netstat -tlnp 2>/dev/null | grep ":443 "
else
    echo -e "${YELLOW}⚠ 443端口: 未监听${NC}"
fi
echo ""

# 6. 检查磁盘空间
echo -e "${BLUE}[6] 磁盘空间${NC}"
df -h / | tail -1 | awk '{print "根目录: 使用 "$3", 可用 "$4", 使用率 "$5}'
if [ -d "$APP_DIR/data" ]; then
    du -sh "$APP_DIR/data" 2>/dev/null | awk '{print "数据目录: "$1}'
fi
echo ""

# 7. 检查最近的日志错误
echo -e "${BLUE}[7] 最近的错误日志（最后10行）${NC}"
if [ -f "$APP_DIR/.env" ]; then
    cd "$APP_DIR"
    set -a
    source .env 2>/dev/null || true
    set +a
    
    COMPOSE_FILES="-f docker-compose.yml"
    if [ -f "docker-compose.production.yml" ]; then
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.production.yml"
    fi
    
    echo -e "${YELLOW}后端日志:${NC}"
    docker compose $COMPOSE_FILES logs --tail=10 backend 2>/dev/null | grep -i error || echo "无错误"
    echo ""
    echo -e "${YELLOW}前端日志:${NC}"
    docker compose $COMPOSE_FILES logs --tail=10 frontend 2>/dev/null | grep -i error || echo "无错误"
fi
echo ""

# 8. 检查访问地址
echo -e "${BLUE}[8] 访问地址${NC}"
if [ -f "$APP_DIR/.env" ]; then
    set -a
    source "$APP_DIR/.env" 2>/dev/null || true
    set +a
    
    if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "your-domain.com" ]; then
        echo "前端: https://dashboard.$DOMAIN"
        echo "API文档: https://api.$DOMAIN/docs"
        echo "数据库管理: https://adminer.$DOMAIN"
        echo "Traefik面板: https://traefik.$DOMAIN"
    else
        echo -e "${YELLOW}⚠ 域名未配置或使用默认值${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 无法获取访问地址（.env文件不存在）${NC}"
fi
echo ""

echo -e "${BLUE}=========================================="
echo "检查完成"
echo "==========================================${NC}"
