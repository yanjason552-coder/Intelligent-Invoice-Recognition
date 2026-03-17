"""
检查发票识别情况脚本
"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session, select, func, and_
from app.core.db import engine
from app.models.models_invoice import RecognitionTask, RecognitionResult, Invoice, InvoiceFile
from app.models.models_invoice import LLMConfig

def check_recognition_status():
    """检查识别任务状态"""
    print("=" * 80)
    print("发票识别情况检查")
    print("=" * 80)
    print()
    
    with Session(engine) as session:
        # 1. 统计各状态的任务数量
        print("【1. 识别任务状态统计】")
        print("-" * 80)
        
        status_counts = {}
        for status in ["pending", "processing", "completed", "failed"]:
            count = session.exec(
                select(func.count()).select_from(RecognitionTask).where(RecognitionTask.status == status)
            ).one()
            status_counts[status] = count
            status_label = {
                "pending": "待处理",
                "processing": "处理中",
                "completed": "已完成",
                "failed": "失败"
            }.get(status, status)
            print(f"  {status_label}: {count} 个任务")
        
        total = sum(status_counts.values())
        print(f"  总计: {total} 个任务")
        print()
        
        # 2. 检查长时间处理中的任务（超过30分钟）
        print("【2. 长时间处理中的任务检查】")
        print("-" * 80)
        thirty_minutes_ago = datetime.now() - timedelta(minutes=30)
        stuck_tasks = session.exec(
            select(RecognitionTask)
            .where(
                and_(
                    RecognitionTask.status == "processing",
                    RecognitionTask.start_time < thirty_minutes_ago
                )
            )
            .order_by(RecognitionTask.start_time)
        ).all()
        
        if stuck_tasks:
            print(f"  发现 {len(stuck_tasks)} 个可能卡住的任务（处理时间超过30分钟）:")
            for task in stuck_tasks[:10]:  # 只显示前10个
                duration = (datetime.now() - task.start_time).total_seconds() / 60 if task.start_time else 0
                print(f"    - 任务ID: {task.id}")
                print(f"      任务编号: {task.task_no}")
                print(f"      开始时间: {task.start_time}")
                print(f"      已处理时长: {duration:.1f} 分钟")
                if task.error_message:
                    print(f"      错误信息: {task.error_message}")
                print()
        else:
            print("  ✓ 没有发现长时间处理中的任务")
        print()
        
        # 3. 最近失败的任务
        print("【3. 最近失败的任务（最近10个）】")
        print("-" * 80)
        failed_tasks = session.exec(
            select(RecognitionTask)
            .where(RecognitionTask.status == "failed")
            .order_by(RecognitionTask.create_time.desc())
            .limit(10)
        ).all()
        
        if failed_tasks:
            for task in failed_tasks:
                print(f"  任务ID: {task.id}")
                print(f"  任务编号: {task.task_no}")
                print(f"  创建时间: {task.create_time}")
                print(f"  错误代码: {task.error_code or 'N/A'}")
                print(f"  错误信息: {task.error_message or 'N/A'}")
                print()
        else:
            print("  ✓ 没有失败的任务")
        print()
        
        # 4. 识别结果统计
        print("【4. 识别结果统计】")
        print("-" * 80)
        result_count = session.exec(select(func.count()).select_from(RecognitionResult)).one()
        print(f"  识别结果总数: {result_count}")
        
        if result_count > 0:
            # 统计各状态的结果
            for status in ["success", "failed", "partial"]:
                count = session.exec(
                    select(func.count()).select_from(RecognitionResult)
                    .where(RecognitionResult.status == status)
                ).one()
                status_label = {
                    "success": "成功",
                    "failed": "失败",
                    "partial": "部分成功"
                }.get(status, status)
                print(f"  {status_label}: {count} 个结果")
            
            # 平均准确率
            avg_accuracy = session.exec(
                select(func.avg(RecognitionResult.accuracy))
                .select_from(RecognitionResult)
            ).one()
            if avg_accuracy:
                print(f"  平均准确率: {avg_accuracy:.2%}")
            
            # 平均置信度
            avg_confidence = session.exec(
                select(func.avg(RecognitionResult.confidence))
                .select_from(RecognitionResult)
            ).one()
            if avg_confidence:
                print(f"  平均置信度: {avg_confidence:.2%}")
        print()
        
        # 5. 最近完成的识别任务
        print("【5. 最近完成的识别任务（最近5个）】")
        print("-" * 80)
        recent_completed = session.exec(
            select(RecognitionTask)
            .where(RecognitionTask.status == "completed")
            .order_by(RecognitionTask.end_time.desc())
            .limit(5)
        ).all()
        
        if recent_completed:
            for task in recent_completed:
                duration = (task.end_time - task.start_time).total_seconds() if task.start_time and task.end_time else 0
                print(f"  任务编号: {task.task_no}")
                print(f"  完成时间: {task.end_time}")
                print(f"  耗时: {duration:.2f} 秒")
                
                # 获取识别结果
                result = session.exec(
                    select(RecognitionResult).where(RecognitionResult.task_id == task.id)
                ).first()
                if result:
                    print(f"  准确率: {result.accuracy:.2%}")
                    print(f"  置信度: {result.confidence:.2%}")
                    print(f"  识别字段数: {result.recognized_fields}/{result.total_fields}")
                print()
        else:
            print("  - 暂无已完成的识别任务")
        print()
        
        # 6. 检查模板提示词使用情况
        print("【6. 模板提示词使用情况】")
        print("-" * 80)
        tasks_with_prompt = session.exec(
            select(RecognitionTask)
            .where(RecognitionTask.params.isnot(None))
        ).all()
        
        prompt_count = 0
        for task in tasks_with_prompt:
            if task.params and task.params.get("template_prompt"):
                prompt_count += 1
        
        print(f"  使用模板提示词的任务数: {prompt_count}")
        print(f"  总任务数: {total}")
        if total > 0:
            print(f"  提示词使用率: {prompt_count/total:.2%}")
        print()
        
        # 7. 模型配置使用情况
        print("【7. 模型配置使用情况】")
        print("-" * 80)
        model_usage = {}
        for task in session.exec(select(RecognitionTask)).all():
            if task.params and task.params.get("model_config_id"):
                model_id = str(task.params.get("model_config_id"))
                model_config = session.get(LLMConfig, task.params.get("model_config_id"))
                if model_config:
                    model_name = model_config.name
                    if model_name not in model_usage:
                        model_usage[model_name] = {"total": 0, "completed": 0, "failed": 0}
                    model_usage[model_name]["total"] += 1
                    if task.status == "completed":
                        model_usage[model_name]["completed"] += 1
                    elif task.status == "failed":
                        model_usage[model_name]["failed"] += 1
        
        if model_usage:
            for model_name, stats in model_usage.items():
                print(f"  {model_name}:")
                print(f"    总任务数: {stats['total']}")
                print(f"    已完成: {stats['completed']}")
                print(f"    失败: {stats['failed']}")
                if stats['total'] > 0:
                    success_rate = stats['completed'] / stats['total'] * 100
                    print(f"    成功率: {success_rate:.1f}%")
                print()
        else:
            print("  - 暂无模型使用记录")
        print()
        
        print("=" * 80)
        print("检查完成")
        print("=" * 80)

if __name__ == "__main__":
    try:
        check_recognition_status()
    except Exception as e:
        print(f"检查失败: {str(e)}")
        import traceback
        traceback.print_exc()

