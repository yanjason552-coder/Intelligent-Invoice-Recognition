"""
ProductionOrder API - 生产订单相关接口
"""

import uuid
from typing import Any, List, Optional, Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select, or_, text

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    UnifiedRequest,
    UnifiedResponse
)
from app.models import (
    ProductionOrder,
    ProductionOrderD,
    ProductionOrderProduce,
    ProductionOrderRouting
)
from app.utils import get_server_datetime

router = APIRouter(prefix="/productionOrder", tags=["productionOrder"])

def assemble_production_order_data(results: List[Any]) -> List[Dict[str, Any]]:
    """装配生产订单数据，将SQL查询结果转换为嵌套的数据结构"""
    production_order_map = {}
    
    for row in results:
        row_dict = dict(row._mapping)
        
        # 主表数据
        production_order_id = row_dict.get("production_order_id")
        if production_order_id and production_order_id not in production_order_map:
            production_order_dict = {}
            
            production_order_dict["productionOrderId"] = row_dict.get("production_order_id")
            production_order_dict["orderNo"] = row_dict.get("order_no")
            production_order_dict["orderDate"] = row_dict.get("order_date")
            production_order_dict["customerId"] = row_dict.get("customer_id")
            production_order_dict["customerName"] = row_dict.get("customer_name")
            production_order_dict["status"] = row_dict.get("status")
            production_order_dict["remark"] = row_dict.get("remark")
            production_order_dict["creator"] = row_dict.get("creator")
            production_order_dict["createDate"] = row_dict.get("create_date")
            production_order_dict["modifierLast"] = row_dict.get("modifier_last")
            production_order_dict["modifyDateLast"] = row_dict.get("modify_date_last")
            production_order_dict["approveStatus"] = row_dict.get("approve_status")
            production_order_dict["approver"] = row_dict.get("approver")
            production_order_dict["approveDate"] = row_dict.get("approve_date")
            production_order_dict["productOrderDList"] = []
            production_order_dict["productOrderProductionList"] = []
            production_order_dict["productOrderRoutingList"] = []
            production_order_map[production_order_id] = production_order_dict
        
        # 明细表数据
        if row_dict.get("production_order_d_id") and production_order_id:
            detail_id = row_dict["production_order_d_id"]
            detail_exists = any(d.get("productionOrderDId") == detail_id 
                              for d in production_order_map[production_order_id]["productOrderDList"])
            
            if not detail_exists:
                detail_dict = {}
                detail_dict["productionOrderDId"] = row_dict.get("production_order_d_id")
                detail_dict["productionOrderId"] = row_dict.get("production_order_id")
                detail_dict["materialId"] = row_dict.get("material_id")
                detail_dict["materialCode"] = row_dict.get("material_code")
                detail_dict["materialDescription"] = row_dict.get("material_description")
                detail_dict["qty"] = row_dict.get("qty")
                detail_dict["unitId"] = row_dict.get("unit_id")
                detail_dict["plannedStartDate"] = row_dict.get("planned_start_date")
                detail_dict["plannedEndDate"] = row_dict.get("planned_end_date")
                detail_dict["actualStartDate"] = row_dict.get("actual_start_date")
                detail_dict["actualEndDate"] = row_dict.get("actual_end_date")
                detail_dict["status"] = row_dict.get("status")
                
                production_order_map[production_order_id]["productOrderDList"].append(detail_dict)
        
        # 产出表数据
        if row_dict.get("production_order_production_id") and production_order_id:
            production_id = row_dict["production_order_production_id"]
            production_exists = any(p.get("productionOrderProductionId") == production_id 
                                  for p in production_order_map[production_order_id]["productOrderProductionList"])
            
            if not production_exists:
                production_dict = {}
                production_dict["productionOrderProductionId"] = row_dict.get("production_order_production_id")
                production_dict["productionOrderId"] = row_dict.get("production_order_id")
                production_dict["seq"] = row_dict.get("seq")
                production_dict["outputType"] = row_dict.get("output_type")
                production_dict["materialId"] = row_dict.get("material_id")
                production_dict["materialCode"] = row_dict.get("material_code")
                production_dict["materialDescription"] = row_dict.get("material_description")
                production_dict["warehouseId"] = row_dict.get("warehouse_id")
                production_dict["planQty"] = row_dict.get("plan_qty")
                production_dict["qualifiedQty"] = row_dict.get("qualified_qty")
                production_dict["unitId"] = row_dict.get("unit_id")
                production_dict["qualifiedQtyStock"] = row_dict.get("qualified_qty_stock")
                production_dict["unitIdStock"] = row_dict.get("unit_id_stock")
                production_dict["qualifiedQtySecond"] = row_dict.get("qualified_qty_second")
                production_dict["unitIdSecond"] = row_dict.get("unit_id_second")
                production_dict["remark"] = row_dict.get("remark")
                
                production_order_map[production_order_id]["productOrderProductionList"].append(production_dict)
        
        # 工序表数据
        if row_dict.get("production_order_routing_id") and production_order_id:
            routing_id = row_dict["production_order_routing_id"]
            routing_exists = any(r.get("productionOrderRoutingId") == routing_id 
                               for r in production_order_map[production_order_id]["productOrderRoutingList"])
            
            if not routing_exists:
                routing_dict = {}
                routing_dict["productionOrderRoutingId"] = row_dict.get("production_order_routing_id")
                routing_dict["productionOrderId"] = row_dict.get("production_order_id")
                routing_dict["seq"] = row_dict.get("seq")
                routing_dict["operationId"] = row_dict.get("operation_id")
                routing_dict["operationDesc"] = row_dict.get("operation_desc")
                routing_dict["planQty"] = row_dict.get("plan_qty")
                routing_dict["unitId"] = row_dict.get("unit_id")
                routing_dict["remark"] = row_dict.get("remark")
                
                production_order_map[production_order_id]["productOrderRoutingList"].append(routing_dict)
    
    return list(production_order_map.values())

@router.post("/unified", response_model=UnifiedResponse)
def unified_production_order_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的生产订单操作API"""
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
        # TODO: 实现创建生产订单的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="创建生产订单成功",
            data={"id": "temp_id"}
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"创建生产订单失败: {str(e)}",
            error_code="CREATE_FAILED"
        )

def _handle_unified_delete(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理删除操作"""
    try:
        # TODO: 实现删除生产订单的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="删除生产订单成功"
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"删除生产订单失败: {str(e)}",
            error_code="DELETE_FAILED"
        )

def _handle_unified_list(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理列表查询操作"""
    try:
        page = request.page if request.page else 1
        limit = request.limit if request.limit else 50
        offset = (page - 1) * limit
        
        base_sql = """
        SELECT 
            production_order.*,
            production_order_d.*
        FROM production_order
        LEFT JOIN production_order_d 
        ON production_order.production_order_id = production_order_d.production_order_id
        """
        
        where_conditions = []
        params = {}
        
        if request.filters:
            for field, value in request.filters.items():
                if value is not None:
                    param_name = f"param_{field}"
                    if isinstance(value, str) and value.startswith('%') and value.endswith('%'):
                        where_conditions.append(f"production_order.{field} LIKE :{param_name}")
                    else:
                        where_conditions.append(f"production_order.{field} = :{param_name}")
                    params[param_name] = value
        
        if where_conditions:
            base_sql += " WHERE " + " AND ".join(where_conditions)
        
        if request.sort:
            order_clauses = []
            for field, direction in request.sort.items():
                order_clauses.append(f"production_order.{field} {direction.upper()}")
            
            if order_clauses:
                base_sql += " ORDER BY " + ", ".join(order_clauses)
        
        base_sql += f" LIMIT {limit} OFFSET {offset}"
        
        result = session.exec(text(base_sql), **params if params else {})
        results = result.all()
        
        count_sql = """
        SELECT COUNT(DISTINCT production_order.production_order_id) as total
        FROM production_order
        LEFT JOIN production_order_d ON production_order.production_order_id = production_order_d.production_order_id
        """
        
        if where_conditions:
            count_sql += " WHERE " + " AND ".join(where_conditions)
        
        count_result = session.exec(text(count_sql), **params).first()
        total = count_result[0] if count_result else 0
        
        data = assemble_production_order_data(results)
        
        return UnifiedResponse(
            success=True,
            code=200,
            message="查询生产订单列表成功",
            data=data,
            pagination={
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"查询生产订单列表失败: {str(e)}",
            error_code="LIST_FAILED"
        )

def _handle_unified_read(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理读取操作"""
    try:
        production_order_id = None
        
        if request.data and isinstance(request.data, dict):
            production_order_id = request.data.get("productionOrderId")
        
        if not production_order_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少必要的参数: productionOrderId",
                error_code="MISSING_PARAMETER"
            )
        
        sql_query = """
        SELECT 
            product_order.*,
            product_order_d.*
        FROM product_order
        LEFT JOIN product_order_d ON product_order.production_order_id = product_order_d.production_order_id
        WHERE product_order.production_order_id = '"""
        sql_query = sql_query + production_order_id + "'"
        
        result = session.exec(text(sql_query))
        results = result.all()
       
        if not results:
            return UnifiedResponse(
                success=False,
                code=404,
                message=f"未找到ID为 {production_order_id} 的生产订单记录",
                error_code="NOT_FOUND"
            )
        
        assembled_data = assemble_production_order_data(results)
        
        if len(assembled_data) == 0:
            return UnifiedResponse(
                success=False,
                code=404,
                message=f"未找到ID为 {production_order_id} 的生产订单记录",
                error_code="NOT_FOUND"
            )
        
        data = assembled_data[0]
        
        return UnifiedResponse(
            success=True,
            code=200,
            message="读取生产订单成功",
            data=data
        )
        
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"读取生产订单失败: {str(e)}",
            error_code="READ_FAILED"
        )

def _handle_unified_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理保存操作"""
    try:
        # TODO: 实现保存生产订单的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="保存生产订单成功"
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"保存生产订单失败: {str(e)}",
            error_code="SAVE_FAILED"
        )

def _handle_unified_batch_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理批量保存操作"""
    try:
        # TODO: 实现批量保存生产订单的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="批量保存生产订单成功"
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"批量保存生产订单失败: {str(e)}",
            error_code="BATCH_SAVE_FAILED"
        )