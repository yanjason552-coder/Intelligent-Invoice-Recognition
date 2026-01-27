# Schema 不匹配处理方案

## 概述

当调用大模型 API 返回的 schema 与系统定义的 schema 不一致时，系统采用多层次的自动处理机制，确保数据可用性和系统稳定性。

## 处理流程

### 1. 验证阶段

**目标**: 检测 schema 不匹配

**步骤**:
1. 使用 JSON Schema 验证器验证大模型返回的数据
2. 识别所有不匹配项（错误和警告）
3. 分类不匹配类型和严重程度

**输出**: `ValidationResult`
- `is_valid`: 是否通过验证
- `errors`: 错误列表
- `warnings`: 警告列表

### 2. 分析阶段

**目标**: 深入分析不匹配项

**不匹配类型**:
- `MISSING_REQUIRED_FIELD`: 缺失必填字段
- `TYPE_MISMATCH`: 类型不匹配
- `EXTRA_FIELD`: 额外字段（不允许）
- `VALUE_VALIDATION_FAILED`: 值验证失败
- `SCHEMA_VERSION_MISMATCH`: Schema 版本不匹配
- `STRUCTURE_MISMATCH`: 结构不匹配

**严重程度**:
- `CRITICAL`: 关键字段缺失或类型错误，无法修复
- `HIGH`: 重要字段问题，需要人工介入
- `MEDIUM`: 一般字段问题，可自动修复
- `LOW`: 警告级别，不影响使用
- `INFO`: 信息级别，仅记录

### 3. 自动修复阶段

**目标**: 尝试自动修复可修复的不匹配项

**修复策略**:
1. **缺失必填字段**: 
   - 使用 Schema 定义的默认值
   - 根据字段类型设置空值（空字符串、0、null 等）

2. **类型不匹配**:
   - 尝试类型转换（字符串转数字、数字转字符串等）
   - 转换失败则使用默认值

3. **额外字段**:
   - 移除不在 Schema 定义中的字段

4. **值验证失败**:
   - 根据验证规则尝试修正
   - 修正失败则使用默认值

**输出**: `RepairResult`
- `success`: 修复是否成功
- `repaired_data`: 修复后的数据
- `repair_actions`: 修复动作列表

### 4. 降级策略阶段

**目标**: 当自动修复失败时，使用降级策略返回可用数据

**降级策略**:
- `partial`: 返回部分有效数据（修复后的数据）
- `empty`: 返回空数据结构（保留 Schema 结构）
- `text`: 返回原始文本数据
- `error`: 返回错误信息

**选择逻辑**:
- 如果修复成功 → `partial`
- 如果只有警告 → `partial`
- 如果修复失败但数据可用 → `partial`
- 如果完全失败 → `empty` 或 `error`

### 5. 人工审核标记

**触发条件**:
- 存在 CRITICAL 级别的不匹配
- 存在 3 个或以上 HIGH 级别的不匹配
- 自动修复失败

**处理方式**:
- 标记任务为"需要人工审核"
- 记录详细的不匹配信息
- 在前端展示不匹配详情
- 允许人工修正后重新处理

## 数据记录

### SchemaValidationRecord 表

记录每次验证的详细信息：

```sql
- id: UUID
- invoice_id: UUID
- task_id: UUID
- schema_id: UUID
- is_valid: BOOLEAN
- error_count: INTEGER
- warning_count: INTEGER
- validation_errors: JSON  # 详细错误信息
- validation_warnings: JSON  # 警告信息
- repair_attempted: BOOLEAN
- repair_success: BOOLEAN
- repair_actions: JSON  # 修复动作列表
- fallback_type: VARCHAR
- fallback_data: JSON
- validation_time_ms: FLOAT
- repair_time_ms: FLOAT
- total_time_ms: FLOAT
- created_at: DATETIME
```

## 监控和告警

### 监控指标

1. **验证成功率**: 验证通过的任务比例
2. **自动修复成功率**: 自动修复成功的比例
3. **人工审核率**: 需要人工审核的任务比例
4. **不匹配类型分布**: 各类型不匹配的统计
5. **严重程度分布**: 各严重程度的统计

### 告警规则

1. **验证失败率 > 20%**: 告警
2. **CRITICAL 级别不匹配 > 5%**: 告警
3. **自动修复失败率 > 30%**: 告警
4. **人工审核率 > 10%**: 告警

## 前端展示

### 不匹配详情页面

显示以下信息：
1. **不匹配概览**:
   - 总错误数、警告数
   - 各严重程度的数量
   - 是否可自动修复

2. **不匹配列表**:
   - 字段路径
   - 不匹配类型
   - 严重程度
   - 期望值 vs 实际值
   - 修复建议

3. **处理结果**:
   - 自动修复动作
   - 降级策略
   - 最终返回数据

4. **操作按钮**:
   - 查看原始数据
   - 查看修复后数据
   - 手动修正
   - 重新识别

## 最佳实践

### 1. Schema 设计

- 使用宽松的 Schema 定义（允许额外字段）
- 为关键字段设置合理的默认值
- 使用类型联合（union types）提高兼容性
- 版本化 Schema，支持向后兼容

### 2. 模型配置

- 在提示词中明确指定输出格式
- 使用示例数据引导模型输出
- 定期更新 Schema 定义以匹配模型输出

### 3. 监控和优化

- 定期分析不匹配模式
- 优化 Schema 定义
- 调整自动修复策略
- 改进模型提示词

## API 端点

### 获取不匹配详情

```
GET /api/v1/invoices/{invoice_id}/schema-mismatch
```

返回:
```json
{
  "has_mismatch": true,
  "mismatch_items": [...],
  "validation_result": {...},
  "repair_result": {...},
  "fallback_result": {...},
  "requires_manual_review": true
}
```

### 手动修正不匹配

```
POST /api/v1/invoices/{invoice_id}/schema-mismatch/fix
```

请求体:
```json
{
  "field_path": "invoice_no",
  "corrected_value": "12345678"
}
```

## 配置选项

### 处理策略配置

```python
HANDLING_STRATEGY = "auto"  # auto/manual/ignore

# 关键字段列表（用于严重程度判断）
CRITICAL_FIELDS = [
    "invoice_no",
    "invoice_date",
    "total_amount",
    "supplier_name"
]

# 自动修复配置
AUTO_REPAIR_ENABLED = True
AUTO_REPAIR_MAX_ATTEMPTS = 3

# 降级策略配置
FALLBACK_STRATEGY = "auto"  # auto/partial/empty/text/error
```

## 示例场景

### 场景 1: 缺失必填字段

**输入**: 
```json
{
  "invoice_date": "2024-01-01",
  "total_amount": 1000.00
}
```

**Schema 要求**: `invoice_no` 为必填字段

**处理**:
1. 检测到缺失 `invoice_no`
2. 判断为 HIGH 严重程度（关键字段）
3. 尝试自动修复：设置默认值 `""`
4. 标记需要人工审核
5. 返回修复后的数据

### 场景 2: 类型不匹配

**输入**:
```json
{
  "invoice_no": 12345678,
  "total_amount": "1000.00"
}
```

**Schema 要求**: 
- `invoice_no`: string
- `total_amount`: number

**处理**:
1. 检测到类型不匹配
2. 判断为 MEDIUM 严重程度
3. 自动修复：
   - `invoice_no`: `12345678` → `"12345678"`
   - `total_amount`: `"1000.00"` → `1000.00`
4. 修复成功，返回修复后的数据

### 场景 3: 额外字段

**输入**:
```json
{
  "invoice_no": "12345678",
  "invoice_date": "2024-01-01",
  "extra_field": "not_in_schema"
}
```

**Schema 要求**: `additionalProperties: false`

**处理**:
1. 检测到额外字段 `extra_field`
2. 判断为 LOW 严重程度
3. 自动修复：移除 `extra_field`
4. 修复成功，返回修复后的数据

## 总结

通过多层次的自动处理机制，系统能够：
1. **自动检测** schema 不匹配
2. **智能修复** 可修复的不匹配项
3. **优雅降级** 确保系统可用性
4. **详细记录** 便于问题追踪和优化
5. **人工介入** 处理复杂情况

这确保了系统的稳定性和数据的可用性，同时提供了完善的监控和优化机制。

