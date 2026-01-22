"""
MaterialClass 实体模型定义
"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey


class MaterialClassD(SQLModel, table=True):
    """MaterialClassD 实体模型"""
    __tablename__ = "material_class_d"
    
    # 主键
    materialClassDId: str = Field(
        sa_column=Column("material_class_d_id", String(200), primary_key=True),
        description="物理主键，GUID"
    )
    
    # 外键关联
    materialClassId: str = Field(
        max_length=200,
        sa_column=Column("material_class_id", String(200), ForeignKey("material_class.material_class_id")),
        description="父键，关联到物料类别主表"
    )
    
    # 属性信息
    featureId: str = Field(
        max_length=200,
        sa_column=Column("feature_id", String(200)),
        description="属性ID"
    )

    # 属性信息
    featureCode: str = Field(
        max_length=10,
        sa_column=Column("feature_code", String(10)),
        description="属性代码"
    )

    # 属性描述（非数据库字段，用于显示）
    featureDesc: Optional[str] = Field(
        default=None,
        max_length=20,
        description="属性描述（非数据库字段）"
    )
    
    # 属性值
    featureValue: str = Field(
        max_length=20,
        sa_column=Column("feature_value", String(20)),
        description="属性值"
    )
    
    # 位置/排序
    position: int = Field(
        sa_column=Column("position", Integer),
        description="位置/排序"
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
        description="批准状态 (N:未批准, Y:已批准, U:批准中, V:失败)"
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
    
   


class MaterialClass(SQLModel, table=True):
    """MaterialClass 实体模型"""
    __tablename__ = "material_class"
    
    # 主键
    materialClassId: str = Field(
        sa_column=Column("material_class_id", String(200), primary_key=True),
        description="物理主键"
    )
    
    # 上阶主键
    materialClassPId: str = Field(
        max_length=200,
        sa_column=Column("material_class_p_id", String(200)),
        description="上阶主键"
    )
    
    # 上级类别编码和描述（非数据库字段，用于显示）
    materialClassPCode: Optional[str] = Field(
        default=None,
        max_length=200,
        description="上级类别编码（非数据库字段）"
    )
    
    materialClassPDesc: Optional[str] = Field(
        default=None,
        max_length=200,
        description="上级类别描述（非数据库字段）"
    )
    
    # 基础信息
    classCode: str = Field(
        max_length=20,
        sa_column=Column("class_code", String(20)),
        description="类别编号"
    )
    
    classDesc: str = Field(
        max_length=20,
        sa_column=Column("class_desc", String(20)),
        description="类别描述"
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
        description="批准状态 (N:未批准 Y:已批准 U:批准中 V:失败)"
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
    def __init__(self, **data):
        super().__init__(**data)
        self._material_class_d_list: List[MaterialClassD] = []
        self._material_class_p_code: str = ''
        self._material_class_p_desc: str = ''
    
    @property
    def materialClassDList(self) -> List[MaterialClassD]:
        # 如果已有值，返回已设置的值，否则返回空列表
        return getattr(self, '_material_class_d_list', [])
    
    @materialClassDList.setter
    def materialClassDList(self, value: List[MaterialClassD]):
        self._material_class_d_list = value
    
   

class MaterialClassCreate(SQLModel):
    """MaterialClass 创建模型"""
    materialClassPId: str = Field(
        max_length=200,
        description="上阶主键"
    )
    
    classCode: str = Field(
        max_length=20,
        description="类别编号"
    )
    
    classDesc: str = Field(
        max_length=20,
        description="类别描述"
    )
    
    remark: Optional[str] = Field(
        default=None,
        max_length=200,
        description="备注"
    )
    
    creator: str = Field(
        max_length=20,
        description="创建人"
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


class MaterialClassUpdate(SQLModel):
    """MaterialClass 更新模型"""
    materialClassPId: Optional[str] = Field(
        default=None,
        max_length=200,
        description="上阶主键"
    )
    
    classCode: Optional[str] = Field(
        default=None,
        max_length=20,
        description="类别编号"
    )
    
    classDesc: Optional[str] = Field(
        default=None,
        max_length=20,
        description="类别描述"
    )
    
    remark: Optional[str] = Field(
        default=None,
        max_length=200,
        description="备注"
    )
    
    modifierLast: Optional[str] = Field(
        default=None,
        max_length=20,
        description="最后修改人"
    )
    
    modifyDateLast: Optional[datetime] = Field(
        default=None,
        description="最近修改日期"
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


class MaterialClassResponse(SQLModel):
    """MaterialClass 响应模型"""
    materialClassId: str = Field(description="物理主键")
    materialClassPId: str = Field(description="上阶主键")
    classCode: str = Field(description="类别编号")
    classDesc: str = Field(description="类别描述")
    remark: Optional[str] = Field(description="备注")
    creator: str = Field(description="创建人")
    createDate: datetime = Field(description="创建日期")
    modifierLast: Optional[str] = Field(description="最后修改人")
    modifyDateLast: Optional[datetime] = Field(description="最近修改日期")
    approveStatus: str = Field(description="批准状态")
    approver: Optional[str] = Field(description="批准人")
    approveDate: Optional[datetime] = Field(description="批准日期")


class MaterialClassDCreate(SQLModel):
    """MaterialClassD 创建模型"""
    materialClassId: str = Field(
        max_length=200,
        description="父键，关联到物料类别主表"
    )
    
    featureId: str = Field(
        max_length=10,
        description="属性ID"
    )
    
    featureValue: str = Field(
        max_length=20,
        description="属性值"
    )
    
    position: int = Field(
        description="位置/排序"
    )
    
    remark: Optional[str] = Field(
        default=None,
        max_length=200,
        description="备注"
    )
    
    creator: str = Field(
        max_length=20,
        description="创建人"
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


class MaterialClassDUpdate(SQLModel):
    """MaterialClassD 更新模型"""
    featureId: Optional[str] = Field(
        default=None,
        max_length=10,
        description="属性ID"
    )
    
    featureValue: Optional[str] = Field(
        default=None,
        max_length=20,
        description="属性值"
    )
    
    position: Optional[int] = Field(
        default=None,
        description="位置/排序"
    )
    
    remark: Optional[str] = Field(
        default=None,
        max_length=200,
        description="备注"
    )
    
    modifierLast: Optional[str] = Field(
        default=None,
        max_length=20,
        description="最后修改人"
    )
    
    modifyDateLast: Optional[datetime] = Field(
        default=None,
        description="最近修改日期"
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


class MaterialClassDResponse(SQLModel):
    """MaterialClassD 响应模型"""
    materialClassDId: str = Field(description="物理主键，GUID")
    materialClassId: str = Field(description="父键，关联到物料类别主表")
    featureId: str = Field(description="属性ID")
    featureValue: str = Field(description="属性值")
    position: int = Field(description="位置/排序")
    remark: Optional[str] = Field(description="备注")
    creator: str = Field(description="创建人")
    createDate: datetime = Field(description="创建日期")
    modifierLast: Optional[str] = Field(description="最后修改人")
    modifyDateLast: Optional[datetime] = Field(description="最近修改日期")
    approveStatus: str = Field(description="批准状态")
    approver: Optional[str] = Field(description="批准人")
    approveDate: Optional[datetime] = Field(description="批准日期")


# 重建模型以确保所有关系都正确设置
MaterialClass.model_rebuild()
MaterialClassD.model_rebuild()
MaterialClassCreate.model_rebuild()
MaterialClassUpdate.model_rebuild()
MaterialClassResponse.model_rebuild()
MaterialClassDCreate.model_rebuild()
MaterialClassDUpdate.model_rebuild()
MaterialClassDResponse.model_rebuild() 