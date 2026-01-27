-- 修复 invoice.company_id 列类型：从 bigint 改为 UUID
-- 执行前请备份数据库！

-- 1. 检查当前列类型
SELECT 
    column_name, 
    data_type, 
    udt_name
FROM information_schema.columns 
WHERE table_name = 'invoice' 
AND column_name = 'company_id';

-- 2. 删除外键约束（如果存在）
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_invoice_company_id'
    ) THEN
        ALTER TABLE invoice DROP CONSTRAINT fk_invoice_company_id;
        RAISE NOTICE '已删除外键约束 fk_invoice_company_id';
    ELSE
        RAISE NOTICE '外键约束 fk_invoice_company_id 不存在';
    END IF;
END $$;

-- 3. 删除索引（如果存在）
DROP INDEX IF EXISTS ix_invoice_company_id;

-- 4. 删除旧列（如果存在且类型不是 UUID）
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'invoice' 
        AND column_name = 'company_id'
        AND data_type != 'uuid'
    ) THEN
        ALTER TABLE invoice DROP COLUMN company_id;
        RAISE NOTICE '已删除旧 company_id 列';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'invoice' 
        AND column_name = 'company_id'
        AND data_type = 'uuid'
    ) THEN
        RAISE NOTICE 'company_id 列已经是 UUID 类型，无需修改';
    ELSE
        RAISE NOTICE 'company_id 列不存在，将创建新列';
    END IF;
END $$;

-- 5. 创建 UUID 类型的 company_id 列（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'invoice' 
        AND column_name = 'company_id'
    ) THEN
        ALTER TABLE invoice ADD COLUMN company_id UUID;
        RAISE NOTICE '已创建 company_id 列（UUID 类型）';
    END IF;
END $$;

-- 6. 创建外键约束
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_invoice_company_id'
    ) THEN
        ALTER TABLE invoice 
        ADD CONSTRAINT fk_invoice_company_id 
        FOREIGN KEY (company_id) 
        REFERENCES company(id) 
        ON DELETE SET NULL;
        RAISE NOTICE '已创建外键约束 fk_invoice_company_id';
    END IF;
END $$;

-- 7. 创建索引
CREATE INDEX IF NOT EXISTS ix_invoice_company_id ON invoice(company_id);

-- 8. 验证修复结果
SELECT 
    column_name, 
    data_type, 
    udt_name,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'invoice' 
AND column_name = 'company_id';

