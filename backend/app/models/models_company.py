import uuid
from typing import Optional
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, DateTime, Table, ForeignKey


# ==================== 用户公司关联表（多对多）====================

class UserCompany(SQLModel, table=True):
    """用户公司关联表 - 实现用户和公司的多对多关系"""
    __tablename__ = "user_company"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", description="用户ID")
    company_id: uuid.UUID = Field(foreign_key="company.id", description="公司ID")
    is_primary: bool = Field(default=False, description="是否为主公司（一个用户只能有一个主公司）")
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="关联时间")
    
    # 关联关系
    user: "User" = Relationship(back_populates="user_companies")
    company: "Company" = Relationship(back_populates="user_companies")


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
    
    # 时间字段
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    
    # 关联关系（多对多）
    user_companies: list["UserCompany"] = Relationship(back_populates="company")


class CompanyPublic(CompanyBase):
    """公司公开响应模型"""
    id: uuid.UUID
    create_time: datetime = Field(description="创建时间")
    user_count: Optional[int] = Field(default=None, description="关联用户数量")


class CompaniesPublic(SQLModel):
    """公司列表响应模型"""
    data: list[CompanyPublic]
    count: int

