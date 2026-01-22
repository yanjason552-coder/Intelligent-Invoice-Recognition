"""
统一的API路由示例
展示如何使用统一的传入参数和返回参数格式
"""

from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from app.api.deps import SessionDep, CurrentUser
from app.models import (
    ApiRequest, ApiResponse, PaginatedRequest, PaginatedResponse,
    CrudRequest, UserRequest, ItemRequest
)
from app.utils import (
    create_success_response, create_error_response, create_paginated_response,
    parse_request_data, parse_paginated_request, parse_crud_request,
    validate_request_timestamp, sanitize_request_data
)
from app import crud
from app.models import User, Item, UserCreate, ItemCreate

router = APIRouter(prefix="/unified", tags=["unified"])


@router.post("/users", response_model=ApiResponse)
async def unified_user_operations(
    request: UserRequest,
    session: SessionDep,
    current_user: CurrentUser | None = None
) -> ApiResponse:
    """
    统一的用户操作API
    支持：login, register, update, delete, list
    """
    try:
        # 验证时间戳
        if not validate_request_timestamp(request.timestamp):
            return create_error_response("请求时间戳无效", "INVALID_TIMESTAMP")
        
        # 记录请求（清理敏感信息）
        sanitized_request = sanitize_request_data(request.model_dump())
        print(f"用户操作请求: {sanitized_request}")
        
        action = request.action.lower()
        
        if action == "login":
            return await _handle_user_login(request, session)
        elif action == "register":
            return await _handle_user_register(request, session)
        elif action == "update":
            if not current_user:
                return create_error_response("需要登录", "AUTHENTICATION_REQUIRED")
            return await _handle_user_update(request, session, current_user)
        elif action == "delete":
            if not current_user:
                return create_error_response("需要登录", "AUTHENTICATION_REQUIRED")
            return await _handle_user_delete(request, session, current_user)
        elif action == "list":
            if not current_user or not current_user.is_superuser:
                return create_error_response("权限不足", "INSUFFICIENT_PERMISSIONS")
            return await _handle_user_list(request, session)
        else:
            return create_error_response(f"不支持的操作: {action}", "UNSUPPORTED_ACTION")
            
    except Exception as e:
        return create_error_response(f"操作失败: {str(e)}", "OPERATION_FAILED")


@router.post("/items", response_model=ApiResponse)
async def unified_item_operations(
    request: ItemRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> ApiResponse:
    """
    统一的项目操作API
    支持：create, read, update, delete, list
    """
    try:
        # 验证时间戳
        if not validate_request_timestamp(request.timestamp):
            return create_error_response("请求时间戳无效", "INVALID_TIMESTAMP")
        
        # 记录请求
        print(f"项目操作请求: {request.model_dump()}")
        
        action = request.action.lower()
        
        if action == "create":
            return await _handle_item_create(request, session, current_user)
        elif action == "read":
            return await _handle_item_read(request, session, current_user)
        elif action == "update":
            return await _handle_item_update(request, session, current_user)
        elif action == "delete":
            return await _handle_item_delete(request, session, current_user)
        elif action == "list":
            return await _handle_item_list(request, session, current_user)
        else:
            return create_error_response(f"不支持的操作: {action}", "UNSUPPORTED_ACTION")
            
    except Exception as e:
        return create_error_response(f"操作失败: {str(e)}", "OPERATION_FAILED")


@router.post("/crud/{model_name}", response_model=ApiResponse)
async def unified_crud_operations(
    model_name: str,
    request: CrudRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> ApiResponse:
    """
    通用的CRUD操作API
    支持任意模型的增删改查
    """
    try:
        # 验证时间戳
        if not validate_request_timestamp(request.timestamp):
            return create_error_response("请求时间戳无效", "INVALID_TIMESTAMP")
        
        # 根据模型名称选择处理函数
        model_handlers = {
            "users": _handle_user_crud,
            "items": _handle_item_crud,
        }
        
        if model_name not in model_handlers:
            return create_error_response(f"不支持的模型: {model_name}", "UNSUPPORTED_MODEL")
        
        handler = model_handlers[model_name]
        return await handler(request, session, current_user)
        
    except Exception as e:
        return create_error_response(f"操作失败: {str(e)}", "OPERATION_FAILED")


# 用户操作处理函数
async def _handle_user_login(request: UserRequest, session: Session) -> ApiResponse:
    """处理用户登录"""
    if not request.email or not request.password:
        return create_error_response("邮箱和密码不能为空", "MISSING_CREDENTIALS")
    
    user = crud.authenticate(session=session, email=request.email, password=request.password)
    if not user:
        return create_error_response("邮箱或密码错误", "INVALID_CREDENTIALS")
    
    if not user.is_active:
        return create_error_response("用户未激活", "USER_INACTIVE")
    
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
    
    return create_success_response(data=token_data, message="登录成功")


async def _handle_user_register(request: UserRequest, session: Session) -> ApiResponse:
    """处理用户注册"""
    if not request.email or not request.password:
        return create_error_response("邮箱和密码不能为空", "MISSING_CREDENTIALS")
    
    # 检查用户是否已存在
    existing_user = crud.get_user_by_email(session=session, email=request.email)
    if existing_user:
        return create_error_response("用户已存在", "USER_EXISTS")
    
    # 创建新用户
    user_create = UserCreate(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )
    
    user = crud.create_user(session=session, user_create=user_create)
    
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser
    }
    
    return create_success_response(data=user_data, message="用户注册成功")


async def _handle_user_update(request: UserRequest, session: Session, current_user: CurrentUser) -> ApiResponse:
    """处理用户更新"""
    # 这里可以实现用户信息更新逻辑
    return create_success_response(data={"user_id": str(current_user.id)}, message="用户信息更新成功")


async def _handle_user_delete(request: UserRequest, session: Session, current_user: CurrentUser) -> ApiResponse:
    """处理用户删除"""
    # 这里可以实现用户删除逻辑
    return create_success_response(message="用户删除成功")


async def _handle_user_list(request: UserRequest, session: Session) -> ApiResponse:
    """处理用户列表查询"""
    pagination = parse_paginated_request(request.model_dump())
    
    # 构建查询
    query = select(User)
    
    # 应用过滤器
    if request.filters:
        if request.filters.get("is_active") is not None:
            query = query.where(User.is_active == request.filters["is_active"])
        if request.filters.get("is_superuser") is not None:
            query = query.where(User.is_superuser == request.filters["is_superuser"])
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()
    
    # 应用分页
    skip = (pagination["page"] - 1) * pagination["limit"]
    query = query.offset(skip).limit(pagination["limit"])
    
    # 应用排序
    if pagination["sort"]:
        for field, direction in pagination["sort"].items():
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
    
    return create_paginated_response(
        data=users_data,
        count=total_count,
        page=pagination["page"],
        limit=pagination["limit"],
        message="用户列表查询成功"
    )


# 项目操作处理函数
async def _handle_item_create(request: ItemRequest, session: Session, current_user: CurrentUser) -> ApiResponse:
    """处理项目创建"""
    if not request.title:
        return create_error_response("标题不能为空", "MISSING_TITLE")
    
    item_create = ItemCreate(
        title=request.title,
        description=request.description
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
    
    return create_success_response(data=item_data, message="项目创建成功")


async def _handle_item_read(request: ItemRequest, session: Session, current_user: CurrentUser) -> ApiResponse:
    """处理项目读取"""
    if not request.id:
        return create_error_response("项目ID不能为空", "MISSING_ITEM_ID")
    
    item = session.get(Item, request.id)
    if not item:
        return create_error_response("项目不存在", "ITEM_NOT_FOUND")
    
    if not current_user.is_superuser and item.owner_id != current_user.id:
        return create_error_response("权限不足", "INSUFFICIENT_PERMISSIONS")
    
    item_data = {
        "id": str(item.id),
        "title": item.title,
        "description": item.description,
        "owner_id": str(item.owner_id)
    }
    
    return create_success_response(data=item_data, message="项目查询成功")


async def _handle_item_update(request: ItemRequest, session: Session, current_user: CurrentUser) -> ApiResponse:
    """处理项目更新"""
    if not request.id:
        return create_error_response("项目ID不能为空", "MISSING_ITEM_ID")
    
    item = session.get(Item, request.id)
    if not item:
        return create_error_response("项目不存在", "ITEM_NOT_FOUND")
    
    if not current_user.is_superuser and item.owner_id != current_user.id:
        return create_error_response("权限不足", "INSUFFICIENT_PERMISSIONS")
    
    # 更新项目信息
    if request.title is not None:
        item.title = request.title
    if request.description is not None:
        item.description = request.description
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    item_data = {
        "id": str(item.id),
        "title": item.title,
        "description": item.description,
        "owner_id": str(item.owner_id)
    }
    
    return create_success_response(data=item_data, message="项目更新成功")


async def _handle_item_delete(request: ItemRequest, session: Session, current_user: CurrentUser) -> ApiResponse:
    """处理项目删除"""
    if not request.id:
        return create_error_response("项目ID不能为空", "MISSING_ITEM_ID")
    
    item = session.get(Item, request.id)
    if not item:
        return create_error_response("项目不存在", "ITEM_NOT_FOUND")
    
    if not current_user.is_superuser and item.owner_id != current_user.id:
        return create_error_response("权限不足", "INSUFFICIENT_PERMISSIONS")
    
    session.delete(item)
    session.commit()
    
    return create_success_response(message="项目删除成功")


async def _handle_item_list(request: ItemRequest, session: Session, current_user: CurrentUser) -> ApiResponse:
    """处理项目列表查询"""
    pagination = parse_paginated_request(request.model_dump())
    
    # 构建查询
    if current_user.is_superuser:
        query = select(Item)
    else:
        query = select(Item).where(Item.owner_id == current_user.id)
    
    # 应用过滤器
    if request.filters:
        if request.filters.get("title"):
            query = query.where(Item.title.contains(request.filters["title"]))
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()
    
    # 应用分页
    skip = (pagination["page"] - 1) * pagination["limit"]
    query = query.offset(skip).limit(pagination["limit"])
    
    # 应用排序
    if pagination["sort"]:
        for field, direction in pagination["sort"].items():
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
    
    return create_paginated_response(
        data=items_data,
        count=total_count,
        page=pagination["page"],
        limit=pagination["limit"],
        message="项目列表查询成功"
    )


# 通用CRUD处理函数
async def _handle_user_crud(request: CrudRequest, session: Session, current_user: CurrentUser) -> ApiResponse:
    """处理用户CRUD操作"""
    action = request.action.lower()
    
    if action == "create":
        return await _handle_user_register(UserRequest(**request.model_dump()), session)
    elif action == "read":
        return await _handle_user_read(request, session, current_user)
    elif action == "update":
        return await _handle_user_update(UserRequest(**request.model_dump()), session, current_user)
    elif action == "delete":
        return await _handle_user_delete(UserRequest(**request.model_dump()), session, current_user)
    elif action == "list":
        return await _handle_user_list(UserRequest(**request.model_dump()), session)
    else:
        return create_error_response(f"不支持的操作: {action}", "UNSUPPORTED_ACTION")


async def _handle_item_crud(request: CrudRequest, session: Session, current_user: CurrentUser) -> ApiResponse:
    """处理项目CRUD操作"""
    action = request.action.lower()
    
    if action == "create":
        return await _handle_item_create(ItemRequest(**request.model_dump()), session, current_user)
    elif action == "read":
        return await _handle_item_read(ItemRequest(**request.model_dump()), session, current_user)
    elif action == "update":
        return await _handle_item_update(ItemRequest(**request.model_dump()), session, current_user)
    elif action == "delete":
        return await _handle_item_delete(ItemRequest(**request.model_dump()), session, current_user)
    elif action == "list":
        return await _handle_item_list(ItemRequest(**request.model_dump()), session, current_user)
    else:
        return create_error_response(f"不支持的操作: {action}", "UNSUPPORTED_ACTION")


async def _handle_user_read(request: CrudRequest, session: Session, current_user: CurrentUser) -> ApiResponse:
    """处理用户读取操作"""
    if not request.id:
        return create_error_response("用户ID不能为空", "MISSING_USER_ID")
    
    user = session.get(User, request.id)
    if not user:
        return create_error_response("用户不存在", "USER_NOT_FOUND")
    
    if not current_user.is_superuser and str(user.id) != str(current_user.id):
        return create_error_response("权限不足", "INSUFFICIENT_PERMISSIONS")
    
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser
    }
    
    return create_success_response(data=user_data, message="用户查询成功") 