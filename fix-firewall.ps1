# 修复防火墙规则，允许5173和8000端口访问

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  配置防火墙规则" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "警告: 需要管理员权限来配置防火墙规则" -ForegroundColor Yellow
    Write-Host "请右键点击PowerShell，选择'以管理员身份运行'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "或者手动运行以下命令：" -ForegroundColor Yellow
    Write-Host "New-NetFirewallRule -DisplayName 'Vite Dev Server' -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow" -ForegroundColor White
    Write-Host "New-NetFirewallRule -DisplayName 'FastAPI Backend' -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow" -ForegroundColor White
    exit 1
}

# 检查是否已存在规则
$existingViteRule = Get-NetFirewallRule -DisplayName "Vite Dev Server" -ErrorAction SilentlyContinue
$existingBackendRule = Get-NetFirewallRule -DisplayName "FastAPI Backend" -ErrorAction SilentlyContinue

# 创建或更新Vite规则
if ($existingViteRule) {
    Write-Host "Vite防火墙规则已存在，正在更新..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName "Vite Dev Server" -ErrorAction SilentlyContinue
}

Write-Host "创建Vite防火墙规则（端口5173）..." -ForegroundColor Green
New-NetFirewallRule -DisplayName "Vite Dev Server" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow -Profile Domain,Private,Public | Out-Null
Write-Host "✓ Vite防火墙规则已创建" -ForegroundColor Green

# 创建或更新后端规则
if ($existingBackendRule) {
    Write-Host "后端防火墙规则已存在，正在更新..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName "FastAPI Backend" -ErrorAction SilentlyContinue
}

Write-Host "创建后端防火墙规则（端口8000）..." -ForegroundColor Green
New-NetFirewallRule -DisplayName "FastAPI Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Domain,Private,Public | Out-Null
Write-Host "✓ 后端防火墙规则已创建" -ForegroundColor Green

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "防火墙规则配置完成！" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "现在可以通过以下地址访问：" -ForegroundColor Yellow
Write-Host "  - http://localhost:5173" -ForegroundColor White
Write-Host "  - http://10.134.134.133:5173" -ForegroundColor White
Write-Host "  - http://10.103.170.204:5173" -ForegroundColor White
Write-Host ""

