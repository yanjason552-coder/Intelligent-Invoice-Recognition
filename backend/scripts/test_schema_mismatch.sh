#!/bin/bash
# Schema 不匹配处理测试脚本

set -e

echo "=========================================="
echo "Schema 不匹配处理测试"
echo "=========================================="

# 运行单元测试
echo ""
echo "1. 运行单元测试..."
pytest app/tests/services/test_schema_mismatch_handler.py -v

# 运行集成测试
echo ""
echo "2. 运行集成测试..."
pytest app/tests/services/test_schema_validation_integration.py -v

# 运行场景测试
echo ""
echo "3. 运行场景测试..."
pytest app/tests/services/test_schema_mismatch_scenarios.py -v

# 生成覆盖率报告
echo ""
echo "4. 生成覆盖率报告..."
pytest app/tests/services/test_schema_mismatch*.py \
    --cov=app.services.schema_mismatch_handler \
    --cov=app.services.schema_validation_service \
    --cov-report=html \
    --cov-report=term

echo ""
echo "=========================================="
echo "测试完成！"
echo "覆盖率报告: htmlcov/index.html"
echo "=========================================="

