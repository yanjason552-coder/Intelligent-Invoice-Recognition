-- 添加 currency 字段到 invoice 表
-- 执行此脚本以添加 currency 字段

ALTER TABLE invoice 
ADD COLUMN IF NOT EXISTS currency VARCHAR(10);

-- 添加注释
COMMENT ON COLUMN invoice.currency IS '币种（如：CNY、USD等）';

