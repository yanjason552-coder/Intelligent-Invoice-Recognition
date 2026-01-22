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
    SalesOrderDocD, 
    SalesOrderDocDFeature
)

router = APIRouter(prefix="/salesOrderDocD", tags=["salesOrderDocD"])


@router.post("/unified", response_model=UnifiedResponse)
def unified_sales_order_operations(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> UnifiedResponse:
    """统一的销售订单项目操作API"""
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
        elif action == "save":
            return _handle_unified_save(request, session, current_user)
        elif action == "batch_save":
            return _handle_unified_batch_save(request, session, current_user)
        elif action == "custom_sql":
            return _handle_custom_sql_query(request, session, current_user)
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
    """处理统一创建操作"""
    if not request.data:
        return UnifiedResponse(
                success=False,
                code=400,
                message="缺少创建数据",
                error_code="MISSING_DATA"
            )
    
    try:
        # 检查业务主键是否已存在
        doc_id = request.data.get("doc_id")
        doc_no = request.data.get("doc_no")
        sequence = request.data.get("sequence")
        
        if not all([doc_id, doc_no, sequence]):
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少必要的业务主键字段",
                error_code="MISSING_REQUIRED_FIELDS"
            )
        
        existing_item = session.exec(
            select(SalesOrderDocD).where(
                SalesOrderDocD.doc_id == doc_id,
                SalesOrderDocD.doc_no == doc_no,
                SalesOrderDocD.sequence == sequence
            )
        ).first()
        
        if existing_item:
            return UnifiedResponse(
                success=False,
                code=400,
                message=f"订单项目已存在: {doc_id}-{doc_no}-{sequence}",
                error_code="DUPLICATE_ITEM"
            )
        
        # 创建新记录
        item_data = request.data.copy()
        item_data.update({
            "creator": current_user.full_name or current_user.email,
            "create_date": datetime.now(),
            "approve_status": "0"
        })
        
        item = SalesOrderDocD(**item_data)
        session.add(item)
        session.commit()
        session.refresh(item)
        
        return UnifiedResponse(
            success=True,
            code=201,
            data=item,
            message="创建成功"
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
    """处理统一读取操作"""
    item_id = request.data.get("id") if request.data else None
    if not item_id:
        return UnifiedResponse(
            success=False,
            code=400,
            message="缺少项目ID",
            error_code="MISSING_ID"
        )
    
    item = session.get(SalesOrderDocD, item_id)
    if not item:
        return UnifiedResponse(
            success=False,
            code=404,
            message="销售订单项目不存在",
            error_code="ITEM_NOT_FOUND"
        )
    
    return UnifiedResponse(
        success=True,
        data=item,
        message="查询成功"
    )



def _handle_unified_delete(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理统一删除操作"""
    item_id = request.data.get("id") if request.data else None
    if not item_id:
        return UnifiedResponse(
            success=False,
            code=400,
            message="缺少项目ID",
            error_code="MISSING_ID"
        )
    
    item = session.get(SalesOrderDocD, item_id)
    if not item:
        return UnifiedResponse(
            success=False,
            code=404,
            message="销售订单项目不存在",
            error_code="ITEM_NOT_FOUND"
        )
    
    # 检查审批状态
    if item.approve_status == "1":
        return UnifiedResponse(
            success=False,
            code=400,
            message="已审批的订单项目不能删除",
            error_code="APPROVED_ITEM_CANNOT_DELETE"
        )
    
    try:
        session.delete(item)
        session.commit()
        
        return UnifiedResponse(
            success=True,
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
    """处理统一列表查询操作 - 使用SQL文本执行"""
    try:
        # 构建基础SQL查询 - 包含salesOrderDocDFeature数据
        # 根据实际数据库表结构调整字段
        base_sql = """
        with tmp1 as (
            select sales_order_doc_d_feature.sales_order_doc_d_feature_id
              ,sales_order_doc_d_feature.sales_order_doc_d_id
              ,sales_order_doc_d_feature.position
              ,sales_order_doc_d_feature.feature_id
              ,regexp_split_to_table(sales_order_doc_d_feature.feature_value,'\|') as feature_value
            from sales_order_doc_d_feature where feature_id = '1'
        )
        ,tmp2 as (
            select tmp1.sales_order_doc_d_feature_id
              ,tmp1.sales_order_doc_d_id
              ,tmp1.position
              ,tmp1.feature_id
              ,string_agg(surface_technology.surface_desc,'|') as feature_value
            from tmp1
            left join surface_technology 
            on surface_technology.surface_code = tmp1.feature_value
            group by tmp1.sales_order_doc_d_feature_id
                     ,tmp1.sales_order_doc_d_id
                     ,tmp1.position
                     ,tmp1.feature_id
        )
        ,sales_order_doc_d_feature as(
            select sales_order_doc_d_feature.sales_order_doc_d_feature_id
              ,sales_order_doc_d_feature.sales_order_doc_d_id
              ,sales_order_doc_d_feature.position
              ,sales_order_doc_d_feature.feature_id
              ,sales_order_doc_d_feature.feature_value
            from sales_order_doc_d_feature
            where sales_order_doc_d_feature.feature_id <> '1'
            union
            select sales_order_doc_d_feature_id
              ,sales_order_doc_d_id
              ,position
              ,feature_id
              ,feature_value
            from tmp2
        )
        SELECT 
            -- 主表字段
            sales_order_doc_d.*,
            sales_order_doc_d_feature.sales_order_doc_d_feature_id,
            sales_order_doc_d_feature.position,sales_order_doc_d_feature.feature_id,
            sales_order_doc_d_feature.feature_value,
            -- Feature表数据
            feature.feature_code, feature.feature_desc
        FROM sales_order_doc_d 
        LEFT JOIN sales_order_doc_d_feature 
        ON sales_order_doc_d.sales_order_doc_d_id = sales_order_doc_d_feature.sales_order_doc_d_id
        LEFT JOIN feature  ON sales_order_doc_d_feature.feature_id = feature.feature_id
        """
        
        # 构建WHERE条件
        where_conditions = []
        params = {}
             
        # 组合WHERE条件
        if where_conditions:
            base_sql += " WHERE " + " AND ".join(where_conditions)
        
        # 获取总数 - 需要去重，因为JOIN会产生重复行
        count_sql = f"SELECT COUNT(DISTINCT sales_order_doc_d.sales_order_doc_d_id) as total FROM sales_order_doc_d "
        if where_conditions:
            count_sql += " WHERE " + " AND ".join(where_conditions)
        count_result = session.execute(text(count_sql), params)
        total = count_result.fetchone().total
        
        # 添加排序
        base_sql += " ORDER BY sales_order_doc_d.create_date asc,sales_order_doc_d.doc_no asc,sales_order_doc_d.sequence asc,sales_order_doc_d_feature.position asc"
        
        # 应用分页
        page = request.page or 1
        limit = request.limit or 20
        skip = (page - 1) * limit
        
        # 执行分页查询
        paginated_sql = f"{base_sql} LIMIT :limit OFFSET :skip"
        params['limit'] = limit
        params['skip'] = skip
        
        result = session.execute(text(paginated_sql), params)
        rows = result.fetchall()
        
        # 将查询结果组织成嵌套结构
        items_dict = {}  # 用于去重和分组
        
        for row in rows:
            sales_order_doc_d_id = row.sales_order_doc_d_id
            
            # 如果这个主记录还没有处理过，创建主记录
            if sales_order_doc_d_id not in items_dict:
                sales_order_doc_d = SalesOrderDocD(
                    salesOrderDocDId=row.sales_order_doc_d_id,
                    customerFullName=row.customer_full_name,
                    docNo=row.doc_no,
                    sequence=row.sequence,
                    docDate=row.doc_date,
                    deliveryDate=row.delivery_date,
                    materialCode=row.material_code,
                    materialDescription=row.material_description,
                    qty=row.qty,
                    nestingedQty=row.nestinged_qty,
                    unitId=row.unit_id,
                    remark=row.remark,
                    creator=row.creator,
                    createDate=row.create_date,
                    modifierLast=row.modifier_last,
                    modifyDateLast=row.modify_date_last,
                    approveStatus=row.approve_status,
                    approver=row.approver,
                    approveDate=row.approve_date
                )
                # 初始化属性列表
                sales_order_doc_d.salesOrderDocDFeatureList = []
                items_dict[row.sales_order_doc_d_id] = sales_order_doc_d
            
            # 如果有属性数据，添加到属性列表
            if row.sales_order_doc_d_feature_id:
                # SalesOrderDocDFeature已经在文件顶部导入
                sales_order_doc_d_feature = SalesOrderDocDFeature(
                    salesOrderDocDFeatureId=row.sales_order_doc_d_feature_id,
                    salesOrderDocDId=row.sales_order_doc_d_id,
                    position=row.position,
                    featureId=row.feature_id,
                    featureValue=row.feature_value
                )
                # 显式设置 property 属性
                sales_order_doc_d_feature.featureCode = row.feature_code
                sales_order_doc_d_feature.featureDesc = row.feature_desc
                
                items_dict[row.sales_order_doc_d_id].salesOrderDocDFeatureList.append(sales_order_doc_d_feature)
        
        # 转换为列表并手动构建字典结构，确保包含子对象
        items = []
        for item in items_dict.values():
            # 手动构建字典，确保包含子对象
            item_dict = {
                "salesOrderDocDId": item.salesOrderDocDId,
                "customerFullName": item.customerFullName,
                "docNo": item.docNo,
                "sequence": item.sequence,
                "docDate": item.docDate,
                "materialId": item.materialId,
                "materialCode": item.materialCode,
                "materialDescription": item.materialDescription,
                "deliveryDate": item.deliveryDate,
                "nestingedQty": item.nestingedQty,
                "qty": item.qty,
                "unitId": item.unitId,
                "remark": item.remark,
                "creator": item.creator,
                "createDate": item.createDate,
                "modifierLast": item.modifierLast,
                "modifyDateLast": item.modifyDateLast,
                "approveStatus": item.approveStatus,
                "approver": item.approver,
                "approveDate": item.approveDate,
                "salesOrderDocDFeatureList": [
                    {
                        "salesOrderDocDFeatureId": feature.salesOrderDocDFeatureId,
                        "salesOrderDocDId": feature.salesOrderDocDId,
                        "position": feature.position,
                        "featureId": feature.featureId,
                        "featureCode": feature.featureCode,
                        "featureDesc": feature.featureDesc,
                        "featureValue": feature.featureValue,
                        "remark": feature.remark,
                        "creator": feature.creator,
                        "createDate": feature.createDate,
                        "modifierLast": feature.modifierLast,
                        "modifyDateLast": feature.modifyDateLast,
                        "approveStatus": feature.approveStatus,
                        "approver": feature.approver,
                        "approveDate": feature.approveDate
                    }
                    for feature in item.salesOrderDocDFeatureList
                ]
            }
            items.append(item_dict)
        
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


def _handle_unified_batch_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理批量保存操作 - 支持主表和明细表的批量插入"""
    try:
        data = request.data
        print(f"DEBUG: 接收到的批量保存数据: {data}")
        
        if not data or not isinstance(data, list):
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少批量保存数据或数据格式错误",
                error_code="MISSING_DATA"
            )
        
        # 统计变量
        main_records_count = 0
        feature_records_count = 0
        
        # 开始事务
        try:
            for sales_order_doc_d_data in data:
                print(f"DEBUG: 处理主表记录: {sales_order_doc_d_data}")
                
                # 提取主表数据
                main_data = {
                    'salesOrderDocDId': sales_order_doc_d_data.get('salesOrderDocDId'),
                    'customerFullName': sales_order_doc_d_data.get('customerFullName', ''),
                    'docId': sales_order_doc_d_data.get('docId'),
                    'docNo': sales_order_doc_d_data.get('docNo', ''),
                    'sequence': sales_order_doc_d_data.get('sequence'),
                    'docDate': sales_order_doc_d_data.get('docDate'),
                    'materialId': sales_order_doc_d_data.get('materialId'),
                    'materialCode': sales_order_doc_d_data.get('materialCode', ''),
                    'materialDescription': sales_order_doc_d_data.get('materialDescription', ''),
                    'qty': sales_order_doc_d_data.get('qty'),
                    'unitId': sales_order_doc_d_data.get('unitId', ''),
                    'deliveryDate': sales_order_doc_d_data.get('deliveryDate'),
                    'nestingedQty': sales_order_doc_d_data.get('nestingedQty'),
                    'creator': sales_order_doc_d_data.get('creator', ''),
                    'createDate': sales_order_doc_d_data.get('createDate'),
                    'modifierLast': sales_order_doc_d_data.get('modifierLast', ''),
                    'modifyDateLast': sales_order_doc_d_data.get('modifyDateLast'),
                    'approveStatus': sales_order_doc_d_data.get('approveStatus', ''),
                    'approver': sales_order_doc_d_data.get('approver', ''),
                    'approveDate': sales_order_doc_d_data.get('approveDate'),
                    'remark': sales_order_doc_d_data.get('remark', '')
                }
                
                # 创建主表记录
                main_record = SalesOrderDocD(**main_data)
                session.add(main_record)
                session.flush()  # 获取生成的ID
                
                main_records_count += 1
                print(f"DEBUG: 主表记录已添加，ID: {main_record.salesOrderDocDId}")
                
                # 处理子表数据
                sales_order_doc_d_feature_list = sales_order_doc_d_data.get('salesOrderDocDFeatureList', [])
                
                for feature_data in sales_order_doc_d_feature_list:
                    print(f"DEBUG: 处理属性记录: {feature_data}")
                    
                    # 提取属性表数据
                    feature_record_data = {
                        'salesOrderDocDFeatureId': feature_data.get('salesOrderDocDFeatureId'),
                        'salesOrderDocDId': main_record.salesOrderDocDId,  # 使用主表生成的ID
                        'position': feature_data.get('position', ''),
                        'featureId': feature_data.get('featureId'),
                        'featureValue': feature_data.get('featureValue', ''),
                        'remark': feature_data.get('remark', ''),
                        'creator': feature_data.get('creator', ''),
                        'createDate': feature_data.get('createDate'),
                        'modifierLast': feature_data.get('modifierLast', ''),
                        'modifyDateLast': feature_data.get('modifyDateLast'),
                        'approveStatus': feature_data.get('approveStatus', ''),
                        'approver': feature_data.get('approver', ''),
                        'approveDate': feature_data.get('approveDate')
                    }
                    
                    # 创建属性表记录
                    feature_record = SalesOrderDocDFeature(**feature_record_data)
                    session.add(feature_record)
                    
                    feature_records_count += 1
                    print(f"DEBUG: 属性记录已添加，ID: {feature_record.salesOrderDocDFeatureId}")
            
                # 提交事务
                session.commit()
            
            print(f"DEBUG: 批量保存完成，主表记录: {main_records_count}，属性记录: {feature_records_count}")
            
            return UnifiedResponse(
                success=True,
                data={
                    'main_records_count': main_records_count,
                    'feature_records_count': feature_records_count,
                    'total_records': main_records_count + feature_records_count
                },
                message=f"批量保存成功，共保存 {main_records_count} 条主表记录和 {feature_records_count} 条属性记录"
            )
            
        except Exception as e:
            # 回滚事务
            session.rollback()
            print(f"DEBUG: 批量保存失败，回滚事务: {str(e)}")
            raise e
            
    except Exception as e:
        print(f"DEBUG: 批量保存操作失败: {str(e)}")
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"批量保存失败: {str(e)}",
            error_code="BATCH_SAVE_FAILED"
        )
def _handle_custom_sql_query(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """使用自定义SQL查询销售订单项目"""
    try:
        # 使用 ORM 查询替代原始 SQL 来避免游标问题
        query = select(SalesOrderDocD)
        
        # 应用搜索条件
        if request.search:
            search_term = f"%{request.search}%"
            query = query.where(
                or_(
                    SalesOrderDocD.doc_no.ilike(search_term),
                    SalesOrderDocD.customer_full_name.ilike(search_term),
                    SalesOrderDocD.material_code.ilike(search_term)
                )
            )
        
        # 应用过滤条件
        if request.filters:
            for field, value in request.filters.items():
                if hasattr(SalesOrderDocD, field):
                    query = query.where(getattr(SalesOrderDocD, field) == value)
        
        # 添加排序
        query = query.order_by(SalesOrderDocD.create_date.desc())
        
        # 执行查询
        items = session.exec(query).all()
        
        # 转换为字典格式并添加 feature_count
        items_dict = []
        for item in items:
            # 暂时设置为0，避免复杂的关联查询
            feature_count = 0
            
            item_dict = {
                'sales_order_doc_d_id': item.sales_order_doc_d_id,
                'customer_full_name': item.customer_full_name,
                'doc_id': item.doc_id,
                'doc_no': item.doc_no,
                'sequence': item.sequence,
                'doc_date': item.doc_date,
                'material_code': item.material_code,
                'material_description': item.material_description,
                'qty': item.qty,
                'creator': item.creator,
                'create_date': item.create_date,
                'approve_status': item.approve_status,
                'feature_count': feature_count
            }
            items_dict.append(item_dict)
        
        return UnifiedResponse(
            success=True,
            data=items_dict,
            message=f"查询成功，共{len(items_dict)}条记录"
        )
        
    except Exception as e:
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"查询失败: {str(e)}",
            error_code="QUERY_FAILED"
        ) 


def _handle_unified_save(request: UnifiedRequest, session: SessionDep, current_user: CurrentUser) -> UnifiedResponse:
    """处理统一保存操作 - 支持主表和明细表的保存"""
    try:
        data = request.data
        print(f"DEBUG: 接收到的保存数据: {data}")
        
        if not data:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少保存数据",
                error_code="MISSING_DATA"
            )
        
        # SalesOrderDocD和SalesOrderDocDFeature已经在文件顶部导入
        
        # 处理主表数据
        sales_order_doc_d_id = data.get("salesOrderDocDId", "")
        sales_order_doc_d_feature_list = data.get("salesOrderDocDFeatureList", [])
        
        if not sales_order_doc_d_id:
            return UnifiedResponse(
                success=False,
                code=400,
                message="缺少销售订单行项目ID",
                error_code="MISSING_ID"
            )
        
        # 检查是否为新建对象（以'new-'开头）
        if sales_order_doc_d_id.startswith('new-'):
            # 生成新的ID
            new_sales_order_doc_d_id = str(uuid.uuid4())
            
            # 创建新记录
            sales_order_doc_d = SalesOrderDocD(
                salesOrderDocDId=new_sales_order_doc_d_id,
                customerFullName=data.get("customerFullName"),
                docNo=data.get("docNo"),
                docDate=data.get("docDate"),
                deliveryDate=data.get("deliveryDate"),
                materialCode=data.get("materialCode"),
                materialDescription=data.get("materialDescription"),
                materialSpecification=data.get("materialSpecification"),
                qty=data.get("qty"),
                unitId=data.get("unitId"),
                remark=data.get("remark"),
                approveStatus=data.get("approveStatus", "N"),
                creator=current_user.email,
                createDate=datetime.now()
            )
            session.add(sales_order_doc_d)
            
            # 保存明细数据
            for detail_data in sales_order_doc_d_feature_list:
                detail_id = detail_data.get("salesOrderDocDFeatureId", "")
                
                if detail_id.startswith('new-'):
                    # 新建明细记录，生成新ID
                    new_detail_id = str(uuid.uuid4())
                else:
                    # 现有明细记录，保持原ID
                    new_detail_id = detail_id
                
                sales_order_doc_d_feature = SalesOrderDocDFeature(
                    salesOrderDocDFeatureId=new_detail_id,
                    salesOrderDocDId=new_sales_order_doc_d_id,
                    position=detail_data.get("position", 0),
                    featureId=detail_data.get("featureId"),
                    featureValue=detail_data.get("featureValue"),
                    remark=detail_data.get("remark"),  # 新增的remark字段
                    creator=current_user.email,
                    createDate=datetime.now(),
                    approveStatus=detail_data.get("approveStatus", "N")
                )
                session.add(sales_order_doc_d_feature)
        else:
            # 更新现有记录
            existing_sales_order_doc_d = session.get(SalesOrderDocD, sales_order_doc_d_id)
            if not existing_sales_order_doc_d:
                return UnifiedResponse(
                    success=False,
                    code=404,
                    message=f"销售订单行项目 {sales_order_doc_d_id} 不存在",
                    error_code="NOT_FOUND"
                )
            
            # 更新主表字段
            existing_sales_order_doc_d.customerFullName = data.get("customerFullName")
            existing_sales_order_doc_d.docNo = data.get("docNo")
            existing_sales_order_doc_d.docDate = data.get("docDate")
            existing_sales_order_doc_d.deliveryDate = data.get("deliveryDate")
            existing_sales_order_doc_d.materialCode = data.get("materialCode")
            existing_sales_order_doc_d.materialDescription = data.get("materialDescription")
            existing_sales_order_doc_d.materialSpecification = data.get("materialSpecification")
            existing_sales_order_doc_d.qty = data.get("qty")
            existing_sales_order_doc_d.unitId = data.get("unitId")
            existing_sales_order_doc_d.remark = data.get("remark")
            existing_sales_order_doc_d.approveStatus = data.get("approveStatus", "N")
            existing_sales_order_doc_d.modifierLast = current_user.email
            existing_sales_order_doc_d.modifyDateLast = datetime.now()
            
            # 删除现有的明细数据
            delete_detail_sql = """
            DELETE FROM sales_order_doc_d_feature 
            WHERE sales_order_doc_d_id = :sales_order_doc_d_id
            """
            session.execute(text(delete_detail_sql), {"sales_order_doc_d_id": sales_order_doc_d_id})
            
            # 保存新的明细数据
            for detail_data in sales_order_doc_d_feature_list:
                detail_id = detail_data.get("salesOrderDocDFeatureId", "")
                
                if detail_id.startswith('new-'):
                    # 新建明细记录，生成新ID
                    new_detail_id = str(uuid.uuid4())
                else:
                    # 现有明细记录，保持原ID
                    new_detail_id = detail_id
                
                sales_order_doc_d_feature = SalesOrderDocDFeature(
                    salesOrderDocDFeatureId=new_detail_id,
                    salesOrderDocDId=sales_order_doc_d_id,
                    position=detail_data.get("position", 0),
                    featureId=detail_data.get("featureId"),
                    featureValue=detail_data.get("featureValue"),
                    remark=detail_data.get("remark"),  # 新增的remark字段
                    creator=current_user.email,
                    createDate=datetime.now(),
                    modifierLast=current_user.email,
                    modifyDateLast=datetime.now(),
                    approveStatus=detail_data.get("approveStatus", "N")
                )
                session.add(sales_order_doc_d_feature)
        
        session.commit()
        
        # 保存完成后，返回完整的对象
        if sales_order_doc_d_id.startswith('new-'):
            final_id = sales_order_doc_d.salesOrderDocDId
        else:
            final_id = sales_order_doc_d_id
        
        # 获取保存后的完整数据
        saved_item = session.get(SalesOrderDocD, final_id)
        if saved_item:
            # 加载关联的明细数据
            from sqlalchemy.orm import selectinload
            saved_item = session.exec(
                select(SalesOrderDocD)
                .options(selectinload(SalesOrderDocD.salesOrderDocDFeatureList))
                .where(SalesOrderDocD.salesOrderDocDId == final_id)
            ).first()
        
        return UnifiedResponse(
            success=True,
            code=200,
            data=saved_item,
            message=f"销售订单行项目保存成功，包含 {len(saved_item.salesOrderDocDFeatureList) if saved_item and saved_item.salesOrderDocDFeatureList else 0} 条明细数据"
        )
        
    except Exception as e:
        session.rollback()
        return UnifiedResponse(
            success=False,
            code=500,
            message=f"保存失败: {str(e)}",
            error_code="SAVE_FAILED"
        ) 