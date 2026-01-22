"""
Feature 相关的工具函数
"""

from typing import List, Optional
from sqlmodel import Session, select
from app.models import Feature, FeatureD


def get_feature_details(session: Session, feature_id: str) -> List[FeatureD]:
    """
    获取 Feature 关联的 FeatureD 列表
    
    Args:
        session: 数据库会话
        feature_id: Feature ID
        
    Returns:
        FeatureD 列表
    """
    details = session.exec(
        select(FeatureD).where(FeatureD.featureId == feature_id)
    ).all()
    return details


def get_feature_with_details(session: Session, feature_id: str) -> Optional[dict]:
    """
    获取 Feature 及其关联的 FeatureD 列表
    
    Args:
        session: 数据库会话
        feature_id: Feature ID
        
    Returns:
        包含 Feature 和 FeatureD 列表的字典
    """
    # 获取 Feature
    feature = session.get(Feature, feature_id)
    if not feature:
        return None
    
    # 获取关联的 FeatureD 列表
    details = get_feature_details(session, feature_id)
    
    # 构建返回数据
    result = feature.model_dump()
    result["featureDList"] = [detail.model_dump() for detail in details]
    
    return result


def create_feature_with_details(
    session: Session, 
    feature_data: dict, 
    details_data: List[dict]
) -> dict:
    """
    创建 Feature 及其关联的 FeatureD 列表
    
    Args:
        session: 数据库会话
        feature_data: Feature 数据
        details_data: FeatureD 数据列表
        
    Returns:
        创建的 Feature 和 FeatureD 列表
    """
    # 创建 Feature
    feature = Feature(**feature_data)
    session.add(feature)
    session.commit()
    session.refresh(feature)
    
    # 创建 FeatureD 列表
    created_details = []
    for detail_data in details_data:
        detail_data["featureId"] = feature.featureId
        detail = FeatureD(**detail_data)
        session.add(detail)
        created_details.append(detail)
    
    session.commit()
    
    # 返回结果
    result = feature.model_dump()
    result["featureDList"] = [detail.model_dump() for detail in created_details]
    
    return result


def update_feature_with_details(
    session: Session,
    feature_id: str,
    feature_data: dict,
    details_data: List[dict]
) -> Optional[dict]:
    """
    更新 Feature 及其关联的 FeatureD 列表
    
    Args:
        session: 数据库会话
        feature_id: Feature ID
        feature_data: Feature 更新数据
        details_data: FeatureD 更新数据列表
        
    Returns:
        更新后的 Feature 和 FeatureD 列表
    """
    # 获取 Feature
    feature = session.get(Feature, feature_id)
    if not feature:
        return None
    
    # 更新 Feature
    for key, value in feature_data.items():
        if hasattr(feature, key):
            setattr(feature, key, value)
    
    # 删除现有的 FeatureD 记录
    existing_details = session.exec(
        select(FeatureD).where(FeatureD.featureId == feature_id)
    ).all()
    
    for detail in existing_details:
        session.delete(detail)
    
    # 创建新的 FeatureD 记录
    created_details = []
    for detail_data in details_data:
        detail_data["featureId"] = feature_id
        detail = FeatureD(**detail_data)
        session.add(detail)
        created_details.append(detail)
    
    session.commit()
    session.refresh(feature)
    
    # 返回结果
    result = feature.model_dump()
    result["featureDList"] = [detail.model_dump() for detail in created_details]
    
    return result


def delete_feature_with_details(session: Session, feature_id: str) -> bool:
    """
    删除 Feature 及其关联的 FeatureD 列表
    
    Args:
        session: 数据库会话
        feature_id: Feature ID
        
    Returns:
        是否删除成功
    """
    # 获取 Feature
    feature = session.get(Feature, feature_id)
    if not feature:
        return False
    
    # 删除关联的 FeatureD 记录
    details = session.exec(
        select(FeatureD).where(FeatureD.featureId == feature_id)
    ).all()
    
    for detail in details:
        session.delete(detail)
    
    # 删除 Feature
    session.delete(feature)
    session.commit()
    
    return True 