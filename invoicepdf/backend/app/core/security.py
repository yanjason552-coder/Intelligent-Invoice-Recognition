from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码 - 使用更兼容的方法
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.debug(f"=== 密码验证开始 ===")
        logger.debug(f"明文密码: {plain_password}")
        logger.debug(f"哈希密码: {hashed_password}")
        
        # 限制密码长度
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password[:72]
        
        # 尝试使用bcrypt直接验证
        import bcrypt
        result = bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
        
        logger.debug(f"密码验证结果: {result}")
        return result
    except Exception as e:
        logger.error(f"直接bcrypt验证失败: {e}")
        # 回退到passlib
        try:
            result = pwd_context.verify(plain_password, hashed_password)
            logger.debug(f"passlib验证结果: {result}")
            return result
        except Exception as e2:
            logger.error(f"passlib验证也失败: {e2}")
            return False


def get_password_hash(password: str) -> str:
    # 限制密码长度以避免bcrypt的72字节限制
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)
