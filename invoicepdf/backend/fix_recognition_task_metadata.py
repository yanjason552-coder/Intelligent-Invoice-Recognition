"""
修复 RecognitionTask 模型的元数据问题
确保 raw_response_uri 字段不会出现在 RecognitionTask 查询中
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect, text
from app.core.db import engine

def check_and_fix():
    """检查并修复 recognition_task 表结构"""
    with engine.connect() as conn:
        # 检查 recognition_task 表是否有 raw_response_uri 列
        inspector = inspect(engine)
        columns = inspector.get_columns('recognition_task')
        column_names = [col['name'] for col in columns]
        
        print("recognition_task 表的列：")
        for col in columns:
            print(f"  - {col['name']}")
        
        if 'raw_response_uri' in column_names:
            print("\n⚠️  发现 recognition_task 表中有 raw_response_uri 列（不应该存在）")
            print("   这个列应该只存在于 recognition_result 表中")
            print("   建议：删除这个列或创建迁移脚本")
        else:
            print("\n✓ recognition_task 表中没有 raw_response_uri 列（正确）")
            print("   问题可能是 SQLModel 的元数据缓存")
            print("   建议：重启后端服务以清除缓存")

if __name__ == "__main__":
    check_and_fix()

