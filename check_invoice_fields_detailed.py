#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查发票字段显示问题
"""

import sys
import json
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlmodel import Session, text, create_engine

# 数据库连接信息
DB_HOST = "219.151.188.129"
DB_PORT = 50510
DB_USER = "postgres"
DB_PASSWORD = "Post.&0055"
DB_NAME = "app"

encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
database_url = f"postgresql+psycopg://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

connect_args = {
    "connect_timeout": 30,
    "options": "-c statement_timeout=300000",
}

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=60,
    pool_size=5,
    max_overflow=10,
    echo=False,
    connect_args=connect_args,
)

invoice_no = "INV-20260206144930-bb24635b"

with Session(engine) as session:
    print("=" * 80)
    print("详细检查发票字段数据")
    print("=" * 80)
    print()
    
    # 1. 查询发票基本信息（不查询不存在的字段）
    invoice_row = session.execute(
        text("""
            SELECT id, invoice_no, model_name, template_name, template_version, 
                   template_version_id, recognition_status, review_status
            FROM invoice
            WHERE invoice_no = :invoice_no
        """),
        {"invoice_no": invoice_no}
    ).fetchone()
    
    if not invoice_row:
        print(f"[错误] 未找到发票: {invoice_no}")
        sys.exit(1)
    
    invoice_id = invoice_row[0]
    print(f"【发票基本信息】")
    print(f"  发票ID: {invoice_id}")
    print(f"  发票编号: {invoice_row[1]}")
    print(f"  模型名称: {invoice_row[2]}")
    print(f"  模板名称: {invoice_row[3]}")
    print(f"  模板版本: {invoice_row[4]}")
    print(f"  模板版本ID: {invoice_row[5]}")
    print(f"  识别状态: {invoice_row[6]}")
    print(f"  审核状态: {invoice_row[7]}")
    print()
    
    # 2. 查询识别结果的完整 normalized_fields
    result_row = session.execute(
        text("""
            SELECT id, normalized_fields, model_usage, recognition_time
            FROM recognition_result
            WHERE invoice_id = :invoice_id
            ORDER BY recognition_time DESC
            LIMIT 1
        """),
        {"invoice_id": str(invoice_id)}
    ).fetchone()
    
    if result_row:
        print(f"【识别结果 - normalized_fields 完整内容】")
        print(f"  结果ID: {result_row[0]}")
        print(f"  识别时间: {result_row[3]}")
        print()
        
        normalized_fields = result_row[1]
        if normalized_fields:
            print(f"  normalized_fields 类型: {type(normalized_fields)}")
            print(f"  normalized_fields 是否为字典: {isinstance(normalized_fields, dict)}")
            print()
            
            if isinstance(normalized_fields, dict):
                print(f"  字段数量: {len(normalized_fields)}")
                print(f"  所有字段键: {list(normalized_fields.keys())}")
                print()
                
                print(f"  字段详细内容:")
                for key, value in normalized_fields.items():
                    if isinstance(value, list):
                        print(f"    {key}: [列表，共 {len(value)} 项]")
                        if len(value) > 0:
                            print(f"      第一项示例: {json.dumps(value[0], ensure_ascii=False, indent=8)}")
                    elif isinstance(value, dict):
                        print(f"    {key}: {{字典}}")
                        print(f"      内容: {json.dumps(value, ensure_ascii=False, indent=8)}")
                    else:
                        print(f"    {key}: {value} (类型: {type(value).__name__})")
                print()
                
                # 检查 items 数组的详细内容
                if 'items' in normalized_fields:
                    items = normalized_fields['items']
                    print(f"  【items 数组详细内容】")
                    print(f"    数组长度: {len(items)}")
                    print(f"    第一项完整内容:")
                    print(json.dumps(items[0] if items else {}, ensure_ascii=False, indent=4))
                    print()
            else:
                print(f"  normalized_fields 内容（字符串）:")
                print(f"  {str(normalized_fields)[:500]}")
                print()
        else:
            print(f"  [警告] normalized_fields 为空")
            print()
    
    # 3. 查询API返回的数据格式（模拟后端API逻辑）
    print(f"【模拟后端API返回数据】")
    print(f"  检查后端API代码逻辑...")
    print()

