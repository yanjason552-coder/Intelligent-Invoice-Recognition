#!/usr/bin/env python3
"""
测试阿里云PostgreSQL数据库连通性 - 测试app和sys数据库
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
        print("成功连接！")
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

        # 列出前5个表名
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            LIMIT 5;
        """)
        tables = cursor.fetchall()
        if tables:
            print("表列表 (前5个):")
            for table in tables:
                print(f"  - {table[0]}")

        # 关闭连接
        cursor.close()
        connection.close()
        print("连接已关闭")
        return True

    except OperationalError as e:
        print(f"连接失败: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False

def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

    # 获取配置
    base_config = {
        'host': os.getenv('POSTGRES_SERVER'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD')
    }

    print("=== 阿里云PostgreSQL数据库连通性测试 ===")

    # 测试app数据库
    app_config = {**base_config, 'database': 'app'}
    app_success = test_database_connection('app', app_config)

    # 测试sys数据库
    sys_config = {**base_config, 'database': 'sys'}
    sys_success = test_database_connection('sys', sys_config)

    print("\n=== 测试结果汇总 ===")
    print(f"app数据库: {'成功' if app_success else '失败'}")
    print(f"sys数据库: {'成功' if sys_success else '失败'}")

    if app_success and sys_success:
        print("所有数据库连接测试通过！")
        return 0
    else:
        print("部分数据库连接测试失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())
