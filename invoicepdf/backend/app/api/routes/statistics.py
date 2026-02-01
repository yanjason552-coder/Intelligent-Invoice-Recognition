"""
统计数据API
"""
from typing import Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from sqlmodel import select

from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import SessionDep, CurrentUser
from app.models.models_invoice import Invoice, InvoiceFile, RecognitionTask, RecognitionResult, Template, LLMConfig
from uuid import UUID

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/overview")
def get_statistics_overview(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    获取统计数据概览
    """
    try:
        # 总发票数
        total_invoices = session.exec(
            select(func.count()).select_from(Invoice)
        ).one()
        
        # 今日新增发票
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_invoices = session.exec(
            select(func.count()).select_from(Invoice).where(
                Invoice.create_time >= today_start
            )
        ).one()
        
        # 识别任务总数
        total_tasks = session.exec(
            select(func.count()).select_from(RecognitionTask)
        ).one()
        
        # 今日识别任务
        today_tasks = session.exec(
            select(func.count()).select_from(RecognitionTask).where(
                RecognitionTask.create_time >= today_start
            )
        ).one()
        
        # 识别任务状态统计
        pending_tasks = session.exec(
            select(func.count()).select_from(RecognitionTask).where(
                RecognitionTask.status == "pending"
            )
        ).one()
        
        processing_tasks = session.exec(
            select(func.count()).select_from(RecognitionTask).where(
                RecognitionTask.status == "processing"
            )
        ).one()
        
        completed_tasks = session.exec(
            select(func.count()).select_from(RecognitionTask).where(
                RecognitionTask.status == "completed"
            )
        ).one()
        
        failed_tasks = session.exec(
            select(func.count()).select_from(RecognitionTask).where(
                RecognitionTask.status == "failed"
            )
        ).one()
        
        # 发票审核状态统计
        pending_review = session.exec(
            select(func.count()).select_from(Invoice).where(
                Invoice.review_status == "pending"
            )
        ).one()
        
        approved_review = session.exec(
            select(func.count()).select_from(Invoice).where(
                Invoice.review_status == "approved"
            )
        ).one()
        
        rejected_review = session.exec(
            select(func.count()).select_from(Invoice).where(
                Invoice.review_status == "rejected"
            )
        ).one()
        
        # 模板总数
        total_templates = session.exec(
            select(func.count()).select_from(Template)
        ).one()
        
        # 活跃模板（status='enabled'）
        active_templates = session.exec(
            select(func.count()).select_from(Template).where(
                Template.status == "enabled"
            )
        ).one()
        
        # 发票总金额统计
        total_amount_result = session.exec(
            select(func.sum(Invoice.total_amount)).select_from(Invoice)
        ).one()
        total_amount = float(total_amount_result) if total_amount_result else 0.0
        
        # 今日发票总金额
        today_amount_result = session.exec(
            select(func.sum(Invoice.total_amount)).select_from(Invoice).where(
                Invoice.create_time >= today_start
            )
        ).one()
        today_amount = float(today_amount_result) if today_amount_result else 0.0
        
        # 最近7天的数据趋势
        seven_days_ago = today_start - timedelta(days=7)
        daily_stats = []
        for i in range(7):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_invoices = session.exec(
                select(func.count()).select_from(Invoice).where(
                    and_(
                        Invoice.create_time >= day_start,
                        Invoice.create_time < day_end
                    )
                )
            ).one()
            
            day_amount_result = session.exec(
                select(func.sum(Invoice.total_amount)).select_from(Invoice).where(
                    and_(
                        Invoice.create_time >= day_start,
                        Invoice.create_time < day_end
                    )
                )
            ).one()
            day_amount = float(day_amount_result) if day_amount_result else 0.0
            
            daily_stats.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "invoices": day_invoices,
                "amount": day_amount
            })
        
        daily_stats.reverse()  # 从最早到最新
        
        return {
            "overview": {
                "total_invoices": total_invoices,
                "today_invoices": today_invoices,
                "total_tasks": total_tasks,
                "today_tasks": today_tasks,
                "total_templates": total_templates,
                "active_templates": active_templates,
                "total_amount": total_amount,
                "today_amount": today_amount
            },
            "task_status": {
                "pending": pending_tasks,
                "processing": processing_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks
            },
            "review_status": {
                "pending": pending_review,
                "approved": approved_review,
                "rejected": rejected_review
            },
            "daily_stats": daily_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.get("/trends")
def get_statistics_trends(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    days: int = 30,
) -> Any:
    """
    获取统计数据趋势（最近N天）
    """
    try:
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)
        
        trends = []
        current_date = start_date
        
        while current_date < end_date:
            next_date = current_date + timedelta(days=1)
            
            # 该日期的发票数
            day_invoices = session.exec(
                select(func.count()).select_from(Invoice).where(
                    and_(
                        Invoice.create_time >= current_date,
                        Invoice.create_time < next_date
                    )
                )
            ).one()
            
            # 该日期的发票金额
            day_amount_result = session.exec(
                select(func.sum(Invoice.total_amount)).select_from(Invoice).where(
                    and_(
                        Invoice.create_time >= current_date,
                        Invoice.create_time < next_date
                    )
                )
            ).one()
            day_amount = float(day_amount_result) if day_amount_result else 0.0
            
            # 该日期的识别任务数
            day_tasks = session.exec(
                select(func.count()).select_from(RecognitionTask).where(
                    and_(
                        RecognitionTask.create_time >= current_date,
                        RecognitionTask.create_time < next_date
                    )
                )
            ).one()
            
            trends.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "invoices": day_invoices,
                "amount": day_amount,
                "tasks": day_tasks
            })
            
            current_date = next_date
        
        return {
            "trends": trends,
            "days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势数据失败: {str(e)}")


@router.get("/recognition-status")
def get_recognition_status(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    检查发票识别情况
    """
    try:
        # 1. 识别任务状态统计
        task_status_counts = {}
        for status in ["pending", "processing", "completed", "failed"]:
            count = session.exec(
                select(func.count()).select_from(RecognitionTask)
                .where(RecognitionTask.status == status)
            ).one()
            task_status_counts[status] = count
        
        total_tasks = sum(task_status_counts.values())
        
        # 2. 检查长时间处理中的任务（超过30分钟）
        thirty_minutes_ago = datetime.now() - timedelta(minutes=30)
        stuck_tasks_query = select(RecognitionTask).where(
            and_(
                RecognitionTask.status == "processing",
                RecognitionTask.start_time < thirty_minutes_ago
            )
        ).order_by(RecognitionTask.start_time).limit(10)
        stuck_tasks = session.exec(stuck_tasks_query).all()
        
        stuck_tasks_list = []
        for task in stuck_tasks:
            duration_minutes = (datetime.now() - task.start_time).total_seconds() / 60 if task.start_time else 0
            stuck_tasks_list.append({
                "id": str(task.id),
                "task_no": task.task_no,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "duration_minutes": round(duration_minutes, 1),
                "error_message": task.error_message
            })
        
        # 3. 最近失败的任务
        failed_tasks_query = select(RecognitionTask).where(
            RecognitionTask.status == "failed"
        ).order_by(RecognitionTask.create_time.desc()).limit(10)
        failed_tasks = session.exec(failed_tasks_query).all()
        
        failed_tasks_list = []
        for task in failed_tasks:
            failed_tasks_list.append({
                "id": str(task.id),
                "task_no": task.task_no,
                "create_time": task.create_time.isoformat() if task.create_time else None,
                "error_code": task.error_code,
                "error_message": task.error_message
            })
        
        # 4. 识别结果统计
        result_total = session.exec(
            select(func.count()).select_from(RecognitionResult)
        ).one()
        
        result_status_counts = {}
        for status in ["success", "failed", "partial"]:
            count = session.exec(
                select(func.count()).select_from(RecognitionResult)
                .where(RecognitionResult.status == status)
            ).one()
            result_status_counts[status] = count
        
        # 平均准确率和置信度
        avg_accuracy_result = session.exec(
            select(func.avg(RecognitionResult.accuracy))
            .select_from(RecognitionResult)
        ).one()
        avg_accuracy = float(avg_accuracy_result) if avg_accuracy_result else None
        
        avg_confidence_result = session.exec(
            select(func.avg(RecognitionResult.confidence))
            .select_from(RecognitionResult)
        ).one()
        avg_confidence = float(avg_confidence_result) if avg_confidence_result else None
        
        # 5. 最近完成的识别任务
        recent_completed_query = select(RecognitionTask).where(
            RecognitionTask.status == "completed"
        ).order_by(RecognitionTask.end_time.desc().nulls_last()).limit(5)
        recent_completed = session.exec(recent_completed_query).all()
        
        recent_completed_list = []
        for task in recent_completed:
            duration = (task.end_time - task.start_time).total_seconds() if task.start_time and task.end_time else None
            
            # 获取识别结果
            result = session.exec(
                select(RecognitionResult).where(RecognitionResult.task_id == task.id)
            ).first()
            
            task_info = {
                "task_no": task.task_no,
                "end_time": task.end_time.isoformat() if task.end_time else None,
                "duration_seconds": round(duration, 2) if duration else None
            }
            
            if result:
                task_info.update({
                    "accuracy": float(result.accuracy) if result.accuracy else None,
                    "confidence": float(result.confidence) if result.confidence else None,
                    "recognized_fields": result.recognized_fields,
                    "total_fields": result.total_fields
                })
            
            recent_completed_list.append(task_info)
        
        # 6. 模板提示词使用情况
        all_tasks = session.exec(select(RecognitionTask)).all()
        prompt_count = 0
        for task in all_tasks:
            if task.params and task.params.get("template_prompt"):
                prompt_value = task.params.get("template_prompt")
                if prompt_value and prompt_value != "null" and str(prompt_value).strip():
                    prompt_count += 1
        
        # 7. 模型配置使用情况
        model_usage = {}
        for task in all_tasks:
            if task.params and task.params.get("model_config_id"):
                try:
                    model_config = session.get(LLMConfig, UUID(task.params.get("model_config_id")))
                    if model_config:
                        model_name = model_config.name
                        if model_name not in model_usage:
                            model_usage[model_name] = {"total": 0, "completed": 0, "failed": 0}
                        model_usage[model_name]["total"] += 1
                        if task.status == "completed":
                            model_usage[model_name]["completed"] += 1
                        elif task.status == "failed":
                            model_usage[model_name]["failed"] += 1
                except Exception:
                    pass
        
        return {
            "task_status": {
                "pending": task_status_counts.get("pending", 0),
                "processing": task_status_counts.get("processing", 0),
                "completed": task_status_counts.get("completed", 0),
                "failed": task_status_counts.get("failed", 0),
                "total": total_tasks
            },
            "stuck_tasks": stuck_tasks_list,
            "failed_tasks": failed_tasks_list,
            "result_status": {
                "total": result_total,
                "success": result_status_counts.get("success", 0),
                "failed": result_status_counts.get("failed", 0),
                "partial": result_status_counts.get("partial", 0),
                "avg_accuracy": avg_accuracy,
                "avg_confidence": avg_confidence
            },
            "recent_completed": recent_completed_list,
            "prompt_usage": {
                "tasks_with_prompt": prompt_count,
                "total_tasks": total_tasks,
                "usage_rate": prompt_count / total_tasks if total_tasks > 0 else 0
            },
            "model_usage": model_usage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取识别情况失败: {str(e)}")

