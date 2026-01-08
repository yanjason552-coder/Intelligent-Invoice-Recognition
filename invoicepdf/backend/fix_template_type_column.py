"""
修复 template 表的 template_type 列
如果表存在但缺少 template_type 列，则添加该列
如果存在 type 列，则重命名为 template_type
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from app.core.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_template_type_column():
    """修复 template 表的 template_type 列"""
    try:
        with engine.connect() as conn:
            # 检查表是否存在
            inspector = inspect(engine)
            if 'template' not in inspector.get_table_names():
                logger.info("template 表不存在，无需修复")
                return
            
            # 获取现有列
            columns = [col['name'] for col in inspector.get_columns('template')]
            logger.info(f"template 表现有列: {columns}")
            
            # 检查是否有 template_type 列
            has_template_type = 'template_type' in columns
            has_type = 'type' in columns
            
            if has_template_type:
                logger.info("✓ template_type 列已存在，无需修复")
                return
            
            # 如果有 type 列，重命名为 template_type
            if has_type:
                logger.info("发现 type 列，准备重命名为 template_type")
                conn.execute(text("ALTER TABLE template RENAME COLUMN type TO template_type"))
                conn.commit()
                logger.info("✓ 已成功将 type 列重命名为 template_type")
            else:
                # 如果既没有 type 也没有 template_type，添加 template_type 列
                logger.info("添加 template_type 列")
                conn.execute(text("""
                    ALTER TABLE template 
                    ADD COLUMN template_type VARCHAR(50) NOT NULL DEFAULT '其他'
                """))
                conn.commit()
                logger.info("✓ 已成功添加 template_type 列")
            
            # 创建索引（如果不存在）
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_template_template_type 
                    ON template(template_type)
                """))
                conn.commit()
                logger.info("✓ 已创建 template_type 索引")
            except Exception as e:
                logger.warning(f"创建索引时出错（可能已存在）: {str(e)}")
            
            logger.info("=" * 60)
            logger.info("修复完成！")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"修复失败: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("修复 template 表的 template_type 列")
    print("=" * 60)
    print()
    
    confirm = input("确认执行此操作？(输入 'YES' 确认): ")
    if confirm != "YES":
        print("操作已取消")
        sys.exit(0)
    
    fix_template_type_column()

