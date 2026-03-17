# 立即部署指南

## 服务器信息
- **IP**: 8.145.33.61
- **SSH端口**: 50518
- **用户名**: root
- **密码**: 6b3fPk9n!

## 数据库信息（外部PostgreSQL）
- **主机**: 8.145.33.61
- **端口**: 50511
- **用户名**: postgres
- **密码**: postgres123
- **数据库名**: invoice_db（需要先创建）

## Git仓库
- **地址**: https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git

## 快速部署步骤

### 方式1: 一键部署（推荐）

**在服务器上执行以下命令：**

```bash
# 1. 连接服务器
ssh -p 50518 root@8.145.33.61
# 输入密码: 6b3fPk9n!

# 2. 下载并执行部署脚本
curl -fsSL https://raw.githubusercontent.com/yanjason552-coder/Intelligent-Invoice-Recognition/main/scripts/aliyun/server-deploy.sh -o /tmp/deploy.sh
chmod +x /tmp/deploy.sh
bash /tmp/deploy.sh
```

**或者手动复制脚本内容：**

```bash
# 1. 连接服务器
ssh -p 50518 root@8.145.33.61

# 2. 创建部署脚本
cat > /tmp/deploy.sh << 'DEPLOY_SCRIPT'
# 复制 scripts/aliyun/server-deploy.sh 的内容到这里
DEPLOY_SCRIPT

chmod +x /tmp/deploy.sh
bash /tmp/deploy.sh
```

### 方式2: 分步执行

**步骤1: 连接服务器**
```bash
ssh -p 50518 root@8.145.33.61
# 密码: 6b3fPk9n!
```

**步骤2: 安装Docker和Docker Compose**
```bash
apt-get update
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# 安装Docker Compose
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

**步骤3: 克隆项目**
```bash
cd /opt
git clone https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git invoice-app
cd invoice-app
```

**步骤4: 配置环境变量**
```bash
# 生成密钥
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)

# 创建.env文件
cat > .env << 'EOF'
PROJECT_NAME=智能发票识别系统
ENVIRONMENT=production
DOMAIN=8.145.33.61
STACK_NAME=invoice-app-production
FRONTEND_HOST=dashboard.8.145.33.61

DOCKER_IMAGE_BACKEND=invoice-app-backend
DOCKER_IMAGE_FRONTEND=invoice-app-frontend
TAG=latest

SECRET_KEY=生成的密钥
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123456

POSTGRES_SERVER=8.145.33.61
POSTGRES_PORT=50511
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=invoice_db

REDIS_PASSWORD=
BACKEND_CORS_ORIGINS=http://8.145.33.61:5173,http://localhost:5173,http://8.145.33.61:8000

TRAEFIK_USERNAME=admin
TRAEFIK_PASSWORD=admin123456
TRAEFIK_EMAIL=admin@example.com
EOF

# 替换SECRET_KEY
sed -i "s|SECRET_KEY=生成的密钥|SECRET_KEY=$SECRET_KEY|g" .env
```

**步骤5: 创建数据库（如果不存在）**
```bash
# 连接到PostgreSQL
psql -h 8.145.33.61 -p 50511 -U postgres -d postgres

# 在PostgreSQL中执行
CREATE DATABASE invoice_db;
\q
```

**步骤6: 构建镜像**
```bash
# 构建后端
cd backend
docker build -t invoice-app-backend:latest .
cd ..

# 构建前端
cd frontend
docker build --build-arg VITE_API_URL=http://8.145.33.61:8000 -t invoice-app-frontend:latest .
cd ..
```

**步骤7: 部署服务**
```bash
# 创建Docker网络
docker network create traefik-public 2>/dev/null || true

# 如果存在外部数据库配置，使用它
if [ -f docker-compose.production.external-db.yml ]; then
    docker compose -f docker-compose.yml -f docker-compose.production.external-db.yml --profile no-db up -d redis prestart backend frontend adminer
else
    docker compose -f docker-compose.yml up -d redis prestart backend frontend adminer
fi
```

**步骤8: 检查服务状态**
```bash
docker compose ps
docker compose logs -f
```

## 验证部署

### 检查服务
```bash
# 查看容器状态
docker ps

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend

# 测试API
curl http://8.145.33.61:8000/api/v1/utils/health-check/
```

### 访问地址
- **前端**: http://8.145.33.61:5173
- **API文档**: http://8.145.33.61:8000/docs
- **API健康检查**: http://8.145.33.61:8000/api/v1/utils/health-check/

## 防火墙配置

确保以下端口已开放：
- **8000**: 后端API
- **5173**: 前端开发服务器（如果使用）
- **80**: HTTP（如果使用Traefik）
- **443**: HTTPS（如果使用Traefik）

```bash
# 检查端口
netstat -tlnp | grep -E "8000|5173|80|443"

# 如果需要开放端口（使用ufw）
ufw allow 8000/tcp
ufw allow 5173/tcp
ufw allow 80/tcp
ufw allow 443/tcp
```

## 常见问题

### 1. 数据库连接失败
```bash
# 测试数据库连接
psql -h 8.145.33.61 -p 50511 -U postgres -d invoice_db

# 检查环境变量
cat .env | grep POSTGRES
```

### 2. 端口被占用
```bash
# 查看端口占用
netstat -tlnp | grep 8000
netstat -tlnp | grep 5173

# 停止占用端口的服务或修改端口配置
```

### 3. 镜像构建失败
```bash
# 查看构建日志
docker build -t invoice-app-backend:latest backend/ 2>&1 | tee build.log

# 检查Dockerfile
cat backend/Dockerfile
```

### 4. 服务无法启动
```bash
# 查看详细日志
docker compose logs backend
docker compose logs frontend

# 检查环境变量
docker exec invoice-app-backend-1 env | grep -E "POSTGRES|SECRET"
```

## 后续操作

### 配置数据库迁移
```bash
# 进入后端容器
docker exec -it invoice-app-backend-1 bash

# 运行迁移
alembic upgrade head
```

### 配置定时备份
```bash
# 编辑crontab
crontab -e

# 添加备份任务
0 2 * * * /opt/invoice-app/scripts/aliyun/backup-db.sh >> /var/log/invoice-backup.log 2>&1
```

## 联系支持

如遇到问题，请：
1. 查看服务日志
2. 检查环境变量配置
3. 验证数据库连接
4. 联系技术支持

