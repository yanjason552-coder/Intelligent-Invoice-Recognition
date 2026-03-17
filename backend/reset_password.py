#!/usr/bin/env python3
"""
重置用户密码脚本
用法: python reset_password.py <email> <new_password>
"""

import sys
import os
from pathlib import Path

# 添加项目路径到 Python 路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select
from app.core.db import engine
from app.core.security import get_password_hash
from app.models import User


def reset_password(email: str, new_password: str):
    """
    重置用户密码
    
    Args:
        email: 用户邮箱
        new_password: 新密码
    """
    print(f"正在查找用户: {email}")
    
    with Session(engine) as session:
        # 查找用户
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        
        if not user:
            print(f"[错误] 未找到邮箱为 {email} 的用户")
            return False
        
        print(f"[成功] 找到用户: {user.email} (ID: {user.id})")
        print(f"   用户名: {user.full_name or '未设置'}")
        print(f"   是否激活: {user.is_active}")
        print(f"   是否超级用户: {user.is_superuser}")
        
        # 重置密码
        user.hashed_password = get_password_hash(new_password)
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"[成功] 密码已成功重置为: {new_password}")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python reset_password.py <email> <new_password>")
        print("示例: python reset_password.py test@example.com test123456")
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    if len(new_password) < 8:
        print("[错误] 密码长度至少为 8 个字符")
        sys.exit(1)
    
    success = reset_password(email, new_password)
    sys.exit(0 if success else 1)

