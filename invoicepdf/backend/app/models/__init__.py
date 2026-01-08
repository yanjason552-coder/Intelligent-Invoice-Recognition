"""
Models 模块 - 统一导出所有数据模型

此模块统一导出所有数据模型，确保：
1. Alembic 迁移时能识别所有表
2. 其他模块可以统一从 app.models 导入
"""

# 导入基础模型（包含 User, Item 等基础模型和通用类型）
from app.models.models import (
    # SQLModel 基类
    SQLModel,
    # 用户相关
    User,
    UserBase,
    UserCreate,
    UserUpdate,
    UserUpdateMe,
    UserPublic,
    UsersPublic,
    UserRegister,
    UpdatePassword,
    # 项目相关
    Item,
    ItemBase,
    ItemCreate,
    ItemUpdate,
    ItemPublic,
    ItemsPublic,
    # 通用类型
    Message,
    Token,
    TokenPayload,
    NewPassword,
    # API 响应格式
    ApiResponse,
    PaginatedResponse,
    ApiRequest,
    PaginatedRequest,
    CrudRequest,
    UserRequest,
    ItemRequest,
    # 统一接口格式
    UnifiedRequest,
    UnifiedResponse,
    PaginationInfo,
    ErrorInfo,
    # 类型变量
    T,
)

# 导入销售订单模型
from app.models.models_sales_order_doc_d import (
    SalesOrderDocD,
    SalesOrderDocDCreate,
    SalesOrderDocDUpdate,
    SalesOrderDocDResponse,
    SalesOrderDocDFeature,
    SalesOrderDocDFeatureCreate,
    SalesOrderDocDFeatureUpdate,
    SalesOrderDocDFeatureResponse,
)

# 导入特征模型
from app.models.models_feature import (
    Feature,
    FeatureCreate,
    FeatureUpdate,
    FeatureResponse,
    FeatureD,
    FeatureDCreate,
    FeatureDUpdate,
    FeatureDResponse,
)

# 导入材料相关模型
from app.models.models_material_class import (
    MaterialClass,
    MaterialClassD,
    MaterialClassCreate,
    MaterialClassResponse,
)

from app.models.models_material import (
    Material,
    MaterialD,
)

from app.models.models_material_density import (
    MaterialDensity,
    MaterialDensityCreate,
    MaterialDensityUpdate,
    MaterialDensityResponse,
    MaterialDensityQuery,
)

# 导入库存模型
from app.models.models_inventory import (
    Inventory,
    MaterialLotFeature,
    MaterialLot,
)

# 导入表面工艺模型
from app.models.models_surface_technology import (
    SurfaceTechnology,
    SurfaceTechnologyD,
)

# 导入操作模型
from app.models.models_operation import (
    Operation,
)

# 导入搭切布局模型
from app.models.models_nesting_layout import (
    NestingLayout,
    NestingLayoutD,
    NestingLayoutSd,
)

# 导入生产订单模型
from app.models.models_production_order import (
    ProductionOrder,
    ProductionOrderD,
    ProductionOrderProduce,
    ProductionOrderRouting,
)

# 导入票据识别模型
from app.models.models_invoice import (
    Invoice,
    InvoiceFile,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    RecognitionTask,
    RecognitionTaskCreate,
    RecognitionTaskResponse,
    RecognitionResult,
    RecognitionResultResponse,
    RecognitionField,
    ReviewRecord,
    OCRConfig,
    LLMConfig,
    RecognitionRule,
)

# 导入角色和权限模型
from app.models.models_role_permission import (
    Role,
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RolePublic,
    RolesPublic,
    Permission,
    PermissionBase,
    PermissionCreate,
    PermissionUpdate,
    PermissionPublic,
    PermissionsPublic,
    UserRole,
    UserRoleBase,
    UserRoleCreate,
    UserRolePublic,
    RolePermission,
    RolePermissionBase,
    RolePermissionCreate,
    RolePermissionPublic,
)

# 导入公司模型
from app.models.models_company import (
    Company,
    CompanyBase,
    CompanyCreate,
    CompanyUpdate,
    CompanyPublic,
    CompaniesPublic,
)

# 从基础模型导入类型别名（如果存在）
from app.models.models import MaterialClassRequest, MaterialClassListRequest, MaterialClassDeleteRequest

__all__ = [
    # SQLModel 基类
    "SQLModel",
    # 用户相关
    "User",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserUpdateMe",
    "UserPublic",
    "UsersPublic",
    "UserRegister",
    "UpdatePassword",
    # 项目相关
    "Item",
    "ItemBase",
    "ItemCreate",
    "ItemUpdate",
    "ItemPublic",
    "ItemsPublic",
    # 通用类型
    "Message",
    "Token",
    "TokenPayload",
    "NewPassword",
    # API 响应格式
    "ApiResponse",
    "PaginatedResponse",
    "ApiRequest",
    "PaginatedRequest",
    "CrudRequest",
    "UserRequest",
    "ItemRequest",
    # 统一接口格式
    "UnifiedRequest",
    "UnifiedResponse",
    "PaginationInfo",
    "ErrorInfo",
    # 销售订单
    "SalesOrderDocD",
    "SalesOrderDocDCreate",
    "SalesOrderDocDUpdate",
    "SalesOrderDocDResponse",
    "SalesOrderDocDFeature",
    "SalesOrderDocDFeatureCreate",
    "SalesOrderDocDFeatureUpdate",
    "SalesOrderDocDFeatureResponse",
    # 特征
    "Feature",
    "FeatureCreate",
    "FeatureUpdate",
    "FeatureResponse",
    "FeatureD",
    "FeatureDCreate",
    "FeatureDUpdate",
    "FeatureDResponse",
    # 材料相关
    "MaterialClass",
    "MaterialClassD",
    "MaterialClassCreate",
    "MaterialClassResponse",
    "Material",
    "MaterialD",
    "MaterialDensity",
    "MaterialDensityCreate",
    "MaterialDensityUpdate",
    "MaterialDensityResponse",
    "MaterialDensityQuery",
    # 库存
    "Inventory",
    "MaterialLotFeature",
    "MaterialLot",
    # 表面工艺
    "SurfaceTechnology",
    "SurfaceTechnologyD",
    # 操作
    "Operation",
    # 搭切布局
    "NestingLayout",
    "NestingLayoutD",
    "NestingLayoutSd",
    # 生产订单
    "ProductionOrder",
    "ProductionOrderD",
    "ProductionOrderProduce",
    "ProductionOrderRouting",
    # 票据识别
    "Invoice",
    "InvoiceFile",
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceResponse",
    "RecognitionTask",
    "RecognitionTaskCreate",
    "RecognitionTaskResponse",
    "RecognitionResult",
    "RecognitionResultResponse",
    "RecognitionField",
    "ReviewRecord",
    "OCRConfig",
    "LLMConfig",
    "RecognitionRule",
    # 类型别名
    "MaterialClassRequest",
    "MaterialClassListRequest",
    "MaterialClassDeleteRequest",
    # 角色和权限
    "Role",
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RolePublic",
    "RolesPublic",
    "Permission",
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionPublic",
    "PermissionsPublic",
    "UserRole",
    "UserRoleBase",
    "UserRoleCreate",
    "UserRolePublic",
    "RolePermission",
    "RolePermissionBase",
    "RolePermissionCreate",
    "RolePermissionPublic",
    # 公司相关
    "Company",
    "CompanyBase",
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyPublic",
    "CompaniesPublic",
    # 类型变量
    "T",
]

