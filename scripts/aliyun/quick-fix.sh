#!/bin/bash
# 快速修复Docker镜像加速器
set -e

echo "=========================================="
echo "快速修复Docker镜像加速器"
echo "=========================================="
echo ""

# 修复Docker镜像加速器配置
echo "[1/3] 修复Docker镜像加速器配置..."
mkdir -p /etc/docker
if [ -f /etc/docker/daemon.json ]; then
    cp /etc/docker/daemon.json /etc/docker/daemon.json.bak.$(date +%Y%m%d_%H%M%S)
    echo "已备份现有配置"
fi

cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "max-concurrent-downloads": 10,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

echo "✓ 配置文件已更新"

# 重启Docker服务
echo "[2/3] 重启Docker服务..."
systemctl daemon-reload
systemctl restart docker
echo "等待Docker服务重启..."
sleep 8

# 验证配置
echo "[3/3] 验证Docker配置..."
docker info | grep -A 5 "Registry Mirrors" || echo "配置可能未完全生效，但可以继续"

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "现在可以测试拉取镜像:"
echo "  docker pull python:3.10"
echo "  docker pull node:20"
echo "  docker pull nginx:1"
echo ""

