"""
Material API - 使用 SQLModel 的版本
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
    Material, MaterialD
)
from app.utils import get_server_datetime

router = APIRouter(prefix="/material", tags=["material"])





@router.post("/unified", response_model=UnifiedResponse)
def unified_material_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的material操作API - 使用SQLModel版本"""
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
        # 创建空的 Material 对象
        material = Material(
            materialId='new-'+str(uuid.uuid4()),
            materialClassId="",
            materialCode="",
            materialDesc="",
            unitId="",
            secondUnitId="",
            remark="",
            approveStatus="N",
            approver="",
            approveDate=None,
            creator=current_user.email,
            createDate=datetime.now(),
            modifierLast=None,
            modifyDateLast=None,
            materialDList=None
        )
        
        # 构建返回数据，包含空的 MaterialD 列表
        result_data = material.model_dump()
        result_data["materialDList"] = []
        
        return UnifiedResponse(
            success=True,
            code=201,
            data=result_data,
            message="空的material对象创建成功"
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
        material_id = data.get("materialId")
        
        if not material_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少materialId参数",
                error_code="MISSING_MATERIAL_ID"
            )
        
        # 先删除关联的属性数据
        delete_detail_sql = "DELETE FROM material_d WHERE material_id = :material_id"
        session.execute(text(delete_detail_sql), {"material_id": material_id})
        
        # 删除主表记录
        delete_main_sql = "DELETE FROM material WHERE material_id = :material_id"
        session.execute(text(delete_main_sql), {"material_id": material_id})
        
        session.commit()
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=None,
            message="material删除成功"
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
            material_id,
            material_class_id,
            material_code,
            material_desc,
            unit_id,
            second_unit_id,
            remark,
            approve_status,
            approver,
            approve_date,
            creator,
            create_date,
            modifier_last,
            modify_date_last
        FROM material
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
                material_code ILIKE '{search_term}' OR 
                material_desc ILIKE '{search_term}' OR 
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
            order_conditions.append("material_code ASC")
        
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
        FROM material
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
                "materialId": row[0],
                "materialClassId": row[1],
                "materialCode": row[2],
                "materialDesc": row[3],
                "unitId": row[4],
                "secondUnitId": row[5],
                "remark": row[6],
                "approveStatus": row[7],
                "approver": row[8],
                "approveDate": row[9],
                "creator": row[10],
                "createDate": row[11],
                "modifierLast": row[12],
                "modifyDateLast": row[13]
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
    """处理物料及属性的保存操作"""
    try:
        # 现在传入的是完整的Material对象
        material_data = request.data or {}
        
        print(f"开始处理提交数据: materialId={material_data.get('materialId')}, materialDList长度={len(material_data.get('materialDList', []))}")
        
        # 开始处理数据
        material_id = None
        header_result = None
        details_result = None

        currentDateTime = get_server_datetime()
        
        # 1. 处理表头数据
        if not material_data:
            return UnifiedResponse(
                success=False,
                code=400,
                message="没有提供要处理的数据",
                error_code="NO_DATA"
            )
        
        # 获取表头数据
        header_data = {
            "materialId": material_data.get("materialId"),
            "materialClassId": material_data.get("materialClassId"),
            "materialCode": material_data.get("materialCode"),
            "materialDesc": material_data.get("materialDesc"),
            "unitId": material_data.get("unitId"),
            "secondUnitId": material_data.get("secondUnitId"),
            "remark": material_data.get("remark"),
            "approveStatus": material_data.get("approveStatus")
        }
        
        # 获取明细数据
        details_data = material_data.get("materialDList", [])

        
        
        # 检查是更新还是创建
        material_id = header_data.get("materialId")
        
        # 调用 read 操作获取现有记录
        read_request = UnifiedRequest(
            action="read",
            module="material",
            data={"materialId": material_id}
        )
        read_response = _handle_unified_read(read_request, session, current_user)
        
        # 判断 read_response 返回有 Material 对象还是空值
        material_exists = read_response.success and read_response.data is not None
        
        # 根据 read_response.data 是否为空，执行新增或更改操作
        if material_exists and read_response.data:
            # 更新现有记录
            material_data = read_response.data
            material = session.get(Material, material_id)
            if material:
                # 更新现有表头
                for field, value in header_data.items():
                    if field != "materialId" and hasattr(material, field):
                        setattr(material, field, value)
                
                # 更新修改信息
                material.modifierLast = current_user.email
                material.modifyDateLast = datetime.now()
                
                session.add(material)
                header_result = {"action": "updated", "materialId": material_id}
        else:
            # 创建新记录
            material_create_data = {
                "materialClassId": header_data.get("materialClassId", ""),
                "materialCode": header_data.get("materialCode", ""),
                "materialDesc": header_data.get("materialDesc", ""),
                "unitId": header_data.get("unitId"),
                "secondUnitId": header_data.get("secondUnitId"),
                "remark": header_data.get("remark"),
                "approveStatus": header_data.get("approveStatus", "N")
            }
            
            # 使用传入的 materialId 或生成新的
            new_material_id = str(uuid.uuid4())
            
            material = Material(
                materialId=new_material_id,
                **material_create_data,
                creator=current_user.email,
                createDate=currentDateTime,
                modifierLast=None,
                modifyDateLast=None
            )
            
            session.add(material)
            material_id = new_material_id
            header_result = {"action": "created", "materialId": material_id}
        
        # 2. 处理明细数据
        if details_data:
            deleted_ids = []
            updated_ids = []
            created_ids = []
            
            # 使用 read_response.data.materialDList 获取现有明细记录
            existing_details = read_response.data.get("materialDList", []) if material_exists and read_response.data else []
            existing_detail_ids = {detail.get("materialDId") for detail in existing_details}
            
            # 处理传入的明细数据
            for detail_item in details_data:
                detail_id = detail_item.get("materialDId")
                
                if detail_id.startswith('new-'):
                    # 创建新记录
                    detail_create_data = {
                        "materialId": material_id,
                        "featureCode": detail_item.get("featureCode", ""),
                        "featureDesc": detail_item.get("featureDesc", ""),
                        "featureValue": detail_item.get("featureValue"),
                        "remark": detail_item.get("remark"),
                        "creator": current_user.email,
                        "createDate": currentDateTime,
                        "modifierLast": current_user.email,
                        "modifyDateLast": currentDateTime,
                        "approveStatus": "N",
                        "approver": None,
                        "approveDate": None
                    }
                    
                    material_d = MaterialD(
                        materialDId=str(uuid.uuid4()),
                        **detail_create_data
                    )
                    
                    session.add(material_d)
                    created_ids.append(material_d.materialDId)
                else:
                    # 更新现有记录
                    material_d = session.get(MaterialD, detail_id)
                    if material_d and material_d.materialId == material_id:
                        for field, value in detail_item.items():
                            if field != "materialDId" and hasattr(material_d, field):
                                setattr(material_d, field, value)
                        session.add(material_d)
                        updated_ids.append(detail_id)
            
            # 删除不再存在的记录
            current_detail_ids = {item.get("materialDId") for item in details_data if not item.get("materialDId", "").startswith('new-')}
            for detail in existing_details:
                detail_id = detail.get("materialDId")
                if detail_id and detail_id not in current_detail_ids:
                    # 从数据库中删除记录
                    material_d_to_delete = session.get(MaterialD, detail_id)
                    if material_d_to_delete:
                        session.delete(material_d_to_delete)
                        deleted_ids.append(detail_id)
            
            details_result = {
                "deleted": deleted_ids,
                "updated": updated_ids,
                "created": created_ids
            }
        # 提交所有更改到数据库
        session.commit()
        
        # 重新获取完整的 Material 对象及其子对象
        material = session.get(Material, material_id)
        material_attributes = session.exec(
            select(MaterialD).where(MaterialD.materialId == material_id)
        ).all()
        
        # 构建返回数据，包含完整的 Material 对象和子对象列表
        result_data = material.model_dump()
        result_data["materialDList"] = [attr.model_dump() for attr in material_attributes]
        
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
    """处理读取操作 - 根据主键获取单个 Material 对象"""
    try:
        data = request.data or {}
        material_id = data.get("materialId")
        
        if not material_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少materialId参数",
                error_code="MISSING_MATERIAL_ID"
            )
        
        # 直接查询数据库获取主表数据
        material = session.get(Material, material_id)
        
        if not material:
            return UnifiedResponse(
                success=False,
                code=404,
                message=f"未找到 materialId 为 {material_id} 的记录",
                error_code="MATERIAL_NOT_FOUND"
            )
        
        # 查询子表数据
        material_attributes = session.exec(
            select(MaterialD).where(MaterialD.materialId == material_id)
        ).all()
        
        # 构建返回数据，包含完整的 Material 对象和子对象列表
        result_data = material.model_dump()
        result_data["materialDList"] = [attr.model_dump() for attr in material_attributes]
        
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


def _handle_unified_batch_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理批量保存操作 - 用于Excel导入"""
    try:
        # 获取批量数据
        batch_data = request.data or []
        
        if not batch_data or not isinstance(batch_data, list):
            return UnifiedResponse(
                success=False,
                code=400,
                message="没有提供有效的批量数据",
                error_code="INVALID_BATCH_DATA"
            )
        
        print(f"开始批量保存 {len(batch_data)} 条记录")
        
        currentDateTime = get_server_datetime()
        success_count = 0
        error_count = 0
        error_details = []
        
        # 批量处理数据
        for index, item_data in enumerate(batch_data):
            try:
                # 验证必需字段
                material_code = item_data.get('material_code', '').strip()
                material_id = item_data.get('material_id', '').strip()
                
                if not material_code and not material_id:
                    error_details.append(f"第{index + 1}行: 缺少物料编码或物料ID")
                    error_count += 1
                    continue
                
                # 确定要查找的记录
                existing_material = None
                search_by_id = False
                
                if material_id:
                    # 优先通过 material_id 查找
                    existing_material = session.get(Material, material_id)
                    search_by_id = True
                
                if not existing_material and material_code:
                    # 如果通过 ID 没找到，再通过编码查找
                    existing_material = session.exec(
                        select(Material).where(Material.materialCode == material_code)
                    ).first()
                
                if existing_material:
                    # 更新现有记录
                    material = existing_material
                    
                    # 更新字段（如果提供了新值）
                    if material_code:
                        material.materialCode = material_code
                    if item_data.get('material_desc'):
                        material.materialDesc = item_data.get('material_desc', '')
                    if item_data.get('material_class_id'):
                        material.materialClassId = item_data.get('material_class_id', '')
                    if item_data.get('unit_id'):
                        material.unitId = item_data.get('unit_id', '')
                    if item_data.get('second_unit_id'):
                        material.secondUnitId = item_data.get('second_unit_id', '')
                    if item_data.get('remark'):
                        material.remark = item_data.get('remark', '')
                    if item_data.get('approve_status'):
                        material.approveStatus = item_data.get('approve_status', 'N')
                    
                    material.modifierLast = current_user.email
                    material.modifyDateLast = currentDateTime
                    
                    session.add(material)
                    success_count += 1
                    print(f"更新记录: {material.materialCode} (ID: {material.materialId})")
                    
                else:
                    # 创建新记录
                    new_material_id = material_id if material_id else str(uuid.uuid4())
                    
                    material = Material(
                        materialId=new_material_id,
                        materialCode=material_code,
                        materialDesc=item_data.get('material_desc', ''),
                        materialClassId=item_data.get('material_class_id', ''),
                        unitId=item_data.get('unit_id', ''),
                        secondUnitId=item_data.get('second_unit_id', ''),
                        remark=item_data.get('remark', ''),
                        approveStatus=item_data.get('approve_status', 'N'),
                        approver='',
                        approveDate=None,
                        creator=current_user.email,
                        createDate=currentDateTime,
                        modifierLast=None,
                        modifyDateLast=None
                    )
                    
                    session.add(material)
                    success_count += 1
                    print(f"创建记录: {material_code} (ID: {new_material_id})")
                
            except Exception as e:
                error_details.append(f"第{index + 1}行: {str(e)}")
                error_count += 1
                print(f"处理第{index + 1}行时出错: {str(e)}")
        
        # 提交所有更改
        session.commit()
        
        # 构建返回消息
        if error_count == 0:
            message = f"批量保存成功，共处理 {success_count} 条记录"
        else:
            message = f"批量保存完成，成功 {success_count} 条，失败 {error_count} 条"
        
        return UnifiedResponse(
            success=True,
            code=200,
            data={
                "total_processed": len(batch_data),
                "success_count": success_count,
                "error_count": error_count,
                "error_details": error_details
            },
            message=message
        )
        
    except Exception as e:
        # 回滚事务
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"批量保存失败: {str(e)}",
            error_code="BATCH_SAVE_FAILED"
        )