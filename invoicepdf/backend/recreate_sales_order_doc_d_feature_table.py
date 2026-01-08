#!/usr/bin/env python3
"""
重新创建销售订单行项目属性表的Python脚本
"""

import psycopg2
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入项目配置
from app.core.config import settings

def recreate_sales_order_doc_d_feature_table():
    """重新创建sales_order_doc_d_feature表"""
    
    # 使用项目配置
    db_config = {
        'host': settings.POSTGRES_SERVER,
        'port': settings.POSTGRES_PORT,
        'database': settings.POSTGRES_DB,
        'user': settings.POSTGRES_USER,
        'password': settings.POSTGRES_PASSWORD
    }
    
    conn = None
    cursor = None
    
    try:
        # 连接数据库
        print("正在连接数据库...")
        conn = psycopg2.connect(**db_config)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("数据库连接成功")
        
        # 先删除现有表
        print("正在删除现有表...")
        cursor.execute("DROP TABLE IF EXISTS sales_order_doc_d_feature CASCADE")
        print("现有表已删除")
        
        # 读取SQL文件
        sql_file_path = Path(__file__).parent / "create_sales_order_doc_d_feature_table.sql"
        
        if not sql_file_path.exists():
            print(f"SQL文件不存在: {sql_file_path}")
            return False
        
        print(f"读取SQL文件: {sql_file_path}")
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 执行SQL语句
        print("正在创建sales_order_doc_d_feature表...")
        cursor.execute(sql_content)
        
        # 提交事务
        conn.commit()
        print("表创建成功！")
        
        # 验证表是否创建成功
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'sales_order_doc_d_feature'
        """)
        
        result = cursor.fetchone()
        if result:
            print("✓ 表验证成功: sales_order_doc_d_feature 已存在")
            
            # 显示表结构
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'sales_order_doc_d_feature'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            print("\n表结构:")
            print("-" * 80)
            print(f"{'字段名':<30} {'数据类型':<20} {'允许NULL':<10} {'默认值':<20}")
            print("-" * 80)
            for col in columns:
                print(f"{col[0]:<30} {col[1]:<20} {col[2]:<10} {str(col[3]):<20}")
            
            # 显示索引
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes 
                WHERE tablename = 'sales_order_doc_d_feature'
            """)
            
            indexes = cursor.fetchall()
            if indexes:
                print("\n索引:")
                print("-" * 80)
                for idx in indexes:
                    print(f"索引名: {idx[0]}")
                    print(f"定义: {idx[1]}")
                    print("-" * 40)
            
        else:
            print("✗ 表验证失败: sales_order_doc_d_feature 不存在")
            return False
        
        return True
        
    except psycopg2.Error as e:
        print(f"数据库错误: {e}")
        if conn:
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"执行错误: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    print("=" * 60)
    print("重新创建销售订单行项目属性表")
    print("=" * 60)
    
    success = recreate_sales_order_doc_d_feature_table()
    
    if success:
        print("\n✓ 表重新创建完成！")
    else:
        print("\n✗ 表重新创建失败！")
    
    print("=" * 60) 