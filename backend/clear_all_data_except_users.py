"""
清空数据库中除用户表之外的所有数据

此脚本会：
1. 保留 user 表的所有数据
2. 清空所有其他业务表的数据
3. 按照外键依赖顺序删除，避免外键约束错误
4. 使用事务确保数据一致性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from app.core.db import engine
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 需要保留的表（用户相关）
PRESERVED_TABLES = {
    'user',
    'alembic_version'  # Alembic 版本表也需要保留
}

# 需要清空的表，按照外键依赖顺序（从子表到父表）
# 注意：这个顺序很重要，需要先删除有外键依赖的表
TABLES_TO_CLEAR = [
    # 识别相关（最深层依赖）
    'recognition_field',
    'review_record',
    'recognition_result',
    'recognition_task',
    
    # 模板相关
    'template_field',
    'template_version',
    'template',
    
    # 票据相关
    'invoice',
    'invoice_file',
    
    # 配置相关
    'model_config',
    'output_schema',
    'llm_config',
    'ocr_config',
    'recognition_rule',
    
    # 业务数据表
    'production_order_routing',
    'production_order_produce',
    'production_order_d',
    'production_order',
    
    'nesting_layout_sd',
    'nesting_layout_d',
    'nesting_layout',
    
    'material_lot_feature',
    'material_lot',
    'inventory',
    
    'operation',
    'surface_technology_d',
    'surface_technology',
    
    'material_density',
    'material_d',
    'material',
    'material_class_d',
    'material_class',
    
    'feature_d',
    'feature',
    
    'sales_order_doc_d_feature',
    'sales_order_doc_d',
    
    # 基础表
    'item',
]

def get_all_tables():
    """获取数据库中所有表名"""
    inspector = inspect(engine)
    return inspector.get_table_names()

def clear_table_data(table_name: str, connection) -> bool:
    """清空指定表的数据"""
    try:
        # 使用 TRUNCATE CASCADE 快速清空表并处理外键约束
        # 如果表有外键引用，使用 DELETE FROM 更安全
        result = connection.execute(text(f'DELETE FROM "{table_name}"'))
        deleted_count = result.rowcount
        logger.info(f"✓ 清空表 {table_name}: 删除了 {deleted_count} 条记录")
        return True
    except SQLAlchemyError as e:
        logger.error(f"✗ 清空表 {table_name} 失败: {str(e)}")
        return False

def clear_all_data():
    """清空所有非用户表的数据"""
    logger.info("=" * 60)
    logger.info("开始清空数据库数据（保留用户表）")
    logger.info("=" * 60)
    
    # 获取所有表
    all_tables = get_all_tables()
    logger.info(f"数据库中共有 {len(all_tables)} 个表")
    
    # 过滤出需要清空的表
    tables_to_clear = [t for t in all_tables if t not in PRESERVED_TABLES]
    
    # 如果表在 TABLES_TO_CLEAR 中，使用指定顺序；否则按字母顺序
    ordered_tables = []
    for table in TABLES_TO_CLEAR:
        if table in tables_to_clear:
            ordered_tables.append(table)
    
    # 添加其他未在列表中的表
    for table in sorted(tables_to_clear):
        if table not in ordered_tables:
            ordered_tables.append(table)
    
    logger.info(f"需要清空的表: {len(ordered_tables)} 个")
    logger.info(f"保留的表: {PRESERVED_TABLES}")
    logger.info("")
    
    # 使用事务执行删除
    with engine.begin() as connection:
        success_count = 0
        fail_count = 0
        
        for table_name in ordered_tables:
            if clear_table_data(table_name, connection):
                success_count += 1
            else:
                fail_count += 1
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"清空完成: 成功 {success_count} 个表, 失败 {fail_count} 个表")
        logger.info("=" * 60)
        
        if fail_count > 0:
            logger.warning("部分表清空失败，请检查错误日志")
            return False
        else:
            logger.info("所有表已成功清空")
            return True

def main():
    """主函数"""
    try:
        # 确认操作
        print("\n" + "=" * 60)
        print("警告：此操作将清空数据库中除用户表外的所有数据！")
        print("=" * 60)
        print(f"数据库: {settings.SQLALCHEMY_DATABASE_URI.split('@')[-1] if '@' in settings.SQLALCHEMY_DATABASE_URI else 'N/A'}")
        print(f"保留的表: {', '.join(PRESERVED_TABLES)}")
        print("=" * 60)
        
        confirm = input("\n确认执行此操作？(输入 'YES' 确认): ")
        
        if confirm != 'YES':
            print("操作已取消")
            return
        
        # 执行清空
        success = clear_all_data()
        
        if success:
            print("\n✓ 数据清空成功完成")
        else:
            print("\n✗ 数据清空过程中出现错误，请检查日志")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

