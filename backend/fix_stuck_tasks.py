#!/usr/bin/env python3
"""
修复卡住的识别任务脚本
"""

import sys
import os
sys.path.append('.')

from datetime import datetime, timedelta
from sqlalchemy import text
from app.core.db import SessionLocal

def fix_stuck_tasks():
    """修复卡住的任务"""

    print("=== 修复卡住的识别任务 ===")

    try:
        with SessionLocal() as session:
            # 查找所有processing状态的任务
            result = session.execute(text("""
                SELECT rt.id, rt.task_no, rt.create_time, rt.start_time,
                       EXTRACT(EPOCH FROM (NOW() - rt.create_time))/60 as minutes_elapsed
                FROM recognition_tasks rt
                WHERE rt.status = 'processing'
                ORDER BY rt.create_time DESC
            """))

            stuck_tasks = result.fetchall()

            if not stuck_tasks:
                print("✅ 没有发现卡住的任务")
                return

            print(f"发现 {len(stuck_tasks)} 个processing状态的任务:")

            fixed_count = 0
            for task in stuck_tasks:
                task_id, task_no, create_time, start_time, minutes_elapsed = task

                print(f"\n任务ID: {task_id}")
                print(f"任务编号: {task_no}")
                print(f"创建时间: {create_time}")
                print(f"开始时间: {start_time}")
                print(f"已运行: {minutes_elapsed:.1f}分钟")

                # 如果任务运行超过10分钟，认为是卡住了，重置为pending状态
                if minutes_elapsed > 10:
                    print("⚠️ 任务运行超过10分钟，重置为pending状态")

                    # 更新任务状态
                    session.execute(text("""
                        UPDATE recognition_tasks
                        SET status = 'pending',
                            start_time = NULL,
                            end_time = NULL,
                            error_code = NULL,
                            error_message = '任务被重置：运行时间过长'
                        WHERE id = :task_id
                    """), {"task_id": task_id})

                    fixed_count += 1
                else:
                    print("ℹ️ 任务仍在正常运行范围内")

            session.commit()

            if fixed_count > 0:
                print(f"\n✅ 成功修复 {fixed_count} 个卡住的任务")
                print("用户现在可以重新启动这些任务")
            else:
                print("\nℹ️ 没有需要修复的任务")

    except Exception as e:
        print(f"❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_stuck_tasks()
