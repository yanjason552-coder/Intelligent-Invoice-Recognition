#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""简单查询脚本 - 直接查询数据库"""

import os
import json
import sys
from pathlib import Path

# 设置环境变量（如果需要）
# os.environ.setdefault('DATABASE_URL', 'postgresql://user:password@localhost/dbname')

# 添加项目路径
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

try:
    from app.core.config import settings
    database_url = str(settings.DATABASE_URL)
except Exception as e:
    print(f"无法加载配置: {e}")
    print("请设置 DATABASE_URL 环境变量")
    sys.exit(1)

from sqlalchemy import create_engine, text

def query_invoice(invoice_id: str):
    """查询发票数据"""
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            print("=" * 80)
            print(f"查询发票: {invoice_id}")
            print("=" * 80)
            
            # 查询识别结果
            result = conn.execute(
                text("""
                    SELECT id, normalized_fields, raw_payload, raw_data, status,
                           recognition_time, create_time
                    FROM recognition_result
                    WHERE invoice_id = :invoice_id
                    ORDER BY recognition_time DESC NULLS LAST, create_time DESC
                    LIMIT 1
                """),
                {"invoice_id": invoice_id}
            )
            row = result.fetchone()
            
            if not row:
                print("❌ 未找到识别结果")
                return
            
            result_id, normalized_fields, raw_payload, raw_data, status, recognition_time, create_time = row
            
            print(f"\n[识别结果]")
            print(f"  结果ID: {result_id}")
            print(f"  状态: {status}")
            print(f"  识别时间: {recognition_time}")
            print(f"  创建时间: {create_time}")
            
            # 检查 normalized_fields
            print(f"\n[normalized_fields]")
            if normalized_fields is None:
                print("  ❌ 为 NULL")
            else:
                print(f"  ✅ 不为 NULL")
                print(f"  类型: {type(normalized_fields)}")
                if isinstance(normalized_fields, dict):
                    print(f"  字段数: {len(normalized_fields)}")
                    print(f"  字段键: {list(normalized_fields.keys())}")
                    if 'items' in normalized_fields:
                        items = normalized_fields.get('items', [])
                        print(f"  items 数量: {len(items) if isinstance(items, list) else 'N/A'}")
                elif isinstance(normalized_fields, str):
                    print(f"  是字符串，长度: {len(normalized_fields)}")
                    try:
                        parsed = json.loads(normalized_fields)
                        print(f"  ✅ 可以解析为 JSON")
                        if isinstance(parsed, dict):
                            print(f"  解析后字段数: {len(parsed)}")
                            print(f"  解析后字段键: {list(parsed.keys())}")
                    except:
                        print(f"  ⚠️  无法解析为 JSON")
            
            # 检查 raw_payload
            print(f"\n[raw_payload]")
            if raw_payload is None:
                print("  ❌ 为 NULL")
            else:
                print(f"  ✅ 不为 NULL")
                print(f"  类型: {type(raw_payload)}")
                if isinstance(raw_payload, str):
                    print(f"  长度: {len(raw_payload)} 字符")
                    print(f"  前300字符: {raw_payload[:300]}")
                    try:
                        raw_json = json.loads(raw_payload)
                        print(f"  ✅ 可以解析为 JSON")
                        if isinstance(raw_json, dict):
                            print(f"  键: {list(raw_json.keys())}")
                            if 'data' in raw_json:
                                data = raw_json['data']
                                if isinstance(data, dict) and 'outputs' in data:
                                    outputs = data['outputs']
                                    if isinstance(outputs, dict) and 'text' in outputs:
                                        text_data = outputs['text']
                                        print(f"  ✅ 找到 data.outputs.text")
                                        if isinstance(text_data, dict):
                                            print(f"    text 字段键: {list(text_data.keys())}")
                                            if 'items' in text_data:
                                                items = text_data.get('items', [])
                                                print(f"    items 数量: {len(items) if isinstance(items, list) else 'N/A'}")
                    except Exception as e:
                        print(f"  ❌ 解析失败: {e}")
            
            print("\n" + "=" * 80)
            
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

if __name__ == "__main__":
    invoice_id = sys.argv[1] if len(sys.argv) > 1 else "2b2701eb-36e2-4069-82d2-78b47877cff7"
    query_invoice(invoice_id)

