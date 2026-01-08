"""
使用统一对象的API路由示例
展示如何使用UnifiedRequest和UnifiedResponse对象
"""

import time
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from app.api.deps import SessionDep, CurrentUser
from app.models import UnifiedRequest, UnifiedResponse
from app.utils import (
    create_unified_success_response, create_unified_error_response, 
    create_unified_pagination_response, validate_unified_request,
    extract_request_data, sanitize_request_data
)
from app import crud
from app.models import User, Item, UserCreate, ItemCreate

router = APIRouter(prefix="/unified-v2", tags=["unified-v2"])


@router.post("/api", response_model=UnifiedResponse)
async def unified_api_endpoint(
    request: UnifiedRequest,
    session: SessionDep,
    current_user: CurrentUser | None = None
) -> dict[str, Any]:
    """
    统一的API端点
    使用UnifiedRequest和UnifiedResponse对象
    """
    start_time = time.time()
    
    try:
        # 记录请求（清理敏感信息）
        sanitized_request = sanitize_request_data(request.model_dump())
        print(f"统一API请求: {sanitized_request}")
        
        # 验证请求
        is_valid, error_message = validate_unified_request(request.model_dump())
        if not is_valid:
            return create_unified_error_response(
                message=error_message,
                error_code="INVALID_REQUEST",
                request_id=request.request_id,
                duration=(time.time() - start_time) * 1000
            )
        
        # 提取请求数据
        request_data = extract_request_data(request.model_dump())
        action = request_data["action"]
        module = request_data["module"]
        
        # 根据模块和操作类型分发处理
        if module == "user":
            return await _handle_user_operations(request_data, session, current_user, start_time)
        elif module == "item":
            if not current_user:
                return create_unified_error_response(
                    message="需要登录",
                    error_code="AUTHENTICATION_REQUIRED",
                    request_id=request.request_id,
                    duration=(time.time() - start_time) * 1000
                )
            return await _handle_item_operations(request_data, session, current_user, start_time)
        else:
            return create_unified_error_response(
                message=f"不支持的模块: {module}",
                error_code="UNSUPPORTED_MODULE",
                request_id=request.request_id,
                duration=(time.time() - start_time) * 1000
            )
            
    except Exception as e:
        return create_unified_error_response(
            message=f"操作失败: {str(e)}",
            error_code="OPERATION_FAILED",
            request_id=request.request_id,
            duration=(time.time() - start_time) * 1000
        )


async def _handle_user_operations(
    request_data: dict[str, Any], 
    session: Session, 
    current_user: CurrentUser | None,
    start_time: float
) -> dict[str, Any]:
    """处理用户相关操作"""
    action = request_data["action"]
    data = request_data["data"]
    request_id = request_data["request_id"]
    
    if action == "login":
        return await _handle_user_login(request_data, session, start_time)
    elif action == "register":
        return await _handle_user_register(request_data, session, start_time)
    elif action == "list":
        if not current_user or not current_user.is_superuser:
            return create_unified_error_response(
                message="权限不足",
                error_code="INSUFFICIENT_PERMISSIONS",
                request_id=request_id,
                duration=(time.time() - start_time) * 1000
            )
        return await _handle_user_list(request_data, session, start_time)
    else:
        return create_unified_error_response(
            message=f"不支持的用户操作: {action}",
            error_code="UNSUPPORTED_ACTION",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )


async def _handle_item_operations(
    request_data: dict[str, Any], 
    session: Session, 
    current_user: CurrentUser,
    start_time: float
) -> dict[str, Any]:
    """处理项目相关操作"""
    action = request_data["action"]
    request_id = request_data["request_id"]
    
    if action == "create":
        return await _handle_item_create(request_data, session, current_user, start_time)
    elif action == "read":
        return await _handle_item_read(request_data, session, current_user, start_time)
    elif action == "update":
        return await _handle_item_update(request_data, session, current_user, start_time)
    elif action == "delete":
        return await _handle_item_delete(request_data, session, current_user, start_time)
    elif action == "list":
        return await _handle_item_list(request_data, session, current_user, start_time)
    else:
        return create_unified_error_response(
            message=f"不支持的项目操作: {action}",
            error_code="UNSUPPORTED_ACTION",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )


# 用户操作处理函数
async def _handle_user_login(
    request_data: dict[str, Any], 
    session: Session, 
    start_time: float
) -> dict[str, Any]:
    """处理用户登录"""
    data = request_data["data"]
    request_id = request_data["request_id"]
    
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return create_unified_error_response(
            message="邮箱和密码不能为空",
            error_code="MISSING_CREDENTIALS",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    user = crud.authenticate(session=session, email=email, password=password)
    if not user:
        return create_unified_error_response(
            message="邮箱或密码错误",
            error_code="INVALID_CREDENTIALS",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    if not user.is_active:
        return create_unified_error_response(
            message="用户未激活",
            error_code="USER_INACTIVE",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    # 生成访问令牌
    from app.core import security
    from app.core.config import settings
    from datetime import timedelta
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    
    token_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser
        }
    }
    
    return create_unified_success_response(
        data=token_data,
        message="登录成功",
        request_id=request_id,
        duration=(time.time() - start_time) * 1000
    )


async def _handle_user_register(
    request_data: dict[str, Any], 
    session: Session, 
    start_time: float
) -> dict[str, Any]:
    """处理用户注册"""
    data = request_data["data"]
    request_id = request_data["request_id"]
    
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")
    
    if not email or not password:
        return create_unified_error_response(
            message="邮箱和密码不能为空",
            error_code="MISSING_CREDENTIALS",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    # 检查用户是否已存在
    existing_user = crud.get_user_by_email(session=session, email=email)
    if existing_user:
        return create_unified_error_response(
            message="用户已存在",
            error_code="USER_EXISTS",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    # 创建新用户
    user_create = UserCreate(
        email=email,
        password=password,
        full_name=full_name
    )
    
    user = crud.create_user(session=session, user_create=user_create)
    
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser
    }
    
    return create_unified_success_response(
        data=user_data,
        message="用户注册成功",
        request_id=request_id,
        duration=(time.time() - start_time) * 1000
    )


async def _handle_user_list(
    request_data: dict[str, Any], 
    session: Session, 
    start_time: float
) -> dict[str, Any]:
    """处理用户列表查询"""
    filters = request_data["filters"]
    sort = request_data["sort"]
    page = request_data["page"]
    limit = request_data["limit"]
    search = request_data["search"]
    request_id = request_data["request_id"]
    
    # 构建查询
    query = select(User)
    
    # 应用过滤器
    if filters:
        if filters.get("is_active") is not None:
            query = query.where(User.is_active == filters["is_active"])
        if filters.get("is_superuser") is not None:
            query = query.where(User.is_superuser == filters["is_superuser"])
    
    # 应用搜索
    if search:
        query = query.where(User.email.contains(search) | User.full_name.contains(search))
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()
    
    # 应用分页
    skip = (page - 1) * limit
    query = query.offset(skip).limit(limit)
    
    # 应用排序
    if sort:
        for field, direction in sort.items():
            if hasattr(User, field):
                if direction.lower() == "desc":
                    query = query.order_by(getattr(User, field).desc())
                else:
                    query = query.order_by(getattr(User, field))
    
    users = session.exec(query).all()
    
    # 转换为字典格式
    users_data = [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser
        }
        for user in users
    ]
    
    return create_unified_pagination_response(
        data=users_data,
        total=total_count,
        page=page,
        limit=limit,
        message="用户列表查询成功",
        request_id=request_id,
        duration=(time.time() - start_time) * 1000
    )


# 项目操作处理函数
async def _handle_item_create(
    request_data: dict[str, Any], 
    session: Session, 
    current_user: CurrentUser,
    start_time: float
) -> dict[str, Any]:
    """处理项目创建"""
    data = request_data["data"]
    request_id = request_data["request_id"]
    
    title = data.get("title")
    description = data.get("description")
    
    if not title:
        return create_unified_error_response(
            message="标题不能为空",
            error_code="MISSING_TITLE",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    item_create = ItemCreate(
        title=title,
        description=description
    )
    
    item = Item.model_validate(item_create, update={"owner_id": current_user.id})
    session.add(item)
    session.commit()
    session.refresh(item)
    
    item_data = {
        "id": str(item.id),
        "title": item.title,
        "description": item.description,
        "owner_id": str(item.owner_id)
    }
    
    return create_unified_success_response(
        data=item_data,
        message="项目创建成功",
        request_id=request_id,
        duration=(time.time() - start_time) * 1000
    )


async def _handle_item_read(
    request_data: dict[str, Any], 
    session: Session, 
    current_user: CurrentUser,
    start_time: float
) -> dict[str, Any]:
    """处理项目读取"""
    data = request_data["data"]
    request_id = request_data["request_id"]
    
    item_id = data.get("id")
    
    if not item_id:
        return create_unified_error_response(
            message="项目ID不能为空",
            error_code="MISSING_ITEM_ID",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    item = session.get(Item, item_id)
    if not item:
        return create_unified_error_response(
            message="项目不存在",
            error_code="ITEM_NOT_FOUND",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    if not current_user.is_superuser and item.owner_id != current_user.id:
        return create_unified_error_response(
            message="权限不足",
            error_code="INSUFFICIENT_PERMISSIONS",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    item_data = {
        "id": str(item.id),
        "title": item.title,
        "description": item.description,
        "owner_id": str(item.owner_id)
    }
    
    return create_unified_success_response(
        data=item_data,
        message="项目查询成功",
        request_id=request_id,
        duration=(time.time() - start_time) * 1000
    )


async def _handle_item_update(
    request_data: dict[str, Any], 
    session: Session, 
    current_user: CurrentUser,
    start_time: float
) -> dict[str, Any]:
    """处理项目更新"""
    data = request_data["data"]
    request_id = request_data["request_id"]
    
    item_id = data.get("id")
    title = data.get("title")
    description = data.get("description")
    
    if not item_id:
        return create_unified_error_response(
            message="项目ID不能为空",
            error_code="MISSING_ITEM_ID",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    item = session.get(Item, item_id)
    if not item:
        return create_unified_error_response(
            message="项目不存在",
            error_code="ITEM_NOT_FOUND",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    if not current_user.is_superuser and item.owner_id != current_user.id:
        return create_unified_error_response(
            message="权限不足",
            error_code="INSUFFICIENT_PERMISSIONS",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    # 更新项目信息
    if title is not None:
        item.title = title
    if description is not None:
        item.description = description
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    item_data = {
        "id": str(item.id),
        "title": item.title,
        "description": item.description,
        "owner_id": str(item.owner_id)
    }
    
    return create_unified_success_response(
        data=item_data,
        message="项目更新成功",
        request_id=request_id,
        duration=(time.time() - start_time) * 1000
    )


async def _handle_item_delete(
    request_data: dict[str, Any], 
    session: Session, 
    current_user: CurrentUser,
    start_time: float
) -> dict[str, Any]:
    """处理项目删除"""
    data = request_data["data"]
    request_id = request_data["request_id"]
    
    item_id = data.get("id")
    
    if not item_id:
        return create_unified_error_response(
            message="项目ID不能为空",
            error_code="MISSING_ITEM_ID",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    item = session.get(Item, item_id)
    if not item:
        return create_unified_error_response(
            message="项目不存在",
            error_code="ITEM_NOT_FOUND",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    if not current_user.is_superuser and item.owner_id != current_user.id:
        return create_unified_error_response(
            message="权限不足",
            error_code="INSUFFICIENT_PERMISSIONS",
            request_id=request_id,
            duration=(time.time() - start_time) * 1000
        )
    
    session.delete(item)
    session.commit()
    
    return create_unified_success_response(
        message="项目删除成功",
        request_id=request_id,
        duration=(time.time() - start_time) * 1000
    )


async def _handle_item_list(
    request_data: dict[str, Any], 
    session: Session, 
    current_user: CurrentUser,
    start_time: float
) -> dict[str, Any]:
    """处理项目列表查询"""
    filters = request_data["filters"]
    sort = request_data["sort"]
    page = request_data["page"]
    limit = request_data["limit"]
    search = request_data["search"]
    request_id = request_data["request_id"]
    
    # 构建查询
    if current_user.is_superuser:
        query = select(Item)
    else:
        query = select(Item).where(Item.owner_id == current_user.id)
    
    # 应用过滤器
    if filters:
        if filters.get("title"):
            query = query.where(Item.title.contains(filters["title"]))
    
    # 应用搜索
    if search:
        query = query.where(Item.title.contains(search) | Item.description.contains(search))
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()
    
    # 应用分页
    skip = (page - 1) * limit
    query = query.offset(skip).limit(limit)
    
    # 应用排序
    if sort:
        for field, direction in sort.items():
            if hasattr(Item, field):
                if direction.lower() == "desc":
                    query = query.order_by(getattr(Item, field).desc())
                else:
                    query = query.order_by(getattr(Item, field))
    
    items = session.exec(query).all()
    
    # 转换为字典格式
    items_data = [
        {
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "owner_id": str(item.owner_id)
        }
        for item in items
    ]
    
    return create_unified_pagination_response(
        data=items_data,
        total=total_count,
        page=page,
        limit=limit,
        message="项目列表查询成功",
        request_id=request_id,
        duration=(time.time() - start_time) * 1000
    ) 