"""
Feature 实体模型定义
"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey

class FeatureD(SQLModel, table=True):
    """Feature_d实体模型"""
    __tablename__ = "feature_d"
    
    # 主键
    featureDId: str = Field(
        sa_column=Column("feature_d_id", String(200), primary_key=True),
        description="明细ID"
    )
    
    # 外键关联
    featureId: str = Field(
        max_length=200,
        sa_column=Column("feature_id", String(200), ForeignKey("feature.feature_id")),
        description="属性ID"
    )
    
    # 明细信息
    featureValue: str = Field(
        max_length=20,
        sa_column=Column("feature_value", String(20)),
        description="属性值"
    )
    
    featureValueDesc: str = Field(
        max_length=20,
        sa_column=Column("feature_value_desc", String(20)),
        description="属性值描述"
    )
    
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

     # 审批信息
    createDate: datetime = Field(
        default=None,
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
        description="审批状态"
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
    
    

class Feature(SQLModel, table=True):
    """Feature 实体模型"""
    __tablename__ = "feature"
    
    # 主键
    featureId: str = Field(
        sa_column=Column("feature_id", String, primary_key=True),
        description="属性ID"
    )
    
    # 基础信息
    featureCode: str = Field(
        max_length=100,
        sa_column=Column("feature_code", String(100)),
        description="属性编码"
    )
    
    featureDesc: str = Field(
        max_length=500,
        sa_column=Column("feature_desc", String(500)),
        description="属性描述"
    )
    
    # 数据类型信息
    dataLen: int = Field(
        default=0,
        sa_column=Column("data_len", Integer),
        description="数据长度"
    )
    
    dataType: str = Field(
        max_length=50,
        sa_column=Column("data_type", String(50)),
        description="数据类型"
    )
    
    dataRanger: Optional[str] = Field(
        default=None,
        max_length=200,
        sa_column=Column("data_ranger", String(200)),
        description="数据范围"
    )
    
    dataMin: Optional[str] = Field(
        default=None,
        max_length=100,
        sa_column=Column("data_min", String(100)),
        description="最小值"
    )
    
    dataMax: Optional[str] = Field(
        default=None,
        max_length=100,
        sa_column=Column("data_max", String(100)),
        description="最大值"
    )
    
    # 备注信息
    remark: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="备注"
    )
    
    # 创建信息
    creator: str = Field(
        max_length=100,
        sa_column=Column("creator", String(100)),
        description="创建人"
    )
    
    createDate: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("create_date", DateTime),
        description="创建日期"
    )
    
    # 修改信息
    modifierLast: str = Field(
        max_length=100,
        sa_column=Column("modifier_last", String(100)),
        description="最后修改人"
    )
    
    modifyDateLast: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("modify_date_last", DateTime),
        description="最后修改日期"
    )
    
    # 审批信息
    approveStatus: str = Field(
        default="N",
        max_length=10,
        sa_column=Column("approve_status", String(10)),
        description="审批状态 (N:未批准, Y:已批准, U:批准中, V:失败)"
    )
    
    approver: Optional[str] = Field(
        default=None,
        max_length=100,
        sa_column=Column("approver", String(100)),
        description="审批人"
    )
    
    approveDate: Optional[datetime] = Field(
        default=None,
        sa_column=Column("approve_date", DateTime),
        description="审批日期"
    )

    # 使用 property 装饰器创建子对象数组属性
    def __init__(self, **data):
        super().__init__(**data)
        self.data_type_desc: str = ""
        self.data_range_desc: str = ""
        self.feature_d_list: List[FeatureD] = []
    
    @property
    def dataTypeDesc(self) -> str:
        return getattr(self, 'data_type_desc', "")
    
    @dataTypeDesc.setter
    def dataTypeDesc(self, value: str):
        self.data_type_desc = value
    
    @property
    def dataRangeDesc(self) -> str:
        return getattr(self, 'data_range_desc', "")
    
    @dataRangeDesc.setter
    def dataRangeDesc(self, value: str):
        self.data_range_desc = value


    @property
    def featureDList(self) -> List[FeatureD]:
        """获取套料排版的钢卷明细列表"""
        # 如果已有值，返回已设置的值，否则返回空列表
        return getattr(self, 'feature_d_list', [])
    
    @featureDList.setter
    def featureDList(self, value: List[FeatureD]):
        """设置套料排版的钢卷明细列表"""
        self.feature_d_list = value




class FeatureCreate(SQLModel):
    """Feature 创建模型"""
    featureCode: str = Field(
        max_length=100,
        description="属性编码"
    )
    
    featureDesc: str = Field(
        max_length=500,
        description="属性描述"
    )
    
    dataLen: int = Field(
        default=0,
        description="数据长度"
    )
    
    dataType: str = Field(
        max_length=50,
        description="数据类型"
    )
    
    dataRanger: Optional[str] = Field(
        default=None,
        max_length=200,
        description="数据范围"
    )
    
    dataMin: Optional[str] = Field(
        default=None,
        max_length=100,
        description="最小值"
    )
    
    dataMax: Optional[str] = Field(
        default=None,
        max_length=100,
        description="最大值"
    )
    
    remark: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="备注"
    )
    
    approveStatus: str = Field(
        default="N",
        max_length=10,
        description="审批状态"
    )
    
    approver: Optional[str] = Field(
        default=None,
        max_length=100,
        description="审批人"
    )
    
    approveDate: Optional[datetime] = Field(
        default=None,
        description="审批日期"
    )


class FeatureUpdate(SQLModel):
    """Feature 更新模型"""
    featureCode: Optional[str] = Field(
        default=None,
        max_length=100,
        description="属性编码"
    )
    
    featureDesc: Optional[str] = Field(
        default=None,
        max_length=500,
        description="属性描述"
    )
    
    dataLen: Optional[int] = Field(
        default=None,
        description="数据长度"
    )
    
    dataType: Optional[str] = Field(
        default=None,
        max_length=50,
        description="数据类型"
    )
    
    dataRanger: Optional[str] = Field(
        default=None,
        max_length=200,
        description="数据范围"
    )
    
    dataMin: Optional[str] = Field(
        default=None,
        max_length=100,
        description="最小值"
    )
    
    dataMax: Optional[str] = Field(
        default=None,
        max_length=100,
        description="最大值"
    )
    
    remark: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="备注"
    )
    
    approveStatus: Optional[str] = Field(
        default=None,
        max_length=10,
        description="审批状态"
    )
    
    approver: Optional[str] = Field(
        default=None,
        max_length=100,
        description="审批人"
    )
    
    approveDate: Optional[datetime] = Field(
        default=None,
        description="审批日期"
    )


class FeatureDCreate(SQLModel):
    """FeatureD 创建模型"""
    featureId: str = Field(
        max_length=200,
        description="属性ID"
    )
    
    featureValue: str = Field(
        max_length=20,
        description="属性值"
    )
    
    featureValueDesc: str = Field(
        max_length=20,
        description="属性值描述"
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

    createDate: datetime = Field(
        default=None,
        description="创建日期"
    )
    
    modifierLast: Optional[str] = Field(
        default=None,
        max_length=20,
        description="最后修改人"
    )
    
    modifyDateLast: Optional[datetime] = Field(
        default=None,
        description="最后修改日期"
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


class FeatureDUpdate(SQLModel):
    """FeatureD 更新模型"""
    featureValue: Optional[str] = Field(
        default=None,
        max_length=20,
        description="属性值"
    )
    
    featureValueDesc: Optional[str] = Field(
        default=None,
        max_length=20,
        description="属性值描述"
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
        description="最后修改日期"
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


class FeatureResponse(SQLModel):
    """Feature 响应模型"""
    featureId: str
    featureCode: str
    featureDesc: str
    dataLen: int
    dataType: str
    dataRanger: Optional[str] = None
    dataMin: Optional[str] = None
    dataMax: Optional[str] = None
    remark: Optional[str] = None
    creator: str
    createDate: datetime
    modifierLast: str
    modifyDateLast: datetime
    approveStatus: str
    approver: Optional[str] = None
    approveDate: Optional[datetime] = None


class FeatureDResponse(SQLModel):
    """FeatureD 响应模型"""
    featureDId: str
    featureId: str
    featureValue: str
    featureValueDesc: str
    remark: Optional[str] = None
    creator: str
    createDate: datetime
    modifierLast: Optional[str] = None
    modifyDateLast: Optional[datetime] = None
    approveStatus: str
    approver: Optional[str] = None
    approveDate: Optional[datetime] = None


# 重建模型以确保所有关系都正确设置
Feature.model_rebuild()
FeatureD.model_rebuild()
FeatureCreate.model_rebuild()
FeatureUpdate.model_rebuild()
FeatureDCreate.model_rebuild()
FeatureDUpdate.model_rebuild()
FeatureResponse.model_rebuild()
FeatureDResponse.model_rebuild() 