# 修复 sample_file_path 和 sample_file_type 列缺失问题

## 问题描述

错误信息：
```
column template.sample_file_path does not exist
column template.sample_file_type does not exist
```

这是因为模型定义中包含了 `sample_file_path` 和 `sample_file_type` 字段，但数据库中这些列不存在。

## 解决方案

有两种方法可以修复这个问题：

### 方法1：直接运行SQL脚本（推荐，最快）

1. 连接到PostgreSQL数据库
2. 运行以下SQL脚本：

```sql
-- 文件位置: backend/fix_add_sample_file_columns.sql
DO $$
BEGIN
    -- 添加 sample_file_path 列（如果不存在）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'sample_file_path'
    ) THEN
        ALTER TABLE template ADD COLUMN sample_file_path VARCHAR(500);
        RAISE NOTICE '✓ 已添加 sample_file_path 列';
    END IF;
    
    -- 添加 sample_file_type 列（如果不存在）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'sample_file_type'
    ) THEN
        ALTER TABLE template ADD COLUMN sample_file_type VARCHAR(50);
        RAISE NOTICE '✓ 已添加 sample_file_type 列';
    END IF;
END $$;
```

或者直接运行SQL文件：
```bash
psql -U your_username -d your_database -f backend/fix_add_sample_file_columns.sql
```

### 方法2：运行Alembic迁移

如果迁移链正确，可以运行：

```powershell
cd backend
python -m alembic upgrade head
```

这会应用所有未应用的迁移，包括 `add_sample_file_to_template_001`。

### 方法3：运行Python修复脚本

```powershell
cd backend
python fix_add_sample_file_columns.py
```

## 验证修复

修复后，可以通过以下方式验证：

```sql
-- 检查列是否存在
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'template' 
AND column_name IN ('sample_file_path', 'sample_file_type');
```

应该看到两行结果：
- sample_file_path | character varying(500)
- sample_file_type | character varying(50)

## 注意事项

- 这些列是可选的（nullable=True），所以不会影响现有数据
- 修复后需要重启后端服务才能生效
- 如果使用Docker，可能需要重启容器

