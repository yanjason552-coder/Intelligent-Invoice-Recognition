#!/usr/bin/env python3
"""
行数据转对象列表的标准方法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlmodel import Session, select, create_engine
from app.models_sales_order_doc_d import SalesOrderDocD, SalesOrderDocDFeature
from app.core.config import settings
from datetime import datetime
import uuid
from typing import List, Dict, Any

def create_test_data(session: Session):
    """创建测试数据"""
    print("创建测试数据...")
    
    # 创建销售订单行项目
    sales_order_doc_d = SalesOrderDocD(
        salesOrderDocDId=str(uuid.uuid4()),
        position=1,
        materialClassId="MAT001",
        materialCode="M001",
        materialDesc="测试物料",
        quantity=10.0,
        unitPrice=100.0,
        totalAmount=1000.0,
        remark="测试备注",
        creator="admin",
        createDate=datetime.now(),
        approveStatus="N"
    )
    session.add(sales_order_doc_d)
    session.commit()
    
    # 创建属性
    feature = SalesOrderDocDFeature(
        salesOrderDocDFeatureId=str(uuid.uuid4()),
        salesOrderDocDId=sales_order_doc_d.salesOrderDocDId,
        position=1,
        featureId="FEAT001",
        featureValue="VALUE001",
        remark="属性备注",
        creator="admin",
        createDate=datetime.now(),
        approveStatus="N"
    )
    session.add(feature)
    session.commit()
    
    return sales_order_doc_d.salesOrderDocDId

def method_1_orm_way(session: Session):
    """方法1: 使用ORM方式（推荐）"""
    print("\n" + "=" * 60)
    print("方法1: 使用ORM方式（推荐）")
    print("=" * 60)
    
    # 直接使用ORM查询，自动返回对象列表
    sales_orders = session.exec(
        select(SalesOrderDocD)
        .options(selectinload(SalesOrderDocD.salesOrderDocDFeatureList))
    ).all()
    
    print(f"✓ 查询到 {len(sales_orders)} 个对象")
    for order in sales_orders:
        print(f"  - ID: {order.salesOrderDocDId}")
        print(f"    编码: {order.materialCode}")
        print(f"    描述: {order.materialDesc}")
        print(f"    属性数量: {len(order.salesOrderDocDFeatureList)}")
        print(f"    类型: {type(order)}")
        print()

def method_2_manual_mapping(session: Session):
    """方法2: 手动映射（原始SQL + 手动转换）"""
    print("\n" + "=" * 60)
    print("方法2: 手动映射（原始SQL + 手动转换）")
    print("=" * 60)
    
    # 执行原始SQL查询
    cursor = session.execute(text("""
        SELECT sales_order_doc_d_id, material_code, material_desc, quantity, total_amount, remark
        FROM sales_order_doc_d
        ORDER BY position
    """))
    
    rows = cursor.fetchall()
    cursor.close()
    
    # 手动映射为对象列表
    sales_orders = []
    for row in rows:
        # 方法2a: 创建字典
        order_dict = {
            "salesOrderDocDId": row[0],
            "materialCode": row[1],
            "materialDesc": row[2],
            "quantity": row[3],
            "totalAmount": row[4],
            "remark": row[5]
        }
        sales_orders.append(order_dict)
    
    print(f"✓ 手动映射为字典列表，共 {len(sales_orders)} 个")
    for order in sales_orders:
        print(f"  - {order}")
    
    # 方法2b: 创建自定义对象
    class SimpleSalesOrder:
        def __init__(self, row):
            self.salesOrderDocDId = row[0]
            self.materialCode = row[1]
            self.materialDesc = row[2]
            self.quantity = row[3]
            self.totalAmount = row[4]
            self.remark = row[5]
        
        def __str__(self):
            return f"SimpleSalesOrder({self.materialCode}: {self.materialDesc})"
    
    # 重新查询并转换为自定义对象
    cursor = session.execute(text("""
        SELECT sales_order_doc_d_id, material_code, material_desc, quantity, total_amount, remark
        FROM sales_order_doc_d
        ORDER BY position
    """))
    
    rows = cursor.fetchall()
    cursor.close()
    
    simple_orders = [SimpleSalesOrder(row) for row in rows]
    print(f"\n✓ 手动映射为自定义对象列表，共 {len(simple_orders)} 个")
    for order in simple_orders:
        print(f"  - {order}")

def method_3_model_validate(session: Session):
    """方法3: 使用model_validate（推荐用于复杂场景）"""
    print("\n" + "=" * 60)
    print("方法3: 使用model_validate（推荐用于复杂场景）")
    print("=" * 60)
    
    # 执行原始SQL查询
    cursor = session.execute(text("""
        SELECT 
            sales_order_doc_d_id, position, material_class_id, material_code, 
            material_desc, quantity, unit_price, total_amount, remark, 
            creator, create_date, approve_status
        FROM sales_order_doc_d
        ORDER BY position
    """))
    
    rows = cursor.fetchall()
    cursor.close()
    
    # 转换为字典列表
    sales_orders = []
    for row in rows:
        order_dict = {
            "salesOrderDocDId": row[0],
            "position": row[1],
            "materialClassId": row[2],
            "materialCode": row[3],
            "materialDesc": row[4],
            "quantity": row[5],
            "unitPrice": row[6],
            "totalAmount": row[7],
            "remark": row[8],
            "creator": row[9],
            "createDate": row[10],
            "approveStatus": row[11]
        }
        sales_orders.append(order_dict)
    
    # 使用model_validate转换为SQLModel对象
    from pydantic import model_validate
    
    validated_orders = []
    for order_dict in sales_orders:
        try:
            # 使用model_validate进行验证和转换
            validated_order = SalesOrderDocD.model_validate(order_dict)
            validated_orders.append(validated_order)
        except Exception as e:
            print(f"验证失败: {e}")
    
    print(f"✓ model_validate转换成功，共 {len(validated_orders)} 个对象")
    for order in validated_orders:
        print(f"  - ID: {order.salesOrderDocDId}")
        print(f"    编码: {order.materialCode}")
        print(f"    类型: {type(order)}")
        print()

def method_4_dataclass_mapping(session: Session):
    """方法4: 使用dataclass进行映射"""
    print("\n" + "=" * 60)
    print("方法4: 使用dataclass进行映射")
    print("=" * 60)
    
    from dataclasses import dataclass
    from typing import Optional
    
    @dataclass
    class SalesOrderSummary:
        salesOrderDocDId: str
        materialCode: str
        materialDesc: str
        quantity: float
        totalAmount: float
        remark: Optional[str] = None
    
    # 执行查询
    cursor = session.execute(text("""
        SELECT sales_order_doc_d_id, material_code, material_desc, quantity, total_amount, remark
        FROM sales_order_doc_d
        ORDER BY position
    """))
    
    rows = cursor.fetchall()
    cursor.close()
    
    # 转换为dataclass对象
    summary_orders = [
        SalesOrderSummary(
            salesOrderDocDId=row[0],
            materialCode=row[1],
            materialDesc=row[2],
            quantity=row[3],
            totalAmount=row[4],
            remark=row[5]
        )
        for row in rows
    ]
    
    print(f"✓ dataclass映射成功，共 {len(summary_orders)} 个对象")
    for order in summary_orders:
        print(f"  - {order}")

def method_5_namedtuple_mapping(session: Session):
    """方法5: 使用namedtuple进行映射"""
    print("\n" + "=" * 60)
    print("方法5: 使用namedtuple进行映射")
    print("=" * 60)
    
    from collections import namedtuple
    
    # 定义namedtuple结构
    SalesOrderRow = namedtuple('SalesOrderRow', [
        'salesOrderDocDId', 'materialCode', 'materialDesc', 
        'quantity', 'totalAmount', 'remark'
    ])
    
    # 执行查询
    cursor = session.execute(text("""
        SELECT sales_order_doc_d_id, material_code, material_desc, quantity, total_amount, remark
        FROM sales_order_doc_d
        ORDER BY position
    """))
    
    rows = cursor.fetchall()
    cursor.close()
    
    # 转换为namedtuple对象
    named_orders = [SalesOrderRow(*row) for row in rows]
    
    print(f"✓ namedtuple映射成功，共 {len(named_orders)} 个对象")
    for order in named_orders:
        print(f"  - ID: {order.salesOrderDocDId}")
        print(f"    编码: {order.materialCode}")
        print(f"    描述: {order.materialDesc}")
        print(f"    数量: {order.quantity}")
        print(f"    金额: {order.totalAmount}")
        print()

def performance_comparison(session: Session):
    """性能对比"""
    print("\n" + "=" * 60)
    print("性能对比")
    print("=" * 60)
    
    import time
    
    # ORM方式性能测试
    start_time = time.time()
    for i in range(10):
        sales_orders = session.exec(select(SalesOrderDocD)).all()
    orm_time = time.time() - start_time
    
    # 手动映射性能测试
    start_time = time.time()
    for i in range(10):
        cursor = session.execute(text("SELECT * FROM sales_order_doc_d"))
        rows = cursor.fetchall()
        cursor.close()
        orders = [{"id": row[0], "code": row[3]} for row in rows]
    manual_time = time.time() - start_time
    
    print(f"ORM方式 10次查询耗时: {orm_time:.4f}秒")
    print(f"手动映射 10次查询耗时: {manual_time:.4f}秒")
    print(f"性能差异: {((manual_time - orm_time) / manual_time * 100):.1f}%")

def main():
    """主函数"""
    print("=" * 60)
    print("行数据转对象列表的标准方法")
    print("=" * 60)
    
    # 创建数据库引擎
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    
    with Session(engine) as session:
        # 创建测试数据
        create_test_data(session)
        
        # 演示各种方法
        method_1_orm_way(session)
        method_2_manual_mapping(session)
        method_3_model_validate(session)
        method_4_dataclass_mapping(session)
        method_5_namedtuple_mapping(session)
        performance_comparison(session)
    
    print("\n" + "=" * 60)
    print("总结:")
    print("✓ 方法1 (ORM): 最推荐，类型安全，自动管理")
    print("✓ 方法3 (model_validate): 适合复杂验证场景")
    print("✓ 方法4 (dataclass): 适合简单数据结构")
    print("✓ 方法5 (namedtuple): 轻量级，不可变")
    print("✓ 方法2 (手动映射): 灵活但容易出错")
    print("=" * 60)

if __name__ == "__main__":
    main() 