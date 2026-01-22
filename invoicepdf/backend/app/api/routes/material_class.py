"""
MaterialClass API - 使用 SQLModel 的版本
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
    MaterialClass, MaterialClassCreate, MaterialClassResponse, MaterialClassD
)
from app.utils import get_server_datetime

router = APIRouter(prefix="/material-class", tags=["material-class"])


@router.post("/unified", response_model=UnifiedResponse)
def unified_material_class_operations(
    request: UnifiedRequest[MaterialClass],
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的material_class操作API - 使用SQLModel版本"""
    try:
        action = request.action.lower()
        
        if action == "create":
            return _handle_unified_create(request, session, current_user)

        elif action == "delete":
            return _handle_unified_delete(request, session, current_user)
        elif action == "list":
            return _handle_unified_list(request, session, current_user)
        elif action == "read":
            return read(request, session, current_user)
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
        data = request.data or {}
        create_empty = data.get("create_empty", False)
        
        if create_empty:
            # 创建空的 MaterialClass 对象
            materialClass = MaterialClass(
                materialClassId='new-'+str(uuid.uuid4()),
                materialClassPId="",
                classCode="",
                classDesc="",
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
                data=materialClass,
                message="空的material_class对象创建成功"
            )
        else:
            # 创建完整的 MaterialClass 对象
            materialClassData = MaterialClassCreate(
                materialClassPId=data.get("materialClassPId", ""),
                classCode=data.get("classCode", ""),
                classDesc=data.get("classDesc", ""),
                remark=data.get("remark"),
                approveStatus=data.get("approveStatus", "N"),
                approver=data.get("approver"),
                approveDate=data.get("approveDate"),
                creator=current_user.email
            )
            
            materialClass = MaterialClass(
                materialClassId=str(uuid.uuid4()),
                **materialClassData.model_dump(),
                createDate=datetime.now(),
                modifierLast=current_user.email,
                modifyDateLast=datetime.now()
            )
            
           
            
            return UnifiedResponse(
                success=True,
                code=201,
                data=materialClass,
                message="material_class创建成功"
            )
        
    except Exception as e:
        
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"创建失败: {str(e)}",
            error_code="CREATE_FAILED"
        )





def _handle_unified_delete(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse[dict[str, Any]]:
    """处理删除操作"""
    try:
        data = request.data or {}
        
        # 从请求数据中获取material_class_id
        material_class_id = data.get("materialClassId")
        if not material_class_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少materialClassId参数",
                error_code="MISSING_ID"
            )
        
        print(f"DEBUG: 准备删除物料类别，ID: {material_class_id}")
        
        # 先删除关联的明细数据
        delete_detail_sql = """
        DELETE FROM material_class_d 
        WHERE material_class_id = :material_class_id
        """
        detail_result = session.execute(text(delete_detail_sql), {"material_class_id": material_class_id})
        deleted_details_count = detail_result.rowcount
        print(f"DEBUG: 删除了 {deleted_details_count} 条明细记录")
        
        # 删除主表记录
        delete_main_sql = """
        DELETE FROM material_class 
        WHERE material_class_id = :material_class_id
        """
        main_result = session.execute(text(delete_main_sql), {"material_class_id": material_class_id})
        deleted_main_count = main_result.rowcount
        
        # 提交事务
        session.commit()
        
        print(f"DEBUG: 成功删除物料类别，ID: {material_class_id}")
        
        return UnifiedResponse(
            success=True,
            code=200,
            data={"deletedId": material_class_id, "deletedDetailsCount": deleted_details_count},
            message=f"成功删除物料类别及其 {deleted_details_count} 条明细数据"
        )
        
    except Exception as e:
        session.rollback()
        print(f"DEBUG: 删除失败: {str(e)}")
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"删除失败: {str(e)}",
            error_code="DELETE_FAILED"
        )


def _handle_unified_list(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse[list[MaterialClass]]:
    """处理列表查询操作"""
    try:
        data = request.data or {}
        filters = request.filters or {}
        where_condition = filters.get("where", "")
        
        # 构建SQL查询
        sql = """
        SELECT material_class.*
        , material_class_p.class_code as material_class_p_code
        , material_class_p.class_desc as material_class_p_desc
        FROM "material_class"
        LEFT JOIN material_class_d
        ON material_class.material_class_id = material_class_d.material_class_id
        left join material_class as material_class_p
        on material_class.material_class_p_id = material_class_p.material_class_id
        """
        
        # 如果有where条件，添加到SQL中
        if where_condition:
            sql += f" WHERE {where_condition}"
        
        sql += " ORDER BY material_class.class_code"
        
        result = session.execute(text(sql))
        rows = result.fetchall()
        
        # 将查询结果转换为MaterialClass对象
        material_classes = []
        for row in rows:
            material_class = MaterialClass(
                materialClassId=row.material_class_id,
                materialClassPId=row.material_class_p_id or "",
                materialClassPCode=row.material_class_p_code or "",
                materialClassPDesc=row.material_class_p_desc or "",
                classCode=row.class_code,
                classDesc=row.class_desc,
                remark=row.remark,
                creator=row.creator,
                createDate=row.create_date,
                modifierLast=row.modifier_last,
                modifyDateLast=row.modify_date_last,
                approveStatus=row.approve_status,
                approver=row.approver,
                approveDate=row.approve_date
            )
            material_classes.append(material_class)
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=material_classes,
            message=f"成功获取 {len(material_classes)} 条物料类别数据"
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"查询失败: {str(e)}",
            error_code="QUERY_FAILED"
        )


def read(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse[MaterialClass]:
    """根据主键获取单个物料类别数据"""
    try:
        data = request.data or {}
        
        # 从请求数据中获取material_class_id
        material_class_id = data.get("materialClassId")
        if not material_class_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少materialClassId参数",
                error_code="MISSING_ID"
            )
        
        # 查询主表数据
        main_sql = """
        SELECT m.*, 
               p.class_code as material_class_p_code,
               p.class_desc as material_class_p_desc
        FROM "material_class" m
        LEFT JOIN "material_class" p ON m.material_class_p_id = p.material_class_id
        WHERE m.material_class_id = :material_class_id
        """
        
        result = session.execute(text(main_sql), {"material_class_id": material_class_id})
        main_row = result.fetchone()
        
        if not main_row:
            return UnifiedResponse(
                success=False,
                code=404,
                message=f"物料类别 {material_class_id} 不存在",
                error_code="NOT_FOUND"
            )
        
        # 查询明细数据
        detail_sql = """
        SELECT material_class_d.material_class_d_id,
        material_class_d.material_class_id,
        material_class_d.feature_id,
        material_class_d.feature_value,
        material_class_d.position,
        material_class_d.remark,
        material_class_d.creator,
        material_class_d.create_date,
        material_class_d.modifier_last,
        material_class_d.modify_date_last,
        material_class_d.approve_status,
        material_class_d.approver,
        material_class_d.approve_date
        ,feature.feature_code
        ,feature.feature_desc
        FROM material_class_d
        left join feature on feature.feature_id = material_class_d.feature_id
        WHERE material_class_id = :material_class_id
        ORDER BY position
        """
        
        detail_result = session.execute(text(detail_sql), {"material_class_id": material_class_id})
        detail_rows = detail_result.fetchall()
        
        # 构建MaterialClassD列表
        material_class_d_list = []
        for detail_row in detail_rows:
            material_class_d = MaterialClassD(
                materialClassDId=detail_row.material_class_d_id,
                materialClassId=detail_row.material_class_id,
                featureId=detail_row.feature_id,
                featureCode=detail_row.feature_code,
                featureDesc=detail_row.feature_desc,
                featureValue=detail_row.feature_value,
                position=detail_row.position,
                remark=detail_row.remark,
                creator=detail_row.creator,
                createDate=detail_row.create_date,
                modifierLast=detail_row.modifier_last,
                modifyDateLast=detail_row.modify_date_last,
                approveStatus=detail_row.approve_status,
                approver=detail_row.approver,
                approveDate=detail_row.approve_date
            )
            material_class_d_list.append(material_class_d)
        
        # 构建完整的MaterialClass对象
        material_class = MaterialClass(
            materialClassId=main_row.material_class_id,
            materialClassPId=main_row.material_class_p_id or "",
            materialClassPCode=main_row.material_class_p_code or "",
            materialClassPDesc=main_row.material_class_p_desc or "",
            classCode=main_row.class_code,
            classDesc=main_row.class_desc,
            remark=main_row.remark,
            creator=main_row.creator,
            createDate=main_row.create_date,
            modifierLast=main_row.modifier_last,
            modifyDateLast=main_row.modify_date_last,
            approveStatus=main_row.approve_status,
            approver=main_row.approver,
            approveDate=main_row.approve_date,
            materialClassDList=material_class_d_list
        )
        
        # 调试日志
        print(f"DEBUG: material_class_d_list长度: {len(material_class_d_list)}")
        print(f"DEBUG: material_class.materialClassDList长度: {len(material_class.materialClassDList) if material_class.materialClassDList else 0}")
        print(f"DEBUG: material_class.materialClassDList类型: {type(material_class.materialClassDList)}")
        if material_class.materialClassDList and len(material_class.materialClassDList) > 0:
            print(f"DEBUG: 第一条明细数据: {material_class.materialClassDList[0]}")
        
        # 手动构建响应数据，确保包含materialClassDList
        response_data = {
            "materialClassId": material_class.materialClassId,
            "materialClassPId": material_class.materialClassPId,
            "materialClassPCode": material_class.materialClassPCode,
            "materialClassPDesc": material_class.materialClassPDesc,
            "classCode": material_class.classCode,
            "classDesc": material_class.classDesc,
            "remark": material_class.remark,
            "creator": material_class.creator,
            "createDate": material_class.createDate,
            "modifierLast": material_class.modifierLast,
            "modifyDateLast": material_class.modifyDateLast,
            "approveStatus": material_class.approveStatus,
            "approver": material_class.approver,
            "approveDate": material_class.approveDate,
            "materialClassDList": material_class_d_list
        }
        
        print(f"DEBUG: 手动构建的响应数据: {response_data}")
        print(f"DEBUG: response_data.materialClassDList长度: {len(response_data['materialClassDList'])}")
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=response_data,
            message=f"成功获取物料类别 {material_class.classCode} 及其 {len(material_class_d_list)} 条明细数据"
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"获取失败: {str(e)}",
            error_code="GET_ONE_FAILED"
        )


def _handle_unified_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse[MaterialClass]:
    """处理保存操作 - 同时保存主表和明细表"""
    try:
        data = request.data
        print(f"DEBUG: 接收到的保存数据: {data}")
        print(f"DEBUG: 数据类型: {type(data)}")
        print(f"DEBUG: 数据键: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        if not data:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少保存数据",
                error_code="MISSING_DATA"
            )
        
        material_class_id = data.get("materialClassId", "")
        if not material_class_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少物料类别ID",
                error_code="MISSING_ID"
            )
        
        # 获取明细数据
        material_class_d_list = data.get("materialClassDList", [])
        
        # 检查是否为新建对象（以'new-'开头）
        if material_class_id.startswith('new-'):
            # 生成新的material_class_id
            new_material_class_id = str(uuid.uuid4())
            
            # 创建新记录
            material_class = MaterialClass(
                materialClassId=new_material_class_id,
                materialClassPId=data.get("materialClassPId", ""),
                classCode=data.get("classCode", ""),
                classDesc=data.get("classDesc", ""),
                remark=data.get("remark"),
                approveStatus=data.get("approveStatus", "N"),
                creator=current_user.email,
                createDate=datetime.now()
            )
            session.add(material_class)
            
            # 保存明细数据
            for detail_data in material_class_d_list:
                # 检查是否为新建明细记录（以'new-'开头）
                detail_id = detail_data.get("materialClassDId", "")
                if detail_id.startswith('new-'):
                    # 新建明细记录，生成新ID
                    new_detail_id = str(uuid.uuid4())
                else:
                    # 现有明细记录，保持原ID
                    new_detail_id = detail_id
                
                material_class_d = MaterialClassD(
                    materialClassDId=new_detail_id,
                    materialClassId=new_material_class_id,
                    featureId=detail_data.get("featureId", ""),
                    featureValue=detail_data.get("featureValue", ""),
                    position=detail_data.get("position", 0),
                    remark=detail_data.get("remark"),
                    creator=current_user.email,
                    createDate=material_class.createDate,
                    approveStatus=detail_data.get("approveStatus", "N")
                )
                session.add(material_class_d)
        else:
            # 更新现有记录
            existing_material_class = session.get(MaterialClass, material_class_id)
            if not existing_material_class:
                return UnifiedResponse(
                    success=False,
                    code=404,
                    message=f"物料类别 {material_class_id} 不存在",
                    error_code="NOT_FOUND"
                )
            
            # 更新主表字段
            existing_material_class.materialClassPId = data.get("materialClassPId", "")
            existing_material_class.classCode = data.get("classCode", "")
            existing_material_class.classDesc = data.get("classDesc", "")
            existing_material_class.remark = data.get("remark")
            existing_material_class.approveStatus = data.get("approveStatus", "N")
            existing_material_class.modifierLast = current_user.email
            existing_material_class.modifyDateLast = datetime.now()
            
            # 删除现有的明细数据
            delete_detail_sql = """
            DELETE FROM material_class_d 
            WHERE material_class_id = :material_class_id
            """
            session.execute(text(delete_detail_sql), {"material_class_id": material_class_id})
            
            # 保存新的明细数据
            for detail_data in material_class_d_list:
                # 检查是否为新建明细记录（以'new-'开头）
                detail_id = detail_data.get("materialClassDId", "")
                if detail_id.startswith('new-'):
                    # 新建明细记录，生成新ID
                    new_detail_id = str(uuid.uuid4())
                else:
                    # 现有明细记录，保持原ID
                    new_detail_id = detail_id
                
                material_class_d = MaterialClassD(
                    materialClassDId=new_detail_id,
                    materialClassId=material_class_id,
                    featureId=detail_data.get("featureId", ""),
                    featureValue=detail_data.get("featureValue", ""),
                    position=detail_data.get("position", 0),
                    remark=detail_data.get("remark"),
                    creator=current_user.email,
                    createDate=datetime.now(),
                    modifierLast=current_user.email,
                    modifyDateLast=datetime.now(),
                    approveStatus=detail_data.get("approveStatus", "N")
                )
                session.add(material_class_d)
        
        session.commit()
        
        # 保存完成后，调用read获取最新的完整对象
        if material_class_id.startswith('new-'):
            # 新建记录，使用新生成的ID
            final_id = material_class.materialClassId
        else:
            # 更新现有记录，使用原ID
            final_id = material_class_id
        
        # 构造read的请求
        get_request = UnifiedRequest(
            action="getOneByKey",
            module="material-class",
            data={"materialClassId": final_id}
        )
        
        # 调用read函数获取最新数据
        get_response = read(get_request, session, current_user)
        
        if get_response.success:
            return UnifiedResponse(
                success=True,
                code=200,
                data=get_response.data,
                message=f"物料类别保存成功，包含 {len(get_response.data.materialClassDList) if get_response.data.materialClassDList else 0} 条明细数据"
            )
        else:
            return UnifiedResponse(
                success=False,
                code=500,
                message="保存成功但无法获取最新数据",
                error_code="FETCH_AFTER_SAVE_FAILED"
            )
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"保存失败: {str(e)}",
            error_code="SAVE_FAILED"
        ) 