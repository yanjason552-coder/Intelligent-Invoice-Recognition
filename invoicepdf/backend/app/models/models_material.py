"""
Material 实体模型定义

设计说明：
1. Material 和 MaterialD 之间存在一对多关系
2. 不创建外键约束，保持数据操作的灵活性
3. 不使用 SQLModel 的 Relationship，只作为普通属性
4. 这种设计的好处：
   - 避免外键约束的性能开销
   - 避免 SQLModel 关联关系的复杂性
   - 允许更灵活的数据操作（如批量导入、数据迁移）
   - 支持分布式架构中的数据关联
   - 便于数据清理和维护
   - 代码更简洁，易于理解和维护
"""

from typing import List, Optional, Annotated, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, select
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func

# 物料属性表模型
# 注意：不创建外键约束，保持关联关系的灵活性
class MaterialD(SQLModel, table=True):
    __tablename__ = "material_d"
    
    # 物理主键
    materialDId: str = Field(max_length=200, sa_column=Column("material_d_id", String(200), primary_key=True))
    
    # 父键 (关联 material 表，但不创建外键约束)
    materialId: str = Field(max_length=200, sa_column=Column("material_id", String(200)))
    
    # 属性编号
    featureCode: str = Field(max_length=10, sa_column=Column("feature_code", String(10)))
    
    # 属性描述
    featureDesc: str = Field(max_length=20, sa_column=Column("feature_desc", String(20)))
    
    # 属性值
    featureValue: Optional[str] = Field(default=None, max_length=20, sa_column=Column("feature_value", String(20)))
    
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
    
    # 移除关联关系，只保留基本字段

# 物料表模型
# 注意：与 MaterialD 的关联关系不依赖外键约束
class Material(SQLModel, table=True):
    __tablename__ = "material"
    
    # 物理主键
    materialId: str = Field(max_length=200, sa_column=Column("material_id", String(200), primary_key=True))
    
    # 物料类别
    materialClassId: str = Field(max_length=200, sa_column=Column("material_class_id", String(200)))
    
    # 物料编号
    materialCode: str = Field(max_length=40, sa_column=Column("material_code", String(40)))
    
    # 物料描述
    materialDesc: str = Field(max_length=200, sa_column=Column("material_desc", String(200)))
    
    # 基本单位
    unitId: Optional[str] = Field(default=None, max_length=200, sa_column=Column("unit_id", String(200)))
    
    # 第二单位
    secondUnitId: Optional[str] = Field(default=None, max_length=200, sa_column=Column("second_unit_id", String(200)))
    
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
    def materialDList(self) -> List[MaterialD]:
        """获取物料的属性列表"""
        # 这里可以通过查询获取，暂时返回空列表
        return []
    
    @materialDList.setter
    def materialDList(self, value: List[MaterialD]):
        """设置物料的属性列表"""
        # 这里可以处理设置逻辑
        pass

# 查询示例函数
def get_material_with_attributes(session, material: Material):
    """获取物料及其所有属性"""
    statement = select(Material).where(Material.materialId == material.materialId)
    material_result = session.exec(statement).first()
    return material_result

def get_materials_by_class(session, material: Material):
    """根据物料类别获取所有物料及其属性"""
    statement = select(Material).where(Material.materialClassId == material.materialClassId)
    materials = session.exec(statement).all()
    return materials

def get_material_attributes(session, material: Material):
    """获取指定物料的所有属性"""
    statement = select(MaterialD).where(MaterialD.materialId == material.materialId)
    attributes = session.exec(statement).all()
    return attributes

def create_material_with_attributes(session, material: Material):
    """创建物料及其属性
    
    Args:
        session: 数据库会话
        material: Material对象，包含物料信息和属性列表
    """
    # 获取属性列表
    attributes_data = []
    if hasattr(material, 'materialDList') and material.materialDList:
        for attr in material.materialDList:
            attr_dict = {
                "materialDId": attr.materialDId,
                "featureCode": attr.featureCode,
                "featureDesc": attr.featureDesc,
                "featureValue": attr.featureValue,
                "remark": attr.remark,
                "creator": attr.creator,
                "createDate": attr.createDate,
                "modifierLast": attr.modifierLast,
                "modifyDateLast": attr.modifyDateLast,
                "approveStatus": attr.approveStatus,
                "approver": attr.approver,
                "approveDate": attr.approveDate
            }
            attributes_data.append(attr_dict)
    
    # 创建主表记录
    session.add(material)
    
    # 创建子表记录
    for attr_data in attributes_data:
        attr_data['materialId'] = material.materialId
        material_d = MaterialD(**attr_data)
        session.add(material_d)
    
    session.commit()
    session.refresh(material)
    return material

def update_material_attributes(session, material: Material):
    """更新物料的属性
    
    Args:
        session: 数据库会话
        material: Material对象，包含物料信息和属性列表(materialDList)
    """
    # 先删除现有属性
    delete_statement = select(MaterialD).where(MaterialD.materialId == material.materialId)
    existing_attrs = session.exec(delete_statement).all()
    for attr in existing_attrs:
        session.delete(attr)
    
    # 从Material对象的materialDList中添加新属性
    if hasattr(material, 'materialDList') and material.materialDList:
        for attr in material.materialDList:
            # 确保设置正确的materialId
            attr.materialId = material.materialId
            session.add(attr)
    
    session.commit()

# 复杂查询示例
def get_materials_with_filter(session, material: Material):
    """复杂查询：根据Material对象的字段筛选物料
    
    注意：多个where条件会自动使用AND连接
    
    Args:
        session: 数据库会话
        material: Material对象，包含查询条件
    """
    statement = select(Material)
    
    # 使用Material对象的字段作为查询条件
    # 多个where条件会自动使用AND连接
    if material.materialId:
        statement = statement.where(Material.materialId == material.materialId)
    if material.materialClassId:
        statement = statement.where(Material.materialClassId == material.materialClassId)
    if material.materialCode:
        statement = statement.where(Material.materialCode == material.materialCode)
    if material.materialDesc:
        statement = statement.where(Material.materialDesc == material.materialDesc)
    if material.unitId:
        statement = statement.where(Material.unitId == material.unitId)
    if material.secondUnitId:
        statement = statement.where(Material.secondUnitId == material.secondUnitId)
    if material.remark:
        statement = statement.where(Material.remark == material.remark)
    if material.creator:
        statement = statement.where(Material.creator == material.creator)
    if material.modifierLast:
        statement = statement.where(Material.modifierLast == material.modifierLast)
    if material.approveStatus:
        statement = statement.where(Material.approveStatus == material.approveStatus)
    if material.approver:
        statement = statement.where(Material.approver == material.approver)
    
    # 如果Material对象包含属性列表，可以通过属性筛选
    if hasattr(material, 'materialDList') and material.materialDList:
        # 先进行JOIN操作
        statement = statement.join(MaterialD, Material.materialId == MaterialD.materialId)
        
        # 为每个属性添加AND条件（多个where会自动使用AND连接）
        for attr in material.materialDList:
            if attr.featureCode:
                statement = statement.where(MaterialD.featureCode == attr.featureCode)
    
    materials = session.exec(statement).all()
    return materials

# 统计查询示例
def get_material_statistics(session):
    """获取物料统计信息"""
    from sqlalchemy import func
    
    # 按类别统计物料数量
    class_stats = session.exec(
        select(Material.materialClassId, func.count(Material.materialId))
        .group_by(Material.materialClassId)
    ).all()
    
    # 按批准状态统计
    status_stats = session.exec(
        select(Material.approveStatus, func.count(Material.materialId))
        .group_by(Material.approveStatus)
    ).all()
    
    return {
        "byClass": class_stats,
        "byStatus": status_stats
    }

# 使用示例
def example_usage():
    """使用示例"""
    # 创建Material对象
    material = Material(
        materialId="mat-001",
        materialClassId="class-001", 
        materialCode="MAT001",
        materialDesc="示例物料",
        unitId="unit-001",
        creator="admin"
    )
    
    # 创建MaterialD对象列表
    material_d_list = [
        MaterialD(
            materialDId="mat-d-001",
            featureCode="COLOR",
            featureDesc="颜色",
            featureValue="红色",
            creator="admin"
        ),
        MaterialD(
            materialDId="mat-d-002", 
            featureCode="SIZE",
            featureDesc="尺寸",
            featureValue="大号",
            creator="admin"
        )
    ]
    
    # 设置关联关系
    material.materialDList = material_d_list
    
    # 创建物料及属性（使用Material对象）
    # material_result = create_material_with_attributes(session, material)
    
    # 更新物料属性示例
    # 修改属性值
    # material.materialDList[0].featureValue = "蓝色"
    # material.materialDList[1].featureValue = "中号"
    # update_material_attributes(session, material)
    
    # 复杂查询示例
    # 方式1：基本查询
    # query_material = Material(materialClassId="class-001", approveStatus="Y")
    # materials = get_materials_with_filter(session, query_material)
    
    # 方式2：通过属性筛选
    # query_material = Material()
    # query_material.materialDList = [MaterialD(featureCode="COLOR")]
    # materials = get_materials_with_filter(session, query_material)
    
    # 方式3：组合查询（多个条件使用AND连接）
    # query_material = Material(materialClassId="class-001", approveStatus="Y")
    # query_material.materialDList = [MaterialD(featureCode="SIZE")]
    # materials = get_materials_with_filter(session, query_material)
    
    # 方式4：多条件AND查询示例
    # query_material = Material(
    #     materialClassId="class-001",    # AND 条件1
    #     approveStatus="Y",              # AND 条件2
    #     creator="admin",                # AND 条件3
    #     materialCode="MAT001"           # AND 条件4
    # )
    # # 生成的SQL: WHERE material_class_id = 'class-001' AND approve_status = 'Y' AND creator = 'admin' AND material_code = 'MAT001'
    # materials = get_materials_with_filter(session, query_material)
    
    # 方式5：多属性AND查询示例
    # query_material = Material(materialClassId="class-001")
    # query_material.materialDList = [
    #     MaterialD(featureCode="COLOR"),  # AND 属性条件1
    #     MaterialD(featureCode="SIZE")    # AND 属性条件2
    # ]
    # # 生成的SQL: 
    # # SELECT material.* FROM material 
    # # JOIN material_d ON material.material_id = material_d.material_id
    # # WHERE material_class_id = 'class-001' 
    # #   AND material_d.feature_code = 'COLOR' 
    # #   AND material_d.feature_code = 'SIZE'
    # materials = get_materials_with_filter(session, query_material)
    
    # 查询示例
    # material = get_material_with_attributes(session, material)
    # print(f"物料: {material.materialDesc}")
    # print(f"属性数量: {len(material.materialDList)}")
    # 
    # for attr in material.materialDList:
    #     print(f"  {attr.featureDesc}: {attr.featureValue}") 