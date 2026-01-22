-- 修复 template_version 表缺失的列
-- 如果列已存在，会忽略错误

-- 添加 schema_snapshot 列（JSONB类型，用于存储模板字段schema快照）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_version' AND column_name = 'schema_snapshot'
    ) THEN
        ALTER TABLE template_version 
        ADD COLUMN schema_snapshot JSONB;
        
        -- 添加注释说明
        COMMENT ON COLUMN template_version.schema_snapshot IS 'Schema快照（发布时生成，用于任务引用，不随模板后续变化）';
    ELSE
        -- 如果列已存在但类型不是JSONB，尝试转换
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'template_version' 
            AND column_name = 'schema_snapshot'
            AND data_type != 'jsonb'
        ) THEN
            -- 先删除旧列（如果数据不重要）
            -- ALTER TABLE template_version DROP COLUMN schema_snapshot;
            -- ALTER TABLE template_version ADD COLUMN schema_snapshot JSONB;
            -- 或者使用转换（如果数据重要）
            ALTER TABLE template_version 
            ALTER COLUMN schema_snapshot TYPE JSONB USING schema_snapshot::jsonb;
        END IF;
    END IF;
END $$;

-- 添加 etag 列
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_version' AND column_name = 'etag'
    ) THEN
        ALTER TABLE template_version 
        ADD COLUMN etag VARCHAR(50);
    END IF;
END $$;

-- 添加 locked_by 列
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_version' AND column_name = 'locked_by'
    ) THEN
        ALTER TABLE template_version 
        ADD COLUMN locked_by UUID;
        
        -- 添加外键约束
        ALTER TABLE template_version 
        ADD CONSTRAINT fk_template_version_locked_by 
        FOREIGN KEY (locked_by) 
        REFERENCES "user"(id);
    END IF;
END $$;

-- 添加 locked_at 列
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_version' AND column_name = 'locked_at'
    ) THEN
        ALTER TABLE template_version 
        ADD COLUMN locked_at TIMESTAMP;
    END IF;
END $$;

