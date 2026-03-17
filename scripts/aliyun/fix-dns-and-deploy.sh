#!/bin/bash
# 修复DNS问题并部署

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "DNS问题诊断和修复"
echo "==========================================${NC}"
echo ""

# 1. 检查DNS配置
echo -e "${YELLOW}[1] 检查DNS配置...${NC}"
cat /etc/resolv.conf
echo ""

# 2. 测试DNS解析
echo -e "${YELLOW}[2] 测试DNS解析...${NC}"
if nslookup docker.mirrors.ustc.edu.cn 2>/dev/null | grep -q "Address"; then
    echo -e "${GREEN}✓ DNS解析正常${NC}"
else
    echo -e "${RED}✗ DNS解析失败${NC}"
    echo ""
    echo -e "${YELLOW}修复DNS配置...${NC}"
    
    # 备份原配置
    cp /etc/resolv.conf /etc/resolv.conf.backup.$(date +%Y%m%d_%H%M%S)
    
    # 添加公共DNS服务器
    cat > /etc/resolv.conf << 'DNS_EOF'
nameserver 223.5.5.5
nameserver 223.6.6.6
nameserver 8.8.8.8
nameserver 114.114.114.114
DNS_EOF
    
    echo -e "${GREEN}✓ DNS配置已更新${NC}"
    echo ""
    echo "新的DNS配置："
    cat /etc/resolv.conf
fi

# 3. 测试网络连接
echo ""
echo -e "${YELLOW}[3] 测试网络连接...${NC}"
if ping -c 2 docker.mirrors.ustc.edu.cn > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 网络连接正常${NC}"
else
    echo -e "${YELLOW}⚠ 网络连接可能有问题，尝试使用其他镜像源${NC}"
fi

# 4. 检查Docker镜像源配置
echo ""
echo -e "${YELLOW}[4] 检查Docker镜像源配置...${NC}"
if [ -f /etc/docker/daemon.json ]; then
    echo "当前Docker镜像源配置："
    cat /etc/docker/daemon.json | grep -A 10 "registry-mirrors"
    
    # 检查镜像源是否可用
    MIRRORS=$(cat /etc/docker/daemon.json | grep -oP '"https://[^"]*"' | tr -d '"')
    for mirror in $MIRRORS; do
        if curl -s --connect-timeout 3 "$mirror" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $mirror 可用${NC}"
        else
            echo -e "${YELLOW}⚠ $mirror 不可用${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠ Docker镜像源未配置${NC}"
fi

echo ""
echo -e "${BLUE}=========================================="
echo "建议的解决方案"
echo "==========================================${NC}"
echo ""
echo "方案1: 使用阿里云镜像加速器（推荐）"
echo "  1. 登录阿里云控制台"
echo "  2. 进入容器镜像服务 -> 镜像加速器"
echo "  3. 复制您的专属加速地址"
echo "  4. 更新 /etc/docker/daemon.json"
echo ""
echo "方案2: 临时禁用镜像源，使用Docker Hub"
echo "  备份并临时移除镜像源配置"
echo ""
echo "方案3: 使用其他可用的镜像源"
echo ""
