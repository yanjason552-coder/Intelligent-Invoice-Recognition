"""
检查"孔位类"模板的字段数量
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select
from app.core.db import engine
from app.models.models_invoice import Template, TemplateField

def check_fields_count():
    """检查孔位类模板的字段数量"""
    with Session(engine) as session:
        # 查找模板
        template = session.exec(
            select(Template).where(
                (Template.name == "孔位类") | (Template.name == "孔类模板")
            )
        ).first()
        
        if not template:
            print("❌ 未找到'孔位类'或'孔类模板'")
            return
        
        print(f"✅ 找到模板: {template.name} (ID: {template.id})")
        print(f"当前版本ID: {template.current_version_id}")
        
        if not template.current_version_id:
            print("❌ 模板没有当前版本")
            return
        
        # 查询字段
        fields = session.exec(
            select(TemplateField)
            .where(TemplateField.template_version_id == template.current_version_id)
            .order_by(TemplateField.sort_order)
        ).all()
        
        print(f"\n字段总数: {len(fields)}")
        print("\n字段列表:")
        print("-" * 120)
        print(f"{'序号':<6} {'字段标识':<35} {'字段名称':<25} {'数据类型':<15} {'父字段ID':<40} {'sort_order':<10}")
        print("-" * 120)
        
        for idx, field in enumerate(fields, 1):
            parent_info = f"{field.parent_field_id}" if field.parent_field_id else "无"
            print(f"{idx:<6} {field.field_key:<35} {field.field_name:<25} {field.data_type:<15} {parent_info:<40} {field.sort_order:<10}")
        
        print("-" * 120)
        
        # 统计
        top_level_fields = [f for f in fields if not f.parent_field_id]
        nested_fields = [f for f in fields if f.parent_field_id]
        
        print(f"\n统计:")
        print(f"  顶层字段: {len(top_level_fields)} 个")
        print(f"  嵌套字段: {len(nested_fields)} 个")
        print(f"  总计: {len(fields)} 个")
        
        if len(fields) < 20:
            print(f"\n⚠️  字段数量不足20个，可能需要运行导入脚本")

if __name__ == "__main__":
    check_fields_count()

