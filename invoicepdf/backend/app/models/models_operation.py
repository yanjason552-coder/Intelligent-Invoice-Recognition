"""
Operation 实体模型定义
"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, select
from sqlalchemy import Column, String, DateTime, Float, CHAR

class Operation(SQLModel, table=True):
    __tablename__ = "operation"
    
    # 物理主键 - GUID
    operationId: str = Field(max_length=200, sa_column=Column("operation_id", String(200), primary_key=True))
    
    # 工艺代码 (业务主键)
    operationCode: str = Field(max_length=10, sa_column=Column("operation_code", String(10), unique=True))
    
    # 工艺名称
    operationName: str = Field(max_length=20, sa_column=Column("operation_name", String(20)))
    
    # 工艺说明
    operationDesc: str = Field(max_length=200, sa_column=Column("operation_desc", String(200)))
    
    # 标准节拍
    stdTactTime: float = Field(sa_column=Column("std_tact_time", Float))
    
    # 节拍单位
    unitIdTactTime: str = Field(max_length=200, sa_column=Column("unit_id_tact_time", String(200)))
    
    # 加工方式 (0卷加工、1板加工)
    processingMode: str = Field(max_length=1, sa_column=Column("processing_mode", CHAR(1)))
    
    # 加工类别 (0表面加工、1剪切加工)
    processingCatego: str = Field(default="0", max_length=1, sa_column=Column("processing_catego", CHAR(1)))
    
    # 损耗数量
    lossQuantity: float = Field(default=0.0, sa_column=Column("loss_quantity", Float))
    
    # 损耗单位 (米、张)
    unitIdLoss: Optional[str] = Field(default="", max_length=200, sa_column=Column("unit_id_loss", String(200)))
    
    # 备注
    remark: str = Field(max_length=200, sa_column=Column("remark", String(200)))
    
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

def get_operation_by_id(session, operation: Operation):
    """根据ID获取工艺方法信息"""
    statement = select(Operation).where(Operation.operationId == operation.operationId)
    result = session.exec(statement).first()
    return result

def get_operation_by_code(session, operation: Operation):
    """根据工艺代码获取工艺方法信息"""
    statement = select(Operation).where(Operation.operationCode == operation.operationCode)
    result = session.exec(statement).first()
    return result

def create_operation(session, operation: Operation):
    """创建工艺方法"""
    session.add(operation)
    session.commit()
    session.refresh(operation)
    return operation

def update_operation(session, operation: Operation):
    """更新工艺方法"""
    session.add(operation)
    session.commit()
    session.refresh(operation)
    return operation

def delete_operation(session, operation: Operation):
    """删除工艺方法"""
    session.delete(operation)
    session.commit()
    return True 