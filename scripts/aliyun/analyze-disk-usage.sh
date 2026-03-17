#!/bin/bash
# 磁盘使用分析脚本
# 找出占用空间最大的文件和目录

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "磁盘使用分析"
echo "==========================================${NC}"
echo ""

# 1. Docker占用空间分析
echo -e "${YELLOW}[1] Docker占用空间分析${NC}"
docker system df 2>/dev/null || echo "Docker未运行或无法获取信息"
echo ""

# 2. 查看最大的Docker镜像
echo -e "${YELLOW}[2] 最大的Docker镜像（前10个）${NC}"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.ID}}" 2>/dev/null | head -11
echo ""

# 3. 查看所有容器
echo -e "${YELLOW}[3] Docker容器列表${NC}"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Size}}" 2>/dev/null || echo "无容器"
echo ""

# 4. 查找占用空间最大的目录（排除/proc, /sys等）
echo -e "${YELLOW}[4] 占用空间最大的目录（前15个）${NC}"
du -h --max-depth=1 / 2>/dev/null | grep -vE "^[0-9]+K" | sort -hr | head -15
echo ""

# 5. 重点检查常见的大目录
echo -e "${YELLOW}[5] 重点目录占用情况${NC}"
for dir in "/var/lib/docker" "/var/log" "/usr" "/opt" "/home" "/tmp" "/root"; do
    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        echo "  $dir: $size"
    fi
done
echo ""

# 6. Docker详细占用
echo -e "${YELLOW}[6] Docker详细占用分析${NC}"
if [ -d /var/lib/docker ]; then
    echo "  Docker根目录: /var/lib/docker"
    du -sh /var/lib/docker 2>/dev/null | awk '{print "    总大小: " $1}'
    echo ""
    echo "  Docker子目录占用:"
    du -h --max-depth=1 /var/lib/docker 2>/dev/null | sort -hr | head -10 | sed 's/^/    /'
fi
echo ""

# 7. 查找大文件（大于100MB）
echo -e "${YELLOW}[7] 查找大文件（>100MB，前20个）${NC}"
find / -type f -size +100M 2>/dev/null | head -20 | while read file; do
    size=$(du -h "$file" 2>/dev/null | cut -f1)
    echo "  $size - $file"
done
echo ""

# 8. 检查日志文件
echo -e "${YELLOW}[8] 大日志文件（>10MB）${NC}"
find /var/log -type f -size +10M 2>/dev/null | head -10 | while read file; do
    size=$(du -h "$file" 2>/dev/null | cut -f1)
    echo "  $size - $file"
done
echo ""

# 9. 检查Docker日志
echo -e "${YELLOW}[9] Docker容器日志占用${NC}"
if [ -d /var/lib/docker/containers ]; then
    total_log_size=$(find /var/lib/docker/containers -name "*.log" -type f -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1)
    echo "  容器日志总大小: $total_log_size"
    echo ""
    echo "  最大的日志文件（前10个）:"
    find /var/lib/docker/containers -name "*.log" -type f -exec du -h {} + 2>/dev/null | sort -hr | head -10 | sed 's/^/    /'
fi
echo ""

# 10. 优化建议
echo -e "${BLUE}=========================================="
echo "优化建议"
echo "==========================================${NC}"
echo ""

# 检查Docker未使用的资源
UNUSED_IMAGES=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l)
STOPPED_CONTAINERS=$(docker ps -a -f "status=exited" -q 2>/dev/null | wc -l)
UNUSED_VOLUMES=$(docker volume ls -f "dangling=true" -q 2>/dev/null | wc -l)

if [ "$UNUSED_IMAGES" -gt 0 ] || [ "$STOPPED_CONTAINERS" -gt 0 ] || [ "$UNUSED_VOLUMES" -gt 0 ]; then
    echo -e "${YELLOW}可以清理的Docker资源:${NC}"
    [ "$UNUSED_IMAGES" -gt 0 ] && echo "  - 未使用的镜像: $UNUSED_IMAGES 个"
    [ "$STOPPED_CONTAINERS" -gt 0 ] && echo "  - 停止的容器: $STOPPED_CONTAINERS 个"
    [ "$UNUSED_VOLUMES" -gt 0 ] && echo "  - 未使用的卷: $UNUSED_VOLUMES 个"
    echo ""
    echo "  清理命令:"
    echo "    docker system prune -af --volumes"
fi

# 检查日志文件
LOG_SIZE=$(find /var/log -type f -size +100M 2>/dev/null | wc -l)
if [ "$LOG_SIZE" -gt 0 ]; then
    echo -e "${YELLOW}发现大日志文件: $LOG_SIZE 个${NC}"
    echo "  可以清理系统日志: journalctl --vacuum-time=7d"
fi

echo ""
echo -e "${GREEN}分析完成！${NC}"
echo ""
