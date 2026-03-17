# 部署问题修复指南

## 问题：Docker镜像拉取失败

### 错误信息
```
failed to resolve source metadata for docker.io/library/python:3.10
unable to fetch descriptor
```

### 原因
- Docker Hub访问受限（中国大陆地区）
- 网络连接问题
- Docker镜像加速器未配置

## 解决方案

### 方案1: 配置Docker镜像加速器（推荐）

**在服务器上执行**：

```bash
# 连接服务器
ssh -p 50518 root@8.145.33.61

# 执行修复脚本
cd /opt/invoice-app
bash scripts/aliyun/fix-docker-mirror.sh

# 或者手动配置
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://dockerhub.azk8s.cn"
  ]
}
EOF

systemctl daemon-reload
systemctl restart docker
```

### 方案2: 重新构建镜像

**在服务器上执行**：

```bash
# 连接服务器
ssh -p 50518 root@8.145.33.61

# 进入项目目录
cd /opt/invoice-app

# 执行重试构建脚本
bash scripts/aliyun/retry-build.sh
```

### 方案3: 手动构建

**步骤1: 配置镜像加速器**
```bash
bash scripts/aliyun/fix-docker-mirror.sh
```

**步骤2: 测试拉取基础镜像**
```bash
docker pull python:3.10
# 如果失败，尝试：
docker pull python:3.10-slim
```

**步骤3: 构建应用镜像**
```bash
cd /opt/invoice-app/backend
docker build -t invoice-app-backend:latest .

cd ../frontend
docker build --build-arg VITE_API_URL=http://8.145.33.61:8000 -t invoice-app-frontend:latest .
```

**步骤4: 部署服务**
```bash
cd /opt/invoice-app
docker compose -f docker-compose.yml -f docker-compose.production.external-db.yml --profile no-db up -d redis prestart backend frontend adminer
```

## 快速修复命令

**一键修复（在服务器上执行）**：

```bash
ssh -p 50518 root@8.145.33.61 << 'DEPLOY_FIX'
cd /opt/invoice-app

# 配置镜像加速器
bash scripts/aliyun/fix-docker-mirror.sh

# 重新构建镜像
bash scripts/aliyun/retry-build.sh

# 部署服务
docker compose -f docker-compose.yml -f docker-compose.production.external-db.yml --profile no-db up -d redis prestart backend frontend adminer

# 检查状态
docker compose ps
DEPLOY_FIX
```

## 验证修复

### 1. 检查Docker配置
```bash
docker info | grep -A 10 "Registry Mirrors"
```

### 2. 测试拉取镜像
```bash
docker pull python:3.10
docker pull node:20
```

### 3. 检查服务状态
```bash
docker compose ps
docker compose logs -f backend
```

## 备选方案

### 如果镜像加速器仍然无法使用

**方案A: 使用阿里云容器镜像服务**

1. 在本地构建镜像
2. 推送到阿里云容器镜像服务
3. 在服务器上拉取

**方案B: 使用代理**

```bash
# 配置Docker使用代理
mkdir -p /etc/systemd/system/docker.service.d
cat > /etc/systemd/system/docker.service.d/http-proxy.conf << EOF
[Service]
Environment="HTTP_PROXY=http://proxy.example.com:8080"
Environment="HTTPS_PROXY=http://proxy.example.com:8080"
Environment="NO_PROXY=localhost,127.0.0.1"
EOF

systemctl daemon-reload
systemctl restart docker
```

**方案C: 使用预构建镜像**

如果项目有预构建的镜像，可以直接使用：
```bash
docker pull your-registry.cn-hangzhou.aliyuncs.com/invoice/backend:latest
docker pull your-registry.cn-hangzhou.aliyuncs.com/invoice/frontend:latest
```

## 常见问题

### Q1: 配置镜像加速器后仍然失败？
**A**: 
1. 检查Docker服务是否重启：`systemctl status docker`
2. 验证配置是否生效：`docker info | grep Mirrors`
3. 尝试不同的镜像源

### Q2: 如何知道镜像加速器是否生效？
**A**: 
```bash
docker pull python:3.10
# 查看拉取日志，如果显示使用了镜像加速器地址，说明配置成功
```

### Q3: 可以同时使用多个镜像源吗？
**A**: 可以，Docker会按顺序尝试，直到成功为止。

## 联系支持

如果以上方案都无法解决问题，请：
1. 检查服务器网络连接
2. 查看Docker日志：`journalctl -u docker`
3. 联系技术支持

