"""
导入"孔位类"模板的20个字段到字段属性表
"""
import sys
from pathlib import Path
from uuid import UUID, uuid4
from sqlalchemy import text

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select
from app.core.db import engine
from app.models.models_invoice import Template, TemplateField, TemplateVersion
from datetime import datetime

# 字段定义（按照用户提供的表格）
FIELD_DEFINITIONS = [
    # 顶层字段（1-10）
    {
        "field_key": "doc_type",
        "field_name": "文档类型",
        "data_name": "doc_type",
        "data_type": "string",
        "is_required": True,
        "description": "固定值 dimension_inspection，用于区分表单类型",
        "sort_order": 0,
        "parent_field_id": None
    },
    {
        "field_key": "form_title",
        "field_name": "表单标题",
        "data_name": "form_title",
        "data_type": "string",
        "is_required": True,
        "description": "表单标题/名称；图片没有明确出现则为 null",
        "sort_order": 1,
        "parent_field_id": None
    },
    {
        "field_key": "drawing_no",
        "field_name": "图号/项目号",
        "data_name": "drawing_no",
        "data_type": "string",
        "is_required": True,
        "description": "图号/图纸编号/项目号；无则 null",
        "sort_order": 2,
        "parent_field_id": None
    },
    {
        "field_key": "part_name",
        "field_name": "零件名称",
        "data_name": "part_name",
        "data_type": "string",
        "is_required": True,
        "description": "零件名称；无则 null",
        "sort_order": 3,
        "parent_field_id": None
    },
    {
        "field_key": "part_no",
        "field_name": "零件号/编号",
        "data_name": "part_no",
        "data_type": "string",
        "is_required": True,
        "description": "零件号/编号；无则 null",
        "sort_order": 4,
        "parent_field_id": None
    },
    {
        "field_key": "date",
        "field_name": "日期",
        "data_name": "date",
        "data_type": "string",
        "is_required": True,
        "description": "日期；建议 YYYY-MM-DD，无法规范化则保留原字符串；无则 null",
        "sort_order": 5,
        "parent_field_id": None
    },
    {
        "field_key": "inspector_name",
        "field_name": "检验员",
        "data_name": "inspector_name",
        "data_type": "string",
        "is_required": True,
        "description": "检验员/检验员签字（手写名）；无则 null",
        "sort_order": 6,
        "parent_field_id": None
    },
    {
        "field_key": "overall_result",
        "field_name": "整单结论",
        "data_name": "overall_result",
        "data_type": "enum",
        "is_required": True,
        "description": "整单结论：pass/fail/unknown（表上无总体结论则 unknown）",
        "sort_order": 7,
        "parent_field_id": None
    },
    {
        "field_key": "remarks",
        "field_name": "备注",
        "data_name": "remarks",
        "data_type": "string",
        "is_required": True,
        "description": "备注信息（如有）；无则 null",
        "sort_order": 8,
        "parent_field_id": None
    },
    {
        "field_key": "items",
        "field_name": "明细行列表",
        "data_name": "items",
        "data_type": "array",
        "is_required": True,
        "description": "明细行数组；每个检验项一行；按序号顺序输出",
        "sort_order": 9,
        "parent_field_id": None
    },
    # items[] 子字段（11-17）
    {
        "field_key": "items.item_no",
        "field_name": "明细序号",
        "data_name": "item_no",
        "data_type": "integer",
        "is_required": True,
        "description": "表格序号（如 4、5、6…）；无法识别则 null",
        "sort_order": 10,
        "parent_field_key": "items"  # 临时字段，稍后替换为 parent_field_id
    },
    {
        "field_key": "items.inspection_item",
        "field_name": "检验项目",
        "data_name": "inspection_item",
        "data_type": "string",
        "is_required": True,
        "description": "检验项目/检验项名称（按表格行标题）",
        "sort_order": 11,
        "parent_field_key": "items"
    },
    {
        "field_key": "items.spec_requirement",
        "field_name": "要求/规格",
        "data_name": "spec_requirement",
        "data_type": "string",
        "is_required": True,
        "description": "要求/规格；保留符号 φ、±、深/通孔、M 螺纹等",
        "sort_order": 12,
        "parent_field_key": "items"
    },
    {
        "field_key": "items.actual_value",
        "field_name": "实际值",
        "data_name": "actual_value",
        "data_type": "string",
        "is_required": True,
        "description": "实际值，可能是单值/多测点/角度值/\"OK\"；尽量保留原意与顺序",
        "sort_order": 13,
        "parent_field_key": "items"
    },
    {
        "field_key": "items.judgement",
        "field_name": "判定",
        "data_name": "judgement",
        "data_type": "enum",
        "is_required": True,
        "description": "判定：根据合格/不合格勾选框填 pass/fail；不清晰填 unknown",
        "sort_order": 14,
        "parent_field_key": "items"
    },
    {
        "field_key": "items.measurements",
        "field_name": "多测点明细",
        "data_name": "measurements",
        "data_type": "array",
        "is_required": True,
        "description": "可选拆分：若能清晰拆分角度/测点，则填写；否则为空数组 []",
        "sort_order": 15,
        "parent_field_key": "items"
    },
    {
        "field_key": "items.notes",
        "field_name": "行备注",
        "data_name": "notes",
        "data_type": "string",
        "is_required": True,
        "description": "该行备注（如有）；无则 null",
        "sort_order": 16,
        "parent_field_key": "items"
    },
    # items[].measurements[] 子字段（18-20）
    {
        "field_key": "items.measurements.angle",
        "field_name": "角度",
        "data_name": "angle",
        "data_type": "string",
        "is_required": True,
        "description": "角度，如 0°/90°/180°；不确定则 null",
        "sort_order": 17,
        "parent_field_key": "items.measurements"
    },
    {
        "field_key": "items.measurements.point_label",
        "field_name": "测点标签",
        "data_name": "point_label",
        "data_type": "string",
        "is_required": True,
        "description": "测点标签，如 A点/B点/上/下/左/右；不确定则 null",
        "sort_order": 18,
        "parent_field_key": "items.measurements"
    },
    {
        "field_key": "items.measurements.value",
        "field_name": "测点实测值",
        "data_name": "value",
        "data_type": "string",
        "is_required": True,
        "description": "该角度/测点对应的实测值（保持原文）",
        "sort_order": 19,
        "parent_field_key": "items.measurements"
    },
]


def import_fields_to_template():
    """导入字段到孔位类模板"""
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
        
        # 获取或创建版本
        current_version = None
        if template.current_version_id:
            # 使用原始 SQL 查询，避免 prompt 列不存在的问题
            version_result = session.execute(
                text("""
                    SELECT id, template_id, version, status, created_by, created_at
                    FROM template_version
                    WHERE id = :version_id
                """),
                {"version_id": str(template.current_version_id)}
            ).first()
            
            if version_result:
                # 手动构建版本对象
                current_version = TemplateVersion(
                    id=version_result[0],
                    template_id=version_result[1],
                    version=version_result[2],
                    status=version_result[3],
                    created_by=version_result[4],
                    created_at=version_result[5]
                )
            
            if current_version and current_version.status != "draft":
                print(f"⚠️  当前版本状态为 {current_version.status}，需要创建新版本")
                # 创建新版本
                version_id_new = uuid4()
                try:
                    session.execute(
                        text("""
                            INSERT INTO template_version (id, template_id, version, status, created_by, created_at)
                            VALUES (:id, :template_id, :version, :status, :created_by, :created_at)
                        """),
                        {
                            "id": str(version_id_new),
                            "template_id": str(template.id),
                            "version": f"v{current_version.version.split('.')[0]}.{int(current_version.version.split('.')[1]) + 1}.0",
                            "status": "draft",
                            "created_by": str(current_version.created_by),
                            "created_at": datetime.now()
                        }
                    )
                    session.flush()
                    template.current_version_id = version_id_new
                    session.add(template)
                    session.flush()
                    # 使用原始 SQL 查询新创建的版本
                    version_result = session.execute(
                        text("""
                            SELECT id, template_id, version, status, created_by, created_at
                            FROM template_version
                            WHERE id = :version_id
                        """),
                        {"version_id": str(version_id_new)}
                    ).first()
                    if version_result:
                        current_version = TemplateVersion(
                            id=version_result[0],
                            template_id=version_result[1],
                            version=version_result[2],
                            status=version_result[3],
                            created_by=version_result[4],
                            created_at=version_result[5]
                        )
                        print(f"✅ 创建新版本: {current_version.version}")
                except Exception as e:
                    print(f"❌ 创建版本失败: {e}")
                    session.rollback()
                    return
        else:
            # 创建新版本
            version_id_new = uuid4()
            # 获取第一个用户作为创建者
            from app.models.models_invoice import User
            first_user = session.exec(select(User)).first()
            if not first_user:
                print("❌ 未找到用户，无法创建版本")
                return
            
            try:
                session.execute(
                    text("""
                        INSERT INTO template_version (id, template_id, version, status, created_by, created_at)
                        VALUES (:id, :template_id, :version, :status, :created_by, :created_at)
                    """),
                    {
                        "id": str(version_id_new),
                        "template_id": str(template.id),
                        "version": "v1.0.0",
                        "status": "draft",
                        "created_by": str(first_user.id),
                        "created_at": datetime.now()
                    }
                )
                session.flush()
                template.current_version_id = version_id_new
                session.add(template)
                session.flush()
                # 使用原始 SQL 查询新创建的版本
                version_result = session.execute(
                    text("""
                        SELECT id, template_id, version, status, created_by, created_at
                        FROM template_version
                        WHERE id = :version_id
                    """),
                    {"version_id": str(version_id_new)}
                ).first()
                if version_result:
                    current_version = TemplateVersion(
                        id=version_result[0],
                        template_id=version_result[1],
                        version=version_result[2],
                        status=version_result[3],
                        created_by=version_result[4],
                        created_at=version_result[5]
                    )
                    print(f"✅ 创建新版本: {current_version.version}")
            except Exception as e:
                print(f"❌ 创建版本失败: {e}")
                session.rollback()
                return
        
        # 删除现有字段
        existing_fields = session.exec(
            select(TemplateField).where(
                TemplateField.template_version_id == current_version.id
            )
        ).all()
        deleted_count = 0
        for field in existing_fields:
            session.delete(field)
            deleted_count += 1
        session.flush()
        if deleted_count > 0:
            print(f"🗑️  删除 {deleted_count} 个现有字段")
        
        # 创建字段映射（用于建立父子关系）
        field_map = {}  # key: field_key, value: TemplateField
        
        # 第一遍：创建所有字段（不设置 parent_field_id）
        created_fields = []
        for field_def in FIELD_DEFINITIONS:
            parent_field_id = None
            if "parent_field_id" in field_def and field_def["parent_field_id"]:
                parent_field_id = field_def["parent_field_id"]
            
            field = TemplateField(
                template_id=template.id,
                template_version_id=current_version.id,
                field_key=field_def["field_key"],
                field_code=field_def["field_key"],
                field_name=field_def["field_name"],
                data_name=field_def.get("data_name"),
                data_type=field_def["data_type"],
                field_type=field_def["data_type"],
                is_required=field_def["is_required"],
                required=field_def["is_required"],
                description=field_def.get("description"),
                sort_order=field_def["sort_order"],
                display_order=field_def["sort_order"],
                parent_field_id=parent_field_id
            )
            session.add(field)
            session.flush()
            field_map[field_def["field_key"]] = field
            created_fields.append((field, field_def))
            print(f"✅ 创建字段: {field_def['field_key']} ({field_def['field_name']})")
        
        # 第二遍：建立父子关系
        updated_count = 0
        for field, field_def in created_fields:
            if "parent_field_key" in field_def and field_def["parent_field_key"]:
                parent_field = field_map.get(field_def["parent_field_key"])
                if parent_field:
                    field.parent_field_id = parent_field.id
                    session.add(field)
                    updated_count += 1
                    print(f"🔗 建立关系: {field_def['field_key']} -> {field_def['parent_field_key']}")
        
        session.commit()
        print(f"\n✅ 成功导入 {len(FIELD_DEFINITIONS)} 个字段")
        print(f"✅ 建立了 {updated_count} 个父子关系")
        print(f"✅ 模板版本: {current_version.version} (ID: {current_version.id})")


if __name__ == "__main__":
    import_fields_to_template()

