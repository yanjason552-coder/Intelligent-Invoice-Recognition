"""
修复 company 表，添加缺失的列
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

def fix_table():
    """修复表结构"""
    print("=" * 50)
    print("修复 company 表结构")
    print("=" * 50)
    
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 需要添加的列
                columns_to_add = [
                    ('address', 'VARCHAR(500)'),
                    ('contact_person', 'VARCHAR(100)'),
                    ('contact_phone', 'VARCHAR(50)'),
                    ('contact_email', 'VARCHAR(100)'),
                ]
                
                print("\n检查并添加缺失的列...")
                
                for col_name, col_type in columns_to_add:
                    # 检查列是否已存在
                    result = conn.execute(text(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'company' 
                        AND column_name = '{col_name}'
                    """))
                    
                    if result.fetchone() is None:
                        print(f"  添加列: {col_name} ({col_type})...")
                        conn.execute(text(f"""
                            ALTER TABLE company 
                            ADD COLUMN {col_name} {col_type}
                        """))
                        print(f"  [OK] {col_name} 列添加成功")
                    else:
                        print(f"  [SKIP] {col_name} 列已存在，跳过")
                
                # 提交事务
                trans.commit()
                
                print("\n" + "=" * 50)
                print("表结构修复成功！")
                print("=" * 50)
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"\n[ERROR] 修复失败: {e}")
                import traceback
                traceback.print_exc()
                raise
                
    except Exception as e:
        print(f"\n[ERROR] 连接数据库失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    fix_table()

