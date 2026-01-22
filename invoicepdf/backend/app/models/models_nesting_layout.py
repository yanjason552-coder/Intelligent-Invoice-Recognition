"""
NestingLayout 实体模型定义

设计说明：
1. NestingLayout 和 NestingLayoutD 之间存在一对多关系
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

# 套料订单明细表模型
class NestingLayoutSd(SQLModel, table=True):
    __tablename__ = "nesting_layout_sd"
    
    # 物理主键
    nestingLayoutSdId: str = Field(max_length=200, sa_column=Column("nesting_layout_sd_id", String(200), primary_key=True))
    
    # 父键 (关联 nesting_layout_d 表)
    nestingLayoutDId: str = Field(max_length=200, sa_column=Column("nesting_layout_d_id", String(200)))
    
    # 销售订单相关字段
    salesOrderDocDId: str = Field(max_length=200, sa_column=Column("sales_order_doc_d_id", String(200)))
    soItemSequenceNo: str = Field(max_length=4, sa_column=Column("so_item_sequence_no", String(4)))
    
    # 位置坐标
    fX: float = Field(default=0.0, sa_column=Column("f_x", Numeric))
    fY: float = Field(default=0.0, sa_column=Column("f_y", Numeric))
    tX: float = Field(default=0.0, sa_column=Column("t_x", Numeric))
    tY: float = Field(default=0.0, sa_column=Column("t_y", Numeric))
    
    # 套用数量
    nestingedQty: float = Field(default=0.0, sa_column=Column("nestinged_qty", Numeric)), 
    unitId: str = Field(max_length=200, sa_column=Column("unit_id", String(200)))
    nestingedSecondQty: float = Field(default=0.0, sa_column=Column("nestinged_second_qty", Numeric))
    unitIdSecond: str = Field(max_length=200, sa_column=Column("unit_id_second", String(200)))

    nestingedSoQty: float = Field(default=0.0, sa_column=Column("nestinged_so_qty", Numeric))
    unitIdSo: str = Field(max_length=200, sa_column=Column("unit_id_so", String(200)))
    
    # 备注
    remark: str = Field(max_length=200, sa_column=Column("remark", String(200)))
    
    # 创建人
    creator: str = Field(max_length=20, sa_column=Column("creator", String(20)))
    
    # 创建日期
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    
    # 最后修改人
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    
    # 最近修改日期
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 批准状态 (N:未批准 Y:已批准)
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    
    # 批准人
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    
    # 批准日期
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))

# 套料钢卷明细表模型
# 注意：不创建外键约束，保持关联关系的灵活性
class NestingLayoutD(SQLModel, table=True):
    __tablename__ = "nesting_layout_d"
    
    # 物理主键
    nestingLayoutDId: str = Field(max_length=200, sa_column=Column("nesting_layout_d_id", String(200), primary_key=True))
    
    # 父键 (关联 nesting_layout 表，但不创建外键约束)
    nestingLayoutId: str = Field(max_length=200, sa_column=Column("nesting_layout_id", String(200)))
    warehouseId: str = Field(max_length=200, sa_column=Column("warehouse_id", String(200)))
    binId: str = Field(max_length=200, sa_column=Column("bin_id", String(200)))
    # 物料相关字段
    materialId: str = Field(max_length=200, sa_column=Column("material_id", String(200)))
    materialCode: Optional[str] = Field(default="", max_length=40, sa_column=Column("material_code", String(40)))
    materialDescription: Optional[str] = Field(default="", max_length=200, sa_column=Column("material_description", String(200)))
    
    # 批号相关字段
    materialLotId: str = Field(max_length=200, sa_column=Column("material_lot_id", String(200)))
    lotNo: Optional[str] = Field(default="", max_length=20, sa_column=Column("lot_no", String(20)))
    lotDesc: Optional[str] = Field(default="", max_length=80, sa_column=Column("lot_desc", String(80)))
    
    # 序号
    sn: Optional[str] = Field(default="", max_length=10, sa_column=Column("sn", String(10)))
    
    # 位置坐标
    startPositionX: float = Field(default=0.0, sa_column=Column("start_position_x", Numeric))
    startPositionY: float = Field(default=0.0, sa_column=Column("start_position_y", Numeric))
    endPositionX: float = Field(default=0.0, sa_column=Column("end_position_x", Numeric))
    endPositionY: float = Field(default=0.0, sa_column=Column("end_position_y", Numeric))
    
    # 套用数量
    nestingedQty: float = Field(default=0.0, sa_column=Column("nestinged_qty", Numeric))
    unitId: str = Field(max_length=200, sa_column=Column("unit_id", String(200)))
    nestingedSecondQty: float = Field(default=0.0, sa_column=Column("nestinged_second_qty", Text))
    unitIdSecond: Optional[str] = Field(default="", max_length=200, sa_column=Column("unit_id_second", String(200)))
    
    # 备注
    remark: str = Field(max_length=200, sa_column=Column("remark", String(200)))
    
    # 创建人
    creator: str = Field(max_length=20, sa_column=Column("creator", String(20)))
    
    # 创建日期
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    
    # 最后修改人
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    
    # 最近修改日期
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 批准状态 (N:未批准 Y:已批准)
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    
    # 批准人
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    
    # 批准日期
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))

    # 库存基本数量
    stockQty: Optional[float] = Field(default=None, sa_column=Column("stock_qty", Numeric))

    # 套料前可用库存基本数量
    availableStockQty: Optional[float] = Field(default=None, sa_column=Column("available_stock_qty", Numeric))

    # 套料后可用库存基本数量
    remainingStockQty: Optional[float] = Field(default=None, sa_column=Column("remaining_stock_qty", Numeric))



    # 使用 property 装饰器创建子对象数组属性
    def __init__(self, **data):
        super().__init__(**data)
        self._nesting_layout_sd_list: List[NestingLayoutSd] = []
    
    @property
    def nestingLayoutSdList(self) -> List[NestingLayoutSd]:
        """获取套料排版的钢卷明细列表"""
        # 如果已有值，返回已设置的值，否则返回空列表
        return getattr(self, '_nesting_layout_sd_list', [])
    
    @nestingLayoutSdList.setter
    def nestingLayoutSdList(self, value: List[NestingLayoutSd]):
        """设置套料排版的钢卷明细列表"""
        self._nesting_layout_sd_list = value

# 套料排版表模型
# 注意：与 NestingLayoutD 的关联关系不依赖外键约束
class NestingLayout(SQLModel, table=True):
    __tablename__ = "nesting_layout"
    
    # 物理主键
    nestingLayoutId: str = Field(max_length=200, sa_column=Column("nesting_layout_id", String(200), primary_key=True))
    
    # 工厂
    plantId: str = Field(max_length=200, sa_column=Column("plant_id", String(200)))
    
    # 套料时间
    nestingDate: datetime = Field(sa_column=Column("nesting_date", DateTime))
    
    # 套料人员
    nestingEmployeeId: str = Field(max_length=200, sa_column=Column("nesting_employee_id", String(200)))
    
    # 套料说明
    nestingDesc: str = Field(max_length=30, sa_column=Column("nesting_desc", String(30)))
    
    # 备注
    remark: str = Field(max_length=200, sa_column=Column("remark", String(200)))
    
    # 创建人
    creator: str = Field(max_length=20, sa_column=Column("creator", String(20)))
    
    # 创建日期
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    
    # 最后修改人
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    
    # 最近修改日期
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 批准状态 (N:未批准 Y:已批准)
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    
    # 批准人
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    
    # 批准日期
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))
    
    # 成材率
    rateOfFinished: Optional[float] = Field(default=0.0, sa_column=Column("rate_of_finished", Numeric))
    # 余料率
    rateOfSurplus: Optional[float] = Field(default=0.0, sa_column=Column("rate_of_surplus", Numeric))

    # 使用 property 装饰器创建子对象数组属性
    def __init__(self, **data):
        super().__init__(**data)
        self._nesting_layout_d_list: List[NestingLayoutD] = []
    
    @property
    def nestingLayoutDList(self) -> List[NestingLayoutD]:
        """获取套料排版的钢卷明细列表"""
        # 如果已有值，返回已设置的值，否则返回空列表
        return getattr(self, '_nesting_layout_d_list', [])
    
    @nestingLayoutDList.setter
    def nestingLayoutDList(self, value: List[NestingLayoutD]):
        """设置套料排版的钢卷明细列表"""
        self._nesting_layout_d_list = value

# 查询示例函数
def get_nesting_layout_with_details(session, nesting_layout: NestingLayout):
    """获取套料排版及其所有钢卷明细"""
    statement = select(NestingLayout).where(NestingLayout.nestingLayoutId == nesting_layout.nestingLayoutId)
    nesting_layout_result = session.exec(statement).first()
    return nesting_layout_result

def get_nesting_layouts_by_plant(session, nesting_layout: NestingLayout):
    """根据工厂获取所有套料排版及其明细"""
    statement = select(NestingLayout).where(NestingLayout.plantId == nesting_layout.plantId)
    nesting_layouts = session.exec(statement).all()
    return nesting_layouts

def get_nesting_layout_details(session, nesting_layout: NestingLayout):
    """获取指定套料排版的所有钢卷明细"""
    statement = select(NestingLayoutD).where(NestingLayoutD.nestingLayoutId == nesting_layout.nestingLayoutId)
    details = session.exec(statement).all()
    return details 