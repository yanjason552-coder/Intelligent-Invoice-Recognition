# 启动前端服务脚本

Write-Host "=== Starting Frontend Service ===" -ForegroundColor Cyan
Write-Host ""

# 检查是否在正确的目录
if (-not (Test-Path "frontend\package.json")) {
    Write-Host "[ERROR] Please run this script from the project root directory" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# 进入前端目录
Set-Location frontend

# 检查 node_modules
if (-not (Test-Path "node_modules")) {
    Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# 启动服务
Write-Host "[INFO] Starting frontend dev server on http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    npm run dev
} catch {
    Write-Host "[ERROR] Failed to start frontend: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check if port 5173 is available" -ForegroundColor Gray
    Write-Host "2. Verify Node.js is installed: node --version" -ForegroundColor Gray
    Write-Host "3. Try reinstalling dependencies: npm install" -ForegroundColor Gray
    exit 1
}


