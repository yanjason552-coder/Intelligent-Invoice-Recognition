"""
Inventory API - 使用 SQLModel 的版本
"""

import time
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
    Inventory, MaterialLotFeature, MaterialLot
)
from app.utils import get_server_datetime

router = APIRouter(prefix="/inventory", tags=["inventory"])





@router.post("/unified", response_model=UnifiedResponse)
def unified_inventory_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的inventory操作API - 使用SQLModel版本"""
    try:
        action = request.action.lower()
        print(f"接收到请求，action: {action}")
        
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
            print("准备调用 _handle_unified_batch_save")
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
        # 创建空的 Inventory 对象
        inventory = Inventory(
            inventoryId='new-'+str(uuid.uuid4()),
            materialId="",
            materialCode="",
            materialDesc="",
            plantId="",
            plantName="",
            warehouseId="",
            warehouseName="",
            binId="",
            binName="",
            materialLotId="",
            lotNo="",
            lotDesc="",
            stockQty=0.0,
            unitIdStock="",
            stockQtySecond=0.0,
            unitIdStockSec="",
            stockQtyLocked=0.0,
            stockQtySecondLocked=0.0,
            approveStatus="N",
            approver="",
            approveDate=None,
            creator=current_user.email,
            createDate=datetime.now(),
            modifierLast=None,
            modifyDateLast=None
        )
        
        # 构建返回数据，包含空的 MaterialLotFeature 列表
        result_data = inventory.model_dump()
        result_data["materialLotFeatureList"] = []
        
        return UnifiedResponse(
            success=True,
            code=201,
            data=result_data,
            message="空的inventory对象创建成功"
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
        inventory_id = data.get("inventory_id")
        
        if not inventory_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少inventory_id参数",
                error_code="MISSING_INVENTORY_ID"
            )
        
        # 先删除关联的批次属性数据
        delete_detail_sql = "DELETE FROM material_lot_feature WHERE material_lot_id = (SELECT material_lot_id FROM inventory WHERE inventory_id = :inventory_id)"
        session.execute(text(delete_detail_sql), {"inventory_id": inventory_id})
        
        # 删除主表记录
        delete_main_sql = "DELETE FROM inventory WHERE inventory_id = :inventory_id"
        session.execute(text(delete_main_sql), {"inventory_id": inventory_id})
        
        session.commit()
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=None,
            message="inventory删除成功"
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
        # SQL 查询模板 - 包含子对象数据
        sql_template = """
        SELECT 
            inventory.*,material_lot_feature.*,feature.feature_desc
        FROM inventory 
        LEFT JOIN material_lot_feature ON inventory.material_lot_id = material_lot_feature.material_lot_id
        left join feature on feature.feature_id = material_lot_feature.feature_id
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
                    # 根据字段类型添加表别名
                    if db_field in ['material_lot_feature_id', 'feature_id', 'feature_code', 'feature_desc', 'feature_value']:
                        filter_conditions.append(f"AND material_lot_feature.{db_field} ILIKE '%{value}%'")
                    else:
                        filter_conditions.append(f"AND inventory.{db_field} ILIKE '%{value}%'")
        
        # 构建搜索条件
        search_conditions = []
        if request.search:
            search_term = f"%{request.search}%"
            search_conditions.append(f"""AND (
                inventory.material_code ILIKE '{search_term}' OR 
                inventory.material_desc ILIKE '{search_term}' OR 
                inventory.plant_name ILIKE '{search_term}' OR 
                inventory.warehouse_name ILIKE '{search_term}' OR 
                inventory.bin_name ILIKE '{search_term}' OR 
                inventory.material_lot_code ILIKE '{search_term}' OR
                material_lot_feature.feature_code ILIKE '{search_term}' OR
                material_lot_feature.feature_desc ILIKE '{search_term}' OR
                material_lot_feature.feature_value ILIKE '{search_term}'
            )""")
        
        # 构建排序条件
        order_conditions = []
        if request.sort:
            for field, direction in request.sort.items():
                # 将字段名转换为数据库字段名
                db_field = ''.join(['_' + c.lower() if c.isupper() else c for c in field]).lstrip('_')
                order_direction = "DESC" if direction.lower() == "desc" else "ASC"
                # 根据字段类型添加表别名
                if db_field in ['material_lot_feature_id', 'feature_id', 'feature_code', 'feature_desc', 'feature_value']:
                    order_conditions.append(f"material_lot_feature.{db_field} {order_direction}")
                else:
                    order_conditions.append(f"inventory.{db_field} {order_direction}")
        else:
            order_conditions.append("inventory.material_code ASC")
        
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
        SELECT COUNT(DISTINCT inventory.inventory_id) as total
        FROM inventory 
        LEFT JOIN material_lot_feature ON inventory.material_lot_id = material_lot_feature.material_lot_id
        WHERE 1=1
        {' '.join(filter_conditions)}
        {' '.join(search_conditions)}
        """
        
        # 执行计数查询
        count_result = session.exec(text(count_sql)).one()
        total = count_result[0] if count_result else 0
        
        # 执行主查询
        result = session.execute(text(sql_query))
        rows = result.fetchall()
        
        # 将查询结果组织成嵌套结构 - 直接使用字典，不创建 SQLModel 对象
        items_dict = {}  # 用于去重和分组
        
        for row in rows:
            inventory_id = row.inventory_id
            
            # 如果这个主记录还没有处理过，创建主记录（使用字典）
            if inventory_id not in items_dict:
                items_dict[inventory_id] = {
                    "inventoryId": row.inventory_id,
                    "materialId": row.material_id,
                    "materialCode": row.material_code,
                    "materialDesc": row.material_desc,
                    "plantId": row.plant_id,
                    "plantName": row.plant_name,
                    "warehouseId": row.warehouse_id,
                    "warehouseName": row.warehouse_name,
                    "binId": row.bin_id,
                    "binName": row.bin_name,
                    "materialLotId": row.material_lot_id,
                    "lotNo": row.lot_no,
                    "lotDesc": row.lot_desc,
                    "stockQty": row.stock_qty,
                    "unitIdStock": row.unit_id_stock,
                    "stockQtySecond": row.stock_qty_second,
                    "unitIdStockSec": row.unit_id_stock_sec,
                    "stockQtyLocked": row.stock_qty_locked,
                    "stockQtySecondLocked": row.stock_qty_second_locked,
                    "approveStatus": row.approve_status,
                    "approver": row.approver,
                    "approveDate": row.approve_date,
                    "creator": row.creator,
                    "createDate": row.create_date,
                    "modifierLast": row.modifier_last,
                    "modifyDateLast": row.modify_date_last,
                    "materialLotFeatureList": []  # 初始化属性列表
                }
            
            # 如果有批次属性数据，添加到属性列表
            if row.material_lot_feature_id:
                feature_dict = {
                    "materialLotFeatureId": row.material_lot_feature_id,
                    "materialLotId": row.material_lot_id,
                    "featureId": row.feature_id,
                    "featureCode": row.feature_code,
                    "featureDesc": row.feature_desc,
                    "featureValue": row.feature_value,
                    "remark": row.remark,
                    "creator": row.creator,
                    "createDate": row.create_date,
                    "modifierLast": row.modifier_last,
                    "modifyDateLast": row.modify_date_last,
                    "approveStatus": row.approve_status,
                    "approver": row.approver,
                    "approveDate": row.approve_date
                }
                items_dict[inventory_id]["materialLotFeatureList"].append(feature_dict)
        
        # 将分组后的数据转换为列表
        items = list(items_dict.values())
        
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
            data=items,
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
    """处理库存及批次属性的保存操作"""
    try:
        # 现在传入的是完整的Inventory对象
        inventory_data = request.data or {}
        
        print(f"开始处理提交数据: inventory_id={inventory_data.get('inventoryId') or inventory_data.get('inventory_id')}, materialLotFeatureList长度={len(inventory_data.get('materialLotFeatureList', []))}")
        
        # 开始处理数据
        inventory_id = None
        header_result = None
        details_result = None

        currentDateTime = get_server_datetime()
        
        # 1. 处理表头数据
        if not inventory_data:
            return UnifiedResponse(
                success=False,
                code=400,
                message="没有提供要处理的数据",
                error_code="NO_DATA"
            )
        
        # 获取表头数据 - 支持驼峰命名
        header_data = {
            "inventoryId": inventory_data.get("inventoryId") or inventory_data.get("inventory_id"),
            "materialId": inventory_data.get("materialId") or inventory_data.get("material_id"),
            "materialCode": inventory_data.get("materialCode") or inventory_data.get("material_code"),
            "materialDesc": inventory_data.get("materialDesc") or inventory_data.get("material_desc"),
            "plantId": inventory_data.get("plantId") or inventory_data.get("plant_id"),
            "plantName": inventory_data.get("plantName") or inventory_data.get("plant_name"),
            "warehouseId": inventory_data.get("warehouseId") or inventory_data.get("warehouse_id"),
            "warehouseName": inventory_data.get("warehouseName") or inventory_data.get("warehouse_name"),
            "binId": inventory_data.get("binId") or inventory_data.get("bin_id"),
            "binName": inventory_data.get("binName") or inventory_data.get("bin_name"),
            "materialLotId": inventory_data.get("materialLotId") or inventory_data.get("material_lot_id"),
            "lotNo": inventory_data.get("lotNo") or inventory_data.get("lot_no"),
            "lotDesc": inventory_data.get("lotDesc") or inventory_data.get("lot_desc"),
            "stockQty": inventory_data.get("stockQty", 0.0) or inventory_data.get("stock_qty", 0.0),
            "unitIdStock": inventory_data.get("unitIdStock") or inventory_data.get("unit_id_stock"),
            "stockQtySecond": inventory_data.get("stockQtySecond", 0.0) or inventory_data.get("stock_qty_second", 0.0),
            "unitIdStockSec": inventory_data.get("unitIdStockSec") or inventory_data.get("unit_id_stock_sec"),
            "stockQtyLocked": inventory_data.get("stockQtyLocked", 0.0) or inventory_data.get("stock_qty_locked", 0.0),
            "stockQtySecondLocked": inventory_data.get("stockQtySecondLocked", 0.0) or inventory_data.get("stock_qty_second_locked", 0.0),
            "approveStatus": inventory_data.get("approveStatus", "N") or inventory_data.get("approve_status", "N")
        }
        
        # 注意：materialLotFeatureList现在在materialLot对象内部，不在这里直接处理

        
        
        # 检查是更新还是创建
        inventory_id = header_data.get("inventoryId")
        
        # 调用 read 操作获取现有记录
        read_request = UnifiedRequest(
            action="read",
            module="inventory",
            data={"inventory_id": inventory_id}
        )
        read_response = _handle_unified_read(read_request, session, current_user)
        
        # 判断 read_response 返回有 Inventory 对象还是空值
        inventory_exists = read_response.success and read_response.data is not None
        
        # 根据 read_response.data 是否为空，执行新增或更改操作
        if inventory_exists and read_response.data:
            # 更新现有记录
            inventory_data = read_response.data
            inventory = session.get(Inventory, inventory_id)
            if inventory:
                # 更新现有表头
                for field, value in header_data.items():
                    if field != "inventoryId" and hasattr(inventory, field):
                        setattr(inventory, field, value)
                
                # 更新修改信息
                inventory.modifierLast = current_user.email
                inventory.modifyDateLast = datetime.now()
                
                session.add(inventory)
                header_result = {"action": "updated", "inventory_id": inventory_id}
        else:
            # 创建新记录
            inventory_create_data = {
                "materialId": header_data.get("materialId", ""),
                "materialCode": header_data.get("materialCode", ""),
                "materialDesc": header_data.get("materialDesc", ""),
                "plantId": header_data.get("plantId"),
                "plantName": header_data.get("plantName"),
                "warehouseId": header_data.get("warehouseId"),
                "warehouseName": header_data.get("warehouseName"),
                "binId": header_data.get("binId"),
                "binName": header_data.get("binName"),
                "materialLotId": header_data.get("materialLotId"),
                "lotNo": header_data.get("lotNo"),
                "lotDesc": header_data.get("lotDesc"),
                "stockQty": header_data.get("stockQty", 0.0),
                "unitIdStock": header_data.get("unitIdStock"),
                "stockQtySecond": header_data.get("stockQtySecond", 0.0),
                "unitIdStockSec": header_data.get("unitIdStockSec"),
                "stockQtyLocked": header_data.get("stockQtyLocked", 0.0),
                "stockQtySecondLocked": header_data.get("stockQtySecondLocked", 0.0),
                "approveStatus": header_data.get("approveStatus", "N")
            }
            
            # 使用传入的 inventory_id 或生成新的
            new_inventory_id = str(uuid.uuid4())
            
            inventory = Inventory(
                inventoryId=new_inventory_id,
                **inventory_create_data,
                creator=current_user.email,
                createDate=currentDateTime,
                modifierLast=None,
                modifyDateLast=None
            )
            
            session.add(inventory)
            inventory_id = new_inventory_id
            header_result = {"action": "created", "inventory_id": inventory_id}
        
        # 2. 处理明细数据 - 现在在materialLot对象内部处理，不在这里直接处理
        
        # 提交所有更改到数据库
        session.commit()
        
        # 重新获取完整的 Inventory 对象
        inventory = session.get(Inventory, inventory_id)
        
        # 构建返回数据
        result_data = inventory.model_dump()
        
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
    """处理读取操作 - 根据主键获取单个 Inventory 对象"""
    try:
        data = request.data or {}
        inventory_id = data.get("inventory_id")
        
        if not inventory_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少inventory_id参数",
                error_code="MISSING_INVENTORY_ID"
            )
        
        # 直接查询数据库获取主表数据
        inventory = session.get(Inventory, inventory_id)
        
        if not inventory:
            return UnifiedResponse(
                success=False,
                code=404,
                message=f"未找到 inventory_id 为 {inventory_id} 的记录",
                error_code="INVENTORY_NOT_FOUND"
            )
        
        # 查询子表数据
        inventory_features = session.exec(
            select(MaterialLotFeature).where(MaterialLotFeature.material_lot_id == inventory_id)
        ).all()
        
        # 构建返回数据，包含完整的 Inventory 对象和子对象列表
        result_data = inventory.model_dump()
        result_data["materialLotFeatureList"] = [attr.model_dump() for attr in inventory_features]
        
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


def _test_database_connection(session: SessionDep) -> bool:
    """测试数据库连接是否正常"""
    try:
        print("测试数据库连接...")
        # 执行一个简单的查询来测试连接
        from sqlmodel import select
        from app.models import User
        stmt = select(User).limit(1)
        result = session.exec(stmt).first()
        print("数据库连接测试成功")
        return True
    except Exception as e:
        print(f"数据库连接测试失败: {e}")
        return False


def _handle_unified_batch_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理批量保存操作 - 处理inventory的内在子对象关系"""
    print("=== 进入 _handle_unified_batch_save 函数 ===")
    
        
    try:
        # 确保session处于干净状态
        if session.in_transaction():
            print("检测到活跃事务，回滚...")
            session.rollback()
        
        # 设置session参数
        session.autoflush = False
        session.autocommit = False
        # 获取批量数据
        batch_data = request.data or []
        print(f"接收到批量数据，类型: {type(batch_data)}, 长度: {len(batch_data) if isinstance(batch_data, list) else 'N/A'}")
        
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
        
        currentDateTime = get_server_datetime()
        results = []
        success_count = 0
        error_count = 0
        
        
        
        # 处理每个inventory对象
        for i, inventory_data in enumerate(batch_data):
            try:
                
                # 提取inventory基本信息
                inventory_id = inventory_data.get("inventoryId") or inventory_data.get("inventory_id")
                material_lot_data = inventory_data.get("materialLot")
                # 1. 处理MaterialLot数据
                material_lot_id = None
                if material_lot_data:
                    
                    material_lot_id = material_lot_data.get("materialLotId") or material_lot_data.get("material_lot_id")
                    # 提取materialLotFeatureList（如果存在）
                    material_lot_features_data = material_lot_data.get("materialLotFeatureList", [])
                    
                    # 直接创建新记录，不检查是否存在
                    if not material_lot_id:
                        material_lot_id = str(uuid.uuid4())
                    
                    # 创建MaterialLot对象，排除materialLotFeatureList字段
                    material_lot_create_data = {
                        "materialLotId": material_lot_id,
                        "materialId": material_lot_data.get("materialId", "") or material_lot_data.get("material_id", ""),
                        "materialCode": material_lot_data.get("materialCode", "") or material_lot_data.get("material_code", ""),
                        "materialDesc": material_lot_data.get("materialDesc", "") or material_lot_data.get("material_desc", ""),
                        "lotNo": material_lot_data.get("lotNo", "") or material_lot_data.get("lot_no", ""),
                        "lotDesc": material_lot_data.get("lotDesc", "") or material_lot_data.get("lot_desc", ""),
                        "manufactureDate": material_lot_data.get("manufactureDate") or material_lot_data.get("manufacture_date"),
                        "remark": material_lot_data.get("remark", ""),
                        "creator": current_user.email,
                        "createDate": currentDateTime,
                        "modifierLast": None,
                        "modifyDateLast": None,
                        "approveStatus": material_lot_data.get("approveStatus", "N") or material_lot_data.get("approve_status", "N"),
                        "approver": material_lot_data.get("approver"),
                        "approveDate": material_lot_data.get("approveDate") or material_lot_data.get("approve_date")
                    }
                    
                    material_lot = MaterialLot(**material_lot_create_data)
                    
                    # 调试：查看生成的SQL语句
                    from sqlalchemy import insert
                                    
                    # 生成INSERT语句
                    stmt = insert(MaterialLot).values(**material_lot_create_data)
                
                    #print(f"编译后SQL: {stmt.compile(compile_kwargs={'literal_binds': True})}")
                    
                    session.add(material_lot)
                   
                    
                    # 处理MaterialLotFeature子对象 - 直接插入
                    if material_lot_features_data:
                        for feature_data in material_lot_features_data:
                            feature_id = feature_data.get("materialLotFeatureId") or feature_data.get("material_lot_feature_id")
                            
                            # 直接创建新记录，不检查是否存在
                            if not feature_id:
                                feature_id = str(uuid.uuid4())
                            
                            feature = MaterialLotFeature(
                                materialLotFeatureId=feature_id,
                                materialLotId=material_lot_id,
                                featureId=feature_data.get("featureId", "") or feature_data.get("feature_id", ""),
                                featureCode=feature_data.get("featureCode", "") or feature_data.get("feature_code", ""),
                                featureDesc=feature_data.get("featureDesc", "") or feature_data.get("feature_desc", ""),
                                featureValue=feature_data.get("featureValue", "") or feature_data.get("feature_value", ""),
                                remark=feature_data.get("remark", ""),
                                creator=current_user.email,
                                createDate=currentDateTime,
                                modifierLast=None,
                                modifyDateLast=None,
                                approveStatus=feature_data.get("approveStatus", "N") or feature_data.get("approve_status", "N"),
                                approver=feature_data.get("approver"),
                                approveDate=feature_data.get("approveDate") or feature_data.get("approve_date")
                            )
                            
                            # 调试：查看生成的SQL语句
                            feature_data_for_sql = {
                                "materialLotFeatureId": feature_id,
                                "materialLotId": material_lot_id,
                                "featureId": feature_data.get("featureId", "") or feature_data.get("feature_id", ""),
                                "featureCode": feature_data.get("featureCode", "") or feature_data.get("feature_code", ""),
                                "featureDesc": feature_data.get("featureDesc", "") or feature_data.get("feature_desc", ""),
                                "featureValue": feature_data.get("featureValue", "") or feature_data.get("feature_value", ""),
                                "remark": feature_data.get("remark", ""),
                                "creator": current_user.email,
                                "createDate": currentDateTime,
                                "modifierLast": None,
                                "modifyDateLast": None,
                                "approveStatus": feature_data.get("approveStatus", "N") or feature_data.get("approve_status", "N"),
                                "approver": feature_data.get("approver"),
                                "approveDate": feature_data.get("approveDate") or feature_data.get("approve_date")
                            }
                            
                           
                            
                            # 生成INSERT语句
                            stmt = insert(MaterialLotFeature).values(**feature_data_for_sql)
                           
                            
                            session.add(feature)
                           
            
                
                # 支持驼峰命名和下划线命名
                inventory_id = inventory_data.get("inventoryId") or inventory_data.get("inventory_id")
                
                # 直接创建新记录，不检查是否存在
                if not inventory_id:
                    inventory_id = str(uuid.uuid4())
                
                inventory = Inventory(
                    inventoryId=inventory_id,
                    materialId=inventory_data.get("materialId", "") or inventory_data.get("material_id", ""),
                    materialCode=inventory_data.get("materialCode", "") or inventory_data.get("material_code", ""),
                    materialDesc=inventory_data.get("materialDesc", "") or inventory_data.get("material_desc", ""),
                    plantId=inventory_data.get("plantId") or inventory_data.get("plant_id"),
                    plantName=inventory_data.get("plantName") or inventory_data.get("plant_name"),
                    warehouseId=inventory_data.get("warehouseId") or inventory_data.get("warehouse_id"),
                    warehouseName=inventory_data.get("warehouseName") or inventory_data.get("warehouse_name"),
                    binId=inventory_data.get("binId") or inventory_data.get("bin_id"),
                    binName=inventory_data.get("binName") or inventory_data.get("bin_name"),
                    materialLotId=material_lot_id or "",
                    lotNo=inventory_data.get("lotNo", "") or inventory_data.get("lot_no", ""),
                    lotDesc=inventory_data.get("lotDesc", "") or inventory_data.get("lot_desc", ""),
                    stockQty=inventory_data.get("stockQty", 0.0) or inventory_data.get("stock_qty", 0.0),
                    unitIdStock=inventory_data.get("unitIdStock", "") or inventory_data.get("unit_id_stock", ""),
                    stockQtySecond=inventory_data.get("stockQtySecond", 0.0) or inventory_data.get("stock_qty_second", 0.0),
                    unitIdStockSec=inventory_data.get("unitIdStockSec", "") or inventory_data.get("unit_id_stock_sec", ""),
                    stockQtyLocked=inventory_data.get("stockQtyLocked", 0.0) or inventory_data.get("stock_qty_locked", 0.0),
                    stockQtySecondLocked=inventory_data.get("stockQtySecondLocked", 0.0) or inventory_data.get("stock_qty_second_locked", 0.0),
                    approveStatus=inventory_data.get("approveStatus", "N") or inventory_data.get("approve_status", "N"),
                    approver=inventory_data.get("approver"),
                    approveDate=inventory_data.get("approveDate") or inventory_data.get("approve_date"),
                    creator=current_user.email,
                    createDate=currentDateTime,
                    modifierLast=None,
                    modifyDateLast=None
                )
                
                # 调试：查看生成的SQL语句
                inventory_data_for_sql = {
                    "inventoryId": inventory_id,
                    "materialId": inventory_data.get("materialId", "") or inventory_data.get("material_id", ""),
                    "materialCode": inventory_data.get("materialCode", "") or inventory_data.get("material_code", ""),
                    "materialDesc": inventory_data.get("materialDesc", "") or inventory_data.get("material_desc", ""),
                    "plantId": inventory_data.get("plantId") or inventory_data.get("plant_id"),
                    "plantName": inventory_data.get("plantName") or inventory_data.get("plant_name"),
                    "warehouseId": inventory_data.get("warehouseId") or inventory_data.get("warehouse_id"),
                    "warehouseName": inventory_data.get("warehouseName") or inventory_data.get("warehouse_name"),
                    "binId": inventory_data.get("binId") or inventory_data.get("bin_id"),
                    "binName": inventory_data.get("binName") or inventory_data.get("bin_name"),
                    "materialLotId": material_lot_id or "",
                    "lotNo": inventory_data.get("lotNo", "") or inventory_data.get("lot_no", ""),
                    "lotDesc": inventory_data.get("lotDesc", "") or inventory_data.get("lot_desc", ""),
                    "stockQty": inventory_data.get("stockQty", 0.0) or inventory_data.get("stock_qty", 0.0),
                    "unitIdStock": inventory_data.get("unitIdStock", "") or inventory_data.get("unit_id_stock", ""),
                    "stockQtySecond": inventory_data.get("stockQtySecond", 0.0) or inventory_data.get("stock_qty_second", 0.0),
                    "unitIdStockSec": inventory_data.get("unitIdStockSec", "") or inventory_data.get("unit_id_stock_sec", ""),
                    "stockQtyLocked": inventory_data.get("stockQtyLocked", 0.0) or inventory_data.get("stock_qty_locked", 0.0),
                    "stockQtySecondLocked": inventory_data.get("stockQtySecondLocked", 0.0) or inventory_data.get("stock_qty_second_locked", 0.0),
                    "approveStatus": inventory_data.get("approveStatus", "N") or inventory_data.get("approve_status", "N"),
                    "approver": inventory_data.get("approver"),
                    "approveDate": inventory_data.get("approveDate") or inventory_data.get("approve_date"),
                    "creator": current_user.email,
                    "createDate": currentDateTime,
                    "modifierLast": None,
                    "modifyDateLast": None
                }
                
                # 生成INSERT语句
                stmt = insert(Inventory).values(**inventory_data_for_sql)
                
                session.add(inventory)
                session.commit()
                print(f"处理数据: {i+1}")
                
                # 每笔数据成功处理后立即提交
               
                    
            except Exception as e:
                # 每笔数据处理失败时立即回滚
              
                print(f"第 {i+1} 条数据处理异常，立即回滚: {str(e)}")
                session.rollback()
                error_count += 1
                results.append({
                    "success": False,
                    "inventory_id": inventory_data.get("inventory_id", "unknown"),
                    "error": str(e)
                })
                return UnifiedResponse(
                success=False,
                code=500,
                message=f"批量保存失败: {str(e)}",
                error_code="BATCH_SAVE_FAILED"
                )
                # 继续处理其他数据
        
        
        # 检查是否有成功的处理
        if success_count > 0:
            return UnifiedResponse(
                success=True,
                code=200,
                data={
                    "total": len(batch_data),
                    "success_count": success_count,
                    "error_count": error_count,
                    "results": results
                },
                message=f"批量保存完成：成功 {success_count} 条，失败 {error_count} 条"
            )
        else:
            return UnifiedResponse(
                success=False,
                code=400,
                data={
                    "total": len(batch_data),
                    "success_count": 0,
                    "error_count": error_count,
                    "results": results
                },
                message=f"批量保存失败：所有 {error_count} 条数据都处理失败"
            )
        
    except Exception as e:
        print(f"批量保存失败: {str(e)}")
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"批量保存失败: {str(e)}",
            error_code="BATCH_SAVE_FAILED"
        )