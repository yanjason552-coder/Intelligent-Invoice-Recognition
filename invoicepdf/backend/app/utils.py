import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import emails  # type: ignore
import jwt
from jinja2 import Template
from jwt.exceptions import InvalidTokenError

from app.core import security
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (
        Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    assert settings.emails_enabled, "no provided configuration for email variables"
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, smtp=smtp_options)
    logger.info(f"send email result: {response}")


def generate_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None


# 统一的API响应工具函数
def create_success_response(data: Any = None, message: str = "操作成功") -> dict[str, Any]:
    """创建成功响应"""
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }


def create_error_response(message: str, error_code: str = "UNKNOWN_ERROR") -> dict[str, Any]:
    """创建错误响应"""
    return {
        "success": False,
        "message": message,
        "error_code": error_code,
        "timestamp": datetime.now().isoformat()
    }


def create_paginated_response(
    data: list[Any], 
    count: int, 
    page: int = 1, 
    limit: int = 100,
    message: str = "查询成功"
) -> dict[str, Any]:
    """创建分页响应"""
    total_pages = (count + limit - 1) // limit if limit > 0 else 1
    
    return {
        "success": True,
        "data": data,
        "count": count,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }


# 统一的请求处理工具函数
def parse_request_data(request_data: dict[str, Any]) -> dict[str, Any]:
    """解析统一请求数据"""
    return {
        "data": request_data.get("data"),
        "params": request_data.get("params", {}),
        "filters": request_data.get("filters", {}),
        "sort": request_data.get("sort", {}),
        "timestamp": request_data.get("timestamp")
    }


def parse_paginated_request(request_data: dict[str, Any]) -> dict[str, Any]:
    """解析分页请求数据"""
    pagination = request_data.get("pagination", {})
    return {
        "page": pagination.get("page", 1),
        "limit": pagination.get("limit", 20),
        "filters": pagination.get("filters", {}),
        "sort": pagination.get("sort", {}),
        "search": pagination.get("search"),
        "timestamp": pagination.get("timestamp")
    }


def parse_crud_request(request_data: dict[str, Any]) -> dict[str, Any]:
    """解析CRUD请求数据"""
    return {
        "action": request_data.get("action"),
        "data": request_data.get("data"),
        "id": request_data.get("id"),
        "filters": request_data.get("filters", {}),
        "pagination": parse_paginated_request(request_data) if request_data.get("pagination") else None,
        "timestamp": request_data.get("timestamp")
    }


def validate_request_timestamp(timestamp: str | None, max_age_seconds: int = 300) -> bool:
    """验证请求时间戳（防止重放攻击）"""
    if not timestamp:
        return True  # 允许没有时间戳的请求
    
    try:
        request_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        current_time = datetime.now(request_time.tzinfo)
        time_diff = abs((current_time - request_time).total_seconds())
        return time_diff <= max_age_seconds
    except Exception:
        return False


def sanitize_request_data(data: dict[str, Any]) -> dict[str, Any]:
    """清理请求数据（移除敏感信息）"""
    sensitive_fields = ["password", "token", "secret", "key"]
    sanitized = data.copy()
    
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = "***"
    
    return sanitized


# 统一对象处理工具函数
def create_unified_response(
    success: bool = True,
    data: Any = None,
    message: str | None = None,
    error_code: str | None = None,
    code: int = 200,
    pagination: dict[str, Any] | None = None,
    request_id: str | None = None,
    duration: float | None = None,
    debug: dict[str, Any] | None = None
) -> dict[str, Any]:
    """创建统一的API响应对象"""
    from app.models import UnifiedResponse
    
    response = UnifiedResponse(
        success=success,
        code=code,
        data=data,
        message=message,
        error_code=error_code,
        pagination=pagination,
        timestamp=datetime.now().isoformat(),
        request_id=request_id,
        duration=duration,
        debug=debug
    )
    
    return response.model_dump(exclude_none=True)


def create_unified_success_response(
    data: Any = None,
    message: str = "操作成功",
    pagination: dict[str, Any] | None = None,
    request_id: str | None = None,
    duration: float | None = None
) -> dict[str, Any]:
    """创建统一的成功响应"""
    return create_unified_response(
        success=True,
        data=data,
        message=message,
        pagination=pagination,
        request_id=request_id,
        duration=duration
    )


def create_unified_error_response(
    message: str,
    error_code: str = "UNKNOWN_ERROR",
    code: int = 400,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
    duration: float | None = None
) -> dict[str, Any]:
    """创建统一的错误响应"""
    debug = {"details": details} if details else None
    
    return create_unified_response(
        success=False,
        message=message,
        error_code=error_code,
        code=code,
        request_id=request_id,
        duration=duration,
        debug=debug
    )


def create_unified_pagination_response(
    data: list[Any],
    total: int,
    page: int = 1,
    limit: int = 20,
    message: str = "查询成功",
    request_id: str | None = None,
    duration: float | None = None
) -> dict[str, Any]:
    """创建统一的分页响应"""
    from app.models import PaginationInfo
    
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    
    pagination_info = PaginationInfo(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )
    
    return create_unified_response(
        success=True,
        data=data,
        message=message,
        pagination=pagination_info.model_dump(),
        request_id=request_id,
        duration=duration
    )


def parse_unified_request(request_data: dict[str, Any]) -> dict[str, Any]:
    """解析统一请求对象"""
    from app.models import UnifiedRequest
    
    # 验证必要字段
    if "action" not in request_data:
        raise ValueError("缺少必要字段: action")
    if "module" not in request_data:
        raise ValueError("缺少必要字段: module")
    
    # 验证时间戳
    timestamp = request_data.get("timestamp")
    if timestamp and not validate_request_timestamp(timestamp):
        raise ValueError("请求时间戳无效")
    
    # 生成请求ID（如果没有提供）
    if "request_id" not in request_data:
        import uuid
        request_data["request_id"] = str(uuid.uuid4())
    
    return request_data


def validate_unified_request(request: dict[str, Any]) -> tuple[bool, str | None]:
    """验证统一请求对象"""
    try:
        # 检查必要字段
        if not request.get("action"):
            return False, "缺少操作类型(action)"
        if not request.get("module"):
            return False, "缺少模块名称(module)"
        
        # 检查操作类型
        valid_actions = ["login", "register", "create", "read", "update", "delete", "list"]
        if request["action"] not in valid_actions:
            return False, f"不支持的操作类型: {request['action']}"
        
        # 检查时间戳
        timestamp = request.get("timestamp")
        if timestamp and not validate_request_timestamp(timestamp):
            return False, "请求时间戳无效"
        
        return True, None
    except Exception as e:
        return False, f"请求验证失败: {str(e)}"


def extract_request_data(request: dict[str, Any]) -> dict[str, Any]:
    """从统一请求对象中提取数据"""
    return {
        "action": request.get("action"),
        "module": request.get("module"),
        "data": request.get("data", {}),
        "params": request.get("params", {}),
        "filters": request.get("filters", {}),
        "sort": request.get("sort", {}),
        "page": request.get("page", 1),
        "limit": request.get("limit", 20),
        "search": request.get("search"),
        "request_id": request.get("request_id"),
        "client_info": request.get("client_info", {})
    }


# 服务器时间工具函数
def get_server_datetime(timezone_name: str = "Asia/Shanghai") -> datetime:
    """
    获取服务器当前日期时间（指定时区）
    
    Args:
        timezone_name: 时区名称，默认为"Asia/Shanghai"
    
    Returns:
        datetime: 带时区信息的当前日期时间
    """
    try:
        import pytz
        tz = pytz.timezone(timezone_name)
        return datetime.now(tz)
    except ImportError:
        # 如果没有安装pytz，使用系统默认时区
        logger.warning("pytz未安装，使用系统默认时区")
        return datetime.now()


def get_server_datetime_utc() -> datetime:
    """
    获取服务器当前日期时间（UTC时区）
    
    Returns:
        datetime: UTC时区的当前日期时间
    """
    return datetime.now(timezone.utc)


def get_server_datetime_iso() -> str:
    """
    获取服务器当前日期时间的ISO格式字符串（包含时区信息）
    
    Returns:
        str: ISO格式的日期时间字符串，如"2024-01-01T12:00:00+08:00"
    """
    return get_server_datetime().isoformat()


def get_server_datetime_utc_iso() -> str:
    """
    获取服务器当前日期时间的UTC ISO格式字符串
    
    Returns:
        str: UTC ISO格式的日期时间字符串，如"2024-01-01T04:00:00+00:00"
    """
    return get_server_datetime_utc().isoformat()


def get_server_date_string(format_str: str = "%Y-%m-%d") -> str:
    """
    获取服务器当前日期字符串
    
    Args:
        format_str: 日期格式字符串，默认为"%Y-%m-%d"
    
    Returns:
        str: 格式化的日期字符串
    """
    return get_server_datetime().strftime(format_str)


def get_server_time_string(format_str: str = "%H:%M:%S") -> str:
    """
    获取服务器当前时间字符串
    
    Args:
        format_str: 时间格式字符串，默认为"%H:%M:%S"
    
    Returns:
        str: 格式化的时间字符串
    """
    return get_server_datetime().strftime(format_str)


def get_server_datetime_string(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取服务器当前日期时间字符串
    
    Args:
        format_str: 日期时间格式字符串，默认为"%Y-%m-%d %H:%M:%S"
    
    Returns:
        str: 格式化的日期时间字符串
    """
    return get_server_datetime().strftime(format_str)


def get_server_timezone_info() -> dict[str, Any]:
    """
    获取服务器时区信息
    
    Returns:
        dict: 包含时区信息的字典
    """
    try:
        import pytz
        current_tz = pytz.timezone("Asia/Shanghai")
        now = datetime.now(current_tz)
        
        return {
            "timezone_name": "Asia/Shanghai",
            "timezone_offset": now.strftime("%z"),
            "timezone_offset_hours": int(now.strftime("%z")[:3]),
            "is_dst": bool(now.dst()),
            "current_datetime": now.isoformat(),
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M:%S")
        }
    except ImportError:
        # 如果没有安装pytz，返回基本时区信息
        now = datetime.now()
        return {
            "timezone_name": "system_default",
            "timezone_offset": "+00:00",
            "timezone_offset_hours": 0,
            "is_dst": False,
            "current_datetime": now.isoformat(),
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M:%S")
        }


def format_datetime_with_timezone(dt: datetime, timezone_name: str = "Asia/Shanghai") -> str:
    """
    格式化日期时间为指定时区的字符串
    
    Args:
        dt: 日期时间对象
        timezone_name: 目标时区名称
    
    Returns:
        str: 格式化后的日期时间字符串
    """
    try:
        import pytz
        target_tz = pytz.timezone(timezone_name)
        if dt.tzinfo is None:
            # 如果输入的时间没有时区信息，假设为UTC
            dt = dt.replace(tzinfo=timezone.utc)
        localized_dt = dt.astimezone(target_tz)
        return localized_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    except ImportError:
        # 如果没有安装pytz，返回原始格式
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_timestamp_milliseconds() -> int:
    """
    获取当前时间戳（毫秒）
    
    Returns:
        int: 毫秒级时间戳
    """
    return int(datetime.now().timestamp() * 1000)


def get_timestamp_seconds() -> int:
    """
    获取当前时间戳（秒）
    
    Returns:
        int: 秒级时间戳
    """
    return int(datetime.now().timestamp())
