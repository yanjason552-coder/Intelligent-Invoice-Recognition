"""
为 template_version 表添加 schema_snapshot 列（JSONB类型）
这是最正确、最符合整体设计的方案
"""
import sys
import os
from sqlalchemy import create_engine, text
from app.core.config import settings

def add_schema_snapshot_column():
    """添加 schema_snapshot 列（JSONB类型）"""
    try:
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        
        with engine.connect() as conn:
            # 添加 schema_snapshot 列（JSONB类型）
            conn.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'template_version' AND column_name = 'schema_snapshot'
                    ) THEN
                        ALTER TABLE template_version ADD COLUMN schema_snapshot JSONB;
                        COMMENT ON COLUMN template_version.schema_snapshot IS 'Schema快照（发布时生成，用于任务引用，不随模板后续变化）';
                        RAISE NOTICE 'schema_snapshot 列已添加';
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
            
            conn.commit()
            print("✅ schema_snapshot 列（JSONB类型）已添加/验证")
            return True
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("正在为 template_version 表添加 schema_snapshot 列（JSONB类型）...")
    success = add_schema_snapshot_column()
    if success:
        print("✅ 完成！")
        sys.exit(0)
    else:
        print("❌ 失败！")
        sys.exit(1)

