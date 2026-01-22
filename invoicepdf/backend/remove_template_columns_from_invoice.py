"""
从 invoice 表中移除模板相关列（template_id 和 template_version_id）

如果这些列不存在，脚本会跳过
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from app.core.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_template_columns():
    """从 invoice 表中移除模板相关列"""
    logger.info("=" * 60)
    logger.info("开始移除 invoice 表中的模板相关列")
    logger.info("=" * 60)
    
    inspector = inspect(engine)
    columns = inspector.get_columns('invoice')
    column_names = [col['name'] for col in columns]
    
    logger.info(f"invoice 表当前列: {', '.join(column_names)}")
    
    columns_to_remove = ['template_id', 'template_version_id']
    removed_columns = []
    
    with engine.begin() as connection:
        for column_name in columns_to_remove:
            if column_name in column_names:
                try:
                    # 删除列
                    connection.execute(text(f'ALTER TABLE invoice DROP COLUMN IF EXISTS "{column_name}"'))
                    logger.info(f"✓ 已删除列: {column_name}")
                    removed_columns.append(column_name)
                except SQLAlchemyError as e:
                    logger.error(f"✗ 删除列 {column_name} 失败: {str(e)}")
            else:
                logger.info(f"○ 列 {column_name} 不存在，跳过")
    
    logger.info("")
    logger.info("=" * 60)
    if removed_columns:
        logger.info(f"成功移除 {len(removed_columns)} 个列: {', '.join(removed_columns)}")
    else:
        logger.info("没有需要移除的列")
    logger.info("=" * 60)
    
    return len(removed_columns) > 0

if __name__ == "__main__":
    try:
        remove_template_columns()
        print("\n✓ 操作完成")
    except Exception as e:
        logger.error(f"执行失败: {str(e)}", exc_info=True)
        sys.exit(1)

