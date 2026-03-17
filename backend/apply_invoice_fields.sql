-- 为 invoice 表添加模板和模型信息字段（快照字段）
-- 这些字段保存识别时使用的模板名称、模板版本和模型名称

-- 添加 template_name 字段
ALTER TABLE invoice 
ADD COLUMN IF NOT EXISTS template_name VARCHAR(200);

-- 添加 template_version 字段
ALTER TABLE invoice 
ADD COLUMN IF NOT EXISTS template_version VARCHAR(50);

-- 添加 model_name 字段
ALTER TABLE invoice 
ADD COLUMN IF NOT EXISTS model_name VARCHAR(200);

-- 添加注释（PostgreSQL）
COMMENT ON COLUMN invoice.template_name IS '识别时使用的模板名称（快照）';
COMMENT ON COLUMN invoice.template_version IS '识别时使用的模板版本（快照）';
COMMENT ON COLUMN invoice.model_name IS '识别时使用的模型名称（快照）';

