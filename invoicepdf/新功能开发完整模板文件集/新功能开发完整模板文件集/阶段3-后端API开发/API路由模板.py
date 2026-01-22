"""
{业务模块} API路由
创建时间：{创建时间}
创建人：{创建人}
描述：{业务模块}相关的API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
import logging

from app.models_{业务模块} import (
    {实体名}, {实体名}Create, {实体名}Update, {实体名}Public, {实体名}ListResponse
)
from app.api.deps import get_current_user, get_db
from app.models import User
from app.core.config import settings

# 创建日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

# =============================================
# 查询接口
# =============================================

@router.get(
    "/{业务模块}", 
    response_model=List[{实体名}Public],
    summary="获取{业务模块}列表",
    description="分页获取{业务模块}列表，支持搜索和过滤"
)
def get_{业务模块}_list(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="限制记录数"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取{业务模块}列表"""
    try:
        # 构建查询语句
        statement = select({实体名})
        
        # 添加过滤条件
        if is_active is not None:
            statement = statement.where({实体名}.is_active == is_active)
        
        # 添加搜索条件
        if search:
            statement = statement.where(
                {实体名}.{字段2}.ilike(f"%{search}%") |
                {实体名}.{字段1}.ilike(f"%{search}%")
            )
        
        # 添加排序
        statement = statement.order_by(
            {实体名}.{字段4}.desc(),
            {实体名}.{字段2}.asc()
        )
        
        # 添加分页
        statement = statement.offset(skip).limit(limit)
        
        # 执行查询
        items = db.exec(statement).all()
        
        logger.info(f"用户 {current_user.email} 查询了 {len(items)} 条{业务模块}记录")
        
        return items
        
    except Exception as e:
        logger.error(f"查询{业务模块}列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询失败"
        )

@router.get(
    "/{业务模块}/count",
    response_model=dict,
    summary="获取{业务模块}总数",
    description="获取{业务模块}的总记录数"
)
def get_{业务模块}_count(
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取{业务模块}总数"""
    try:
        statement = select(func.count({实体名}.id))
        
        if is_active is not None:
            statement = statement.where({实体名}.is_active == is_active)
        
        count = db.exec(statement).first()
        
        return {"count": count or 0}
        
    except Exception as e:
        logger.error(f"查询{业务模块}总数失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询失败"
        )

@router.get(
    "/{业务模块}/{item_id}",
    response_model={实体名}Public,
    summary="获取单个{业务模块}",
    description="根据ID获取单个{业务模块}的详细信息"
)
def get_{业务模块}_by_id(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个{业务模块}"""
    try:
        item = db.get({实体名}, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="{业务模块}不存在"
            )
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询{业务模块}详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询失败"
        )

# =============================================
# 创建接口
# =============================================

@router.post(
    "/{业务模块}",
    response_model={实体名}Public,
    status_code=status.HTTP_201_CREATED,
    summary="创建{业务模块}",
    description="创建新的{业务模块}记录"
)
def create_{业务模块}(
    item: {实体名}Create,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建{业务模块}"""
    try:
        # 检查{字段1}是否已存在
        existing = db.exec(
            select({实体名}).where({实体名}.{字段1} == item.{字段1})
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="{字段1}已存在"
            )
        
        # 创建新记录
        db_item = {实体名}.from_orm(item)
        db_item.created_by = current_user.id
        db_item.updated_by = current_user.id
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        logger.info(f"用户 {current_user.email} 创建了{业务模块}: {item.{字段1}}")
        
        return db_item
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建{业务模块}失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建失败"
        )

# =============================================
# 更新接口
# =============================================

@router.put(
    "/{业务模块}/{item_id}",
    response_model={实体名}Public,
    summary="更新{业务模块}",
    description="更新指定{业务模块}的信息"
)
def update_{业务模块}(
    item_id: str,
    item_update: {实体名}Update,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新{业务模块}"""
    try:
        # 查找记录
        db_item = db.get({实体名}, item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="{业务模块}不存在"
            )
        
        # 检查{字段1}是否重复（如果更新了{字段1}）
        if item_update.{字段1} and item_update.{字段1} != db_item.{字段1}:
            existing = db.exec(
                select({实体名}).where({实体名}.{字段1} == item_update.{字段1})
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="{字段1}已存在"
                )
        
        # 更新字段
        update_data = item_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        # 更新审计字段
        db_item.updated_by = current_user.id
        db_item.updated_at = datetime.utcnow()
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        logger.info(f"用户 {current_user.email} 更新了{业务模块}: {db_item.{字段1}}")
        
        return db_item
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新{业务模块}失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败"
        )

# =============================================
# 删除接口
# =============================================

@router.delete(
    "/{业务模块}/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除{业务模块}",
    description="删除指定的{业务模块}记录"
)
def delete_{业务模块}(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除{业务模块}"""
    try:
        # 查找记录
        db_item = db.get({实体名}, item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="{业务模块}不存在"
            )
        
        # 检查是否可以删除（如果有业务逻辑限制）
        # if db_item.has_related_data:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="该{业务模块}有关联数据，无法删除"
        #     )
        
        # 删除记录
        db.delete(db_item)
        db.commit()
        
        logger.info(f"用户 {current_user.email} 删除了{业务模块}: {db_item.{字段1}}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除{业务模块}失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除失败"
        )

# =============================================
# 批量操作接口（可选）
# =============================================

@router.post(
    "/{业务模块}/batch-delete",
    summary="批量删除{业务模块}",
    description="批量删除多个{业务模块}记录"
)
def batch_delete_{业务模块}(
    item_ids: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量删除{业务模块}"""
    try:
        if not item_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请选择要删除的记录"
            )
        
        # 查找记录
        items = db.exec(
            select({实体名}).where({实体名}.id.in_(item_ids))
        ).all()
        
        if len(items) != len(item_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="部分{业务模块}不存在"
            )
        
        # 批量删除
        for item in items:
            db.delete(item)
        
        db.commit()
        
        logger.info(f"用户 {current_user.email} 批量删除了 {len(items)} 条{业务模块}记录")
        
        return {"message": f"成功删除 {len(items)} 条记录"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"批量删除{业务模块}失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量删除失败"
        )
