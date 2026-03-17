import uuid
from typing import Any
import logging

from sqlmodel import Session, select, delete

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate, UserCompany, Company

# 设置日志
logger = logging.getLogger(__name__)

def create_user(*, session: Session, user_create: UserCreate) -> User:
    # 提取公司关联信息
    company_ids = user_create.company_ids if hasattr(user_create, 'company_ids') and user_create.company_ids else []
    primary_company_id = user_create.primary_company_id if hasattr(user_create, 'primary_company_id') else None
    
    # 创建用户（不包含公司信息）
    user_data = user_create.model_dump(exclude={'company_ids', 'primary_company_id'}, exclude_unset=True)
    db_obj = User.model_validate(
        user_data, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.flush()  # 先刷新以获取用户ID
    
    # 创建用户公司关联
    if company_ids:
        # 验证主公司ID是否在company_ids中
        if primary_company_id and primary_company_id not in company_ids:
            raise ValueError("主公司ID必须在公司ID列表中")
        
        # 如果没有指定主公司，使用第一个公司作为主公司
        if not primary_company_id and company_ids:
            primary_company_id = company_ids[0]
        
        for company_id in company_ids:
            user_company = UserCompany(
                user_id=db_obj.id,
                company_id=company_id,
                is_primary=(company_id == primary_company_id)
            )
            session.add(user_company)
    
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude={'company_ids', 'primary_company_id'}, exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    
    # 更新公司关联
    if hasattr(user_in, 'company_ids') and user_in.company_ids is not None:
        # 删除旧的关联
        existing_associations = session.exec(
            select(UserCompany).where(UserCompany.user_id == db_user.id)
        ).all()
        for assoc in existing_associations:
            session.delete(assoc)
        session.flush()
        
        # 去重：确保 company_ids 中没有重复值
        unique_company_ids = list(dict.fromkeys(user_in.company_ids))  # 保持顺序的去重
        
        # 创建新的关联
        primary_company_id = user_in.primary_company_id if hasattr(user_in, 'primary_company_id') else None
        
        # 验证主公司ID是否在company_ids中
        if primary_company_id and primary_company_id not in unique_company_ids:
            raise ValueError("主公司ID必须在公司ID列表中")
        
        # 如果没有指定主公司，使用第一个公司作为主公司
        if not primary_company_id and unique_company_ids:
            primary_company_id = unique_company_ids[0]
        
        # 确保只有一个主公司
        for company_id in unique_company_ids:
            user_company = UserCompany(
                user_id=db_user.id,
                company_id=company_id,
                is_primary=(company_id == primary_company_id)
            )
            session.add(user_company)
    
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    logger.debug(f"=== 根据邮箱查找用户 ===")
    logger.debug(f"查找邮箱: {email}")
    
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    
    if session_user:
        logger.debug(f"找到用户: ID={session_user.id}, 邮箱={session_user.email}, 激活状态={session_user.is_active}")
    else:
        logger.debug("未找到用户")
    
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    logger.debug(f"=== 用户认证开始 ===")
    logger.debug(f"认证邮箱: {email}")
    logger.debug(f"密码长度: {len(password) if password else 0}")
    
    # 断点1：根据邮箱查找用户
    logger.debug("断点1: 根据邮箱查找用户")
    db_user = get_user_by_email(session=session, email=email)
    
    if not db_user:
        logger.error("断点1: 用户不存在")
        return None
    
    # 断点2：验证密码 - 这是关键断点位置
    logger.debug("断点2: 验证密码")
    logger.debug(f"输入的明文密码: {password}")
    logger.debug(f"数据库中的哈希密码: {db_user.hashed_password}")
    logger.debug(f"哈希密码长度: {len(db_user.hashed_password) if db_user.hashed_password else 0}")
    
    # 在这里可以设置断点进行调试
    password_valid = verify_password(password, db_user.hashed_password)
    logger.debug(f"断点2: 密码验证结果: {password_valid}")
    
    if not password_valid:
        logger.error("断点2: 密码验证失败")
        logger.error(f"密码验证失败 - 输入密码: {password}")
        logger.error(f"数据库哈希密码: {db_user.hashed_password}")
        return None
    
    logger.debug("断点2: 密码验证成功")
    logger.debug(f"=== 用户认证成功: {db_user.email} ===")
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
