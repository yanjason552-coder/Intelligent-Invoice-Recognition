#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控识别任务状态
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("[错误] 需要安装 psycopg2: pip install psycopg2-binary")
    sys.exit(1)

DB_HOST = "219.151.188.129"
DB_PORT = "50510"
DB_USER = "postgres"
DB_PASSWORD = "Post.&0055"
DB_NAME = "app"

def monitor_task(task_id=None, file_name="China SY inv 1.PDF", interval=5):
    """监控任务状态"""
    
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 如果没有提供task_id，通过文件名查找
        if not task_id:
            cur.execute("""
                SELECT t.id, t.task_no, t.status, t.start_time, t.error_code, t.error_message
                FROM recognition_task t
                JOIN invoice i ON t.invoice_id = i.id
                JOIN invoice_file f ON i.file_id = f.id
                WHERE f.file_name = %s
                ORDER BY t.create_time DESC
                LIMIT 1;
            """, (file_name,))
            task = cur.fetchone()
            if not task:
                print(f"[错误] 未找到文件 {file_name} 的任务")
                return
            task_id = task['id']
        
        print("=" * 80)
        print("实时监控识别任务")
        print("=" * 80)
        print(f"任务ID: {task_id}")
        print(f"监控间隔: {interval} 秒")
        print("按 Ctrl+C 停止监控")
        print("=" * 80)
        
        last_status = None
        start_time = None
        
        while True:
            cur.execute("""
                SELECT 
                    t.id, t.task_no, t.status, t.start_time, t.end_time,
                    t.error_code, t.error_message, t.create_time,
                    i.recognition_status,
                    f.external_file_id
                FROM recognition_task t
                LEFT JOIN invoice i ON t.invoice_id = i.id
                LEFT JOIN invoice_file f ON i.file_id = f.id
                WHERE t.id = %s;
            """, (task_id,))
            
            task = cur.fetchone()
            
            if not task:
                print(f"[错误] 任务不存在: {task_id}")
                break
            
            current_time = datetime.now()
            status = task['status']
            
            # 计算持续时间
            duration = None
            if task['start_time']:
                duration = (current_time - task['start_time']).total_seconds()
                if start_time is None:
                    start_time = task['start_time']
            
            # 状态变化时显示详细信息
            if status != last_status:
                print(f"\n[{current_time.strftime('%H:%M:%S')}] 状态变化: {last_status} -> {status}")
                last_status = status
            
            # 显示当前状态
            status_line = f"[{current_time.strftime('%H:%M:%S')}] 状态: {status}"
            if duration:
                status_line += f" | 持续时间: {duration:.1f}秒 ({duration/60:.1f}分钟)"
            if task['error_code']:
                status_line += f" | 错误: {task['error_code']}"
            if task['external_file_id']:
                status_line += f" | external_file_id: {task['external_file_id'][:20]}..."
            
            print(status_line, end='\r')
            
            # 如果任务完成或失败，停止监控
            if status in ['completed', 'failed']:
                print("\n")
                print("=" * 80)
                if status == 'completed':
                    print("✓ 任务已完成")
                else:
                    print("✗ 任务失败")
                    if task['error_code']:
                        print(f"错误代码: {task['error_code']}")
                    if task['error_message']:
                        print(f"错误消息: {task['error_message']}")
                print("=" * 80)
                break
            
            # 如果卡住超过5分钟，显示警告
            if duration and duration > 300:
                print(f"\n⚠️  任务已运行超过5分钟，可能已超时")
                print(f"   开始时间: {task['start_time']}")
                print(f"   当前时间: {current_time}")
                print(f"   持续时间: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")
                if not task['error_code']:
                    print(f"   建议: 查看后端日志了解卡住的具体位置")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n监控已停止")
    except Exception as e:
        print(f"\n[错误] 监控过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    task_id = sys.argv[1] if len(sys.argv) > 1 else None
    file_name = sys.argv[2] if len(sys.argv) > 2 else "China SY inv 1.PDF"
    monitor_task(task_id, file_name)

