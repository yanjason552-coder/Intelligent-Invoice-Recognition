import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func, or_

from app.api.deps import (
    SessionDep,
    get_current_active_superuser,
)
from app.models import (
    Permission,
    PermissionCreate,
    PermissionUpdate,
    PermissionPublic,
    PermissionsPublic,
    RolePermission,
    RolePermissionCreate,
    Role,
    RolePublic,
    Message,
)

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=PermissionsPublic,
)
def read_permissions(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    resource: str | None = None,
) -> Any:
    """
    获取权限列表
    """
    statement = select(Permission)
    
    if resource:
        statement = statement.where(Permission.resource == resource)
    
    count_statement = select(func.count()).select_from(Permission)
    if resource:
        count_statement = count_statement.where(Permission.resource == resource)
    count = session.exec(count_statement).one()

    statement = statement.offset(skip).limit(limit)
    permissions = session.exec(statement).all()

    return PermissionsPublic(data=permissions, count=count)


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=PermissionPublic,
)
def create_permission(
    *,
    session: SessionDep,
    permission_in: PermissionCreate,
) -> Any:
    """
    创建新权限
    """
    # 检查权限代码是否已存在
    existing_permission = session.exec(
        select(Permission).where(Permission.code == permission_in.code)
    ).first()
    if existing_permission:
        raise HTTPException(
            status_code=400,
            detail="该权限代码已存在",
        )

    permission = Permission(**permission_in.model_dump())
    session.add(permission)
    session.commit()
    session.refresh(permission)
    return permission


@router.get(
    "/{permission_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=PermissionPublic,
)
def read_permission(
    permission_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    根据ID获取权限
    """
    permission = session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    return permission


@router.patch(
    "/{permission_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=PermissionPublic,
)
def update_permission(
    *,
    session: SessionDep,
    permission_id: uuid.UUID,
    permission_in: PermissionUpdate,
) -> Any:
    """
    更新权限
    """
    permission = session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")

    # 如果更新代码，检查是否冲突
    if permission_in.code and permission_in.code != permission.code:
        existing_permission = session.exec(
            select(Permission).where(Permission.code == permission_in.code)
        ).first()
        if existing_permission:
            raise HTTPException(
                status_code=400,
                detail="该权限代码已存在",
            )

    permission_data = permission_in.model_dump(exclude_unset=True)
    permission.sqlmodel_update(permission_data)
    session.add(permission)
    session.commit()
    session.refresh(permission)
    return permission


@router.delete(
    "/{permission_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def delete_permission(
    *,
    session: SessionDep,
    permission_id: uuid.UUID,
) -> Any:
    """
    删除权限
    """
    permission = session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")

    session.delete(permission)
    session.commit()
    return Message(message="权限删除成功")


@router.get(
    "/{permission_id}/roles",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[RolePublic],
)
def get_permission_roles(
    permission_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    获取拥有该权限的角色列表
    """
    permission = session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")

    statement = (
        select(Role)
        .join(RolePermission)
        .where(RolePermission.permission_id == permission_id)
    )
    roles = session.exec(statement).all()
    
    return roles


@router.post(
    "/roles/{role_id}/permissions/{permission_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def assign_permission_to_role(
    *,
    session: SessionDep,
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
) -> Any:
    """
    为角色分配权限
    """
    # 检查角色是否存在
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 检查权限是否存在
    permission = session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")

    # 检查是否已存在关联
    existing = session.exec(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="角色已拥有该权限")

    role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
    session.add(role_permission)
    session.commit()
    return Message(message="权限分配成功")


@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def remove_permission_from_role(
    *,
    session: SessionDep,
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
) -> Any:
    """
    移除角色的权限
    """
    role_permission = session.exec(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        )
    ).first()
    
    if not role_permission:
        raise HTTPException(status_code=404, detail="角色权限关联不存在")

    session.delete(role_permission)
    session.commit()
    return Message(message="权限移除成功")


@router.get(
    "/roles/{role_id}/permissions",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[PermissionPublic],
)
def get_role_permissions(
    role_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    获取角色的权限列表
    """
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    statement = (
        select(Permission)
        .join(RolePermission)
        .where(RolePermission.role_id == role_id)
    )
    permissions = session.exec(statement).all()
    
    return permissions

