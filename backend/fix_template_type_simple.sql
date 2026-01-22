-- 快速修复 template 表的 template_type 列
-- 在 PostgreSQL 中直接执行此 SQL

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
        RAISE NOTICE '已将 type 列重命名为 template_type';
    END IF;
    
    -- 如果既没有 type 也没有 template_type，添加 template_type 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'template_type'
    ) THEN
        ALTER TABLE template ADD COLUMN template_type VARCHAR(50) NOT NULL DEFAULT '其他';
        RAISE NOTICE '已添加 template_type 列';
    ELSE
        RAISE NOTICE 'template_type 列已存在';
    END IF;
    
    -- 创建索引（如果不存在）
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'template' AND indexname = 'ix_template_template_type'
    ) THEN
        CREATE INDEX ix_template_template_type ON template(template_type);
        RAISE NOTICE '已创建 template_type 索引';
    ELSE
        RAISE NOTICE 'template_type 索引已存在';
    END IF;
END $$;

