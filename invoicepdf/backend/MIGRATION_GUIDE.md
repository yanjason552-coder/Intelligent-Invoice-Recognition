# 数据库迁移指南

## 执行数据库迁移

### 1. 检查当前迁移状态

```bash
cd backend
alembic current
```

### 2. 查看迁移历史

```bash
alembic history
```

### 3. 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 或者指定版本
alembic upgrade create_invoice_tables_001
```

### 4. 回滚迁移（如果需要）

```bash
# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade 1a31ce608336
```

## 迁移文件说明

迁移文件：`backend/app/alembic/versions/create_invoice_recognition_tables.py`

此迁移文件会创建以下表：
- invoice_file（票据文件表）
- template（模板表）
- template_field（模板字段表）
- template_training_task（模板训练任务表）
- invoice（票据表）
- recognition_task（识别任务表）
- recognition_result（识别结果表）
- recognition_field（识别字段表）
- review_record（审核记录表）
- ocr_config（OCR配置表）
- recognition_rule（识别规则表）

## 注意事项

1. **备份数据库**：在执行迁移前，请先备份数据库
2. **测试环境**：建议先在测试环境执行迁移
3. **依赖关系**：迁移文件依赖于 `1a31ce608336` 版本，确保该版本已执行
4. **外键约束**：所有外键都设置了适当的删除策略（CASCADE 或 SET NULL）

## 验证迁移

迁移执行后，可以通过以下方式验证：

```sql
-- 检查表是否存在
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'invoice%' OR table_name LIKE 'template%' OR table_name LIKE 'recognition%' OR table_name LIKE 'review%' OR table_name LIKE 'ocr%';

-- 检查表结构
\d invoice
\d template
\d recognition_task
```

## 常见问题

### 问题1：迁移失败，提示表已存在
**解决方案**：检查是否已经手动创建了表，如果是，可以：
1. 删除已创建的表
2. 或者修改迁移文件，使用 `op.create_table(..., if_not_exists=True)`

### 问题2：外键约束错误
**解决方案**：确保依赖的表（如 user 表）已经存在

### 问题3：UUID类型不支持
**解决方案**：确保PostgreSQL版本 >= 13，或者使用字符串类型替代UUID


