# 启动后端服务脚本
# 使用方法: .\start_backend.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  启动后端服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在 backend 目录
if (-not (Test-Path "app")) {
    Write-Host "错误: 请在 backend 目录下运行此脚本" -ForegroundColor Red
    exit 1
}

# 检查虚拟环境
if (-not (Test-Path ".venv")) {
    Write-Host "警告: 未找到虚拟环境，正在创建..." -ForegroundColor Yellow
    uv sync
}

# 激活虚拟环境并启动服务
Write-Host "正在启动后端服务..." -ForegroundColor Yellow
Write-Host "服务地址: http://localhost:8000" -ForegroundColor Green
Write-Host "API文档: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "健康检查: http://localhost:8000/api/v1/health" -ForegroundColor Green
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

# 使用 uvicorn 启动服务
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

