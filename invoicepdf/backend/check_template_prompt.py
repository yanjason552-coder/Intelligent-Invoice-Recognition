#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查模板提示词字段"""
import os
import sys
import io
import psycopg2
from psycopg2.extras import RealDictCursor

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 数据库配置
DB_CONFIG = {
    "host": "219.151.188.129",
    "port": "50510",
    "user": "postgres",
    "password": "Post.&0055",
    "database": "app"
}

def check_template_prompt(template_id: str):
    """检查模板的prompt字段"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查询模板
        cur.execute("""
            SELECT id, name, prompt, 
                   pg_typeof(prompt) as prompt_type
            FROM template 
            WHERE id = %s
        """, (template_id,))
        
        result = cur.fetchone()
        if result:
            print("=" * 60)
            print("模板信息:")
            print(f"  ID: {result['id']}")
            print(f"  名称: {result['name']}")
            print(f"  提示词: {result['prompt']}")
            print(f"  提示词类型: {result['prompt_type']}")
            print("=" * 60)
        else:
            print(f"未找到模板: {template_id}")
        
        # 检查字段是否存在
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'template' AND column_name = 'prompt'
        """)
        
        column_info = cur.fetchone()
        if column_info:
            print("\n字段信息:")
            print(f"  字段名: {column_info['column_name']}")
            print(f"  数据类型: {column_info['data_type']}")
            print(f"  可空: {column_info['is_nullable']}")
        else:
            print("\n警告: template表中没有找到prompt字段！")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    template_id = "3cede2eb-2acf-465e-91da-899cff8ad9bd"
    if len(sys.argv) > 1:
        template_id = sys.argv[1]
    check_template_prompt(template_id)

