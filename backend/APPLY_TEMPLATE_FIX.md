# 修复 template_type 列

## 问题
数据库中的 `template` 表缺少 `template_type` 列，导致 API 返回 500 错误。

## 解决方案

### 方法 1：直接执行 SQL（最快）

在 PostgreSQL 数据库中执行 `fix_template_type_simple.sql` 文件中的 SQL：

```sql
DO $$
BEGIN
    -- 如果存在 type 列，重命名为 template_type
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'type'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'template_type'
    ) THEN
        ALTER TABLE template RENAME COLUMN type TO template_type;
    END IF;
    
    -- 如果既没有 type 也没有 template_type，添加 template_type 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'template_type'
    ) THEN
        ALTER TABLE template ADD COLUMN template_type VARCHAR(50) NOT NULL DEFAULT '其他';
    END IF;
    
    -- 创建索引（如果不存在）
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'template' AND indexname = 'ix_template_template_type'
    ) THEN
        CREATE INDEX ix_template_template_type ON template(template_type);
    END IF;
END $$;
```

### 方法 2：通过 Alembic 迁移

如果 `fix_template_type_001` 迁移还没有应用，可以：

```powershell
cd backend

# 检查当前版本
python -m alembic current

# 如果显示 template_version_001，需要先应用 add_template_management_001 分支
# 先升级到 add_template_management_001
python -m alembic upgrade add_template_management_001

# 然后升级到 fix_template_type_001
python -m alembic upgrade fix_template_type_001

# 最后升级合并迁移
python -m alembic upgrade merge_template_branches_001
```

## 验证

修复后，刷新前端页面，模板列表应该能正常加载。

如果还有问题，检查后端日志确认 `template_type` 列是否存在。

