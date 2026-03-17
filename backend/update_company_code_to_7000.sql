-- 更新 invoice_file 和 invoice 表中的公司代码字段为 7000
-- 如果字段不存在，先添加字段，然后更新所有行

-- ============================================
-- 1. 处理 invoice_file 表
-- ============================================

-- 检查 invoice_file 表是否有 company_code 字段，如果没有则添加
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'invoice_file' 
        AND column_name = 'company_code'
    ) THEN
        ALTER TABLE invoice_file ADD COLUMN company_code VARCHAR(50);
        RAISE NOTICE '已添加 company_code 字段到 invoice_file 表';
    ELSE
        RAISE NOTICE 'invoice_file 表已存在 company_code 字段';
    END IF;
END $$;

-- 更新 invoice_file 表所有行的 company_code 为 7000
UPDATE invoice_file 
SET company_code = '7000'
WHERE company_code IS NULL OR company_code != '7000';

-- 显示更新结果
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'invoice_file 表已更新 % 行，company_code 设置为 7000', updated_count;
END $$;

-- ============================================
-- 2. 处理 invoice 表
-- ============================================

-- 检查 invoice 表是否有 company_code 字段，如果没有则添加
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'invoice' 
        AND column_name = 'company_code'
    ) THEN
        ALTER TABLE invoice ADD COLUMN company_code VARCHAR(50);
        RAISE NOTICE '已添加 company_code 字段到 invoice 表';
    ELSE
        RAISE NOTICE 'invoice 表已存在 company_code 字段';
    END IF;
END $$;

-- 更新 invoice 表所有行的 company_code 为 7000
UPDATE invoice 
SET company_code = '7000'
WHERE company_code IS NULL OR company_code != '7000';

-- 显示更新结果
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'invoice 表已更新 % 行，company_code 设置为 7000', updated_count;
END $$;

-- ============================================
-- 3. 验证更新结果
-- ============================================

-- 显示统计信息
SELECT 
    'invoice_file' as table_name,
    COUNT(*) as total_rows,
    COUNT(company_code) as rows_with_company_code,
    COUNT(CASE WHEN company_code = '7000' THEN 1 END) as rows_with_7000
FROM invoice_file
UNION ALL
SELECT 
    'invoice' as table_name,
    COUNT(*) as total_rows,
    COUNT(company_code) as rows_with_company_code,
    COUNT(CASE WHEN company_code = '7000' THEN 1 END) as rows_with_7000
FROM invoice;

