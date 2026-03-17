#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速修复 invoice_file 表缺失字段"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings

def main():
    print("=" * 80)
    print("修复 invoice_file 表缺失字段")
    print("=" * 80)
    
    # 获取数据库连接
    try:
        database_url = str(settings.DATABASE_URL) if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL else str(settings.SQLALCHEMY_DATABASE_URI)
    except:
        print("错误: 无法获取数据库配置")
        return False
    
    db_info = database_url.split('@')[1] if '@' in database_url else '***'
    print(f"数据库: {db_info}")
    
    # SQL 语句
    sql_statements = [
        "ALTER TABLE invoice_file ADD COLUMN IF NOT EXISTS model_name VARCHAR(200);",
        "ALTER TABLE invoice_file ADD COLUMN IF NOT EXISTS template_name VARCHAR(200);",
        "ALTER TABLE invoice_file ADD COLUMN IF NOT EXISTS template_version VARCHAR(50);",
    ]
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            for sql in sql_statements:
                print(f"执行: {sql[:50]}...")
                conn.execute(text(sql))
            conn.commit()
        print("\n✅ 字段添加成功！")
        print("已添加以下字段:")
        print("  - model_name")
        print("  - template_name")
        print("  - template_version")
        return True
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
