import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func, or_

from app.api.deps import (
    SessionDep,
    get_current_active_superuser,
)
from app.models import (
    Role,
    RoleCreate,
    RoleUpdate,
    RolePublic,
    RolesPublic,
    UserRole,
    UserRoleCreate,
    UserRolePublic,
    RolePermission,
    RolePermissionCreate,
    Permission,
    PermissionPublic,
    Message,
)

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RolesPublic,
)
def read_roles(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    获取角色列表
    """
    count_statement = select(func.count()).select_from(Role)
    count = session.exec(count_statement).one()

    statement = select(Role).offset(skip).limit(limit)
    roles = session.exec(statement).all()

    return RolesPublic(data=roles, count=count)


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RolePublic,
)
def create_role(
    *,
    session: SessionDep,
    role_in: RoleCreate,
) -> Any:
    """
    创建新角色
    """
    # 检查角色代码是否已存在
    existing_role = session.exec(
        select(Role).where(Role.code == role_in.code)
    ).first()
    if existing_role:
        raise HTTPException(
            status_code=400,
            detail="该角色代码已存在",
        )

    role = Role(**role_in.model_dump())
    session.add(role)
    session.commit()
    session.refresh(role)
    return role


@router.get(
    "/{role_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RolePublic,
)
def read_role(
    role_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    根据ID获取角色
    """
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return role


@router.patch(
    "/{role_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RolePublic,
)
def update_role(
    *,
    session: SessionDep,
    role_id: uuid.UUID,
    role_in: RoleUpdate,
) -> Any:
    """
    更新角色
    """
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 如果更新代码，检查是否冲突
    if role_in.code and role_in.code != role.code:
        existing_role = session.exec(
            select(Role).where(Role.code == role_in.code)
        ).first()
        if existing_role:
            raise HTTPException(
                status_code=400,
                detail="该角色代码已存在",
            )

    role_data = role_in.model_dump(exclude_unset=True)
    role.sqlmodel_update(role_data)
    session.add(role)
    session.commit()
    session.refresh(role)
    return role


@router.delete(
    "/{role_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def delete_role(
    *,
    session: SessionDep,
    role_id: uuid.UUID,
) -> Any:
    """
    删除角色
    """
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    session.delete(role)
    session.commit()
    return Message(message="角色删除成功")


@router.get(
    "/{role_id}/users",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[UserRolePublic],
)
def get_role_users(
    role_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    获取角色的用户列表
    """
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    statement = select(UserRole).where(UserRole.role_id == role_id)
    user_roles = session.exec(statement).all()
    
    # 加载关联的角色信息
    result = []
    for user_role in user_roles:
        session.refresh(user_role, ["role"])
        result.append(UserRolePublic(
            id=user_role.id,
            user_id=user_role.user_id,
            role_id=user_role.role_id,
            role=RolePublic(**user_role.role.model_dump()) if user_role.role else None
        ))
    
    return result


@router.post(
    "/{role_id}/users/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserRolePublic,
)
def assign_role_to_user(
    *,
    session: SessionDep,
    role_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Any:
    """
    为用户分配角色
    """
    # 检查角色是否存在
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 检查用户是否存在
    from app.models import User
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已存在关联
    existing = session.exec(
        select(UserRole).where(
            UserRole.role_id == role_id,
            UserRole.user_id == user_id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户已拥有该角色")

    user_role = UserRole(role_id=role_id, user_id=user_id)
    session.add(user_role)
    session.commit()
    session.refresh(user_role, ["role"])
    
    return UserRolePublic(
        id=user_role.id,
        user_id=user_role.user_id,
        role_id=user_role.role_id,
        role=RolePublic(**user_role.role.model_dump()) if user_role.role else None
    )


@router.delete(
    "/{role_id}/users/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def remove_role_from_user(
    *,
    session: SessionDep,
    role_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Any:
    """
    移除用户的角色
    """
    user_role = session.exec(
        select(UserRole).where(
            UserRole.role_id == role_id,
            UserRole.user_id == user_id
        )
    ).first()
    
    if not user_role:
        raise HTTPException(status_code=404, detail="用户角色关联不存在")

    session.delete(user_role)
    session.commit()
    return Message(message="角色移除成功")

