"""
ProductionOrder 实体模型定义

设计说明：
1. ProductionOrder、ProductionOrderD、ProductionOrderProduce 和 ProductionOrderRouting 之间存在一对多关系
2. 不创建外键约束，保持数据操作的灵活性
3. 不使用 SQLModel 的 Relationship，只作为普通属性
4. 这种设计的好处：
   - 避免外键约束的性能开销
   - 避免 SQLModel 关联关系的复杂性
   - 允许更灵活的数据操作（如批量导入、数据迁移）
   - 支持分布式架构中的数据关联
   - 便于数据清理和维护
   - 代码更简洁，易于理解和维护
"""

from typing import List, Optional, Annotated, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, select
from sqlalchemy import Column, String, DateTime, Text, Numeric
from sqlalchemy.sql import func

# 生产订单工序表模型
class ProductionOrderRouting(SQLModel, table=True):
    __tablename__ = "production_order_routing"
    
    # 父键
    productionOrderId: str = Field(max_length=200, sa_column=Column("production_order_id", String(200)))
    
    # 物理主键
    productionOrderRoutingId: str = Field(max_length=200, sa_column=Column("production_order_routing_id", String(200), primary_key=True))
    
    # 序号
    seq: str = Field(default="0000", max_length=4, sa_column=Column("seq", String(4)))
    
    # 工艺方法
    operationId: str = Field(max_length=200, sa_column=Column("operation_id", String(200)))
    
    # 工艺说明
    operationDesc: str = Field(max_length=200, sa_column=Column("operation_desc", String(200)))
    
    # 计划数量
    planQty: float = Field(default=0.0, sa_column=Column("plan_qty", Numeric))
    
    # 计划单位
    unitId: str = Field(default="", max_length=200, sa_column=Column("unit_id", String(200)))
    
    # 备注
    remark: Optional[str] = Field(default=None, max_length=200, sa_column=Column("remark", String(200)))
    
    # 创建人
    creator: str = Field(default="", max_length=20, sa_column=Column("creator", String(20)))
    
    # 创建日期
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    
    # 最后修改人
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    
    # 最近修改日期
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 批准状态 (N:未批准 Y:已批准 U:批准中 V:失败)
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    
    # 批准人
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    
    # 批准日期
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))

# 生产订单产出表模型
class ProductionOrderProduce(SQLModel, table=True):
    __tablename__ = "production_order_produce"
    
    # 父键
    productionOrderId: str = Field(max_length=200, sa_column=Column("production_order_id", String(200)))
    
    # 物理主键
    productionOrderProduceId: str = Field(max_length=200, sa_column=Column("production_order_produce_id", String(200), primary_key=True))
    
    # 序号
    seq: str = Field(max_length=4, sa_column=Column("seq", String(4)))
    
    # 产出类型 (0:主产品 1:联产品 2:副产品)
    outputType: str = Field(default="0", max_length=1, sa_column=Column("output_type", String(1)))
    
    # 物料主键
    materialId: str = Field(default="", max_length=200, sa_column=Column("material_id", String(200)))
    
    # 物料代码
    materialCode: str = Field(default="", max_length=40, sa_column=Column("material_code", String(40)))
    
    # 物料描述
    materialDescription: str = Field(default="", max_length=200, sa_column=Column("material_description", String(200)))
    
    # 收货仓库
    warehouseId: str = Field(max_length=200, sa_column=Column("warehouse_id", String(200)))
    
    # 计划业务数量
    planQty: float = Field(default=0.0, sa_column=Column("plan_qty", Numeric))
    
    # 合格业务数量
    qualifiedQty: float = Field(default=0.0, sa_column=Column("qualified_qty", Numeric))
    
    # 业务单位
    unitId: str = Field(max_length=200, sa_column=Column("unit_id", String(200)))
    
    # 库存单位合格数量
    qualifiedQtyStock: float = Field(default=0.0, sa_column=Column("qualified_qty_stock", Numeric))
    
    # 库存单位
    unitIdStock: str = Field(max_length=200, sa_column=Column("unit_id_stock", String(200)))
    
    # 第二库存单位合格数量
    qualifiedQtySecond: Optional[float] = Field(default=0.0, sa_column=Column("qualified_qty_second", Numeric))
    
    # 第二库存单位
    unitIdSecond: Optional[str] = Field(default=None, max_length=200, sa_column=Column("unit_id_second", String(200)))
    
    # 备注
    remark: Optional[str] = Field(default=None, max_length=200, sa_column=Column("remark", String(200)))
    
    # 创建人
    creator: str = Field(default="", max_length=20, sa_column=Column("creator", String(20)))
    
    # 创建日期
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    
    # 最后修改人
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    
    # 最近修改日期
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 批准状态 (N:未批准 Y:已批准 U:批准中 V:失败)
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    
    # 批准人
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    
    # 批准日期
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))

# 生产订单明细表模型
class ProductionOrderD(SQLModel, table=True):
    __tablename__ = "production_order_d"
    
    # 父键
    productionOrderId: str = Field(max_length=200, sa_column=Column("production_order_id", String(200)))
    
    # 物理主键
    productionOrderDId: str = Field(max_length=200, sa_column=Column("production_order_d_id", String(200), primary_key=True))
    
    # 序号
    seq: str = Field(max_length=4, sa_column=Column("seq", String(4)))
    
    # 物料主键
    materialId: str = Field(default="", max_length=200, sa_column=Column("material_id", String(200)))
    
    # 物料代码
    materialCode: str = Field(default="", max_length=40, sa_column=Column("material_code", String(40)))
    
    # 物料描述
    materialDescription: str = Field(default="", max_length=200, sa_column=Column("material_description", String(200)))
    
    # 发料仓库
    warehouseId: str = Field(max_length=200, sa_column=Column("warehouse_id", String(200)))
    
    # 业务单位需领数量
    issueQty: float = Field(default=0.0, sa_column=Column("issue_qty", Numeric))
    
    # 业务单位已领数量
    issuedQty: float = Field(default=0.0, sa_column=Column("issued_qty", Numeric))
    
    # 业务单位
    unitIdIssue: str = Field(max_length=200, sa_column=Column("unit_id_issue", String(200)))
    
    # 库存单位需领数量
    issueQtyStock: float = Field(default=0.0, sa_column=Column("issue_qty_stock", Numeric))
    
    # 库存单位已领数量
    issuedQtyStock: float = Field(default=0.0, sa_column=Column("issued_qty_stock", Numeric))
    
    # 库存单位
    unitIdStock: str = Field(max_length=200, sa_column=Column("unit_id_stock", String(200)))
    
    # 第二库存单位需领数量
    issueQtySecond: Optional[float] = Field(default=0.0, sa_column=Column("issue_qty_second", Numeric))
    
    # 第二库存单位已领数量
    issuedQtySecond: Optional[float] = Field(default=0.0, sa_column=Column("issued_qty_second", Numeric))
    
    # 第二库存单位
    unitIdSecond: Optional[str] = Field(default=None, max_length=200, sa_column=Column("unit_id_second", String(200)))
    
    # 备注
    remark: Optional[str] = Field(default=None, max_length=200, sa_column=Column("remark", String(200)))
    
    # 创建人
    creator: str = Field(default="", max_length=20, sa_column=Column("creator", String(20)))
    
    # 创建日期
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    
    # 最后修改人
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    
    # 最近修改日期
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 批准状态 (N:未批准 Y:已批准 U:批准中 V:失败)
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    
    # 批准人
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    
    # 批准日期
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))

# 生产订单表模型
class ProductionOrder(SQLModel, table=True):
    __tablename__ = "production_order"
    
    # 物理主键
    productionOrderId: str = Field(max_length=200, sa_column=Column("production_order_id", String(200), primary_key=True))
    
    # 凭证类型
    docId: str = Field(max_length=10, sa_column=Column("doc_id", String(10)))
    
    # 单号
    docNo: str = Field(max_length=12, sa_column=Column("doc_no", String(12)))
    
    # 凭证日期
    docDate: datetime = Field(sa_column=Column("doc_date", DateTime))
    
    # 物料主键
    materialId: str = Field(default="", max_length=200, sa_column=Column("material_id", String(200)))
    
    # 物料代码
    materialCode: str = Field(default="", max_length=40, sa_column=Column("material_code", String(40)))
    
    # 物料描述
    materialDescription: str = Field(default="", max_length=200, sa_column=Column("material_description", String(200)))
    
    # 工厂
    plantId: str = Field(max_length=200, sa_column=Column("plant_id", String(200)))
    
    # 收货仓库
    warehouseId: str = Field(max_length=200, sa_column=Column("warehouse_id", String(200)))
    
    # 批号主键
    materialLotId: Optional[str] = Field(default=None, max_length=200, sa_column=Column("material_lot_id", String(200)))
    
    # 批号
    lotNo: Optional[str] = Field(default=None, max_length=40, sa_column=Column("lot_no", String(40)))
    
    # 计划生产数量
    planQty: float = Field(default=0.0, sa_column=Column("plan_qty", Numeric))
    
    # 单位
    unitId: str = Field(max_length=200, sa_column=Column("unit_id", String(200)))
    
    # 基本开始日期
    basicDateStart: datetime = Field(sa_column=Column("basic_date_start", DateTime))
    
    # 基本完工日期
    basicDateEnd: datetime = Field(sa_column=Column("basic_date_end", DateTime))
    
    # 备注
    remark: Optional[str] = Field(default=None, max_length=200, sa_column=Column("remark", String(200)))
    
    # 创建人
    creator: str = Field(default="", max_length=20, sa_column=Column("creator", String(20)))
    
    # 创建日期
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    
    # 最后修改人
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    
    # 最近修改日期
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 批准状态 (N:未批准 Y:已批准 U:批准中 V:失败)
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    
    # 批准人
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    
    # 批准日期
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))
    
    # 使用 property 装饰器创建子对象数组属性
    def __init__(self, **data):
        super().__init__(**data)
        self._production_order_d_list: List[ProductionOrderD] = []
        self._production_order_production_list: List[ProductionOrderProduce] = []
        self._production_order_routing_list: List[ProductionOrderRouting] = []
    
    @property
    def productionOrderDList(self) -> List[ProductionOrderD]:
        """获取生产订单明细列表"""
        return getattr(self, '_production_order_d_list', [])
    
    @productionOrderDList.setter
    def productionOrderDList(self, value: List[ProductionOrderD]):
        """设置生产订单明细列表"""
        self._production_order_d_list = value
    
    @property
    def productionOrderProduceList(self) -> List[ProductionOrderProduce]:
        """获取生产订单产出列表"""
        return getattr(self, '_production_order_produce_list', [])
    
    @productionOrderProduceList.setter
    def productionOrderProduceList(self, value: List[ProductionOrderProduce]):
        """设置生产订单产出列表"""
        self._production_order_produce_list = value
    
    @property
    def productionOrderRoutingList(self) -> List[ProductionOrderRouting]:
        """获取生产订单工序列表"""
        return getattr(self, '_production_order_routing_list', [])
    
    @productionOrderRoutingList.setter
    def productionOrderRoutingList(self, value: List[ProductionOrderRouting]):
        """设置生产订单工序列表"""
        self._production_order_routing_list = value



