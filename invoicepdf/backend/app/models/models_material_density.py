from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Float, DateTime
from typing import Optional
from datetime import datetime

# 材质密度对照表模型
class MaterialDensity(SQLModel, table=True):
    __tablename__ = "material_density"
    
    # 物理主键
    materialDensityId: str = Field(max_length=200, sa_column=Column("material_density_id", String(200), primary_key=True))
    
    # 代码 - 业务主键
    materialCode: str = Field(max_length=10, sa_column=Column("material_code", String(10)))
    
    # 描述
    materialDesc: str = Field(max_length=20, sa_column=Column("material_desc", String(20)))
    
    # 密度
    density: float = Field(sa_column=Column("density", Float))
    
    # 密度单位
    densityUnitId: str = Field(max_length=200, sa_column=Column("density_unit_id", String(200)))
    
    # 备注
    remark: str = Field(max_length=200, sa_column=Column("remark", String(200)))
    
    # 创建信息
    creator: str = Field(max_length=20, sa_column=Column("creator", String(20)))
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    
    # 修改信息
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 审批相关字段
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))


# 创建请求模型
class MaterialDensityCreate(SQLModel):
    materialCode: str = Field(max_length=10, description="代码")
    materialDesc: str = Field(max_length=20, description="描述")
    density: float = Field(description="密度")
    densityUnitId: str = Field(max_length=200, description="密度单位")
    remark: str = Field(max_length=200, description="备注")
    creator: str = Field(max_length=20, description="创建人")
    approveStatus: str = Field(default="N", max_length=1, description="批准状态")


# 更新请求模型
class MaterialDensityUpdate(SQLModel):
    materialCode: Optional[str] = Field(default=None, max_length=10, description="代码")
    materialDesc: Optional[str] = Field(default=None, max_length=20, description="描述")
    density: Optional[float] = Field(default=None, description="密度")
    densityUnitId: Optional[str] = Field(default=None, max_length=200, description="密度单位")
    remark: Optional[str] = Field(default=None, max_length=200, description="备注")
    modifierLast: Optional[str] = Field(default=None, max_length=20, description="最后修改人")
    approveStatus: Optional[str] = Field(default=None, max_length=1, description="批准状态")
    approver: Optional[str] = Field(default=None, max_length=20, description="批准人")


# 响应模型
class MaterialDensityResponse(SQLModel):
    materialDensityId: str
    materialCode: str
    materialDesc: str
    density: float
    densityUnitId: str
    remark: str
    creator: str
    createDate: datetime
    modifierLast: Optional[str]
    modifyDateLast: Optional[datetime]
    approveStatus: str
    approver: Optional[str]
    approveDate: Optional[datetime]


# 查询模型
class MaterialDensityQuery(SQLModel):
    materialCode: Optional[str] = Field(default=None, description="代码")
    materialDesc: Optional[str] = Field(default=None, description="描述")
    densityUnitId: Optional[str] = Field(default=None, description="密度单位")
    approveStatus: Optional[str] = Field(default=None, description="批准状态")
    creator: Optional[str] = Field(default=None, description="创建人")
    page: Optional[int] = Field(default=1, description="页码")
    limit: Optional[int] = Field(default=20, description="每页数量") 