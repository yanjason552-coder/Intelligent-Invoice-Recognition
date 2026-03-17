#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查指定发票的 normalized_fields 情况"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings

def check_invoice(invoice_id: str):
    """检查指定发票的 normalized_fields"""
    try:
        database_url = str(settings.DATABASE_URL) if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL else str(settings.SQLALCHEMY_DATABASE_URI)
    except Exception as e:
        print(f"错误: 无法获取数据库配置: {e}")
        return
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            print("=" * 80)
            print(f"检查发票: {invoice_id}")
            print("=" * 80)
            
            # 查询发票基本信息
            invoice_result = conn.execute(
                text("""
                    SELECT id, invoice_no, model_name, recognition_status
                    FROM invoice
                    WHERE id = :invoice_id
                """),
                {"invoice_id": invoice_id}
            )
            invoice = invoice_result.fetchone()
            
            if not invoice:
                print(f"❌ 未找到发票: {invoice_id}")
                return
            
            invoice_id_db, invoice_no, model_name, recognition_status = invoice
            print(f"\n[发票信息]")
            print(f"  发票编号: {invoice_no}")
            print(f"  模型名称: {model_name}")
            print(f"  识别状态: {recognition_status}")
            
            # 查询识别结果
            result_result = conn.execute(
                text("""
                    SELECT id, normalized_fields, raw_payload, raw_data, status,
                           created_at
                    FROM recognition_result
                    WHERE invoice_id = :invoice_id
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"invoice_id": invoice_id}
            )
            result = result_result.fetchone()
            
            if not result:
                print(f"\n❌ 未找到识别结果")
                return
            
            result_id, normalized_fields, raw_payload, raw_data, status, created_at = result
            print(f"\n[识别结果]")
            print(f"  结果ID: {result_id}")
            print(f"  状态: {status}")
            print(f"  创建时间: {created_at}")
            
            # 检查 normalized_fields
            print(f"\n[normalized_fields 检查]")
            if normalized_fields:
                print(f"  ✅ normalized_fields 存在")
                if isinstance(normalized_fields, dict):
                    print(f"  字段数: {len(normalized_fields)}")
                    print(f"  字段键: {list(normalized_fields.keys())}")
                    if "items" in normalized_fields:
                        items = normalized_fields.get("items", [])
                        if isinstance(items, list):
                            print(f"  ✅ 包含 items 数组，数量: {len(items)}")
                        else:
                            print(f"  ⚠️  items 不是数组: {type(items)}")
                    print(f"\n  内容:")
                    print(json.dumps(normalized_fields, ensure_ascii=False, indent=2)[:1000])
                else:
                    print(f"  ⚠️  normalized_fields 不是字典: {type(normalized_fields)}")
                    print(f"  值: {normalized_fields}")
            else:
                print(f"  ❌ normalized_fields 为空")
            
            # 检查 raw_payload
            print(f"\n[raw_payload 检查]")
            if raw_payload:
                print(f"  ✅ raw_payload 存在，长度: {len(raw_payload)} 字符")
                print(f"  前500字符: {raw_payload[:500]}")
                try:
                    raw_json = json.loads(raw_payload)
                    print(f"\n  ✅ raw_payload 解析成功")
                    print(f"  类型: {type(raw_json)}")
                    if isinstance(raw_json, dict):
                        print(f"  键: {list(raw_json.keys())}")
                        if "text" in raw_json:
                            print(f"  ✅ 包含 'text' 字段")
                            text_data = raw_json["text"]
                            if isinstance(text_data, dict):
                                print(f"  text 字段是字典，键: {list(text_data.keys())}")
                                if "items" in text_data:
                                    items = text_data.get("items", [])
                                    if isinstance(items, list):
                                        print(f"  ✅ text.items 是数组，数量: {len(items)}")
                                    else:
                                        print(f"  ⚠️  text.items 不是数组: {type(items)}")
                                print(f"\n  text 内容预览:")
                                print(json.dumps(text_data, ensure_ascii=False, indent=2)[:1000])
                            else:
                                print(f"  ⚠️  text 字段不是字典: {type(text_data)}")
                        else:
                            print(f"  ⚠️  不包含 'text' 字段")
                except Exception as e:
                    print(f"  ❌ raw_payload 解析失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"  ❌ raw_payload 为空")
            
            # 检查 raw_data
            print(f"\n[raw_data 检查]")
            if raw_data:
                print(f"  ✅ raw_data 存在")
                if isinstance(raw_data, dict):
                    print(f"  类型: dict，键: {list(raw_data.keys())}")
                    if "text" in raw_data:
                        print(f"  ✅ 包含 'text' 字段")
                else:
                    print(f"  类型: {type(raw_data)}")
            else:
                print(f"  ❌ raw_data 为空")
            
            print("\n" + "=" * 80)
            print("检查完成")
            print("=" * 80)
            
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        invoice_id = sys.argv[1]
    else:
        invoice_id = "3f63ea37-4dc4-4ee2-bdc6-176ecb1d29d3"  # 默认使用用户提供的发票ID
    check_invoice(invoice_id)

