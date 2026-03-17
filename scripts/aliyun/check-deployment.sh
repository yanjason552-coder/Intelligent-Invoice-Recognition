#!/bin/bash
# 部署前检查脚本
# 检查部署所需的所有配置和文件是否就绪

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_DIR=${APP_DIR:-/opt/invoice-app}
ERRORS=0
WARNINGS=0

echo -e "${BLUE}=========================================="
echo "部署前检查"
echo "==========================================${NC}"
echo ""

# 检查函数
check_item() {
    local name=$1
    local status=$2
    local message=$3
    
    if [ "$status" = "ok" ]; then
        echo -e "${GREEN}✓${NC} $name: $message"
    elif [ "$status" = "warning" ]; then
        echo -e "${YELLOW}⚠${NC} $name: $message"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${RED}✗${NC} $name: $message"
        ERRORS=$((ERRORS + 1))
    fi
}

# 1. 检查系统环境
echo -e "${BLUE}[1] 系统环境检查${NC}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    check_item "Docker" "ok" "$DOCKER_VERSION"
else
    check_item "Docker" "error" "未安装"
fi

if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version)
    else
        COMPOSE_VERSION=$(docker-compose --version)
    fi
    check_item "Docker Compose" "ok" "$COMPOSE_VERSION"
else
    check_item "Docker Compose" "error" "未安装"
fi

if docker network ls | grep -q traefik-public; then
    check_item "Docker网络" "ok" "traefik-public 已存在"
else
    check_item "Docker网络" "warning" "traefik-public 不存在（部署脚本会自动创建）"
fi

# 检查Docker镜像源配置
if [ -f /etc/docker/daemon.json ]; then
    if grep -q "registry-mirrors" /etc/docker/daemon.json; then
        check_item "Docker镜像源" "ok" "已配置"
    else
        check_item "Docker镜像源" "warning" "未配置镜像源（建议配置以加速下载）"
    fi
else
    check_item "Docker镜像源" "warning" "daemon.json 不存在"
fi

echo ""

# 2. 检查项目文件
echo -e "${BLUE}[2] 项目文件检查${NC}"
if [ -d "$APP_DIR" ]; then
    check_item "项目目录" "ok" "$APP_DIR 存在"
else
    check_item "项目目录" "error" "$APP_DIR 不存在"
fi

if [ -f "$APP_DIR/docker-compose.yml" ]; then
    check_item "docker-compose.yml" "ok" "存在"
else
    check_item "docker-compose.yml" "error" "不存在"
fi

if [ -f "$APP_DIR/docker-compose.production.yml" ]; then
    check_item "docker-compose.production.yml" "ok" "存在"
else
    check_item "docker-compose.production.yml" "warning" "不存在（可选）"
fi

if [ -f "$APP_DIR/docker-compose.traefik.yml" ]; then
    check_item "docker-compose.traefik.yml" "ok" "存在"
else
    check_item "docker-compose.traefik.yml" "error" "不存在"
fi

if [ -d "$APP_DIR/backend" ]; then
    check_item "backend目录" "ok" "存在"
else
    check_item "backend目录" "error" "不存在"
fi

if [ -d "$APP_DIR/frontend" ]; then
    check_item "frontend目录" "ok" "存在"
else
    check_item "frontend目录" "error" "不存在"
fi

echo ""

# 3. 检查环境变量文件
echo -e "${BLUE}[3] 环境变量检查${NC}"
if [ -f "$APP_DIR/.env" ]; then
    check_item ".env文件" "ok" "存在"
    
    # 加载环境变量
    set -a
    source "$APP_DIR/.env" 2>/dev/null || true
    set +a
    
    # 检查必需的环境变量
    required_vars=(
        "DOMAIN"
        "STACK_NAME"
        "SECRET_KEY"
        "POSTGRES_PASSWORD"
        "POSTGRES_USER"
        "POSTGRES_DB"
        "FIRST_SUPERUSER"
        "FIRST_SUPERUSER_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            check_item "$var" "error" "未设置"
        elif [ "${!var}" = "changethis" ] || [ "${!var}" = "your-domain.com" ]; then
            check_item "$var" "error" "使用默认值，需要修改"
        else
            if [ "$var" = "SECRET_KEY" ] || [ "$var" = "POSTGRES_PASSWORD" ]; then
                check_item "$var" "ok" "已设置（已隐藏）"
            else
                check_item "$var" "ok" "已设置: ${!var}"
            fi
        fi
    done
    
    # 检查可选但重要的环境变量
    if [ -z "$DOCKER_IMAGE_BACKEND" ]; then
        check_item "DOCKER_IMAGE_BACKEND" "warning" "未设置（如果使用镜像部署需要设置）"
    else
        check_item "DOCKER_IMAGE_BACKEND" "ok" "已设置: $DOCKER_IMAGE_BACKEND"
    fi
    
    if [ -z "$DOCKER_IMAGE_FRONTEND" ]; then
        check_item "DOCKER_IMAGE_FRONTEND" "warning" "未设置（如果使用镜像部署需要设置）"
    else
        check_item "DOCKER_IMAGE_FRONTEND" "ok" "已设置: $DOCKER_IMAGE_FRONTEND"
    fi
    
    if [ -z "$TAG" ]; then
        check_item "TAG" "warning" "未设置（默认使用 latest）"
    else
        check_item "TAG" "ok" "已设置: $TAG"
    fi
    
    if [ -z "$TRAEFIK_PASSWORD" ]; then
        check_item "TRAEFIK_PASSWORD" "warning" "未设置（Traefik管理密码）"
    else
        check_item "TRAEFIK_PASSWORD" "ok" "已设置"
    fi
    
    if [ -z "$TRAEFIK_EMAIL" ]; then
        check_item "TRAEFIK_EMAIL" "warning" "未设置（Let's Encrypt证书需要）"
    else
        check_item "TRAEFIK_EMAIL" "ok" "已设置: $TRAEFIK_EMAIL"
    fi
    
else
    check_item ".env文件" "error" "不存在"
    echo -e "${YELLOW}提示: 可以运行以下命令创建 .env 文件：${NC}"
    echo "  cp scripts/aliyun/.env.production.template .env"
    echo "  然后编辑 .env 文件配置必要的环境变量"
fi

echo ""

# 4. 检查目录权限
echo -e "${BLUE}[4] 目录权限检查${NC}"
if [ -d "$APP_DIR" ]; then
    if [ -w "$APP_DIR" ]; then
        check_item "项目目录权限" "ok" "可写"
    else
        check_item "项目目录权限" "error" "不可写"
    fi
fi

# 检查数据目录
data_dirs=(
    "/opt/invoice-app/uploads"
    "/opt/invoice-app/data/postgres"
    "/opt/invoice-app/data/redis"
    "/opt/invoice-app/backups"
)

for dir in "${data_dirs[@]}"; do
    if [ -d "$dir" ]; then
        check_item "$dir" "ok" "存在"
    else
        check_item "$dir" "warning" "不存在（部署脚本会自动创建）"
    fi
done

echo ""

# 5. 检查网络和端口
echo -e "${BLUE}[5] 网络和端口检查${NC}"
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    check_item "80端口" "warning" "已被占用"
else
    check_item "80端口" "ok" "可用"
fi

if netstat -tlnp 2>/dev/null | grep -q ":443 "; then
    check_item "443端口" "warning" "已被占用"
else
    check_item "443端口" "ok" "可用"
fi

# 检查防火墙
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        if ufw status | grep -q "80/tcp" && ufw status | grep -q "443/tcp"; then
            check_item "防火墙规则" "ok" "80和443端口已开放"
        else
            check_item "防火墙规则" "warning" "80或443端口未开放"
        fi
    else
        check_item "防火墙" "warning" "未启用"
    fi
fi

echo ""

# 6. 检查Docker镜像（如果配置了镜像地址）
if [ -f "$APP_DIR/.env" ]; then
    set -a
    source "$APP_DIR/.env" 2>/dev/null || true
    set +a
    
    if [ -n "$DOCKER_IMAGE_BACKEND" ] && [ -n "$TAG" ]; then
        echo -e "${BLUE}[6] Docker镜像检查${NC}"
        IMAGE_BACKEND="${DOCKER_IMAGE_BACKEND}:${TAG}"
        if docker images | grep -q "${DOCKER_IMAGE_BACKEND}"; then
            check_item "后端镜像" "ok" "本地存在: $IMAGE_BACKEND"
        else
            check_item "后端镜像" "warning" "本地不存在: $IMAGE_BACKEND（部署时会自动拉取）"
        fi
        
        if [ -n "$DOCKER_IMAGE_FRONTEND" ]; then
            IMAGE_FRONTEND="${DOCKER_IMAGE_FRONTEND}:${TAG}"
            if docker images | grep -q "${DOCKER_IMAGE_FRONTEND}"; then
                check_item "前端镜像" "ok" "本地存在: $IMAGE_FRONTEND"
            else
                check_item "前端镜像" "warning" "本地不存在: $IMAGE_FRONTEND（部署时会自动拉取）"
            fi
        fi
        echo ""
    fi
fi

# 7. 检查Traefik部署状态
echo -e "${BLUE}[7] Traefik部署状态${NC}"
TRAEFIK_DIR=${TRAEFIK_DIR:-/opt/traefik-public}
if [ -f "$TRAEFIK_DIR/docker-compose.yml" ] || [ -f "$TRAEFIK_DIR/docker-compose.traefik.yml" ]; then
    if docker ps | grep -q traefik; then
        check_item "Traefik服务" "ok" "正在运行"
    else
        check_item "Traefik服务" "warning" "未运行（部署脚本会自动启动）"
    fi
else
    check_item "Traefik配置" "warning" "未部署（部署脚本会自动部署）"
fi

echo ""

# 总结
echo -e "${BLUE}=========================================="
echo "检查完成"
echo "==========================================${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过，可以开始部署！${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ 有 $WARNINGS 个警告，建议修复后再部署${NC}"
    exit 0
else
    echo -e "${RED}✗ 发现 $ERRORS 个错误和 $WARNINGS 个警告${NC}"
    echo ""
    echo "请修复错误后重新运行检查："
    echo "  bash scripts/aliyun/check-deployment.sh"
    exit 1
fi
