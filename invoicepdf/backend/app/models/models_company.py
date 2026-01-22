import uuid
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel


# ==================== 公司模型 ====================

class CompanyBase(SQLModel):
    """公司基础模型"""
    name: str = Field(max_length=200, index=True, description="公司名称")
    code: str = Field(unique=True, max_length=50, index=True, description="公司代码")
    address: Optional[str] = Field(default=None, max_length=500, description="公司地址")
    contact_person: Optional[str] = Field(default=None, max_length=100, description="联系人")
    contact_phone: Optional[str] = Field(default=None, max_length=50, description="联系电话")
    contact_email: Optional[str] = Field(default=None, max_length=100, description="联系邮箱")
    description: Optional[str] = Field(default=None, max_length=1000, description="公司描述")
    is_active: bool = Field(default=True, description="是否启用")


class CompanyCreate(CompanyBase):
    """创建公司请求模型"""
    pass


class CompanyUpdate(SQLModel):
    """更新公司请求模型"""
    name: Optional[str] = Field(default=None, max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=500)
    contact_person: Optional[str] = Field(default=None, max_length=100)
    contact_phone: Optional[str] = Field(default=None, max_length=50)
    contact_email: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_active: Optional[bool] = None


class Company(CompanyBase, table=True):
    """公司数据库模型"""
    __tablename__ = "company"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # 关联关系
    users: list["User"] = Relationship(back_populates="company")


class CompanyPublic(CompanyBase):
    """公司公开响应模型"""
    id: uuid.UUID
    user_count: Optional[int] = Field(default=None, description="关联用户数量")


class CompaniesPublic(SQLModel):
    """公司列表响应模型"""
    data: list[CompanyPublic]
    count: int

