# Schema 不匹配处理测试脚本 (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Schema 不匹配处理测试" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 运行单元测试
Write-Host "`n1. 运行单元测试..." -ForegroundColor Yellow
pytest app/tests/services/test_schema_mismatch_handler.py -v

# 运行集成测试
Write-Host "`n2. 运行集成测试..." -ForegroundColor Yellow
pytest app/tests/services/test_schema_validation_integration.py -v

# 运行场景测试
Write-Host "`n3. 运行场景测试..." -ForegroundColor Yellow
pytest app/tests/services/test_schema_mismatch_scenarios.py -v

# 生成覆盖率报告
Write-Host "`n4. 生成覆盖率报告..." -ForegroundColor Yellow
pytest app/tests/services/test_schema_mismatch*.py `
    --cov=app.services.schema_mismatch_handler `
    --cov=app.services.schema_validation_service `
    --cov-report=html `
    --cov-report=term

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "测试完成！" -ForegroundColor Green
Write-Host "覆盖率报告: htmlcov/index.html" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

