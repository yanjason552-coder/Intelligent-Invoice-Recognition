"""
统计数据API
"""
from typing import Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from sqlmodel import select

from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import SessionDep, CurrentUser
from app.models.models_invoice import Invoice, InvoiceFile, RecognitionTask, Template

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

