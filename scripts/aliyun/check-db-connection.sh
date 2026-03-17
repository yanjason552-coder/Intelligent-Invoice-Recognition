#!/bin/bash
# 数据库连接诊断脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR=${APP_DIR:-/opt/invoice-app}

echo -e "${BLUE}=========================================="
echo "数据库连接诊断"
echo "==========================================${NC}"
echo ""

# 加载环境变量
if [ -f "$APP_DIR/.env" ]; then
    set -a
    source "$APP_DIR/.env" 2>/dev/null || true
    set +a
fi

# 1. 检查环境变量配置
echo -e "${YELLOW}[1] 数据库配置检查${NC}"
echo "  POSTGRES_SERVER: ${POSTGRES_SERVER:-未设置}"
echo "  POSTGRES_PORT: ${POSTGRES_PORT:-未设置}"
echo "  POSTGRES_USER: ${POSTGRES_USER:-未设置}"
echo "  POSTGRES_DB: ${POSTGRES_DB:-未设置}"
echo "  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:+已设置（已隐藏）}"
echo ""

# 2. 网络连通性测试
if [ -n "$POSTGRES_SERVER" ] && [ -n "$POSTGRES_PORT" ]; then
    echo -e "${YELLOW}[2] 网络连通性测试${NC}"
    
    # Ping测试
    echo "  测试ping连接..."
    if ping -c 2 -W 3 "$POSTGRES_SERVER" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ Ping成功${NC}"
    else
        echo -e "  ${RED}✗ Ping失败${NC}"
    fi
    
    # 端口连通性测试
    echo "  测试端口 $POSTGRES_PORT 连通性..."
    if timeout 5 bash -c "echo > /dev/tcp/$POSTGRES_SERVER/$POSTGRES_PORT" 2>/dev/null; then
        echo -e "  ${GREEN}✓ 端口 $POSTGRES_PORT 可访问${NC}"
    else
        echo -e "  ${RED}✗ 端口 $POSTGRES_PORT 不可访问${NC}"
        echo -e "  ${YELLOW}可能原因:${NC}"
        echo "    - 防火墙阻止"
        echo "    - 数据库服务未运行"
        echo "    - 端口配置错误"
    fi
    echo ""
fi

# 3. 使用psql测试连接（如果已安装）
if command -v psql &> /dev/null; then
    echo -e "${YELLOW}[3] 使用psql测试连接${NC}"
    if [ -n "$POSTGRES_SERVER" ] && [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_DB" ]; then
        export PGPASSWORD="$POSTGRES_PASSWORD"
        if timeout 10 psql -h "$POSTGRES_SERVER" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓ 数据库连接成功${NC}"
            echo ""
            echo "  数据库版本信息:"
            timeout 10 psql -h "$POSTGRES_SERVER" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" 2>/dev/null | head -3 | sed 's/^/    /'
        else
            echo -e "  ${RED}✗ 数据库连接失败${NC}"
            echo ""
            echo "  详细错误信息:"
            timeout 10 psql -h "$POSTGRES_SERVER" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" 2>&1 | sed 's/^/    /' || true
        fi
        unset PGPASSWORD
    else
        echo -e "  ${YELLOW}⚠ 数据库配置不完整，跳过psql测试${NC}"
    fi
else
    echo -e "${YELLOW}⚠ psql未安装，跳过数据库连接测试${NC}"
    echo "  安装psql: apt-get install postgresql-client"
fi
echo ""

# 4. 检查防火墙规则
echo -e "${YELLOW}[4] 防火墙检查${NC}"
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        echo "  防火墙状态: 已启用"
        if ufw status | grep -q "$POSTGRES_PORT"; then
            echo -e "  ${GREEN}✓ 端口 $POSTGRES_PORT 已在防火墙规则中${NC}"
        else
            echo -e "  ${YELLOW}⚠ 端口 $POSTGRES_PORT 可能被防火墙阻止${NC}"
        fi
    else
        echo "  防火墙状态: 未启用"
    fi
else
    echo "  ufw未安装"
fi
echo ""

# 5. 检查DNS解析
if [ -n "$POSTGRES_SERVER" ]; then
    echo -e "${YELLOW}[5] DNS解析检查${NC}"
    if nslookup "$POSTGRES_SERVER" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ DNS解析正常${NC}"
        nslookup "$POSTGRES_SERVER" 2>/dev/null | grep -A 2 "Name:" | sed 's/^/    /' || true
    else
        # 如果是IP地址，跳过DNS检查
        if [[ "$POSTGRES_SERVER" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "  使用IP地址，跳过DNS检查"
        else
            echo -e "  ${YELLOW}⚠ DNS解析失败${NC}"
        fi
    fi
    echo ""
fi

# 6. 提供解决方案
echo -e "${BLUE}=========================================="
echo "解决方案建议"
echo "==========================================${NC}"
echo ""

if [ -n "$POSTGRES_SERVER" ] && [ -n "$POSTGRES_PORT" ]; then
    echo "1. 检查数据库服务器是否运行:"
    echo "   ssh到数据库服务器检查PostgreSQL服务状态"
    echo ""
    
    echo "2. 检查防火墙规则:"
    echo "   在数据库服务器上确保端口 $POSTGRES_PORT 已开放"
    echo "   在应用服务器上确保可以访问 $POSTGRES_SERVER:$POSTGRES_PORT"
    echo ""
    
    echo "3. 测试连接:"
    echo "   timeout 10 bash -c 'echo > /dev/tcp/$POSTGRES_SERVER/$POSTGRES_PORT'"
    echo ""
    
    echo "4. 如果使用psql测试:"
    echo "   export PGPASSWORD='$POSTGRES_PASSWORD'"
    echo "   psql -h $POSTGRES_SERVER -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB"
    echo ""
    
    echo "5. 检查数据库配置:"
    echo "   确认 .env 文件中的数据库配置正确"
    echo "   确认数据库用户有访问权限"
    echo ""
fi

echo -e "${GREEN}诊断完成！${NC}"
echo ""
