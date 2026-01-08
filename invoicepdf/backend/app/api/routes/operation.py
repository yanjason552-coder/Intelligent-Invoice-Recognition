"""
Operation API - 使用 SQLModel 的版本
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
    Operation
)
from app.utils import get_server_datetime

router = APIRouter(prefix="/operation", tags=["operation"])

@router.post("/unified", response_model=UnifiedResponse)
def unified_operation_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的operation操作API"""
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
        operation = Operation(
            operationId='new-'+str(uuid.uuid4()),
            operationCode="",
            operationName="",
            operationDesc="",
            stdTactTime=0.0,
            unitIdTactTime="",
            processingMode="0",
            processingCatego="0",
            lossQuantity=0.0,
            unitIdLoss="",
            remark="",
            approveStatus="N",
            approver="",
            approveDate=None,
            creator=current_user.email,
            createDate=datetime.now(),
            modifierLast=None,
            modifyDateLast=None
        )
        
        result_data = operation.model_dump()
        
        return UnifiedResponse(
            success=True,
            code=201,
            data=result_data,
            message="空的operation对象创建成功"
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
        operation_id = request.data.get("operationId")
        if not operation_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少operationId参数",
                error_code="MISSING_ID"
            )
        
        statement = select(Operation).where(Operation.operationId == operation_id)
        operation = session.exec(statement).first()
        
        if not operation:
            return UnifiedResponse(
                success=False,
                code=404,
                message=f"未找到ID为{operation_id}的工艺方法",
                error_code="NOT_FOUND"
            )
        
        session.delete(operation)
        session.commit()
        
        return UnifiedResponse(
            success=True,
            code=200,
            message=f"工艺方法删除成功"
        )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"删除失败: {str(e)}",
            error_code="DELETE_FAILED"
        )

def _handle_unified_read(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理读取操作"""
    try:
        operation_id = request.data.get("operationId")
        if not operation_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少operationId参数",
                error_code="MISSING_ID"
            )
        
        statement = select(Operation).where(Operation.operationId == operation_id)
        operation = session.exec(statement).first()
        
        if not operation:
            return UnifiedResponse(
                success=False,
                code=404,
                message=f"未找到ID为{operation_id}的工艺方法",
                error_code="NOT_FOUND"
            )
        
        result_data = operation.model_dump()
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=result_data,
            message="工艺方法查询成功"
        )
        
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"查询失败: {str(e)}",
            error_code="QUERY_FAILED"
        )

def _handle_unified_list(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理列表查询操作"""
    try:
        page = request.page or 1
        limit = request.limit or 10
        filters = request.filters or {}
        search = request.search or {}
        
        sql_template = """
        SELECT 
            operation_id, operation_code, operation_name, operation_desc,
            std_tact_time, unit_id_tact_time, processing_mode, processing_catego,
            loss_quantity, unit_id_loss, remark, approve_status, approver,
            approve_date, creator, create_date, modifier_last, modify_date_last
        FROM operation
        WHERE 1=1
        -- {filter_conditions}
        -- {search_conditions}
        -- {order_conditions}
        -- {pagination_conditions}
        """
        
        filter_conditions = []
        if filters.get("operationCode"):
            filter_conditions.append(f"AND operation_code = '{filters['operationCode']}'")
        if filters.get("processingMode"):
            filter_conditions.append(f"AND processing_mode = '{filters['processingMode']}'")
        if filters.get("approveStatus"):
            filter_conditions.append(f"AND approve_status = '{filters['approveStatus']}'")
        
        search_conditions = []
        if search.get("keyword"):
            keyword = search["keyword"]
            search_conditions.append(f"AND (operation_code LIKE '%{keyword}%' OR operation_name LIKE '%{keyword}%')")
        
        order_conditions = ["create_date DESC"]
        offset = (page - 1) * limit
        pagination_conditions = f"LIMIT {limit} OFFSET {offset}"
        
        sql_query = sql_template.replace(
            "-- {filter_conditions}", '\n'.join(filter_conditions)
        ).replace(
            "-- {search_conditions}", '\n'.join(search_conditions)
        ).replace(
            "-- {order_conditions}", f"ORDER BY {', '.join(order_conditions)}"
        ).replace(
            "-- {pagination_conditions}", pagination_conditions
        )
        
        count_sql = f"""
        SELECT COUNT(*) as total
        FROM operation
        WHERE 1=1
        {' '.join(filter_conditions)}
        {' '.join(search_conditions)}
        """
        
        count_result = session.exec(text(count_sql)).one()
        total = count_result[0] if count_result else 0
        
        result = session.exec(text(sql_query))
        items = result.all()
        
        items_dict = []
        for row in items:
            item_dict = {
                "operationId": row[0], "operationCode": row[1], "operationName": row[2],
                "operationDesc": row[3], "stdTactTime": row[4], "unitIdTactTime": row[5],
                "processingMode": row[6], "processingCatego": row[7], "lossQuantity": row[8],
                "unitIdLoss": row[9], "remark": row[10], "approveStatus": row[11],
                "approver": row[12], "approveDate": row[13], "creator": row[14],
                "createDate": row[15], "modifierLast": row[16], "modifyDateLast": row[17]
            }
            items_dict.append(item_dict)
        
        total_pages = (total + limit - 1) // limit
        pagination = {
            "page": page, "limit": limit, "total": total,
            "total_pages": total_pages, "has_next": page < total_pages, "has_prev": page > 1
        }
        
        return UnifiedResponse(
            success=True, code=200, data=items_dict, pagination=pagination,
            message=f"查询成功，共{total}条记录"
        )
        
    except Exception as e:
        return UnifiedResponse(
            success=False, code=500, message=f"查询失败: {str(e)}", error_code="QUERY_FAILED"
        )

def _handle_unified_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理工艺方法的保存操作"""
    try:
        operation_data = request.data or {}
        operation_id = operation_data.get("operationId", "")
        is_new_record = operation_id.startswith("new-") if operation_id else True
        currentDateTime = get_server_datetime()
        
        if is_new_record:
            operation = Operation(
                operationId=str(uuid.uuid4()),
                operationCode=operation_data.get("operationCode", ""),
                operationName=operation_data.get("operationName", ""),
                operationDesc=operation_data.get("operationDesc", ""),
                stdTactTime=operation_data.get("stdTactTime", 0.0),
                unitIdTactTime=operation_data.get("unitIdTactTime", ""),
                processingMode=operation_data.get("processingMode", "0"),
                processingCatego=operation_data.get("processingCatego", "0"),
                lossQuantity=operation_data.get("lossQuantity", 0.0),
                unitIdLoss=operation_data.get("unitIdLoss", ""),
                remark=operation_data.get("remark", ""),
                approveStatus="N", approver="", approveDate=None,
                creator=current_user.email, createDate=currentDateTime,
                modifierLast=None, modifyDateLast=None
            )
            
            session.add(operation)
            session.commit()
            session.refresh(operation)
            
            return UnifiedResponse(
                success=True, code=201, data=operation.model_dump(),
                message="工艺方法创建成功"
            )
        else:
            statement = select(Operation).where(Operation.operationId == operation_id)
            operation = session.exec(statement).first()
            
            if not operation:
                return UnifiedResponse(
                    success=False, code=404,
                    message=f"未找到ID为{operation_id}的工艺方法", error_code="NOT_FOUND"
                )
            
            operation.operationCode = operation_data.get("operationCode", operation.operationCode)
            operation.operationName = operation_data.get("operationName", operation.operationName)
            operation.operationDesc = operation_data.get("operationDesc", operation.operationDesc)
            operation.stdTactTime = operation_data.get("stdTactTime", operation.stdTactTime)
            operation.unitIdTactTime = operation_data.get("unitIdTactTime", operation.unitIdTactTime)
            operation.processingMode = operation_data.get("processingMode", operation.processingMode)
            operation.processingCatego = operation_data.get("processingCatego", operation.processingCatego)
            operation.lossQuantity = operation_data.get("lossQuantity", operation.lossQuantity)
            operation.unitIdLoss = operation_data.get("unitIdLoss", operation.unitIdLoss)
            operation.remark = operation_data.get("remark", operation.remark)
            operation.modifierLast = current_user.email
            operation.modifyDateLast = currentDateTime
            
            session.add(operation)
            session.commit()
            session.refresh(operation)
            
            return UnifiedResponse(
                success=True, code=200, data=operation.model_dump(),
                message="工艺方法更新成功"
            )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False, code=500, message=f"保存失败: {str(e)}", error_code="SAVE_FAILED"
        ) 