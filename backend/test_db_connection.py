#!/usr/bin/env python3
"""
测试数据库连接
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_db_connection():
    """测试数据库连接"""
    try:
        from app.core.db import engine
        from sqlalchemy import text
        from sqlmodel import Session

        print("=== 测试数据库连接 ===")

        with Session(engine) as session:
            # 测试基本查询
            result = session.exec(text("SELECT 1 as test")).one()
            print(f"[OK] 基本查询成功: {result}")

            # 测试数据库版本
            version_result = session.exec(text("SELECT version()")).first()
            print(f"[OK] 数据库版本: {str(version_result)[:50]}...")

            # 测试表查询
            try:
                user_count = session.exec(text("SELECT COUNT(*) FROM users")).first()
                print(f"[OK] 用户表查询成功: {user_count} 个用户")
            except Exception as e:
                print(f"[WARN] 用户表查询失败: {e}")

            try:
                invoice_count = session.exec(text("SELECT COUNT(*) FROM invoices")).first()
                print(f"[OK] 发票表查询成功: {invoice_count} 个发票")
            except Exception as e:
                print(f"[WARN] 发票表查询失败: {e}")

        print("[OK] 数据库连接正常")

    except Exception as e:
        print(f"[FAIL] 数据库连接失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_connection()
