"""
全面清理和修复模板相关数据库结构
1. 检查并修复 template 表结构
2. 清理旧的不兼容字段
3. 确保表结构与新模型一致
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from app.core.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_and_fix_template():
    """清理和修复模板表结构"""
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # 检查表是否存在
            if 'template' not in inspector.get_table_names():
                logger.info("template 表不存在，无需修复")
                return
            
            # 获取现有列
            columns = {col['name']: col for col in inspector.get_columns('template')}
            logger.info(f"template 表现有列: {list(columns.keys())}")
            
            # 1. 修复 template_type 列
            if 'template_type' not in columns:
                if 'type' in columns:
                    logger.info("将 type 列重命名为 template_type")
                    conn.execute(text("ALTER TABLE template RENAME COLUMN type TO template_type"))
                else:
                    logger.info("添加 template_type 列")
                    conn.execute(text("""
                        ALTER TABLE template 
                        ADD COLUMN template_type VARCHAR(50) NOT NULL DEFAULT '其他'
                    """))
                conn.commit()
                logger.info("✓ template_type 列已修复")
            
            # 2. 删除旧的、不需要的列（如果存在）
            old_columns_to_remove = [
                'template_file_path',
                'sample_image_path', 
                'training_samples',
                'last_training_time',
                'version'  # 旧版本字段，现在使用 template_version 表
            ]
            
            for col_name in old_columns_to_remove:
                if col_name in columns:
                    logger.info(f"删除旧列: {col_name}")
                    try:
                        conn.execute(text(f"ALTER TABLE template DROP COLUMN IF EXISTS {col_name}"))
                        conn.commit()
                        logger.info(f"✓ 已删除列: {col_name}")
                    except Exception as e:
                        logger.warning(f"删除列 {col_name} 时出错: {str(e)}")
            
            # 3. 确保必需的列存在
            required_columns = {
                'current_version_id': 'UUID',
                'update_time': 'TIMESTAMP'
            }
            
            for col_name, col_type in required_columns.items():
                if col_name not in columns:
                    logger.info(f"添加必需列: {col_name}")
                    try:
                        if col_type == 'UUID':
                            conn.execute(text(f"""
                                ALTER TABLE template 
                                ADD COLUMN {col_name} UUID
                            """))
                        elif col_type == 'TIMESTAMP':
                            conn.execute(text(f"""
                                ALTER TABLE template 
                                ADD COLUMN {col_name} TIMESTAMP
                            """))
                        conn.commit()
                        logger.info(f"✓ 已添加列: {col_name}")
                    except Exception as e:
                        logger.warning(f"添加列 {col_name} 时出错: {str(e)}")
            
            # 4. 修复 status 列的默认值（如果存在旧值）
            try:
                conn.execute(text("""
                    UPDATE template 
                    SET status = 'enabled' 
                    WHERE status = 'active' OR status IS NULL
                """))
                conn.commit()
                logger.info("✓ 已修复 status 列的默认值")
            except Exception as e:
                logger.warning(f"修复 status 时出错: {str(e)}")
            
            # 5. 确保索引存在
            indexes = {idx['name']: idx for idx in inspector.get_indexes('template')}
            
            if 'ix_template_template_type' not in indexes:
                logger.info("创建 template_type 索引")
                try:
                    conn.execute(text("""
                        CREATE INDEX ix_template_template_type 
                        ON template(template_type)
                    """))
                    conn.commit()
                    logger.info("✓ 已创建 template_type 索引")
                except Exception as e:
                    logger.warning(f"创建索引时出错: {str(e)}")
            
            # 6. 检查 template_field 表（如果有旧字段）
            if 'template_field' in inspector.get_table_names():
                field_columns = {col['name']: col for col in inspector.get_columns('template_field')}
                
                # 检查是否有旧的 field_code 或 field_type 列
                if 'field_code' in field_columns and 'field_key' not in field_columns:
                    logger.info("将 field_code 列重命名为 field_key")
                    try:
                        conn.execute(text("ALTER TABLE template_field RENAME COLUMN field_code TO field_key"))
                        conn.commit()
                        logger.info("✓ 已重命名 field_code -> field_key")
                    except Exception as e:
                        logger.warning(f"重命名 field_code 时出错: {str(e)}")
                
                if 'field_type' in field_columns and 'data_type' not in field_columns:
                    logger.info("将 field_type 列重命名为 data_type")
                    try:
                        conn.execute(text("ALTER TABLE template_field RENAME COLUMN field_type TO data_type"))
                        conn.commit()
                        logger.info("✓ 已重命名 field_type -> data_type")
                    except Exception as e:
                        logger.warning(f"重命名 field_type 时出错: {str(e)}")
            
            logger.info("=" * 60)
            logger.info("模板表结构修复完成！")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"修复失败: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("清理和修复模板相关数据库结构")
    print("=" * 60)
    print()
    print("此脚本将：")
    print("1. 修复 template_type 列（重命名 type 或添加）")
    print("2. 删除旧的、不需要的列")
    print("3. 添加必需的列")
    print("4. 修复索引")
    print("5. 修复 template_field 表的字段名")
    print()
    
    confirm = input("确认执行此操作？(输入 'YES' 确认): ")
    if confirm != "YES":
        print("操作已取消")
        sys.exit(0)
    
    cleanup_and_fix_template()

