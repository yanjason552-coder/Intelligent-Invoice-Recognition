from datetime import timedelta
from typing import Annotated, Any
import pdb
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import Message, NewPassword, Token, UserPublic
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["login-debug"])


@router.post("/login/access-token-debug")
def login_access_token_debug(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    带断点调试的登录函数
    """
    print("=== 登录函数开始 ===")
    print(f"用户名/邮箱: {form_data.username}")
    print(f"密码长度: {len(form_data.password) if form_data.password else 0}")
    
    # 断点1：检查输入参数
    print("\n断点1: 检查输入参数")
    pdb.set_trace()  # 在这里设置断点
    
    # 断点2：验证用户
    print("\n断点2: 开始验证用户")
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    print(f"用户验证结果: {user is not None}")
    
    pdb.set_trace()  # 在这里设置断点
    
    if user:
        print(f"用户ID: {user.id}")
        print(f"用户邮箱: {user.email}")
        print(f"用户是否激活: {user.is_active}")
    
    # 断点3：检查用户是否存在
    print("\n断点3: 检查用户是否存在")
    if not user:
        print("用户不存在或密码错误")
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # 断点4：检查用户是否激活
    print("\n断点4: 检查用户是否激活")
    if not user.is_active:
        print("用户未激活")
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # 断点5：生成访问令牌
    print("\n断点5: 生成访问令牌")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    print(f"令牌过期时间: {access_token_expires}")
    
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    print(f"生成的访问令牌: {access_token[:20]}...")
    
    # 断点6：返回结果
    print("\n断点6: 返回登录结果")
    result = Token(access_token=access_token)
    print(f"登录成功，用户: {user.email}")
    print("=== 登录函数结束 ===")
    
    return result 