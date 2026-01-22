# 修复迁移分支问题的脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  修复 Alembic 迁移分支问题" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查当前迁移状态
Write-Host "步骤1: 检查当前迁移状态..." -ForegroundColor Yellow
try {
    $currentOutput = @()
    python -m alembic current | ForEach-Object { $currentOutput += $_ }
    $current = $currentOutput -join "`n"
    Write-Host "当前版本:" -ForegroundColor Gray
    Write-Host $current -ForegroundColor Gray
} catch {
    Write-Host "无法获取当前版本（可能是首次迁移）" -ForegroundColor Gray
}

Write-Host ""

# 2. 检查所有head
Write-Host "步骤2: 检查迁移head..." -ForegroundColor Yellow
try {
    $headsOutput = @()
    python -m alembic heads | ForEach-Object { $headsOutput += $_ }
    $heads = $headsOutput -join "`n"
    Write-Host $heads -ForegroundColor Gray
    
    if ($heads -match "Multiple head") {
        Write-Host "检测到多个head，需要修复" -ForegroundColor Red
        Write-Host ""
        Write-Host "解决方案：" -ForegroundColor Yellow
        Write-Host "1. 我已经修改了 remove_material_foreign_key_constraint.py" -ForegroundColor Green
        Write-Host "2. 现在尝试执行迁移..." -ForegroundColor Green
        Write-Host ""
        
        # 尝试升级
        Write-Host "步骤3: 执行迁移..." -ForegroundColor Yellow
        python -m alembic upgrade head
    } else {
        Write-Host "[OK] 迁移链正常" -ForegroundColor Green
        Write-Host ""
        Write-Host "步骤3: 执行迁移..." -ForegroundColor Yellow
        python -m alembic upgrade head
    }
} catch {
    Write-Host "[ERROR] 错误: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "如果仍然失败，请尝试：" -ForegroundColor Yellow
    Write-Host "1. 检查数据库连接" -ForegroundColor Gray
    Write-Host "2. 查看详细错误信息" -ForegroundColor Gray
    Write-Host "3. 参考 FIX_MIGRATION_SIMPLE.md" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
