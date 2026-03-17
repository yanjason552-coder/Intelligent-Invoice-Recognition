# 部署检查清单

## 📋 部署前必须准备的信息

### 1. 服务器信息 ✅
- [x] ECS实例已创建
- [x] 操作系统：Ubuntu 22.04 LTS
- [x] Docker已安装并配置镜像源
- [ ] Docker Compose已安装
- [ ] 安全组已配置（80, 443, 22端口）

### 2. 域名配置 ⚠️
- [ ] 域名已准备（如果使用IP访问可跳过）
- [ ] DNS解析已配置：
  - [ ] api.your-domain.com → ECS公网IP
  - [ ] dashboard.your-domain.com → ECS公网IP
  - [ ] adminer.your-domain.com → ECS公网IP
  - [ ] traefik.your-domain.com → ECS公网IP

### 3. 数据库配置 ⚠️
**选项A: 使用外部PostgreSQL数据库（推荐）**
- [ ] 数据库主机地址: `8.145.33.61`
- [ ] 数据库端口: `50511`
- [ ] 数据库用户名: `postgres`
- [ ] 数据库密码: `postgres123`
- [ ] 数据库名称: `app` 或 `invoice_db`
- [ ] 数据库已创建

**选项B: 使用Docker Compose中的PostgreSQL**
- [ ] 使用默认配置（POSTGRES_SERVER=db）

### 4. Docker镜像配置 ⚠️
**选项A: 使用阿里云容器镜像服务（推荐生产环境）**
- [ ] 镜像仓库地址: `registry.cn-hangzhou.aliyuncs.com`
- [ ] 命名空间: `invoice`
- [ ] 后端镜像: `backend`
- [ ] 前端镜像: `frontend`
- [ ] 镜像标签: `v1.0.0` 或 `latest`
- [ ] 镜像已构建并推送到仓库

**选项B: 在服务器上构建镜像**
- [ ] 项目代码已上传到服务器
- [ ] Dockerfile存在且正确

### 5. 环境变量配置 ⚠️ 必须配置

#### 基本配置
- [ ] `DOMAIN`: 您的域名或IP地址
- [ ] `STACK_NAME`: Docker Compose堆栈名称（如：invoice-app-production）
- [ ] `FRONTEND_HOST`: 前端访问地址（如：dashboard.your-domain.com）

#### 安全配置（必须修改！）
- [ ] `SECRET_KEY`: 生成的安全密钥
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] `POSTGRES_PASSWORD`: 数据库密码（如果使用外部数据库，使用实际密码）
- [ ] `FIRST_SUPERUSER`: 管理员邮箱（如：admin@example.com）
- [ ] `FIRST_SUPERUSER_PASSWORD`: 管理员密码

#### Docker镜像配置（如果使用镜像部署）
- [ ] `DOCKER_IMAGE_BACKEND`: 后端镜像完整地址
- [ ] `DOCKER_IMAGE_FRONTEND`: 前端镜像完整地址
- [ ] `TAG`: 镜像标签

#### Traefik配置
- [ ] `TRAEFIK_USERNAME`: Traefik管理用户名（默认：admin）
- [ ] `TRAEFIK_PASSWORD`: Traefik管理密码
- [ ] `TRAEFIK_EMAIL`: Let's Encrypt证书邮箱

#### 其他配置
- [ ] `BACKEND_CORS_ORIGINS`: CORS允许的域名列表
- [ ] `SMTP_HOST`: SMTP服务器（可选，用于邮件功能）
- [ ] `SMTP_USER`: SMTP用户名（可选）
- [ ] `SMTP_PASSWORD`: SMTP密码（可选）

## 🚀 部署步骤

### 步骤1: 在服务器上运行准备脚本
```bash
cd /opt/invoice-app
bash scripts/aliyun/prepare-deployment.sh
```

### 步骤2: 配置环境变量
```bash
# 如果.env文件不存在，从模板创建
cp scripts/aliyun/.env.production.template .env

# 编辑.env文件
vim .env
# 或使用其他编辑器
nano .env
```

### 步骤3: 运行部署检查
```bash
bash scripts/aliyun/check-deployment.sh
```

### 步骤4: 部署应用
```bash
bash scripts/aliyun/deploy-production.sh
```

### 步骤5: 检查部署状态
```bash
bash scripts/aliyun/check-deployment-status.sh
```

## ✅ 部署后验证

### 1. 服务状态检查
```bash
# 检查所有服务状态
docker compose -f docker-compose.yml -f docker-compose.production.yml ps

# 检查服务日志
docker compose -f docker-compose.yml -f docker-compose.production.yml logs -f
```

### 2. 访问测试
- [ ] 前端访问：https://dashboard.your-domain.com
- [ ] API文档：https://api.your-domain.com/docs
- [ ] 健康检查：https://api.your-domain.com/api/v1/utils/health-check/
- [ ] 数据库管理：https://adminer.your-domain.com
- [ ] Traefik面板：https://traefik.your-domain.com

### 3. 功能测试
- [ ] 用户登录功能正常
- [ ] API接口正常响应
- [ ] 文件上传功能正常
- [ ] 数据库连接正常

## 🔧 常用命令

### 查看日志
```bash
# 所有服务日志
docker compose -f docker-compose.yml -f docker-compose.production.yml logs -f

# 特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

### 重启服务
```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml restart
```

### 停止服务
```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml down
```

### 更新部署
```bash
# 1. 更新镜像标签
vim .env
# 修改 TAG=v1.1.0

# 2. 重新部署
bash scripts/aliyun/deploy-production.sh
```

## ❓ 常见问题

### Q1: 部署检查脚本显示错误
**A**: 运行 `bash scripts/aliyun/check-deployment.sh` 查看详细错误信息，根据提示修复。

### Q2: 服务无法启动
**A**: 
- 检查环境变量配置：`cat .env`
- 查看服务日志：`docker compose logs [service-name]`
- 检查端口占用：`netstat -tlnp | grep -E "80|443"`

### Q3: SSL证书申请失败
**A**:
- 检查域名解析：`nslookup api.your-domain.com`
- 检查80和443端口是否开放
- 查看Traefik日志：`docker logs traefik-public-traefik-1`

### Q4: 数据库连接失败
**A**:
- 检查数据库配置：`grep POSTGRES .env`
- 测试数据库连接：`psql -h [host] -p [port] -U [user] -d [db]`
- 检查防火墙规则

## 📞 获取帮助

如遇到问题：
1. 运行部署检查脚本：`bash scripts/aliyun/check-deployment.sh`
2. 运行状态检查脚本：`bash scripts/aliyun/check-deployment-status.sh`
3. 查看服务日志
4. 参考详细部署文档：`DEPLOYMENT_GUIDE.md`
