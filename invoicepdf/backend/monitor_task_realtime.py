#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控任务执行情况
"""

import sys
import os
import time
from datetime import datetime

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

def monitor_task(file_name="China SY inv 3.pdf", interval=5):
    """实时监控任务执行情况"""
    
    print("=" * 80)
    print(f"实时监控任务: {file_name}")
    print("=" * 80)
    print("按 Ctrl+C 停止监控")
    print()
    
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        last_status = None
        check_count = 0
        
        while True:
            check_count += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 查找文件
            cur.execute("""
                SELECT id, file_name, external_file_id, upload_time
                FROM invoice_file
                WHERE file_name = %s
                ORDER BY upload_time DESC
                LIMIT 1;
            """, (file_name,))
            file_record = cur.fetchone()
            
            if not file_record:
                print(f"[{timestamp}] 检查 #{check_count}: 未找到文件记录")
                time.sleep(interval)
                continue
            
            # 查找任务
            cur.execute("""
                SELECT 
                    t.id,
                    t.status,
                    t.create_time,
                    t.start_time,
                    t.end_time,
                    t.error_code,
                    t.error_message,
                    i.invoice_no,
                    llm.name as config_name
                FROM recognition_task t
                JOIN invoice i ON t.invoice_id = i.id
                JOIN invoice_file f ON i.file_id = f.id
                LEFT JOIN llm_config llm ON (t.params->>'model_config_id')::uuid = llm.id
                WHERE f.file_name = %s
                ORDER BY t.create_time DESC
                LIMIT 1;
            """, (file_name,))
            
            task = cur.fetchone()
            
            if not task:
                print(f"[{timestamp}] 检查 #{check_count}: 文件已找到 (ID: {file_record['id']}), 但未找到任务")
                print(f"  external_file_id: {file_record['external_file_id']}")
                time.sleep(interval)
                continue
            
            # 检查状态变化
            status_changed = (last_status != task['status'])
            last_status = task['status']
            
            # 计算运行时长
            elapsed_str = ""
            if task['start_time']:
                elapsed = datetime.now() - task['start_time']
                elapsed_str = f", 已运行: {elapsed}"
            
            # 显示状态
            status_icon = {
                'pending': '⏳',
                'processing': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(task['status'], '❓')
            
            if status_changed or check_count == 1:
                print(f"\n[{timestamp}] 检查 #{check_count}")
                print(f"  任务ID: {task['id']}")
                print(f"  状态: {status_icon} {task['status']}")
                print(f"  创建时间: {task['create_time']}")
                if task['start_time']:
                    print(f"  开始时间: {task['start_time']}")
                if task['end_time']:
                    print(f"  结束时间: {task['end_time']}")
                print(f"  模型配置: {task['config_name']}")
                print(f"  external_file_id: {file_record['external_file_id']}")
                if task['error_code']:
                    print(f"  错误代码: {task['error_code']}")
                if task['error_message']:
                    print(f"  错误消息: {task['error_message']}")
                print(f"  {elapsed_str}")
            else:
                # 只显示状态和运行时长
                print(f"[{timestamp}] 状态: {status_icon} {task['status']}{elapsed_str}", end='\r')
            
            # 如果任务完成或失败，停止监控
            if task['status'] in ('completed', 'failed'):
                print(f"\n\n任务已结束: {task['status']}")
                if task['status'] == 'failed':
                    print(f"错误代码: {task['error_code']}")
                    print(f"错误消息: {task['error_message']}")
                break
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n监控已停止")
    except Exception as e:
        print(f"\n[错误] 监控失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    file_name = sys.argv[1] if len(sys.argv) > 1 else "China SY inv 3.pdf"
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    monitor_task(file_name, interval)

