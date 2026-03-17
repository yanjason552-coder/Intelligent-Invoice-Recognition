#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控发票识别任务
使用方法：
  python monitor_invoice_recognition.py [task_id] [interval]
  或
  python monitor_invoice_recognition.py [file_name] [interval]
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from sqlmodel import Session, select, func
from backend.app.core.db import engine
from backend.app.models.models_invoice import RecognitionTask, Invoice, InvoiceFile

def monitor_latest_task(interval=5):
    """监控最新的识别任务"""
    print("=" * 80)
    print("实时监控发票识别任务")
    print("=" * 80)
    print(f"监控间隔: {interval} 秒")
    print("按 Ctrl+C 停止监控")
    print("=" * 80)
    print()
    
    try:
        last_status = None
        task_id = None
        
        while True:
            with Session(engine) as session:
                # 查找最新的任务
                if not task_id:
                    # 查找最新的processing或pending任务
                    latest_task = session.exec(
                        select(RecognitionTask)
                        .where(RecognitionTask.status.in_(["pending", "processing"]))
                        .order_by(RecognitionTask.create_time.desc())
                        .limit(1)
                    ).first()
                    
                    if not latest_task:
                        # 如果没有处理中的任务，查找最新的任务
                        latest_task = session.exec(
                            select(RecognitionTask)
                            .order_by(RecognitionTask.create_time.desc())
                            .limit(1)
                        ).first()
                    
                    if latest_task:
                        task_id = latest_task.id
                        print(f"找到任务: {latest_task.task_no}")
                        print(f"任务ID: {task_id}")
                        print(f"状态: {latest_task.status}")
                        print()
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 未找到任务，等待中...", end='\r')
                        time.sleep(interval)
                        continue
                
                # 查询任务详情
                task = session.get(RecognitionTask, task_id)
                if not task:
                    print(f"[错误] 任务不存在: {task_id}")
                    task_id = None
                    time.sleep(interval)
                    continue
                
                # 获取发票和文件信息
                invoice = session.get(Invoice, task.invoice_id)
                file_info = None
                if invoice:
                    file_info = session.get(InvoiceFile, invoice.file_id)
                
                current_time = datetime.now()
                status = task.status
                
                # 计算持续时间
                duration_str = ""
                if task.start_time:
                    duration = (current_time - task.start_time).total_seconds()
                    duration_str = f" | 已运行: {duration:.1f}秒 ({duration/60:.1f}分钟)"
                
                # 状态变化时显示详细信息
                if status != last_status:
                    print(f"\n[{current_time.strftime('%H:%M:%S')}] {'='*60}")
                    print(f"状态变化: {last_status or 'N/A'} -> {status}")
                    print(f"任务编号: {task.task_no}")
                    if file_info:
                        print(f"文件名: {file_info.file_name}")
                    if task.start_time:
                        print(f"开始时间: {task.start_time}")
                    if task.error_code:
                        print(f"错误代码: {task.error_code}")
                    if task.error_message:
                        print(f"错误消息: {task.error_message[:100]}")
                    print(f"{'='*60}")
                    last_status = status
                
                # 显示当前状态
                status_icon = {
                    'pending': '⏳',
                    'processing': '🔄',
                    'completed': '✅',
                    'failed': '❌'
                }.get(status, '❓')
                
                status_line = f"[{current_time.strftime('%H:%M:%S')}] {status_icon} 状态: {status}{duration_str}"
                if task.error_code:
                    status_line += f" | 错误: {task.error_code}"
                
                print(status_line, end='\r')
                
                # 如果任务完成或失败，显示结果并继续监控下一个任务
                if status in ['completed', 'failed']:
                    print("\n")
                    print("=" * 80)
                    if status == 'completed':
                        print("✓ 任务已完成")
                        if task.end_time and task.start_time:
                            total_duration = (task.end_time - task.start_time).total_seconds()
                            print(f"总耗时: {total_duration:.2f} 秒 ({total_duration/60:.1f} 分钟)")
                    else:
                        print("✗ 任务失败")
                        if task.error_code:
                            print(f"错误代码: {task.error_code}")
                        if task.error_message:
                            print(f"错误消息: {task.error_message}")
                    print("=" * 80)
                    print("\n继续监控下一个任务...\n")
                    task_id = None
                    last_status = None
                    time.sleep(interval)
                    continue
                
                # 如果卡住超过5分钟，显示警告
                if task.start_time:
                    duration = (current_time - task.start_time).total_seconds()
                    if duration > 300:
                        print(f"\n⚠️  警告: 任务已运行超过5分钟 ({duration/60:.1f} 分钟)")
                        print(f"   建议: 查看后端日志了解详细情况")
                
                time.sleep(interval)
                
    except KeyboardInterrupt:
        print("\n\n监控已停止")
    except Exception as e:
        print(f"\n[错误] 监控过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    monitor_latest_task(interval)

