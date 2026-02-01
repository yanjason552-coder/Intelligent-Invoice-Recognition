from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session
from sqlalchemy import text

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    使用生成器模式确保会话正确关闭
    添加连接重试机制和更好的错误处理
    """
    import logging
    import time
    from sqlalchemy.exc import OperationalError, DisconnectionError
    
    logger = logging.getLogger(__name__)
    
    max_retries = 2  # 减少重试次数，快速失败
    retry_delay = 0.5  # 秒
    
    session = None
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # 创建会话（pool_pre_ping会自动检查连接有效性，不需要手动测试）
            session = Session(engine, autocommit=False, autoflush=True)
            
            # 连接成功，跳出重试循环
            # 注意：移除了手动连接测试，因为pool_pre_ping已经会自动检查连接
            # 这样可以减少连接占用时间，避免连接池耗尽
            break
            
        except HTTPException:
            raise
        except Exception as e:
            if session:
                try:
                    session.close()
                except:
                    pass
            session = None
            last_error = e
            
            if attempt < max_retries - 1:
                logger.warning(
                    f"创建数据库会话失败（尝试 {attempt + 1}/{max_retries}）: {e}，"
                    f"{retry_delay}秒后重试..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                logger.error(f"创建数据库会话失败（已重试{max_retries}次）: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"数据库连接失败: {str(e)}。请检查数据库服务器是否正常运行。"
                )
    
    if not session:
        error_msg = f"无法创建数据库会话。最后错误: {last_error}" if last_error else "无法创建数据库会话"
        raise HTTPException(
            status_code=503,
            detail=error_msg + "。请检查数据库连接配置和服务器状态。"
        )
    
    try:
        # 生成会话，FastAPI 会在请求完成后自动调用生成器的清理逻辑
        yield session
        
        # 提交事务（如果没有异常）
        session.commit()
    except (OperationalError, DisconnectionError) as db_error:
        # 数据库连接错误，尝试自动重连
        logger.error(f"数据库操作时连接断开: {db_error}", exc_info=True)
        if session:
            try:
                session.rollback()
            except:
                pass
        
        # 尝试自动重连（仅一次）
        try:
            from app.core.db import reconnect_database
            logger.info("尝试自动重连数据库...")
            if reconnect_database():
                logger.info("数据库自动重连成功，请重试请求")
                raise HTTPException(
                    status_code=503,
                    detail="数据库连接已断开并已自动重连，请重试请求"
                )
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"数据库连接在操作过程中断开，自动重连失败: {str(db_error)}。请检查数据库服务器状态或使用 /api/v1/health/db/reconnect 手动重连。"
                )
        except HTTPException:
            raise
        except Exception as reconnect_error:
            logger.error(f"自动重连失败: {reconnect_error}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail=f"数据库连接在操作过程中断开，自动重连失败: {str(db_error)}。请检查数据库服务器状态。"
            )
    except HTTPException:
        # 重新抛出 HTTP 异常，不提交事务
        if session:
            try:
                session.rollback()
            except:
                pass
        raise
    except Exception as e:
        # 回滚事务并记录错误
        logger.error(f"数据库会话错误: {e}", exc_info=True)
        if session:
            try:
                session.rollback()
            except:
                pass
        raise HTTPException(
            status_code=500,
            detail=f"数据库操作失败: {str(e)}"
        )
    finally:
        # 确保会话被关闭
        if session:
            try:
                session.close()
            except:
                pass


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # 解码 JWT token
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
        except (InvalidTokenError, ValidationError) as e:
            logger.warning(f"Token验证失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
        
        # 从数据库获取用户
        try:
            user = session.get(User, token_data.sub)
        except Exception as db_error:
            logger.error(f"数据库查询用户失败: {str(db_error)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"数据库查询失败: {str(db_error)}"
            )
        
        if not user:
            logger.warning(f"用户不存在: {token_data.sub}")
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.is_active:
            logger.warning(f"用户未激活: {token_data.sub}")
            raise HTTPException(status_code=400, detail="Inactive user")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前用户失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取用户信息失败: {str(e)}"
        )


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
