"""
孔位类记录API路由
"""
from typing import Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func, and_
from datetime import datetime
import logging

from app.api.deps import SessionDep, CurrentUser
from app.models import UserCompany
from app.models import Message
from app.models.models_invoice import (
    HolePositionRecord, HolePositionItem,
    HolePositionRecordCreate, HolePositionRecordUpdate, HolePositionRecordResponse,
    HolePositionItemUpdate, HolePositionItemsBatchUpdate,
    InvoiceFile
)
from sqlmodel import SQLModel, Field

router = APIRouter(prefix="/hole-position", tags=["hole-position"])

logger = logging.getLogger(__name__)


def get_user_company_ids_hole_position(session: SessionDep, user_id: UUID) -> list[UUID]:
    """
    获取用户关联的所有公司ID列表
    """
    from app.models import UserCompany
    user_companies = session.exec(
        select(UserCompany).where(UserCompany.user_id == user_id)
    ).all()
    return [uc.company_id for uc in user_companies]


def check_hole_position_permission(record: HolePositionRecord, current_user: CurrentUser, session: SessionDep) -> bool:
    """
    检查孔位类记录访问权限
    规则：
    1. 超级用户可以访问所有记录
    2. 普通用户只能访问自己关联公司的记录
    """
    # 超级用户可以访问所有记录
    if current_user.is_superuser:
        return True
    
    # 如果记录没有公司ID，允许访问（向后兼容）
    if not record.company_id:
        return True
    
    # 获取用户关联的公司ID列表
    user_company_ids = get_user_company_ids_hole_position(session, current_user.id)
    
    # 如果用户没有关联任何公司，则无权访问
    if not user_company_ids:
        return False
    
    # 检查记录的公司ID是否在用户的公司列表中
    return record.company_id in user_company_ids


def add_company_filter_hole_position(statement, current_user: CurrentUser, session: SessionDep, conditions=None):
    """
    根据用户的公司ID列表过滤孔位类记录查询
    规则：
    1. 超级用户可以查看所有记录
    2. 普通用户只能查看自己关联公司的记录
    3. 如果用户没有关联任何公司，则不展示任何记录
    """
    if conditions is None:
        conditions = []
    
    # 如果不是超级用户，添加公司过滤条件
    if not current_user.is_superuser:
        user_company_ids = get_user_company_ids_hole_position(session, current_user.id)
        if user_company_ids:
            # 用户有关联公司，只能查看这些公司的记录
            conditions.append(HolePositionRecord.company_id.in_(user_company_ids))
        else:
            # 如果用户没有关联任何公司，返回空结果（使用一个永远为False的条件）
            conditions.append(HolePositionRecord.id.is_(None))
    
    if conditions:
        statement = statement.where(and_(*conditions))
    
    return statement, conditions


@router.post("/", response_model=HolePositionRecordResponse)
def create_hole_position_record(
    *,
    session: SessionDep,
    record_in: HolePositionRecordCreate,
    current_user: CurrentUser
) -> Any:
    """
    创建孔位类记录
    """
    try:
        # 验证文件是否存在
        file = session.get(InvoiceFile, record_in.file_id)
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 生成记录编号
        record_no = f"HP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}"
        
        # 创建记录
        record = HolePositionRecord(
            record_no=record_no,
            file_id=record_in.file_id,
            doc_type=record_in.doc_type,
            form_title=record_in.form_title,
            drawing_no=record_in.drawing_no,
            part_name=record_in.part_name,
            part_no=record_in.part_no,
            date=record_in.date,
            inspector_name=record_in.inspector_name,
            overall_result=record_in.overall_result,
            remarks=record_in.remarks,
            template_name=record_in.template_name,
            template_version=record_in.template_version,
            model_name=record_in.model_name,
            creator_id=current_user.id,
            company_id=current_user.company_id,
            recognition_status="pending"
        )
        
        session.add(record)
        session.commit()
        session.refresh(record)
        
        # 如果有行项目，创建行项目
        if record_in.items:
            for item_data in record_in.items:
                item = HolePositionItem(
                    record_id=record.id,
                    item_no=item_data.item_no,
                    inspection_item=item_data.inspection_item,
                    spec_requirement=item_data.spec_requirement,
                    actual_value=item_data.actual_value,
                    actual=item_data.actual,
                    range_min=item_data.range_min,
                    range_max=item_data.range_max,
                    range_value=item_data.range_value,
                    judgement=item_data.judgement,
                    notes=item_data.notes
                )
                session.add(item)
        
        session.commit()
        session.refresh(record)
        
        return HolePositionRecordResponse(
            id=record.id,
            record_no=record.record_no,
            doc_type=record.doc_type,
            form_title=record.form_title,
            drawing_no=record.drawing_no,
            part_name=record.part_name,
            part_no=record.part_no,
            date=record.date,
            inspector_name=record.inspector_name,
            overall_result=record.overall_result,
            remarks=record.remarks,
            file_id=record.file_id,
            template_name=record.template_name,
            template_version=record.template_version,
            model_name=record.model_name,
            recognition_accuracy=record.recognition_accuracy,
            recognition_status=record.recognition_status,
            review_status=record.review_status,
            reviewer_id=record.reviewer_id,
            review_time=record.review_time,
            review_comment=record.review_comment,
            creator_id=record.creator_id,
            company_id=record.company_id,
            create_time=record.create_time,
            update_time=record.update_time
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建孔位类记录失败: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建记录失败: {str(e)}")


@router.get("/query")
def query_hole_position_records(
    *,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    record_no: str | None = None,
    model_name: str | None = None,
    template_name: str | None = None,
    review_status: str | None = None,
    recognition_status: str | None = None,
    current_user: CurrentUser
) -> Any:
    """
    查询孔位类记录列表（支持按模型和模板筛选）
    """
    try:
        statement = select(HolePositionRecord)
        
        # 构建查询条件
        conditions = []
        if record_no:
            conditions.append(HolePositionRecord.record_no.contains(record_no))
        if model_name:
            conditions.append(HolePositionRecord.model_name == model_name)
        if template_name:
            conditions.append(HolePositionRecord.template_name == template_name)
        if review_status:
            conditions.append(HolePositionRecord.review_status == review_status)
        if recognition_status:
            conditions.append(HolePositionRecord.recognition_status == recognition_status)
        
        # 添加公司过滤条件
        statement, conditions = add_company_filter_hole_position(statement, current_user, conditions)
        
        # 总数
        count_statement = select(func.count()).select_from(HolePositionRecord)
        if conditions:
            count_statement = count_statement.where(and_(*conditions))
        total = session.exec(count_statement).one()
        
        # 分页查询
        records = session.exec(
            statement.order_by(HolePositionRecord.create_time.desc()).offset(skip).limit(limit)
        ).all()
        
        # 批量获取公司代码
        from app.models.models_company import Company
        company_ids = {r.company_id for r in records if r.company_id}
        companies_dict = {}
        if company_ids:
            companies = session.exec(select(Company).where(Company.id.in_(list(company_ids)))).all()
            companies_dict = {c.id: c.code for c in companies}
        
        return {
            "data": [
                {
                    **HolePositionRecordResponse(
                        id=r.id,
                        record_no=r.record_no,
                        doc_type=r.doc_type,
                        form_title=r.form_title,
                        drawing_no=r.drawing_no,
                        part_name=r.part_name,
                        part_no=r.part_no,
                        date=r.date,
                        inspector_name=r.inspector_name,
                        overall_result=r.overall_result,
                        remarks=r.remarks,
                        file_id=r.file_id,
                        template_name=r.template_name,
                        template_version=r.template_version,
                        model_name=r.model_name,
                        recognition_accuracy=r.recognition_accuracy,
                        recognition_status=r.recognition_status,
                        review_status=r.review_status,
                        reviewer_id=r.reviewer_id,
                        review_time=r.review_time,
                        review_comment=r.review_comment,
                        creator_id=r.creator_id,
                        company_id=r.company_id,
                        create_time=r.create_time,
                        update_time=r.update_time
                    ).model_dump(),
                    "company_code": companies_dict.get(r.company_id) if r.company_id else None
                }
                for r in records
            ],
            "count": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"查询孔位类记录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{record_id}", response_model=HolePositionRecordResponse)
def get_hole_position_record(
    *,
    session: SessionDep,
    record_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    获取孔位类记录详情
    """
    record = session.get(HolePositionRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 检查权限
    if not check_hole_position_permission(record, current_user, session):
        raise HTTPException(status_code=403, detail="无权访问此记录")
    
    return HolePositionRecordResponse(
        id=record.id,
        record_no=record.record_no,
        doc_type=record.doc_type,
        form_title=record.form_title,
        drawing_no=record.drawing_no,
        part_name=record.part_name,
        part_no=record.part_no,
        date=record.date,
        inspector_name=record.inspector_name,
        overall_result=record.overall_result,
        remarks=record.remarks,
        file_id=record.file_id,
        template_name=record.template_name,
        template_version=record.template_version,
        model_name=record.model_name,
        recognition_accuracy=record.recognition_accuracy,
        recognition_status=record.recognition_status,
        review_status=record.review_status,
        reviewer_id=record.reviewer_id,
        review_time=record.review_time,
        review_comment=record.review_comment,
        creator_id=record.creator_id,
        company_id=record.company_id,
        create_time=record.create_time,
        update_time=record.update_time
    )


@router.patch("/{record_id}", response_model=HolePositionRecordResponse)
def update_hole_position_record(
    *,
    session: SessionDep,
    record_id: UUID,
    record_in: HolePositionRecordUpdate,
    current_user: CurrentUser
) -> Any:
    """
    更新孔位类记录
    """
    record = session.get(HolePositionRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 检查权限
    if not check_hole_position_permission(record, current_user, session):
        raise HTTPException(status_code=403, detail="无权访问此记录")
    
    # 更新字段
    update_data = record_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    
    record.update_time = datetime.now()
    session.add(record)
    session.commit()
    session.refresh(record)
    
    return HolePositionRecordResponse(
        id=record.id,
        record_no=record.record_no,
        doc_type=record.doc_type,
        form_title=record.form_title,
        drawing_no=record.drawing_no,
        part_name=record.part_name,
        part_no=record.part_no,
        date=record.date,
        inspector_name=record.inspector_name,
        overall_result=record.overall_result,
        remarks=record.remarks,
        file_id=record.file_id,
        template_name=record.template_name,
        template_version=record.template_version,
        model_name=record.model_name,
        recognition_accuracy=record.recognition_accuracy,
        recognition_status=record.recognition_status,
        review_status=record.review_status,
        reviewer_id=record.reviewer_id,
        review_time=record.review_time,
        review_comment=record.review_comment,
        creator_id=record.creator_id,
        company_id=record.company_id,
        create_time=record.create_time,
        update_time=record.update_time
    )


@router.get("/{record_id}/items")
def get_hole_position_items(
    *,
    session: SessionDep,
    record_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    获取孔位类记录的行项目列表
    """
    # 验证记录是否存在
    record = session.get(HolePositionRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 检查权限
    if not check_hole_position_permission(record, current_user, session):
        raise HTTPException(status_code=403, detail="无权访问此记录")
    
    # 查询该记录的所有行项目
    items = session.exec(
        select(HolePositionItem).where(HolePositionItem.record_id == record_id).order_by(HolePositionItem.item_no)
    ).all()
    
    return {
        "data": [
            {
                "item_no": item.item_no,
                "inspection_item": item.inspection_item,
                "spec_requirement": item.spec_requirement,
                "actual_value": item.actual_value,
                "actual": item.actual,
                "range_min": item.range_min,
                "range_max": item.range_max,
                "range_value": item.range_value,
                "judgement": item.judgement,
                "notes": item.notes
            }
            for item in items
        ],
        "count": len(items)
    }


@router.put("/{record_id}/items", response_model=Message)
def update_hole_position_items(
    *,
    session: SessionDep,
    record_id: UUID,
    items_in: HolePositionItemsBatchUpdate,
    current_user: CurrentUser
) -> Any:
    """
    批量更新孔位类记录的行项目
    """
    # 验证记录是否存在
    record = session.get(HolePositionRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 检查权限
    if not check_hole_position_permission(record, current_user, session):
        raise HTTPException(status_code=403, detail="无权访问此记录")
    
    # 获取当前所有行项目
    existing_items = session.exec(
        select(HolePositionItem).where(HolePositionItem.record_id == record_id).order_by(HolePositionItem.item_no)
    ).all()
    
    # 创建item_no到行项目的映射
    item_map = {(item.record_id, item.item_no): item for item in existing_items}
    
    # 更新或创建行项目
    for item_update in items_in.items:
        if item_update.item_no is None:
            continue
        key = (record_id, item_update.item_no)
        if key in item_map:
            # 更新现有行项目
            item = item_map[key]
            update_data = item_update.model_dump(exclude_unset=True, exclude={'item_no'})
            for field, value in update_data.items():
                setattr(item, field, value)
            item.update_time = datetime.now()
            session.add(item)
        else:
            # 创建新行项目
            new_item = HolePositionItem(
                record_id=record_id,
                item_no=item_update.item_no,
                **item_update.model_dump(exclude_unset=True, exclude={'item_no'})
            )
            session.add(new_item)
    
    session.commit()
    return Message(message="行项目更新成功")


@router.get("/review/pending")
def get_pending_reviews(
    *,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    model_name: str | None = None,
    template_name: str | None = None,
    current_user: CurrentUser
) -> Any:
    """
    获取待审核孔位类记录列表（支持按模型和模板筛选）
    """
    try:
        statement = select(HolePositionRecord).where(HolePositionRecord.review_status == "pending")
        
        # 构建查询条件
        conditions = [HolePositionRecord.review_status == "pending"]
        if model_name:
            conditions.append(HolePositionRecord.model_name == model_name)
        if template_name:
            conditions.append(HolePositionRecord.template_name == template_name)
        
        # 添加公司过滤条件
        statement, conditions = add_company_filter_hole_position(statement, current_user, conditions)
        
        # 总数
        count_statement = select(func.count()).select_from(HolePositionRecord).where(and_(*conditions))
        total = session.exec(count_statement).one()
        
        # 分页查询
        records = session.exec(
            statement.order_by(HolePositionRecord.create_time.desc()).offset(skip).limit(limit)
        ).all()
        
        # 批量获取公司代码
        from app.models.models_company import Company
        company_ids = {r.company_id for r in records if r.company_id}
        companies_dict = {}
        if company_ids:
            companies = session.exec(select(Company).where(Company.id.in_(list(company_ids)))).all()
            companies_dict = {c.id: c.code for c in companies}
        
        return {
            "data": [
                {
                    **HolePositionRecordResponse(
                        id=r.id,
                        record_no=r.record_no,
                        doc_type=r.doc_type,
                        form_title=r.form_title,
                        drawing_no=r.drawing_no,
                        part_name=r.part_name,
                        part_no=r.part_no,
                        date=r.date,
                        inspector_name=r.inspector_name,
                        overall_result=r.overall_result,
                        remarks=r.remarks,
                        file_id=r.file_id,
                        template_name=r.template_name,
                        template_version=r.template_version,
                        model_name=r.model_name,
                        recognition_accuracy=r.recognition_accuracy,
                        recognition_status=r.recognition_status,
                        review_status=r.review_status,
                        reviewer_id=r.reviewer_id,
                        review_time=r.review_time,
                        review_comment=r.review_comment,
                        creator_id=r.creator_id,
                        company_id=r.company_id,
                        create_time=r.create_time,
                        update_time=r.update_time
                    ).model_dump(),
                    "company_code": companies_dict.get(r.company_id) if r.company_id else None
                }
                for r in records
            ],
            "count": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"获取待审核记录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/{record_id}/review/approve", response_model=Message)
def approve_hole_position_record(
    *,
    session: SessionDep,
    record_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    审核通过孔位类记录
    """
    record = session.get(HolePositionRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 检查权限
    if not check_hole_position_permission(record, current_user, session):
        raise HTTPException(status_code=403, detail="无权访问此记录")
    
    record.review_status = "approved"
    record.reviewer_id = current_user.id
    record.review_time = datetime.now()
    record.update_time = datetime.now()
    
    session.add(record)
    session.commit()
    
    return Message(message="审核通过成功")


class RejectRequest(SQLModel):
    comment: str = Field(..., description="审核意见（必填）")


@router.post("/{record_id}/review/reject", response_model=Message)
def reject_hole_position_record(
    *,
    session: SessionDep,
    record_id: UUID,
    reject_request: RejectRequest,
    current_user: CurrentUser
) -> Any:
    """
    审核拒绝孔位类记录
    """
    record = session.get(HolePositionRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 检查权限
    if not check_hole_position_permission(record, current_user, session):
        raise HTTPException(status_code=403, detail="无权访问此记录")
    
    record.review_status = "rejected"
    record.reviewer_id = current_user.id
    record.review_time = datetime.now()
    record.review_comment = reject_request.comment
    record.update_time = datetime.now()
    
    session.add(record)
    session.commit()
    
    return Message(message="审核拒绝成功")

