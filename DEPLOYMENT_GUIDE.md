# 阿里云ECS部署快速指南

## 📋 部署流程概览

```
本地准备 → 服务器初始化 → 构建镜像 → 配置环境 → 部署应用 → 配置备份
```

## 🚀 快速开始

### 前置条件检查

在开始部署前，请确保：

1. ✅ ECS实例已创建（推荐：ecs.c6.xlarge，4核8GB，Ubuntu 22.04）
2. ✅ 安全组已配置（80, 443, 22端口）
3. ✅ 域名已准备并解析到ECS公网IP
4. ✅ 阿里云容器镜像服务已创建
5. ✅ 本地已安装Docker Desktop（用于构建镜像）

### 步骤1: 本地准备 ✅ 在本地执行

**Windows用户**:
```powershell
# 运行部署准备检查
powershell -ExecutionPolicy Bypass -File scripts/aliyun/prepare-deployment.ps1
```

**Linux/Mac用户**:
```bash
# 运行部署准备检查
bash scripts/aliyun/prepare-deployment.sh
```

这将验证所有必要的文件是否存在。

### 步骤2: 初始化服务器 ⚠️ 在ECS上执行

```bash
# 1. 连接服务器
ssh root@your-server-ip

# 2. 上传项目文件
# 方式A: 使用git
cd /opt
git clone your-repository-url invoice-app
cd invoice-app

# 方式B: 使用scp（在本地执行）
# scp -r . root@your-server-ip:/opt/invoice-app

# 3. 运行初始化脚本
chmod +x scripts/aliyun/init-server.sh
bash scripts/aliyun/init-server.sh
```

**验证**:
```bash
docker --version
docker compose version
```

### 步骤3: 构建镜像 ⚠️ 在本地执行

**Windows PowerShell**:
```powershell
# 设置环境变量
$env:REGISTRY="your-registry.cn-hangzhou.aliyuncs.com"
$env:NAMESPACE="invoice"
$env:ALIYUN_REGISTRY_USERNAME="your-username"
$env:ALIYUN_REGISTRY_PASSWORD="your-password"

# 使用Git Bash或WSL运行
bash scripts/aliyun/build-and-push.sh v1.0.0
```

**Linux/Mac**:
```bash
# 设置环境变量
export REGISTRY=your-registry.cn-hangzhou.aliyuncs.com
export NAMESPACE=invoice
export ALIYUN_REGISTRY_USERNAME=your-username
export ALIYUN_REGISTRY_PASSWORD=your-password

# 运行构建脚本
bash scripts/aliyun/build-and-push.sh v1.0.0
```

**验证**: 登录阿里云控制台，检查镜像是否已上传。

### 步骤4: 配置环境 ⚠️ 在ECS上执行

```bash
# 1. 连接服务器
ssh root@your-server-ip
cd /opt/invoice-app

# 2. 复制环境变量模板
cp scripts/aliyun/.env.production.template .env

# 3. 编辑环境变量
vim .env
```

**必须配置的关键项**:

```bash
# 域名配置
DOMAIN=your-domain.com
FRONTEND_HOST=dashboard.your-domain.com

# Docker镜像配置
DOCKER_IMAGE_BACKEND=your-registry.cn-hangzhou.aliyuncs.com/invoice/backend
DOCKER_IMAGE_FRONTEND=your-registry.cn-hangzhou.aliyuncs.com/invoice/frontend
TAG=v1.0.0

# 生成安全密钥（在服务器上执行）
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# 将生成的密钥填入以下配置：
SECRET_KEY=<生成的密钥>
POSTGRES_PASSWORD=<生成的密钥>

# 管理员账户
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=<设置安全密码>

# Traefik配置
TRAEFIK_USERNAME=admin
TRAEFIK_PASSWORD=<设置Traefik管理密码>
TRAEFIK_EMAIL=admin@your-domain.com
```

### 步骤5: 部署应用 ⚠️ 在ECS上执行

```bash
# 1. 确保在项目目录
cd /opt/invoice-app

# 2. 运行部署脚本
chmod +x scripts/aliyun/deploy-production.sh
bash scripts/aliyun/deploy-production.sh
```

**验证部署**:
```bash
# 检查服务状态
docker compose -f docker-compose.yml -f docker-compose.production.yml ps

# 查看日志
docker compose -f docker-compose.yml -f docker-compose.production.yml logs -f

# 测试API（等待几分钟让服务完全启动）
curl https://api.your-domain.com/api/v1/utils/health-check/
```

### 步骤6: 配置备份 ⚠️ 在ECS上执行

```bash
# 1. 测试备份脚本
chmod +x scripts/aliyun/backup-db.sh
./scripts/aliyun/backup-db.sh

# 2. 配置定时任务
crontab -e

# 3. 添加以下行（每天凌晨2点备份）
0 2 * * * /opt/invoice-app/scripts/aliyun/backup-db.sh >> /var/log/invoice-backup.log 2>&1
```

**验证备份**:
```bash
# 检查备份文件
ls -lh /opt/invoice-app/backups/

# 查看备份日志
tail -f /var/log/invoice-backup.log
```

## ✅ 部署后验证

访问以下地址验证部署：

- 🌐 **前端**: https://dashboard.your-domain.com
- 📚 **API文档**: https://api.your-domain.com/docs
- 🗄️ **数据库管理**: https://adminer.your-domain.com
- 🔧 **Traefik面板**: https://traefik.your-domain.com

## 📚 详细文档

- **完整部署文档**: [docs/aliyun-deployment.md](docs/aliyun-deployment.md)
- **部署检查清单**: [scripts/aliyun/deployment-checklist.md](scripts/aliyun/deployment-checklist.md)
- **脚本使用说明**: [scripts/aliyun/README.md](scripts/aliyun/README.md)

## 🔧 常用命令

### 查看服务状态
```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml ps
```

### 查看日志
```bash
# 所有服务
docker compose -f docker-compose.yml -f docker-compose.production.yml logs -f

# 特定服务
docker compose logs -f backend
docker compose logs -f frontend
```

### 重启服务
```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml restart
```

### 更新部署
```bash
# 1. 构建新镜像（在本地）
bash scripts/aliyun/build-and-push.sh v1.1.0

# 2. 更新TAG（在服务器上）
vim /opt/invoice-app/.env
# 修改 TAG=v1.1.0

# 3. 重新部署（在服务器上）
bash scripts/aliyun/deploy-production.sh
```

## ❓ 常见问题

### Q: 初始化脚本执行失败？
**A**: 检查网络连接，确保可以访问Docker官方源。如果网络受限，可以使用阿里云镜像源。

### Q: 镜像构建失败？
**A**: 
- 检查Docker是否运行：`docker ps`
- 检查镜像仓库登录：`docker login`
- 检查网络连接

### Q: 部署失败？
**A**:
- 检查环境变量：`cat /opt/invoice-app/.env`
- 检查镜像是否存在：`docker images | grep invoice`
- 查看容器日志：`docker compose logs`

### Q: SSL证书申请失败？
**A**:
- 检查域名解析：`nslookup api.your-domain.com`
- 检查端口开放：`netstat -tlnp | grep -E "80|443"`
- 查看Traefik日志：`docker logs traefik-public-traefik-1`

## 📞 获取帮助

如遇到问题：
1. 查看 [部署检查清单](scripts/aliyun/deployment-checklist.md)
2. 查看 [详细部署文档](docs/aliyun-deployment.md)
3. 检查服务日志
4. 联系技术支持团队

---

**祝部署顺利！** 🎉

