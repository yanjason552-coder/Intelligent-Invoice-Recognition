"""
SalesOrderDocD 和 SalesOrderDocDFeature 实体模型定义
"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import Double, Field, SQLModel, Relationship
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey

class SalesOrderDocDFeature(SQLModel, table=True):
    """SalesOrderDocDFeature 实体模型 - 销售订单行项目属性"""
    __tablename__ = "sales_order_doc_d_feature"
    
    # 主键
    salesOrderDocDFeatureId: str = Field(
        sa_column=Column("sales_order_doc_d_feature_id", String(200), primary_key=True),
        description="物理主键"
    )
    
    # 外键关联
    salesOrderDocDId: str = Field(
        max_length=200,
        sa_column=Column("sales_order_doc_d_id", String(200), ForeignKey("sales_order_doc_d.sales_order_doc_d_id")),
        description="行项目ID"
    )
    
    # 位置
    position: int = Field(
        default=0,
        sa_column=Column("position", Integer),
        description="位置"
    )
    
    # 属性信息
    featureId: Optional[str] = Field(
        default=None,
        max_length=200,
        sa_column=Column("feature_id", String(200)),
        description="属性ID"
    )
    
    featureValue: Optional[str] = Field(
        default=None,
        max_length=20,
        sa_column=Column("feature_value", String(20)),
        description="属性值"
    )
    
    # 备注信息
    remark: Optional[str] = Field(
        default=None,
        max_length=200,
        sa_column=Column("remark", String(200)),
        description="备注"
    )
    
    # 创建信息
    creator: str = Field(
        max_length=20,
        sa_column=Column("creator", String(20)),
        description="创建人"
    )
    
    createDate: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("create_date", DateTime),
        description="创建日期"
    )
    
    # 修改信息
    modifierLast: Optional[str] = Field(
        default=None,
        max_length=20,
        sa_column=Column("modifier_last", String(20)),
        description="最后修改人"
    )
    
    modifyDateLast: Optional[datetime] = Field(
        default=None,
        sa_column=Column("modify_date_last", DateTime),
        description="最近修改日期"
    )
    
    # 审批信息
    approveStatus: str = Field(
        default="N",
        max_length=1,
        sa_column=Column("approve_status", String(1)),
        description="批准状态"
    )
    
    approver: Optional[str] = Field(
        default=None,
        max_length=20,
        sa_column=Column("approver", String(20)),
        description="批准人"
    )
    
    approveDate: Optional[datetime] = Field(
        default=None,
        sa_column=Column("approve_date", DateTime),
        description="批准日期"
    )

    # 使用 property 装饰器创建子对象数组属性
    @property
    def featureCode(self) -> str:
        """获取物料的属性列表"""
        # 如果还没有初始化，返回空列表
        if not hasattr(self, '_featureCode'):
            self._featureCode = ""
        return self._featureCode
    
    @featureCode.setter
    def featureCode(self, value: str):
        """设置物料的属性列表"""
        self._featureCode = value

    @property
    def featureDesc(self) -> str:
        """获取物料的属性列表"""
        # 如果还没有初始化，返回空列表
        if not hasattr(self, '_featureDesc'):
            self._featureDesc = ""
        return self._featureDesc
    
    @featureDesc.setter
    def featureDesc(self, value: str):
        """设置物料的属性列表"""
        self._featureDesc = value


class SalesOrderDocD(SQLModel, table=True):
    """SalesOrderDocD 实体模型 - 销售订单行项目"""
    __tablename__ = "sales_order_doc_d"
    
    # 主键
    salesOrderDocDId: str = Field(
        sa_column=Column("sales_order_doc_d_id", String(200), primary_key=True),
        description="行项目ID"
    )
    
    # 客户信息
    customerFullName: Optional[str] = Field(
        default=None,
        max_length=80,
        sa_column=Column("customer_full_name", String(80)),
        description="客户全称"
    )

    # 订单基本信息
    docId: str = Field(
        max_length=200,
        sa_column=Column("doc_id", String(200)),
        description="订单类型"
    )

    docNo: str = Field(
        max_length=20,
        sa_column=Column("doc_no", String(20)),
        description="订单单号"
    )

    sequence: str = Field(
        max_length=4,
        sa_column=Column("sequence", String(4)),
        description="订单行号"
    )

    docDate: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("doc_date", DateTime),
        description="订单日期"
    )

    # 物料信息
    materialId: Optional[str] = Field(
        default=None,
        max_length=200,
        sa_column=Column("material_id", String(200)),
        description="物料主键"
    )
        
    materialCode: Optional[str] = Field(
        default=None,
        max_length=40,
        sa_column=Column("material_code", String(40)),
        description="物料编码"
    )
    
    materialDescription: Optional[str] = Field(
        default=None,
        max_length=200,
        sa_column=Column("material_description", String(200)),
        description="物料描述"
    )
    
    # 数量和单位
    qty: Optional[float] = Field(
        default=None,
        sa_column=Column("qty", Double),
        description="订单数量"
    )
    
    unitId: Optional[str] = Field(
        default=None,
        max_length=200,
        sa_column=Column("unit_id", String(200)),
        description="订单单位"
    )
    
    # 交期和套料信息
    deliveryDate: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("delivery_date", DateTime),
        description="交期"
    )
    
    nestingedQty: Optional[float] = Field(
        default=None,
        sa_column=Column("nestinged_qty", Double),
        description="已套料数量"
    )
    
    # 备注信息
    remark: Optional[str] = Field(
        default=None,
        max_length=200,
        sa_column=Column("remark", String(200)),
        description="备注"
    )
    
    # 创建信息
    creator: str = Field(
        max_length=20,
        sa_column=Column("creator", String(20)),
        description="创建人"
    )
    
    createDate: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("create_date", DateTime),
        description="创建日期"
    )
    
    # 修改信息
    modifierLast: Optional[str] = Field(
        default=None,
        max_length=20,
        sa_column=Column("modifier_last", String(20)),
        description="最后修改人"
    )
    
    modifyDateLast: Optional[datetime] = Field(
        default=None,
        sa_column=Column("modify_date_last", DateTime),
        description="最后修改日期"
    )
    
    # 审批信息
    approveStatus: str = Field(
        default="N",
        max_length=1,
        sa_column=Column("approve_status", String(1)),
        description="审批状态 (N:未批准, Y:已批准, U:批准中, V:失败)"
    )
    
    approver: Optional[str] = Field(
        default=None,
        max_length=20,
        sa_column=Column("approver", String(20)),
        description="审批人"
    )
    
    approveDate: Optional[datetime] = Field(
        default=None,
        sa_column=Column("approve_date", DateTime),
        description="审批日期"
    )

    

    # 使用 property 装饰器创建子对象数组属性
    @property
    def salesOrderDocDFeatureList(self) -> List[SalesOrderDocDFeature]:
        """获取物料的属性列表"""
        # 如果还没有初始化，返回空列表
        if not hasattr(self, '_salesOrderDocDFeatureList'):
            self._salesOrderDocDFeatureList = []
        return self._salesOrderDocDFeatureList
    
    @salesOrderDocDFeatureList.setter
    def salesOrderDocDFeatureList(self, value: List[SalesOrderDocDFeature]):
        """设置物料的属性列表"""
        self._salesOrderDocDFeatureList = value



# 创建模型
class SalesOrderDocDCreate(SQLModel):
    """SalesOrderDocD 创建模型"""
    customerFullName: Optional[str] = Field(
        default=None,
        max_length=80,
        description="客户全称"
    )
    
    docId: str = Field(
        max_length=200,
        description="订单类型"
    )
    
    docNo: str = Field(
        max_length=20,
        description="订单单号"
    )
    
    sequence: str = Field(
        max_length=4,
        description="订单行号"
    )
    
    docDate: Optional[datetime] = Field(
        default=None,
        description="订单日期"
    )
    
    materialId: Optional[str] = Field(
        default=None,
        max_length=200,
        description="物料主键"
    )
    
    materialCode: Optional[str] = Field(
        default=None,
        max_length=40,
        description="物料编码"
    )
    
    materialDescription: Optional[str] = Field(
        default=None,
        max_length=200,
        description="物料描述"
    )
    
    qty: Optional[float] = Field(
        default=None,
        description="订单数量"
    )
    
    unitId: Optional[str] = Field(
        default=None,
        max_length=200,
        description="订单单位"
    )
    
    deliveryDate: Optional[datetime] = Field(
        default=None,
        description="交期"
    )
    
    nestingedQty: Optional[float] = Field(
        default=None,
        description="已套料数量"
    )
    
    remark: Optional[str] = Field(
        default=None,
        max_length=200,
        description="备注"
    )
    
    approveStatus: str = Field(
        default="N",
        max_length=1,
        description="审批状态"
    )
    
    approver: Optional[str] = Field(
        default=None,
        max_length=20,
        description="审批人"
    )
    
    approveDate: Optional[datetime] = Field(
        default=None,
        description="审批日期"
    )


class SalesOrderDocDUpdate(SQLModel):
    """SalesOrderDocD 更新模型"""
    customerFullName: Optional[str] = Field(
        default=None,
        max_length=80,
        description="客户全称"
    )
    
    docId: Optional[str] = Field(
        default=None,
        max_length=200,
        description="订单类型"
    )
    
    docNo: Optional[str] = Field(
        default=None,
        max_length=20,
        description="订单单号"
    )
    
    sequence: Optional[str] = Field(
        default=None,
        max_length=4,
        description="订单行号"
    )
    
    docDate: Optional[datetime] = Field(
        default=None,
        description="订单日期"
    )
    
    materialId: Optional[str] = Field(
        default=None,
        max_length=200,
        description="物料主键"
    )
    
    materialCode: Optional[str] = Field(
        default=None,
        max_length=40,
        description="物料编码"
    )
    
    materialDescription: Optional[str] = Field(
        default=None,
        max_length=200,
        description="物料描述"
    )
    
    qty: Optional[float] = Field(
        default=None,
        description="订单数量"
    )
    
    unitId: Optional[str] = Field(
        default=None,
        max_length=200,
        description="订单单位"
    )
    
    deliveryDate: Optional[datetime] = Field(
        default=None,
        description="交期"
    )
    
    nestingedQty: Optional[float] = Field(
        default=None,
        description="已套料数量"
    )
    
    remark: Optional[str] = Field(
        default=None,
        max_length=200,
        description="备注"
    )
    
    approveStatus: Optional[str] = Field(
        default=None,
        max_length=1,
        description="审批状态"
    )
    
    approver: Optional[str] = Field(
        default=None,
        max_length=20,
        description="审批人"
    )
    
    approveDate: Optional[datetime] = Field(
        default=None,
        description="审批日期"
    )


class SalesOrderDocDResponse(SQLModel):
    """SalesOrderDocD 响应模型"""
    salesOrderDocDId: str = Field(description="行项目ID")
    customerFullName: Optional[str] = Field(description="客户全称")
    docId: Optional[str] = Field(description="订单类型")
    docNo: Optional[str] = Field(description="订单单号")
    sequence: Optional[str] = Field(description="订单行号")
    docDate: Optional[datetime] = Field(description="订单日期")
    materialId: Optional[str] = Field(description="物料主键")
    materialCode: Optional[str] = Field(description="物料编码")
    materialDescription: Optional[str] = Field(description="物料描述")
    qty: Optional[float] = Field(description="订单数量")
    unitId: Optional[str] = Field(description="订单单位")
    deliveryDate: Optional[datetime] = Field(description="交期")
    nestingedQty: Optional[float] = Field(description="已套料数量")
    remark: Optional[str] = Field(description="备注")
    creator: Optional[str] = Field(description="创建人")
    createDate: Optional[datetime] = Field(description="创建日期")
    modifierLast: Optional[str] = Field(description="最后修改人")
    modifyDateLast: Optional[datetime] = Field(description="最后修改日期")
    approveStatus: Optional[str] = Field(description="审批状态")
    approver: Optional[str] = Field(description="审批人")
    approveDate: Optional[datetime] = Field(description="审批日期")
    salesOrderDocDFeatureList: List["SalesOrderDocDFeatureResponse"] = Field(default=[], description="属性列表")


# 属性创建模型
class SalesOrderDocDFeatureCreate(SQLModel):
    """SalesOrderDocDFeature 创建模型"""
    position: int = Field(
        default=0,
        description="位置"
    )
    
    featureId: Optional[str] = Field(
        default=None,
        max_length=200,
        description="属性ID"
    )
    
    featureValue: Optional[str] = Field(
        default=None,
        max_length=20,
        description="属性值"
    )
    
    remark: Optional[str] = Field(
        default=None,
        max_length=200,
        description="备注"
    )
    
    approveStatus: str = Field(
        default="N",
        max_length=1,
        description="批准状态"
    )
    
    approver: Optional[str] = Field(
        default=None,
        max_length=20,
        description="批准人"
    )
    
    approveDate: Optional[datetime] = Field(
        default=None,
        description="批准日期"
    )


class SalesOrderDocDFeatureUpdate(SQLModel):
    """SalesOrderDocDFeature 更新模型"""
    position: Optional[int] = Field(
        default=None,
        description="位置"
    )
    
    featureId: Optional[str] = Field(
        default=None,
        max_length=200,
        description="属性ID"
    )
    
    featureValue: Optional[str] = Field(
        default=None,
        max_length=20,
        description="属性值"
    )
    
    remark: Optional[str] = Field(
        default=None,
        max_length=200,
        description="备注"
    )
    
    approveStatus: Optional[str] = Field(
        default=None,
        max_length=1,
        description="批准状态"
    )
    
    approver: Optional[str] = Field(
        default=None,
        max_length=20,
        description="批准人"
    )
    
    approveDate: Optional[datetime] = Field(
        default=None,
        description="批准日期"
    )


class SalesOrderDocDFeatureResponse(SQLModel):
    """SalesOrderDocDFeature 响应模型"""
    salesOrderDocDFeatureId: str = Field(description="物理主键")
    salesOrderDocDId: str = Field(description="行项目ID")
    position: int = Field(description="位置")
    featureId: Optional[str] = Field(description="属性ID")
    featureValue: Optional[str] = Field(description="属性值")
    remark: Optional[str] = Field(description="备注")
    creator: str = Field(description="创建人")
    createDate: datetime = Field(description="创建日期")
    modifierLast: Optional[str] = Field(description="最后修改人")
    modifyDateLast: Optional[datetime] = Field(description="最近修改日期")
    approveStatus: str = Field(description="批准状态")
    approver: Optional[str] = Field(description="批准人")
    approveDate: Optional[datetime] = Field(description="批准日期")


# 重建模型关系（避免循环导入）
SQLModel.model_rebuild() 