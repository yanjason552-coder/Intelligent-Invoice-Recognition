# 阿里云部署脚本说明

本目录包含用于在阿里云ECS上部署智能发票识别系统的所有脚本。

## 脚本列表

### 1. init-server.sh
**用途**: 初始化ECS服务器环境

**功能**:
- 更新系统包
- 安装Docker和Docker Compose
- 创建必要的目录结构
- 创建Docker网络
- 配置防火墙规则

**使用方法**:
```bash
chmod +x scripts/aliyun/init-server.sh
sudo bash scripts/aliyun/init-server.sh
```

### 2. build-and-push.sh
**用途**: 构建Docker镜像并推送到阿里云容器镜像服务

**功能**:
- 构建后端镜像
- 构建前端镜像
- 推送到阿里云镜像仓库

**使用方法**:
```bash
# 设置环境变量
export REGISTRY=your-registry.cn-hangzhou.aliyuncs.com
export NAMESPACE=invoice
export ALIYUN_REGISTRY_USERNAME=your-username
export ALIYUN_REGISTRY_PASSWORD=your-password

# 运行脚本
chmod +x scripts/aliyun/build-and-push.sh
./scripts/aliyun/build-and-push.sh v1.0.0
```

**参数**:
- 第一个参数（可选）: 镜像标签，默认为 `latest`

### 3. deploy-production.sh
**用途**: 在生产环境部署应用

**功能**:
- 检查环境变量配置
- 部署Traefik（如果尚未部署）
- 拉取最新镜像
- 停止旧容器
- 启动新容器
- 检查服务状态

**使用方法**:
```bash
chmod +x scripts/aliyun/deploy-production.sh
sudo bash scripts/aliyun/deploy-production.sh
```

**前置条件**:
- 服务器已初始化
- 环境变量文件 `/opt/invoice-app/.env` 已配置
- Docker镜像已构建并推送到镜像仓库

### 4. backup-db.sh
**用途**: 备份PostgreSQL数据库

**功能**:
- 导出数据库
- 压缩备份文件
- 可选上传到OSS
- 清理旧备份

**使用方法**:
```bash
chmod +x scripts/aliyun/backup-db.sh
./scripts/aliyun/backup-db.sh
```

**环境变量**:
- `BACKUP_DIR`: 备份目录（默认: `/opt/invoice-app/backups`）
- `RETENTION_DAYS`: 保留天数（默认: 7）
- `DB_CONTAINER`: 数据库容器名（默认: `invoice-app-db-1`）
- `OSS_ENABLED`: 是否启用OSS上传（默认: `false`）

**定时任务配置**:
```bash
# 编辑crontab
crontab -e

# 添加每天凌晨2点备份
0 2 * * * /opt/invoice-app/scripts/aliyun/backup-db.sh >> /var/log/invoice-backup.log 2>&1
```

## 环境变量模板

### .env.production.template
生产环境变量配置模板文件。

**使用方法**:
```bash
# 复制模板文件
cp scripts/aliyun/.env.production.template /opt/invoice-app/.env

# 编辑配置文件
vim /opt/invoice-app/.env
```

**重要配置项**:
- `DOMAIN`: 域名
- `SECRET_KEY`: 安全密钥（必须生成）
- `POSTGRES_PASSWORD`: 数据库密码（必须生成）
- `DOCKER_IMAGE_BACKEND`: 后端镜像地址
- `DOCKER_IMAGE_FRONTEND`: 前端镜像地址

## 部署流程

### 第一次部署

1. **初始化服务器**
   ```bash
   sudo bash scripts/aliyun/init-server.sh
   ```

2. **构建和推送镜像**
   ```bash
   # 在本地开发机器上
   ./scripts/aliyun/build-and-push.sh v1.0.0
   ```

3. **配置环境变量**
   ```bash
   # 在服务器上
   cp scripts/aliyun/.env.production.template /opt/invoice-app/.env
   vim /opt/invoice-app/.env
   ```

4. **部署应用**
   ```bash
   # 在服务器上
   sudo bash scripts/aliyun/deploy-production.sh
   ```

### 更新部署

1. **构建新镜像**
   ```bash
   ./scripts/aliyun/build-and-push.sh v1.1.0
   ```

2. **更新环境变量**
   ```bash
   # 在.env文件中更新TAG
   TAG=v1.1.0
   ```

3. **重新部署**
   ```bash
   sudo bash scripts/aliyun/deploy-production.sh
   ```

## 注意事项

1. **权限**: 所有脚本都需要执行权限，使用 `chmod +x` 添加
2. **用户**: 部署脚本需要root权限，使用 `sudo` 运行
3. **环境变量**: 确保所有必要的环境变量都已正确配置
4. **网络**: 确保服务器可以访问阿里云容器镜像服务
5. **域名**: 确保域名已正确解析到服务器IP

## 故障排查

### 脚本执行失败

1. 检查脚本权限: `ls -l scripts/aliyun/*.sh`
2. 检查执行用户: `whoami`
3. 查看错误信息: 脚本会输出详细的错误信息

### 镜像构建失败

1. 检查Docker是否运行: `docker ps`
2. 检查网络连接: `ping your-registry.cn-hangzhou.aliyuncs.com`
3. 检查登录状态: `docker login`

### 部署失败

1. 检查环境变量: `cat /opt/invoice-app/.env`
2. 检查镜像是否存在: `docker images | grep invoice`
3. 查看容器日志: `docker compose logs`

## 相关文档

- [阿里云部署指南](../docs/aliyun-deployment.md)
- [Docker Compose配置说明](../../docker-compose.production.yml)

