#!/bin/bash
# 域名配置脚本
# 快速配置域名相关设置

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR=${APP_DIR:-/opt/invoice-app}

echo -e "${BLUE}=========================================="
echo "域名配置向导"
echo "==========================================${NC}"
echo ""

# 检查.env文件
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${RED}错误: .env文件不存在${NC}"
    echo "请先运行: bash $APP_DIR/scripts/aliyun/prepare-deployment.sh"
    exit 1
fi

# 读取当前配置
set -a
source "$APP_DIR/.env" 2>/dev/null || true
set +a

echo "当前配置："
echo "  DOMAIN: ${DOMAIN:-未设置}"
echo "  TRAEFIK_EMAIL: ${TRAEFIK_EMAIL:-未设置}"
echo ""

# 读取域名
read -p "请输入您的域名（例如：example.com，直接回车使用当前值）: " NEW_DOMAIN
if [ -z "$NEW_DOMAIN" ]; then
    NEW_DOMAIN="$DOMAIN"
fi

if [ -z "$NEW_DOMAIN" ] || [ "$NEW_DOMAIN" = "your-domain.com" ] || [ "$NEW_DOMAIN" = "8.145.33.61" ]; then
    echo -e "${RED}错误: 请输入有效的域名${NC}"
    exit 1
fi

# 读取邮箱
read -p "请输入您的邮箱（用于SSL证书，直接回车使用当前值）: " NEW_EMAIL
if [ -z "$NEW_EMAIL" ]; then
    NEW_EMAIL="$TRAEFIK_EMAIL"
fi

if [ -z "$NEW_EMAIL" ] || [ "$NEW_EMAIL" = "admin@example.com" ]; then
    echo -e "${RED}错误: 请输入有效的邮箱地址${NC}"
    exit 1
fi

# 备份.env文件
BACKUP_FILE="$APP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
cp "$APP_DIR/.env" "$BACKUP_FILE"
echo -e "${GREEN}✓ 已备份.env文件到: $BACKUP_FILE${NC}"

# 更新配置
echo ""
echo -e "${YELLOW}更新配置...${NC}"

# 更新DOMAIN
sed -i "s|^DOMAIN=.*|DOMAIN=$NEW_DOMAIN|" "$APP_DIR/.env"

# 更新FRONTEND_HOST
sed -i "s|^FRONTEND_HOST=.*|FRONTEND_HOST=dashboard.$NEW_DOMAIN|" "$APP_DIR/.env"

# 更新TRAEFIK_EMAIL
sed -i "s|^TRAEFIK_EMAIL=.*|TRAEFIK_EMAIL=$NEW_EMAIL|" "$APP_DIR/.env"

# 更新CORS配置
CORS_CONFIG="[\"https://dashboard.$NEW_DOMAIN\",\"http://localhost:5173\"]"
sed -i "s|^BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=$CORS_CONFIG|" "$APP_DIR/.env"

echo -e "${GREEN}✓ 配置已更新${NC}"

# 显示更新后的配置
echo ""
echo -e "${BLUE}更新后的配置：${NC}"
echo "  DOMAIN: $NEW_DOMAIN"
echo "  FRONTEND_HOST: dashboard.$NEW_DOMAIN"
echo "  TRAEFIK_EMAIL: $NEW_EMAIL"
echo "  BACKEND_CORS_ORIGINS: $CORS_CONFIG"
echo ""

# DNS配置提示
echo -e "${BLUE}=========================================="
echo "DNS配置说明"
echo "==========================================${NC}"
echo ""
echo "请在您的DNS管理面板添加以下A记录："
echo ""
echo "  类型    主机记录    记录值          说明"
echo "  A       api         8.145.33.61     API服务"
echo "  A       dashboard   8.145.33.61     前端服务"
echo "  A       adminer     8.145.33.61     数据库管理"
echo "  A       traefik     8.145.33.61     Traefik面板"
echo ""
echo "完整域名示例："
echo "  - api.$NEW_DOMAIN"
echo "  - dashboard.$NEW_DOMAIN"
echo "  - adminer.$NEW_DOMAIN"
echo "  - traefik.$NEW_DOMAIN"
echo ""

# 验证DNS提示
echo -e "${YELLOW}验证DNS解析（等待DNS生效后运行）：${NC}"
echo "  nslookup api.$NEW_DOMAIN"
echo "  nslookup dashboard.$NEW_DOMAIN"
echo ""

# 部署提示
echo -e "${BLUE}=========================================="
echo "下一步操作"
echo "==========================================${NC}"
echo ""
echo "1. 配置DNS解析（如上所示）"
echo ""
echo "2. 等待DNS生效（通常几分钟到几小时）"
echo ""
echo "3. 验证DNS解析："
echo "   nslookup api.$NEW_DOMAIN"
echo ""
echo "4. 部署Traefik（如果未部署）："
echo "   cd /opt/traefik-public"
echo "   export DOMAIN=$NEW_DOMAIN"
echo "   export EMAIL=$NEW_EMAIL"
echo "   export USERNAME=admin"
echo "   export PASSWORD=\$(openssl passwd -apr1 'admin123456')"
echo "   docker compose -f docker-compose.traefik.yml up -d"
echo ""
echo "5. 部署应用："
echo "   bash $APP_DIR/scripts/aliyun/deploy-production.sh"
echo ""
echo -e "${GREEN}配置完成！${NC}"
echo ""
