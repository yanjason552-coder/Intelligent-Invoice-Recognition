"""
删除状态为"失败"和"识别中"的识别任务
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session, select
from sqlalchemy import text
from app.core.db import engine
from app.models.models_invoice import RecognitionTask, RecognitionResult

def delete_failed_and_processing_tasks():
    """删除状态为failed和processing的识别任务"""
    print("=" * 80)
    print("删除状态为'失败'和'识别中'的识别任务")
    print("=" * 80)
    print()
    
    with Session(engine) as session:
        # 1. 统计要删除的任务数量
        print("【1. 统计要删除的任务】")
        print("-" * 80)
        
        failed_count = session.exec(
            select(RecognitionTask).where(RecognitionTask.status == "failed")
        ).all()
        processing_count = session.exec(
            select(RecognitionTask).where(RecognitionTask.status == "processing")
        ).all()
        
        failed_num = len(failed_count)
        processing_num = len(processing_count)
        total_num = failed_num + processing_num
        
        print(f"  失败状态的任务: {failed_num} 个")
        print(f"  识别中状态的任务: {processing_num} 个")
        print(f"  总计: {total_num} 个任务")
        print()
        
        if total_num == 0:
            print("没有需要删除的任务。")
            return
        
        # 2. 确认删除
        print("【2. 确认删除】")
        print("-" * 80)
        confirm_msg = input(f"确定要删除这 {total_num} 个任务吗？(yes/no): ")
        if confirm_msg.lower() != "yes":
            print("操作已取消。")
            return
        
        # 3. 获取要删除的任务ID列表
        print()
        print("【3. 开始删除】")
        print("-" * 80)
        
        tasks_to_delete = failed_count + processing_count
        task_ids = [task.id for task in tasks_to_delete]
        task_ids_str = [str(tid) for tid in task_ids]
        placeholders = ','.join([f"'{tid}'" for tid in task_ids_str])
        
        deleted_results = 0
        deleted_validations = 0
        deleted_tasks = 0
        
        try:
            # 3.1 删除关联的识别结果（使用SQL直接删除）
            print("  正在删除关联的识别结果...")
            try:
                delete_results_sql = text(f"DELETE FROM recognition_result WHERE task_id IN ({placeholders})")
                result = session.exec(delete_results_sql)
                deleted_results = result.rowcount if hasattr(result, 'rowcount') else 0
                session.commit()
                
                if deleted_results > 0:
                    print(f"  ✓ 已删除 {deleted_results} 个识别结果")
                else:
                    print(f"  ✓ 没有找到需要删除的识别结果")
            except Exception as e:
                print(f"  ⚠ 删除识别结果时出错: {str(e)}")
                session.rollback()
            
            # 3.2 删除关联的Schema验证记录（如果表存在，使用SQL直接删除）
            print("  正在删除关联的Schema验证记录...")
            try:
                delete_validations_sql = text(f"DELETE FROM schema_validation_record WHERE task_id IN ({placeholders})")
                result = session.exec(delete_validations_sql)
                deleted_validations = result.rowcount if hasattr(result, 'rowcount') else 0
                session.commit()
                
                if deleted_validations > 0:
                    print(f"  ✓ 已删除 {deleted_validations} 个Schema验证记录")
                else:
                    print(f"  ✓ 没有找到需要删除的Schema验证记录")
            except Exception as e:
                # 如果表不存在或其他错误，记录警告但继续执行
                error_msg = str(e)
                if "does not exist" in error_msg or "UndefinedTable" in error_msg:
                    print(f"  ⚠ schema_validation_record 表不存在，跳过删除Schema验证记录")
                else:
                    print(f"  ⚠ 删除Schema验证记录时出错: {error_msg}")
                session.rollback()
            
            # 3.3 删除识别任务（使用SQL直接删除）
            print("  正在删除识别任务...")
            delete_tasks_sql = text(f"DELETE FROM recognition_task WHERE id IN ({placeholders})")
            result = session.exec(delete_tasks_sql)
            deleted_tasks = result.rowcount if hasattr(result, 'rowcount') else 0
            session.commit()
            
            print(f"  ✓ 已删除 {deleted_tasks} 个识别任务")
            
            print()
            print("【4. 删除完成】")
            print("-" * 80)
            print(f"  删除的识别结果: {deleted_results} 个")
            print(f"  删除的Schema验证记录: {deleted_validations} 个")
            print(f"  删除的识别任务: {deleted_tasks} 个")
            print(f"  总计删除: {deleted_results + deleted_validations + deleted_tasks} 条记录")
            
        except Exception as e:
            session.rollback()
            print()
            print("【错误】")
            print("-" * 80)
            print(f"删除过程中发生错误: {str(e)}")
            print("已回滚所有更改。")
            raise


if __name__ == "__main__":
    try:
        delete_failed_and_processing_tasks()
    except KeyboardInterrupt:
        print("\n\n操作被用户中断。")
    except Exception as e:
        print(f"\n\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
