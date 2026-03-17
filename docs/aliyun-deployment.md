# 阿里云ECS部署指南

本文档提供智能发票识别系统在阿里云ECS上的完整部署指南。

## 目录

- [一、准备工作](#一准备工作)
- [二、ECS服务器配置](#二ecs服务器配置)
- [三、服务器初始化](#三服务器初始化)
- [四、构建和推送Docker镜像](#四构建和推送docker镜像)
- [五、配置环境变量](#五配置环境变量)
- [六、部署应用](#六部署应用)
- [七、域名和SSL配置](#七域名和ssl配置)
- [八、数据备份](#八数据备份)
- [九、监控和维护](#九监控和维护)
- [十、故障排查](#十故障排查)

## 一、准备工作

### 1.1 阿里云资源准备

在开始部署之前，需要准备以下资源：

1. **ECS云服务器**
   - 实例规格：ecs.c6.xlarge (4核8GB) 或更高
   - 操作系统：Ubuntu 22.04 LTS
   - 系统盘：40GB SSD云盘
   - 数据盘：100GB SSD云盘（可选，用于数据存储）

2. **容器镜像服务**
   - 创建容器镜像服务实例
   - 创建命名空间：`invoice`
   - 创建镜像仓库：`backend` 和 `frontend`

3. **域名**
   - 已备案的域名（用于SSL证书申请）
   - 域名DNS解析权限

4. **安全组配置**
   ```
   入方向规则：
   - HTTP (80)    : 0.0.0.0/0
   - HTTPS (443)  : 0.0.0.0/0
   - SSH (22)     : 您的IP地址（限制访问）
   
   出方向规则：
   - 全部开放
   ```

### 1.2 本地环境准备

- Git客户端
- Docker Desktop（用于本地构建镜像）
- SSH客户端（用于连接服务器）

## 二、ECS服务器配置

### 2.1 购买ECS实例

1. 登录阿里云控制台
2. 进入ECS实例页面
3. 选择配置：
   - **实例规格**：ecs.c6.xlarge (4核8GB)
   - **镜像**：Ubuntu 22.04 LTS
   - **系统盘**：40GB SSD云盘
   - **网络**：专有网络VPC
   - **安全组**：配置上述规则

### 2.2 配置安全组

1. 在ECS控制台找到安全组
2. 添加入站规则：
   - HTTP (80端口)
   - HTTPS (443端口)
   - SSH (22端口，限制为您的IP)

### 2.3 配置弹性公网IP

1. 为ECS实例分配弹性公网IP
2. 记录公网IP地址（用于DNS解析）

## 三、服务器初始化

### 3.1 连接服务器

```bash
ssh root@your-server-ip
```

### 3.2 运行初始化脚本

将项目文件上传到服务器，或直接在服务器上克隆项目：

```bash
# 克隆项目（或使用其他方式上传）
git clone your-repository-url
cd invoicepdf

# 运行初始化脚本
chmod +x scripts/aliyun/init-server.sh
sudo bash scripts/aliyun/init-server.sh
```

初始化脚本会：
- 更新系统包
- 安装Docker和Docker Compose
- 创建必要的目录结构
- 创建Docker网络
- 配置防火墙规则

### 3.3 验证安装

```bash
# 检查Docker版本
docker --version
docker compose version

# 检查Docker网络
docker network ls | grep traefik-public
```

## 四、构建和推送Docker镜像

### 4.1 配置阿里云容器镜像服务

1. 登录阿里云控制台
2. 进入容器镜像服务
3. 创建命名空间：`invoice`
4. 创建镜像仓库：
   - `backend`（后端镜像）
   - `frontend`（前端镜像）

### 4.2 获取镜像仓库地址

记录以下信息：
- 镜像仓库地址：`your-registry.cn-hangzhou.aliyuncs.com`
- 命名空间：`invoice`
- 登录用户名和密码

### 4.3 构建和推送镜像

在本地开发机器上：

```bash
# 设置环境变量
export REGISTRY=your-registry.cn-hangzhou.aliyuncs.com
export NAMESPACE=invoice
export ALIYUN_REGISTRY_USERNAME=your-username
export ALIYUN_REGISTRY_PASSWORD=your-password

# 运行构建脚本
chmod +x scripts/aliyun/build-and-push.sh
./scripts/aliyun/build-and-push.sh v1.0.0
```

或者手动构建：

```bash
# 登录镜像仓库
docker login --username=your-username your-registry.cn-hangzhou.aliyuncs.com

# 构建后端镜像
cd backend
docker build -t your-registry.cn-hangzhou.aliyuncs.com/invoice/backend:v1.0.0 .
docker push your-registry.cn-hangzhou.aliyuncs.com/invoice/backend:v1.0.0

# 构建前端镜像
cd ../frontend
docker build --build-arg VITE_API_URL=https://api.your-domain.com -t your-registry.cn-hangzhou.aliyuncs.com/invoice/frontend:v1.0.0 .
docker push your-registry.cn-hangzhou.aliyuncs.com/invoice/frontend:v1.0.0
```

## 五、配置环境变量

### 5.1 创建环境变量文件

在服务器上创建环境变量文件：

```bash
# 复制模板文件
cp scripts/aliyun/.env.production.template /opt/invoice-app/.env

# 编辑环境变量
vim /opt/invoice-app/.env
```

### 5.2 配置关键参数

必须修改以下配置项：

```bash
# 域名配置
DOMAIN=your-domain.com
FRONTEND_HOST=dashboard.your-domain.com

# Docker镜像配置
DOCKER_IMAGE_BACKEND=your-registry.cn-hangzhou.aliyuncs.com/invoice/backend
DOCKER_IMAGE_FRONTEND=your-registry.cn-hangzhou.aliyuncs.com/invoice/frontend
TAG=v1.0.0

# 安全密钥（必须生成）
SECRET_KEY=<使用python3生成>
POSTGRES_PASSWORD=<使用python3生成>
FIRST_SUPERUSER_PASSWORD=<设置管理员密码>

# Traefik配置
TRAEFIK_USERNAME=admin
TRAEFIK_PASSWORD=<设置Traefik管理密码>
TRAEFIK_EMAIL=admin@your-domain.com
```

### 5.3 生成安全密钥

```bash
# 生成SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成POSTGRES_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 六、部署应用

### 6.1 上传项目文件

将项目文件上传到服务器：

```bash
# 方式1：使用git
cd /opt/invoice-app
git clone your-repository-url .

# 方式2：使用scp
scp -r /local/path/invoicepdf root@your-server-ip:/opt/invoice-app
```

### 6.2 部署Traefik

Traefik会在部署脚本中自动部署，也可以手动部署：

```bash
cd /opt/traefik-public
cp /opt/invoice-app/docker-compose.traefik.yml .

# 设置环境变量
export DOMAIN=your-domain.com
export USERNAME=admin
export PASSWORD=your-password
export HASHED_PASSWORD=$(openssl passwd -apr1 "$PASSWORD")
export EMAIL=admin@your-domain.com

# 启动Traefik
docker compose -f docker-compose.traefik.yml up -d
```

### 6.3 部署应用服务

```bash
cd /opt/invoice-app

# 运行部署脚本
chmod +x scripts/aliyun/deploy-production.sh
sudo bash scripts/aliyun/deploy-production.sh
```

部署脚本会：
1. 检查环境变量配置
2. 部署Traefik（如果尚未部署）
3. 拉取最新镜像
4. 停止旧容器
5. 启动新容器
6. 检查服务状态

### 6.4 验证部署

```bash
# 检查服务状态
docker compose -f docker-compose.yml -f docker-compose.production.yml ps

# 查看服务日志
docker compose -f docker-compose.yml -f docker-compose.production.yml logs -f

# 检查服务健康状态
curl https://api.your-domain.com/api/v1/utils/health-check/
```

## 七、域名和SSL配置

### 7.1 DNS配置

在阿里云DNS控制台配置A记录：

```
类型    主机记录    记录值（ECS公网IP）
A       api        your-server-ip
A       dashboard  your-server-ip
A       adminer    your-server-ip
A       traefik    your-server-ip
```

### 7.2 SSL证书

Traefik会自动通过Let's Encrypt申请SSL证书：

1. 确保域名已正确解析到ECS公网IP
2. 确保80和443端口已开放
3. 确保Traefik环境变量中的EMAIL已配置
4. 等待几分钟，Traefik会自动申请证书

验证SSL证书：

```bash
# 检查证书状态
docker logs traefik-public-traefik-1 | grep acme

# 测试HTTPS访问
curl -I https://api.your-domain.com
```

## 八、数据备份

### 8.1 配置自动备份

```bash
# 编辑crontab
crontab -e

# 添加每天凌晨2点备份
0 2 * * * /opt/invoice-app/scripts/aliyun/backup-db.sh >> /var/log/invoice-backup.log 2>&1
```

### 8.2 手动备份

```bash
# 运行备份脚本
chmod +x scripts/aliyun/backup-db.sh
./scripts/aliyun/backup-db.sh
```

### 8.3 配置OSS备份（可选）

1. 安装ossutil工具
2. 配置OSS访问凭证
3. 在备份脚本中启用OSS上传

```bash
# 在.env文件中配置
OSS_ENABLED=true
OSS_BUCKET=your-bucket-name
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
```

## 九、监控和维护

### 9.1 配置阿里云云监控

1. 在ECS控制台安装云监控Agent
2. 配置监控项：
   - CPU使用率
   - 内存使用率
   - 磁盘使用率
   - 网络流量
3. 设置告警规则

### 9.2 日志管理

```bash
# 查看服务日志
docker compose -f docker-compose.yml -f docker-compose.production.yml logs -f backend
docker compose -f docker-compose.yml -f docker-compose.production.yml logs -f frontend

# 查看最近100行日志
docker compose -f docker-compose.yml -f docker-compose.production.yml logs --tail=100
```

### 9.3 性能监控

```bash
# 查看容器资源使用情况
docker stats

# 查看磁盘使用情况
df -h
du -sh /opt/invoice-app/data/*
```

## 十、故障排查

### 10.1 服务无法启动

```bash
# 检查容器状态
docker compose -f docker-compose.yml -f docker-compose.production.yml ps

# 查看错误日志
docker compose -f docker-compose.yml -f docker-compose.production.yml logs backend
docker compose -f docker-compose.yml -f docker-compose.production.yml logs frontend

# 检查环境变量
docker exec invoice-app-backend-1 env | grep -E "POSTGRES|SECRET"
```

### 10.2 SSL证书申请失败

```bash
# 检查Traefik日志
docker logs traefik-public-traefik-1

# 检查域名解析
nslookup api.your-domain.com

# 检查端口开放
netstat -tlnp | grep -E "80|443"
```

### 10.3 数据库连接失败

```bash
# 检查数据库容器状态
docker ps | grep db

# 检查数据库日志
docker logs invoice-app-db-1

# 测试数据库连接
docker exec invoice-app-db-1 psql -U postgres -d invoice_db -c "SELECT 1;"
```

### 10.4 前端无法访问后端

```bash
# 检查CORS配置
grep BACKEND_CORS_ORIGINS /opt/invoice-app/.env

# 检查API URL配置
docker exec invoice-app-frontend-1 env | grep VITE_API_URL

# 测试API连接
curl https://api.your-domain.com/api/v1/utils/health-check/
```

## 十一、常用命令

### 11.1 服务管理

```bash
# 启动服务
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d

# 停止服务
docker compose -f docker-compose.yml -f docker-compose.production.yml down

# 重启服务
docker compose -f docker-compose.yml -f docker-compose.production.yml restart

# 查看服务状态
docker compose -f docker-compose.yml -f docker-compose.production.yml ps
```

### 11.2 更新部署

```bash
# 拉取最新镜像
docker compose -f docker-compose.yml -f docker-compose.production.yml pull

# 重新部署
cd /opt/invoice-app
bash scripts/aliyun/deploy-production.sh
```

### 11.3 数据库操作

```bash
# 进入数据库容器
docker exec -it invoice-app-db-1 bash

# 连接数据库
docker exec -it invoice-app-db-1 psql -U postgres -d invoice_db

# 执行数据库迁移
docker exec invoice-app-backend-1 alembic upgrade head
```

## 十二、安全建议

1. **定期更新系统**
   ```bash
   apt-get update && apt-get upgrade -y
   ```

2. **定期更新Docker镜像**
   ```bash
   docker compose pull
   docker compose up -d
   ```

3. **配置防火墙**
   ```bash
   ufw enable
   ufw status
   ```

4. **使用强密码**
   - 所有密码使用随机生成的强密码
   - 定期更换密码

5. **限制SSH访问**
   - 仅允许特定IP访问SSH
   - 使用SSH密钥认证

6. **启用日志审计**
   - 定期检查日志文件
   - 配置日志告警

## 十三、成本优化

1. **选择合适的实例规格**
   - 根据实际负载选择合适的ECS规格
   - 使用弹性伸缩（如需要）

2. **优化存储**
   - 定期清理日志文件
   - 清理旧的备份文件

3. **使用预留实例**
   - 长期使用可考虑预留实例
   - 可节省30-50%成本

## 十四、后续优化

1. **高可用部署**
   - 使用SLB + 多台ECS
   - 配置数据库主从复制

2. **使用RDS**
   - 迁移到RDS PostgreSQL
   - 获得更好的数据库性能和管理

3. **CDN加速**
   - 前端静态资源使用CDN
   - 提升访问速度

4. **日志服务**
   - 集成阿里云日志服务(SLS)
   - 集中管理和分析日志

5. **CI/CD自动化**
   - 配置GitHub Actions自动部署
   - 实现持续集成和部署

## 附录

### A. 文件结构

```
/opt/invoice-app/
├── .env                          # 环境变量配置
├── docker-compose.yml            # Docker Compose配置
├── docker-compose.production.yml # 生产环境配置
├── scripts/
│   └── aliyun/
│       ├── init-server.sh        # 服务器初始化脚本
│       ├── build-and-push.sh     # 镜像构建脚本
│       ├── deploy-production.sh  # 部署脚本
│       └── backup-db.sh          # 备份脚本
├── data/
│   ├── postgres/                 # 数据库数据
│   └── redis/                    # Redis数据
├── uploads/                      # 文件上传目录
└── backups/                      # 备份目录

/opt/traefik-public/
└── docker-compose.traefik.yml    # Traefik配置
```

### B. 环境变量说明

详细的环境变量说明请参考 `scripts/aliyun/.env.production.template`

### C. 相关链接

- [阿里云ECS文档](https://help.aliyun.com/product/25365.html)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [Traefik文档](https://doc.traefik.io/traefik/)

### D. 技术支持

如遇到问题，请：
1. 查看本文档的故障排查章节
2. 检查服务日志
3. 联系技术支持团队

