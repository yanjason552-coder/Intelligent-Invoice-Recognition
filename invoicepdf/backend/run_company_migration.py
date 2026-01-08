"""
执行公司表和用户 company_id 列的迁移脚本
"""
import sys
import os

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.db import engine

def run_migration():
    """执行迁移"""
    print("=" * 50)
    print("开始执行公司表和用户 company_id 列的迁移")
    print("=" * 50)
    
    try:
        # 使用项目配置的数据库引擎
        print("使用项目配置的数据库连接...")
        
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                print("\n1. 创建 company 表...")
                conn.execute(text("""
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
                    )
                """))
                print("   [OK] company 表创建成功")
                
                print("\n2. 创建索引...")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_company_code ON company(code)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_company_name ON company(name)
                """))
                print("   [OK] 索引创建成功")
                
                print("\n3. 在 user 表中添加 company_id 列...")
                # 检查列是否已存在
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user' 
                    AND column_name = 'company_id'
                """))
                
                if result.fetchone() is None:
                    conn.execute(text("""
                        ALTER TABLE "user" ADD COLUMN company_id UUID
                    """))
                    print("   [OK] company_id 列添加成功")
                else:
                    print("   [SKIP] company_id 列已存在，跳过")
                
                print("\n4. 创建外键约束...")
                # 检查外键是否已存在
                result = conn.execute(text("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'user' 
                    AND constraint_name = 'fk_user_company_id'
                """))
                
                if result.fetchone() is None:
                    conn.execute(text("""
                        ALTER TABLE "user" 
                        ADD CONSTRAINT fk_user_company_id 
                        FOREIGN KEY (company_id) 
                        REFERENCES company(id) 
                        ON DELETE SET NULL
                    """))
                    print("   [OK] 外键约束创建成功")
                else:
                    print("   [SKIP] 外键约束已存在，跳过")
                
                print("\n5. 创建 company_id 索引...")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_user_company_id ON "user"(company_id)
                """))
                print("   [OK] 索引创建成功")
                
                # 提交事务
                trans.commit()
                
                print("\n" + "=" * 50)
                print("迁移执行成功！")
                print("=" * 50)
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"\n[ERROR] 迁移执行失败: {e}")
                raise
                
    except Exception as e:
        print(f"\n[ERROR] 连接数据库失败: {e}")
        print("\n请检查:")
        print("1. 数据库服务是否运行")
        print("2. 数据库连接配置是否正确")
        print("3. 是否有足够的权限执行 DDL 操作")
        print("4. 是否安装了 psycopg 或 psycopg2 模块")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()

