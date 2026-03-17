#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接查询数据库，检查模板的prompt字段
"""
import sys
import io
import psycopg2
from psycopg2.extras import RealDictCursor

# 修复Windows控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 数据库连接配置
DB_CONFIG = {
    "host": "219.151.188.129",
    "port": 50510,
    "database": "app",  # 尝试app数据库
    "user": "postgres",
    "password": "Post.&0055"
}

TEMPLATE_ID = "3cede2eb-2acf-465e-91da-899cff8ad9bd"

def main():
    try:
        # 连接数据库
        print(f"正在连接数据库 {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ 数据库连接成功\n")
        
        # 查询模板的prompt字段
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 方法1：查询prompt字段
            print("=" * 60)
            print("方法1：查询prompt字段")
            print("=" * 60)
            cur.execute(
                "SELECT id, name, prompt FROM template WHERE id = %s",
                (TEMPLATE_ID,)
            )
            row = cur.fetchone()
            if row:
                print(f"模板ID: {row['id']}")
                print(f"模板名称: {row['name']}")
                print(f"prompt字段值: {repr(row['prompt'])}")
                print(f"prompt字段类型: {type(row['prompt'])}")
                print(f"prompt是否为空: {row['prompt'] is None}")
                print(f"prompt是否为空字符串: {row['prompt'] == ''}")
            else:
                print(f"❌ 未找到ID为 {TEMPLATE_ID} 的模板")
            
            # 方法2：查询所有字段
            print("\n" + "=" * 60)
            print("方法2：查询所有字段")
            print("=" * 60)
            cur.execute(
                "SELECT * FROM template WHERE id = %s",
                (TEMPLATE_ID,)
            )
            row = cur.fetchone()
            if row:
                print(f"所有字段:")
                for key, value in row.items():
                    if key == 'prompt':
                        print(f"  {key}: {repr(value)} ⭐ (这是prompt字段)")
                    else:
                        print(f"  {key}: {value}")
            
            # 方法3：检查prompt列是否存在
            print("\n" + "=" * 60)
            print("方法3：检查prompt列是否存在")
            print("=" * 60)
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'template' AND column_name = 'prompt'
            """)
            col_info = cur.fetchone()
            if col_info:
                print(f"✅ prompt列存在:")
                print(f"  列名: {col_info['column_name']}")
                print(f"  数据类型: {col_info['data_type']}")
                print(f"  是否可为空: {col_info['is_nullable']}")
            else:
                print("❌ prompt列不存在！")
            
            # 方法4：更新测试（如果prompt为空）
            if row and (row['prompt'] is None or row['prompt'] == ''):
                print("\n" + "=" * 60)
                print("方法4：尝试更新prompt字段")
                print("=" * 60)
                test_prompt = "测试提示词_直接更新"
                cur.execute(
                    "UPDATE template SET prompt = %s WHERE id = %s",
                    (test_prompt, TEMPLATE_ID)
                )
                conn.commit()
                print(f"✅ 已更新prompt为: {test_prompt}")
                
                # 再次查询验证
                cur.execute(
                    "SELECT prompt FROM template WHERE id = %s",
                    (TEMPLATE_ID,)
                )
                updated_row = cur.fetchone()
                if updated_row:
                    print(f"✅ 验证更新后的prompt: {repr(updated_row['prompt'])}")
        
        conn.close()
        print("\n✅ 测试完成")
        
    except psycopg2.OperationalError as e:
        print(f"❌ 数据库连接失败: {e}")
        # 尝试其他数据库名
        for db_name in ["ruoyi_db", "luoyi_db"]:
            try:
                print(f"\n尝试连接数据库: {db_name}...")
                DB_CONFIG["database"] = db_name
                conn = psycopg2.connect(**DB_CONFIG)
                print(f"✅ 成功连接到数据库: {db_name}")
                conn.close()
                print("请修改脚本中的database配置后重试")
                break
            except:
                continue
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

