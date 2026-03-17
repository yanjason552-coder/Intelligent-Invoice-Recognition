# 部署准备脚本 (Windows PowerShell版本)
# 用于在本地验证部署配置和准备部署文件

Write-Host "==========================================" -ForegroundColor Green
Write-Host "部署准备检查" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 检查脚本文件
Write-Host "`n检查脚本文件..." -ForegroundColor Yellow
$scripts = @(
    "scripts\aliyun\init-server.sh",
    "scripts\aliyun\build-and-push.sh",
    "scripts\aliyun\deploy-production.sh",
    "scripts\aliyun\backup-db.sh",
    "scripts\aliyun\.env.production.template"
)

$allExists = $true
foreach ($script in $scripts) {
    if (Test-Path $script) {
        Write-Host "✓ $script" -ForegroundColor Green
    } else {
        Write-Host "✗ $script (缺失)" -ForegroundColor Red
        $allExists = $false
    }
}

if (-not $allExists) {
    Write-Host "`n错误: 部分脚本文件缺失！" -ForegroundColor Red
    exit 1
}

# 检查Docker Compose文件
Write-Host "`n检查Docker Compose文件..." -ForegroundColor Yellow
$composeFiles = @(
    "docker-compose.yml",
    "docker-compose.production.yml",
    "docker-compose.traefik.yml"
)

foreach ($file in $composeFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $file" -ForegroundColor Green
    } else {
        Write-Host "✗ $file (缺失)" -ForegroundColor Red
        $allExists = $false
    }
}

# 检查Docker
Write-Host "`n检查Docker环境..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker已安装" -ForegroundColor Green
        Write-Host "  $dockerVersion" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠ Docker未安装（构建镜像时需要）" -ForegroundColor Yellow
}

# 显示部署步骤
Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "部署步骤说明" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

Write-Host "`n步骤1: 初始化服务器 (在ECS上执行)" -ForegroundColor Cyan
Write-Host "  ssh root@your-server-ip"
Write-Host "  cd /opt/invoice-app"
Write-Host "  bash scripts/aliyun/init-server.sh"

Write-Host "`n步骤2: 构建镜像 (在本地执行)" -ForegroundColor Cyan
Write-Host "  `$env:REGISTRY='your-registry.cn-hangzhou.aliyuncs.com'"
Write-Host "  `$env:NAMESPACE='invoice'"
Write-Host "  `$env:ALIYUN_REGISTRY_USERNAME='your-username'"
Write-Host "  `$env:ALIYUN_REGISTRY_PASSWORD='your-password'"
Write-Host "  bash scripts/aliyun/build-and-push.sh v1.0.0"

Write-Host "`n步骤3: 配置环境 (在ECS上执行)" -ForegroundColor Cyan
Write-Host "  ssh root@your-server-ip"
Write-Host "  cd /opt/invoice-app"
Write-Host "  cp scripts/aliyun/.env.production.template .env"
Write-Host "  vim .env"

Write-Host "`n步骤4: 部署应用 (在ECS上执行)" -ForegroundColor Cyan
Write-Host "  ssh root@your-server-ip"
Write-Host "  cd /opt/invoice-app"
Write-Host "  bash scripts/aliyun/deploy-production.sh"

Write-Host "`n步骤5: 配置备份 (在ECS上执行)" -ForegroundColor Cyan
Write-Host "  ssh root@your-server-ip"
Write-Host "  crontab -e"
Write-Host "  # 添加: 0 2 * * * /opt/invoice-app/scripts/aliyun/backup-db.sh"

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "准备完成！" -ForegroundColor Green
Write-Host "详细说明请参考: scripts/aliyun/deployment-checklist.md" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Green

