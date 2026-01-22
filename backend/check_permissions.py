"""
检查权限表中的 resource 字段
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

def check_permissions():
    """检查权限表"""
    print("=" * 50)
    print("检查权限表中的 resource 字段")
    print("=" * 50)
    
    try:
        with engine.connect() as conn:
            # 检查有多少条记录的 resource 为 NULL
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM permission 
                WHERE resource IS NULL
            """))
            null_count = result.scalar()
            
            print(f"\nresource 为 NULL 的记录数: {null_count}")
            
            if null_count > 0:
                # 查看这些记录
                print("\n查看 resource 为 NULL 的记录:")
                result = conn.execute(text("""
                    SELECT id, name, code, resource, action, description
                    FROM permission 
                    WHERE resource IS NULL
                    LIMIT 10
                """))
                
                records = result.fetchall()
                for record in records:
                    print(f"  ID: {record[0]}, Name: {record[1]}, Code: {record[2]}, Resource: {record[3]}, Action: {record[4]}")
                
                # 检查是否可以基于 code 推断 resource
                print("\n尝试基于 code 推断 resource...")
                result = conn.execute(text("""
                    SELECT id, code, resource
                    FROM permission 
                    WHERE resource IS NULL
                """))
                
                records = result.fetchall()
                for record in records:
                    code = record[1]
                    # 尝试从 code 中提取 resource（假设格式为 resource:action）
                    if ':' in code:
                        resource = code.split(':')[0]
                        print(f"  Code: {code} -> Resource: {resource}")
                    else:
                        print(f"  Code: {code} -> 无法推断 resource")
                
    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_permissions()

