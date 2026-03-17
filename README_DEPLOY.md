# 快速部署指南

## 🚀 一键部署（推荐）

### Windows用户

**双击运行批处理文件**：

1. **deploy.bat** - 完整版（推荐）
   - 自动检测Git Bash
   - 详细的提示信息
   - 错误处理

2. **deploy-simple.bat** - 简化版
   - 快速启动
   - 最小化提示

**或者手动执行**：

```cmd
deploy.bat
```

### Linux/Mac用户

```bash
bash scripts/aliyun/deploy-commands.sh
```

## 📋 部署流程

部署脚本会自动执行以下步骤：

1. ✅ **上传部署脚本**到服务器 `/tmp/server-deploy.sh`
2. ✅ **连接服务器**并执行部署脚本
3. ✅ **自动完成**：
   - 安装Docker和Docker Compose
   - 克隆Git仓库
   - 配置环境变量
   - 构建Docker镜像
   - 部署所有服务

## 🔑 服务器信息

- **IP**: 8.145.33.61
- **SSH端口**: 50518
- **用户名**: root
- **密码**: 6b3fPk9n!

## 🗄️ 数据库信息

- **主机**: 8.145.33.61
- **端口**: 50511
- **用户名**: postgres
- **密码**: postgres123
- **数据库名**: invoice_db

## ✅ 部署后验证

部署完成后，访问以下地址：

- 🌐 **前端**: http://8.145.33.61:5173
- 📚 **API文档**: http://8.145.33.61:8000/docs
- 🏥 **健康检查**: http://8.145.33.61:8000/api/v1/utils/health-check/

## 🔍 查看服务状态

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

## ⚠️ 注意事项

1. **首次部署前**：
   - 确保PostgreSQL数据库 `invoice_db` 已创建
   - 如果未创建，执行：
     ```sql
     psql -h 8.145.33.61 -p 50511 -U postgres
     CREATE DATABASE invoice_db;
     ```

2. **防火墙配置**：
   - 确保端口8000和5173已开放
   - 如果需要：
     ```bash
     ufw allow 8000/tcp
     ufw allow 5173/tcp
     ```

3. **数据库迁移**：
   - 部署完成后需要运行数据库迁移
   - 执行：
     ```bash
     docker exec -it invoice-app-backend-1 bash
     alembic upgrade head
     ```

## 🆘 故障排查

### 如果批处理文件无法运行

1. **检查Git Bash是否安装**：
   - 下载：https://git-scm.com/download/win
   - 安装后重新运行批处理文件

2. **手动执行**：
   - 打开Git Bash
   - 执行：`bash scripts/aliyun/deploy-commands.sh`

### 如果部署失败

1. **检查网络连接**：
   ```bash
   ping 8.145.33.61
   ```

2. **检查SSH连接**：
   ```bash
   ssh -p 50518 root@8.145.33.61
   ```

3. **查看详细日志**：
   - 部署脚本会输出详细的执行日志
   - 注意查看错误信息

4. **参考详细文档**：
   - `DEPLOY_NOW.md` - 完整部署指南
   - `EXECUTE_DEPLOY.md` - 执行说明

## 📞 获取帮助

如遇到问题：
1. 查看部署日志
2. 检查服务状态
3. 参考故障排查章节
4. 联系技术支持

---

**祝部署顺利！** 🎉

