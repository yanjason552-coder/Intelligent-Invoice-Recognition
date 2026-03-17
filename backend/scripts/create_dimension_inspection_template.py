"""
创建"孔位类"模板的脚本
运行方式: python scripts/create_dimension_inspection_template.py
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select
from app.core.db import engine
from app.models.models_invoice import Template, TemplateField, TemplateVersion
from app.models.models import User
from app.api.routes.template import _parse_nested_json_to_fields, _key_to_field_name
from datetime import datetime
from uuid import uuid4

# 定义字段的详细属性
FIELD_DEFINITIONS = {
    "doc_type": {
        "field_name": "文档类型",
        "data_name": "doc_type",
        "data_type": "string",
        "is_required": True,
        "description": "固定值 dimension_inspection，用于区分表单类型",
        "example": "dimension_inspection"
    },
    "form_title": {
        "field_name": "表单标题",
        "data_name": "form_title",
        "data_type": "string | null",
        "is_required": True,
        "description": "表单标题/名称；图片没有明确出现则为 null",
        "example": None
    },
    "drawing_no": {
        "field_name": "图号/项目号",
        "data_name": "drawing_no",
        "data_type": "string | null",
        "is_required": True,
        "description": "图号/图纸编号/项目号；无则 null",
        "example": None
    },
    "part_name": {
        "field_name": "零件名称",
        "data_name": "part_name",
        "data_type": "string | null",
        "is_required": True,
        "description": "零件名称；无则 null",
        "example": None
    },
    "part_no": {
        "field_name": "零件号/编号",
        "data_name": "part_no",
        "data_type": "string | null",
        "is_required": True,
        "description": "零件号/编号；无则 null",
        "example": None
    },
    "date": {
        "field_name": "日期",
        "data_name": "date",
        "data_type": "string | null",
        "is_required": True,
        "description": "日期；建议 YYYY-MM-DD，无法规范化则保留原字符串；无则 null",
        "example": "2024-01-01"
    },
    "inspector_name": {
        "field_name": "检验员",
        "data_name": "inspector_name",
        "data_type": "string | null",
        "is_required": True,
        "description": "检验员/检验员签字（手写名）；无则 null",
        "example": None
    },
    "overall_result": {
        "field_name": "整单结论",
        "data_name": "overall_result",
        "data_type": "enum",
        "is_required": True,
        "description": "整单结论：pass/fail/unknown（表上无总体结论则 unknown）",
        "example": "unknown"
    },
    "remarks": {
        "field_name": "备注",
        "data_name": "remarks",
        "data_type": "string | null",
        "is_required": True,
        "description": "备注信息（如有）；无则 null",
        "example": None
    },
    "items": {
        "field_name": "明细行列表",
        "data_name": "items",
        "data_type": "array",
        "is_required": True,
        "description": "明细行数组；每个检验项一行；按序号顺序输出",
        "example": []
    },
    "items.item_no": {
        "field_name": "明细序号",
        "data_name": "item_no",
        "data_type": "integer | null",
        "is_required": True,
        "description": "表格序号（如 4、5、6…）；无法识别则 null",
        "example": None
    },
    "items.inspection_item": {
        "field_name": "检验项目",
        "data_name": "inspection_item",
        "data_type": "string | null",
        "is_required": True,
        "description": "检验项目/检验项名称（按表格行标题）",
        "example": None
    },
    "items.spec_requirement": {
        "field_name": "要求/规格",
        "data_name": "spec_requirement",
        "data_type": "string | null",
        "is_required": True,
        "description": "要求/规格；保留符号 φ、±、深/通孔、M 螺纹等",
        "example": None
    },
    "items.actual_value": {
        "field_name": "实际值",
        "data_name": "actual_value",
        "data_type": "string | null",
        "is_required": True,
        "description": "实际值，可能是单值/多测点/角度值/\"OK\"；尽量保留原意与顺序",
        "example": None
    },
    "items.judgement": {
        "field_name": "判定",
        "data_name": "judgement",
        "data_type": "enum",
        "is_required": True,
        "description": "判定：根据合格/不合格勾选框填 pass/fail；不清晰填 unknown",
        "example": "unknown"
    },
    "items.measurements": {
        "field_name": "多测点明细",
        "data_name": "measurements",
        "data_type": "array",
        "is_required": True,
        "description": "可选拆分：若能清晰拆分角度/测点，则填写；否则为空数组 []",
        "example": []
    },
    "items.measurements.angle": {
        "field_name": "角度",
        "data_name": "angle",
        "data_type": "string | null",
        "is_required": True,
        "description": "角度，如 0°/90°/180°；不确定则 null",
        "example": "0°"
    },
    "items.measurements.point_label": {
        "field_name": "测点标签",
        "data_name": "point_label",
        "data_type": "string | null",
        "is_required": True,
        "description": "测点标签，如 A点/B点/上/下/左/右；不确定则 null",
        "example": "A点"
    },
    "items.measurements.value": {
        "field_name": "测点实测值",
        "data_name": "value",
        "data_type": "string | null",
        "is_required": True,
        "description": "该角度/测点对应的实测值（保持原文）",
        "example": None
    },
    "items.notes": {
        "field_name": "行备注",
        "data_name": "notes",
        "data_type": "string | null",
        "is_required": True,
        "description": "该行备注（如有）；无则 null",
        "example": None
    }
}

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


def create_dimension_inspection_template():
    """创建孔位类模板"""
    with Session(engine) as session:
        # 获取第一个用户ID作为creator_id
        first_user = session.exec(select(User)).first()
        creator_id = first_user.id if first_user else None
        
        if not creator_id:
            print("警告: 未找到用户，将尝试使用默认UUID")
            # 如果数据库中没有用户，使用一个默认的UUID（需要确保该UUID在数据库中存在）
            # 或者修改数据库约束允许NULL
            raise ValueError("数据库中不存在用户，请先创建用户或修改数据库约束")
        
        # 检查模板是否已存在（检查"孔位类"和"孔类模板"）
        existing_template = session.exec(
            select(Template).where(
                (Template.name == "孔位类") | (Template.name == "孔类模板")
            )
        ).first()
        
        if existing_template:
            print(f"找到现有模板: {existing_template.name} (ID: {existing_template.id})")
            template_id = existing_template.id
            # 更新模板名称和状态
            existing_template.name = "孔位类"
            existing_template.status = "enabled"
            existing_template.description = "尺寸检验记录模板（Dimension Inspection Record）"
            session.add(existing_template)
            session.commit()
            print("已更新模板名称和状态为 enabled")
        else:
            # 创建模板
            template = Template(
                name="孔位类",
                template_type="其他",
                description="尺寸检验记录模板（Dimension Inspection Record）",
                status="enabled",  # 改为 enabled 状态，确保前端可见
                creator_id=creator_id,
                create_time=datetime.now(),
            )
            session.add(template)
            session.flush()
            template_id = template.id
            print(f"创建模板成功，ID: {template_id}")
        
        # 删除现有版本和字段（如果存在）- 使用原始SQL避免字段不存在的问题
        from sqlalchemy import text
        
        # 先删除字段
        session.exec(
            text("""
                DELETE FROM template_field 
                WHERE template_version_id IN (
                    SELECT id FROM template_version WHERE template_id = :template_id
                )
            """),
            {"template_id": str(template_id)}
        )
        
        # 再删除版本
        session.exec(
            text("DELETE FROM template_version WHERE template_id = :template_id"),
            {"template_id": str(template_id)}
        )
        
        session.commit()
        
        # 创建新版本（使用原始SQL插入，避免字段不存在的问题）
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
        session.commit()
        print(f"创建版本成功，ID: {version_id_new}")
        
        # 更新模板的当前版本
        session.exec(
            text("UPDATE template SET current_version_id = :version_id WHERE id = :template_id"),
            {"version_id": str(version_id_new), "template_id": str(template_id)}
        )
        session.commit()
        
        # 创建版本对象用于后续使用（只设置基本字段）
        version = TemplateVersion(
            id=version_id_new,
            template_id=template_id,
            version="v1.0.0",
            status="draft",
            created_by=creator_id,
            created_at=datetime.now(),
        )
        
        # 解析Schema生成字段定义
        field_definitions = _parse_nested_json_to_fields(SCHEMA_JSON)
        print(f"解析得到 {len(field_definitions)} 个字段定义")
        
        # 创建字段映射
        field_map = {}
        
        # 第一遍：创建所有字段（不设置 parent_field_id）
        for idx, field_def in enumerate(field_definitions):
            if not isinstance(field_def, dict):
                print(f"跳过无效的字段定义: {field_def}")
                continue
            
            field_key = field_def.get("field_key")
            if not field_key:
                print(f"跳过缺少 field_key 的字段定义: {field_def}")
                continue
            
            # 获取字段的详细属性
            field_attrs = FIELD_DEFINITIONS.get(field_key, {})
            
            # 确定数据类型
            data_type = field_def.get("data_type", "string")
            if field_attrs.get("data_type"):
                # 如果定义中有更详细的类型，使用定义中的
                data_type_str = field_attrs["data_type"]
                if "enum" in data_type_str:
                    data_type = "enum"
                elif "array" in data_type_str:
                    data_type = "array"
                elif "integer" in data_type_str:
                    data_type = "integer"
                elif "number" in data_type_str:
                    data_type = "number"
                else:
                    data_type = "string"
            else:
                # 如果没有定义，使用解析出的类型
                data_type = field_def.get("data_type", "string")
            
            # 处理示例值
            example_value = None
            if field_attrs.get("example") is not None:
                example_value = str(field_attrs["example"])
            elif field_def.get("example"):
                example_value = str(field_def["example"])
            
            field = TemplateField(
                template_id=template_id,
                template_version_id=version.id,
                field_key=field_key,
                field_code=field_key,
                field_name=field_attrs.get("field_name") or field_def.get("field_name") or _key_to_field_name(field_key),
                data_name=field_attrs.get("data_name", field_key),
                data_type=data_type,
                field_type=data_type,
                is_required=field_attrs.get("is_required", True),
                required=field_attrs.get("is_required", True),
                description=field_attrs.get("description") or field_def.get("description"),
                example=example_value,
                sort_order=field_def.get("sort_order", idx),
                display_order=field_def.get("sort_order", idx),
            )
            session.add(field)
            session.flush()
            field_map[field_key] = field
            print(f"创建字段: {field_key} ({field.field_name})")
        
        # 第二遍：建立父子关系
        for field_def in field_definitions:
            if not isinstance(field_def, dict):
                continue
            
            field_key = field_def.get("field_key")
            parent_field_key = field_def.get("parent_field_key")
            
            if field_key and field_key in field_map and parent_field_key and parent_field_key in field_map:
                field = field_map[field_key]
                parent_field = field_map[parent_field_key]
                field.parent_field_id = parent_field.id
                session.add(field)
                print(f"建立关系: {field_key} -> {parent_field_key}")
        
        session.commit()
        print(f"\n模板创建完成！")
        print(f"模板ID: {template_id}")
        print(f"版本ID: {version.id}")
        print(f"字段数量: {len(field_map)}")


if __name__ == "__main__":
    try:
        create_dimension_inspection_template()
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

