#!/usr/bin/env python3
"""
测试阿里云PostgreSQL数据库连通性
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2 import OperationalError

def test_database_connection(db_name, db_config):
    """测试指定数据库的连接"""
    print(f"\n=== 测试 {db_name} 数据库连接 ===")
    print(f"主机: {db_config['host']}")
    print(f"端口: {db_config['port']}")
    print(f"数据库: {db_config['database']}")
    print(f"用户: {db_config['user']}")
    print("密码: ***")
    print("-" * 50)

    try:
        # 尝试连接数据库
        print("正在连接数据库...")
        connection = psycopg2.connect(**db_config)
        connection.set_session(autocommit=True)

        # 创建游标
        cursor = connection.cursor()

        # 执行简单查询
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print("[SUCCESS] 连接成功！")
        print(f"PostgreSQL版本: {version[0]}")

        # 获取数据库大小
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
        db_size = cursor.fetchone()
        print(f"数据库大小: {db_size[0]}")

        # 获取表数量
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        table_count = cursor.fetchone()
        print(f"公共表数量: {table_count[0]}")

        # 列出前10个表名
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            LIMIT 10;
        """)
        tables = cursor.fetchall()
        if tables:
            print("表列表 (前10个):")
            for table in tables:
                print(f"  - {table[0]}")

        # 关闭连接
        cursor.close()
        connection.close()
        print("[SUCCESS] 连接已关闭")
        return True

    except OperationalError as e:
        print(f"[FAILED] 连接失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 发生错误: {e}")
        return False

def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

    print("环境变量检查:")
    print(f"SYS_DB_HOST: '{os.getenv('SYS_DB_HOST')}'")
    print(f"SYS_DB_PORT: '{os.getenv('SYS_DB_PORT')}'")
    print(f"SYS_DB_NAME: '{os.getenv('SYS_DB_NAME')}'")
    print("-" * 50)

    # 主数据库配置
    main_db_config = {
        'host': os.getenv('POSTGRES_SERVER'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD')
    }

    # 系统数据库配置
    sys_db_config = {
        'host': os.getenv('SYS_DB_HOST'),
        'port': int(os.getenv('SYS_DB_PORT', 5432)),
        'database': os.getenv('SYS_DB_NAME'),
        'user': os.getenv('SYS_DB_USER'),
        'password': os.getenv('SYS_DB_PASSWORD')
    }

    print("=== 阿里云数据库连通性测试 ===")

    # 测试主数据库
    main_success = test_database_connection("主数据库(app)", main_db_config)

    # 测试系统数据库
    sys_success = test_database_connection("系统数据库(sys)", sys_db_config)

    print("\n=== 测试结果汇总 ===")
    if main_success:
        print("[SUCCESS] 主数据库(app): 连接正常")
    else:
        print("[FAILED] 主数据库(app): 连接失败")

    if sys_success:
        print("[SUCCESS] 系统数据库(sys): 连接正常")
    else:
        print("[FAILED] 系统数据库(sys): 连接失败")

    if main_success and sys_success:
        print("\n[SUCCESS] 所有数据库连接测试通过！")
        return True
    else:
        print("\n[FAILED] 部分数据库连接失败，请检查配置和网络连接")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
