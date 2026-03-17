#!/bin/bash
# 方式一部署命令 - 可直接复制执行
# 在Git Bash或Linux/Mac终端中执行

set -e

SERVER_IP="8.145.33.61"
SSH_PORT="50518"
SSH_USER="root"
SSH_PASSWORD="6b3fPk9n!"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "方式一：一键部署"
echo "=========================================="
echo "服务器: $SERVER_IP:$SSH_PORT"
echo "项目目录: $SCRIPT_DIR"
echo ""

# 检查部署脚本是否存在
if [ ! -f "scripts/aliyun/server-deploy.sh" ]; then
    echo "错误: 部署脚本不存在: scripts/aliyun/server-deploy.sh"
    exit 1
fi

# 步骤1: 上传部署脚本
echo "[1/3] 上传部署脚本到服务器..."
echo "提示: 请输入服务器密码: $SSH_PASSWORD"
echo ""
scp -P $SSH_PORT -o StrictHostKeyChecking=no scripts/aliyun/server-deploy.sh ${SSH_USER}@${SERVER_IP}:/tmp/server-deploy.sh

if [ $? -eq 0 ]; then
    echo "✓ 脚本上传成功"
else
    echo "✗ 脚本上传失败，请检查网络连接和密码"
    exit 1
fi

# 步骤2: 连接服务器并执行部署
echo ""
echo "[2/3] 连接服务器并执行部署..."
echo "提示: 请输入服务器密码: $SSH_PASSWORD"
echo ""
echo "注意: 如果遇到Docker镜像拉取失败，部署脚本会自动配置镜像加速器"
echo ""
ssh -p $SSH_PORT -o StrictHostKeyChecking=no ${SSH_USER}@${SERVER_IP} "chmod +x /tmp/server-deploy.sh && bash /tmp/server-deploy.sh"

# 如果部署失败，提供修复建议
if [ $? -ne 0 ]; then
    echo ""
    echo "=========================================="
    echo "部署可能遇到问题"
    echo "=========================================="
    echo ""
    echo "如果遇到Docker镜像拉取失败，请执行以下修复："
    echo ""
    echo "方法1: 在服务器上执行修复脚本"
    echo "  ssh -p $SSH_PORT $SSH_USER@$SERVER_IP"
    echo "  cd /opt/invoice-app"
    echo "  bash scripts/aliyun/fix-docker-mirror.sh"
    echo "  bash scripts/aliyun/retry-build.sh"
    echo ""
    echo "方法2: 查看详细修复指南"
    echo "  参考文件: FIX_DEPLOYMENT.md"
    echo ""
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "部署完成！"
    echo "=========================================="
    echo ""
    echo "访问地址:"
    echo "  前端: http://$SERVER_IP:5173"
    echo "  API文档: http://$SERVER_IP:8000/docs"
    echo "  API健康检查: http://$SERVER_IP:8000/api/v1/utils/health-check/"
    echo ""
    echo "查看服务状态:"
    echo "  ssh -p $SSH_PORT $SSH_USER@$SERVER_IP"
    echo "  docker compose ps"
    echo "=========================================="
else
    echo "✗ 部署失败，请检查错误信息"
    exit 1
fi

