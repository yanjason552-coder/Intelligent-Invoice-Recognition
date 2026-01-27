"""
删除所有发票相关数据的简化脚本
可以直接通过环境变量或命令行参数指定数据库连接信息
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """获取数据库连接URL"""
    # 方式1: 从环境变量获取完整的 DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # 确保使用 psycopg 驱动
        if database_url.startswith('postgresql://') and '+psycopg' not in database_url:
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        return database_url
    
    # 方式2: 从单独的环境变量构建连接字符串
    postgres_server = os.getenv('POSTGRES_SERVER', 'localhost')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    postgres_user = os.getenv('POSTGRES_USER', 'postgres')
    postgres_password = os.getenv('POSTGRES_PASSWORD', '')
    postgres_db = os.getenv('POSTGRES_DB', 'app')
    
    if postgres_user and postgres_db:
        return f"postgresql+psycopg://{postgres_user}:{postgres_password}@{postgres_server}:{postgres_port}/{postgres_db}"
    
    # 方式3: 从命令行参数获取
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    raise ValueError(
        "请提供数据库连接信息。方式1: 设置 DATABASE_URL 环境变量\n"
        "方式2: 设置 POSTGRES_SERVER, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB 环境变量\n"
        "方式3: 作为命令行参数传入: python delete_all_invoices_simple.py 'postgresql+psycopg://user:pass@host:port/db'"
    )

def delete_all_invoices():
    """删除所有发票相关数据"""
    logger.info("=" * 60)
    logger.info("开始删除所有发票相关数据")
    logger.info("=" * 60)
    
    try:
        database_url = get_database_url()
        logger.info(f"数据库连接: {database_url.split('@')[1] if '@' in database_url else '已配置'}")
        
        # 创建数据库引擎
        engine = create_engine(database_url, echo=False)
        
        with engine.begin() as connection:
            # 1. 删除发票行项目
            logger.info("正在删除发票行项目 (invoice_item)...")
            result = connection.execute(text("DELETE FROM invoice_item"))
            item_count = result.rowcount
            logger.info(f"✓ 已删除 {item_count} 条发票行项目记录")
            
            # 2. 删除识别结果
            logger.info("正在删除识别结果 (recognition_result)...")
            result = connection.execute(text("DELETE FROM recognition_result"))
            result_count = result.rowcount
            logger.info(f"✓ 已删除 {result_count} 条识别结果记录")
            
            # 3. 删除识别字段
            logger.info("正在删除识别字段 (recognition_field)...")
            result = connection.execute(text("DELETE FROM recognition_field"))
            field_count = result.rowcount
            logger.info(f"✓ 已删除 {field_count} 条识别字段记录")
            
            # 4. 删除模式验证记录
            logger.info("正在删除模式验证记录 (schema_validation_record)...")
            result = connection.execute(text("DELETE FROM schema_validation_record"))
            validation_count = result.rowcount
            logger.info(f"✓ 已删除 {validation_count} 条模式验证记录")
            
            # 5. 删除审核记录
            logger.info("正在删除审核记录 (review_record)...")
            result = connection.execute(text("DELETE FROM review_record"))
            review_count = result.rowcount
            logger.info(f"✓ 已删除 {review_count} 条审核记录")
            
            # 6. 删除识别任务
            logger.info("正在删除识别任务 (recognition_task)...")
            result = connection.execute(text("DELETE FROM recognition_task"))
            task_count = result.rowcount
            logger.info(f"✓ 已删除 {task_count} 条识别任务记录")
            
            # 7. 删除发票
            logger.info("正在删除发票 (invoice)...")
            result = connection.execute(text("DELETE FROM invoice"))
            invoice_count = result.rowcount
            logger.info(f"✓ 已删除 {invoice_count} 条发票记录")
            
            # 8. 删除发票文件
            logger.info("正在删除发票文件 (invoice_file)...")
            result = connection.execute(text("DELETE FROM invoice_file"))
            file_count = result.rowcount
            logger.info(f"✓ 已删除 {file_count} 条发票文件记录")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("删除完成！")
            logger.info("=" * 60)
            logger.info(f"总计删除:")
            logger.info(f"  - 发票行项目: {item_count} 条")
            logger.info(f"  - 识别结果: {result_count} 条")
            logger.info(f"  - 识别字段: {field_count} 条")
            logger.info(f"  - 模式验证记录: {validation_count} 条")
            logger.info(f"  - 审核记录: {review_count} 条")
            logger.info(f"  - 识别任务: {task_count} 条")
            logger.info(f"  - 发票: {invoice_count} 条")
            logger.info(f"  - 发票文件: {file_count} 条")
            logger.info("=" * 60)
            
            return True
            
    except ValueError as e:
        logger.error(str(e))
        return False
    except SQLAlchemyError as e:
        logger.error(f"删除过程中发生数据库错误: {str(e)}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"删除过程中发生未知错误: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    # 确认删除
    print("\n" + "=" * 60)
    print("警告：此操作将删除数据库中所有发票相关数据！")
    print("=" * 60)
    confirm = input("\n确认删除？请输入 'yes' 继续: ")
    
    if confirm.lower() == 'yes':
        try:
            success = delete_all_invoices()
            if success:
                logger.info("\n✓ 所有发票数据已成功删除")
            else:
                logger.error("\n✗ 删除过程中发生错误，请检查日志")
                sys.exit(1)
        except KeyboardInterrupt:
            logger.warning("\n操作已取消")
            sys.exit(1)
        except Exception as e:
            logger.error(f"\n✗ 发生错误: {str(e)}", exc_info=True)
            sys.exit(1)
    else:
        logger.info("操作已取消")
        sys.exit(0)

