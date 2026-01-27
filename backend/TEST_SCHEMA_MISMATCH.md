# Schema 不匹配处理测试指南

## 测试文件结构

```
backend/app/tests/services/
├── test_schema_mismatch_handler.py      # 单元测试
├── test_schema_validation_integration.py # 集成测试
└── test_schema_mismatch_scenarios.py     # 场景测试
```

## 运行测试

### 1. 运行所有 Schema 不匹配测试

```bash
cd backend
pytest app/tests/services/test_schema_mismatch*.py -v
```

### 2. 运行特定测试文件

```bash
# 单元测试
pytest app/tests/services/test_schema_mismatch_handler.py -v

# 集成测试
pytest app/tests/services/test_schema_validation_integration.py -v

# 场景测试
pytest app/tests/services/test_schema_mismatch_scenarios.py -v
```

### 3. 运行特定测试类

```bash
pytest app/tests/services/test_schema_mismatch_handler.py::TestMismatchAnalysis -v
```

### 4. 运行特定测试用例

```bash
pytest app/tests/services/test_schema_mismatch_handler.py::TestMismatchAnalysis::test_analyze_missing_required_field -v
```

### 5. 显示覆盖率

```bash
pytest app/tests/services/test_schema_mismatch*.py --cov=app.services.schema_mismatch_handler --cov-report=html
```

## 测试用例说明

### 单元测试 (`test_schema_mismatch_handler.py`)

#### 1. TestMismatchAnalysis - 不匹配分析测试
- `test_analyze_missing_required_field`: 测试缺失必填字段的分析
- `test_analyze_type_mismatch`: 测试类型不匹配的分析
- `test_analyze_extra_field`: 测试额外字段的分析

#### 2. TestSeverityClassification - 严重程度分类测试
- `test_classify_critical_severity`: 测试关键字段的严重程度
- `test_classify_medium_severity`: 测试一般字段的严重程度
- `test_classify_low_severity`: 测试额外字段的严重程度

#### 3. TestAutoRepairCapability - 自动修复能力测试
- `test_can_repair_type_mismatch`: 测试类型不匹配可以修复
- `test_cannot_repair_critical_missing_field`: 测试关键字段缺失不能自动修复
- `test_can_repair_extra_field`: 测试额外字段可以修复

#### 4. TestRepairSuggestion - 修复建议测试
- `test_suggestion_for_missing_field`: 测试缺失字段的修复建议
- `test_suggestion_for_type_mismatch`: 测试类型不匹配的修复建议

#### 5. TestManualReviewRequirement - 人工审核需求测试
- `test_requires_review_for_critical`: 测试关键错误需要人工审核
- `test_requires_review_for_multiple_high`: 测试多个高级错误需要人工审核
- `test_no_review_for_repair_success`: 测试修复成功不需要人工审核

#### 6. TestHandleMismatch - 完整处理流程测试
- `test_handle_valid_data`: 测试处理有效数据
- `test_handle_missing_field`: 测试处理缺失字段
- `test_handle_type_mismatch`: 测试处理类型不匹配
- `test_handle_ignore_strategy`: 测试忽略策略

### 集成测试 (`test_schema_validation_integration.py`)

#### 1. TestSchemaValidationScenarios - Schema 验证场景测试
- `test_scenario_missing_required_field`: 场景1 - 缺失必填字段
- `test_scenario_type_mismatch`: 场景2 - 类型不匹配
- `test_scenario_extra_field`: 场景3 - 额外字段
- `test_scenario_valid_data`: 场景4 - 有效数据
- `test_scenario_multiple_errors`: 场景5 - 多个错误

#### 2. TestRepairStrategies - 修复策略测试
- `test_auto_repair_strategy`: 测试自动修复策略
- `test_ignore_strategy`: 测试忽略策略

#### 3. TestFallbackStrategies - 降级策略测试
- `test_fallback_on_repair_failure`: 测试修复失败时的降级

#### 4. TestDatabaseRecording - 数据库记录测试
- `test_record_validation_to_db`: 测试验证结果记录到数据库

### 场景测试 (`test_schema_mismatch_scenarios.py`)

#### TestRealWorldScenarios - 真实场景测试
- `test_scenario_invoice_number_as_integer`: 发票号码返回为整数
- `test_scenario_amount_as_string`: 金额返回为字符串
- `test_scenario_missing_critical_field`: 缺失关键字段
- `test_scenario_extra_fields_from_model`: 模型返回额外字段
- `test_scenario_nested_structure_mismatch`: 嵌套结构不匹配
- `test_scenario_completely_wrong_structure`: 完全错误的数据结构
- `test_scenario_partial_data`: 部分数据缺失
- `test_scenario_null_values`: 字段值为 null
- `test_scenario_empty_strings`: 空字符串

## 快速手动测试

运行手动测试脚本（不需要数据库）：

```bash
cd backend
python test_schema_mismatch_manual.py
```

这个脚本会测试5个常见场景，输出详细的处理结果。

## 手动测试步骤

### 1. 准备测试数据

创建测试 Schema：

```python
schema_definition = {
    "type": "object",
    "required": ["invoice_no", "invoice_date", "total_amount"],
    "properties": {
        "invoice_no": {"type": "string"},
        "invoice_date": {"type": "string", "format": "date"},
        "total_amount": {"type": "number"}
    },
    "additionalProperties": False
}
```

### 2. 测试场景1: 缺失必填字段

**输入数据**:
```json
{
  "invoice_date": "2024-01-01",
  "total_amount": 1000.00
}
```

**预期结果**:
- `has_mismatch`: true
- `total_errors`: >= 1
- `mismatch_items` 中包含 `invoice_no` 的缺失错误
- `requires_manual_review`: true (如果是关键字段)

### 3. 测试场景2: 类型不匹配

**输入数据**:
```json
{
  "invoice_no": 12345678,
  "invoice_date": "2024-01-01",
  "total_amount": "1000.00"
}
```

**预期结果**:
- `has_mismatch`: true
- `repair_result.success`: true (如果可以修复)
- `final_data.invoice_no`: "12345678" (字符串)
- `final_data.total_amount`: 1000.00 (数字)

### 4. 测试场景3: 额外字段

**输入数据**:
```json
{
  "invoice_no": "12345678",
  "invoice_date": "2024-01-01",
  "total_amount": 1000.00,
  "extra_field": "not_allowed"
}
```

**预期结果**:
- `has_mismatch`: true
- `total_warnings`: >= 1
- `final_data` 中不包含 `extra_field`

### 4. 使用 API 测试

#### 创建识别任务并测试

```bash
# 1. 上传发票文件
POST /api/v1/invoices/upload
Content-Type: multipart/form-data
file: test_invoice.pdf

# 2. 创建识别任务（使用有 Schema 不匹配的模型配置）
POST /api/v1/invoices/recognition-tasks
{
  "invoice_id": "...",
  "params": {
    "output_schema_id": "...",
    "model_config_id": "..."
  }
}

# 3. 查询 Schema 验证状态
GET /api/v1/invoices/{invoice_id}/schema-validation

# 4. 查看不匹配详情
GET /api/v1/invoices/{invoice_id}/schema-validation
```

## 测试检查清单

### 功能测试
- [ ] 缺失必填字段检测
- [ ] 类型不匹配检测
- [ ] 额外字段检测
- [ ] 值验证失败检测
- [ ] 嵌套结构不匹配检测

### 修复功能测试
- [ ] 自动修复缺失字段（使用默认值）
- [ ] 自动修复类型不匹配（类型转换）
- [ ] 自动移除额外字段
- [ ] 修复后数据验证

### 降级策略测试
- [ ] 修复失败时使用降级策略
- [ ] 降级数据格式正确
- [ ] 降级策略选择合理

### 人工审核测试
- [ ] CRITICAL 错误触发人工审核
- [ ] 多个 HIGH 错误触发人工审核
- [ ] 修复失败触发人工审核

### 数据库记录测试
- [ ] 验证记录正确保存
- [ ] 修复动作正确记录
- [ ] 降级信息正确记录

### 性能测试
- [ ] 处理时间在合理范围内
- [ ] 大量不匹配项的处理性能
- [ ] 并发处理能力

## 调试技巧

### 1. 启用详细日志

在测试中添加日志输出：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 检查中间结果

```python
result = await schema_mismatch_handler.handle_mismatch(...)
print(f"Mismatch items: {result.mismatch_items}")
print(f"Repair actions: {result.repair_result.repair_actions if result.repair_result else None}")
print(f"Final data: {result.final_data}")
```

### 3. 使用 pytest 的调试选项

```bash
# 在第一个失败时停止
pytest -x

# 显示详细输出
pytest -v -s

# 显示局部变量
pytest -l
```

## 常见问题

### Q: 测试失败，提示 Schema 不存在
A: 确保测试中创建了 Schema 或使用现有的 Schema ID

### Q: 测试中验证总是通过
A: 检查 Schema 定义是否正确，确保 `additionalProperties: false` 等设置正确

### Q: 修复结果不符合预期
A: 检查 `schema_validation_service` 的实现，确保修复逻辑正确

## 持续集成

在 CI/CD 中添加测试：

```yaml
# .github/workflows/test.yml
- name: Run Schema Mismatch Tests
  run: |
    cd backend
    pytest app/tests/services/test_schema_mismatch*.py -v --cov=app.services.schema_mismatch_handler
```

## 测试报告示例

运行测试后，查看覆盖率报告：

```bash
pytest app/tests/services/test_schema_mismatch*.py --cov=app.services.schema_mismatch_handler --cov-report=html
# 打开 htmlcov/index.html 查看详细覆盖率
```

## 下一步

1. 添加更多边界情况测试
2. 添加性能测试
3. 添加压力测试
4. 集成到 CI/CD 流程

