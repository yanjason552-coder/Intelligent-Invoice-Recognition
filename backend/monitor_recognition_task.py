#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""监控识别任务的处理过程"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings

def monitor_latest_task():
    """监控最新的识别任务"""
    try:
        database_url = str(settings.DATABASE_URL) if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL else str(settings.SQLALCHEMY_DATABASE_URI)
    except Exception as e:
        print(f"错误: 无法获取数据库配置: {e}")
        return
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # 查询最新的识别任务
            print("=" * 80)
            print("查询最新的识别任务...")
            print("=" * 80)
            
            task_result = conn.execute(
                text("""
                    SELECT id, task_no, invoice_id, status, start_time, end_time, 
                           error_code, error_message, create_time
                    FROM recognition_task
                    ORDER BY create_time DESC
                    LIMIT 5
                """)
            )
            tasks = task_result.fetchall()
            
            if not tasks:
                print("没有找到识别任务")
                return
            
            print(f"\n找到 {len(tasks)} 个最新任务:\n")
            
            for i, task in enumerate(tasks, 1):
                task_id, task_no, invoice_id, status, start_time, end_time, error_code, error_message, create_time = task
                print(f"[任务 {i}]")
                print(f"  任务ID: {task_id}")
                print(f"  任务编号: {task_no}")
                print(f"  发票ID: {invoice_id}")
                print(f"  状态: {status}")
                print(f"  开始时间: {start_time}")
                print(f"  结束时间: {end_time}")
                print(f"  创建时间: {create_time}")
                if error_code:
                    print(f"  错误代码: {error_code}")
                if error_message:
                    print(f"  错误消息: {error_message[:200]}...")
                print()
                
                # 查询对应的识别结果
                if invoice_id:
                    result_result = conn.execute(
                        text("""
                            SELECT id, normalized_fields, raw_payload, status, 
                                   total_fields, recognized_fields, accuracy,
                                   created_at
                            FROM recognition_result
                            WHERE invoice_id = :invoice_id
                            ORDER BY created_at DESC
                            LIMIT 1
                        """),
                        {"invoice_id": str(invoice_id)}
                    )
                    result = result_result.fetchone()
                    
                    if result:
                        result_id, normalized_fields, raw_payload, result_status, total_fields, recognized_fields, accuracy, created_at = result
                        print(f"  [识别结果]")
                        print(f"    结果ID: {result_id}")
                        print(f"    状态: {result_status}")
                        print(f"    总字段数: {total_fields}")
                        print(f"    已识别字段数: {recognized_fields}")
                        print(f"    准确率: {accuracy}")
                        print(f"    创建时间: {created_at}")
                        
                        # 检查 normalized_fields
                        if normalized_fields:
                            print(f"    ✅ normalized_fields 存在")
                            if isinstance(normalized_fields, dict):
                                print(f"    字段数: {len(normalized_fields)}")
                                print(f"    字段键: {list(normalized_fields.keys())[:10]}...")
                                if "items" in normalized_fields:
                                    items = normalized_fields.get("items", [])
                                    if isinstance(items, list):
                                        print(f"    ✅ 包含 items 数组，数量: {len(items)}")
                                    else:
                                        print(f"    ⚠️  items 不是数组: {type(items)}")
                                # 显示部分内容
                                normalized_str = json.dumps(normalized_fields, ensure_ascii=False, indent=2)
                                print(f"    内容预览 (前500字符):")
                                print(f"    {normalized_str[:500]}...")
                            else:
                                print(f"    ⚠️  normalized_fields 不是字典: {type(normalized_fields)}")
                        else:
                            print(f"    ❌ normalized_fields 为空")
                            
                            # 检查 raw_payload
                            if raw_payload:
                                print(f"    ✅ raw_payload 存在，长度: {len(raw_payload)} 字符")
                                try:
                                    raw_json = json.loads(raw_payload)
                                    print(f"    raw_payload 解析成功，类型: {type(raw_json)}")
                                    if isinstance(raw_json, dict):
                                        print(f"    键: {list(raw_json.keys())}")
                                        if "text" in raw_json:
                                            print(f"    ✅ 包含 'text' 字段")
                                            text_data = raw_json["text"]
                                            if isinstance(text_data, dict):
                                                print(f"    text 字段是字典，键: {list(text_data.keys())[:10]}...")
                                                if "items" in text_data:
                                                    items = text_data.get("items", [])
                                                    if isinstance(items, list):
                                                        print(f"    ✅ text.items 是数组，数量: {len(items)}")
                                                    else:
                                                        print(f"    ⚠️  text.items 不是数组: {type(items)}")
                                            else:
                                                print(f"    ⚠️  text 字段不是字典: {type(text_data)}")
                                        else:
                                            print(f"    ⚠️  不包含 'text' 字段")
                                except Exception as e:
                                    print(f"    ⚠️  raw_payload 解析失败: {e}")
                            else:
                                print(f"    ❌ raw_payload 也为空")
                        
                        print()
            
            print("=" * 80)
            print("监控完成")
            print("=" * 80)
            
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

if __name__ == "__main__":
    monitor_latest_task()

