-- 添加 prompt 字段到 template 表
-- 如果字段已存在，则不会报错（使用 IF NOT EXISTS）

-- PostgreSQL
ALTER TABLE template ADD COLUMN IF NOT EXISTS prompt TEXT;

-- 验证字段是否添加成功
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'template' AND column_name = 'prompt';

