#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试API调用 - 模拟识别流程
用于验证API调用是否能到达DIFY平台
"""

import sys
import os
import json
import httpx
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

def test_api_call_directly(file_name="China SY inv 3.pdf"):
    """直接测试API调用"""
    
    print("=" * 80)
    print("直接测试 DIFY API 调用")
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
            SELECT id, file_name, external_file_id, file_path
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
        
        if not file_record['external_file_id']:
            print("[错误] 文件缺少external_file_id")
            return
        
        # 2. 查找任务和模型配置
        print(f"\n[2] 查找任务和模型配置")
        cur.execute("""
            SELECT 
                t.id as task_id,
                t.params,
                t.operator_id,
                llm.id as config_id,
                llm.name as config_name,
                llm.endpoint,
                llm.api_key,
                llm.app_type,
                llm.workflow_id
            FROM recognition_task t
            JOIN invoice i ON t.invoice_id = i.id
            JOIN invoice_file f ON i.file_id = f.id
            JOIN llm_config llm ON (t.params->>'model_config_id')::uuid = llm.id
            WHERE f.file_name = %s
            ORDER BY t.create_time DESC
            LIMIT 1;
        """, (file_name,))
        
        task_config = cur.fetchone()
        
        if not task_config:
            print("[错误] 未找到任务或模型配置")
            return
        
        print(f"[2成功] 任务ID: {task_config['task_id']}")
        print(f"[2成功] 模型配置: {task_config['config_name']}")
        print(f"[2成功] API端点: {task_config['endpoint']}")
        
        # 3. 获取schema定义
        schema_definition = None
        params = task_config['params']
        if params and params.get("output_schema_id"):
            print(f"\n[3] 查找Schema定义")
            schema_id = params.get("output_schema_id")
            cur.execute("""
                SELECT schema_definition
                FROM output_schema
                WHERE id = %s;
            """, (schema_id,))
            schema = cur.fetchone()
            if schema and schema['schema_definition']:
                schema_definition = schema['schema_definition']
                print(f"[3成功] 找到Schema定义，字段数: {len(schema_definition) if isinstance(schema_definition, dict) else 'N/A'}")
        
        # 4. 构建请求
        print(f"\n[4] 构建API请求")
        endpoint = task_config['endpoint']
        api_key = task_config['api_key']
        external_file_id = file_record['external_file_id']
        user_id = f"user_{task_config['operator_id']}"
        
        endpoint_clean = endpoint.rstrip('/')
        url = f"{endpoint_clean}/workflows/run"
        
        inputs = {
            "InvoiceFile": {
                "transfer_method": "local_file",
                "type": "document",  # PDF文件
                "upload_file_id": external_file_id
            }
        }
        
        if schema_definition:
            inputs["OutputSchema"] = schema_definition
        
        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": user_id
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"[4成功] URL: {url}")
        print(f"[4成功] 请求报文:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        
        # 5. 发送请求
        print(f"\n[5] 发送HTTP请求")
        print(f"[5] 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        print(f"[5] 目标: {url}")
        
        start_time = datetime.now()
        
        try:
            with httpx.Client(timeout=300.0) as client:
                print(f"[5] 开始发送请求...")
                response = client.post(url, json=payload, headers=headers)
                elapsed_time = (datetime.now() - start_time).total_seconds()
                
                print(f"\n[5完成] 收到响应")
                print(f"[5完成] 耗时: {elapsed_time:.2f} 秒")
                print(f"[5完成] HTTP状态码: {response.status_code}")
                print(f"[5完成] 响应头: {dict(response.headers)}")
                
                # 尝试解析响应
                try:
                    response_json = response.json()
                    print(f"\n[5完成] 响应内容:")
                    print(json.dumps(response_json, ensure_ascii=False, indent=2)[:2000])
                except:
                    print(f"\n[5完成] 响应文本: {response.text[:1000]}")
                
                if response.status_code == 200:
                    print("\n✓ API调用成功！")
                else:
                    print(f"\n✗ API调用失败，HTTP状态码: {response.status_code}")
                    
        except httpx.TimeoutException:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            print(f"\n✗ 请求超时")
            print(f"   耗时: {elapsed_time:.2f} 秒")
            print(f"   超时设置: 300秒")
        except httpx.HTTPStatusError as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            print(f"\n✗ HTTP错误")
            print(f"   状态码: {e.response.status_code}")
            print(f"   耗时: {elapsed_time:.2f} 秒")
            print(f"   响应: {e.response.text[:500]}")
        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            print(f"\n✗ 请求异常")
            print(f"   异常类型: {type(e).__name__}")
            print(f"   异常消息: {str(e)}")
            print(f"   耗时: {elapsed_time:.2f} 秒")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"\n[错误] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    file_name = sys.argv[1] if len(sys.argv) > 1 else "China SY inv 3.pdf"
    test_api_call_directly(file_name)

