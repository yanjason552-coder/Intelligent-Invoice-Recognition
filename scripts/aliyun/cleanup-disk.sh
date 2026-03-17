#!/bin/bash
# 磁盘清理脚本
# 清理Docker未使用的资源、日志等

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "磁盘空间清理"
echo "==========================================${NC}"
echo ""

# 1. 检查磁盘使用情况
echo -e "${YELLOW}[1] 检查磁盘使用情况${NC}"
df -h
echo ""

# 2. 清理Docker未使用的资源
echo -e "${YELLOW}[2] 清理Docker未使用的资源${NC}"
echo "  清理未使用的镜像、容器、网络和构建缓存..."

# 清理所有未使用的资源（谨慎操作）
docker system prune -af --volumes 2>/dev/null || {
    echo -e "${YELLOW}⚠ 清理Docker资源时出错，尝试分步清理...${NC}"
    
    # 分步清理
    echo "  清理停止的容器..."
    docker container prune -f 2>/dev/null || true
    
    echo "  清理未使用的镜像..."
    docker image prune -af 2>/dev/null || true
    
    echo "  清理未使用的卷..."
    docker volume prune -f 2>/dev/null || true
    
    echo "  清理未使用的网络..."
    docker network prune -f 2>/dev/null || true
}

echo -e "${GREEN}✓ Docker资源清理完成${NC}"
echo ""

# 3. 清理Docker日志
echo -e "${YELLOW}[3] 清理Docker日志${NC}"
if [ -d /var/lib/docker/containers ]; then
    echo "  清理容器日志..."
    find /var/lib/docker/containers -name "*.log" -type f -delete 2>/dev/null || true
    echo -e "${GREEN}✓ Docker日志清理完成${NC}"
else
    echo -e "${YELLOW}⚠ Docker日志目录不存在${NC}"
fi
echo ""

# 4. 清理系统日志
echo -e "${YELLOW}[4] 清理系统日志${NC}"
if command -v journalctl &> /dev/null; then
    echo "  清理journal日志..."
    journalctl --vacuum-time=7d 2>/dev/null || true
    echo -e "${GREEN}✓ 系统日志清理完成${NC}"
fi

# 清理旧的日志文件
if [ -d /var/log ]; then
    echo "  清理/var/log中的旧日志..."
    find /var/log -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
    find /var/log -name "*.gz" -type f -mtime +30 -delete 2>/dev/null || true
fi
echo ""

# 5. 清理临时文件
echo -e "${YELLOW}[5] 清理临时文件${NC}"
if [ -d /tmp ]; then
    find /tmp -type f -mtime +7 -delete 2>/dev/null || true
    echo -e "${GREEN}✓ 临时文件清理完成${NC}"
fi
echo ""

# 6. 检查大文件
echo -e "${YELLOW}[6] 查找大文件（前10个）${NC}"
echo "  查找大于100MB的文件..."
find / -type f -size +100M 2>/dev/null | head -10 | while read file; do
    size=$(du -h "$file" 2>/dev/null | cut -f1)
    echo "    $size - $file"
done
echo ""

# 7. 再次检查磁盘使用情况
echo -e "${YELLOW}[7] 清理后的磁盘使用情况${NC}"
df -h
echo ""

echo -e "${GREEN}=========================================="
echo "清理完成"
echo "==========================================${NC}"
echo ""
