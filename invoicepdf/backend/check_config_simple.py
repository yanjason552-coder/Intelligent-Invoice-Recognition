#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的配置检查脚本 - 直接连接数据库，不依赖应用配置
"""

import os
import sys

# 设置输出编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 数据库连接信息
DB_HOST = os.getenv("POSTGRES_SERVER", "219.151.188.129")
DB_PORT = os.getenv("POSTGRES_PORT", "50510")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Post.&0055")
DB_NAME = os.getenv("POSTGRES_DB", "ruoyi_db")

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ 需要安装 psycopg2: pip install psycopg2-binary")
    sys.exit(1)

def check_llm_config():
    """检查 llm_config 表配置"""
    print("=" * 80)
    print("=== 检查 llm_config 表配置 ===")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 先检查表是否存在
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%config%'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        print(f"\n找到以下包含 'config' 的表:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # 检查是否有 llm_config 表
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'llm_config'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("\n[警告] llm_config 表不存在")
            print("可能的原因:")
            print("  1. 表名不同（请检查上面的表列表）")
            print("  2. 表在不同的 schema 中")
            print("  3. 数据库迁移未执行")
            return False
        
        # 查询所有配置
        cur.execute("""
            SELECT 
                id,
                name,
                endpoint,
                CASE 
                    WHEN api_key IS NULL OR api_key = '' THEN '未设置'
                    ELSE '已设置'
                END as api_key_status,
                app_type,
                workflow_id,
                app_id,
                is_active,
                is_default,
                timeout,
                max_retries
            FROM llm_config
            ORDER BY create_time DESC
        """)
        
        configs = cur.fetchall()
        
        if not configs:
            print("[错误] llm_config 表中没有配置")
            return False
        
        print(f"\n找到 {len(configs)} 个配置:\n")
        
        all_valid = True
        for idx, config in enumerate(configs, 1):
            print(f"--- 配置 {idx}: {config['name']} (ID: {config['id']}) ---")
            
            issues = []
            
            # 检查必需字段
            if not config['name'] or not config['name'].strip():
                issues.append("[错误] name: 配置名称不能为空")
            else:
                print(f"[OK] name: {config['name']}")
            
            if not config['endpoint'] or not config['endpoint'].strip():
                issues.append("[错误] endpoint: API端点地址不能为空")
            else:
                endpoint = config['endpoint'].strip()
                if not endpoint.startswith(("http://", "https://")):
                    issues.append(f"[警告] endpoint: 格式可能不正确: {endpoint}")
                else:
                    print(f"[OK] endpoint: {endpoint}")
            
            if config['api_key_status'] == '未设置':
                issues.append("[错误] api_key: API密钥不能为空")
            else:
                print(f"[OK] api_key: {config['api_key_status']}")
            
            if not config['is_active']:
                issues.append("[警告] is_active: 配置未启用")
            else:
                print(f"[OK] is_active: {config['is_active']}")
            
            print(f"ℹ️  app_type: {config['app_type']}")
            
            if config['app_type'] == 'workflow' and not config['workflow_id']:
                issues.append("[警告] workflow_id: app_type 为 workflow 时，建议配置 workflow_id")
            elif config['workflow_id']:
                print(f"[OK] workflow_id: {config['workflow_id']}")
            
            if config['app_type'] == 'chat' and not config['app_id']:
                issues.append("[警告] app_id: app_type 为 chat 时，建议配置 app_id")
            elif config['app_id']:
                print(f"[OK] app_id: {config['app_id']}")
            
            if issues:
                print("\n[警告] 发现以下问题:")
                for issue in issues:
                    print(f"  {issue}")
                all_valid = False
            else:
                print("\n[OK] 配置检查通过")
            
            print()
        
        cur.close()
        conn.close()
        
        return all_valid
        
    except Exception as e:
        error_msg = str(e)
        print(f"[错误] 数据库连接失败: {error_msg}")
        print("\n提示: 请确保:")
        print("  1. 数据库服务正在运行")
        print("  2. 数据库连接信息正确")
        print("  3. 数据库名称正确（当前: luoyi_db）")
        print("  4. 可以通过环境变量设置: POSTGRES_SERVER, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB")
        
        # 如果是数据库不存在错误，尝试列出可用数据库
        if "does not exist" in error_msg.lower():
            print("\n尝试列出可用数据库...")
            try:
                conn = psycopg2.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database="postgres"  # 连接到默认数据库
                )
                cur = conn.cursor()
                cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
                databases = cur.fetchall()
                print("可用数据库列表:")
                for db in databases:
                    print(f"  - {db[0]}")
                cur.close()
                conn.close()
            except Exception as e2:
                print(f"无法列出数据库: {str(e2)}")
        
        return False

def check_external_file_id():
    """检查文件的 external_file_id"""
    print("=" * 80)
    print("=== 检查文件的 external_file_id ===")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查询所有文件
        cur.execute("""
            SELECT 
                id,
                file_name,
                file_path,
                file_type,
                file_size,
                external_file_id,
                upload_time
            FROM invoice_file
            ORDER BY upload_time DESC
        """)
        
        files = cur.fetchall()
        
        if not files:
            print("[错误] invoice_file 表中没有文件")
            return
        
        print(f"\n找到 {len(files)} 个文件:\n")
        
        files_without_external_id = []
        files_with_external_id = []
        
        for idx, file in enumerate(files, 1):
            print(f"--- 文件 {idx}: {file['file_name']} (ID: {file['id']}) ---")
            print(f"  文件路径: {file['file_path']}")
            print(f"  文件类型: {file['file_type']}")
            print(f"  文件大小: {file['file_size']} 字节")
            
            if file['external_file_id']:
                print(f"  [OK] external_file_id: {file['external_file_id']}")
                files_with_external_id.append(file)
            else:
                print(f"  [错误] external_file_id: 未设置")
                files_without_external_id.append(file)
            
            # 检查文件是否存在
            if file['file_path']:
                if os.path.exists(file['file_path']):
                    print(f"  [OK] 本地文件存在")
                else:
                    print(f"  [错误] 本地文件不存在: {file['file_path']}")
            
            print()
        
        # 统计信息
        print("=" * 80)
        print("=== 统计信息 ===")
        print(f"总文件数: {len(files)}")
        print(f"有 external_file_id: {len(files_with_external_id)}")
        print(f"无 external_file_id: {len(files_without_external_id)}")
        
        if files_without_external_id:
            print("\n[警告] 以下文件缺少 external_file_id:")
            for file in files_without_external_id:
                print(f"  - {file['file_name']} (ID: {file['id']})")
            print("\n提示: 这些文件在识别时会自动上传到外部API并获取 external_file_id")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"[错误] 数据库连接失败: {str(e)}")
        print("\n提示: 请确保数据库服务正在运行且连接信息正确")

def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("配置和文件检查工具 (简化版)")
    print("=" * 80)
    print(f"\n数据库连接信息:")
    print(f"  主机: {DB_HOST}")
    print(f"  端口: {DB_PORT}")
    print(f"  用户: {DB_USER}")
    print(f"  数据库: {DB_NAME}")
    print("=" * 80 + "\n")
    
    # 1. 检查 llm_config 配置
    config_valid = check_llm_config()
    
    print("\n")
    
    # 2. 检查 external_file_id
    check_external_file_id()
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)
    
    if not config_valid:
        print("\n[警告] 发现配置问题，请修复后再进行识别任务")

if __name__ == "__main__":
    main()

