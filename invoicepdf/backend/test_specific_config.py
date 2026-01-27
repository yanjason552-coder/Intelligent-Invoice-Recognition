#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试特定模型配置的API调用
"""

import sys
import os
import json
import httpx
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

def test_config_api(file_name="China SY inv 1.PDF", config_name="API_V3_JsonSchema"):
    """测试特定模型配置的API调用"""
    
    print("=" * 80)
    print(f"测试模型配置: {config_name}")
    print(f"文件: {file_name}")
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
        
        if not file_record['external_file_id']:
            print("[错误] 文件缺少external_file_id，无法调用API")
            return
        
        # 2. 查找模型配置
        print(f"\n[2] 查找模型配置: {config_name}")
        cur.execute("""
            SELECT id, name, endpoint, api_key, app_type, workflow_id, is_active
            FROM llm_config
            WHERE name = %s;
        """, (config_name,))
        
        config = cur.fetchone()
        
        if not config:
            print(f"[错误] 未找到模型配置: {config_name}")
            return
        
        print(f"[2成功] 配置ID: {config['id']}")
        print(f"[2成功] API端点: {config['endpoint']}")
        print(f"[2成功] 应用类型: {config['app_type']}")
        print(f"[2成功] 工作流ID: {config['workflow_id']}")
        print(f"[2成功] 是否启用: {config['is_active']}")
        
        if not config['is_active']:
            print("[警告] 模型配置未启用")
        
        # 3. 查找该文件的任务，检查是否使用了这个配置
        print(f"\n[3] 查找文件的任务")
        cur.execute("""
            SELECT 
                t.id,
                t.status,
                t.params,
                t.create_time,
                llm.name as config_name
            FROM recognition_task t
            JOIN invoice i ON t.invoice_id = i.id
            JOIN invoice_file f ON i.file_id = f.id
            LEFT JOIN llm_config llm ON (t.params->>'model_config_id')::uuid = llm.id
            WHERE f.file_name = %s
            ORDER BY t.create_time DESC
            LIMIT 5;
        """, (file_name,))
        
        tasks = cur.fetchall()
        
        if tasks:
            print(f"[3成功] 找到 {len(tasks)} 个任务:")
            for idx, task in enumerate(tasks, 1):
                print(f"\n  任务 #{idx}:")
                print(f"    任务ID: {task['id']}")
                print(f"    状态: {task['status']}")
                print(f"    使用的配置: {task['config_name']}")
                print(f"    创建时间: {task['create_time']}")
        else:
            print("[3] 未找到任务")
        
        # 4. 查找Schema定义（如果配置需要）
        print(f"\n[4] 查找Schema定义")
        cur.execute("""
            SELECT id, name, schema_definition
            FROM output_schema
            ORDER BY create_time DESC
            LIMIT 5;
        """,)
        
        schemas = cur.fetchall()
        
        if schemas:
            print(f"[4成功] 找到 {len(schemas)} 个Schema:")
            for idx, schema in enumerate(schemas, 1):
                print(f"\n  Schema #{idx}:")
                print(f"    ID: {schema['id']}")
                print(f"    名称: {schema['name']}")
                if schema['schema_definition']:
                    if isinstance(schema['schema_definition'], dict):
                        print(f"    字段数: {len(schema['schema_definition'])}")
        else:
            print("[4] 未找到Schema定义")
        
        # 5. 构建并测试API调用
        print(f"\n[5] 构建API请求")
        endpoint = config['endpoint']
        api_key = config['api_key']
        external_file_id = file_record['external_file_id']
        
        endpoint_clean = endpoint.rstrip('/')
        url = f"{endpoint_clean}/workflows/run"
        
        inputs = {
            "InvoiceFile": {
                "transfer_method": "local_file",
                "type": "document",
                "upload_file_id": external_file_id
            }
        }
        
        # 如果有Schema，添加到inputs中
        # 根据配置名称判断使用哪个字段名
        config_name_lower = config_name.lower()
        schema_field_name = "JsonSchema" if "jsonschema" in config_name_lower else "OutputSchema"
        
        if schemas and len(schemas) > 0:
            schema_def = schemas[0]['schema_definition']
            if schema_def:
                # 如果字段名是JsonSchema，需要将schema转换为JSON字符串
                if schema_field_name == "JsonSchema":
                    if isinstance(schema_def, dict):
                        schema_value = json.dumps(schema_def, ensure_ascii=False)
                    elif isinstance(schema_def, str):
                        schema_value = schema_def
                    else:
                        schema_value = json.dumps(schema_def, ensure_ascii=False)
                    inputs[schema_field_name] = schema_value
                    print(f"[5] 已添加Schema: {schemas[0]['name']} (字段名: {schema_field_name}, 字符串格式)")
                else:
                    inputs[schema_field_name] = schema_def
                    print(f"[5] 已添加Schema: {schemas[0]['name']} (字段名: {schema_field_name})")
        else:
            # 如果配置需要JsonSchema但没有提供，记录警告
            if "jsonschema" in config_name_lower:
                print(f"[5警告] 配置 {config_name} 可能需要 JsonSchema，但未提供Schema定义")
        
        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": "user_test"
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"[5成功] URL: {url}")
        print(f"[5成功] 请求报文:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        
        # 6. 发送请求
        print(f"\n[6] 发送HTTP请求")
        print(f"[6] 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        
        start_time = datetime.now()
        
        try:
            with httpx.Client(timeout=300.0) as client:
                print(f"[6] 开始发送请求...")
                response = client.post(url, json=payload, headers=headers)
                elapsed_time = (datetime.now() - start_time).total_seconds()
                
                print(f"\n[6完成] 收到响应")
                print(f"[6完成] 耗时: {elapsed_time:.2f} 秒")
                print(f"[6完成] HTTP状态码: {response.status_code}")
                
                # 解析响应
                try:
                    response_json = response.json()
                    print(f"\n[6完成] 响应内容:")
                    print(json.dumps(response_json, ensure_ascii=False, indent=2)[:2000])
                    
                    # 检查工作流状态
                    if isinstance(response_json, dict):
                        data = response_json.get("data", {})
                        if isinstance(data, dict):
                            status = data.get("status")
                            if status:
                                print(f"\n工作流状态: {status}")
                                if status not in ("succeeded", "success", "completed"):
                                    error = data.get("error")
                                    print(f"错误信息: {error}")
                                    print(f"\n❌ API调用失败: 工作流状态为 {status}")
                                else:
                                    print(f"\n✅ API调用成功!")
                except:
                    print(f"\n[6完成] 响应文本: {response.text[:1000]}")
                
                if response.status_code == 200:
                    print("\n✓ HTTP请求成功")
                else:
                    print(f"\n✗ HTTP请求失败，状态码: {response.status_code}")
                    
        except httpx.TimeoutException:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            print(f"\n✗ 请求超时")
            print(f"   耗时: {elapsed_time:.2f} 秒")
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
    file_name = sys.argv[1] if len(sys.argv) > 1 else "China SY inv 1.PDF"
    config_name = sys.argv[2] if len(sys.argv) > 2 else "API_V3_JsonSchema"
    test_config_api(file_name, config_name)

