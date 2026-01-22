-- 修复缺失的列：为 template_field 表添加新字段
-- 如果列已存在，会忽略错误

-- 添加 parent_field_id 列
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_field' AND column_name = 'parent_field_id'
    ) THEN
        ALTER TABLE template_field 
        ADD COLUMN parent_field_id UUID;
        
        -- 添加外键约束
        ALTER TABLE template_field 
        ADD CONSTRAINT fk_template_field_parent_id 
        FOREIGN KEY (parent_field_id) 
        REFERENCES template_field(id) 
        ON DELETE CASCADE;
    END IF;
END $$;

-- 添加 deprecated 列
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_field' AND column_name = 'deprecated'
    ) THEN
        ALTER TABLE template_field 
        ADD COLUMN deprecated BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- 添加 deprecated_at 列
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_field' AND column_name = 'deprecated_at'
    ) THEN
        ALTER TABLE template_field 
        ADD COLUMN deprecated_at TIMESTAMP;
    END IF;
END $$;

-- 检查并删除可能存在的 sub_fields 列（如果存在）
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_field' AND column_name = 'sub_fields'
    ) THEN
        ALTER TABLE template_field DROP COLUMN sub_fields;
    END IF;
END $$;

