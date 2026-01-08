"""
FeatureD API - 处理 feature_d 表的操作
"""

import uuid
from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select, or_

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    UnifiedRequest,
    UnifiedResponse
)
from app.models import (
    FeatureD, FeatureDCreate, FeatureDUpdate, FeatureDResponse
)

router = APIRouter(prefix="/feature-d", tags=["feature-d"])


@router.post("/unified", response_model=UnifiedResponse)
def unified_feature_d_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的feature_d操作API"""
    try:
        action = request.action.lower()
        
        if action == "create":
            return _handle_unified_create(request, session, current_user)
        elif action == "read":
            return _handle_unified_read(request, session, current_user)
        elif action == "update":
            return _handle_unified_update(request, session, current_user)
        elif action == "delete":
            return _handle_unified_delete(request, session, current_user)
        elif action == "list":
            return _handle_unified_list(request, session, current_user)
        elif action == "batch_create":
            return _handle_unified_batch_create(request, session, current_user)
        elif action == "batch_update":
            return _handle_unified_batch_update(request, session, current_user)
        elif action == "batch_delete":
            return _handle_unified_batch_delete(request, session, current_user)
        else:
            return UnifiedResponse(
                success=False,
                code=400,
                message=f"不支持的操作: {action}",
                error_code="UNSUPPORTED_ACTION"
            )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"操作失败: {str(e)}",
            error_code="OPERATION_FAILED"
        )


def _handle_unified_create(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理创建操作"""
    try:
        data = request.data or {}
        
        # 创建 FeatureD 对象
        feature_d_data = FeatureDCreate(
            featureId=data.get("featureId", ""),
            featureValue=data.get("featureValue", ""),
            featureValueDesc=data.get("featureValueDesc", ""),
            remark=data.get("remark"),
            creator=current_user.email,
            approve_date=data.get("approve_date")
        )
        
        # 创建 FeatureD 实体
        feature_d = FeatureD(
            feature_d_id=str(uuid.uuid4()),
            **feature_d_data.model_dump()
        )
        
        session.add(feature_d)
        session.commit()
        session.refresh(feature_d)
        
        return UnifiedResponse(
            success=True,
            code=201,
            data={"featureDId": feature_d.featureDId},
            message="feature_d创建成功"
        )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"创建失败: {str(e)}",
            error_code="CREATE_FAILED"
        )


def _handle_unified_read(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理读取操作"""
    try:
        data = request.data or {}
        feature_d_id = data.get("feature_d_id")
        
        if not feature_d_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少feature_d_id参数",
                error_code="MISSING_FEATURE_D_ID"
            )
        
        # 使用 SQLModel 查询
        feature_d = session.get(FeatureD, feature_d_id)
        
        if not feature_d:
            return UnifiedResponse(
                success=False,
                code=404,
                message="feature_d不存在",
                error_code="FEATURE_D_NOT_FOUND"
            )
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=feature_d.model_dump(),
            message="查询成功"
        )
        
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"查询失败: {str(e)}",
            error_code="READ_FAILED"
        )


def _handle_unified_update(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理更新操作"""
    try:
        data = request.data or {}
        feature_d_id = data.get("featureDId")
        
        if not feature_d_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少featureDId参数",
                error_code="MISSING_FEATURE_D_ID"
            )
        
        # 获取现有记录
        feature_d = session.get(FeatureD, feature_d_id)
        if not feature_d:
            return UnifiedResponse(
                success=False,
                code=404,
                message="feature_d不存在",
                error_code="FEATURE_D_NOT_FOUND"
            )
        
        # 更新字段
        update_data = FeatureDUpdate(**data)
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(feature_d, field, value)
        
        session.add(feature_d)
        session.commit()
        session.refresh(feature_d)
        
        return UnifiedResponse(
            success=True,
            code=200,
            data={"featureDId": feature_d_id},
            message="feature_d更新成功"
        )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"更新失败: {str(e)}",
            error_code="UPDATE_FAILED"
        )


def _handle_unified_delete(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理删除操作"""
    try:
        data = request.data or {}
        feature_d_id = data.get("featureDId")
        
        if not feature_d_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少featureDId参数",
                error_code="MISSING_FEATURE_D_ID"
            )
        
        # 获取记录
        feature_d = session.get(FeatureD, feature_d_id)
        if not feature_d:
            return UnifiedResponse(
                success=False,
                code=404,
                message="feature_d不存在",
                error_code="FEATURE_D_NOT_FOUND"
            )
        
        session.delete(feature_d)
        session.commit()
        
        return UnifiedResponse(
            success=True,
            code=200,
            data={"featureDId": feature_d_id},
            message="feature_d删除成功"
        )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"删除失败: {str(e)}",
            error_code="DELETE_FAILED"
        )


def _handle_unified_list(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理列表查询操作"""
    try:
        # 构建基础查询
        query = select(FeatureD)
        
        # 应用过滤条件
        if request.filters:
            for field, value in request.filters.items():
                if value and hasattr(FeatureD, field):
                    # 使用 ILIKE 进行模糊查询
                    query = query.where(getattr(FeatureD, field).ilike(f"%{value}%"))
        
        # 应用搜索条件
        if request.search:
            search_term = f"%{request.search}%"
            query = query.where(
                or_(
                    FeatureD.featureValue.ilike(search_term),
                    FeatureD.featureValueDesc.ilike(search_term),
                    FeatureD.remark.ilike(search_term)
                )
            )
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = session.exec(count_query).one()
        
        # 应用排序
        if request.sort:
            for field, direction in request.sort.items():
                if hasattr(FeatureD, field):
                    if direction.lower() == "desc":
                        query = query.order_by(getattr(FeatureD, field).desc())
                    else:
                        query = query.order_by(getattr(FeatureD, field).asc())
        else:
            query = query.order_by(FeatureD.featureDId.asc())
        
        # 应用分页
        page = request.page or 1
        limit = request.limit or 20
        skip = (page - 1) * limit
        
        query = query.offset(skip).limit(limit)
        
        # 执行查询
        items = session.exec(query).all()
        
        # 转换为字典列表
        items_dict = [item.model_dump() for item in items]
        
        # 构建分页信息
        total_pages = (total + limit - 1) // limit
        pagination = {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=items_dict,
            pagination=pagination,
            message=f"查询成功，共{total}条记录"
        )
        
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"查询失败: {str(e)}",
            error_code="QUERY_FAILED"
        )


def _handle_unified_batch_create(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理批量创建操作"""
    try:
        data = request.data or {}
        items = data.get("items", [])
        
        if not items:
            return UnifiedResponse(
                success=False,
                code=400,
                message="没有提供要创建的数据",
                error_code="NO_ITEMS_PROVIDED"
            )
        
        created_ids = []
        
        for item_data in items:
            # 创建 FeatureD 对象
            feature_d_data = FeatureDCreate(**item_data)
            
            # 创建 FeatureD 实体
            feature_d = FeatureD(
                featureDId=str(uuid.uuid4()),
                **feature_d_data.model_dump()
            )
            
            session.add(feature_d)
            created_ids.append(feature_d.featureDId)
        
        session.commit()
        
        return UnifiedResponse(
            success=True,
            code=201,
            data={"created_ids": created_ids},
            message=f"批量创建成功，共创建{len(created_ids)}条记录"
        )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"批量创建失败: {str(e)}",
            error_code="BATCH_CREATE_FAILED"
        )


def _handle_unified_batch_update(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理批量更新操作"""
    try:
        data = request.data or {}
        items = data.get("items", [])
        
        if not items:
            return UnifiedResponse(
                success=False,
                code=400,
                message="没有提供要更新的数据",
                error_code="NO_ITEMS_PROVIDED"
            )
        
        updated_ids = []
        
        for item_data in items:
            feature_d_id = item_data.get("featureDId")
            if not feature_d_id:
                continue
                
            # 获取现有记录
            feature_d = session.get(FeatureD, feature_d_id)
            if not feature_d:
                continue
            
            # 更新字段
            update_data = FeatureDUpdate(**item_data)
            for field, value in update_data.model_dump(exclude_unset=True).items():
                if field != "featureDId":  # 跳过ID字段
                    setattr(feature_d, field, value)
            
            session.add(feature_d)
            updated_ids.append(feature_d_id)
        
        session.commit()
        
        return UnifiedResponse(
            success=True,
            code=200,
            data={"updated_ids": updated_ids},
            message=f"批量更新成功，共更新{len(updated_ids)}条记录"
        )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"批量更新失败: {str(e)}",
            error_code="BATCH_UPDATE_FAILED"
        )


def _handle_unified_batch_delete(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理批量删除操作"""
    try:
        data = request.data or {}
        feature_d_ids = data.get("featureDIds", [])
        
        if not feature_d_ids:
            return UnifiedResponse(
                success=False,
                code=400,
                message="没有提供要删除的ID列表",
                error_code="NO_IDS_PROVIDED"
            )
        
        deleted_ids = []
        
        for feature_d_id in feature_d_ids:
            # 获取记录
            feature_d = session.get(FeatureD, feature_d_id)
            if feature_d:
                session.delete(feature_d)
                deleted_ids.append(feature_d_id)
        
        session.commit()
        
        return UnifiedResponse(
            success=True,
            code=200,
            data={"deleted_ids": deleted_ids},
            message=f"批量删除成功，共删除{len(deleted_ids)}条记录"
        )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"批量删除失败: {str(e)}",
            error_code="BATCH_DELETE_FAILED"
        ) 