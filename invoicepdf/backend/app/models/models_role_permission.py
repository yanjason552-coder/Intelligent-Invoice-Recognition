import uuid
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel, Column, String, Text
from sqlalchemy import JSON


# ==================== 角色模型 ====================

class RoleBase(SQLModel):
    """角色基础模型"""
    name: str = Field(max_length=100, index=True, description="角色名称")
    code: str = Field(unique=True, max_length=50, index=True, description="角色代码")
    description: Optional[str] = Field(default=None, max_length=500, description="角色描述")
    is_active: bool = Field(default=True, description="是否启用")


class RoleCreate(RoleBase):
    """创建角色请求模型"""
    pass


class RoleUpdate(SQLModel):
    """更新角色请求模型"""
    name: Optional[str] = Field(default=None, max_length=100)
    code: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class Role(RoleBase, table=True):
    """角色数据库模型"""
    __tablename__ = "role"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # 关联关系
    user_roles: list["UserRole"] = Relationship(back_populates="role", cascade_delete=True)
    role_permissions: list["RolePermission"] = Relationship(back_populates="role", cascade_delete=True)


class RolePublic(RoleBase):
    """角色公开响应模型"""
    id: uuid.UUID


class RolesPublic(SQLModel):
    """角色列表响应模型"""
    data: list[RolePublic]
    count: int


# ==================== 权限模型 ====================

class PermissionBase(SQLModel):
    """权限基础模型"""
    name: str = Field(max_length=100, index=True, description="权限名称")
    code: str = Field(unique=True, max_length=100, index=True, description="权限代码")
    resource: str = Field(max_length=100, description="资源名称（如：user, invoice, template）")
    action: str = Field(max_length=50, description="操作类型（如：create, read, update, delete）")
    description: Optional[str] = Field(default=None, max_length=500, description="权限描述")
    is_active: bool = Field(default=True, description="是否启用")


class PermissionCreate(PermissionBase):
    """创建权限请求模型"""
    pass


class PermissionUpdate(SQLModel):
    """更新权限请求模型"""
    name: Optional[str] = Field(default=None, max_length=100)
    code: Optional[str] = Field(default=None, max_length=100)
    resource: Optional[str] = Field(default=None, max_length=100)
    action: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class Permission(PermissionBase, table=True):
    """权限数据库模型"""
    __tablename__ = "permission"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # 关联关系
    role_permissions: list["RolePermission"] = Relationship(back_populates="permission", cascade_delete=True)


class PermissionPublic(PermissionBase):
    """权限公开响应模型"""
    id: uuid.UUID


class PermissionsPublic(SQLModel):
    """权限列表响应模型"""
    data: list[PermissionPublic]
    count: int


# ==================== 用户角色关联模型 ====================

class UserRoleBase(SQLModel):
    """用户角色关联基础模型"""
    user_id: uuid.UUID = Field(foreign_key="user.id", description="用户ID")
    role_id: uuid.UUID = Field(foreign_key="role.id", description="角色ID")


class UserRoleCreate(UserRoleBase):
    """创建用户角色关联请求模型"""
    pass


class UserRole(UserRoleBase, table=True):
    """用户角色关联数据库模型"""
    __tablename__ = "user_role"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # 关联关系
    user: "User" = Relationship(back_populates="user_roles")
    role: Role = Relationship(back_populates="user_roles")


class UserRolePublic(UserRoleBase):
    """用户角色关联公开响应模型"""
    id: uuid.UUID
    role: Optional[RolePublic] = None


# ==================== 角色权限关联模型 ====================

class RolePermissionBase(SQLModel):
    """角色权限关联基础模型"""
    role_id: uuid.UUID = Field(foreign_key="role.id", description="角色ID")
    permission_id: uuid.UUID = Field(foreign_key="permission.id", description="权限ID")


class RolePermissionCreate(RolePermissionBase):
    """创建角色权限关联请求模型"""
    pass


class RolePermission(RolePermissionBase, table=True):
    """角色权限关联数据库模型"""
    __tablename__ = "role_permission"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # 关联关系
    role: Role = Relationship(back_populates="role_permissions")
    permission: Permission = Relationship(back_populates="role_permissions")


class RolePermissionPublic(RolePermissionBase):
    """角色权限关联公开响应模型"""
    id: uuid.UUID
    role: Optional[RolePublic] = None
    permission: Optional[PermissionPublic] = None


# ==================== 用户扩展模型 ====================

# 需要在 models.py 中的 User 模型添加关联关系
# user_roles: list["UserRole"] = Relationship(back_populates="user", cascade_delete=True)

