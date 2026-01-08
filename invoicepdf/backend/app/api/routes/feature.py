"""
Feature API - 使用 SQLModel 的版本
"""

from difflib import unified_diff
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
    Feature, FeatureCreate, FeatureResponse,
    FeatureD, FeatureDCreate, FeatureDUpdate, FeatureDResponse
)
from app.utils import get_server_datetime
from app.core.config import settings

def _convert_to_camel_case(snake_str: str) -> str:
    """将下划线命名转换为驼峰命名"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def _convert_to_snake_case(camel_str: str) -> str:
    """将驼峰命名转换为下划线命名"""
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()

router = APIRouter(prefix="/feature", tags=["feature"])


@router.post("/unified", response_model=UnifiedResponse)
def unified_feature_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的feature操作API - 使用SQLModel版本"""
    try:
        action = request.action.lower()
        
        if action == "create":
            return _handle_unified_create(request, session, current_user)
        elif action == "read":
            return _handle_unified_read(request, session, current_user)

        elif action == "delete":
            return _handle_unified_delete(request, session, current_user)
        elif action == "list":
            return _handle_unified_list(request, session, current_user)
        elif action == "submit_all":
            return _handle_unified_submit_all(request, session, current_user)
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
        create_empty = data.get("create_empty", False)
        
        if create_empty:
            # 创建空的 Feature 对象
            feature = Feature(
                featureId='new-'+str(uuid.uuid4()),
                featureCode="",
                featureDesc="",
                dataLen=0,
                dataType="",
                dataRanger=None,
                dataMin=None,
                dataMax=None,
                remark=None,
                approveStatus="N",
                approver=None,
                approveDate=None,
                creator=current_user.email,
                createDate=datetime.now(),
                modifierLast=current_user.email,
                modifyDateLast=datetime.now()
            )
            return UnifiedResponse(
                success=True,
                code=201,
                data=feature,
                message="空的feature对象创建成功"
            )
        else:
            # 创建完整的 Feature 对象
            feature_data = FeatureCreate(
                featureCode=data.get("featureCode", ""),
                featureDesc=data.get("featureDesc", ""),
                dataLen=data.get("dataLen", 0),
                dataType=data.get("dataType", ""),
                dataRanger=data.get("dataRanger"),
                dataMin=data.get("dataMin"),
                dataMax=data.get("dataMax"),
                remark=data.get("remark"),
                approveStatus=data.get("approveStatus", "N"),
                approver=data.get("approver"),
                approveDate=data.get("approveDate")
            )
            
            feature = Feature(
                featureId=str(uuid.uuid4()),
                **feature_data.model_dump(),
                creator=current_user.email,
                createDate=datetime.now(),
                modifierLast=current_user.email,
                modifyDateLast=datetime.now()
            )
            
            session.add(feature)
            session.commit()
            session.refresh(feature)
            
            return UnifiedResponse(
                success=True,
                code=201,
                data=feature,
                message="feature创建成功"
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
        feature_id = data.get("featureId")
        
        if not feature_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少featureId参数",
                error_code="MISSING_FEATURE_ID"
            )
        
        # 使用 SQLModel 查询
        feature = session.get(Feature, feature_id)
        
        if not feature:
            return UnifiedResponse(
                success=False,
                code=404,
                message="feature不存在",
                error_code="FEATURE_NOT_FOUND"
            )
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=feature.model_dump(),
            message="查询成功"
        )
        
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"查询失败: {str(e)}",
            error_code="READ_FAILED"
        )





def _handle_unified_delete(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理删除操作"""
    try:
        data = request.data or {}
        feature_id = data.get("featureId")
        
        if not feature_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少featureId参数",
                error_code="MISSING_FEATURE_ID"
            )
        
        # 使用SQL语句删除记录
        delete_sql = "DELETE FROM feature_d WHERE feature_id = '" + feature_id+"'"
        result = session.exec(text(delete_sql))

        delete_sql = "DELETE FROM feature WHERE feature_id = '" + feature_id+"'"
        result = session.exec(text(delete_sql))
        
        session.commit()
        
        
        return UnifiedResponse(
            success=True,
            code=200,
            data={"featureId": feature_id},
            message="feature删除成功"
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
        # 跨数据库查询：feature表与sys数据库的data_dictionary表关联
        # 获取sys数据库的dblink连接字符串
        sys_dblink_string = settings.get_sys_db_dblink_string()
        
        base_sql = f"""
        with data_type as(
            SELECT * FROM dblink(
                '{sys_dblink_string}',
                'SELECT dict_value, dict_desc
                 FROM public.data_dictionary 
                 WHERE dict_group_code=''dataType'''
            ) AS dd_data(
                dict_value VARCHAR(10), 
                dict_desc VARCHAR(40)
            )
        )
        ,data_range as(
            SELECT * FROM dblink(
                '{sys_dblink_string}',
                'SELECT dict_value, dict_desc
                 FROM public.data_dictionary 
                 WHERE dict_group_code=''dataRange'''
            ) AS dd_data(
                dict_value VARCHAR(10), 
                dict_desc VARCHAR(40)
            )
        )
        SELECT 
            feature_id,
            feature_code,
            feature_desc,
            data_len,
            data_type,
            data_ranger,
            data_min,
            data_max,
            remark,
            approve_status,
            approver,
            approve_date,
            creator,
            create_date,
            modifier_last,
            modify_date_last,
            data_type.dict_desc as data_type_desc,
            data_range.dict_desc as data_range_desc          
        FROM feature
        left join data_type on feature.data_type = data_type.dict_value
        left join data_range on feature.data_ranger = data_range.dict_value
        WHERE 1=1
        """
        count_sql = "SELECT COUNT(*) FROM feature WHERE 1=1"
        
        # 构建WHERE条件
        where_conditions = []
        params = {}
        
        # 应用过滤条件
        if request.filters:
            for field, value in request.filters.items():
                # 转换字段名为snake_case
                snake_field = _convert_to_snake_case(field)
                where_conditions.append(f"{snake_field} ILIKE %({field})s")
                params[field] = f"%{value}%"
        
        # 应用搜索条件
        if request.search:
            search_term = f"%{request.search}%"
            where_conditions.append("(feature_code ILIKE %(search)s OR feature_desc ILIKE %(search)s OR remark ILIKE %(search)s)")
            params["search"] = search_term
        
        # 添加WHERE条件到SQL
        if where_conditions:
            where_clause = " AND " + " AND ".join(where_conditions)
            base_sql += where_clause
            count_sql += where_clause
        
        # 获取总数
        total_result = session.exec(text(count_sql), **params if params else {}).one()
        total = total_result[0] if total_result else 0
        
        # 应用排序
        if request.sort:
            order_clauses = []
            for field, direction in request.sort.items():
                # 转换字段名为snake_case
                snake_field = _convert_to_snake_case(field)
                if direction.lower() == "desc":
                    order_clauses.append(f"{snake_field} DESC")
                else:
                    order_clauses.append(f"{snake_field} ASC")
            if order_clauses:
                base_sql += " ORDER BY " + ", ".join(order_clauses)
        else:
            base_sql += " ORDER BY create_date DESC"
        
        # 应用分页
        page = request.page or 1
        limit = request.limit or 20
        skip = (page - 1) * limit
        
        base_sql += f" LIMIT {limit} OFFSET {skip}"
        
        # 执行查询
        result = session.exec(text(base_sql), **params if params else {})
        items = result.all()
        
        # 转换为字典列表 - 将下划线命名转换为驼峰命名
        items_dict = []
        for item in items:
            item_dict = {}
            for key, value in item._mapping.items():
                # 将下划线命名转换为驼峰命名
                camel_key = _convert_to_camel_case(key)
                item_dict[camel_key] = value
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




def _handle_unified_submit_all(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理表头和明细数据一次性提交"""
    try:
        # 现在传入的是完整的Feature对象
        feature_data = request.data or {}
        
        print(f"开始处理提交数据: featureId={feature_data.get('featureId')}, featureDList长度={len(feature_data.get('featureDList', []))}")
        
        # 开始处理数据
        feature_id = None
        header_result = None
        details_result = None

        currentDateTime = get_server_datetime()
        
        # 1. 处理表头数据
        if not feature_data:
            return UnifiedResponse(
                success=False,
                code=400,
                message="没有提供要处理的数据",
                error_code="NO_DATA"
            )
        
        # 获取表头数据
        header_data = {
            "featureId": feature_data.get("featureId"),
            "featureCode": feature_data.get("featureCode"),
            "featureDesc": feature_data.get("featureDesc"),
            "dataType": feature_data.get("dataType"),
            "dataLen": feature_data.get("dataLen"),
            "dataRanger": feature_data.get("dataRanger"),
            "dataMin": feature_data.get("dataMin"),
            "dataMax": feature_data.get("dataMax"),
            "remark": feature_data.get("remark"),
            "approveStatus": feature_data.get("approveStatus")
        }
        
        # 获取明细数据
        details_data = feature_data.get("featureDList", [])
        
        # 检查是更新还是创建
        feature_id = header_data.get("featureId")
        if feature_id and not feature_id.startswith('new-'):
            # 更新现有表头
            feature = session.get(Feature, feature_id)
            if feature:
                # 更新字段
                for field, value in header_data.items():
                    if field != "featureId" and hasattr(feature, field):
                        setattr(feature, field, value)
                
                # 更新修改信息
                feature.modifierLast = current_user.email
                feature.modifyDateLast = datetime.now()
                
                session.add(feature)
                header_result = {"action": "updated", "featureId": feature_id}
            else:
                return UnifiedResponse(
                    success=False,
                    code=404,
                    message="表头记录不存在",
                    error_code="HEADER_NOT_FOUND"
                )
        else:
            # 创建新表头
            feature_create_data = {
                "featureCode": header_data.get("featureCode", ""),
                "featureDesc": header_data.get("featureDesc", ""),
                "dataType": header_data.get("dataType", ""),
                "dataLen": header_data.get("dataLen", 0),
                "dataRanger": header_data.get("dataRanger", ""),
                "dataMin": header_data.get("dataMin", ""),
                "dataMax": header_data.get("dataMax", ""),
                "remark": header_data.get("remark", ""),
                "approveStatus": header_data.get("approveStatus", "N")
            }
            
            feature = Feature(
                featureId=str(uuid.uuid4()),
                **feature_create_data,
                creator=current_user.email,
                createDate=currentDateTime,
                modifierLast=current_user.email,
                modifyDateLast=currentDateTime
            )
            
            session.add(feature)
            feature_id = feature.featureId
            header_result = {"action": "created", "featureId": feature_id}
        
        # 2. 处理明细数据
        if details_data:
            deleted_ids = []
            updated_ids = []
            created_ids = []
            
            # 获取数据库中现有的明细记录
            existing_details = session.exec(
                select(FeatureD).where(FeatureD.featureId == feature_id)
            ).all()
            existing_detail_ids = {detail.featureDId for detail in existing_details}
            
            # 处理传入的明细数据
            for detail_item in details_data:
                detail_id = detail_item.get("featureDId")
                
                if detail_id.startswith('new-'):
                    # 创建新记录
                    detail_create_data = {
                        "featureId": feature_id,
                        "featureValue": detail_item.get("featureValue", ""),
                        "featureValueDesc": detail_item.get("featureValueDesc", ""),
                        "remark": detail_item.get("remark"),
                        "creator": current_user.email,
                        "createDate": currentDateTime,
                        "modifierLast": current_user.email,
                        "modifyDateLast": currentDateTime,
                        "approveStatus": "N",
                        "approver": None,
                        "approveDate": None
                    }
                    
                    feature_d = FeatureD(
                        featureDId=str(uuid.uuid4()),
                        **detail_create_data
                    )
                    
                    session.add(feature_d)
                    created_ids.append(feature_d.featureDId)
                else:
                    # 更新现有记录
                    feature_d = session.get(FeatureD, detail_id)
                    if feature_d and feature_d.featureId == feature_id:
                        for field, value in detail_item.items():
                            if field != "featureDId" and hasattr(feature_d, field):
                                setattr(feature_d, field, value)
                        session.add(feature_d)
                        updated_ids.append(detail_id)
            
            # 删除不再存在的记录
            current_detail_ids = {item.get("featureDId") for item in details_data if not item.get("featureDId", "").startswith('new-')}
            for detail in existing_details:
                if detail.featureDId not in current_detail_ids:
                    session.delete(detail)
                    deleted_ids.append(detail.featureDId)
            
            details_result = {
                "deleted": deleted_ids,
                "updated": updated_ids,
                "created": created_ids
            }
        
        # 提交所有更改到数据库
        session.commit()
        
        return UnifiedResponse(
            success=True,
            code=200,
            data={
                "header": header_result,
                "details": details_result,
                "featureId": feature_id
            },
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