#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查任务执行情况 - 查看任务状态和日志
"""

import sys
import os
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

def check_task_execution(file_name="China SY inv 3.pdf"):
    """检查任务执行情况"""
    
    print("=" * 80)
    print("检查任务执行情况")
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
        # 1. 查找文件
        print(f"\n[1] 查找文件: {file_name}")
        cur.execute("""
            SELECT id, file_name, external_file_id, upload_time
            FROM invoice_file
            WHERE file_name = %s
            ORDER BY upload_time DESC
            LIMIT 1;
        """, (file_name,))
        file_record = cur.fetchone()
        
        if not file_record:
            print(f"[错误] 未找到文件: {file_name}")
            return
        
        print(f"[1成功] 文件ID: {file_record['id']}")
        print(f"[1成功] external_file_id: {file_record['external_file_id']}")
        
        # 2. 查找发票和任务
        print(f"\n[2] 查找发票和任务")
        cur.execute("""
            SELECT 
                i.id as invoice_id,
                i.invoice_no,
                t.id as task_id,
                t.status,
                t.params,
                t.create_time,
                t.start_time,
                t.end_time,
                t.error_code,
                t.error_message,
                t.operator_id
            FROM invoice i
            JOIN invoice_file f ON i.file_id = f.id
            LEFT JOIN recognition_task t ON t.invoice_id = i.id
            WHERE f.file_name = %s
            ORDER BY t.create_time DESC NULLS LAST
            LIMIT 5;
        """, (file_name,))
        
        tasks = cur.fetchall()
        
        if not tasks:
            print("[错误] 未找到发票或任务")
            return
        
        print(f"[2成功] 找到 {len(tasks)} 个任务记录")
        
        for idx, task in enumerate(tasks, 1):
            print(f"\n--- 任务 #{idx} ---")
            print(f"任务ID: {task['task_id']}")
            print(f"发票ID: {task['invoice_id']}")
            print(f"发票编号: {task['invoice_no']}")
            print(f"状态: {task['status']}")
            print(f"创建时间: {task['create_time']}")
            print(f"开始时间: {task['start_time']}")
            print(f"结束时间: {task['end_time']}")
            if task['error_code']:
                print(f"错误代码: {task['error_code']}")
            if task['error_message']:
                print(f"错误消息: {task['error_message']}")
            
            # 检查任务参数
            if task['params']:
                params = task['params']
                print(f"\n任务参数:")
                print(f"  model_config_id: {params.get('model_config_id')}")
                print(f"  output_schema_id: {params.get('output_schema_id')}")
            
            # 检查是否有识别结果
            if task['task_id']:
                cur.execute("""
                    SELECT id, raw_data, normalized_fields, create_time
                    FROM recognition_result
                    WHERE task_id = %s
                    ORDER BY create_time DESC
                    LIMIT 1;
                """, (task['task_id'],))
                result = cur.fetchone()
                if result:
                    print(f"\n识别结果:")
                    print(f"  结果ID: {result['id']}")
                    print(f"  创建时间: {result['create_time']}")
                    if result['raw_data']:
                        import json
                        result_data = result['raw_data']
                        if isinstance(result_data, dict):
                            print(f"  原始数据字段数: {len(result_data)}")
                            print(f"  主要字段: {list(result_data.keys())[:5]}")
                    if result['normalized_fields']:
                        normalized = result['normalized_fields']
                        if isinstance(normalized, dict):
                            print(f"  标准化字段数: {len(normalized)}")
                else:
                    print(f"\n识别结果: 无")
        
        # 3. 检查最近的processing状态任务
        print(f"\n[3] 检查最近的processing状态任务")
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
                print(f"  - 任务ID: {task['id']}")
                print(f"    文件名: {task['file_name']}")
                print(f"    创建时间: {task['create_time']}")
                print(f"    开始时间: {task['start_time']}")
                print(f"    模型配置: {task['config_name']}")
                print(f"    API端点: {task['endpoint']}")
                print()
        else:
            print("[3] 没有找到processing状态的任务")
        
        # 4. 检查是否有失败的最近任务
        print(f"\n[4] 检查最近的失败任务")
        cur.execute("""
            SELECT 
                t.id,
                t.status,
                t.error_code,
                t.error_message,
                t.create_time,
                t.start_time,
                t.end_time,
                f.file_name
            FROM recognition_task t
            JOIN invoice i ON t.invoice_id = i.id
            JOIN invoice_file f ON i.file_id = f.id
            WHERE t.status = 'failed'
            ORDER BY t.end_time DESC NULLS LAST, t.create_time DESC
            LIMIT 5;
        """)
        
        failed_tasks = cur.fetchall()
        
        if failed_tasks:
            print(f"[4] 找到 {len(failed_tasks)} 个失败的任务:")
            for task in failed_tasks:
                print(f"  - 任务ID: {task['id']}")
                print(f"    文件名: {task['file_name']}")
                print(f"    错误代码: {task['error_code']}")
                print(f"    错误消息: {task['error_message']}")
                print(f"    创建时间: {task['create_time']}")
                print(f"    开始时间: {task['start_time']}")
                print(f"    结束时间: {task['end_time']}")
                print()
        else:
            print("[4] 没有找到失败的任务")
        
    except Exception as e:
        print(f"\n[错误] 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    file_name = sys.argv[1] if len(sys.argv) > 1 else "China SY inv 3.pdf"
    check_task_execution(file_name)

