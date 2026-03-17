# 执行修复的PowerShell脚本
# 连接到服务器并执行修复脚本

$SERVER_IP = "8.145.33.61"
$SSH_PORT = "50518"
$SSH_USER = "root"
$SSH_PASSWORD = "6b3fPk9n!"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "执行Docker镜像问题修复" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# 查找Git Bash
$gitBash = $null
$possiblePaths = @(
    "C:\Program Files\Git\bin\bash.exe",
    "C:\Program Files (x86)\Git\bin\bash.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $gitBash = $path
        break
    }
}

if (-not $gitBash) {
    Write-Host "错误: 未找到Git Bash" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动执行以下步骤:" -ForegroundColor Yellow
    Write-Host "1. 使用SSH客户端连接服务器: ssh -p $SSH_PORT $SSH_USER@$SERVER_IP" -ForegroundColor Cyan
    Write-Host "2. 在服务器上执行修复脚本（见下方）" -ForegroundColor Cyan
    exit 1
}

Write-Host "找到Git Bash: $gitBash" -ForegroundColor Green
Write-Host ""

# 创建临时脚本文件，包含完整的修复命令
$fixScript = @"
#!/bin/bash
set -e

echo "=========================================="
echo "开始修复Docker镜像问题"
echo "=========================================="

# 配置Docker镜像加速器
echo "[1/5] 配置Docker镜像加速器..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'DOCKER_DAEMON'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://dockerhub.azk8s.cn"
  ],
  "max-concurrent-downloads": 10
}
DOCKER_DAEMON

systemctl daemon-reload
systemctl restart docker
sleep 5
echo "✓ Docker镜像加速器配置完成"

# 测试拉取镜像
echo "[2/5] 测试拉取基础镜像..."
docker pull python:3.10 || docker pull python:3.10-slim
echo "✓ 基础镜像拉取成功"

# 确保项目目录存在
echo "[3/5] 检查项目目录..."
if [ ! -d "/opt/invoice-app" ]; then
    cd /opt
    git clone https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git invoice-app
fi
cd /opt/invoice-app
echo "✓ 项目目录准备完成"

# 执行完整修复脚本（如果存在）
if [ -f scripts/aliyun/fix-and-retry-deploy.sh ]; then
    echo "[4/5] 执行完整修复脚本..."
    chmod +x scripts/aliyun/fix-and-retry-deploy.sh
    bash scripts/aliyun/fix-and-retry-deploy.sh
else
    echo "[4/5] 执行修复和构建..."
    # 配置环境变量
    if [ ! -f .env ]; then
        SECRET_KEY=\$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
        cat > .env << EOF
PROJECT_NAME=智能发票识别系统
ENVIRONMENT=production
DOMAIN=8.145.33.61
STACK_NAME=invoice-app-production
FRONTEND_HOST=dashboard.8.145.33.61
DOCKER_IMAGE_BACKEND=invoice-app-backend
DOCKER_IMAGE_FRONTEND=invoice-app-frontend
TAG=latest
SECRET_KEY=\$SECRET_KEY
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123456
POSTGRES_SERVER=8.145.33.61
POSTGRES_PORT=50511
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=invoice_db
REDIS_PASSWORD=
BACKEND_CORS_ORIGINS=http://8.145.33.61:5173,http://localhost:5173,http://8.145.33.61:8000
TRAEFIK_USERNAME=admin
TRAEFIK_PASSWORD=admin123456
TRAEFIK_EMAIL=admin@example.com
EOF
    fi
    
    # 构建镜像
    echo "构建后端镜像..."
    cd backend && docker build -t invoice-app-backend:latest . && cd ..
    echo "构建前端镜像..."
    cd frontend && docker build --build-arg VITE_API_URL=http://8.145.33.61:8000 -t invoice-app-frontend:latest . && cd ..
    
    # 部署服务
    echo "[5/5] 部署服务..."
    docker network create traefik-public 2>/dev/null || true
    if [ -f docker-compose.production.external-db.yml ]; then
        docker compose -f docker-compose.yml -f docker-compose.production.external-db.yml --profile no-db up -d redis prestart backend frontend adminer
    else
        docker compose -f docker-compose.yml up -d redis prestart backend frontend adminer
    fi
    
    sleep 10
    docker compose ps
fi

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
"@

# 将脚本保存到临时文件
$tempScript = [System.IO.Path]::GetTempFileName() + ".sh"
$fixScript | Out-File -FilePath $tempScript -Encoding UTF8 -NoNewline

Write-Host "准备连接到服务器执行修复..." -ForegroundColor Yellow
Write-Host "提示: 需要输入服务器密码: $SSH_PASSWORD" -ForegroundColor Cyan
Write-Host ""

# 上传修复脚本到服务器并执行
$uploadAndExecute = @"
# 上传修复脚本
scp -P $SSH_PORT `"$tempScript`" ${SSH_USER}@${SERVER_IP}:/tmp/fix-docker.sh

# 执行修复脚本
ssh -p $SSH_PORT ${SSH_USER}@${SERVER_IP} 'chmod +x /tmp/fix-docker.sh && bash /tmp/fix-docker.sh'
"@

Write-Host "执行修复命令..." -ForegroundColor Yellow
& $gitBash -c $uploadAndExecute

# 清理临时文件
Remove-Item $tempScript -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "修复执行完成！" -ForegroundColor Green

