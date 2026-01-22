"""
检查 recognition_task 表的列结构
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect
from app.core.config import settings

def check_table_columns():
    """检查 recognition_task 表的列"""
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    inspector = inspect(engine)
    
    # 获取 recognition_task 表的所有列
    columns = inspector.get_columns('recognition_task')
    
    print("recognition_task 表的列：")
    print("-" * 60)
    for col in columns:
        print(f"  {col['name']}: {col['type']}")
    
    # 检查是否有 raw_response_uri 列
    column_names = [col['name'] for col in columns]
    if 'raw_response_uri' in column_names:
        print("\n⚠️  警告：recognition_task 表中存在 raw_response_uri 列，但模型中不应该有")
    else:
        print("\n✓ recognition_task 表中没有 raw_response_uri 列（正确）")
    
    # 检查 recognition_result 表的列
    print("\n" + "=" * 60)
    print("recognition_result 表的列：")
    print("-" * 60)
    result_columns = inspector.get_columns('recognition_result')
    result_column_names = [col['name'] for col in result_columns]
    for col in result_columns:
        print(f"  {col['name']}: {col['type']}")
    
    if 'raw_response_uri' in result_column_names:
        print("\n✓ recognition_result 表中有 raw_response_uri 列（正确）")
    else:
        print("\n⚠️  警告：recognition_result 表中没有 raw_response_uri 列")

if __name__ == "__main__":
    check_table_columns()

