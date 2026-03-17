# 服务器快速修复指南

## 问题
Docker镜像拉取失败，错误：`403 Forbidden` from `dockerhub.azk8s.cn`

## 解决方案

### 步骤1: 修复Docker镜像加速器配置

在服务器上执行以下命令：

```bash
# 备份现有配置
cp /etc/docker/daemon.json /etc/docker/daemon.json.bak 2>/dev/null || true

# 创建新的配置文件
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

# 重启Docker服务
systemctl daemon-reload
systemctl restart docker
sleep 8

# 验证配置
docker info | grep -A 5 "Registry Mirrors"
```

### 步骤2: 测试拉取基础镜像

```bash
docker pull python:3.10 || docker pull python:3.10-slim
docker pull node:20 || docker pull node:20-slim
docker pull nginx:1 || docker pull nginx:latest
```

### 步骤3: 清理构建缓存并重新构建

```bash
cd /opt/invoice-app

# 清理缓存
docker builder prune -f

# 构建后端镜像
cd backend
docker build -t invoice-app-backend:latest .

# 构建前端镜像
cd ../frontend
docker build --build-arg VITE_API_URL=http://8.145.33.61:8000 -t invoice-app-frontend:latest .
```

### 步骤4: 重新部署服务

```bash
cd /opt/invoice-app

# 停止旧容器
docker compose -f docker-compose.yml down

# 启动服务
docker compose -f docker-compose.yml up -d redis prestart backend frontend adminer

# 检查服务状态
docker compose ps
```

## 一键执行（如果脚本已存在）

如果项目已更新，可以直接执行：

```bash
cd /opt/invoice-app
git pull
bash scripts/aliyun/quick-fix.sh
```

然后继续执行构建和部署步骤。

