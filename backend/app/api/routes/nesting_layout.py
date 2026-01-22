"""
NestingLayout API - 套料排版相关接口
"""

import uuid
from typing import Any, List, Optional, Dict, Any
from datetime import datetime
import pandas as pd

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select, or_, text

from app.api.routes.material import _handle_unified_list as material_list
from app.api.routes.direct_matching import DirectMatching
from app.api.routes.self_matching import self_matching
from app.api.routes.two_sided_matching import two_sided_matching
from app.api.routes.failde_matching import Failed_matching
from app.api.routes.MaterialNestingVisualization_111 import MaterialNestingVisualization
from app.api.routes.max10_failclass import MAX10Failclass

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    UnifiedRequest,
    UnifiedResponse
)
from app.models import (
    Material, MaterialD,
    NestingLayout, 
    NestingLayoutD,
    NestingLayoutSd,
    Inventory, MaterialLotFeature
)
from app.utils import get_server_datetime

router = APIRouter(prefix="/nesting-layout", tags=["nesting-layout"])

def assemble_nesting_layout_data(results: List[Any]) -> List[Dict[str, Any]]:
    """
    装配套料排版数据，将SQL查询结果转换为嵌套的数据结构
    
    Args:
        results: SQL查询结果列表
        
    Returns:
        装配好的嵌套数据结构列表
    """
    # 组织数据结构 - 按主表分组，装配子对象列表
    nesting_layout_map = {}
    
    for row in results:
        # 将SQL结果行转换为字典
        row_dict = dict(row._mapping)
        
        # 提取主表数据
        nesting_layout_id = row_dict.get("nesting_layout_id")
        if nesting_layout_id and nesting_layout_id not in nesting_layout_map:
            # 初始化主表记录
            nesting_layout_dict = {}
            
            nesting_layout_dict["nestingLayoutId"] = row_dict.get("nesting_layout_id")
            nesting_layout_dict["plantId"] = row_dict.get("plant_id")
            nesting_layout_dict["nestingEmployeeId"] = row_dict.get("nesting_employee_id")
            nesting_layout_dict["nestingDate"] = row_dict.get("nesting_date")
            nesting_layout_dict["nestingDesc"] = row_dict.get("nesting_desc")
            nesting_layout_dict["remark"] = row_dict.get("remark")
            nesting_layout_dict["creator"] = row_dict.get("creator")
            nesting_layout_dict["createDate"] = row_dict.get("create_date")
            nesting_layout_dict["modifierLast"] = row_dict.get("modifier_last")
            nesting_layout_dict["modifyDateLast"] = row_dict.get("modify_date_last")
            nesting_layout_dict["approveStatus"] = row_dict.get("approve_status")
            nesting_layout_dict["approver"] = row_dict.get("approver")
            nesting_layout_dict["approveDate"] = row_dict.get("approve_date")
            nesting_layout_dict["rateOfFinished"] = row_dict.get("rate_of_finished")
            nesting_layout_dict["rateOfSurplus"] = row_dict.get("rate_of_surplus")
            nesting_layout_dict["nestingLayoutDList"] = []
            nesting_layout_map[nesting_layout_id] = nesting_layout_dict
        
        # 提取明细表数据
        if row_dict.get("nesting_layout_d_id") and nesting_layout_id:
            detail_id = row_dict["nesting_layout_d_id"]
            # 检查是否已添加过该明细
            detail_exists = any(d.get("nestingLayoutDId") == detail_id 
                              for d in nesting_layout_map[nesting_layout_id]["nestingLayoutDList"])
            
            if not detail_exists:
                detail_dict = {}
                detail_dict["nestingLayoutDId"] = row_dict.get("nesting_layout_d_id")
                detail_dict["nestingLayoutId"] = row_dict.get("nesting_layout_id")
                detail_dict["warehouseId"] = row_dict.get("warehouse_id")
                detail_dict["binId"] = row_dict.get("bin_id")
                detail_dict["materialId"] = row_dict.get("material_id")
                detail_dict["materialCode"] = row_dict.get("material_code")
                detail_dict["materialDescription"] = row_dict.get("material_description")
                detail_dict["materialLotId"] = row_dict.get("material_lot_id")
                detail_dict["lotNo"] = row_dict.get("lot_no")
                detail_dict["lotDesc"] = row_dict.get("lot_desc")
                detail_dict["sn"] = row_dict.get("sn")
                detail_dict["startPositionX"] = row_dict.get("start_position_x")
                detail_dict["startPositionY"] = row_dict.get("start_position_y")
                detail_dict["endPositionX"] = row_dict.get("end_position_x")
                detail_dict["endPositionY"] = row_dict.get("end_position_y")
                detail_dict["nestingedQty"] = row_dict.get("nestinged_qty")
                detail_dict["unitId"] = row_dict.get("unit_id")
                detail_dict["nestingedSecondQty"] = row_dict.get("nestinged_second_qty")
                detail_dict["unitIdSecond"] = row_dict.get("unit_id_second")
                detail_dict["nestingedSoQty"] = row_dict.get("nestinged_so_qty")
                detail_dict["unitIdSo"] = row_dict.get("unit_id_so")
                detail_dict["stockQty"] = row_dict.get("stock_qty")
                detail_dict["availableStockQty"] = row_dict.get("available_stock_qty")
                detail_dict["remainingStockQty"] = row_dict.get("remaining_stock_qty")
                
                detail_dict["nestingLayoutSdList"] = []
                nesting_layout_map[nesting_layout_id]["nestingLayoutDList"].append(detail_dict)
            
            # 提取子明细表数据
            if row_dict.get("nesting_layout_sd_id"):
                sub_detail_id = row_dict["nesting_layout_sd_id"]
                detail_id = row_dict["nesting_layout_d_id"]
                
                # 找到对应的明细记录
                target_detail = None
                for detail in nesting_layout_map[nesting_layout_id]["nestingLayoutDList"]:
                    if detail["nestingLayoutDId"] == detail_id:
                        target_detail = detail
                        break
                
                if target_detail:
                    # 检查是否已添加过该子明细
                    sub_detail_exists = any(sd.get("nestingLayoutSdId") == sub_detail_id 
                                          for sd in target_detail["nestingLayoutSdList"])
                    
                    if not sub_detail_exists:
                        sub_detail_dict = {}
                        
                        sub_detail_dict["nestingLayoutSdId"] = row_dict.get("nesting_layout_sd_id")
                        sub_detail_dict["nestingLayoutDId"] = row_dict.get("nesting_layout_d_id")
                        sub_detail_dict["salesOrderDocDId"] = row_dict.get("sales_order_doc_d_id")
                        sub_detail_dict["soItemSequenceNo"] = row_dict.get("so_item_sequence_no")
                        sub_detail_dict["fX"] = row_dict.get("f_x")
                        sub_detail_dict["fY"] = row_dict.get("f_y")
                        sub_detail_dict["tX"] = row_dict.get("t_x")
                        sub_detail_dict["tY"] = row_dict.get("t_y")
                        sub_detail_dict["nestingedQty"] = row_dict.get("nestinged_qty")
                        sub_detail_dict["unitId"] = row_dict.get("unit_id")
                        sub_detail_dict["nestingedSecondQty"] = row_dict.get("nestinged_second_qty")
                        sub_detail_dict["unitIdSecond"] = row_dict.get("unit_id_second")
                        sub_detail_dict["nestingedSoQty"] = row_dict.get("nestinged_so_qty")
                        sub_detail_dict["unitIdSo"] = row_dict.get("unit_id_so")
                        
                        target_detail["nestingLayoutSdList"].append(sub_detail_dict)
    
    # 转换为列表
    return list(nesting_layout_map.values())

@router.post("/unified", response_model=UnifiedResponse)
def unified_nesting_layout_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的nesting-layout操作API"""
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
# 定义安全转换为浮点数的工具函数
def safe_float(value, default=0.0):
    """
    将输入值安全转换为浮点数
    :param value: 待转换的值（可能是字符串、None等）
    :param default: 转换失败时的默认值
    :return: 转换后的浮点数或默认值
    """
    if not value:  # 处理空字符串、None等
        return default
    try:
        return float(str(value).strip())  # 去除首尾空格后转换
    except (ValueError, TypeError):  # 处理非数字字符串（如"abc"）
        return default

def _handle_unified_create(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理创建操作，整合套料排版功能"""
    try:
        # 整合套料排版功能
        try:
            # 从请求中获取数据
            request_data = request.data or {}
            selected_so_data = request_data.get("selectedSoData", [])

            if not selected_so_data:
                return UnifiedResponse(
                    success=False,
                    code=400,
                    message="未提供选中的销售订单数据",
                    error_code="MISSING_ORDER_DATA"
                )

            # 将销售订单数据转换为Orders DataFrame
            orders_rows = []
            for so_item in selected_so_data:
                # 从so_item根节点直接提取所有需要的属性
                order_row = {
                    'NO': so_item.get("docNo", ""),  # 订单单号
                    'docDate': so_item.get("docDate", ""),
                    'deliveryDate': so_item.get("deliveryDate", ""),
                    'materialCode': so_item.get("材质", ""),  # 新增材质提取
                    'Quantity': so_item.get("qty", 0),
                    'Width': safe_float(so_item.get("宽度", "")), 
                    'Length': safe_float(so_item.get("长度", "")), 
                    'Thickness': safe_float(so_item.get("公称厚度", "")), 
                    'ProcessOrder': so_item.get("表面要求", ""),
                    'customerName': so_item.get("customerFullName", "")  # 客户名称
                }
                orders_rows.append(order_row)

            # 生成DataFrame并校验
            Orders = pd.DataFrame(orders_rows)
            if Orders.empty:
                return UnifiedResponse(
                    success=False,
                    code=400,
                    message="提取的销售订单数据为空",
                    error_code="EMPTY_ORDER_DATA"
                )

            print(f"数据提取成功，共获取{len(Orders)}条订单数据")
           
            # 从订单中提取唯一的材质和厚度组合
            print("开始提取订单的材质和厚度...")
            unique_materials = Orders['materialCode'].unique().tolist()
            unique_thicknesses = Orders['Thickness'].unique().tolist()
            
            print(f"订单中包含的材质: {unique_materials}")
            print(f"订单中包含的厚度: {unique_thicknesses}")
            
            # 直接查询数据库获取所有库存数据及其特征
            # 不硬编码审批状态限制，与 inventory.py 保持一致
            print("\n开始查询所有库存数据...")
            inventory_sql = """
            SELECT 
                inv.inventory_id,
                inv.material_lot_id,
                inv.material_code,
                inv.material_desc,
                inv.stock_qty,
                inv.lot_no,
                inv.bin_name,
                inv.warehouse_name,
                inv.approve_status,
                mlf.feature_desc,
                mlf.feature_value
            FROM inventory inv
            LEFT JOIN material_lot_feature mlf 
                ON inv.material_lot_id = mlf.material_lot_id
            WHERE 1=1
            ORDER BY inv.inventory_id, mlf.feature_desc
            """
            
            try:
                result = session.execute(text(inventory_sql))
                rows = result.fetchall()
            except Exception as e:
                return UnifiedResponse(
                    success=False,
                    code=500,
                    message=f"查询库存数据库失败: {str(e)}",
                    error_code="DATABASE_QUERY_FAILED"
                )
            
            print(f"成功查询到 {len(rows)} 行数据（包含特征信息）")
            
            if not rows:
                return UnifiedResponse(
                    success=False,
                    code=400,
                    message="未找到任何库存数据",
                    error_code="NO_INVENTORY_DATA"
                )
            
            # 处理查询结果，按 inventory_id 分组，构建库存数据结构
            inventory_map = {}
            for row in rows:
                inventory_id = row.inventory_id
                
                if inventory_id not in inventory_map:
                    inventory_map[inventory_id] = {
                        'inventoryId': row.inventory_id,
                        'materialLotId': row.material_lot_id,
                        'materialCode': row.material_code,
                        'materialDesc': row.material_desc,
                        'stockQty': row.stock_qty,
                        'lotNo': row.lot_no,
                        'binName': row.bin_name,
                        'warehouseName': row.warehouse_name,
                        'approveStatus': row.approve_status,
                        'features': {}  # 存储特征字段
                    }
                
                # 收集特征信息
                if row.feature_desc and row.feature_value:
                    inventory_map[inventory_id]['features'][row.feature_desc] = row.feature_value
            
            all_inventory_data = list(inventory_map.values())
            print(f"处理后得到 {len(all_inventory_data)} 条库存记录")
            
            # 调试：输出前3条库存的特征信息
            if len(all_inventory_data) > 0:
                print("\n调试信息：前3条库存的特征数据示例")
                for idx, inv in enumerate(all_inventory_data[:3]):
                    print(f"  库存{idx+1}:")
                    print(f"    inventoryId: {inv.get('inventoryId')}")
                    print(f"    materialCode: {inv.get('materialCode')}")
                    print(f"    materialDesc: {inv.get('materialDesc')}")
                    print(f"    features: {inv.get('features')}")
                print("")
            
            # 按材质和厚度组合筛选库存数据（在内存中进行）
            material_information_rows = []
            
            for material_code in unique_materials:
                print(f"\n处理订单材质: {material_code}")
                
                for thickness in unique_thicknesses:
                    print(f"  处理订单厚度: {thickness}")
                    
                    matched_count = 0
                    checked_count = 0
                    
                    # 遍历所有库存数据，筛选匹配的记录
                    for inv_item in all_inventory_data:
                        checked_count += 1
                        # 从 features 字典中提取特征信息
                        features = inv_item.get('features', {})
                        
                        # 检查材质是否匹配 - 材质存储在 material_lot_feature 中
                        item_material = features.get('材质')
                        if not item_material or item_material != material_code:
                            continue
                        
                        # 检查厚度是否匹配 - 只使用公称厚度
                        item_thickness = features.get('公称厚度')
                        
                        if item_thickness:
                            try:
                                item_thickness_float = float(item_thickness)
                                # 厚度匹配检查（允许一定误差）
                                if abs(item_thickness_float - thickness) > 0.01:
                                    continue
                            except (ValueError, TypeError):
                                continue
                        else:
                            # 如果没有公称厚度，跳过该记录
                            continue
                        
                        # 检查是否为钢卷
                        material_desc = inv_item.get('materialDesc', '')
                        if '钢卷' not in str(material_desc):
                            continue
                        
                        # 提取钢卷信息
                        width = features.get('宽度')
                        identifier = inv_item.get('materialLotId')
                        stock_qty = inv_item.get('stockQty', 0)  # 重量(kg)
                        
                        # 验证必要信息是否完整（宽度、标识、重量）
                        if width and identifier and stock_qty > 0:
                            try:
                                width_float = float(width)  # 宽度(mm)
                                
                                # 根据密度、重量、宽度和厚度计算钢卷长度
                                # 304不锈钢密度: 7.93 g/cm³ = 0.00000793 kg/mm³
                                density = 0.00000793  # kg/mm³
                                
                                # 计算公式:
                                # 体积(mm³) = 重量(kg) / 密度(kg/mm³)
                                # 体积(mm³) = 长度(mm) × 宽度(mm) × 厚度(mm)
                                # 长度(mm) = 重量(kg) / (密度(kg/mm³) × 宽度(mm) × 厚度(mm))
                                
                                length_float = stock_qty / (density * width_float * item_thickness_float)
                                
                                if length_float > 0:
                                    material_info_row = {
                                        'Material': '钢卷',
                                        'Width': width_float,
                                        'Length': length_float,
                                        'Thickness': item_thickness_float,
                                        'MaterialCode': material_code,
                                        'Identifier': identifier,
                                        'InventoryId': inv_item.get('inventoryId'),
                                        'LotNo': inv_item.get('lotNo'),
                                        'StockQty': stock_qty,
                                        'MaterialDesc': material_desc,
                                        'BinName': inv_item.get('binName'),
                                        'WarehouseName': inv_item.get('warehouseName')
                                    }
                                    material_information_rows.append(material_info_row)
                                    matched_count += 1
                                    print(f"      添加钢卷: 材质={material_code}, 宽度={width_float}mm, 厚度={item_thickness_float}mm, 重量={stock_qty}kg, 计算长度={length_float:.2f}mm, 标识={identifier}")
                            except (ValueError, TypeError, ZeroDivisionError) as e:
                                print(f"      跳过无效数据: 宽度={width}, 厚度={item_thickness}, 重量={stock_qty}, 错误={str(e)}")
                    
                    print(f"    检查了 {checked_count} 条库存，匹配到 {matched_count} 条符合材质({material_code})和厚度({thickness})的记录")
                    
                    # 输出前3条库存的特征信息用于调试
                    if matched_count == 0 and checked_count > 0:
                        print(f"    调试信息：显示前3条库存的材质和厚度特征")
                        for idx, inv_item in enumerate(all_inventory_data[:3]):
                            features = inv_item.get('features', {})
                            print(f"      库存{idx+1}: 材质={features.get('材质')}, 公称厚度={features.get('公称厚度')}, materialDesc={inv_item.get('materialDesc')}")
            
            if not material_information_rows:
                return UnifiedResponse(
                    success=False,
                    code=400,
                    message=f"未找到匹配订单材质({unique_materials})和厚度({unique_thicknesses})的钢卷库存数据",
                    error_code="NO_MATERIAL_INVENTORY"
                )
            
            print(f"\n共找到 {len(material_information_rows)} 条可用的钢卷库存")
            MaterialInformation = pd.DataFrame(material_information_rows)
            
            # 1. 直接处理宽度匹配率100%的订单
            RemainOrders, DirectFinalTable, DirectUtilizationTable, MaterialInformation = DirectMatching(
                MaterialInformation, Orders
            )
            
            # 2. 处理匹配率大于95%的单订单
            r_orders, SelfFinalTable, SelfUtilizationTable, MaterialInformation = self_matching(
                MaterialInformation, RemainOrders
            )
            
            # 3. 两两匹配且匹配率大于90%
            # 检查是否还有剩余订单需要处理
            if not r_orders.empty:
                # 检查剩余订单数量是否足够进行两两匹配（至少需要2个订单）
                if len(r_orders) >= 2:
                    print(f"\n还有 {len(r_orders)} 条剩余订单，进行两两匹配...")
                    
                    # 临时保存中间结果用于后续处理
                    with pd.ExcelWriter('temp_self.xlsx') as writer:
                        r_orders.to_excel(writer, sheet_name='Sheet1', index=False)  # MAX10Failclass期望读取Sheet1
                        MaterialInformation.to_excel(writer, sheet_name='MaterialInformation', index=False)
                    
                    MAX10Failclass('temp_self.xlsx', 0)  # 失败订单重分类
                    classifiedOrder = pd.read_excel("分类数据.xlsx", sheet_name='分类结果')
                    MaterialInformation_input = pd.read_excel('temp_self.xlsx', sheet_name='MaterialInformation')
                    
                    FailedOrders, BestMatches, PairFinalTable, PairUtilizationTable, MaterialInformation_updated = two_sided_matching(
                        MaterialInformation_input, classifiedOrder
                    )
                    
                    # 4. 失败订单匹配
                    MaterialInformation_failed = MaterialInformation_updated
                    FailedTable, FailedUtilizationTable, MaterialInformation_final = Failed_matching(
                        MaterialInformation_failed, FailedOrders
                    )
                else:
                    # 剩余订单不足2个，无法进行两两匹配，直接进入失败订单匹配
                    print(f"\n只剩 {len(r_orders)} 条订单，不足2个无法进行两两匹配，直接进入失败订单匹配...")
                    
                    # 跳过两两匹配，创建空的DataFrame
                    PairFinalTable = pd.DataFrame()
                    PairUtilizationTable = pd.DataFrame()
                    
                    # 直接将剩余订单作为失败订单处理
                    FailedTable, FailedUtilizationTable, MaterialInformation_final = Failed_matching(
                        MaterialInformation, r_orders
                    )
            else:
                print("\n所有订单已在前两步匹配完成，无需进行两两匹配和失败匹配")
                # 创建空的DataFrame，保持数据结构一致
                PairFinalTable = pd.DataFrame()
                PairUtilizationTable = pd.DataFrame()
                FailedTable = pd.DataFrame()
                FailedUtilizationTable = pd.DataFrame()
                MaterialInformation_final = MaterialInformation
            
            # 合并所有套料数据
            AllFinalTable = pd.concat(
                [DirectFinalTable, SelfFinalTable, PairFinalTable, FailedTable],
                ignore_index=True
            )
            
            print("\n" + "="*80)
            print("套料结果汇总 - AllFinalTable")
            print("="*80)
            print(f"总记录数: {len(AllFinalTable)}")
            if not AllFinalTable.empty:
                print(f"列名: {list(AllFinalTable.columns)}")
                print("\n前5条记录:")
                print(AllFinalTable.head().to_string())
            else:
                print("AllFinalTable 为空")
            print("="*80 + "\n")
            
            # 补全前端需要的字段信息
            if not AllFinalTable.empty:
                print("\n开始补全前端所需的字段信息...")
                print(f"AllFinalTable 当前列名: {list(AllFinalTable.columns)}")
                print(f"MaterialInformation_final 列名: {list(MaterialInformation_final.columns)}")
                
                # 创建 MaterialInformation 的查找字典，以 Identifier 为键
                material_info_dict = {}
                if not MaterialInformation_final.empty:
                    print(f"MaterialInformation_final 记录数: {len(MaterialInformation_final)}")
                    for idx, row in MaterialInformation_final.iterrows():
                        identifier = row.get('Identifier')
                        if identifier:
                            material_info_dict[identifier] = {
                                'MaterialCode': row.get('MaterialCode', ''),
                                'MaterialDesc': row.get('MaterialDesc', ''),
                                'WarehouseName': row.get('WarehouseName', ''),
                                'BinName': row.get('BinName', ''),
                                'LotNo': row.get('LotNo', ''),
                                'StockQty': row.get('StockQty', 0),
                                'InventoryId': row.get('InventoryId', '')
                            }
                    print(f"成功创建 {len(material_info_dict)} 个钢卷信息字典")
                
                # 确保 AllFinalTable 包含所有必要的列
                required_columns = [
                    'material_code', 'material_desc', 'warehouse_name', 
                    'bin_name', 'lot_no', 'stock_qty', 'stock_qty_locked', 'nesting_qty'
                ]
                
                # 如果列不存在或为空，从 MaterialInformation 补充
                for col in required_columns:
                    if col not in AllFinalTable.columns:
                        AllFinalTable[col] = ''
                
                # 遍历每一行，补充缺失的信息
                matched_count = 0
                for idx, row in AllFinalTable.iterrows():
                    # 获取钢卷标识符（可能的列名）
                    identifier = None
                    for id_col in ['SteelRollIdentifier', 'Identifier', 'Steel_Identifier', 'identifier', 'MaterialLotId', 'material_lot_id', 'steel_roll_identifier']:
                        if id_col in row and pd.notna(row[id_col]):
                            identifier = row[id_col]
                            if idx < 3:  # 调试信息
                                print(f"  第{idx+1}行: 从列'{id_col}'获取identifier={identifier}")
                            break
                    
                    if identifier and identifier in material_info_dict:
                        matched_count += 1
                        material_info = material_info_dict[identifier]
                        
                        # 补充物料编码 - 检查所有可能的现有字段
                        current_material_code = row.get('material_code') or row.get('MaterialCode') or ''
                        if not current_material_code or str(current_material_code).strip() == '':
                            AllFinalTable.at[idx, 'material_code'] = material_info['MaterialCode']
                        elif 'material_code' not in AllFinalTable.columns or pd.isna(AllFinalTable.at[idx, 'material_code']):
                            AllFinalTable.at[idx, 'material_code'] = material_info['MaterialCode']
                        
                        # 补充物料描述
                        current_material_desc = row.get('material_desc') or row.get('MaterialDesc') or ''
                        if not current_material_desc or str(current_material_desc).strip() == '':
                            AllFinalTable.at[idx, 'material_desc'] = material_info['MaterialDesc']
                        elif 'material_desc' not in AllFinalTable.columns or pd.isna(AllFinalTable.at[idx, 'material_desc']):
                            AllFinalTable.at[idx, 'material_desc'] = material_info['MaterialDesc']
                        
                        # 补充仓库名称
                        current_warehouse = row.get('warehouse_name') or row.get('WarehouseName') or ''
                        if not current_warehouse or str(current_warehouse).strip() == '':
                            AllFinalTable.at[idx, 'warehouse_name'] = material_info['WarehouseName']
                        elif 'warehouse_name' not in AllFinalTable.columns or pd.isna(AllFinalTable.at[idx, 'warehouse_name']):
                            AllFinalTable.at[idx, 'warehouse_name'] = material_info['WarehouseName']
                        
                        # 补充库位名称
                        current_bin = row.get('bin_name') or row.get('BinName') or ''
                        if not current_bin or str(current_bin).strip() == '':
                            AllFinalTable.at[idx, 'bin_name'] = material_info['BinName']
                        elif 'bin_name' not in AllFinalTable.columns or pd.isna(AllFinalTable.at[idx, 'bin_name']):
                            AllFinalTable.at[idx, 'bin_name'] = material_info['BinName']
                        
                        # 补充批号
                        current_lot = row.get('lot_no') or row.get('LotNo') or ''
                        if not current_lot or str(current_lot).strip() == '':
                            AllFinalTable.at[idx, 'lot_no'] = material_info['LotNo']
                        elif 'lot_no' not in AllFinalTable.columns or pd.isna(AllFinalTable.at[idx, 'lot_no']):
                            AllFinalTable.at[idx, 'lot_no'] = material_info['LotNo']
                        
                        # 补充库存数量（钢卷的总重量）
                        current_stock = row.get('stock_qty') or row.get('StockQty') or 0
                        if not current_stock or float(current_stock) == 0:
                            AllFinalTable.at[idx, 'stock_qty'] = material_info['StockQty']
                        elif 'stock_qty' not in AllFinalTable.columns or pd.isna(AllFinalTable.at[idx, 'stock_qty']):
                            AllFinalTable.at[idx, 'stock_qty'] = material_info['StockQty']
                    else:
                        if idx < 3:  # 只打印前3条未匹配的记录用于调试
                            available_ids = [col for col in ['SteelRollIdentifier', 'Identifier', 'Steel_Identifier', 'identifier', 'MaterialLotId'] if col in row]
                            print(f"  警告: 第{idx+1}行未找到匹配的钢卷信息")
                            print(f"    identifier={identifier}, 可用ID列={available_ids}")
                            print(f"    material_info_dict中的键: {list(material_info_dict.keys())[:5]}")
                
                print(f"成功匹配并补全 {matched_count}/{len(AllFinalTable)} 条记录")
                
                # 计算已套数量（stock_qty_locked）- 这里需要查询数据库中已锁定的库存
                # 暂时设置为0，后续可以通过查询 nesting_layout_d 表计算
                if 'stock_qty_locked' not in AllFinalTable.columns:
                    AllFinalTable['stock_qty_locked'] = 0
                else:
                    AllFinalTable['stock_qty_locked'].fillna(0, inplace=True)
                
                # 确保 nesting_qty（本次数量/本次使用重量）存在
                # 计算方法：使用长度 × 钢卷宽度 × 厚度 × 密度 = 重量(kg)
                if 'nesting_qty' not in AllFinalTable.columns:
                    AllFinalTable['nesting_qty'] = 0
                
                # 计算本次使用数量（重量）
                print("\n开始计算本次使用数量（重量）...")
                
                # 先从 MaterialInformation_final 创建钢卷信息查找字典
                steel_info_dict = {}
                if not MaterialInformation_final.empty:
                    for idx, mat_row in MaterialInformation_final.iterrows():
                        identifier = mat_row.get('Identifier')
                        if identifier:
                            steel_info_dict[identifier] = {
                                'Width': mat_row.get('Width', 0),
                                'Thickness': mat_row.get('Thickness', 0),
                                'MaterialCode': mat_row.get('MaterialCode', '')
                            }
                    print(f"成功创建 {len(steel_info_dict)} 个钢卷信息字典")
                    if len(steel_info_dict) > 0:
                        sample_key = list(steel_info_dict.keys())[0]
                        print(f"  示例: {sample_key} -> {steel_info_dict[sample_key]}")
                
                # 304不锈钢密度: 7.93 g/cm³ = 0.00000793 kg/mm³
                density = 0.00000793
                
                for idx, row in AllFinalTable.iterrows():
                    # 获取钢卷标识符
                    identifier = None
                    for id_col in ['SteelRollIdentifier', 'Identifier', 'Steel_Identifier', 'identifier']:
                        if id_col in row and pd.notna(row[id_col]):
                            identifier = row[id_col]
                            break
                    
                    # 优先从 steel_info_dict 获取钢卷信息
                    steel_width = 0
                    steel_thickness = 0
                    
                    if identifier and identifier in steel_info_dict:
                        steel_info = steel_info_dict[identifier]
                        steel_width = steel_info.get('Width', 0)
                        steel_thickness = steel_info.get('Thickness', 0)
                    
                    # 如果还是获取不到，尝试从 AllFinalTable 本身获取
                    if steel_width == 0:
                        steel_width = row.get('SteelWidth') or row.get('Width') or 0
                    if steel_thickness == 0:
                        steel_thickness = row.get('Thickness') or 0
                    
                    # 获取使用长度
                    used_length = row.get('UsedLength') or row.get('used_length') or 0
                    
                    if steel_width > 0 and steel_thickness > 0 and used_length > 0:
                        # 计算使用面积 (mm²) = 使用长度 (mm) × 钢卷宽度 (mm)
                        used_area = used_length * steel_width
                        
                        # 计算使用体积 (mm³) = 使用面积 (mm²) × 厚度 (mm)
                        used_volume = used_area * steel_thickness
                        
                        # 计算使用重量 (kg) = 使用体积 (mm³) × 密度 (kg/mm³)
                        used_weight = used_volume * density
                        
                        AllFinalTable.at[idx, 'nesting_qty'] = round(used_weight, 2)
                        
                        if idx < 3:  # 调试输出前3条
                            print(f"  第{idx+1}行: 钢卷={identifier}, 宽度={steel_width}mm, 厚度={steel_thickness}mm, " +
                                  f"使用长度={used_length}mm, 计算重量={used_weight:.2f}kg")
                    else:
                        if idx < 3:
                            print(f"  第{idx+1}行: 缺少计算参数")
                            print(f"    钢卷标识={identifier}")
                            print(f"    宽度={steel_width}, 厚度={steel_thickness}, 使用长度={used_length}")
                            print(f"    在steel_info_dict中? {identifier in steel_info_dict if identifier else False}")
                            if identifier:
                                # 打印AllFinalTable中的相关列
                                print(f"    AllFinalTable行数据相关列:")
                                for col in ['SteelWidth', 'Width', 'Thickness', 'SteelRollIdentifier']:
                                    if col in row:
                                        print(f"      {col}={row[col]}")
                
                print(f"本次使用数量计算完成")
                
                print(f"字段补全完成，最终列名: {list(AllFinalTable.columns)}")
                print("\n补全后的前3条记录:")
                display_cols = ['material_code', 'material_desc', 'warehouse_name', 'bin_name', 
                              'lot_no', 'stock_qty', 'stock_qty_locked', 'nesting_qty']
                existing_cols = [col for col in display_cols if col in AllFinalTable.columns]
                if existing_cols:
                    print(AllFinalTable[existing_cols].head(3).to_string())
                print("")
            
            # 合并所有材料利用率数据
            AllMaterialUtilizationTable = pd.concat(
                [DirectUtilizationTable, SelfUtilizationTable, PairUtilizationTable, FailedUtilizationTable],
                ignore_index=True
            )
            
            # 生成坐标数据结果
            try:
                print("\n开始生成坐标数据...")
                print(f"AllFinalTable 列名: {list(AllFinalTable.columns)}")
                print(f"MaterialInformation_final 列名: {list(MaterialInformation_final.columns)}")
                
                visualization_result = MaterialNestingVisualization(AllFinalTable, MaterialInformation_final)
                
                print("\n" + "="*80)
                print("坐标数据结果 - visualization_result")
                print("="*80)
                print(f"钢卷数量: {len(visualization_result)}")
                
                for idx, steel_data in enumerate(visualization_result):
                    print(f"\n钢卷 {idx+1}:")
                    print(f"  标识: {steel_data.get('steelIdentifier')}")
                    print(f"  长度: {steel_data.get('steelLength')}mm")
                    print(f"  宽度: {steel_data.get('steelWidth')}mm")
                    print(f"  使用长度: {steel_data.get('usedLength')}mm")
                    print(f"  订单坐标数量: {len(steel_data.get('coordinates', []))}")
                    
                    # 显示前3个订单坐标
                    coordinates = steel_data.get('coordinates', [])
                    if len(coordinates) > 0:
                        print(f"  前3个订单坐标:")
                        for coord_idx, coord in enumerate(coordinates[:3]):
                            print(f"    订单{coord_idx+1}: docNo={coord.get('docNo')}, x={coord.get('x')}, y={coord.get('y')}, " + 
                                  f"长={coord.get('length')}, 宽={coord.get('width')}")
                
                print("="*80 + "\n")
                
            except Exception as e:
                print(f"\n生成坐标数据失败: {str(e)}")
                import traceback
                traceback.print_exc()
                visualization_result = []
                print("使用空的坐标结果\n")
            # 将套料结果添加到返回数据中
            result_data = {}
            result_data["nesting_result"] = {
                "final_table": AllFinalTable.to_dict('records'),
                "utilization_table": AllMaterialUtilizationTable.to_dict('records'),
                "visualization": visualization_result
            }
            
            message = "套料排版创建成功"
            
        except Exception as e:
            print("\n" + "="*80)
            print("套料排版处理失败，捕获异常:")
            print("="*80)
            print(f"异常类型: {type(e).__name__}")
            print(f"异常信息: {str(e)}")
            import traceback
            traceback.print_exc()
            print("="*80 + "\n")
            message = f"套料排版处理失败: {str(e)}, 已创建基础material对象"
            result_data = {}
        
        return UnifiedResponse(
            success=True,
            code=201,
            data=result_data,
            message=message
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
        nesting_layout_id = data.get("nestingLayoutId")
        
        if not nesting_layout_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少nestingLayoutId参数",
                error_code="MISSING_ID"
            )
        
        # 查找要删除的记录
        nesting_layout = session.get(NestingLayout, nesting_layout_id)
        
        if not nesting_layout:
            return UnifiedResponse(
                success=False,
                code=404,
                message=f"未找到ID为{nesting_layout_id}的套料排版记录",
                error_code="NOT_FOUND"
            )
        
        # 删除关联的子子表数据
        detail_ids_query = select(NestingLayoutD.nestingLayoutDId).where(
            NestingLayoutD.nestingLayoutId == nesting_layout_id
        )
        detail_ids = session.exec(detail_ids_query).all()
        
        for detail_id in detail_ids:
            # 删除子明细表数据
            sub_detail_delete = text(
                "DELETE FROM nesting_layout_sd WHERE nesting_layout_d_id = :detail_id"
            )
            session.exec(sub_detail_delete, {"detail_id": detail_id})
        
        # 删除子表数据
        detail_delete = text(
            "DELETE FROM nesting_layout_d WHERE nesting_layout_id = :nesting_layout_id"
        )
        session.exec(detail_delete, {"nesting_layout_id": nesting_layout_id})
        
        # 删除主表记录
        session.delete(nesting_layout)
        session.commit()
        
        return UnifiedResponse(
            success=True,
            code=200,
            message="套料排版删除成功"
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
    """处理列表查询操作 - 嵌套布局表关联查询"""
    try:
        # 获取查询参数
        page = request.page if request.page else 1
        limit = request.limit if request.limit else 50
        offset = (page - 1) * limit
        
        # 构建基础查询 - nesting_layout left join nesting_layout_d left join nesting_layout_sd
        base_sql = """
        SELECT 
            nesting_layout.*,
            nesting_layout_d.*,
            nesting_layout_sd.*
        FROM nesting_layout
        LEFT JOIN nesting_layout_d ON nesting_layout.nesting_layout_id = nesting_layout_d.nesting_layout_id
        LEFT JOIN nesting_layout_sd ON nesting_layout_d.nesting_layout_d_id = nesting_layout_sd.nesting_layout_d_id
        """
        
        # 构建WHERE条件
        where_conditions = []
        params = {}
        
        # 处理filters条件
        if request.filters:
            for field, value in request.filters.items():
                if value is not None:
                    param_name = f"param_{field}"
                    if isinstance(value, str) and value.startswith('%') and value.endswith('%'):
                        # LIKE查询
                        where_conditions.append(f"nesting_layout.{field} LIKE :{param_name}")
                    else:
                        # 精确匹配
                        where_conditions.append(f"nesting_layout.{field} = :{param_name}")
                    params[param_name] = value
        
        # 添加WHERE条件
        if where_conditions:
            base_sql += " WHERE " + " AND ".join(where_conditions)
        
        # 添加排序
        if request.sort:
            order_clauses = []
            for field, direction in request.sort.items():
                order_clauses.append(f"nesting_layout.{field} {direction.upper()}")
            
            if order_clauses:
                base_sql += " ORDER BY " + ", ".join(order_clauses)
        
        # 添加分页
        base_sql += f" LIMIT {limit} OFFSET {offset}"
        
        # 执行查询
        result = session.exec(text(base_sql), **params if params else {})
        results = result.all()
        
        # 获取总数
        count_sql = """
        SELECT COUNT(DISTINCT nesting_layout.nesting_layout_id) as total
        FROM nesting_layout
        LEFT JOIN nesting_layout_d ON nesting_layout.nesting_layout_id = nesting_layout_d.nesting_layout_id
        LEFT JOIN nesting_layout_sd ON nesting_layout_d.nesting_layout_d_id = nesting_layout_sd.nesting_layout_d_id
        """
        
        if where_conditions:
            count_sql += " WHERE " + " AND ".join(where_conditions)
        
        count_result = session.exec(text(count_sql), **params).first()
        total = count_result[0] if count_result else 0
        
        # 使用装配好的数据
        data = assemble_nesting_layout_data(results)
        
        return UnifiedResponse(
            success=True,
            code=200,
            message="查询套料排版列表成功",
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
            message=f"查询套料排版列表失败: {str(e)}",
            error_code="LIST_FAILED"
        )

def _handle_unified_read(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理读取操作 - 读取一个完整的NestingLayout对象，包含子对象及子子对象"""
    try:
        # 获取要读取的套料排版ID
        nesting_layout_id = None
        
        # 从请求数据中获取ID
        if request.data and isinstance(request.data, dict):
            nesting_layout_id = request.data.get("nestingLayoutId")
        
        
        
        if not nesting_layout_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少必要的参数: nestingLayoutId",
                error_code="MISSING_PARAMETER"
            )
        
        # 构建查询SQL - 获取完整的嵌套数据结构
        sql_query = """
        SELECT 
            nesting_layout.*,
            nesting_layout_d.*,
            nesting_layout_sd.*
        FROM nesting_layout
        LEFT JOIN nesting_layout_d ON nesting_layout.nesting_layout_id = nesting_layout_d.nesting_layout_id
        LEFT JOIN nesting_layout_sd ON nesting_layout_d.nesting_layout_d_id = nesting_layout_sd.nesting_layout_d_id
        WHERE nesting_layout.nesting_layout_id = '"""
        sql_query = sql_query + nesting_layout_id + "'"
        
        
        # 执行查询
        
        result = session.exec(text(sql_query))
        results = result.all()
       
        
        if not results:
            return UnifiedResponse(
                success=False,
                code=404,
                message=f"未找到ID为 {nesting_layout_id} 的套料排版记录",
                error_code="NOT_FOUND"
            )
        
        # 使用装配函数处理数据
        assembled_data = assemble_nesting_layout_data(results)
        
        # 由于是按ID查询，应该只有一条主记录
        if len(assembled_data) == 0:
            return UnifiedResponse(
                success=False,
                code=404,
                message=f"未找到ID为 {nesting_layout_id} 的套料排版记录",
                error_code="NOT_FOUND"
            )
        
        # 返回第一条记录（完整的嵌套数据）
        data = assembled_data[0]
        
        return UnifiedResponse(
            success=True,
            code=200,
            message="读取套料排版成功",
            data=data
        )
        
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"读取套料排版失败: {str(e)}",
            error_code="READ_FAILED"
        )

def _handle_unified_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理保存操作"""
    try:
        # TODO: 实现保存套料排版的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="保存套料排版成功"
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"保存套料排版失败: {str(e)}",
            error_code="SAVE_FAILED"
        )

def _handle_unified_batch_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理批量保存操作"""
    try:
        # TODO: 实现批量保存套料排版的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="批量保存套料排版成功"
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"批量保存套料排版失败: {str(e)}",
            error_code="BATCH_SAVE_FAILED"
        )

# 套料钢卷明细相关API
@router.post("/detail/unified", response_model=UnifiedResponse)
def unified_nesting_layout_detail_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的nesting-layout-detail操作API"""
    try:
        action = request.action.lower()
        
        if action == "create":
            return _handle_detail_create(request, session, current_user)
        elif action == "delete":
            return _handle_detail_delete(request, session, current_user)
        elif action == "list":
            return _handle_detail_list(request, session, current_user)
        elif action == "read":
            return _handle_detail_read(request, session, current_user)
        elif action == "save":
            return _handle_detail_save(request, session, current_user)
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

def _handle_detail_create(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理创建套料钢卷明细操作"""
    try:
        # TODO: 实现创建套料钢卷明细的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="创建套料钢卷明细成功",
            data={"id": "temp_detail_id"}
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"创建套料钢卷明细失败: {str(e)}",
            error_code="DETAIL_CREATE_FAILED"
        )

def _handle_detail_delete(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理删除套料钢卷明细操作"""
    try:
        # TODO: 实现删除套料钢卷明细的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="删除套料钢卷明细成功"
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"删除套料钢卷明细失败: {str(e)}",
            error_code="DETAIL_DELETE_FAILED"
        )

def _handle_detail_list(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理套料钢卷明细列表查询操作"""
    try:
        # TODO: 实现套料钢卷明细列表查询逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="查询套料钢卷明细列表成功",
            data=[],
            pagination={
                "total": 0,
                "page": 1,
                "limit": 50
            }
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"查询套料钢卷明细列表失败: {str(e)}",
            error_code="DETAIL_LIST_FAILED"
        )

def _handle_detail_read(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理读取套料钢卷明细操作"""
    try:
        # TODO: 实现读取套料钢卷明细详情的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="读取套料钢卷明细成功",
            data={}
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"读取套料钢卷明细失败: {str(e)}",
            error_code="DETAIL_READ_FAILED"
        )

def _handle_detail_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理保存套料钢卷明细操作"""
    try:
        # TODO: 实现保存套料钢卷明细的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="保存套料钢卷明细成功"
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"保存套料钢卷明细失败: {str(e)}",
            error_code="DETAIL_SAVE_FAILED"
        )

# 套料订单明细相关API
@router.post("/order-detail/unified", response_model=UnifiedResponse)
def unified_nesting_layout_order_detail_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的nesting-layout-order-detail操作API"""
    try:
        action = request.action.lower()
        
        if action == "create":
            return _handle_order_detail_create(request, session, current_user)
        elif action == "delete":
            return _handle_order_detail_delete(request, session, current_user)
        elif action == "list":
            return _handle_order_detail_list(request, session, current_user)
        elif action == "read":
            return _handle_order_detail_read(request, session, current_user)
        elif action == "save":
            return _handle_order_detail_save(request, session, current_user)
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

def _handle_order_detail_create(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理创建套料订单明细操作"""
    try:
        # TODO: 实现创建套料订单明细的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="创建套料订单明细成功",
            data={"id": "temp_order_detail_id"}
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"创建套料订单明细失败: {str(e)}",
            error_code="ORDER_DETAIL_CREATE_FAILED"
        )

def _handle_order_detail_delete(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理删除套料订单明细操作"""
    try:
        # TODO: 实现删除套料订单明细的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="删除套料订单明细成功"
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"删除套料订单明细失败: {str(e)}",
            error_code="ORDER_DETAIL_DELETE_FAILED"
        )

def _handle_order_detail_list(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理套料订单明细列表查询操作"""
    try:
        # TODO: 实现套料订单明细列表查询逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="查询套料订单明细列表成功",
            data=[],
            pagination={
                "total": 0,
                "page": 1,
                "limit": 50
            }
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"查询套料订单明细列表失败: {str(e)}",
            error_code="ORDER_DETAIL_LIST_FAILED"
        )

def _handle_order_detail_read(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理读取套料订单明细操作"""
    try:
        # TODO: 实现读取套料订单明细详情的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="读取套料订单明细成功",
            data={}
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"读取套料订单明细失败: {str(e)}",
            error_code="ORDER_DETAIL_READ_FAILED"
        )

def _handle_order_detail_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理保存套料订单明细操作"""
    try:
        # TODO: 实现保存套料订单明细的逻辑
        return UnifiedResponse(
            success=True,
            code=200,
            message="保存套料订单明细成功"
        )
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"保存套料订单明细失败: {str(e)}",
            error_code="ORDER_DETAIL_SAVE_FAILED"
        ) 