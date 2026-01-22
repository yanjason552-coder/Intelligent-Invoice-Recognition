"""
Material Density API - 材质密度对照表接口
"""

import uuid
from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select, or_, text

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    UnifiedRequest,
    UnifiedResponse
)
from app.models import (
    MaterialDensity, MaterialDensityCreate, MaterialDensityUpdate, MaterialDensityResponse, MaterialDensityQuery
)
from app.utils import get_server_datetime

router = APIRouter(prefix="/material-density", tags=["material-density"])


@router.post("/unified", response_model=UnifiedResponse)
def unified_material_density_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的material_density操作API"""
    try:
        action = request.action.lower()
        
        if action == "create":
            return _handle_unified_create(request, session, current_user)
        elif action == "delete":
            return _handle_unified_delete(request, session, current_user)
        elif action == "list":
            return _handle_unified_list(request, session, current_user)
        elif action == "read":
            return _handle_unified_read(request, session, current_user)
        elif action == "save":
            return _handle_unified_save(request, session, current_user)
        elif action == "batch_save":
            return _handle_unified_batch_save(request, session, current_user)
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
        # 创建空的 MaterialDensity 对象
        material_density = MaterialDensity(
            materialDensityId='new-'+str(uuid.uuid4()),
            materialCode="",
            materialDesc="",
            density=0.0,
            densityUnitId="",
            remark="",
            approveStatus="N",
            approver="",
            approveDate=None,
            creator=current_user.email,
            createDate=datetime.now(),
            modifierLast=None,
            modifyDateLast=None
        )
        
        # 构建返回数据
        result_data = material_density.model_dump()
        
        return UnifiedResponse(
            success=True,
            code=201,
            data=result_data,
            message="空的material_density对象创建成功"
        )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"创建失败: {str(e)}",
            error_code="CREATE_FAILED"
        )


def _handle_unified_delete(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理删除操作"""
    try:
        request_data = request.data or {}
        material_density_id = request_data.get("materialDensityId") or request_data.get("material_density_id")
        
        if not material_density_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少materialDensityId参数",
                error_code="MISSING_ID"
            )
        
        # 查找要删除的记录
        statement = select(MaterialDensity).where(MaterialDensity.materialDensityId == material_density_id)
        material_density = session.exec(statement).first()
        
        if not material_density:
            return UnifiedResponse(
                success=False,
                code=404,
                message="记录不存在",
                error_code="NOT_FOUND"
            )
        
        # 执行删除
        session.delete(material_density)
        session.commit()
        
        return UnifiedResponse(
            success=True,
            code=200,
            message="删除成功"
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
        # 获取分页参数 - 处理data为None的情况
        request_data = request.data or {}
        page = request_data.get("page", 1)
        limit = request_data.get("limit", 20)
        filters = request_data.get("filters", {})
        
        # 构建查询语句
        statement = select(MaterialDensity)
        
        # 应用过滤条件
        if filters:
            if filters.get("materialCode"):
                statement = statement.where(MaterialDensity.materialCode.contains(filters["materialCode"]))
            if filters.get("materialDesc"):
                statement = statement.where(MaterialDensity.materialDesc.contains(filters["materialDesc"]))
            if filters.get("densityUnitId"):
                statement = statement.where(MaterialDensity.densityUnitId == filters["densityUnitId"])
            if filters.get("approveStatus"):
                statement = statement.where(MaterialDensity.approveStatus == filters["approveStatus"])
            if filters.get("creator"):
                statement = statement.where(MaterialDensity.creator == filters["creator"])
        
        # 获取总数
        count_statement = select(func.count(MaterialDensity.materialDensityId))
        if filters:
            if filters.get("materialCode"):
                count_statement = count_statement.where(MaterialDensity.materialCode.contains(filters["materialCode"]))
            if filters.get("materialDesc"):
                count_statement = count_statement.where(MaterialDensity.materialDesc.contains(filters["materialDesc"]))
            if filters.get("densityUnitId"):
                count_statement = count_statement.where(MaterialDensity.densityUnitId == filters["densityUnitId"])
            if filters.get("approveStatus"):
                count_statement = count_statement.where(MaterialDensity.approveStatus == filters["approveStatus"])
            if filters.get("creator"):
                count_statement = count_statement.where(MaterialDensity.creator == filters["creator"])
        
        total = session.exec(count_statement).first()
        
        # 应用分页
        offset = (page - 1) * limit
        statement = statement.offset(offset).limit(limit)
        
        # 执行查询
        items = session.exec(statement).all()
        
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


def _handle_unified_read(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理读取操作"""
    try:
        request_data = request.data or {}
        material_density_id = request_data.get("materialDensityId") or request_data.get("material_density_id")
        
        if not material_density_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少materialDensityId参数",
                error_code="MISSING_ID"
            )
        
        # 查找记录
        statement = select(MaterialDensity).where(MaterialDensity.materialDensityId == material_density_id)
        material_density = session.exec(statement).first()
        
        if not material_density:
            return UnifiedResponse(
                success=False,
                code=404,
                message="记录不存在",
                error_code="NOT_FOUND"
            )
        
        # 转换为字典
        result_data = material_density.model_dump()
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=result_data,
            message="查询成功"
        )
        
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"查询失败: {str(e)}",
            error_code="QUERY_FAILED"
        )


def _handle_unified_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理保存操作"""
    try:
        material_density_data = request.data or {}
        
        # 检查是创建还是更新
        material_density_id = material_density_data.get("materialDensityId") or material_density_data.get("material_density_id")
        
        if not material_density_id or material_density_id.startswith('new-'):
            # 创建新记录
            material_density_id = str(uuid.uuid4())
            material_density_data["materialDensityId"] = material_density_id
            material_density_data["creator"] = current_user.email
            material_density_data["createDate"] = get_server_datetime()
            
            material_density = MaterialDensity(**material_density_data)
            session.add(material_density)
            message = "创建成功"
        else:
            # 更新现有记录
            statement = select(MaterialDensity).where(MaterialDensity.materialDensityId == material_density_id)
            material_density = session.exec(statement).first()
            
            if not material_density:
                return UnifiedResponse(
                    success=False,
                    code=404,
                    message="记录不存在",
                    error_code="NOT_FOUND"
                )
            
            # 更新字段
            for key, value in material_density_data.items():
                if hasattr(material_density, key) and key not in ["materialDensityId", "creator", "createDate"]:
                    setattr(material_density, key, value)
            
            material_density.modifierLast = current_user.email
            material_density.modifyDateLast = get_server_datetime()
            message = "更新成功"
        
        session.commit()
        session.refresh(material_density)
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=material_density.model_dump(),
            message=message
        )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"保存失败: {str(e)}",
            error_code="SAVE_FAILED"
        )


def _handle_unified_batch_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理批量保存操作"""
    try:
        batch_data = request.data or []
        
        if not isinstance(batch_data, list):
            return UnifiedResponse(
                success=False,
                code=400,
                message="批量数据必须是数组格式",
                error_code="INVALID_BATCH_DATA"
            )
        
        if not batch_data:
            return UnifiedResponse(
                success=False,
                code=400,
                message="没有提供要处理的数据",
                error_code="NO_DATA"
            )
        
        results = []
        success_count = 0
        error_count = 0
        
        for i, item_data in enumerate(batch_data):
            try:
                # 检查是创建还是更新
                material_density_id = item_data.get("materialDensityId") or item_data.get("material_density_id")
                
                if not material_density_id or material_density_id.startswith('new-'):
                    # 创建新记录
                    material_density_id = str(uuid.uuid4())
                    item_data["materialDensityId"] = material_density_id
                    item_data["creator"] = current_user.email
                    item_data["createDate"] = get_server_datetime()
                    
                    material_density = MaterialDensity(**item_data)
                    session.add(material_density)
                else:
                    # 更新现有记录
                    statement = select(MaterialDensity).where(MaterialDensity.materialDensityId == material_density_id)
                    material_density = session.exec(statement).first()
                    
                    if material_density:
                        # 更新字段
                        for key, value in item_data.items():
                            if hasattr(material_density, key) and key not in ["materialDensityId", "creator", "createDate"]:
                                setattr(material_density, key, value)
                        
                        material_density.modifierLast = current_user.email
                        material_density.modifyDateLast = get_server_datetime()
                    else:
                        # 记录不存在，创建新记录
                        item_data["materialDensityId"] = material_density_id
                        item_data["creator"] = current_user.email
                        item_data["createDate"] = get_server_datetime()
                        
                        material_density = MaterialDensity(**item_data)
                        session.add(material_density)
                
                session.commit()
                success_count += 1
                results.append({
                    "success": True,
                    "material_density_id": material_density_id,
                    "message": "处理成功"
                })
                
            except Exception as e:
                session.rollback()
                error_count += 1
                results.append({
                    "success": False,
                    "material_density_id": item_data.get("materialDensityId", "unknown"),
                    "error": str(e)
                })
        
        return UnifiedResponse(
            success=True,
            code=200,
            data={
                "results": results,
                "summary": {
                    "total": len(batch_data),
                    "success": success_count,
                    "error": error_count
                }
            },
            message=f"批量处理完成：成功 {success_count} 条，失败 {error_count} 条"
        )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"批量保存失败: {str(e)}",
            error_code="BATCH_SAVE_FAILED"
        ) 