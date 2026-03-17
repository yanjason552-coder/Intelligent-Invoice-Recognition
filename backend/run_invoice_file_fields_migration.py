"""
执行 invoice_file 表字段迁移脚本
添加 model_name, template_name, template_version 三个字段
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """执行迁移脚本"""
    print("=" * 80)
    print("开始执行 invoice_file 表字段迁移")
    print("=" * 80)
    
    # 创建数据库连接
    database_url = str(settings.DATABASE_URL) if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL else str(settings.SQLALCHEMY_DATABASE_URI)
    db_info = database_url.split('@')[1] if '@' in database_url else '***'
    print(f"数据库连接: {db_info}")
    engine = create_engine(database_url)
    
    # 读取 SQL 文件
    sql_file = project_root / "add_invoice_file_model_template_fields.sql"
    if not sql_file.exists():
        print(f"错误: 找不到迁移脚本文件: {sql_file}")
        return False
    
    print(f"读取迁移脚本: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    try:
        with engine.connect() as conn:
            # 执行 SQL
            print("\n执行 SQL 语句...")
            conn.execute(text(sql_content))
            conn.commit()
            print("迁移成功完成！")
            print("\n已添加以下字段到 invoice_file 表:")
            print("  - model_name (VARCHAR(200))")
            print("  - template_name (VARCHAR(200))")
            print("  - template_version (VARCHAR(50))")
            return True
    except Exception as e:
        print(f"\n迁移失败: {str(e)}")
        print("\n错误详情:")
        import traceback
        traceback.print_exc()
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
