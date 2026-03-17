# 阿里云ECS部署检查清单

## 部署前准备

### 1. 服务器准备
- [ ] ECS实例已创建（推荐：ecs.c6.xlarge，4核8GB）
- [ ] 操作系统：Ubuntu 22.04 LTS
- [ ] 系统盘：40GB SSD云盘
- [ ] 数据盘：100GB SSD云盘（可选）
- [ ] 安全组已配置：
  - [ ] HTTP (80端口) - 0.0.0.0/0
  - [ ] HTTPS (443端口) - 0.0.0.0/0
  - [ ] SSH (22端口) - 限制为您的IP
- [ ] 弹性公网IP已分配
- [ ] SSH密钥或密码已准备

### 2. 域名配置
- [ ] 域名已备案（如需要）
- [ ] DNS解析已配置：
  - [ ] api.your-domain.com → ECS公网IP
  - [ ] dashboard.your-domain.com → ECS公网IP
  - [ ] adminer.your-domain.com → ECS公网IP
  - [ ] traefik.your-domain.com → ECS公网IP

### 3. 阿里云服务
- [ ] 容器镜像服务实例已创建
- [ ] 命名空间已创建：`invoice`
- [ ] 镜像仓库已创建：
  - [ ] `backend`
  - [ ] `frontend`
- [ ] 镜像仓库登录凭证已准备：
  - [ ] 用户名
  - [ ] 密码

### 4. 本地环境
- [ ] Git已安装
- [ ] Docker Desktop已安装（用于构建镜像）
- [ ] SSH客户端已准备
- [ ] 项目代码已克隆或下载

## 部署步骤

### 步骤1: 初始化服务器 ⚠️ 在ECS上执行

```bash
# 1. 连接服务器
ssh root@your-server-ip

# 2. 上传项目文件（选择一种方式）
# 方式A: 使用git
cd /opt
git clone your-repository-url invoice-app
cd invoice-app

# 方式B: 使用scp（在本地执行）
# scp -r /local/path/invoicepdf root@your-server-ip:/opt/invoice-app

# 3. 运行初始化脚本
chmod +x scripts/aliyun/init-server.sh
bash scripts/aliyun/init-server.sh
```

**验证**:
```bash
docker --version
docker compose version
docker network ls | grep traefik-public
```

### 步骤2: 构建镜像 ⚠️ 在本地或CI/CD环境执行

```bash
# 1. 设置环境变量
export REGISTRY=your-registry.cn-hangzhou.aliyuncs.com
export NAMESPACE=invoice
export ALIYUN_REGISTRY_USERNAME=your-username
export ALIYUN_REGISTRY_PASSWORD=your-password

# 2. 运行构建脚本
chmod +x scripts/aliyun/build-and-push.sh
./scripts/aliyun/build-and-push.sh v1.0.0
```

**验证**:
- 登录阿里云控制台
- 检查容器镜像服务中的镜像是否已上传

### 步骤3: 配置环境 ⚠️ 在ECS上执行

```bash
# 1. 连接服务器
ssh root@your-server-ip
cd /opt/invoice-app

# 2. 复制环境变量模板
cp scripts/aliyun/.env.production.template .env

# 3. 编辑环境变量
vim .env
# 或使用其他编辑器
nano .env
```

**必须配置的项**:
- `DOMAIN`: 您的域名
- `DOCKER_IMAGE_BACKEND`: 后端镜像地址
- `DOCKER_IMAGE_FRONTEND`: 前端镜像地址
- `TAG`: 镜像标签（如 v1.0.0）
- `SECRET_KEY`: 生成的安全密钥
- `POSTGRES_PASSWORD`: 生成的数据库密码
- `FIRST_SUPERUSER`: 管理员邮箱
- `FIRST_SUPERUSER_PASSWORD`: 管理员密码
- `TRAEFIK_PASSWORD`: Traefik管理密码

**生成密钥**:
```bash
# 生成SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成POSTGRES_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 步骤4: 部署应用 ⚠️ 在ECS上执行

```bash
# 1. 连接服务器
ssh root@your-server-ip
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

# 测试API
curl https://api.your-domain.com/api/v1/utils/health-check/
```

### 步骤5: 配置备份 ⚠️ 在ECS上执行

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

## 部署后验证

### 1. 服务访问
- [ ] 前端访问：https://dashboard.your-domain.com
- [ ] API文档：https://api.your-domain.com/docs
- [ ] 数据库管理：https://adminer.your-domain.com
- [ ] Traefik面板：https://traefik.your-domain.com

### 2. SSL证书
- [ ] SSL证书已自动申请
- [ ] HTTPS访问正常
- [ ] HTTP自动跳转到HTTPS

### 3. 功能测试
- [ ] 用户登录功能正常
- [ ] API接口正常响应
- [ ] 文件上传功能正常
- [ ] 数据库连接正常

### 4. 监控配置
- [ ] 阿里云云监控Agent已安装
- [ ] 监控告警已配置
- [ ] 日志收集正常

## 常见问题

### Q1: 初始化脚本执行失败
**A**: 检查网络连接，确保可以访问Docker官方源

### Q2: 镜像构建失败
**A**: 
- 检查Docker是否运行
- 检查镜像仓库登录凭证
- 检查网络连接

### Q3: 部署失败
**A**:
- 检查环境变量配置
- 检查镜像是否存在
- 查看容器日志：`docker compose logs`

### Q4: SSL证书申请失败
**A**:
- 检查域名解析是否正确
- 检查80和443端口是否开放
- 检查Traefik日志

### Q5: 数据库连接失败
**A**:
- 检查数据库容器状态
- 检查环境变量中的数据库密码
- 查看数据库日志

## 后续维护

### 更新部署
```bash
# 1. 构建新镜像
./scripts/aliyun/build-and-push.sh v1.1.0

# 2. 在服务器上更新TAG
vim /opt/invoice-app/.env
# 修改 TAG=v1.1.0

# 3. 重新部署
bash scripts/aliyun/deploy-production.sh
```

### 查看日志
```bash
# 查看所有服务日志
docker compose -f docker-compose.yml -f docker-compose.production.yml logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 重启服务
```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml restart
```

## 联系支持

如遇到问题，请：
1. 查看本文档的常见问题部分
2. 查看详细部署文档：`docs/aliyun-deployment.md`
3. 检查服务日志
4. 联系技术支持团队

