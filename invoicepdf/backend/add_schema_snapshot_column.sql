-- 为 template_version 表添加 schema_snapshot 列（JSONB类型）
-- 这是最正确、最符合整体设计的方案

-- 添加 schema_snapshot 列（JSONB类型）
ALTER TABLE template_version
ADD COLUMN IF NOT EXISTS schema_snapshot JSONB;

-- 添加注释说明
COMMENT ON COLUMN template_version.schema_snapshot IS 'Schema快照（发布时生成，用于任务引用，不随模板后续变化）';

-- 如果列已存在但类型不是JSONB，转换为JSONB
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'template_version' 
        AND column_name = 'schema_snapshot'
        AND data_type != 'jsonb'
    ) THEN
        -- 转换为JSONB类型
        ALTER TABLE template_version 
        ALTER COLUMN schema_snapshot TYPE JSONB USING schema_snapshot::jsonb;
    END IF;
END $$;

