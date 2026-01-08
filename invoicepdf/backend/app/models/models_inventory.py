"""
Inventory 实体模型定义

设计说明：
1. Inventory 和 MaterialLotFeature 之间存在一对多关系
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
from sqlalchemy import Column, String, DateTime, Text, Float
from sqlalchemy.sql import func

# 批次属性表模型
# 注意：不创建外键约束，保持关联关系的灵活性
class MaterialLotFeature(SQLModel, table=True):
    __tablename__ = "material_lot_feature"
    
    # 物理主键
    materialLotFeatureId: str = Field(max_length=200, sa_column=Column("material_lot_feature_id", String(200), primary_key=True))
    
    # 批次主键 (关联 inventory 表，但不创建外键约束)
    materialLotId: str = Field(max_length=200, sa_column=Column("material_lot_id", String(200)))
    
    # 属性ID
    featureId: str = Field(max_length=200, sa_column=Column("feature_id", String(200)))
    
    # 属性代码
    featureCode: str = Field(max_length=10, sa_column=Column("feature_code", String(10)))
    
    # 属性描述
    featureDesc: str = Field(max_length=20, sa_column=Column("feature_desc", String(20)))
    
    # 属性值
    featureValue: str = Field(max_length=20, sa_column=Column("feature_value", String(20)))
    
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
    
    # 移除关联关系，只保留基本字段

# 物料批号表模型
# 注意：与 MaterialLotFeature 的关联关系不依赖外键约束
class MaterialLot(SQLModel, table=True):
    __tablename__ = "material_lot"
    
    # 物理主键
    materialLotId: str = Field(max_length=200, sa_column=Column("material_lot_id", String(200), primary_key=True))
    
    # 物料相关字段
    materialId: str = Field(max_length=200, sa_column=Column("material_id", String(200)))
    materialCode: str = Field(max_length=40, sa_column=Column("material_code", String(40)))
    materialDesc: str = Field(max_length=200, sa_column=Column("material_desc", String(200)))
    
    # 批号相关字段
    lotNo: str = Field(max_length=40, sa_column=Column("lot_no", String(40)))
    lotDesc: str = Field(max_length=80, sa_column=Column("lot_desc", String(80)))
    
    # 制造日期
    manufactureDate: Optional[datetime] = Field(default=None, sa_column=Column("manufacture_date", DateTime))
    
    # 备注
    remark: str = Field(max_length=200, sa_column=Column("remark", String(200)))
    
    # 创建信息
    creator: str = Field(max_length=20, sa_column=Column("creator", String(20)))
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    
    # 修改信息
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 审批相关字段
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))
    
    @property
    def materialLotFeatureList(self) -> List[MaterialLotFeature]:
        """获取库存的属性列表"""
        # 这里可以通过查询获取，暂时返回空列表
        return []
    
    @materialLotFeatureList.setter
    def materialLotFeatureList(self, value: List[MaterialLotFeature]):
        """设置库存的属性列表"""
        # 这里可以处理设置逻辑
        pass
# 库存明细表模型
# 注意：与 MaterialLotFeature 的关联关系不依赖外键约束
class Inventory(SQLModel, table=True):
    __tablename__ = "inventory"
    
    # 物理主键
    inventoryId: str = Field(max_length=200, sa_column=Column("inventory_id", String(200), primary_key=True))
    
    # 物料相关字段
    materialId: str = Field(max_length=200, sa_column=Column("material_id", String(200)))
    materialCode: Optional[str] = Field(default=None, max_length=40, sa_column=Column("material_code", String(40)))
    materialDesc: Optional[str] = Field(default=None, max_length=200, sa_column=Column("material_desc", String(200)))
    
    # 工厂相关字段
    plantId: Optional[str] = Field(default=None, max_length=200, sa_column=Column("plant_id", String(200)))
    plantName: Optional[str] = Field(default=None, max_length=20, sa_column=Column("plant_name", String(20)))
    
    # 仓库相关字段
    warehouseId: Optional[str] = Field(default=None, max_length=200, sa_column=Column("warehouse_id", String(200)))
    warehouseName: Optional[str] = Field(default=None, max_length=20, sa_column=Column("warehouse_name", String(20)))
    
    # 库位相关字段
    binId: Optional[str] = Field(default=None, max_length=200, sa_column=Column("bin_id", String(200)))
    binName: Optional[str] = Field(default=None, max_length=20, sa_column=Column("bin_name", String(20)))
    
    # 批号相关字段
    materialLotId: str = Field(max_length=200, sa_column=Column("material_lot_id", String(200)))
    lotNo: str = Field(max_length=20, sa_column=Column("lot_no", String(20)))
    lotDesc: str = Field(max_length=80, sa_column=Column("lot_desc", String(80)))
    
    # 库存数量字段
    stockQty: float = Field(default=0.0, sa_column=Column("stock_qty", Float))
    unitIdStock: str = Field(max_length=200, sa_column=Column("unit_id_stock", String(200)))
    stockQtySecond: float = Field(default=0.0, sa_column=Column("stock_qty_second", Float))
    unitIdStockSec: str = Field(max_length=200, sa_column=Column("unit_id_stock_sec", String(200)))
    
    # 已套用库存数量字段
    stockQtyLocked: float = Field(default=0.0, sa_column=Column("stock_qty_locked", Float))
    stockQtySecondLocked: float = Field(default=0.0, sa_column=Column("stock_qty_second_locked", Float))
    
    # 时间戳字段
    createDate: datetime = Field(default_factory=datetime.now, sa_column=Column("create_date", DateTime))
    creator: str = Field(max_length=20, sa_column=Column("creator", String(20)))
    modifierLast: Optional[str] = Field(default=None, max_length=20, sa_column=Column("modifier_last", String(20)))
    modifyDateLast: Optional[datetime] = Field(default=None, sa_column=Column("modify_date_last", DateTime))
    
    # 审批相关字段
    approveStatus: str = Field(default="N", max_length=1, sa_column=Column("approve_status", String(1)))
    approver: Optional[str] = Field(default=None, max_length=20, sa_column=Column("approver", String(20)))
    approveDate: Optional[datetime] = Field(default=None, sa_column=Column("approve_date", DateTime))
    
    
    
    @property
    def materialLot(self) -> Optional[MaterialLot]:
        """获取库存关联的物料批次"""
        # 这里可以通过查询获取，暂时返回None
        return None
    
    @materialLot.setter
    def materialLot(self, value: Optional[MaterialLot]):
        """设置库存关联的物料批次"""
        # 这里可以处理设置逻辑
        pass

# 查询示例函数
def get_inventory_with_features(session, inventory: Inventory):
    """获取库存及其所有批次属性"""
    statement = select(Inventory).where(Inventory.inventoryId == inventory.inventoryId)
    inventory_result = session.exec(statement).first()
    return inventory_result

def get_inventory_features(session, inventory: Inventory):
    """获取指定库存的所有批次属性"""
    statement = select(MaterialLotFeature).where(MaterialLotFeature.materialLotId == inventory.materialLotId)
    features = session.exec(statement).all()
    return features

def create_inventory_with_features(session, inventory: Inventory):
    """创建库存及其批次属性
    
    Args:
        session: 数据库会话
        inventory: Inventory对象，包含materialLot对象，materialLot对象包含materialLotFeatureList
    """
    try:
        # 1. 创建 MaterialLot 对象（如果存在）
        if inventory.materialLot:
            print(f"创建 MaterialLot: {inventory.materialLot.materialLotId}")
            session.add(inventory.materialLot)
            
            # 2. 创建 MaterialLotFeature 对象（如果存在）
            if hasattr(inventory.materialLot, 'materialLotFeatureList') and inventory.materialLot.materialLotFeatureList:
                for feature in inventory.materialLot.materialLotFeatureList:
                    print(f"创建 MaterialLotFeature: {feature.materialLotFeatureId}")
                    session.add(feature)
        
        # 3. 创建 Inventory 对象
        print(f"创建 Inventory: {inventory.inventoryId}")
        session.add(inventory)
        
        # 4. 提交所有更改
        session.commit()
        session.refresh(inventory)
        
        print("库存及其批次属性创建成功")
        return inventory
        
    except Exception as e:
        print(f"创建库存及其批次属性失败: {e}")
        session.rollback()
        raise e

def update_inventory_features(session, inventory: Inventory):
    """更新库存的批次属性
    
    Args:
        session: 数据库会话
        inventory: Inventory对象，包含materialLot对象，materialLot对象包含materialLotFeatureList
    """
    try:
        if not inventory.materialLot:
            print("没有找到MaterialLot对象，无法更新批次属性")
            return
        
        # 1. 先删除现有的 MaterialLotFeature 记录
        delete_statement = select(MaterialLotFeature).where(MaterialLotFeature.materialLotId == inventory.materialLot.materialLotId)
        existing_features = session.exec(delete_statement).all()
        for feature in existing_features:
            print(f"删除现有 MaterialLotFeature: {feature.materialLotFeatureId}")
            session.delete(feature)
        
        # 2. 添加新的 MaterialLotFeature 记录
        if hasattr(inventory.materialLot, 'materialLotFeatureList') and inventory.materialLot.materialLotFeatureList:
            for feature in inventory.materialLot.materialLotFeatureList:
                # 确保设置正确的materialLotId
                feature.materialLotId = inventory.materialLot.materialLotId
                print(f"添加新 MaterialLotFeature: {feature.materialLotFeatureId}")
                session.add(feature)
        
        # 3. 更新 MaterialLot 对象
        session.add(inventory.materialLot)
        
        # 4. 更新 Inventory 对象
        session.add(inventory)
        
        session.commit()
        print("库存及其批次属性更新成功")
        
    except Exception as e:
        print(f"更新库存及其批次属性失败: {e}")
        session.rollback()
        raise e

# 复杂查询示例
def get_inventory_with_filter(session, inventory: Inventory):
    """复杂查询：根据Inventory对象的字段筛选库存
    
    注意：多个where条件会自动使用AND连接
    
    Args:
        session: 数据库会话
        inventory: Inventory对象，包含查询条件
    """
    statement = select(Inventory)
    
    # 使用Inventory对象的字段作为查询条件
    # 多个where条件会自动使用AND连接
    if inventory.inventory_id:
        statement = statement.where(Inventory.inventory_id == inventory.inventory_id)
    if inventory.material_id:
        statement = statement.where(Inventory.material_id == inventory.material_id)
    if inventory.material_code:
        statement = statement.where(Inventory.material_code == inventory.material_code)
    if inventory.material_desc:
        statement = statement.where(Inventory.material_desc == inventory.material_desc)
    if inventory.plant_id:
        statement = statement.where(Inventory.plant_id == inventory.plant_id)
    if inventory.warehouse_id:
        statement = statement.where(Inventory.warehouse_id == inventory.warehouse_id)
    if inventory.bin_id:
        statement = statement.where(Inventory.bin_id == inventory.bin_id)
    if inventory.material_lot_id:
        statement = statement.where(Inventory.material_lot_id == inventory.material_lot_id)
    if inventory.approve_status:
        statement = statement.where(Inventory.approve_status == inventory.approve_status)
    if inventory.approver:
        statement = statement.where(Inventory.approver == inventory.approver)
    
    # 如果Inventory对象包含批次属性列表，可以通过属性筛选
    if hasattr(inventory, 'materialLotFeaturesList') and inventory.materialLotFeaturesList:
        # 先进行JOIN操作
        statement = statement.join(MaterialLotFeature, Inventory.material_lot_id == MaterialLotFeature.material_lot_id)
        
        # 为每个批次属性添加AND条件（多个where会自动使用AND连接）
        for feature in inventory.materialLotFeaturesList:
            if feature.feature_code:
                statement = statement.where(MaterialLotFeature.feature_code == feature.feature_code)
    
    inventories = session.exec(statement).all()
    return inventories

# 统计查询示例
def get_inventory_statistics(session):
    """获取库存统计信息"""
    from sqlalchemy import func
    
    # 按工厂统计库存数量
    plant_stats = session.exec(
        select(Inventory.plant_id, func.count(Inventory.inventory_id))
        .group_by(Inventory.plant_id)
    ).all()
    
    # 按批准状态统计
    status_stats = session.exec(
        select(Inventory.approve_status, func.count(Inventory.inventory_id))
        .group_by(Inventory.approve_status)
    ).all()
    
    return {
        "byPlant": plant_stats,
        "byStatus": status_stats
    }

# 使用示例
def example_usage():
    """使用示例"""
    # 创建Inventory对象
    inventory = Inventory(
        inventoryId="inv-001",
        materialId="mat-001",
        materialCode="MAT001",
        materialDesc="示例物料",
        materialLotId="lot-001",
        lotNo="LOT001",
        lotDesc="示例批号",
        stockQty=100.0,
        unitIdStock="unit-001",
        stockQtySecond=50.0,
        unitIdStockSec="unit-002",
        plantId="plant-001",
        warehouseId="wh-001",
        binId="bin-001"
    )
    
    # 创建MaterialLotFeature对象列表
    material_lot_features_list = [
        MaterialLotFeature(
            materialLotFeatureId="mlf-001",
            materialLotId="lot-001",
            featureId="feat-001",
            featureCode="COLOR",
            featureDesc="颜色",
            featureValue="红色",
            remark="颜色属性",
            creator="admin"
        ),
        MaterialLotFeature(
            materialLotFeatureId="mlf-002",
            materialLotId="lot-001",
            featureId="feat-002",
            featureCode="SIZE",
            featureDesc="尺寸",
            featureValue="大号",
            remark="尺寸属性",
            creator="admin"
        )
    ]
    
    # 设置关联关系
    inventory.materialLotFeaturesList = material_lot_features_list
    
    # 创建库存及批次属性（使用Inventory对象）
    # inventory_result = create_inventory_with_features(session, inventory)
    
    # 更新库存批次属性示例
    # 修改属性值
    # inventory.materialLotFeaturesList[0].featureValue = "蓝色"
    # inventory.materialLotFeaturesList[1].featureValue = "中号"
    # update_inventory_features(session, inventory)
    
    # 复杂查询示例
    # 方式1：基本查询
    # query_inventory = Inventory(plantId="plant-001", approveStatus="Y")
    # inventories = get_inventory_with_filter(session, query_inventory)
    
    # 方式2：通过批次属性筛选
    # query_inventory = Inventory()
    # query_inventory.materialLotFeaturesList = [MaterialLotFeature(featureCode="COLOR")]
    # inventories = get_inventory_with_filter(session, query_inventory)
    
    # 方式3：组合查询（多个条件使用AND连接）
    # query_inventory = Inventory(plantId="plant-001", approveStatus="Y")
    # query_inventory.materialLotFeaturesList = [MaterialLotFeature(featureCode="SIZE")]
    # inventories = get_inventory_with_filter(session, query_inventory)
    
    # 查询示例
    # inventory = get_inventory_with_features(session, inventory)
    # print(f"库存: {inventory.materialDesc}")
    # print(f"批次属性数量: {len(inventory.materialLotFeaturesList)}")
    # 
    # for feature in inventory.materialLotFeaturesList:
    #     print(f"  {feature.featureDesc}: {feature.featureValue}")

# MaterialLot 查询示例函数
def get_material_lot_with_features(session, material_lot: MaterialLot):
    """获取批次及其所有属性"""
    statement = select(MaterialLot).where(MaterialLot.materialLotId == material_lot.materialLotId)
    material_lot_result = session.exec(statement).first()
    return material_lot_result

def get_material_lots_by_material(session, material_id: str):
    """根据物料ID获取所有批次及其属性"""
    statement = select(MaterialLot).where(MaterialLot.materialId == material_id)
    material_lots = session.exec(statement).all()
    return material_lots

def get_material_lot_features(session, material_lot: MaterialLot):
    """获取指定批次的所有属性"""
    statement = select(MaterialLotFeature).where(MaterialLotFeature.materialLotId == material_lot.materialLotId)
    features = session.exec(statement).all()
    return features

def create_material_lot_with_features(session, material_lot: MaterialLot):
    """创建批次及其属性
    
    Args:
        session: 数据库会话
        material_lot: MaterialLot对象，包含批次信息和属性列表
    """
    # 获取属性列表
    features_data = []
    if hasattr(material_lot, 'materialLotFeatureList') and material_lot.materialLotFeatureList:
        for feature in material_lot.materialLotFeatureList:
            feature_dict = {
                "material_lot_feature_id": feature.material_lot_feature_id,
                "material_lot_id": feature.material_lot_id,
                "feature_id": feature.feature_id,
                "feature_code": feature.feature_code,
                "feature_desc": feature.feature_desc,
                "feature_value": feature.feature_value,
                "remark": feature.remark,
                "creator": feature.creator,
                "create_date": feature.create_date,
                "modifier_last": feature.modifier_last,
                "modify_date_last": feature.modify_date_last,
                "approve_status": feature.approve_status,
                "approver": feature.approver,
                "approve_date": feature.approve_date
            }
            features_data.append(feature_dict)
    
    # 创建批次记录
    material_lot_dict = {
        "material_lot_id": material_lot.material_lot_id,
        "material_id": material_lot.material_id,
        "material_code": material_lot.material_code,
        "material_desc": material_lot.material_desc,
        "lot_no": material_lot.lot_no,
        "lot_desc": material_lot.lot_desc,
        "manufacture_date": material_lot.manufacture_date,
        "remark": material_lot.remark,
        "creator": material_lot.creator,
        "create_date": material_lot.create_date,
        "modifier_last": material_lot.modifier_last,
        "modify_date_last": material_lot.modify_date_last,
        "approve_status": material_lot.approve_status,
        "approver": material_lot.approver,
        "approve_date": material_lot.approve_date
    }
    
    # 这里可以添加实际的数据库操作逻辑
    print(f"创建批次: {material_lot_dict}")
    print(f"创建属性: {features_data}")
    
    return material_lot_dict, features_data 