"""
手动修复迁移：添加缺失的列
如果迁移没有完全执行，可以运行此脚本
"""
import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_missing_columns():
    """添加缺失的列"""
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        # 检查并添加 parent_field_id
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'template_field' AND column_name = 'parent_field_id'
                ) THEN
                    ALTER TABLE template_field ADD COLUMN parent_field_id UUID;
                    ALTER TABLE template_field 
                    ADD CONSTRAINT fk_template_field_parent_id 
                    FOREIGN KEY (parent_field_id) 
                    REFERENCES template_field(id) 
                    ON DELETE CASCADE;
                END IF;
            END $$;
        """))
        
        # 检查并添加 deprecated
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'template_field' AND column_name = 'deprecated'
                ) THEN
                    ALTER TABLE template_field ADD COLUMN deprecated BOOLEAN DEFAULT FALSE;
                END IF;
            END $$;
        """))
        
        # 检查并添加 deprecated_at
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'template_field' AND column_name = 'deprecated_at'
                ) THEN
                    ALTER TABLE template_field ADD COLUMN deprecated_at TIMESTAMP;
                END IF;
            END $$;
        """))
        
        # 删除可能存在的 sub_fields 列
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'template_field' AND column_name = 'sub_fields'
                ) THEN
                    ALTER TABLE template_field DROP COLUMN sub_fields;
                END IF;
            END $$;
        """))
        
        conn.commit()
        print("✅ 缺失的列已添加")

if __name__ == "__main__":
    fix_missing_columns()

