"""
快速修复：添加 sample_file_path 和 sample_file_type 列到 template 表
修复错误: column template.sample_file_path does not exist
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from app.core.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_add_sample_file_columns():
    """添加缺失的 sample_file_path 和 sample_file_type 列"""
    try:
        inspector = inspect(engine)
        
        # 检查表是否存在
        if 'template' not in inspector.get_table_names():
            logger.error("template 表不存在！")
            return False
        
        # 获取现有列
        columns = {col['name']: col for col in inspector.get_columns('template')}
        logger.info(f"template 表现有列: {list(columns.keys())}")
        
        # 使用 begin() 来管理事务
        with engine.begin() as conn:
            # 添加 sample_file_path 列（如果不存在）
            if 'sample_file_path' not in columns:
                logger.info("添加 sample_file_path 列...")
                conn.execute(text("""
                    ALTER TABLE template 
                    ADD COLUMN sample_file_path VARCHAR(500)
                """))
                logger.info("✓ sample_file_path 列已添加")
            else:
                logger.info("sample_file_path 列已存在，跳过")
            
            # 添加 sample_file_type 列（如果不存在）
            if 'sample_file_type' not in columns:
                logger.info("添加 sample_file_type 列...")
                conn.execute(text("""
                    ALTER TABLE template 
                    ADD COLUMN sample_file_type VARCHAR(50)
                """))
                logger.info("✓ sample_file_type 列已添加")
            else:
                logger.info("sample_file_type 列已存在，跳过")
        
        logger.info("=" * 50)
        logger.info("修复完成！")
        logger.info("=" * 50)
        return True
            
    except Exception as e:
        logger.error(f"修复失败: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = fix_add_sample_file_columns()
    sys.exit(0 if success else 1)

