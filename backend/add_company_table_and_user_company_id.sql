-- 添加公司表和用户公司ID列的SQL脚本
-- 如果无法使用 Alembic 迁移，可以手动执行此脚本

-- 1. 创建 company 表
CREATE TABLE IF NOT EXISTS company (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    address VARCHAR(500),
    contact_person VARCHAR(100),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(100),
    description VARCHAR(1000),
    is_active BOOLEAN NOT NULL DEFAULT true
);

-- 2. 创建索引
CREATE INDEX IF NOT EXISTS ix_company_code ON company(code);
CREATE INDEX IF NOT EXISTS ix_company_name ON company(name);

-- 3. 在 user 表中添加 company_id 列
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS company_id UUID;

-- 4. 创建外键约束
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_user_company_id'
    ) THEN
        ALTER TABLE "user" 
        ADD CONSTRAINT fk_user_company_id 
        FOREIGN KEY (company_id) 
        REFERENCES company(id) 
        ON DELETE SET NULL;
    END IF;
END $$;

-- 5. 创建索引
CREATE INDEX IF NOT EXISTS ix_user_company_id ON "user"(company_id);

