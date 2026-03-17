#!/bin/bash

# Docker 镜像源配置脚本
# 用于配置 Docker 使用国内镜像源以加速镜像下载

set -e

echo "开始配置 Docker 镜像源..."

# 备份现有的 daemon.json 文件
echo "备份现有的 daemon.json 文件..."
cp /etc/docker/daemon.json /etc/docker/daemon.json.bak 2>/dev/null || true

# 创建新的 daemon.json 配置文件
echo "创建新的 daemon.json 配置文件..."
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

# 重新加载 systemd 配置
echo "重新加载 systemd 配置..."
systemctl daemon-reload

# 重启 Docker 服务
echo "重启 Docker 服务..."
systemctl restart docker

# 等待 Docker 服务启动
echo "等待 Docker 服务启动..."
sleep 8

# 验证配置
echo "验证 Docker 镜像源配置..."
docker info | grep -A 5 "Registry Mirrors"

echo "Docker 镜像源配置完成！"
