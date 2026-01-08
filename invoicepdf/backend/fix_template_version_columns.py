"""
手动修复 template_version 表缺失的列
如果迁移没有完全执行，可以运行此脚本
"""
import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_template_version_columns():
    """添加缺失的列"""
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        # 检查并添加 schema_snapshot（JSONB类型）
        print("检查 schema_snapshot 列...")
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'template_version' AND column_name = 'schema_snapshot'
                ) THEN
                    ALTER TABLE template_version ADD COLUMN schema_snapshot JSONB;
                    COMMENT ON COLUMN template_version.schema_snapshot IS 'Schema快照（发布时生成，用于任务引用，不随模板后续变化）';
                    RAISE NOTICE 'schema_snapshot 列已添加（JSONB类型）';
                ELSE
                    -- 如果列已存在但类型不是JSONB，转换为JSONB
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'template_version' 
                        AND column_name = 'schema_snapshot'
                        AND data_type != 'jsonb'
                    ) THEN
                        ALTER TABLE template_version 
                        ALTER COLUMN schema_snapshot TYPE JSONB USING schema_snapshot::jsonb;
                        RAISE NOTICE 'schema_snapshot 列类型已转换为 JSONB';
                    ELSE
                        RAISE NOTICE 'schema_snapshot 列已存在且类型正确（JSONB）';
                    END IF;
                END IF;
            END $$;
        """))
        print("  ✓ schema_snapshot 列已处理（JSONB类型）")
        
        # 检查并添加 etag
        print("检查 etag 列...")
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'template_version' AND column_name = 'etag'
                ) THEN
                    ALTER TABLE template_version ADD COLUMN etag VARCHAR(50);
                    RAISE NOTICE 'etag 列已添加';
                ELSE
                    RAISE NOTICE 'etag 列已存在';
                END IF;
            END $$;
        """))
        print("  ✓ etag 列已处理")
        
        # 检查并添加 locked_by
        print("检查 locked_by 列...")
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'template_version' AND column_name = 'locked_by'
                ) THEN
                    ALTER TABLE template_version ADD COLUMN locked_by UUID;
                    RAISE NOTICE 'locked_by 列已添加';
                ELSE
                    RAISE NOTICE 'locked_by 列已存在';
                END IF;
            END $$;
        """))
        print("  ✓ locked_by 列已处理")
        
        # 检查并添加外键约束（如果列已存在但约束不存在）
        print("检查 locked_by 外键约束...")
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'fk_template_version_locked_by'
                ) THEN
                    ALTER TABLE template_version 
                    ADD CONSTRAINT fk_template_version_locked_by 
                    FOREIGN KEY (locked_by) 
                    REFERENCES "user"(id);
                    RAISE NOTICE 'locked_by 外键约束已添加';
                ELSE
                    RAISE NOTICE 'locked_by 外键约束已存在';
                END IF;
            END $$;
        """))
        print("  ✓ locked_by 外键约束已处理")
        
        # 检查并添加 locked_at
        print("检查 locked_at 列...")
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'template_version' AND column_name = 'locked_at'
                ) THEN
                    ALTER TABLE template_version ADD COLUMN locked_at TIMESTAMP;
                    RAISE NOTICE 'locked_at 列已添加';
                ELSE
                    RAISE NOTICE 'locked_at 列已存在';
                END IF;
            END $$;
        """))
        print("  ✓ locked_at 列已处理")
        
        conn.commit()
        print("\n✅ template_version 表的所有缺失列已添加/验证完成")

if __name__ == "__main__":
    fix_template_version_columns()

