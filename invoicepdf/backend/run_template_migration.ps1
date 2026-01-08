# 修复模板迁移分支问题

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  修复模板迁移分支" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 检查当前状态
Write-Host "步骤1: 检查当前迁移状态..." -ForegroundColor Yellow
python -m alembic current
Write-Host ""

# 步骤2: 检查所有 head
Write-Host "步骤2: 检查迁移 head..." -ForegroundColor Yellow
python -m alembic heads
Write-Host ""

# 步骤3: 升级到第一个 head
Write-Host "步骤3: 升级到 fix_template_type_001..." -ForegroundColor Yellow
python -m alembic upgrade fix_template_type_001
Write-Host ""

# 步骤4: 升级到第二个 head
Write-Host "步骤4: 升级到 template_version_001..." -ForegroundColor Yellow
python -m alembic upgrade template_version_001
Write-Host ""

# 步骤5: 升级合并迁移
Write-Host "步骤5: 升级合并迁移..." -ForegroundColor Yellow
python -m alembic upgrade merge_template_branches_001
Write-Host ""

# 步骤6: 验证
Write-Host "步骤6: 验证迁移..." -ForegroundColor Yellow
Write-Host "当前版本:" -ForegroundColor Gray
python -m alembic current
Write-Host ""
Write-Host "所有 head:" -ForegroundColor Gray
python -m alembic heads
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  迁移完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

