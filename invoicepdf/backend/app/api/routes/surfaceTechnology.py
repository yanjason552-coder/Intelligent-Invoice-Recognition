"""
SurfaceTechnology API - 使用 SQLModel 的版本
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
    SurfaceTechnology
)
from app.utils import get_server_datetime

router = APIRouter(prefix="/surface-technology", tags=["surface-technology"])





@router.post("/unified", response_model=UnifiedResponse)
def unified_surface_technology_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的surface-technology操作API - 使用SQLModel版本"""
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
        # 创建空的 SurfaceTechnology 对象
        surface_technology = SurfaceTechnology(
            surfaceTechnologyId='new-'+str(uuid.uuid4()),
            surfaceCode="",
            surfaceDesc="",
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
        result_data = surface_technology.model_dump()
        
        return UnifiedResponse(
            success=True,
            code=201,
            data=result_data,
            message="空的surface-technology对象创建成功"
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
        data = request.data or {}
        surface_technology_id = data.get("surfaceTechnologyId")
        
        if not surface_technology_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少surfaceTechnologyId参数",
                error_code="MISSING_SURFACE_TECHNOLOGY_ID"
            )
        
        # 删除主表记录
        delete_main_sql = "DELETE FROM surface_technology WHERE surface_technology_id = :surface_technology_id"
        session.execute(text(delete_main_sql), {"surface_technology_id": surface_technology_id})
        
        session.commit()
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=None,
            message="surface-technology删除成功"
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
    """处理列表查询操作 - 使用 SQL 文本执行"""
    try:
        # SQL 查询模板
        sql_template = """
        SELECT 
            distinct surface_technology.*
        FROM surface_technology
        left join surface_technology_d on surface_technology.surface_technology_id = surface_technology_d.surface_id
        left join operation on surface_technology_d.operation_id = operation.operation_id
        WHERE 1=1
        -- {filter_conditions}
        -- {search_conditions}
        -- {order_conditions}
        -- {pagination_conditions}
        """
        
        # 构建过滤条件
        filter_conditions = []
        if request.filters:
            for field, value in request.filters.items():
                if value:
                    # 将字段名转换为数据库字段名（驼峰转下划线）
                    db_field = ''.join(['_' + c.lower() if c.isupper() else c for c in field]).lstrip('_')
                    filter_conditions.append(f"AND {db_field} ILIKE '%{value}%'")
        
        # 构建搜索条件
        search_conditions = []
        if request.search:
            search_term = f"%{request.search}%"
            search_conditions.append(f"""AND (
                surface_code ILIKE '{search_term}' OR 
                surface_desc ILIKE '{search_term}' OR 
                remark ILIKE '{search_term}'
            )""")
        
        # 构建排序条件
        order_conditions = []
        if request.sort:
            for field, direction in request.sort.items():
                # 将字段名转换为数据库字段名
                db_field = ''.join(['_' + c.lower() if c.isupper() else c for c in field]).lstrip('_')
                order_direction = "DESC" if direction.lower() == "desc" else "ASC"
                order_conditions.append(f"{db_field} {order_direction}")
        else:
            order_conditions.append("surface_code ASC")
        
        # 构建分页条件
        page = request.page or 1
        limit = request.limit or 20
        offset = (page - 1) * limit
        pagination_conditions = f"LIMIT {limit} OFFSET {offset}"
        
        # 替换 SQL 模板中的占位符
        sql_query = sql_template.replace(
            "-- {filter_conditions}", 
            '\n'.join(filter_conditions)
        ).replace(
            "-- {search_conditions}", 
            '\n'.join(search_conditions)
        ).replace(
            "-- {order_conditions}", 
            f"ORDER BY {', '.join(order_conditions)}"
        ).replace(
            "-- {pagination_conditions}", 
            pagination_conditions
        )
        
        # 构建计数查询
        count_sql = f"""
        SELECT COUNT(*) as total
        FROM surface_technology
        WHERE 1=1
        {' '.join(filter_conditions)}
        {' '.join(search_conditions)}
        """
        
        # 执行计数查询
        count_result = session.exec(text(count_sql)).one()
        total = count_result[0] if count_result else 0
        
        # 执行主查询
        result = session.exec(text(sql_query))
        items = result.all()
        
        # 转换为字典列表
        items_dict = []
        for row in items:
            item_dict = {
                "surfaceTechnologyId": row[0],
                "surfaceCode": row[1],
                "surfaceDesc": row[2],
                "remark": row[3],
                "approveStatus": row[4],
                "approver": row[5],
                "approveDate": row[6],
                "creator": row[7],
                "createDate": row[8],
                "modifierLast": row[9],
                "modifyDateLast": row[10],
                "surfaceTechnologyDList":[]
            }
            items_dict.append(item_dict)
        
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


def _handle_unified_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理表面要求的保存操作"""
    try:
        # 现在传入的是完整的SurfaceTechnology对象
        surface_technology_data = request.data or {}
        
        print(f"开始处理提交数据: surfaceTechnologyId={surface_technology_data.get('surfaceTechnologyId')}")
        
        # 开始处理数据
        surface_technology_id = None
        header_result = None

        currentDateTime = get_server_datetime()
        
        # 1. 处理表头数据
        if not surface_technology_data:
            return UnifiedResponse(
                success=False,
                code=400,
                message="没有提供要处理的数据",
                error_code="NO_DATA"
            )
        
        # 获取表头数据
        header_data = {
            "surfaceTechnologyId": surface_technology_data.get("surfaceTechnologyId"),
            "surfaceCode": surface_technology_data.get("surfaceCode"),
            "surfaceDesc": surface_technology_data.get("surfaceDesc"),
            "remark": surface_technology_data.get("remark"),
            "approveStatus": surface_technology_data.get("approveStatus")
        }
        
        # 检查是更新还是创建
        surface_technology_id = header_data.get("surfaceTechnologyId")
        
        # 调用 read 操作获取现有记录
        read_request = UnifiedRequest(
            action="read",
            module="surface-technology",
            data={"surfaceTechnologyId": surface_technology_id}
        )
        read_response = _handle_unified_read(read_request, session, current_user)
        
        # 判断 read_response 返回有 SurfaceTechnology 对象还是空值
        surface_technology_exists = read_response.success and read_response.data is not None
        
        # 根据 read_response.data 是否为空，执行新增或更改操作
        if surface_technology_exists and read_response.data:
            # 更新现有记录
            surface_technology = session.get(SurfaceTechnology, surface_technology_id)
            if surface_technology:
                # 更新现有表头
                for field, value in header_data.items():
                    if field != "surfaceTechnologyId" and hasattr(surface_technology, field):
                        setattr(surface_technology, field, value)
                
                # 更新修改信息
                surface_technology.modifierLast = current_user.email
                surface_technology.modifyDateLast = datetime.now()
                
                session.add(surface_technology)
                header_result = {"action": "updated", "surfaceTechnologyId": surface_technology_id}
        else:
            # 创建新记录
            surface_technology_create_data = {
                "surfaceCode": header_data.get("surfaceCode", ""),
                "surfaceDesc": header_data.get("surfaceDesc", ""),
                "remark": header_data.get("remark"),
                "approveStatus": header_data.get("approveStatus", "N")
            }
            
            # 使用传入的 surfaceTechnologyId 或生成新的
            new_surface_technology_id = str(uuid.uuid4())
            
            surface_technology = SurfaceTechnology(
                surfaceTechnologyId=new_surface_technology_id,
                **surface_technology_create_data,
                creator=current_user.email,
                createDate=currentDateTime,
                modifierLast=None,
                modifyDateLast=None
            )
            
            session.add(surface_technology)
            surface_technology_id = new_surface_technology_id
            header_result = {"action": "created", "surfaceTechnologyId": surface_technology_id}
        
        # 提交所有更改到数据库
        session.commit()
        
        # 重新获取完整的 SurfaceTechnology 对象
        surface_technology = session.get(SurfaceTechnology, surface_technology_id)
        
        # 构建返回数据
        result_data = surface_technology.model_dump()
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=result_data,
            message="数据提交成功"
        )
        
    except Exception as e:
        # 回滚事务
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"提交失败: {str(e)}",
            error_code="SUBMIT_FAILED"
        )


def _handle_unified_read(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理读取操作 - 根据主键获取单个 SurfaceTechnology 对象"""
    try:
        data = request.data or {}
        surface_technology_id = data.get("surfaceTechnologyId")
        
        if not surface_technology_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少surfaceTechnologyId参数",
                error_code="MISSING_SURFACE_TECHNOLOGY_ID"
            )
        
        # 直接查询数据库获取主表数据
        surface_technology = session.get(SurfaceTechnology, surface_technology_id)
        
        if not surface_technology:
            return UnifiedResponse(
                success=False,
                code=404,
                message=f"未找到 surfaceTechnologyId 为 {surface_technology_id} 的记录",
                error_code="SURFACE_TECHNOLOGY_NOT_FOUND"
            )
        
        # 查询并装配明细数据
        detail_sql = """
        SELECT surface_technology_d.*, 
        operation.operation_code, operation.operation_name
        FROM surface_technology_d
        LEFT JOIN operation ON operation.operation_id = surface_technology_d.operation_id
        WHERE surface_id = :surface_technology_id
        ORDER BY operation.operation_code
        """
        
        detail_result = session.execute(text(detail_sql), {"surface_technology_id": surface_technology_id})
        detail_rows = detail_result.fetchall()
        
        # 构建明细数据列表
        surface_technology_d_list = []
        for detail_row in detail_rows:
            detail_dict = {
                "surfaceTechnologyDId": detail_row.surface_technology_d_id,
                "surfaceId": detail_row.surface_id,
                "operationId": detail_row.operation_id,
                "operationCode": detail_row.operation_code,
                "operationName": detail_row.operation_name,
                "remark": detail_row.remark,
                "creator": detail_row.creator,
                "createDate": detail_row.create_date,
                "modifierLast": detail_row.modifier_last,
                "modifyDateLast": detail_row.modify_date_last,
                "approveStatus": detail_row.approve_status,
                "approver": detail_row.approver,
                "approveDate": detail_row.approve_date
            }
            surface_technology_d_list.append(detail_dict)
        
        # 构建返回数据
        result_data = surface_technology.model_dump()
        result_data["surfaceTechnologyDList"] = surface_technology_d_list
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=result_data,
            message="数据获取成功"
        )
        
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"读取失败: {str(e)}",
            error_code="READ_FAILED"
        )