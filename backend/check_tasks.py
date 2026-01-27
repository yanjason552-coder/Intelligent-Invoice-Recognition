#!/usr/bin/env python3
"""
检查识别任务状态的脚本
"""

import asyncio
from sqlmodel import select
from app.core.db import SessionLocal
from app.models.models_invoice import RecognitionTask, Invoice, InvoiceFile

async def check_tasks():
    with SessionLocal() as session:
        # 查询所有识别任务
        tasks = session.exec(
            select(RecognitionTask).order_by(RecognitionTask.create_time.desc()).limit(10)
        ).all()

        print('=== 最近10个识别任务 ===')
        for task in tasks:
            invoice = session.get(Invoice, task.invoice_id)
            file = session.get(InvoiceFile, invoice.file_id) if invoice else None

            print(f'任务ID: {task.id}')
            print(f'任务编号: {task.task_no}')
            print(f'状态: {task.status}')
            print(f'文件名: {file.file_name if file else "N/A"}')
            print(f'创建时间: {task.create_time}')
            print(f'开始时间: {task.start_time}')
            print(f'结束时间: {task.end_time}')
            print(f'耗时: {task.duration}秒' if task.duration else '耗时: N/A')
            print(f'错误信息: {task.error_message}' if task.error_message else '错误信息: 无')
            print('-' * 50)

        # 特别查找 China SY inv 3.pdf 文件
        print('\n=== 查找 China SY inv 3.pdf 文件 ===')
        china_tasks = session.exec(
            select(RecognitionTask)
            .join(Invoice, RecognitionTask.invoice_id == Invoice.id)
            .join(InvoiceFile, Invoice.file_id == InvoiceFile.id)
            .where(InvoiceFile.file_name.like('%China SY inv 3.pdf%'))
        ).all()

        if china_tasks:
            print(f'找到 {len(china_tasks)} 个相关任务:')
            for task in china_tasks:
                invoice = session.get(Invoice, task.invoice_id)
                file = session.get(InvoiceFile, invoice.file_id) if invoice else None

                print(f'任务ID: {task.id}')
                print(f'任务编号: {task.task_no}')
                print(f'状态: {task.status}')
                print(f'创建时间: {task.create_time}')
                print(f'开始时间: {task.start_time}')
                print(f'结束时间: {task.end_time}')
                print(f'错误信息: {task.error_message}' if task.error_message else '错误信息: 无')
        else:
            print('未找到 China SY inv 3.pdf 相关的任务')

if __name__ == "__main__":
    asyncio.run(check_tasks())
