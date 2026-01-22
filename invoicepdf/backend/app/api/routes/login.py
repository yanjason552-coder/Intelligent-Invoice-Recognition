from datetime import timedelta
from typing import Annotated, Any
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import Message, NewPassword, Token, UserPublic, UnifiedRequest, UnifiedResponse
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
    create_unified_success_response,
    create_unified_error_response,
    validate_unified_request,
    extract_request_data,
    sanitize_request_data
)

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    import traceback
    
    try:
        # 断点调试：记录输入参数
        logger.debug(f"=== 传统登录函数开始 ===")
        logger.debug(f"传统登录 - 用户名/邮箱: {form_data.username}")
        logger.debug(f"传统登录 - 密码长度: {len(form_data.password) if form_data.password else 0}")
        
        # 断点1：验证用户
        logger.debug("传统登录 - 断点1: 开始验证用户")
        try:
            user = crud.authenticate(
                session=session, email=form_data.username, password=form_data.password
            )
        except HTTPException:
            # 重新抛出 HTTP 异常（如数据库连接错误）
            raise
        except Exception as auth_error:
            logger.error(f"传统登录 - 断点1: 用户验证异常: {str(auth_error)}")
            logger.error(f"传统登录 - 断点1: 异常类型: {type(auth_error).__name__}")
            logger.error(f"传统登录 - 断点1: 异常堆栈: {traceback.format_exc()}")
            
            # 检查是否是数据库连接错误
            error_str = str(auth_error).lower()
            if "connection" in error_str or "database" in error_str or "server closed" in error_str:
                raise HTTPException(
                    status_code=503,  # Service Unavailable
                    detail="数据库连接失败，请稍后重试"
                )
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Authentication error: {str(auth_error)}"
                )
        
        logger.debug(f"传统登录 - 断点1: 用户验证结果 - 用户存在: {user is not None}")
        if user:
            logger.debug(f"传统登录 - 断点1: 用户ID: {user.id}")
            logger.debug(f"传统登录 - 断点1: 用户邮箱: {user.email}")
            logger.debug(f"传统登录 - 断点1: 用户是否激活: {user.is_active}")
        
        # 断点2：检查用户是否存在
        logger.debug("传统登录 - 断点2: 检查用户是否存在")
        if not user:
            logger.error("传统登录 - 断点2: 用户不存在或密码错误")
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        
        # 断点3：检查用户是否激活
        logger.debug("传统登录 - 断点3: 检查用户是否激活")
        if not user.is_active:
            logger.error("传统登录 - 断点3: 用户未激活")
            raise HTTPException(status_code=400, detail="Inactive user")
        
        # 断点4：生成访问令牌
        logger.debug("传统登录 - 断点4: 生成访问令牌")
        try:
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            logger.debug(f"传统登录 - 断点4: 令牌过期时间: {access_token_expires}")
            
            access_token = security.create_access_token(
                user.id, expires_delta=access_token_expires
            )
            logger.debug(f"传统登录 - 断点4: 生成的访问令牌: {access_token[:20]}...")
        except Exception as token_error:
            logger.error(f"传统登录 - 断点4: 生成令牌异常: {str(token_error)}")
            logger.error(f"传统登录 - 断点4: 异常堆栈: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Token generation error: {str(token_error)}"
            )
        
        # 断点5：返回结果
        logger.debug("传统登录 - 断点5: 返回登录结果")
        result = Token(access_token=access_token)
        logger.debug(f"传统登录 - 断点5: 登录成功，用户: {user.email}")
        logger.debug("=== 传统登录函数结束 ===")
        
        return result
        
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        # 捕获所有其他异常
        logger.error(f"传统登录 - 未处理的异常: {str(e)}")
        logger.error(f"传统登录 - 异常类型: {type(e).__name__}")
        logger.error(f"传统登录 - 异常堆栈: {traceback.format_exc()}")
        
        # 检查是否是数据库连接错误
        error_str = str(e).lower()
        if "connection" in error_str or "database" in error_str or "server closed" in error_str:
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail="数据库连接失败，请稍后重试。如果问题持续，请联系管理员。"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"登录失败: {str(e)}"
            )


@router.post("/login/unified", response_model=UnifiedResponse)
async def login_unified(
    request: UnifiedRequest,
    session: SessionDep
) -> dict[str, Any]:
    """
    使用统一对象的登录验证
    """
    # 断点1：函数开始
    logger.debug("=== 统一对象登录函数开始 ===")
    logger.debug(f"断点1: 接收到统一登录请求")
    logger.debug(f"断点1: 请求ID: {request.request_id}")
    logger.debug(f"断点1: 操作类型: {request.action}")
    logger.debug(f"断点1: 模块名称: {request.module}")
    
    start_time = time.time()
    
    try:
        # 断点2：请求数据清理和记录
        logger.debug("断点2: 开始清理和记录请求数据")
        sanitized_request = sanitize_request_data(request.model_dump())
        logger.debug(f"断点2: 清理后的请求数据: {sanitized_request}")
        
        # 断点3：请求验证
        logger.debug("断点3: 开始验证请求格式")
        is_valid, error_message = validate_unified_request(request.model_dump())
        logger.debug(f"断点3: 请求验证结果 - 有效: {is_valid}")
        if not is_valid:
            logger.error(f"断点3: 请求验证失败 - {error_message}")
            return create_unified_error_response(
                message=error_message,
                error_code="INVALID_REQUEST",
                request_id=request.request_id,
                duration=(time.time() - start_time) * 1000
            )
        logger.debug("断点3: 请求验证通过")
        
        # 断点4：检查操作类型
        logger.debug("断点4: 检查操作类型")
        logger.debug(f"断点4: 期望操作类型: login, 实际操作类型: {request.action}")
        if request.action != "login":
            logger.error(f"断点4: 不支持的操作类型: {request.action}")
            return create_unified_error_response(
                message=f"不支持的操作类型: {request.action}",
                error_code="UNSUPPORTED_ACTION",
                request_id=request.request_id,
                duration=(time.time() - start_time) * 1000
            )
        logger.debug("断点4: 操作类型检查通过")
        
        # 断点5：检查模块类型
        logger.debug("断点5: 检查模块类型")
        logger.debug(f"断点5: 期望模块类型: user, 实际模块类型: {request.module}")
        if request.module != "user":
            logger.error(f"断点5: 不支持的模块: {request.module}")
            return create_unified_error_response(
                message=f"不支持的模块: {request.module}",
                error_code="UNSUPPORTED_MODULE",
                request_id=request.request_id,
                duration=(time.time() - start_time) * 1000
            )
        logger.debug("断点5: 模块类型检查通过")
        
        # 断点6：提取登录数据
        logger.debug("断点6: 提取登录数据")
        data = request.data or {}
        email = data.get("email")
        password = data.get("password")
        logger.debug(f"断点6: 提取到的邮箱: {email}")
        logger.debug(f"断点6: 提取到的密码长度: {len(password) if password else 0}")
        
        # 断点7：验证必要字段
        logger.debug("断点7: 验证必要字段")
        if not email:
            logger.error("断点7: 邮箱字段为空")
            return create_unified_error_response(
                message="邮箱不能为空",
                error_code="MISSING_EMAIL",
                request_id=request.request_id,
                duration=(time.time() - start_time) * 1000
            )
        logger.debug("断点7: 邮箱字段验证通过")
        
        if not password:
            logger.error("断点7: 密码字段为空")
            return create_unified_error_response(
                message="密码不能为空",
                error_code="MISSING_PASSWORD",
                request_id=request.request_id,
                duration=(time.time() - start_time) * 1000
            )
        logger.debug("断点7: 密码字段验证通过")
        
        # 断点8：用户验证
        logger.debug("断点8: 开始用户验证")
        logger.debug(f"断点8: 验证邮箱: {email}")
        user = crud.authenticate(session=session, email=email, password=password)
        logger.debug(f"断点8: 用户验证结果 - 用户存在: {user is not None}")
        
        if not user:
            logger.error(f"断点8: 用户验证失败 - 邮箱或密码错误: {email}")
            return create_unified_error_response(
                message="邮箱或密码错误",
                error_code="INVALID_CREDENTIALS",
                request_id=request.request_id,
                duration=(time.time() - start_time) * 1000
            )
        
        logger.debug(f"断点8: 用户验证成功")
        logger.debug(f"断点8: 用户ID: {user.id}")
        logger.debug(f"断点8: 用户邮箱: {user.email}")
        logger.debug(f"断点8: 用户是否激活: {user.is_active}")
        logger.debug(f"断点8: 用户是否超级用户: {user.is_superuser}")
        
        # 断点9：检查用户状态
        logger.debug("断点9: 检查用户状态")
        if not user.is_active:
            logger.error(f"断点9: 用户未激活: {email}")
            return create_unified_error_response(
                message="用户未激活",
                error_code="USER_INACTIVE",
                request_id=request.request_id,
                duration=(time.time() - start_time) * 1000
            )
        logger.debug("断点9: 用户状态检查通过")
        
        # 断点10：生成访问令牌
        logger.debug("断点10: 开始生成访问令牌")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        logger.debug(f"断点10: 令牌过期时间: {access_token_expires}")
        
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        logger.debug(f"断点10: 生成的访问令牌: {access_token[:20]}...")
        
        # 断点11：构建响应数据
        logger.debug("断点11: 构建响应数据")
        response_data = {
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
        logger.debug(f"断点11: 响应数据构建完成")
        logger.debug(f"断点11: 用户信息: {response_data['user']}")
        
        # 断点12：返回成功响应
        logger.debug("断点12: 准备返回成功响应")
        duration = (time.time() - start_time) * 1000
        logger.debug(f"断点12: 处理耗时: {duration:.2f}ms")
        
        result = create_unified_success_response(
            data=response_data,
            message="登录成功",
            request_id=request.request_id,
            duration=duration
        )
        
        logger.debug(f"断点12: 登录成功，用户: {email}")
        logger.debug("=== 统一对象登录函数结束 ===")
        
        return result
        
    except Exception as e:
        # 断点13：异常处理
        logger.error(f"断点13: 登录异常: {str(e)}")
        logger.error(f"断点13: 异常类型: {type(e).__name__}")
        import traceback
        logger.error(f"断点13: 异常堆栈: {traceback.format_exc()}")
        
        return create_unified_error_response(
            message=f"登录失败: {str(e)}",
            error_code="LOGIN_FAILED",
            request_id=request.request_id,
            duration=(time.time() - start_time) * 1000
        )


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(email: str, session: SessionDep) -> Message:
    """
    Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    send_email(
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Password recovery email sent")


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )
