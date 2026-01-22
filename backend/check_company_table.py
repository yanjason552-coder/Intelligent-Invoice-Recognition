"""
检查 company 表结构
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

from sqlalchemy import text, inspect
from app.core.db import engine

def check_table():
    """检查表结构"""
    print("=" * 50)
    print("检查 company 表结构")
    print("=" * 50)
    
    try:
        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'company'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("[ERROR] company 表不存在！")
                return
            
            print("[OK] company 表存在")
            
            # 检查所有列
            print("\n检查列...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'company'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print(f"\n找到 {len(columns)} 个列:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            # 检查需要的列
            required_columns = ['id', 'name', 'code', 'address', 'contact_person', 
                              'contact_phone', 'contact_email', 'description', 'is_active']
            existing_columns = [col[0] for col in columns]
            
            print("\n检查必需的列...")
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            if missing_columns:
                print(f"[ERROR] 缺少以下列: {', '.join(missing_columns)}")
                return missing_columns
            else:
                print("[OK] 所有必需的列都存在")
                
    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    check_table()

