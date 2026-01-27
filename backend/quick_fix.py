#!/usr/bin/env python3
"""
快速修复卡住任务的脚本 - 内联版本
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def fix_stuck_tasks():
    """修复卡住的任务"""
    try:
        # 直接使用SQLAlchemy连接
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        # 数据库连接
        DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/invoice_db"
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        print("=== 修复卡住的识别任务 ===")

        with SessionLocal() as session:
            # 查找所有processing状态超过5分钟的任务
            result = session.execute(text("""
                UPDATE recognition_tasks
                SET status = 'pending',
                    start_time = NULL,
                    end_time = NULL,
                    error_code = NULL,
                    error_message = '任务被系统重置：可能由于Schema验证问题导致卡住'
                WHERE status = 'processing'
                AND start_time IS NOT NULL
                AND EXTRACT(EPOCH FROM (NOW() - start_time))/60 > 5
            """))

            updated_count = result.rowcount
            session.commit()

            print(f"✅ 成功重置 {updated_count} 个卡住的任务")

            if updated_count > 0:
                print("这些任务现在可以重新启动了")
            else:
                print("没有发现需要重置的任务")

    except Exception as e:
        print(f"❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_stuck_tasks()
