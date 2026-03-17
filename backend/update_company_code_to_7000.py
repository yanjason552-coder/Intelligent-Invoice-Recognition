"""
更新 invoice_file 和 invoice 表中的公司代码字段为 7000
如果字段不存在，先添加字段，然后更新所有行
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from app.core.db import engine
from app.core.config import settings

def update_company_code():
    """更新两个表中的公司代码字段为 7000"""
    
    with engine.connect() as conn:
        # 开始事务
        trans = conn.begin()
        
        try:
            # ============================================
            # 1. 处理 invoice_file 表
            # ============================================
            print("=" * 60)
            print("处理 invoice_file 表...")
            print("=" * 60)
            
            # 检查表是否存在 company_code 字段
            inspector = inspect(engine)
            invoice_file_columns = [col['name'] for col in inspector.get_columns('invoice_file')]
            
            if 'company_code' not in invoice_file_columns:
                print("invoice_file 表没有 company_code 字段，正在添加...")
                conn.execute(text("ALTER TABLE invoice_file ADD COLUMN company_code VARCHAR(50)"))
                conn.commit()
                trans = conn.begin()  # 重新开始事务
                print("✅ 已添加 company_code 字段到 invoice_file 表")
            else:
                print("✅ invoice_file 表已存在 company_code 字段")
            
            # 更新所有行的 company_code 为 7000
            result = conn.execute(
                text("UPDATE invoice_file SET company_code = '7000' WHERE company_code IS NULL OR company_code != '7000'")
            )
            updated_count = result.rowcount
            print(f"✅ invoice_file 表已更新 {updated_count} 行，company_code 设置为 7000")
            
            # ============================================
            # 2. 处理 invoice 表
            # ============================================
            print("\n" + "=" * 60)
            print("处理 invoice 表...")
            print("=" * 60)
            
            # 检查表是否存在 company_code 字段
            invoice_columns = [col['name'] for col in inspector.get_columns('invoice')]
            
            if 'company_code' not in invoice_columns:
                print("invoice 表没有 company_code 字段，正在添加...")
                conn.execute(text("ALTER TABLE invoice ADD COLUMN company_code VARCHAR(50)"))
                conn.commit()
                trans = conn.begin()  # 重新开始事务
                print("✅ 已添加 company_code 字段到 invoice 表")
            else:
                print("✅ invoice 表已存在 company_code 字段")
            
            # 更新所有行的 company_code 为 7000
            result = conn.execute(
                text("UPDATE invoice SET company_code = '7000' WHERE company_code IS NULL OR company_code != '7000'")
            )
            updated_count = result.rowcount
            print(f"✅ invoice 表已更新 {updated_count} 行，company_code 设置为 7000")
            
            # 提交事务
            trans.commit()
            print("\n" + "=" * 60)
            print("✅ 所有更新已完成并提交")
            print("=" * 60)
            
            # ============================================
            # 3. 验证更新结果
            # ============================================
            print("\n" + "=" * 60)
            print("验证更新结果...")
            print("=" * 60)
            
            # 查询 invoice_file 表统计
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(company_code) as rows_with_company_code,
                    COUNT(CASE WHEN company_code = '7000' THEN 1 END) as rows_with_7000
                FROM invoice_file
            """))
            row = result.fetchone()
            print(f"\ninvoice_file 表:")
            print(f"  总行数: {row[0]}")
            print(f"  有 company_code 的行数: {row[1]}")
            print(f"  company_code = '7000' 的行数: {row[2]}")
            
            # 查询 invoice 表统计
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(company_code) as rows_with_company_code,
                    COUNT(CASE WHEN company_code = '7000' THEN 1 END) as rows_with_7000
                FROM invoice
            """))
            row = result.fetchone()
            print(f"\ninvoice 表:")
            print(f"  总行数: {row[0]}")
            print(f"  有 company_code 的行数: {row[1]}")
            print(f"  company_code = '7000' 的行数: {row[2]}")
            
        except Exception as e:
            # 回滚事务
            trans.rollback()
            print(f"\n❌ 更新失败: {str(e)}")
            raise
        finally:
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("开始更新公司代码字段为 7000")
    print("=" * 60)
    print(f"数据库: {settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}")
    print()
    
    try:
        update_company_code()
        print("\n✅ 脚本执行成功！")
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {str(e)}")
        sys.exit(1)

