#!/bin/bash
# 阿里云容器镜像服务构建和推送脚本
# 用法: ./build-and-push.sh [tag]
# 示例: ./build-and-push.sh v1.0.0

set -e

# 配置变量（请根据实际情况修改）
REGISTRY=${REGISTRY:-your-registry.cn-hangzhou.aliyuncs.com}
NAMESPACE=${NAMESPACE:-invoice}
TAG=${1:-latest}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo "开始构建和推送Docker镜像"
echo "==========================================${NC}"
echo "镜像仓库: ${REGISTRY}"
echo "命名空间: ${NAMESPACE}"
echo "标签: ${TAG}"
echo ""

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 登录阿里云容器镜像服务
echo -e "${YELLOW}登录阿里云容器镜像服务...${NC}"
if [ -z "$ALIYUN_REGISTRY_USERNAME" ] || [ -z "$ALIYUN_REGISTRY_PASSWORD" ]; then
    echo -e "${YELLOW}提示: 请设置环境变量 ALIYUN_REGISTRY_USERNAME 和 ALIYUN_REGISTRY_PASSWORD${NC}"
    echo "或者手动登录: docker login --username=your-username $REGISTRY"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    docker login --username=$ALIYUN_REGISTRY_USERNAME $REGISTRY
else
    echo "$ALIYUN_REGISTRY_PASSWORD" | docker login --username=$ALIYUN_REGISTRY_USERNAME --password-stdin $REGISTRY
fi

# 构建后端镜像
echo -e "${YELLOW}构建后端镜像...${NC}"
cd backend
docker build -t $REGISTRY/$NAMESPACE/backend:$TAG .
echo -e "${GREEN}后端镜像构建完成${NC}"

# 推送后端镜像
echo -e "${YELLOW}推送后端镜像...${NC}"
docker push $REGISTRY/$NAMESPACE/backend:$TAG
echo -e "${GREEN}后端镜像推送完成${NC}"

# 构建前端镜像
echo -e "${YELLOW}构建前端镜像...${NC}"
cd ../frontend
docker build --build-arg VITE_API_URL=${VITE_API_URL:-https://api.your-domain.com} -t $REGISTRY/$NAMESPACE/frontend:$TAG .
echo -e "${GREEN}前端镜像构建完成${NC}"

# 推送前端镜像
echo -e "${YELLOW}推送前端镜像...${NC}"
docker push $REGISTRY/$NAMESPACE/frontend:$TAG
echo -e "${GREEN}前端镜像推送完成${NC}"

cd ..

echo ""
echo -e "${GREEN}=========================================="
echo "镜像构建和推送完成！"
echo "==========================================${NC}"
echo "后端镜像: $REGISTRY/$NAMESPACE/backend:$TAG"
echo "前端镜像: $REGISTRY/$NAMESPACE/frontend:$TAG"
echo ""
echo "下一步："
echo "1. 在服务器上更新 .env 文件中的镜像地址"
echo "2. 运行部署脚本进行部署"
echo "=========================================="

