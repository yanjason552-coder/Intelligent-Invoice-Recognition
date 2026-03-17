#!/bin/bash
# 重试构建脚本
# 用于在配置镜像加速器后重新构建镜像

set -e

SERVER_IP="8.145.33.61"

echo "=========================================="
echo "重新构建Docker镜像"
echo "=========================================="

cd /opt/invoice-app

# 先配置镜像加速器
echo "[1/3] 配置Docker镜像加速器..."
bash scripts/aliyun/fix-docker-mirror.sh

# 测试拉取基础镜像
echo "[2/3] 测试拉取基础镜像..."
echo "拉取python:3.10..."
docker pull python:3.10 || {
    echo "尝试拉取python:3.10-slim..."
    docker pull python:3.10-slim
}

echo "拉取node:20..."
docker pull node:20 || docker pull node:20-slim

# 构建镜像
echo "[3/3] 构建应用镜像..."
echo "构建后端镜像..."
cd backend
docker build -t invoice-app-backend:latest . || {
    echo "构建失败，尝试清理缓存后重建..."
    docker builder prune -f
    docker build --no-cache -t invoice-app-backend:latest .
}
cd ..

echo "构建前端镜像..."
cd frontend
docker build --build-arg VITE_API_URL=http://$SERVER_IP:8000 -t invoice-app-frontend:latest . || {
    echo "构建失败，尝试清理缓存后重建..."
    docker builder prune -f
    docker build --no-cache --build-arg VITE_API_URL=http://$SERVER_IP:8000 -t invoice-app-frontend:latest .
}
cd ..

echo ""
echo "=========================================="
echo "镜像构建完成！"
echo "=========================================="
echo ""
docker images | grep invoice-app
echo ""

