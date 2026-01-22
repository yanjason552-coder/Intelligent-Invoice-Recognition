# 执行数据库迁移脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  执行数据库迁移" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否有多个head
Write-Host "步骤1: 检查迁移状态..." -ForegroundColor Yellow
$headsOutput = @()
try {
    python -m alembic heads | ForEach-Object { $headsOutput += $_ }
} catch {
    $headsOutput += $_.Exception.Message
}
$headsOutput = $headsOutput -join "`n"

if ($headsOutput -match "Multiple head") {
    Write-Host "检测到多个迁移head，需要先合并分支" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "解决方案：" -ForegroundColor Green
    Write-Host "1. 我已经创建了合并迁移文件: merge_invoice_and_material.py" -ForegroundColor Gray
    Write-Host "2. 现在需要先升级到两个head，然后升级合并迁移" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "步骤2: 升级到 create_invoice_tables_001..." -ForegroundColor Yellow
    python -m alembic upgrade create_invoice_tables_001
    
    Write-Host ""
    Write-Host "步骤3: 升级到 remove_material_fk..." -ForegroundColor Yellow
    python -m alembic upgrade remove_material_fk
    
    Write-Host ""
    Write-Host "步骤4: 升级合并迁移..." -ForegroundColor Yellow
    python -m alembic upgrade merge_001
    
} else {
    Write-Host "[OK] 迁移链正常，直接升级到head" -ForegroundColor Green
    Write-Host ""
    Write-Host "步骤2: 执行迁移..." -ForegroundColor Yellow
    python -m alembic upgrade head
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  迁移完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "验证迁移：" -ForegroundColor Yellow
Write-Host "  python -m alembic current" -ForegroundColor Gray
Write-Host ""
