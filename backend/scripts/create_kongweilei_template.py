"""
快速创建"孔位类"模板的脚本
使用方法：在项目根目录运行 python backend/scripts/create_kongweilei_template.py
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
if os.path.exists(backend_dir):
    os.chdir(backend_dir)

from sqlmodel import Session, select, text
from app.core.db import engine
from app.models.models_invoice import Template, TemplateField, TemplateVersion
from app.models.models import User
from app.api.routes.template import _parse_nested_json_to_fields, _key_to_field_name
from datetime import datetime
from uuid import uuid4
import json

# Schema JSON结构
SCHEMA_JSON = {
    "doc_type": "dimension_inspection",
    "form_title": None,
    "drawing_no": None,
    "part_name": None,
    "part_no": None,
    "date": None,
    "inspector_name": None,
    "overall_result": "unknown",
    "remarks": None,
    "items": [
        {
            "item_no": None,
            "inspection_item": None,
            "spec_requirement": None,
            "actual_value": None,
            "judgement": "unknown",
            "measurements": [
                {
                    "angle": None,
                    "point_label": None,
                    "value": None
                }
            ],
            "notes": None
        }
    ]
}

def create_template():
    """创建或更新孔位类模板"""
    with Session(engine) as session:
        # 获取第一个用户
        first_user = session.exec(select(User)).first()
        if not first_user:
            print("错误: 数据库中不存在用户，请先创建用户")
            return
        creator_id = first_user.id
        print(f"使用用户ID: {creator_id}")
        
        # 检查模板是否存在（检查"孔类模板"和"孔位类"）
        existing_template = session.exec(
            select(Template).where(
                (Template.name == "孔位类") | (Template.name == "孔类模板")
            )
        ).first()
        
        template_id = None
        if existing_template:
            print(f"找到现有模板: {existing_template.name} (ID: {existing_template.id})")
            template_id = existing_template.id
            # 更新模板名称和状态
            existing_template.name = "孔位类"
            existing_template.status = "enabled"
            existing_template.description = "尺寸检验记录模板（Dimension Inspection Record）"
            session.add(existing_template)
            session.commit()
            print("已更新模板名称和状态")
        else:
            # 创建新模板
            template = Template(
                name="孔位类",
                template_type="其他",
                description="尺寸检验记录模板（Dimension Inspection Record）",
                status="enabled",
                creator_id=creator_id,
                create_time=datetime.now(),
            )
            session.add(template)
            session.flush()
            template_id = template.id
            print(f"创建新模板成功，ID: {template_id}")
        
        # 删除现有版本和字段
        session.exec(
            text("DELETE FROM template_field WHERE template_version_id IN (SELECT id FROM template_version WHERE template_id = :template_id)"),
            {"template_id": str(template_id)}
        )
        session.exec(
            text("DELETE FROM template_version WHERE template_id = :template_id"),
            {"template_id": str(template_id)}
        )
        session.commit()
        print("已删除旧版本和字段")
        
        # 创建新版本
        version_id_new = uuid4()
        session.exec(
            text("""
                INSERT INTO template_version (id, template_id, version, status, created_by, created_at)
                VALUES (:id, :template_id, :version, :status, :created_by, :created_at)
            """),
            {
                "id": str(version_id_new),
                "template_id": str(template_id),
                "version": "v1.0.0",
                "status": "draft",
                "created_by": str(creator_id),
                "created_at": datetime.now()
            }
        )
        session.exec(
            text("UPDATE template SET current_version_id = :version_id WHERE id = :template_id"),
            {"version_id": str(version_id_new), "template_id": str(template_id)}
        )
        session.commit()
        print(f"创建版本成功，ID: {version_id_new}")
        
        # 解析Schema并创建字段
        field_definitions = _parse_nested_json_to_fields(SCHEMA_JSON)
        print(f"解析得到 {len(field_definitions)} 个字段定义")
        
        # 字段详细属性映射
        FIELD_ATTRS = {
            "doc_type": {"field_name": "文档类型", "description": "固定值 dimension_inspection，用于区分表单类型", "example": "dimension_inspection"},
            "form_title": {"field_name": "表单标题", "description": "表单标题/名称；图片没有明确出现则为 null"},
            "drawing_no": {"field_name": "图号/项目号", "description": "图号/图纸编号/项目号；无则 null"},
            "part_name": {"field_name": "零件名称", "description": "零件名称；无则 null"},
            "part_no": {"field_name": "零件号/编号", "description": "零件号/编号；无则 null"},
            "date": {"field_name": "日期", "description": "日期；建议 YYYY-MM-DD，无法规范化则保留原字符串；无则 null", "example": "2024-01-01"},
            "inspector_name": {"field_name": "检验员", "description": "检验员/检验员签字（手写名）；无则 null"},
            "overall_result": {"field_name": "整单结论", "description": "整单结论：pass/fail/unknown（表上无总体结论则 unknown）", "example": "unknown"},
            "remarks": {"field_name": "备注", "description": "备注信息（如有）；无则 null"},
            "items": {"field_name": "明细行列表", "description": "明细行数组；每个检验项一行；按序号顺序输出"},
            "items.item_no": {"field_name": "明细序号", "description": "表格序号（如 4、5、6…）；无法识别则 null"},
            "items.inspection_item": {"field_name": "检验项目", "description": "检验项目/检验项名称（按表格行标题）"},
            "items.spec_requirement": {"field_name": "要求/规格", "description": "要求/规格；保留符号 φ、±、深/通孔、M 螺纹等"},
            "items.actual_value": {"field_name": "实际值", "description": "实际值，可能是单值/多测点/角度值/\"OK\"；尽量保留原意与顺序"},
            "items.judgement": {"field_name": "判定", "description": "判定：根据合格/不合格勾选框填 pass/fail；不清晰填 unknown", "example": "unknown"},
            "items.measurements": {"field_name": "多测点明细", "description": "可选拆分：若能清晰拆分角度/测点，则填写；否则为空数组 []"},
            "items.measurements.angle": {"field_name": "角度", "description": "角度，如 0°/90°/180°；不确定则 null", "example": "0°"},
            "items.measurements.point_label": {"field_name": "测点标签", "description": "测点标签，如 A点/B点/上/下/左/右；不确定则 null", "example": "A点"},
            "items.measurements.value": {"field_name": "测点实测值", "description": "该角度/测点对应的实测值（保持原文）"},
            "items.notes": {"field_name": "行备注", "description": "该行备注（如有）；无则 null"},
        }
        
        field_map = {}
        for idx, field_def in enumerate(field_definitions):
            if not isinstance(field_def, dict):
                continue
            field_key = field_def.get("field_key")
            if not field_key:
                continue
            
            attrs = FIELD_ATTRS.get(field_key, {})
            data_type = field_def.get("data_type", "string")
            if "enum" in str(attrs.get("data_type", "")):
                data_type = "enum"
            elif "array" in str(attrs.get("data_type", "")):
                data_type = "array"
            elif "integer" in str(attrs.get("data_type", "")):
                data_type = "integer"
            
            field = TemplateField(
                template_id=template_id,
                template_version_id=version_id_new,
                field_key=field_key,
                field_code=field_key,
                field_name=attrs.get("field_name") or _key_to_field_name(field_key),
                data_name=field_key,
                data_type=data_type,
                field_type=data_type,
                is_required=True,
                required=True,
                description=attrs.get("description"),
                example=str(attrs.get("example")) if attrs.get("example") else None,
                sort_order=idx,
                display_order=idx,
            )
            session.add(field)
            session.flush()
            field_map[field_key] = field
        
        # 建立父子关系
        for field_def in field_definitions:
            if not isinstance(field_def, dict):
                continue
            field_key = field_def.get("field_key")
            parent_field_key = field_def.get("parent_field_key")
            if field_key in field_map and parent_field_key in field_map:
                field_map[field_key].parent_field_id = field_map[parent_field_key].id
                session.add(field_map[field_key])
        
        session.commit()
        print(f"\n模板创建完成！")
        print(f"模板ID: {template_id}")
        print(f"版本ID: {version_id_new}")
        print(f"字段数量: {len(field_map)}")

if __name__ == "__main__":
    import os
    try:
        create_template()
    except Exception as e:
        import traceback
        print(f"错误: {str(e)}")
        traceback.print_exc()

