"""
修复权限表中的 resource 字段
从 code 字段推断 resource（格式：resource:action）
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

def fix_permissions():
    """修复权限表的 resource 字段"""
    print("=" * 50)
    print("修复权限表中的 resource 字段")
    print("=" * 50)
    
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 获取所有 resource 为 NULL 的记录
                result = conn.execute(text("""
                    SELECT id, code, resource
                    FROM permission 
                    WHERE resource IS NULL
                """))
                
                records = result.fetchall()
                print(f"\n找到 {len(records)} 条需要修复的记录")
                
                updated_count = 0
                failed_count = 0
                
                for record in records:
                    permission_id = record[0]
                    code = record[1]
                    
                    # 从 code 中提取 resource
                    if ':' in code:
                        resource = code.split(':')[0]
                        
                        # 特殊处理 menu 类型的 code（格式为 menu:/path）
                        if code.startswith('menu:'):
                            resource = 'menu'
                        
                        # 更新记录
                        try:
                            conn.execute(text("""
                                UPDATE permission 
                                SET resource = :resource
                                WHERE id = :id
                            """), {"resource": resource, "id": permission_id})
                            updated_count += 1
                            print(f"  [OK] {code} -> resource: {resource}")
                        except Exception as e:
                            failed_count += 1
                            print(f"  [ERROR] 更新失败 {code}: {e}")
                    else:
                        # 如果无法从 code 推断，使用默认值
                        resource = 'unknown'
                        try:
                            conn.execute(text("""
                                UPDATE permission 
                                SET resource = :resource
                                WHERE id = :id
                            """), {"resource": resource, "id": permission_id})
                            updated_count += 1
                            print(f"  [WARN] {code} -> resource: {resource} (无法推断，使用默认值)")
                        except Exception as e:
                            failed_count += 1
                            print(f"  [ERROR] 更新失败 {code}: {e}")
                
                # 提交事务
                trans.commit()
                
                print("\n" + "=" * 50)
                print(f"修复完成！")
                print(f"  成功更新: {updated_count} 条")
                print(f"  失败: {failed_count} 条")
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
    fix_permissions()

