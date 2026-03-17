"""
检查"孔位类"模板的字段定义
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select
from app.core.db import engine
from app.models.models_invoice import Template, TemplateField

def check_template_fields():
    """检查孔位类模板的字段"""
    with Session(engine) as session:
        # 查找模板
        template = session.exec(
            select(Template).where(
                (Template.name == "孔位类") | (Template.name == "孔类模板")
            )
        ).first()
        
        if not template:
            print("未找到'孔位类'或'孔类模板'")
            return
        
        print(f"找到模板: {template.name} (ID: {template.id})")
        print(f"当前版本ID: {template.current_version_id}")
        
        if not template.current_version_id:
            print("模板没有当前版本")
            return
        
        # 查询字段
        fields = session.exec(
            select(TemplateField)
            .where(TemplateField.template_version_id == template.current_version_id)
            .order_by(TemplateField.sort_order)
        ).all()
        
        print(f"\n字段总数: {len(fields)}")
        print("\n字段列表:")
        print("-" * 100)
        print(f"{'序号':<6} {'字段标识':<30} {'字段名称':<25} {'数据类型':<15} {'是否必填':<10} {'父字段ID':<40}")
        print("-" * 100)
        
        invoice_related_fields = []
        for idx, field in enumerate(fields, 1):
            parent_info = f"{field.parent_field_id}" if field.parent_field_id else "无"
            print(f"{idx:<6} {field.field_key:<30} {field.field_name:<25} {field.data_type:<15} {'是' if field.is_required else '否':<10} {parent_info:<40}")
            
            # 检查是否有发票相关字段
            field_key_lower = field.field_key.lower()
            field_name_lower = field.field_name.lower() if field.field_name else ""
            if any(keyword in field_key_lower or keyword in field_name_lower 
                   for keyword in ['invoice', '发票', 'purchase_order', '采购订单', 'supplier', '供应商']):
                invoice_related_fields.append({
                    'field_key': field.field_key,
                    'field_name': field.field_name,
                    'data_type': field.data_type
                })
        
        print("-" * 100)
        
        if invoice_related_fields:
            print(f"\n⚠️  发现 {len(invoice_related_fields)} 个发票相关字段（不应该出现在尺寸检验记录模板中）:")
            for field in invoice_related_fields:
                print(f"  - {field['field_key']} ({field['field_name']})")
        else:
            print("\n✅ 未发现发票相关字段，字段定义正确")

if __name__ == "__main__":
    check_template_fields()

