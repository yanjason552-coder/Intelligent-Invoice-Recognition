"""
SurfaceTechnology 实体模型定义

设计说明：
1. SurfaceTechnology 表用于存储表面要求信息
2. 包含表面代码、描述、审批状态等业务字段
3. 使用 SQLModel 进行 ORM 映射
4. 支持审批流程和审计跟踪
"""

from typing import List, Optional, Annotated, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, select
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
# 表面工艺映射表模型
class SurfaceTechnologyD(SQLModel, table=True):
    __tablename__ = "surface_technology_d"
    
    # 物理主键 - GUID
    surfaceTechnologyDId: str = Field(max_length=200, sa_column=Column("surface_technology_d_id", String(200), primary_key=True))
    
    # 表面主键 - GUID (外键关联到 surface_technology 表)
    surfaceId: str = Field(max_length=200, sa_column=Column("surface_id", String(200)))
    
    # 工艺主键 - GUID (外键关联到 operation 表)
    operationId: str = Field(max_length=200, sa_column=Column("operation_id", String(200)))
    
    # 备注
    remark: Optional[str] = Field(default=None, max_length=200, sa_column=Column("remark", String(200)))
    
    # 创建人
    creator: str = Field(max_length=20, sa_column=Column("creator", String(20)))
    
    # 创建日期
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    
    # 最后修改人
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    
    # 最近修改日期
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 批准状态 (N:未批准 Y:已批准)
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    
    # 批准人
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    
    # 批准日期
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))

    @property
    def operationCode(self) -> str:
        """工艺代码"""
        # 这里可以通过查询获取，暂时返回空列表
        return ""
    
    @operationCode.setter
    def operationCode(self, value: str):
        """工艺代码"""
        # 这里可以处理设置逻辑
        pass
    @property
    def operationName(self) -> str:
        """工艺描述"""
        # 这里可以通过查询获取，暂时返回空列表
        return ""
    
    @operationName.setter
    def operationName(self, value: str):
        """工艺描述"""
        # 这里可以处理设置逻辑
        pass

# 表面要求表模型
class SurfaceTechnology(SQLModel, table=True):
    __tablename__ = "surface_technology"
    
    # 物理主键 - GUID
    surfaceTechnologyId: str = Field(max_length=200, sa_column=Column("surface_technology_id", String(200), primary_key=True))
    
    # 表面代码
    surfaceCode: Optional[str] = Field(default=None, max_length=10, sa_column=Column("surface_code", String(10)))
    
    # 表面描述 - HL、No.4、和纹、古铜、黑钛、玫瑰金、抗指纹、精No.8、小米粒
    surfaceDesc: Optional[str] = Field(default=None, max_length=20, sa_column=Column("surface_desc", String(20)))
    
    # 备注
    remark: Optional[str] = Field(default=None, max_length=200, sa_column=Column("remark", String(200)))
    
    # 创建人
    creator: str = Field(max_length=20, sa_column=Column("creator", String(20)))
    
    # 创建日期
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    
    # 最后修改人
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    
    # 最近修改日期
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 批准状态 (N:未批准 Y:已批准 U:批准中 V:失败)
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    
    # 批准人
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    
    # 批准日期
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))
    # 使用 property 装饰器创建子对象数组属性
    @property
    def surfaceTechnologyDList(self) -> List[SurfaceTechnologyD]:
        """获取物料的属性列表"""
        # 这里可以通过查询获取，暂时返回空列表
        return []
    
    @surfaceTechnologyDList.setter
    def surfaceTechnologyDList(self, value: List[SurfaceTechnologyD]):
        """设置物料的属性列表"""
        # 这里可以处理设置逻辑
        pass
# 查询示例函数
def get_surface_technology_by_id(session, surface_technology: SurfaceTechnology):
    """根据ID获取表面要求信息"""
    statement = select(SurfaceTechnology).where(SurfaceTechnology.surfaceTechnologyId == surface_technology.surfaceTechnologyId)
    result = session.exec(statement).first()
    return result

def get_surface_technologies_by_code(session, surface_technology: SurfaceTechnology):
    """根据表面代码获取所有表面要求"""
    statement = select(SurfaceTechnology).where(SurfaceTechnology.surfaceCode == surface_technology.surfaceCode)
    results = session.exec(statement).all()
    return results

def get_surface_technologies_by_desc(session, surface_technology: SurfaceTechnology):
    """根据表面描述获取表面要求"""
    statement = select(SurfaceTechnology).where(SurfaceTechnology.surfaceDesc == surface_technology.surfaceDesc)
    results = session.exec(statement).all()
    return results

def create_surface_technology(session, surface_technology: SurfaceTechnology):
    """创建表面要求
    
    Args:
        session: 数据库会话
        surface_technology: SurfaceTechnology对象，包含表面要求信息
    """
    # 创建表面要求记录
    session.add(surface_technology)
    session.commit()
    session.refresh(surface_technology)
    return surface_technology

def update_surface_technology(session, surface_technology: SurfaceTechnology):
    """更新表面要求
    
    Args:
        session: 数据库会话
        surface_technology: SurfaceTechnology对象，包含更新的表面要求信息
    """
    # 更新表面要求记录
    session.add(surface_technology)
    session.commit()
    session.refresh(surface_technology)
    return surface_technology

# 复杂查询示例
def get_surface_technologies_with_filter(session, surface_technology: SurfaceTechnology):
    """复杂查询：根据SurfaceTechnology对象的字段筛选表面要求
    
    注意：多个where条件会自动使用AND连接
    
    Args:
        session: 数据库会话
        surface_technology: SurfaceTechnology对象，包含查询条件
    """
    statement = select(SurfaceTechnology)
    
    # 使用SurfaceTechnology对象的字段作为查询条件
    # 多个where条件会自动使用AND连接
    if surface_technology.surfaceTechnologyId:
        statement = statement.where(SurfaceTechnology.surfaceTechnologyId == surface_technology.surfaceTechnologyId)
    if surface_technology.surfaceCode:
        statement = statement.where(SurfaceTechnology.surfaceCode == surface_technology.surfaceCode)
    if surface_technology.surfaceDesc:
        statement = statement.where(SurfaceTechnology.surfaceDesc == surface_technology.surfaceDesc)
    if surface_technology.remark:
        statement = statement.where(SurfaceTechnology.remark == surface_technology.remark)
    if surface_technology.creator:
        statement = statement.where(SurfaceTechnology.creator == surface_technology.creator)
    if surface_technology.modifierLast:
        statement = statement.where(SurfaceTechnology.modifierLast == surface_technology.modifierLast)
    if surface_technology.approveStatus:
        statement = statement.where(SurfaceTechnology.approveStatus == surface_technology.approveStatus)
    if surface_technology.approver:
        statement = statement.where(SurfaceTechnology.approver == surface_technology.approver)
    
    results = session.exec(statement).all()
    return results

# 统计查询示例
def get_surface_technology_statistics(session):
    """获取表面要求统计信息"""
    from sqlalchemy import func
    
    # 按表面代码统计数量
    code_stats = session.exec(
        select(SurfaceTechnology.surfaceCode, func.count(SurfaceTechnology.surfaceTechnologyId))
        .group_by(SurfaceTechnology.surfaceCode)
    ).all()
    
    # 按批准状态统计
    status_stats = session.exec(
        select(SurfaceTechnology.approveStatus, func.count(SurfaceTechnology.surfaceTechnologyId))
        .group_by(SurfaceTechnology.approveStatus)
    ).all()
    
    return {
        "byCode": code_stats,
        "byStatus": status_stats
    }

# 使用示例
def example_usage():
    """使用示例"""
    # 创建SurfaceTechnology对象
    surface_technology = SurfaceTechnology(
        surfaceTechnologyId="st-001",
        surfaceCode="HL",
        surfaceDesc="HL",
        remark="高亮表面处理",
        creator="admin@example.com"
    )
    
    # 创建表面要求示例
    # surface_technology_result = create_surface_technology(session, surface_technology)
    
    # 更新表面要求示例
    # surface_technology.surfaceDesc = "高亮表面处理"
    # surface_technology.remark = "高亮表面处理备注"
    # update_surface_technology(session, surface_technology)
    
    # 复杂查询示例
    # 方式1：基本查询
    # query_surface = SurfaceTechnology(surfaceCode="HL", approveStatus="Y")
    # results = get_surface_technologies_with_filter(session, query_surface)
    
    # 方式2：多条件AND查询示例
    # query_surface = SurfaceTechnology(
    #     surfaceCode="HL",           # AND 条件1
    #     approveStatus="Y",          # AND 条件2
    #     creator="admin@example.com" # AND 条件3
    # )
    # # 生成的SQL: WHERE surface_code = 'HL' AND approve_status = 'Y' AND creator = 'admin@example.com'
    # results = get_surface_technologies_with_filter(session, query_surface)
    
    # 查询示例
    # surface_tech = get_surface_technology_by_id(session, surface_technology)
    # print(f"表面要求: {surface_tech.surfaceDesc}")
    # print(f"表面代码: {surface_tech.surfaceCode}")
    # print(f"备注: {surface_tech.remark}")