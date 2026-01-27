#!/usr/bin/env python3
"""
诊断识别任务状态的脚本
"""

import sys
import os
sys.path.append('.')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 数据库连接
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/invoice_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def diagnose_tasks():
    """诊断任务状态"""
    try:
        with SessionLocal() as session:
            # 查询所有识别任务
            result = session.execute(text("""
                SELECT
                    rt.id,
                    rt.task_no,
                    rt.status,
                    rt.create_time,
                    rt.start_time,
                    rt.end_time,
                    rt.error_code,
                    rt.error_message,
                    rt.duration,
                    i.file_id,
                    if.file_name,
                    if.external_file_id
                FROM recognition_tasks rt
                LEFT JOIN invoices i ON rt.invoice_id = i.id
                LEFT JOIN invoice_files if ON i.file_id = if.id
                ORDER BY rt.create_time DESC
                LIMIT 20
            """))

            tasks = result.fetchall()

            print("=== 最近20个识别任务状态 ===")
            for task in tasks:
                print(f"\n任务ID: {task[0]}")
                print(f"任务编号: {task[1]}")
                print(f"状态: {task[2]}")
                print(f"文件名: {task[9]}")
                print(f"外部文件ID: {task[10]}")
                print(f"创建时间: {task[3]}")
                print(f"开始时间: {task[4]}")
                print(f"结束时间: {task[5]}")
                print(f"耗时: {task[8]}秒" if task[8] else "耗时: N/A")
                if task[6]:  # error_code
                    print(f"错误代码: {task[6]}")
                if task[7]:  # error_message
                    print(f"错误信息: {task[7]}")
                print("-" * 50)

            # 查找特定的China SY inv 3.pdf文件
            print("\n=== 查找 China SY inv 3.pdf 相关任务 ===")
            result = session.execute(text("""
                SELECT
                    rt.id,
                    rt.task_no,
                    rt.status,
                    rt.create_time,
                    rt.start_time,
                    rt.end_time,
                    rt.error_code,
                    rt.error_message,
                    if.file_name
                FROM recognition_tasks rt
                LEFT JOIN invoices i ON rt.invoice_id = i.id
                LEFT JOIN invoice_files if ON i.file_id = if.id
                WHERE if.file_name LIKE '%China SY inv 3.pdf%'
                ORDER BY rt.create_time DESC
            """))

            china_tasks = result.fetchall()

            if china_tasks:
                print(f"找到 {len(china_tasks)} 个相关任务:")
                for task in china_tasks:
                    print(f"\n任务ID: {task[0]}")
                    print(f"任务编号: {task[1]}")
                    print(f"状态: {task[2]}")
                    print(f"文件名: {task[8]}")
                    print(f"创建时间: {task[3]}")
                    print(f"开始时间: {task[4]}")
                    print(f"结束时间: {task[5]}")
                    if task[6]:  # error_code
                        print(f"错误代码: {task[6]}")
                    if task[7]:  # error_message
                        print(f"错误信息: {task[7]}")
            else:
                print("未找到 China SY inv 3.pdf 相关的任务")

            # 检查是否有长时间运行的任务
            print("\n=== 检查长时间运行的任务（超过5分钟）===")
            result = session.execute(text("""
                SELECT
                    rt.id,
                    rt.task_no,
                    rt.status,
                    rt.create_time,
                    rt.start_time,
                    EXTRACT(EPOCH FROM (NOW() - rt.create_time))/60 as minutes_elapsed,
                    if.file_name
                FROM recognition_tasks rt
                LEFT JOIN invoices i ON rt.invoice_id = i.id
                LEFT JOIN invoice_files if ON i.file_id = if.id
                WHERE rt.status IN ('pending', 'processing')
                AND EXTRACT(EPOCH FROM (NOW() - rt.create_time))/60 > 5
                ORDER BY rt.create_time DESC
            """))

            long_running = result.fetchall()

            if long_running:
                print(f"找到 {len(long_running)} 个长时间运行的任务:")
                for task in long_running:
                    print(f"任务ID: {task[0]}, 状态: {task[2]}, 已运行: {task[5]:.1f}分钟, 文件: {task[6]}")
            else:
                print("没有发现长时间运行的任务")

    except Exception as e:
        print(f"诊断出错: {str(e)}")

if __name__ == "__main__":
    diagnose_tasks()
