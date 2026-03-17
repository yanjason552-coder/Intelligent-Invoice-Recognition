# 快速修复指南

## 🚨 问题：Docker镜像拉取失败

### 错误信息
```
failed to resolve source metadata for docker.io/library/python:3.10
```

## ✅ 快速修复（3步）

### 方法1: 使用批处理文件（最简单）

**双击运行**：
```
fix-and-deploy.bat
```

### 方法2: 在服务器上手动执行

**连接服务器**：
```bash
ssh -p 50518 root@8.145.33.61
# 密码: 6b3fPk9n!
```

**执行修复命令**：
```bash
cd /opt/invoice-app

# 步骤1: 配置Docker镜像加速器
bash scripts/aliyun/fix-docker-mirror.sh

# 步骤2: 重新构建镜像
bash scripts/aliyun/retry-build.sh

# 步骤3: 重新部署
docker compose -f docker-compose.yml -f docker-compose.production.external-db.yml --profile no-db up -d redis prestart backend frontend adminer

# 步骤4: 检查状态
docker compose ps
```

### 方法3: 一键修复命令

**在Git Bash中执行**：
```bash
# 上传修复脚本
scp -P 50518 scripts/aliyun/fix-docker-mirror.sh scripts/aliyun/retry-build.sh root@8.145.33.61:/tmp/

# 执行修复
ssh -p 50518 root@8.145.33.61 'chmod +x /tmp/fix-docker-mirror.sh /tmp/retry-build.sh && bash /tmp/fix-docker-mirror.sh && cd /opt/invoice-app && bash /tmp/retry-build.sh && docker compose -f docker-compose.yml -f docker-compose.production.external-db.yml --profile no-db up -d'
```

## 🔍 验证修复

### 1. 检查Docker配置
```bash
docker info | grep -A 5 "Registry Mirrors"
```

### 2. 测试拉取镜像
```bash
docker pull python:3.10
```

### 3. 检查服务状态
```bash
docker compose ps
docker compose logs -f backend
```

## 📋 修复后访问

- **前端**: http://8.145.33.61:5173
- **API文档**: http://8.145.33.61:8000/docs
- **健康检查**: http://8.145.33.61:8000/api/v1/utils/health-check/

## ⚠️ 如果仍然失败

1. **检查网络连接**
   ```bash
   ping docker.mirrors.ustc.edu.cn
   ```

2. **尝试其他镜像源**
   - 编辑 `/etc/docker/daemon.json`
   - 更换镜像源地址

3. **查看详细文档**
   - `FIX_DEPLOYMENT.md` - 完整修复指南

## 🆘 需要帮助？

如果以上方法都无法解决，请：
1. 查看Docker日志：`journalctl -u docker`
2. 检查网络连接
3. 联系技术支持

