-- 添加 sample_file_path 和 sample_file_type 列到 template 表
-- 修复错误: column template.sample_file_path does not exist

DO $$
BEGIN
    -- 添加 sample_file_path 列（如果不存在）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'sample_file_path'
    ) THEN
        ALTER TABLE template ADD COLUMN sample_file_path VARCHAR(500);
        RAISE NOTICE '✓ 已添加 sample_file_path 列';
    ELSE
        RAISE NOTICE 'sample_file_path 列已存在，跳过';
    END IF;
    
    -- 添加 sample_file_type 列（如果不存在）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'sample_file_type'
    ) THEN
        ALTER TABLE template ADD COLUMN sample_file_type VARCHAR(50);
        RAISE NOTICE '✓ 已添加 sample_file_type 列';
    ELSE
        RAISE NOTICE 'sample_file_type 列已存在，跳过';
    END IF;
END $$;

