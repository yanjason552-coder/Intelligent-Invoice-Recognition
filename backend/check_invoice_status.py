#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查询发票处理情况"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from app.core.config import settings

def check_invoice(invoice_no: str):
    """查询发票处理情况"""
    database_url = str(settings.DATABASE_URL) if settings.DATABASE_URL else str(settings.SQLALCHEMY_DATABASE_URI)
    engine = create_engine(database_url)
    conn = engine.connect()
    
    try:
        # 查询发票基本信息
        print("=" * 80)
        print(f"查询发票: {invoice_no}")
        print("=" * 80)
        
        invoice_result = conn.execute(
            text("""
                SELECT id, invoice_no, recognition_status, review_status, 
                       recognition_accuracy, create_time, file_id
                FROM invoice 
                WHERE invoice_no = :invoice_no
            """),
            {"invoice_no": invoice_no}
        )
        invoice = invoice_result.fetchone()
        
        if not invoice:
            print(f"[ERROR] 未找到发票: {invoice_no}")
            return
        
        invoice_id = invoice[0]
        print(f"\n[发票基本信息]")
        print(f"  ID: {invoice_id}")
        print(f"  发票编号: {invoice[1]}")
        print(f"  识别状态: {invoice[2]}")
        print(f"  审核状态: {invoice[3]}")
        print(f"  识别准确率: {invoice[4]}")
        print(f"  创建时间: {invoice[5]}")
        print(f"  文件ID: {invoice[6]}")
        
        # 查询识别任务
        print(f"\n[识别任务]")
        task_result = conn.execute(
            text("""
                SELECT id, task_no, status, start_time, end_time, duration, 
                       error_message, error_code, create_time
                FROM recognition_task 
                WHERE invoice_id = :invoice_id
                ORDER BY create_time DESC
            """),
            {"invoice_id": invoice_id}
        )
        tasks = task_result.fetchall()
        
        if tasks:
            for idx, task in enumerate(tasks, 1):
                print(f"\n  任务 {idx}:")
                print(f"    任务ID: {task[0]}")
                print(f"    任务编号: {task[1]}")
                print(f"    状态: {task[2]}")
                print(f"    开始时间: {task[3]}")
                print(f"    结束时间: {task[4]}")
                print(f"    耗时: {task[5]}秒" if task[5] else "    耗时: -")
                print(f"    错误代码: {task[7]}" if task[7] else "    错误代码: -")
                print(f"    错误信息: {task[6]}" if task[6] else "    错误信息: -")
                print(f"    创建时间: {task[8]}")
        else:
            print("  [WARNING] 没有找到识别任务")
        
        # 查询识别结果
        print(f"\n[识别结果]")
        result_result = conn.execute(
            text("""
                SELECT id, task_id, status, total_fields, recognized_fields, 
                       accuracy, confidence, recognition_time
                FROM recognition_result 
                WHERE invoice_id = :invoice_id
                ORDER BY recognition_time DESC
            """),
            {"invoice_id": invoice_id}
        )
        results = result_result.fetchall()
        
        if results:
            for idx, result in enumerate(results, 1):
                print(f"\n  结果 {idx}:")
                print(f"    结果ID: {result[0]}")
                print(f"    任务ID: {result[1]}")
                print(f"    状态: {result[2]}")
                print(f"    总字段数: {result[3]}")
                print(f"    已识别字段数: {result[4]}")
                print(f"    准确率: {result[5]}")
                print(f"    置信度: {result[6]}")
                print(f"    识别时间: {result[7]}")
        else:
            print("  [WARNING] 没有找到识别结果")
        
        # 查询审核记录
        print(f"\n[审核记录]")
        review_result = conn.execute(
            text("""
                SELECT id, review_status, review_comment, reviewer_id, review_time
                FROM review_record 
                WHERE invoice_id = :invoice_id
                ORDER BY review_time DESC
            """),
            {"invoice_id": invoice_id}
        )
        reviews = review_result.fetchall()
        
        if reviews:
            for idx, review in enumerate(reviews, 1):
                print(f"\n  审核记录 {idx}:")
                print(f"    记录ID: {review[0]}")
                print(f"    审核状态: {review[1]}")
                print(f"    审核意见: {review[2]}" if review[2] else "    审核意见: -")
                print(f"    审核人ID: {review[3]}")
                print(f"    审核时间: {review[4]}")
        else:
            print("  [WARNING] 没有找到审核记录")
        
        print("\n" + "=" * 80)
        
    finally:
        conn.close()

if __name__ == "__main__":
    invoice_no = "INV-20260204220829-47f7d8db"
    check_invoice(invoice_no)

