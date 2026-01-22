import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from typing import Any, Generic, TypeVar, Optional

# 定义泛型类型变量
T = TypeVar('T')


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    company_id: uuid.UUID | None = Field(default=None, foreign_key="company.id", description="公司ID")
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    user_roles: list["UserRole"] = Relationship(back_populates="user", cascade_delete=True)
    company: Optional["Company"] = Relationship(back_populates="users")


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# 统一的API响应格式
class ApiResponse(SQLModel):
    success: bool
    data: Any | None = None
    message: str | None = None
    error_code: str | None = None
    timestamp: str | None = None


# 分页响应格式
class PaginatedResponse(SQLModel):
    success: bool
    data: list[Any]
    count: int
    page: int | None = None
    limit: int | None = None
    total_pages: int | None = None
    message: str | None = None
    timestamp: str | None = None


# 统一的API请求格式
class ApiRequest(SQLModel):
    data: Any | None = None
    params: dict[str, Any] | None = None
    filters: dict[str, Any] | None = None
    sort: dict[str, str] | None = None  # {"field": "asc/desc"}
    timestamp: str | None = None


# 分页请求格式
class PaginatedRequest(SQLModel):
    page: int = 1
    limit: int = 20
    filters: dict[str, Any] | None = None
    sort: dict[str, str] | None = None
    search: str | None = None
    timestamp: str | None = None


# 通用CRUD请求格式
class CrudRequest(SQLModel):
    action: str  # "create", "read", "update", "delete", "list"
    data: Any | None = None
    id: str | None = None
    filters: dict[str, Any] | None = None
    pagination: PaginatedRequest | None = None
    timestamp: str | None = None


# 用户相关请求格式
class UserRequest(SQLModel):
    action: str  # "login", "register", "update", "delete", "list"
    email: str | None = None
    password: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    filters: dict[str, Any] | None = None
    pagination: PaginatedRequest | None = None
    timestamp: str | None = None


# 项目相关请求格式
class ItemRequest(SQLModel):
    action: str  # "create", "read", "update", "delete", "list"
    id: str | None = None
    title: str | None = None
    description: str | None = None
    owner_id: str | None = None
    filters: dict[str, Any] | None = None
    pagination: PaginatedRequest | None = None
    timestamp: str | None = None


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


# 统一的API传入参数对象
class UnifiedRequest(SQLModel, Generic[T]):
    """统一的API传入参数对象"""
    # 基础信息
    action: str  # 操作类型：login, register, create, read, update, delete, list
    module: str  # 模块名称：user, item, order, etc.
    
    # 数据字段
    data: T | None = None  # 主要数据
    params: dict[str, Any] | None = None  # 额外参数
    filters: dict[str, Any] | None = None  # 过滤条件
    sort: dict[str, str] | None = None  # 排序条件 {"field": "asc/desc"}
    
    # 分页信息
    page: int | None = None
    limit: int | None = None
    search: str | None = None  # 搜索关键词
    
    # 安全信息
    timestamp: str | None = None  # 请求时间戳
    signature: str | None = None  # 请求签名（可选）
    
    # 元数据
    request_id: str | None = None  # 请求ID
    client_info: dict[str, Any] | None = None  # 客户端信息


# 统一的API返回参数对象
class UnifiedResponse(SQLModel, Generic[T]):
    """统一的API返回参数对象"""
    # 基础状态
    success: bool  # 操作是否成功
    code: int = 200  # HTTP状态码
    
    # 数据内容
    data: T | None = None  # 主要数据
    message: str | None = None  # 响应消息
    error_code: str | None = None  # 错误代码
    
    # 分页信息（当返回列表时）
    pagination: dict[str, Any] | None = None  # 分页信息
    
    # 元数据
    timestamp: str | None = None  # 响应时间戳
    request_id: str | None = None  # 请求ID
    duration: float | None = None  # 处理耗时（毫秒）
    
    # 调试信息（开发环境）
    debug: dict[str, Any] | None = None  # 调试信息


# 分页信息对象
class PaginationInfo(SQLModel):
    """分页信息对象"""
    page: int  # 当前页码
    limit: int  # 每页数量
    total: int  # 总数量
    total_pages: int  # 总页数
    has_next: bool  # 是否有下一页
    has_prev: bool  # 是否有上一页


# 错误信息对象
class ErrorInfo(SQLModel):
    """错误信息对象"""
    code: str  # 错误代码
    message: str  # 错误消息
    details: dict[str, Any] | None = None  # 错误详情
    field: str | None = None  # 错误字段（表单验证错误时）


# 导入销售订单项目表模型
from app.models.models_sales_order_doc_d import (
    SalesOrderDocD, SalesOrderDocDCreate, SalesOrderDocDUpdate, SalesOrderDocDResponse,
    SalesOrderDocDFeature, SalesOrderDocDFeatureCreate, SalesOrderDocDFeatureUpdate, SalesOrderDocDFeatureResponse
)
from app.models.models_feature import (
    Feature, FeatureCreate, FeatureUpdate, FeatureResponse,
    FeatureD, FeatureDCreate, FeatureDUpdate, FeatureDResponse
)

# 导入物料类别模型
from app.models.models_material_class import MaterialClass, MaterialClassD

# 定义具体的请求类型别名
MaterialClassRequest = UnifiedRequest[MaterialClass]
MaterialClassListRequest = UnifiedRequest[dict[str, Any]]  # 列表查询通常不需要具体数据
MaterialClassDeleteRequest = UnifiedRequest[dict[str, str]]  # 删除请求只需要ID