#!/bin/bash
# 部署状态检查脚本
# 全面检查当前部署状态

set -e

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

# 加载环境变量
if [ -f "$APP_DIR/.env" ]; then
    set -a
    source "$APP_DIR/.env" 2>/dev/null || true
    set +a
fi

# 1. Docker服务状态
echo -e "${BLUE}[1] Docker服务状态${NC}"
if systemctl is-active --quiet docker; then
    echo -e "${GREEN}✓ Docker服务: 运行中${NC}"
    echo "  版本: $(docker --version)"
else
    echo -e "${RED}✗ Docker服务: 未运行${NC}"
fi

if docker compose version &> /dev/null 2>&1 || docker-compose --version &> /dev/null 2>&1; then
    if docker compose version &> /dev/null 2>&1; then
        echo "  Compose版本: $(docker compose version)"
    else
        echo "  Compose版本: $(docker-compose --version)"
    fi
fi
echo ""

# 2. Docker镜像源状态
echo -e "${BLUE}[2] Docker镜像源配置${NC}"
if [ -f /etc/docker/daemon.json ]; then
    if docker info 2>/dev/null | grep -q "Registry Mirrors"; then
        docker info 2>/dev/null | grep -A 5 "Registry Mirrors"
    else
        echo -e "${YELLOW}⚠ 无法获取镜像源信息${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Docker配置文件不存在${NC}"
fi
echo ""

# 3. Traefik状态
echo -e "${BLUE}[3] Traefik服务状态${NC}"
if docker ps | grep -q traefik; then
    echo -e "${GREEN}✓ Traefik: 运行中${NC}"
    TRAEFIK_CONTAINER=$(docker ps | grep traefik | awk '{print $1}')
    echo "  容器ID: $TRAEFIK_CONTAINER"
    echo "  状态: $(docker ps | grep traefik | awk '{print $7, $8, $9, $10}')"
    
    # 检查Traefik日志中的错误
    echo ""
    echo "  最近日志（最后5行）:"
    docker logs --tail 5 $TRAEFIK_CONTAINER 2>/dev/null | sed 's/^/    /' || echo "    无法获取日志"
else
    echo -e "${YELLOW}⚠ Traefik: 未运行${NC}"
fi
echo ""

# 4. 应用服务状态
echo -e "${BLUE}[4] 应用服务状态${NC}"
if [ -f "$APP_DIR/docker-compose.yml" ]; then
    cd "$APP_DIR"
    COMPOSE_FILES="-f docker-compose.yml"
    if [ -f "docker-compose.production.yml" ]; then
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.production.yml"
    fi
    
    if docker compose $COMPOSE_FILES ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}✓ 应用服务: 运行中${NC}"
        echo ""
        docker compose $COMPOSE_FILES ps
        
        # 检查各个服务的健康状态
        echo ""
        echo "  服务健康状态:"
        services=("db" "redis" "backend" "frontend" "prestart")
        for service in "${services[@]}"; do
            if docker compose $COMPOSE_FILES ps 2>/dev/null | grep -q "$service"; then
                CONTAINER_ID=$(docker compose $COMPOSE_FILES ps -q $service 2>/dev/null | head -1)
                if [ -n "$CONTAINER_ID" ]; then
                    HEALTH=$(docker inspect $CONTAINER_ID 2>/dev/null | grep -oP '"Health".*?"Status":"\K[^"]+' || echo "no-healthcheck")
                    STATUS=$(docker compose $COMPOSE_FILES ps $service 2>/dev/null | grep "$service" | awk '{print $4, $5, $6, $7, $8, $9, $10}')
                    if [ "$HEALTH" = "healthy" ]; then
                        echo -e "    ${GREEN}✓${NC} $service: 健康 - $STATUS"
                    elif [ "$HEALTH" = "starting" ]; then
                        echo -e "    ${YELLOW}⚠${NC} $service: 启动中 - $STATUS"
                    elif [ "$HEALTH" = "unhealthy" ]; then
                        echo -e "    ${RED}✗${NC} $service: 不健康 - $STATUS"
                    else
                        echo -e "    ${BLUE}○${NC} $service: $STATUS"
                    fi
                fi
            fi
        done
    else
        echo -e "${YELLOW}⚠ 应用服务: 未运行${NC}"
        echo ""
        echo "  尝试查看所有容器状态:"
        docker compose $COMPOSE_FILES ps -a 2>/dev/null || echo "    无法获取容器状态"
    fi
else
    echo -e "${YELLOW}⚠ docker-compose.yml 文件不存在${NC}"
fi
echo ""

# 5. 端口监听状态
echo -e "${BLUE}[5] 端口监听状态${NC}"
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo -e "${GREEN}✓ 80端口: 监听中${NC}"
    netstat -tlnp 2>/dev/null | grep ":80 " | head -1 | sed 's/^/  /'
else
    echo -e "${YELLOW}⚠ 80端口: 未监听${NC}"
fi

if netstat -tlnp 2>/dev/null | grep -q ":443 "; then
    echo -e "${GREEN}✓ 443端口: 监听中${NC}"
    netstat -tlnp 2>/dev/null | grep ":443 " | head -1 | sed 's/^/  /'
else
    echo -e "${YELLOW}⚠ 443端口: 未监听${NC}"
fi

if netstat -tlnp 2>/dev/null | grep -q ":5173 "; then
    echo -e "${YELLOW}⚠ 5173端口: 监听中（开发端口）${NC}"
    netstat -tlnp 2>/dev/null | grep ":5173 " | head -1 | sed 's/^/  /'
fi
echo ""

# 6. 磁盘空间
echo -e "${BLUE}[6] 磁盘空间${NC}"
df -h / | tail -1 | awk '{printf "  根目录: 使用 %s, 可用 %s, 使用率 %s\n", $3, $4, $5}'
if [ -d "$APP_DIR/data" ]; then
    du -sh "$APP_DIR/data" 2>/dev/null | awk '{print "  数据目录: " $1}'
fi
if [ -d "$APP_DIR/uploads" ]; then
    du -sh "$APP_DIR/uploads" 2>/dev/null | awk '{print "  上传目录: " $1}'
fi
echo ""

# 7. 访问地址
echo -e "${BLUE}[7] 访问地址${NC}"
if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "your-domain.com" ]; then
    echo ""
    if docker ps | grep -q traefik; then
        echo -e "${GREEN}使用Traefik访问（推荐）:${NC}"
        echo "  前端: https://dashboard.$DOMAIN"
        echo "  API文档: https://api.$DOMAIN/docs"
        echo "  健康检查: https://api.$DOMAIN/api/v1/utils/health-check/"
        echo "  数据库管理: https://adminer.$DOMAIN"
        echo "  Traefik面板: https://traefik.$DOMAIN"
    else
        echo -e "${YELLOW}Traefik未运行，无法通过域名访问${NC}"
    fi
    
    echo ""
    echo "  直接IP访问（如果配置了端口映射）:"
    echo "  http://$DOMAIN"
else
    echo -e "${YELLOW}⚠ DOMAIN未配置或使用默认值${NC}"
    echo "  当前DOMAIN: ${DOMAIN:-未设置}"
fi
echo ""

# 8. 最近的错误日志
echo -e "${BLUE}[8] 最近的错误日志（最后10行）${NC}"
if [ -f "$APP_DIR/docker-compose.yml" ]; then
    cd "$APP_DIR"
    COMPOSE_FILES="-f docker-compose.yml"
    if [ -f "docker-compose.production.yml" ]; then
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.production.yml"
    fi
    
    echo ""
    echo -e "${YELLOW}后端日志:${NC}"
    docker compose $COMPOSE_FILES logs --tail=10 backend 2>/dev/null | grep -i error || echo "  无错误"
    
    echo ""
    echo -e "${YELLOW}前端日志:${NC}"
    docker compose $COMPOSE_FILES logs --tail=10 frontend 2>/dev/null | grep -i error || echo "  无错误"
    
    echo ""
    echo -e "${YELLOW}数据库日志:${NC}"
    docker compose $COMPOSE_FILES logs --tail=10 db 2>/dev/null | grep -i error || echo "  无错误"
fi
echo ""

# 9. 环境变量检查
echo -e "${BLUE}[9] 关键环境变量${NC}"
if [ -f "$APP_DIR/.env" ]; then
    echo "  DOMAIN: ${DOMAIN:-未设置}"
    echo "  ENVIRONMENT: ${ENVIRONMENT:-未设置}"
    echo "  POSTGRES_SERVER: ${POSTGRES_SERVER:-未设置}"
    echo "  POSTGRES_DB: ${POSTGRES_DB:-未设置}"
    echo "  DOCKER_IMAGE_BACKEND: ${DOCKER_IMAGE_BACKEND:-未设置}"
    echo "  DOCKER_IMAGE_FRONTEND: ${DOCKER_IMAGE_FRONTEND:-未设置}"
    echo "  TAG: ${TAG:-未设置}"
else
    echo -e "${YELLOW}⚠ .env文件不存在${NC}"
fi
echo ""

# 总结
echo -e "${BLUE}=========================================="
echo "检查完成"
echo "==========================================${NC}"
echo ""

# 提供建议
if ! docker ps | grep -q traefik; then
    echo -e "${YELLOW}建议: 部署Traefik以启用域名访问${NC}"
fi

if [ -f "$APP_DIR/docker-compose.yml" ] && ! docker compose -f "$APP_DIR/docker-compose.yml" ps 2>/dev/null | grep -q "Up"; then
    echo -e "${YELLOW}建议: 运行部署脚本启动应用服务${NC}"
    echo "  bash $APP_DIR/scripts/aliyun/deploy-production.sh"
fi

echo ""
echo "常用命令:"
echo "  查看所有日志: docker compose -f docker-compose.yml -f docker-compose.production.yml logs -f"
echo "  重启服务: docker compose -f docker-compose.yml -f docker-compose.production.yml restart"
echo "  停止服务: docker compose -f docker-compose.yml -f docker-compose.production.yml down"
echo ""
