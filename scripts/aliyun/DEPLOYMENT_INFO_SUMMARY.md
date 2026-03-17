# 部署信息总结

## ✅ 已完成配置

### 1. Docker环境
- ✅ Docker已安装
- ✅ Docker镜像源已配置（中科大、网易、百度镜像）
- ✅ Docker镜像源配置脚本已创建：`~/scripts/configure_docker_mirrors.sh`

### 2. 服务器信息
- ✅ 服务器IP: `8.145.33.61`（从.env文件推断）
- ✅ 数据库服务器: `8.145.33.61:50511`（外部PostgreSQL）

## ⚠️ 需要配置的信息

### 1. 环境变量配置（.env文件）

#### 必须配置的项：

**基本配置**
- [ ] `DOMAIN`: 当前使用IP `8.145.33.61`，建议配置域名
- [ ] `STACK_NAME`: Docker Compose堆栈名称（建议：`invoice-app-production`）
- [ ] `FRONTEND_HOST`: 前端访问地址（如：`dashboard.8.145.33.61` 或 `dashboard.your-domain.com`）

**安全配置（必须修改！）**
- [ ] `SECRET_KEY`: 当前为开发密钥 `super-secret-key-for-development-only-not-changethis`
  - 需要生成新的生产环境密钥：
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] `FIRST_SUPERUSER_PASSWORD`: 当前为 `admin123`，建议修改为更安全的密码
- [ ] `POSTGRES_PASSWORD`: 当前为 `postgres123`，如果使用外部数据库，确认密码正确

**Docker镜像配置（如果使用镜像部署）**
- [ ] `DOCKER_IMAGE_BACKEND`: 后端镜像地址（如果使用阿里云镜像服务）
- [ ] `DOCKER_IMAGE_FRONTEND`: 前端镜像地址（如果使用阿里云镜像服务）
- [ ] `TAG`: 镜像标签（如：`v1.0.0` 或 `latest`）

**Traefik配置（如果使用HTTPS）**
- [ ] `TRAEFIK_USERNAME`: Traefik管理用户名（默认：`admin`）
- [ ] `TRAEFIK_PASSWORD`: Traefik管理密码
- [ ] `TRAEFIK_EMAIL`: Let's Encrypt证书邮箱

**CORS配置**
- [ ] `BACKEND_CORS_ORIGINS`: 当前配置为本地开发地址，需要添加生产环境地址

#### 可选配置：
- [ ] `SMTP_HOST`: SMTP服务器（用于邮件功能）
- [ ] `SMTP_USER`: SMTP用户名
- [ ] `SMTP_PASSWORD`: SMTP密码
- [ ] `EMAILS_FROM_EMAIL`: 发件人邮箱
- [ ] `SENTRY_DSN`: Sentry错误监控（可选）

### 2. 数据库配置

**当前配置（从.env文件推断）：**
- 数据库主机: `8.145.33.61`
- 数据库端口: `50511`
- 数据库用户: `postgres`
- 数据库密码: `postgres123`
- 数据库名称: `app`（主数据库）或 `sys`（系统数据库）

**需要确认：**
- [ ] 数据库 `invoice_db` 是否已创建（如果使用新数据库）
- [ ] 数据库连接是否正常
- [ ] 数据库用户权限是否足够

### 3. Docker镜像

**选项A: 使用阿里云容器镜像服务（推荐）**
- [ ] 创建阿里云容器镜像服务实例
- [ ] 创建命名空间：`invoice`
- [ ] 创建镜像仓库：`backend` 和 `frontend`
- [ ] 构建并推送镜像到仓库
- [ ] 配置镜像拉取凭证（如果需要）

**选项B: 在服务器上构建镜像**
- [ ] 确保项目代码已上传到服务器
- [ ] 确保Dockerfile存在且正确
- [ ] 构建镜像：`docker build -t backend:latest ./backend`

### 4. 网络和域名

**如果使用IP访问：**
- [ ] 确认安全组已开放80和443端口
- [ ] 确认防火墙规则已配置

**如果使用域名访问：**
- [ ] 域名已准备
- [ ] DNS解析已配置：
  - `api.your-domain.com` → `8.145.33.61`
  - `dashboard.your-domain.com` → `8.145.33.61`
  - `adminer.your-domain.com` → `8.145.33.61`
  - `traefik.your-domain.com` → `8.145.33.61`
- [ ] 域名已备案（如果需要）

### 5. 目录和权限

**需要创建的目录：**
- [ ] `/opt/invoice-app` - 项目目录
- [ ] `/opt/invoice-app/uploads` - 文件上传目录
- [ ] `/opt/invoice-app/data/postgres` - PostgreSQL数据目录（如果使用Docker PostgreSQL）
- [ ] `/opt/invoice-app/data/redis` - Redis数据目录
- [ ] `/opt/invoice-app/backups` - 备份目录
- [ ] `/opt/traefik-public` - Traefik配置目录

**权限设置：**
- [ ] 确保目录有正确的读写权限
- [ ] 确保Docker可以访问这些目录

### 6. Docker网络

- [ ] 创建Docker网络：`docker network create traefik-public`
- [ ] 确认网络已创建：`docker network ls | grep traefik-public`

## 🚀 快速部署步骤

### 1. 在服务器上准备环境
```bash
# 连接服务器
ssh root@8.145.33.61

# 运行准备脚本（如果项目已上传）
cd /opt/invoice-app
bash scripts/aliyun/prepare-deployment.sh
```

### 2. 配置环境变量
```bash
# 从模板创建.env文件
cp scripts/aliyun/.env.production.template .env

# 编辑.env文件，填写所有必需配置
vim .env
```

### 3. 运行部署检查
```bash
# 检查部署准备情况
bash scripts/aliyun/check-deployment.sh
```

### 4. 部署应用
```bash
# 运行部署脚本
bash scripts/aliyun/deploy-production.sh
```

### 5. 检查部署状态
```bash
# 检查服务状态
bash scripts/aliyun/check-deployment-status.sh

# 或手动检查
docker compose -f docker-compose.yml -f docker-compose.production.yml ps
```

## 📝 环境变量配置示例

基于当前配置，`.env` 文件应该类似这样：

```bash
# 项目配置
PROJECT_NAME=智能发票识别系统
ENVIRONMENT=production
DOMAIN=8.145.33.61  # 或您的域名
STACK_NAME=invoice-app-production
FRONTEND_HOST=dashboard.8.145.33.61  # 或 dashboard.your-domain.com

# Docker镜像配置（如果使用镜像）
DOCKER_IMAGE_BACKEND=your-registry.cn-hangzhou.aliyuncs.com/invoice/backend
DOCKER_IMAGE_FRONTEND=your-registry.cn-hangzhou.aliyuncs.com/invoice/frontend
TAG=latest

# 安全配置（必须修改！）
SECRET_KEY=<生成的32位安全密钥>
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=<设置安全密码>

# 数据库配置（外部PostgreSQL）
POSTGRES_SERVER=8.145.33.61
POSTGRES_PORT=50511
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=app  # 或 invoice_db

# Redis配置
REDIS_PASSWORD=

# CORS配置
BACKEND_CORS_ORIGINS=["https://dashboard.8.145.33.61","http://localhost:5173"]

# Traefik配置（如果使用HTTPS）
TRAEFIK_USERNAME=admin
TRAEFIK_PASSWORD=<设置Traefik管理密码>
TRAEFIK_EMAIL=admin@example.com

# 邮件配置（可选）
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=noreply@example.com
```

## 🔍 检查清单

运行以下命令检查部署准备情况：

```bash
# 1. 检查Docker环境
docker --version
docker compose version
docker info | grep -A 5 "Registry Mirrors"

# 2. 检查项目文件
ls -la /opt/invoice-app/
ls -la /opt/invoice-app/docker-compose*.yml

# 3. 检查环境变量
cat /opt/invoice-app/.env | grep -E "SECRET_KEY|DOMAIN|POSTGRES"

# 4. 检查Docker网络
docker network ls | grep traefik-public

# 5. 检查端口
netstat -tlnp | grep -E "80|443"

# 6. 运行完整检查
bash /opt/invoice-app/scripts/aliyun/check-deployment.sh
```

## 📞 下一步

1. **配置环境变量**: 编辑 `.env` 文件，填写所有必需配置
2. **运行部署检查**: `bash scripts/aliyun/check-deployment.sh`
3. **修复所有错误**: 根据检查结果修复配置
4. **部署应用**: `bash scripts/aliyun/deploy-production.sh`
5. **验证部署**: 访问应用并测试功能
