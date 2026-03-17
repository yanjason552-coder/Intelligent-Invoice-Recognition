#!/usr/bin/env python3
"""
测试数据库配置是否正确
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=== 数据库配置检查 ===")
print(f"POSTGRES_SERVER: {os.getenv('POSTGRES_SERVER')}")
print(f"POSTGRES_PORT: {os.getenv('POSTGRES_PORT')}")
print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER')}")
print(f"POSTGRES_DB: {os.getenv('POSTGRES_DB')}")
print(f"POSTGRES_PASSWORD: {'***' if os.getenv('POSTGRES_PASSWORD') else 'Not set'}")

print("\n=== 系统数据库配置检查 ===")
print(f"SYS_DB_HOST: {os.getenv('SYS_DB_HOST')}")
print(f"SYS_DB_PORT: {os.getenv('SYS_DB_PORT')}")
print(f"SYS_DB_NAME: {os.getenv('SYS_DB_NAME')}")
print(f"SYS_DB_USER: {os.getenv('SYS_DB_USER')}")
print(f"SYS_DB_PASSWORD: {'***' if os.getenv('SYS_DB_PASSWORD') else 'Not set'}")

print("\n=== 配置验证 ===")
required_vars = ['POSTGRES_SERVER', 'POSTGRES_PORT', 'POSTGRES_USER', 'POSTGRES_DB', 'POSTGRES_PASSWORD']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
else:
    print("✅ 所有必需的环境变量都已配置")

print("\n=== 数据库连接字符串预览 ===")
if all(os.getenv(var) for var in required_vars):
    connection_string = f"postgresql://{os.getenv('POSTGRES_USER')}:***@{os.getenv('POSTGRES_SERVER')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    print(f"连接字符串: {connection_string}")
else:
    print("❌ 无法生成连接字符串，缺少必需配置")
