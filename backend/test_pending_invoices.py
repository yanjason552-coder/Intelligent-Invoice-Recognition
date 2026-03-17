"""
测试待审核发票接口
用于诊断500错误
"""
import sys
import traceback

try:
    from app.core.config import settings
    from app.core.db import engine
    from app.models.models_invoice import Invoice
    from app.models.models_company import Company
    from sqlmodel import Session, select, func, and_
    
    print("=" * 60)
    print("测试待审核发票接口")
    print("=" * 60)
    
    # 1. 测试数据库连接
    print("\n1. 测试数据库连接...")
    try:
        with Session(engine) as session:
            result = session.exec(select(func.count()).select_from(Invoice)).one()
            print(f"   [OK] 数据库连接成功，Invoice表记录数: {result}")
    except Exception as e:
        print(f"   [FAIL] 数据库连接失败: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    # 2. 测试Invoice表结构
    print("\n2. 检查Invoice表结构...")
    try:
        with Session(engine) as session:
            # 检查关键字段是否存在
            test_invoice = session.exec(select(Invoice).limit(1)).first()
            if test_invoice:
                print(f"   [OK] Invoice表存在，示例记录ID: {test_invoice.id}")
                print(f"   [INFO] review_status: {test_invoice.review_status}")
                print(f"   [INFO] company_id: {test_invoice.company_id}")
            else:
                print("   [WARNING] Invoice表为空")
    except Exception as e:
        print(f"   [FAIL] 检查Invoice表失败: {e}")
        traceback.print_exc()
    
    # 3. 测试查询待审核发票
    print("\n3. 测试查询待审核发票...")
    try:
        with Session(engine) as session:
            conditions = [Invoice.review_status == "pending"]
            count_statement = select(func.count()).select_from(Invoice).where(and_(*conditions))
            total = session.exec(count_statement).one()
            print(f"   [OK] 待审核发票数量: {total}")
            
            # 查询前10条
            statement = select(Invoice).where(and_(*conditions))
            invoices = session.exec(statement.order_by(Invoice.create_time.desc()).limit(10)).all()
            print(f"   [OK] 查询到 {len(invoices)} 条记录")
    except Exception as e:
        print(f"   [FAIL] 查询待审核发票失败: {e}")
        traceback.print_exc()
    
    # 4. 测试Company表
    print("\n4. 检查Company表...")
    try:
        with Session(engine) as session:
            company_count = session.exec(select(func.count()).select_from(Company)).one()
            print(f"   [OK] Company表存在，记录数: {company_count}")
    except Exception as e:
        print(f"   [FAIL] 检查Company表失败: {e}")
        traceback.print_exc()
    
    # 5. 测试InvoiceResponse模型
    print("\n5. 测试InvoiceResponse模型...")
    try:
        from app.models.models_invoice import InvoiceResponse
        
        with Session(engine) as session:
            invoice = session.exec(select(Invoice).limit(1)).first()
            if invoice:
                # 尝试创建InvoiceResponse
                response = InvoiceResponse(
                    id=invoice.id,
                    invoice_no=invoice.invoice_no,
                    invoice_type=invoice.invoice_type,
                    invoice_date=invoice.invoice_date,
                    amount=invoice.amount,
                    tax_amount=invoice.tax_amount,
                    total_amount=invoice.total_amount,
                    currency=invoice.currency,
                    supplier_name=invoice.supplier_name,
                    supplier_tax_no=invoice.supplier_tax_no,
                    buyer_name=invoice.buyer_name,
                    buyer_tax_no=invoice.buyer_tax_no,
                    recognition_accuracy=invoice.recognition_accuracy,
                    recognition_status=invoice.recognition_status,
                    review_status=invoice.review_status,
                    company_id=invoice.company_id,
                    company_code=None,
                    template_name=invoice.template_name,
                    template_version=invoice.template_version,
                    model_name=invoice.model_name,
                    create_time=invoice.create_time
                )
                print(f"   [OK] InvoiceResponse模型创建成功")
            else:
                print("   [WARNING] 没有发票记录可以测试")
    except Exception as e:
        print(f"   [FAIL] InvoiceResponse模型测试失败: {e}")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] 测试失败: {e}")
    traceback.print_exc()
    sys.exit(1)
