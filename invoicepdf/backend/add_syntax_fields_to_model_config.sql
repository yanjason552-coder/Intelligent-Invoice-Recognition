-- 为 model_config 表添加 syntax 相关字段
-- 如果字段已存在，会报错但不会影响

DO $$ 
BEGIN
    -- 添加 syntax_endpoint 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'model_config' AND column_name = 'syntax_endpoint'
    ) THEN
        ALTER TABLE model_config ADD COLUMN syntax_endpoint VARCHAR(500);
    END IF;

    -- 添加 syntax_api_key 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'model_config' AND column_name = 'syntax_api_key'
    ) THEN
        ALTER TABLE model_config ADD COLUMN syntax_api_key VARCHAR(200);
    END IF;

    -- 添加 syntax_app_id 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'model_config' AND column_name = 'syntax_app_id'
    ) THEN
        ALTER TABLE model_config ADD COLUMN syntax_app_id VARCHAR(100);
    END IF;

    -- 添加 syntax_workflow_id 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'model_config' AND column_name = 'syntax_workflow_id'
    ) THEN
        ALTER TABLE model_config ADD COLUMN syntax_workflow_id VARCHAR(100);
    END IF;
END $$;

-- 更新 provider 默认值为 syntax（如果还没有设置）
UPDATE model_config 
SET provider = 'syntax' 
WHERE provider = 'dify' OR provider IS NULL;

