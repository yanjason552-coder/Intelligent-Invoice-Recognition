#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查任务日志 - 查看任务执行详情
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

def check_task_logs(task_id="0fd519c9-7716-42b2-8091-dae1cb3f535b"):
    """检查特定任务的详细信息"""
    
    print("=" * 80)
    print(f"检查任务详情: {task_id}")
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
        # 查询任务详情
        cur.execute("""
            SELECT 
                t.*,
                i.invoice_no,
                f.file_name,
                f.external_file_id,
                f.file_path,
                llm.name as config_name,
                llm.endpoint,
                llm.api_key,
                llm.app_type,
                llm.workflow_id
            FROM recognition_task t
            JOIN invoice i ON t.invoice_id = i.id
            JOIN invoice_file f ON i.file_id = f.id
            LEFT JOIN llm_config llm ON (t.params->>'model_config_id')::uuid = llm.id
            WHERE t.id = %s;
        """, (task_id,))
        
        task = cur.fetchone()
        
        if not task:
            print(f"[错误] 未找到任务: {task_id}")
            return
        
        print(f"\n任务基本信息:")
        print(f"  任务ID: {task['id']}")
        print(f"  任务编号: {task['task_no']}")
        print(f"  状态: {task['status']}")
        print(f"  创建时间: {task['create_time']}")
        print(f"  开始时间: {task['start_time']}")
        print(f"  结束时间: {task['end_time']}")
        if task['start_time']:
            elapsed = datetime.now() - task['start_time']
            print(f"  已运行时长: {elapsed}")
        print(f"  错误代码: {task['error_code']}")
        print(f"  错误消息: {task['error_message']}")
        
        print(f"\n文件信息:")
        print(f"  文件名: {task['file_name']}")
        print(f"  文件路径: {task['file_path']}")
        print(f"  external_file_id: {task['external_file_id']}")
        
        print(f"\n模型配置:")
        print(f"  配置名称: {task['config_name']}")
        print(f"  API端点: {task['endpoint']}")
        print(f"  API Key: {'*' * 20 if task['api_key'] else '未设置'}")
        print(f"  应用类型: {task['app_type']}")
        print(f"  工作流ID: {task['workflow_id']}")
        
        print(f"\n任务参数:")
        import json
        params = task['params']
        if params:
            print(json.dumps(params, ensure_ascii=False, indent=2))
        
        # 检查是否有识别结果
        cur.execute("""
            SELECT id, status, create_time
            FROM recognition_result
            WHERE task_id = %s;
        """, (task_id,))
        
        result = cur.fetchone()
        if result:
            print(f"\n识别结果:")
            print(f"  结果ID: {result['id']}")
            print(f"  状态: {result['status']}")
            print(f"  创建时间: {result['create_time']}")
        else:
            print(f"\n识别结果: 无")
        
        # 检查文件是否存在
        import os
        if task['file_path']:
            file_exists = os.path.exists(task['file_path'])
            print(f"\n文件检查:")
            print(f"  文件路径存在: {file_exists}")
            if file_exists:
                file_size = os.path.getsize(task['file_path'])
                print(f"  文件大小: {file_size} 字节")
        
    except Exception as e:
        print(f"\n[错误] 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    task_id = sys.argv[1] if len(sys.argv) > 1 else "0fd519c9-7716-42b2-8091-dae1cb3f535b"
    check_task_logs(task_id)

