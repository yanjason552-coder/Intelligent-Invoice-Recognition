# 部署工具使用指南

## 📦 已创建的部署工具

### 1. Docker镜像源配置脚本
**文件**: `~/scripts/configure_docker_mirrors.sh`（在服务器上）

**用途**: 配置Docker使用国内镜像源，加速镜像下载

**使用方法**:
```bash
sudo bash ~/scripts/configure_docker_mirrors.sh
```

**状态**: ✅ 已配置完成

---

### 2. 部署准备脚本
**文件**: `scripts/aliyun/prepare-deployment.sh`

**用途**: 自动创建必要的目录、Docker网络，生成安全密钥

**使用方法**:
```bash
cd /opt/invoice-app
bash scripts/aliyun/prepare-deployment.sh
```

**功能**:
- 创建项目目录结构
- 创建Docker网络 `traefik-public`
- 从模板创建 `.env` 文件
- 自动生成安全密钥（SECRET_KEY, POSTGRES_PASSWORD）
- 检查Docker镜像源配置
- 检查防火墙配置

---

### 3. 部署前检查脚本
**文件**: `scripts/aliyun/check-deployment.sh`

**用途**: 全面检查部署所需的所有配置和文件是否就绪

**使用方法**:
```bash
cd /opt/invoice-app
bash scripts/aliyun/check-deployment.sh
```

**检查项**:
- ✅ Docker和Docker Compose安装状态
- ✅ Docker网络和镜像源配置
- ✅ 项目文件完整性
- ✅ 环境变量配置（必需和可选）
- ✅ 目录权限
- ✅ 端口可用性
- ✅ Docker镜像存在性
- ✅ Traefik部署状态

**输出**: 
- ✓ 绿色：检查通过
- ⚠ 黄色：警告（建议修复）
- ✗ 红色：错误（必须修复）

---

### 4. 部署状态检查脚本
**文件**: `scripts/aliyun/check-deployment-status.sh`

**用途**: 检查当前部署的运行状态和健康情况

**使用方法**:
```bash
cd /opt/invoice-app
bash scripts/aliyun/check-deployment-status.sh
```

**检查项**:
- Docker服务状态
- Traefik服务状态
- 应用服务状态
- 容器健康状态
- 端口监听状态
- 磁盘空间
- 最近的错误日志
- 访问地址

---

### 5. 生产环境部署脚本
**文件**: `scripts/aliyun/deploy-production.sh`

**用途**: 执行完整的生产环境部署流程

**使用方法**:
```bash
cd /opt/invoice-app
bash scripts/aliyun/deploy-production.sh
```

**功能**:
- 检查环境变量配置
- 部署Traefik（如果未部署）
- 拉取最新镜像
- 停止旧容器
- 启动新容器
- 检查服务状态
- 显示访问地址

---

### 6. 环境变量模板
**文件**: `scripts/aliyun/.env.production.template`

**用途**: 生产环境环境变量配置模板

**使用方法**:
```bash
cp scripts/aliyun/.env.production.template .env
vim .env  # 编辑配置
```

**包含配置项**:
- 项目基本配置
- Docker镜像配置
- 安全配置
- 数据库配置
- Redis配置
- CORS配置
- 邮件配置
- Traefik配置
- Sentry配置

---

## 🚀 完整部署流程

### 步骤1: 服务器初始化
```bash
# 连接服务器
ssh root@your-server-ip

# 如果Docker镜像源未配置，运行：
sudo bash ~/scripts/configure_docker_mirrors.sh
```

### 步骤2: 上传项目代码
```bash
# 方式A: 使用Git
cd /opt
git clone your-repository-url invoice-app
cd invoice-app

# 方式B: 使用SCP（在本地执行）
# scp -r /local/path/invoicepdf root@your-server-ip:/opt/invoice-app
```

### 步骤3: 运行准备脚本
```bash
cd /opt/invoice-app
bash scripts/aliyun/prepare-deployment.sh
```

### 步骤4: 配置环境变量
```bash
# 如果.env文件不存在，从模板创建
cp scripts/aliyun/.env.production.template .env

# 编辑.env文件
vim .env
# 填写所有必需配置，特别是：
# - DOMAIN
# - SECRET_KEY（会自动生成）
# - POSTGRES_PASSWORD（会自动生成）
# - FIRST_SUPERUSER_PASSWORD
# - DOCKER_IMAGE_BACKEND（如果使用镜像）
# - DOCKER_IMAGE_FRONTEND（如果使用镜像）
# - TRAEFIK_PASSWORD
# - TRAEFIK_EMAIL
```

### 步骤5: 运行部署检查
```bash
bash scripts/aliyun/check-deployment.sh
```

**如果检查通过**，继续下一步。**如果有错误**，根据提示修复配置。

### 步骤6: 部署应用
```bash
bash scripts/aliyun/deploy-production.sh
```

### 步骤7: 检查部署状态
```bash
bash scripts/aliyun/check-deployment-status.sh
```

### 步骤8: 验证访问
访问以下地址验证部署：
- 前端: https://dashboard.your-domain.com
- API文档: https://api.your-domain.com/docs
- 健康检查: https://api.your-domain.com/api/v1/utils/health-check/
- 数据库管理: https://adminer.your-domain.com
- Traefik面板: https://traefik.your-domain.com

---

## 🔧 常用操作

### 查看服务日志
```bash
# 所有服务
docker compose -f docker-compose.yml -f docker-compose.production.yml logs -f

# 特定服务
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

### 检查服务状态
```bash
# 快速检查
docker compose -f docker-compose.yml -f docker-compose.production.yml ps

# 详细检查
bash scripts/aliyun/check-deployment-status.sh
```

---

## 📚 相关文档

- **部署指南**: `DEPLOYMENT_GUIDE.md`
- **部署检查清单**: `DEPLOYMENT_CHECKLIST.md`
- **部署信息总结**: `DEPLOYMENT_INFO_SUMMARY.md`
- **服务器初始化脚本**: `init-server.sh`

---

## ❓ 故障排查

### 问题1: 部署检查失败
**解决**: 
1. 运行 `bash scripts/aliyun/check-deployment.sh` 查看详细错误
2. 根据错误提示修复配置
3. 重新运行检查

### 问题2: 服务无法启动
**解决**:
1. 检查环境变量: `cat .env`
2. 查看服务日志: `docker compose logs [service-name]`
3. 检查端口占用: `netstat -tlnp | grep -E "80|443"`
4. 运行状态检查: `bash scripts/aliyun/check-deployment-status.sh`

### 问题3: 镜像拉取失败
**解决**:
1. 检查Docker镜像源配置: `docker info | grep -A 5 "Registry Mirrors"`
2. 如果未配置，运行: `sudo bash ~/scripts/configure_docker_mirrors.sh`
3. 检查镜像仓库登录: `docker login your-registry`

### 问题4: 数据库连接失败
**解决**:
1. 检查数据库配置: `grep POSTGRES .env`
2. 测试数据库连接: `psql -h [host] -p [port] -U [user] -d [db]`
3. 检查防火墙规则
4. 查看数据库日志: `docker compose logs db`

---

## 📞 获取帮助

如遇到问题：
1. 运行部署检查脚本查看详细错误
2. 运行状态检查脚本查看运行状态
3. 查看服务日志定位问题
4. 参考相关文档
