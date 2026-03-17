# 域名配置完整指南

## 📋 使用域名访问的配置步骤

### 前置条件

1. ✅ **已拥有域名**（例如：`example.com`）
2. ✅ **域名已备案**（如果在中国大陆使用）
3. ✅ **ECS服务器已准备**（IP: `8.145.33.61`）
4. ✅ **Docker和Docker Compose已安装**
5. ✅ **80和443端口已开放**（安全组和防火墙）

---

## 🚀 配置步骤

### 步骤1: 配置DNS解析

在您的域名DNS管理面板（如阿里云DNS、Cloudflare等）添加以下A记录：

```
类型    主机记录    记录值           TTL
A       api        8.145.33.61     600
A       dashboard  8.145.33.61     600
A       adminer    8.145.33.61     600
A       traefik    8.145.33.61     600
```

**示例**（假设域名为 `example.com`）：
- `api.example.com` → `8.145.33.61`
- `dashboard.example.com` → `8.145.33.61`
- `adminer.example.com` → `8.145.33.61`
- `traefik.example.com` → `8.145.33.61`

**验证DNS解析**：
```bash
# 在服务器或本地执行
nslookup api.example.com
nslookup dashboard.example.com
```

---

### 步骤2: 修改环境变量配置

编辑 `/opt/invoice-app/.env` 文件：

```bash
vim /opt/invoice-app/.env
```

**修改以下配置项**：

```bash
# 将DOMAIN改为您的域名（不带www）
DOMAIN=example.com

# 更新FRONTEND_HOST
FRONTEND_HOST=dashboard.example.com

# 更新CORS配置（添加域名）
BACKEND_CORS_ORIGINS=["https://dashboard.example.com","http://localhost:5173"]

# 确保Traefik邮箱配置正确（用于Let's Encrypt证书）
TRAEFIK_EMAIL=your-email@example.com  # 使用真实邮箱地址
```

**完整示例**：
```bash
PROJECT_NAME=智能发票识别系统
ENVIRONMENT=production
DOMAIN=example.com
STACK_NAME=invoice-app-production
FRONTEND_HOST=dashboard.example.com

# Docker镜像配置
DOCKER_IMAGE_BACKEND=invoice-app-backend
DOCKER_IMAGE_FRONTEND=invoice-app-frontend
TAG=latest

# 安全配置
SECRET_KEY=4_vwykW2OBvb-OQl30-xv9G0mRhW1vdGJ9fl2MDoCkg
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123456

# 数据库配置
POSTGRES_SERVER=8.145.33.61
POSTGRES_PORT=50511
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=invoice_db

# Redis配置
REDIS_PASSWORD=

# CORS配置（添加域名）
BACKEND_CORS_ORIGINS=["https://dashboard.example.com","http://localhost:5173"]

# Traefik配置（重要！）
TRAEFIK_USERNAME=admin
TRAEFIK_PASSWORD=admin123456
TRAEFIK_EMAIL=your-email@example.com  # 必须使用真实邮箱
```

---

### 步骤3: 部署Traefik

Traefik将自动申请Let's Encrypt SSL证书。

```bash
cd /opt/invoice-app

# 确保docker-compose.traefik.yml存在
ls -la docker-compose.traefik.yml

# 创建Traefik目录
mkdir -p /opt/traefik-public

# 复制Traefik配置文件
cp docker-compose.traefik.yml /opt/traefik-public/

# 进入Traefik目录
cd /opt/traefik-public

# 设置Traefik环境变量
export DOMAIN=example.com
export USERNAME=admin
export PASSWORD=admin123456
export HASHED_PASSWORD=$(openssl passwd -apr1 "$PASSWORD")
export EMAIL=your-email@example.com

# 部署Traefik
docker compose -f docker-compose.traefik.yml up -d

# 查看Traefik日志
docker compose -f docker-compose.traefik.yml logs -f
```

**等待SSL证书申请**（通常需要1-2分钟）：
```bash
# 查看证书申请状态
docker logs traefik-public-traefik-1 | grep -i acme
```

---

### 步骤4: 部署应用服务

```bash
cd /opt/invoice-app

# 运行部署脚本
bash scripts/aliyun/deploy-production.sh
```

或者手动部署：

```bash
cd /opt/invoice-app

# 加载环境变量
set -a
source .env
set +a

# 部署服务
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d

# 查看服务状态
docker compose -f docker-compose.yml -f docker-compose.production.yml ps
```

---

### 步骤5: 验证访问

等待服务启动后（约1-2分钟），访问以下地址：

- ✅ **前端**: https://dashboard.example.com
- ✅ **API文档**: https://api.example.com/docs
- ✅ **健康检查**: https://api.example.com/api/v1/utils/health-check/
- ✅ **数据库管理**: https://adminer.example.com
- ✅ **Traefik面板**: https://traefik.example.com

**注意**：
- HTTP会自动重定向到HTTPS
- SSL证书由Let's Encrypt自动申请和管理
- 首次访问可能需要等待证书申请完成

---

## 🔍 故障排查

### 问题1: DNS解析未生效

**检查方法**：
```bash
# 在服务器上检查
nslookup api.example.com
nslookup dashboard.example.com

# 或在本地检查
ping api.example.com
```

**解决方法**：
- 确认DNS记录已添加
- 等待DNS传播（通常几分钟到几小时）
- 检查DNS服务商配置是否正确

---

### 问题2: SSL证书申请失败

**检查Traefik日志**：
```bash
docker logs traefik-public-traefik-1 | grep -i error
docker logs traefik-public-traefik-1 | grep -i acme
```

**常见原因**：
1. **DNS解析未生效** - 确保域名已正确解析到服务器IP
2. **80端口未开放** - Let's Encrypt需要80端口进行验证
3. **防火墙阻止** - 检查安全组和防火墙规则
4. **邮箱配置错误** - 确保TRAEFIK_EMAIL是有效邮箱

**解决方法**：
```bash
# 检查端口
netstat -tlnp | grep -E "80|443"

# 检查防火墙
ufw status
# 如果防火墙启用，确保已开放端口
ufw allow 80/tcp
ufw allow 443/tcp

# 检查安全组（阿里云控制台）
# 确保80和443端口已开放
```

---

### 问题3: 服务无法访问

**检查服务状态**：
```bash
# 检查所有容器
docker ps -a

# 检查服务日志
cd /opt/invoice-app
docker compose -f docker-compose.yml -f docker-compose.production.yml logs

# 检查特定服务
docker compose logs backend
docker compose logs frontend
```

**检查Traefik路由**：
```bash
# 访问Traefik API（需要认证）
curl -u admin:admin123456 http://traefik.example.com/api/http/routers
```

---

### 问题4: CORS错误

**症状**：前端无法访问API，浏览器控制台显示CORS错误

**解决方法**：
1. 检查`.env`文件中的`BACKEND_CORS_ORIGINS`配置
2. 确保包含前端域名（使用HTTPS）
3. 重启后端服务：

```bash
cd /opt/invoice-app
docker compose restart backend
```

---

## 📝 快速配置脚本

创建以下脚本快速配置域名：

```bash
cat > /opt/invoice-app/scripts/aliyun/setup-domain.sh << 'SETUP_EOF'
#!/bin/bash
# 域名配置脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR=${APP_DIR:-/opt/invoice-app}

echo -e "${BLUE}域名配置向导${NC}"
echo ""

# 读取域名
read -p "请输入您的域名（例如：example.com）: " DOMAIN
read -p "请输入您的邮箱（用于SSL证书）: " EMAIL

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo -e "${RED}错误: 域名和邮箱不能为空${NC}"
    exit 1
fi

# 更新.env文件
if [ -f "$APP_DIR/.env" ]; then
    echo -e "${YELLOW}更新.env文件...${NC}"
    
    # 备份原文件
    cp "$APP_DIR/.env" "$APP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
    
    # 更新DOMAIN
    sed -i "s|^DOMAIN=.*|DOMAIN=$DOMAIN|" "$APP_DIR/.env"
    
    # 更新FRONTEND_HOST
    sed -i "s|^FRONTEND_HOST=.*|FRONTEND_HOST=dashboard.$DOMAIN|" "$APP_DIR/.env"
    
    # 更新TRAEFIK_EMAIL
    sed -i "s|^TRAEFIK_EMAIL=.*|TRAEFIK_EMAIL=$EMAIL|" "$APP_DIR/.env"
    
    # 更新CORS（添加域名）
    if ! grep -q "https://dashboard.$DOMAIN" "$APP_DIR/.env"; then
        sed -i "s|BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=[\"https://dashboard.$DOMAIN\",\"http://localhost:5173\"]|" "$APP_DIR/.env"
    fi
    
    echo -e "${GREEN}✓ .env文件已更新${NC}"
else
    echo -e "${RED}错误: .env文件不存在${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}配置完成！${NC}"
echo ""
echo "下一步："
echo "1. 配置DNS解析："
echo "   - api.$DOMAIN → 8.145.33.61"
echo "   - dashboard.$DOMAIN → 8.145.33.61"
echo "   - adminer.$DOMAIN → 8.145.33.61"
echo "   - traefik.$DOMAIN → 8.145.33.61"
echo ""
echo "2. 验证DNS解析："
echo "   nslookup api.$DOMAIN"
echo ""
echo "3. 部署Traefik："
echo "   cd /opt/traefik-public"
echo "   export DOMAIN=$DOMAIN"
echo "   export EMAIL=$EMAIL"
echo "   export USERNAME=admin"
echo "   export PASSWORD=\$(openssl passwd -apr1 'admin123456')"
echo "   docker compose -f docker-compose.traefik.yml up -d"
echo ""
echo "4. 部署应用："
echo "   bash $APP_DIR/scripts/aliyun/deploy-production.sh"
echo ""
SETUP_EOF

chmod +x /opt/invoice-app/scripts/aliyun/setup-domain.sh
```

---

## ✅ 配置检查清单

使用域名前，确认以下项：

- [ ] DNS解析已配置（api、dashboard、adminer、traefik）
- [ ] DNS解析已生效（nslookup验证）
- [ ] `.env`文件中的`DOMAIN`已更新为域名
- [ ] `.env`文件中的`TRAEFIK_EMAIL`已设置为真实邮箱
- [ ] `.env`文件中的`BACKEND_CORS_ORIGINS`包含前端域名
- [ ] 80和443端口已开放（安全组和防火墙）
- [ ] Traefik已部署并运行
- [ ] SSL证书已申请成功（查看Traefik日志）
- [ ] 应用服务已部署并运行

---

## 📞 获取帮助

如遇到问题：
1. 检查DNS解析：`nslookup api.your-domain.com`
2. 查看Traefik日志：`docker logs traefik-public-traefik-1`
3. 查看应用日志：`docker compose logs`
4. 运行状态检查：`bash scripts/aliyun/check-deployment-status.sh`
