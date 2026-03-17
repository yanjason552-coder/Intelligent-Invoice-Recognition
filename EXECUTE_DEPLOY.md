# 执行部署 - 方式一

## 快速执行

### 使用Git Bash执行（推荐）

1. **打开Git Bash**

2. **执行以下命令**：

```bash
# 进入项目目录
cd /c/FITS/Project/Invoice/智能发票识别_Final_V2/invoicepdf

# 执行部署脚本
bash scripts/aliyun/deploy-commands.sh
```

**或者手动执行以下命令**：

```bash
# 步骤1: 上传部署脚本
scp -P 50518 scripts/aliyun/server-deploy.sh root@8.145.33.61:/tmp/server-deploy.sh
# 输入密码: 6b3fPk9n!

# 步骤2: 连接服务器并执行部署
ssh -p 50518 root@8.145.33.61 'chmod +x /tmp/server-deploy.sh && bash /tmp/server-deploy.sh'
# 输入密码: 6b3fPk9n!
```

### 直接在服务器上执行（如果无法使用SCP）

1. **使用SSH客户端连接服务器**：
   - 主机: 8.145.33.61
   - 端口: 50518
   - 用户名: root
   - 密码: 6b3fPk9n!

2. **在服务器上执行**：

```bash
# 克隆项目
cd /opt
git clone https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git invoice-app
cd invoice-app

# 执行部署脚本
chmod +x scripts/aliyun/server-deploy.sh
bash scripts/aliyun/server-deploy.sh
```

## 部署过程说明

部署脚本会自动执行以下步骤：

1. ✅ 更新系统并安装Docker和Docker Compose
2. ✅ 创建必要的目录结构
3. ✅ 克隆Git仓库
4. ✅ 配置环境变量（使用外部PostgreSQL）
5. ✅ 构建Docker镜像
6. ✅ 部署服务（Redis、Backend、Frontend、Adminer）
7. ✅ 检查服务状态

## 部署后验证

### 检查服务状态

```bash
# 连接服务器
ssh -p 50518 root@8.145.33.61

# 查看服务状态
cd /opt/invoice-app
docker compose ps

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 访问服务

- **前端**: http://8.145.33.61:5173
- **API文档**: http://8.145.33.61:8000/docs
- **API健康检查**: http://8.145.33.61:8000/api/v1/utils/health-check/

### 测试API

```bash
# 测试健康检查
curl http://8.145.33.61:8000/api/v1/utils/health-check/

# 测试API文档
curl http://8.145.33.61:8000/docs
```

## 注意事项

1. **数据库准备**：
   - 确保PostgreSQL数据库 `invoice_db` 已创建
   - 如果未创建，执行：
     ```sql
     psql -h 8.145.33.61 -p 50511 -U postgres
     CREATE DATABASE invoice_db;
     ```

2. **防火墙配置**：
   - 确保端口8000和5173已开放
   - 如果需要，执行：
     ```bash
     ufw allow 8000/tcp
     ufw allow 5173/tcp
     ```

3. **首次部署**：
   - 部署完成后需要运行数据库迁移
   - 执行：
     ```bash
     docker exec -it invoice-app-backend-1 bash
     alembic upgrade head
     ```

## 故障排查

### 如果部署失败

1. **检查网络连接**：
   ```bash
   ping 8.145.33.61
   ```

2. **检查SSH连接**：
   ```bash
   ssh -p 50518 root@8.145.33.61
   ```

3. **查看部署日志**：
   - 部署脚本会输出详细的执行日志
   - 注意查看错误信息

4. **手动检查步骤**：
   - 参考 `DEPLOY_NOW.md` 中的方式二（分步执行）

## 下一步

部署完成后：

1. ✅ 验证服务是否正常运行
2. ✅ 测试API接口
3. ✅ 配置数据库迁移
4. ✅ 设置定时备份（参考 `scripts/aliyun/backup-db.sh`）

