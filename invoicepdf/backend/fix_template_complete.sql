-- ============================================================
-- 全面修复模板相关数据库结构
-- 清理旧字段，修复新字段，确保表结构与新模型一致
-- ============================================================

-- 1. 修复 template 表的 template_type 列
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
        RAISE NOTICE '✓ 已将 type 列重命名为 template_type';
    END IF;
    
    -- 如果既没有 type 也没有 template_type，添加 template_type 列
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'template_type'
    ) THEN
        ALTER TABLE template ADD COLUMN template_type VARCHAR(50) NOT NULL DEFAULT '其他';
        RAISE NOTICE '✓ 已添加 template_type 列';
    ELSE
        RAISE NOTICE '✓ template_type 列已存在';
    END IF;
END $$;

-- 2. 删除旧的、不需要的列
DO $$
BEGIN
    -- 删除 template_file_path
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'template_file_path'
    ) THEN
        ALTER TABLE template DROP COLUMN template_file_path;
        RAISE NOTICE '✓ 已删除 template_file_path 列';
    END IF;
    
    -- 删除 sample_image_path
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'sample_image_path'
    ) THEN
        ALTER TABLE template DROP COLUMN sample_image_path;
        RAISE NOTICE '✓ 已删除 sample_image_path 列';
    END IF;
    
    -- 删除 training_samples
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'training_samples'
    ) THEN
        ALTER TABLE template DROP COLUMN training_samples;
        RAISE NOTICE '✓ 已删除 training_samples 列';
    END IF;
    
    -- 删除 last_training_time
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'last_training_time'
    ) THEN
        ALTER TABLE template DROP COLUMN last_training_time;
        RAISE NOTICE '✓ 已删除 last_training_time 列';
    END IF;
    
    -- 删除旧的 version 列（现在使用 template_version 表）
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'version'
    ) THEN
        ALTER TABLE template DROP COLUMN version;
        RAISE NOTICE '✓ 已删除 version 列';
    END IF;
END $$;

-- 3. 确保必需的列存在
DO $$
BEGIN
    -- 添加 current_version_id（如果不存在）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'current_version_id'
    ) THEN
        ALTER TABLE template ADD COLUMN current_version_id UUID;
        RAISE NOTICE '✓ 已添加 current_version_id 列';
    END IF;
    
    -- 确保 update_time 存在
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template' AND column_name = 'update_time'
    ) THEN
        ALTER TABLE template ADD COLUMN update_time TIMESTAMP;
        RAISE NOTICE '✓ 已添加 update_time 列';
    END IF;
END $$;

-- 4. 修复 status 列的默认值和旧值
DO $$
BEGIN
    -- 将 'active' 状态更新为 'enabled'
    UPDATE template 
    SET status = 'enabled' 
    WHERE status = 'active';
    
    IF FOUND THEN
        RAISE NOTICE '✓ 已修复 status 列的旧值 (active -> enabled)';
    END IF;
END $$;

-- 5. 创建/确保索引存在
DO $$
BEGIN
    -- template_type 索引
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'template' AND indexname = 'ix_template_template_type'
    ) THEN
        CREATE INDEX ix_template_template_type ON template(template_type);
        RAISE NOTICE '✓ 已创建 template_type 索引';
    END IF;
END $$;

-- 6. 修复 template_field 表的字段名（如果存在旧字段）
DO $$
BEGIN
    -- 将 field_code 重命名为 field_key
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_field' AND column_name = 'field_code'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_field' AND column_name = 'field_key'
    ) THEN
        ALTER TABLE template_field RENAME COLUMN field_code TO field_key;
        RAISE NOTICE '✓ 已将 field_code 重命名为 field_key';
    END IF;
    
    -- 将 field_type 重命名为 data_type
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_field' AND column_name = 'field_type'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_field' AND column_name = 'data_type'
    ) THEN
        ALTER TABLE template_field RENAME COLUMN field_type TO data_type;
        RAISE NOTICE '✓ 已将 field_type 重命名为 data_type';
    END IF;
END $$;

-- 7. 确保 template_field 表有必需的列
DO $$
BEGIN
    -- 添加 template_version_id（如果不存在）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_field' AND column_name = 'template_version_id'
    ) THEN
        ALTER TABLE template_field ADD COLUMN template_version_id UUID;
        RAISE NOTICE '✓ 已添加 template_version_id 列到 template_field';
    END IF;
    
    -- 添加 parent_field_id（如果不存在）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_field' AND column_name = 'parent_field_id'
    ) THEN
        ALTER TABLE template_field ADD COLUMN parent_field_id UUID;
        RAISE NOTICE '✓ 已添加 parent_field_id 列到 template_field';
    END IF;
    
    -- 添加 sort_order（如果不存在）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_field' AND column_name = 'sort_order'
    ) THEN
        ALTER TABLE template_field ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0;
        RAISE NOTICE '✓ 已添加 sort_order 列到 template_field';
    END IF;
END $$;

-- 完成
SELECT '模板表结构修复完成！' AS result;

