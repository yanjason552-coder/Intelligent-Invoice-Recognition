#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查最近的任务执行情况
"""

import sys
import os
from datetime import datetime, timedelta

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

def check_recent_tasks():
    """检查最近的任务"""
    
    print("=" * 80)
    print("检查最近的任务执行情况")
    print("=" * 80)
    
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. 查找包含 "China SY inv" 的文件
        print(f"\n[1] 查找包含 'China SY inv' 的文件")
        cur.execute("""
            SELECT id, file_name, external_file_id, upload_time
            FROM invoice_file
            WHERE file_name LIKE %s
            ORDER BY upload_time DESC
            LIMIT 10;
        """, ('%China SY inv%',))
        
        files = cur.fetchall()
        
        if files:
            print(f"[1成功] 找到 {len(files)} 个文件:")
            for f in files:
                print(f"  - {f['file_name']} (ID: {f['id']}, external_file_id: {f['external_file_id']})")
        else:
            print("[1] 未找到匹配的文件")
        
        # 2. 查找最近1小时内的任务
        print(f"\n[2] 查找最近1小时内的任务")
        one_hour_ago = datetime.now() - timedelta(hours=1)
        cur.execute("""
            SELECT 
                t.id,
                t.status,
                t.create_time,
                t.start_time,
                t.end_time,
                t.error_code,
                t.error_message,
                f.file_name,
                llm.name as config_name,
                llm.endpoint
            FROM recognition_task t
            JOIN invoice i ON t.invoice_id = i.id
            JOIN invoice_file f ON i.file_id = f.id
            LEFT JOIN llm_config llm ON (t.params->>'model_config_id')::uuid = llm.id
            WHERE t.create_time >= %s
            ORDER BY t.create_time DESC
            LIMIT 20;
        """, (one_hour_ago,))
        
        tasks = cur.fetchall()
        
        if tasks:
            print(f"[2成功] 找到 {len(tasks)} 个最近的任务:")
            for task in tasks:
                print(f"\n  --- 任务: {task['id']} ---")
                print(f"  文件名: {task['file_name']}")
                print(f"  状态: {task['status']}")
                print(f"  创建时间: {task['create_time']}")
                print(f"  开始时间: {task['start_time']}")
                print(f"  结束时间: {task['end_time']}")
                if task['error_code']:
                    print(f"  错误代码: {task['error_code']}")
                if task['error_message']:
                    print(f"  错误消息: {task['error_message']}")
                print(f"  模型配置: {task['config_name']}")
                print(f"  API端点: {task['endpoint']}")
        else:
            print("[2] 未找到最近1小时内的任务")
        
        # 3. 查找所有processing状态的任务
        print(f"\n[3] 查找所有processing状态的任务")
        cur.execute("""
            SELECT 
                t.id,
                t.status,
                t.create_time,
                t.start_time,
                f.file_name,
                llm.name as config_name,
                llm.endpoint
            FROM recognition_task t
            JOIN invoice i ON t.invoice_id = i.id
            JOIN invoice_file f ON i.file_id = f.id
            LEFT JOIN llm_config llm ON (t.params->>'model_config_id')::uuid = llm.id
            WHERE t.status = 'processing'
            ORDER BY t.start_time DESC NULLS LAST, t.create_time DESC
            LIMIT 10;
        """)
        
        processing_tasks = cur.fetchall()
        
        if processing_tasks:
            print(f"[3] 找到 {len(processing_tasks)} 个processing状态的任务:")
            for task in processing_tasks:
                print(f"\n  --- 任务: {task['id']} ---")
                print(f"  文件名: {task['file_name']}")
                print(f"  创建时间: {task['create_time']}")
                print(f"  开始时间: {task['start_time']}")
                if task['start_time']:
                    elapsed = datetime.now() - task['start_time']
                    print(f"  已运行时长: {elapsed}")
                print(f"  模型配置: {task['config_name']}")
                print(f"  API端点: {task['endpoint']}")
        else:
            print("[3] 没有找到processing状态的任务")
        
    except Exception as e:
        print(f"\n[错误] 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_recent_tasks()

