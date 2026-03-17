#!/bin/bash
# 在服务器上创建所有部署脚本
# 一次性创建所有必要的部署工具

set -e

APP_DIR=${APP_DIR:-/opt/invoice-app}
SCRIPTS_DIR="$APP_DIR/scripts/aliyun"

echo "创建脚本目录..."
mkdir -p "$SCRIPTS_DIR"

echo "正在创建所有部署脚本..."
echo ""

# 1. 创建部署检查脚本
echo "[1/3] 创建部署检查脚本..."
cat > "$SCRIPTS_DIR/check-deployment.sh" << 'CHECK_EOF'
#!/bin/bash
# 部署前检查脚本
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR=${APP_DIR:-/opt/invoice-app}
ERRORS=0
WARNINGS=0

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

echo -e "${BLUE}=========================================="
echo "部署前检查"
echo "==========================================${NC}"
echo ""

# 检查Docker
echo -e "${BLUE}[1] Docker环境检查${NC}"
if command -v docker &> /dev/null; then
    check_item "Docker" "ok" "$(docker --version)"
else
    check_item "Docker" "error" "未安装"
fi

if docker compose version &> /dev/null 2>&1 || docker-compose --version &> /dev/null 2>&1; then
    if docker compose version &> /dev/null 2>&1; then
        check_item "Docker Compose" "ok" "$(docker compose version)"
    else
        check_item "Docker Compose" "ok" "$(docker-compose --version)"
    fi
else
    check_item "Docker Compose" "error" "未安装"
fi

if docker network ls | grep -q traefik-public; then
    check_item "Docker网络" "ok" "traefik-public 已存在"
else
    check_item "Docker网络" "warning" "traefik-public 不存在"
fi
echo ""

# 检查项目文件
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
echo ""

# 检查环境变量
echo -e "${BLUE}[3] 环境变量检查${NC}"
if [ -f "$APP_DIR/.env" ]; then
    check_item ".env文件" "ok" "存在"
    
    set -a
    source "$APP_DIR/.env" 2>/dev/null || true
    set +a
    
    required_vars=("DOMAIN" "STACK_NAME" "SECRET_KEY" "POSTGRES_PASSWORD" "POSTGRES_USER" "POSTGRES_DB" "FIRST_SUPERUSER" "FIRST_SUPERUSER_PASSWORD")
    
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
else
    check_item ".env文件" "error" "不存在"
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
    echo "  bash $SCRIPTS_DIR/check-deployment.sh"
    exit 1
fi
CHECK_EOF

chmod +x "$SCRIPTS_DIR/check-deployment.sh"
echo "✓ 部署检查脚本已创建"
echo ""

# 2. 创建部署脚本
echo "[2/3] 创建部署脚本..."
cat > "$SCRIPTS_DIR/deploy-production.sh" << 'DEPLOY_EOF'
#!/bin/bash
# 生产环境部署脚本
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR=${APP_DIR:-/opt/invoice-app}
TRAEFIK_DIR=${TRAEFIK_DIR:-/opt/traefik-public}

echo -e "${GREEN}=========================================="
echo "开始部署生产环境"
echo "==========================================${NC}"
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}错误: 请以root用户运行此脚本${NC}"
    exit 1
fi

# 检查环境变量文件
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${RED}错误: .env 文件不存在于 $APP_DIR${NC}"
    exit 1
fi

# 加载环境变量
set -a
source "$APP_DIR/.env" 2>/dev/null || true
set +a

# 检查必要的环境变量
required_vars=("DOMAIN" "STACK_NAME" "SECRET_KEY" "POSTGRES_PASSWORD" "FIRST_SUPERUSER" "FIRST_SUPERUSER_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}错误: 环境变量 $var 未设置${NC}"
        exit 1
    fi
done

# 检查docker-compose.yml
if [ ! -f "$APP_DIR/docker-compose.yml" ]; then
    echo -e "${RED}错误: docker-compose.yml 文件不存在${NC}"
    exit 1
fi

cd "$APP_DIR"

# 检查是否有生产环境配置文件
COMPOSE_FILES="-f docker-compose.yml"
if [ -f "docker-compose.production.yml" ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.production.yml"
fi

# 拉取最新镜像（如果使用镜像）
if [ -n "$DOCKER_IMAGE_BACKEND" ] && [ "$DOCKER_IMAGE_BACKEND" != "your-registry.cn-hangzhou.aliyuncs.com/invoice/backend" ]; then
    echo -e "${YELLOW}拉取最新镜像...${NC}"
    docker compose $COMPOSE_FILES pull || echo "镜像拉取失败，将使用本地构建"
fi

# 停止旧容器
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

echo ""
echo -e "${GREEN}=========================================="
echo "部署完成！"
echo "==========================================${NC}"
echo ""
echo "查看日志: docker compose $COMPOSE_FILES logs -f"
echo "重启服务: docker compose $COMPOSE_FILES restart"
echo ""
DEPLOY_EOF

chmod +x "$SCRIPTS_DIR/deploy-production.sh"
echo "✓ 部署脚本已创建"
echo ""

# 3. 创建状态检查脚本
echo "[3/3] 创建状态检查脚本..."
cat > "$SCRIPTS_DIR/check-deployment-status.sh" << 'STATUS_EOF'
#!/bin/bash
# 部署状态检查脚本
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

# Docker服务状态
echo -e "${BLUE}[1] Docker服务状态${NC}"
if systemctl is-active --quiet docker; then
    echo -e "${GREEN}✓ Docker服务: 运行中${NC}"
else
    echo -e "${RED}✗ Docker服务: 未运行${NC}"
fi
echo ""

# Traefik状态
echo -e "${BLUE}[2] Traefik服务状态${NC}"
if docker ps | grep -q traefik; then
    echo -e "${GREEN}✓ Traefik: 运行中${NC}"
    docker ps | grep traefik
else
    echo -e "${YELLOW}⚠ Traefik: 未运行${NC}"
fi
echo ""

# 应用服务状态
echo -e "${BLUE}[3] 应用服务状态${NC}"
if [ -f "$APP_DIR/.env" ] && [ -f "$APP_DIR/docker-compose.yml" ]; then
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
        echo -e "${YELLOW}⚠ 应用服务: 未运行${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 无法检查应用服务状态${NC}"
fi
echo ""

# 端口监听
echo -e "${BLUE}[4] 端口监听状态${NC}"
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo -e "${GREEN}✓ 80端口: 监听中${NC}"
else
    echo -e "${YELLOW}⚠ 80端口: 未监听${NC}"
fi

if netstat -tlnp 2>/dev/null | grep -q ":443 "; then
    echo -e "${GREEN}✓ 443端口: 监听中${NC}"
else
    echo -e "${YELLOW}⚠ 443端口: 未监听${NC}"
fi
echo ""

# 访问地址
echo -e "${BLUE}[5] 访问地址${NC}"
if [ -f "$APP_DIR/.env" ]; then
    set -a
    source "$APP_DIR/.env" 2>/dev/null || true
    set +a
    
    if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "your-domain.com" ]; then
        echo "前端: https://dashboard.$DOMAIN"
        echo "API文档: https://api.$DOMAIN/docs"
        echo "数据库管理: https://adminer.$DOMAIN"
    else
        echo "域名: $DOMAIN"
    fi
fi
echo ""

echo -e "${BLUE}=========================================="
echo "检查完成"
echo "==========================================${NC}"
STATUS_EOF

chmod +x "$SCRIPTS_DIR/check-deployment-status.sh"
echo "✓ 状态检查脚本已创建"
echo ""

echo -e "${GREEN}=========================================="
echo "所有脚本创建完成！"
echo "==========================================${NC}"
echo ""
echo "可用的脚本："
echo "  1. bash $SCRIPTS_DIR/check-deployment.sh        - 部署前检查"
echo "  2. bash $SCRIPTS_DIR/deploy-production.sh       - 部署应用"
echo "  3. bash $SCRIPTS_DIR/check-deployment-status.sh - 检查部署状态"
echo ""
CREATE_EOF

chmod +x "$SCRIPTS_DIR/create-all-scripts.sh"

echo "✓ 脚本创建工具已准备"
echo ""
echo "在服务器上运行以下命令创建所有脚本："
echo "  bash $SCRIPTS_DIR/create-all-scripts.sh"
