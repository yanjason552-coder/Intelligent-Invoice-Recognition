# 快速部署脚本 - PowerShell版本
# 使用提供的服务器信息进行部署

$SERVER_IP = "8.145.33.61"
$SSH_PORT = "50518"
$SSH_USER = "root"
$SSH_PASSWORD = "6b3fPk9n!"

$DB_HOST = "8.145.33.61"
$DB_PORT = "50511"
$DB_USER = "postgres"
$DB_PASSWORD = "postgres123"
$DB_NAME = "invoice_db"

$GIT_REPO = "https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "快速部署 - 智能发票识别系统" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "服务器: $SERVER_IP`:$SSH_PORT"
Write-Host "数据库: $DB_HOST`:$DB_PORT"
Write-Host "Git仓库: $GIT_REPO"
Write-Host ""

# 检查plink或ssh是否可用
$usePlink = $false
if (Get-Command plink -ErrorAction SilentlyContinue) {
    $usePlink = $true
    Write-Host "使用plink进行SSH连接" -ForegroundColor Yellow
} elseif (Get-Command ssh -ErrorAction SilentlyContinue) {
    Write-Host "使用ssh进行SSH连接" -ForegroundColor Yellow
} else {
    Write-Host "错误: 未找到SSH客户端（plink或ssh）" -ForegroundColor Red
    Write-Host "请安装:"
    Write-Host "  1. PuTTY (包含plink)"
    Write-Host "  2. OpenSSH (Windows 10+)"
    exit 1
}

# 生成SSH命令
function Invoke-RemoteCommand {
    param([string]$Command)
    
    if ($usePlink) {
        $env:SSH_PASSWORD = $SSH_PASSWORD
        echo y | plink -ssh -P $SSH_PORT -l $SSH_USER -pw $SSH_PASSWORD $SERVER_IP $Command
    } else {
        # 使用ssh（需要配置SSH密钥或手动输入密码）
        ssh -p $SSH_PORT $SSH_USER@$SERVER_IP $Command
    }
}

Write-Host "[1/6] 测试服务器连接..." -ForegroundColor Yellow
try {
    $result = Invoke-RemoteCommand "echo '连接成功'"
    if ($result -match "连接成功") {
        Write-Host "✓ 服务器连接成功" -ForegroundColor Green
    } else {
        Write-Host "✗ 服务器连接失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ 服务器连接失败: $_" -ForegroundColor Red
    Write-Host "提示: 如果使用ssh，可能需要手动输入密码" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "部署步骤说明" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "由于Windows环境限制，建议使用以下方式之一进行部署:" -ForegroundColor Yellow
Write-Host ""
Write-Host "方式1: 使用Git Bash执行bash脚本" -ForegroundColor Cyan
Write-Host "  1. 打开Git Bash"
Write-Host "  2. 执行: bash scripts/aliyun/quick-deploy.sh"
Write-Host ""
Write-Host "方式2: 手动执行步骤（推荐）" -ForegroundColor Cyan
Write-Host "  1. 使用SSH客户端连接服务器:"
Write-Host "     ssh -p $SSH_PORT $SSH_USER@$SERVER_IP"
Write-Host "     密码: $SSH_PASSWORD"
Write-Host ""
Write-Host "  2. 在服务器上执行以下命令:"
Write-Host "     cd /opt"
Write-Host "     git clone $GIT_REPO invoice-app"
Write-Host "     cd invoice-app"
Write-Host "     bash scripts/aliyun/init-server.sh"
Write-Host ""
Write-Host "  3. 配置环境变量:"
Write-Host "     cp scripts/aliyun/.env.production.template .env"
Write-Host "     vim .env"
Write-Host "     设置:"
Write-Host "       POSTGRES_SERVER=$DB_HOST"
Write-Host "       POSTGRES_PORT=$DB_PORT"
Write-Host "       POSTGRES_USER=$DB_USER"
Write-Host "       POSTGRES_PASSWORD=$DB_PASSWORD"
Write-Host "       POSTGRES_DB=$DB_NAME"
Write-Host ""
Write-Host "  4. 构建和部署:"
Write-Host "     cd backend && docker build -t invoice-app-backend:latest ."
Write-Host "     cd ../frontend && docker build -t invoice-app-frontend:latest ."
Write-Host "     cd .."
Write-Host "     docker compose -f docker-compose.yml -f docker-compose.production.external-db.yml --profile no-db up -d"
Write-Host ""
Write-Host "方式3: 使用WSL执行bash脚本" -ForegroundColor Cyan
Write-Host "  1. 在WSL中执行: bash scripts/aliyun/quick-deploy.sh"
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green

# 生成快速部署命令文件
$deployCommands = @"
#!/bin/bash
# 快速部署命令 - 在服务器上执行

cd /opt
git clone $GIT_REPO invoice-app
cd invoice-app

# 初始化服务器
bash scripts/aliyun/init-server.sh

# 配置环境变量
cat > .env << 'ENVEOF'
PROJECT_NAME=智能发票识别系统
ENVIRONMENT=production
DOMAIN=8.145.33.61
STACK_NAME=invoice-app-production
FRONTEND_HOST=dashboard.8.145.33.61

DOCKER_IMAGE_BACKEND=invoice-app-backend
DOCKER_IMAGE_FRONTEND=invoice-app-frontend
TAG=latest

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "changethis_$(openssl rand -hex 16)")
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123456

POSTGRES_SERVER=$DB_HOST
POSTGRES_PORT=$DB_PORT
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=$DB_NAME

REDIS_PASSWORD=
BACKEND_CORS_ORIGINS=http://8.145.33.61:5173,http://localhost:5173,http://8.145.33.61:8000

TRAEFIK_USERNAME=admin
TRAEFIK_PASSWORD=admin123456
TRAEFIK_EMAIL=admin@example.com
ENVEOF

# 构建镜像
cd backend && docker build -t invoice-app-backend:latest .
cd ../frontend && docker build --build-arg VITE_API_URL=http://8.145.33.61:8000 -t invoice-app-frontend:latest .
cd ..

# 部署服务（使用外部数据库）
docker compose -f docker-compose.yml -f docker-compose.production.external-db.yml --profile no-db up -d redis prestart backend frontend adminer

echo "部署完成！"
echo "访问地址:"
echo "  前端: http://8.145.33.61:5173"
echo "  API: http://8.145.33.61:8000/docs"
"@

$deployCommands | Out-File -FilePath "scripts/aliyun/server-deploy-commands.sh" -Encoding UTF8

Write-Host ""
Write-Host "已生成服务器部署命令文件: scripts/aliyun/server-deploy-commands.sh" -ForegroundColor Green
Write-Host "可以将此文件上传到服务器执行" -ForegroundColor Yellow
Write-Host ""

