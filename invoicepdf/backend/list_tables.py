#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出数据库中的所有表
"""

import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("需要安装 psycopg2: pip install psycopg2-binary")
    sys.exit(1)

DB_HOST = "219.151.188.129"
DB_PORT = "50510"
DB_USER = "postgres"
DB_PASSWORD = "Post.&0055"
DB_NAME = "ruoyi_db"

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 列出所有表
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    
    print("=" * 80)
    print(f"数据库 {DB_NAME} 中的所有表 (共 {len(tables)} 个):")
    print("=" * 80)
    
    # 查找可能相关的表
    invoice_tables = []
    config_tables = []
    other_tables = []
    
    for table in tables:
        table_name = table['table_name']
        if 'invoice' in table_name.lower():
            invoice_tables.append(table_name)
        elif 'config' in table_name.lower():
            config_tables.append(table_name)
        else:
            other_tables.append(table_name)
    
    if invoice_tables:
        print("\n发票相关表:")
        for table in invoice_tables:
            print(f"  - {table}")
    
    if config_tables:
        print("\n配置相关表:")
        for table in config_tables:
            print(f"  - {table}")
    
    print("\n所有表列表:")
    for idx, table in enumerate(tables, 1):
        print(f"  {idx:3d}. {table['table_name']}")
    
    # 检查是否有 llm_config 或 model_config
    print("\n" + "=" * 80)
    print("检查关键表是否存在:")
    print("=" * 80)
    
    key_tables = ['llm_config', 'model_config', 'invoice_file', 'invoice', 'recognition_task']
    for table_name in key_tables:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            ) as exists;
        """, (table_name,))
        result = cur.fetchone()
        exists = result['exists'] if isinstance(result, dict) else result[0]
        status = "[存在]" if exists else "[不存在]"
        print(f"  {status} {table_name}")
    
    print("\n" + "=" * 80)
    print("结论:")
    print("=" * 80)
    if not any('invoice' in t['table_name'].lower() for t in tables):
        print("[警告] 当前数据库 (ruoyi_db) 中没有找到发票相关的表")
        print("可能的原因:")
        print("  1. 发票识别系统的数据在另一个数据库中（如 'app' 数据库）")
        print("  2. 数据库迁移未执行")
        print("\n建议: 检查 'app' 数据库")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"错误: {str(e)}")
    import traceback
    traceback.print_exc()

