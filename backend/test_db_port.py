"""
数据库端口连通性测试脚本
用于诊断数据库连接超时问题
"""
import socket
import sys
import time
from urllib.parse import urlparse

def test_port_connectivity(host: str, port: int, timeout: int = 10) -> bool:
    """测试TCP端口连通性"""
    try:
        print(f"正在测试 {host}:{port} 的连通性...")
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        elapsed = time.time() - start_time
        sock.close()
        
        if result == 0:
            print(f"[OK] 端口 {port} 可达 (耗时: {elapsed:.2f}秒)")
            return True
        else:
            print(f"[FAIL] 端口 {port} 不可达 (错误代码: {result})")
            return False
    except socket.timeout:
        print(f"[TIMEOUT] 连接超时（{timeout}秒）")
        return False
    except Exception as e:
        print(f"[ERROR] 连接失败: {e}")
        return False

def test_database_connection(database_url: str) -> None:
    """测试数据库连接"""
    try:
        from app.core.config import settings
        from app.core.db import engine
        
        print("\n" + "="*60)
        print("数据库连接测试")
        print("="*60)
        
        # 解析数据库URL
        parsed = urlparse(database_url)
        host = parsed.hostname
        port = parsed.port or 5432
        
        print(f"数据库主机: {host}")
        print(f"数据库端口: {port}")
        print(f"数据库名称: {parsed.path.lstrip('/')}")
        print(f"用户名: {parsed.username}")
        print()
        
        # 测试端口连通性
        print("步骤1: 测试端口连通性")
        print("-" * 60)
        port_ok = test_port_connectivity(host, port, timeout=30)
        
        if not port_ok:
            print("\n[WARNING] 端口不可达，可能的原因：")
            print("  1. 防火墙阻止了连接")
            print("  2. 数据库服务器未运行")
            print("  3. 数据库服务器只允许特定IP访问")
            print("  4. 网络路由问题")
            return
        
        # 测试实际数据库连接
        print("\n步骤2: 测试数据库连接")
        print("-" * 60)
        try:
            start_time = time.time()
            with engine.connect() as conn:
                result = conn.exec_driver_sql("SELECT 1")
                elapsed = time.time() - start_time
                print(f"[OK] 数据库连接成功 (耗时: {elapsed:.2f}秒)")
                
                # 测试查询
                result = conn.exec_driver_sql("SELECT version()")
                version = result.fetchone()[0]
                print(f"[OK] PostgreSQL版本: {version[:50]}...")
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"[FAIL] 数据库连接失败 (耗时: {elapsed:.2f}秒)")
            print(f"   错误: {e}")
            print("\n可能的原因：")
            print("  1. 数据库用户名或密码错误")
            print("  2. 数据库不存在")
            print("  3. 用户没有访问权限")
            print("  4. SSL/TLS配置问题")
            
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        from app.core.config import settings
        database_url = settings.SQLALCHEMY_DATABASE_URI
        test_database_connection(database_url)
    except Exception as e:
        print(f"[ERROR] 无法读取数据库配置: {e}")
        print("\n请确保：")
        print("  1. 在 backend 目录下运行此脚本")
        print("  2. .env 文件配置正确")
        sys.exit(1)
