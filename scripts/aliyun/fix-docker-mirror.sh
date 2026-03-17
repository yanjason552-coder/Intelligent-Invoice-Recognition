#!/bin/bash
# 修复Docker镜像拉取问题
# 配置Docker镜像加速器

echo "=========================================="
echo "配置Docker镜像加速器"
echo "=========================================="

# 检查Docker是否运行
if ! systemctl is-active --quiet docker; then
    echo "启动Docker服务..."
    systemctl start docker
fi

# 创建Docker配置目录
mkdir -p /etc/docker

# 备份现有配置
if [ -f /etc/docker/daemon.json ]; then
    cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
    echo "已备份现有配置到 /etc/docker/daemon.json.bak"
fi

# 配置镜像加速器（移除不可用的dockerhub.azk8s.cn）
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

echo "Docker镜像加速器配置完成"

# 重启Docker服务
echo "重启Docker服务..."
systemctl daemon-reload
systemctl restart docker

# 等待Docker启动
sleep 3

# 验证配置
echo ""
echo "验证Docker配置..."
docker info | grep -A 10 "Registry Mirrors" || echo "配置可能未生效，请检查Docker服务状态"

echo ""
echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo ""
echo "现在可以重新尝试构建镜像："
echo "  docker pull python:3.10"
echo "  或"
echo "  docker build -t invoice-app-backend:latest backend/"
echo ""

