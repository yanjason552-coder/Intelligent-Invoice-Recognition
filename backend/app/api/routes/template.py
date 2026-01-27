import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

import openpyxl
from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models.models import Message
from app.models.models_invoice import Template, TemplateField, TemplateVersion

router = APIRouter(prefix="/templates", tags=["templates"])


def _normalize_bool(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y", "是", "必填", "required")


def _normalize_str(v: Any) -> str:
    return ("" if v is None else str(v)).strip()


def _safe_template_status(status: Optional[str]) -> str:
    if not status:
        return "enabled"
    if status not in ("enabled", "disabled", "deprecated"):
        raise HTTPException(status_code=400, detail="模板状态必须是 enabled/disabled/deprecated")
    return status


def _safe_data_type(dt: Optional[str]) -> str:
    if not dt:
        return "string"
    dt = dt.strip().lower()
    allowed = {"string", "number", "date", "datetime", "boolean", "enum", "object", "array"}
    return dt if dt in allowed else "string"


@router.get("")
@router.get("/")
def list_templates(
    *,
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
    q: str | None = None,
    status: str | None = None,
    template_type: str | None = None,
    current_user: CurrentUser,
) -> Any:
    """
    获取模板列表（分页）
    前端依赖返回结构：{ data: [...], count: number, skip, limit }
    """
    statement = select(Template)
    conditions: list[Any] = []
    if q:
        # 简化：名称/描述模糊匹配（description 可能为空）
        conditions.append((Template.name.contains(q)) | (Template.description.contains(q)))
    if status:
        conditions.append(Template.status == status)
    if template_type:
        conditions.append(Template.template_type == template_type)
    if conditions:
        from sqlalchemy import and_

        statement = statement.where(and_(*conditions))

    # 总数
    from sqlalchemy import func

    count_stmt = select(func.count()).select_from(Template)
    if conditions:
        from sqlalchemy import and_

        count_stmt = count_stmt.where(and_(*conditions))
    total = session.exec(count_stmt).one()

    templates = session.exec(
        statement.order_by(Template.create_time.desc()).offset(skip).limit(limit)
    ).all()

    # 批量补齐 current_version 字符串
    version_ids = [t.current_version_id for t in templates if t.current_version_id]
    version_map: dict[UUID, TemplateVersion] = {}
    if version_ids:
        versions = session.exec(select(TemplateVersion).where(TemplateVersion.id.in_(version_ids))).all()
        version_map = {v.id: v for v in versions}

    data = []
    for t in templates:
        v = version_map.get(t.current_version_id) if t.current_version_id else None
        data.append(
            {
                "id": str(t.id),
                "name": t.name,
                "template_type": t.template_type,
                "description": t.description,
                "status": t.status,
                "schema_id": str(t.default_schema_id) if t.default_schema_id else None,
                "default_schema_id": str(t.default_schema_id) if t.default_schema_id else None,
                "current_version": v.version if v else None,
                "accuracy": t.accuracy,
                "create_time": t.create_time,
                "update_time": t.update_time,
            }
        )

    return {"data": data, "count": int(total), "skip": skip, "limit": limit}


@router.get("/{template_id}")
def get_template_detail(
    *,
    session: SessionDep,
    template_id: UUID,
    current_user: CurrentUser,
) -> Any:
    template = session.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 选取当前版本（若为空则取最新 created_at）
    version: TemplateVersion | None = None
    if template.current_version_id:
        version = session.get(TemplateVersion, template.current_version_id)
    if not version:
        version = session.exec(
            select(TemplateVersion)
            .where(TemplateVersion.template_id == template_id)
            .order_by(TemplateVersion.created_at.desc())
        ).first()

    fields = []
    if version:
        fields = session.exec(
            select(TemplateField)
            .where(TemplateField.template_version_id == version.id)
            .order_by(TemplateField.sort_order)
        ).all()

    return {
        "id": str(template.id),
        "name": template.name,
        "template_type": template.template_type,
        "description": template.description,
        "status": template.status,
        "accuracy": template.accuracy,
        "schema_id": str(template.default_schema_id) if template.default_schema_id else None,
        "default_schema_id": str(template.default_schema_id) if template.default_schema_id else None,
        "version": {
            "id": str(version.id) if version else None,
            "version": version.version if version else None,
            "status": version.status if version else None,
            "schema_snapshot": version.schema_snapshot if version else None,
            "created_at": version.created_at.isoformat() if version and version.created_at else None,
            "published_at": version.published_at.isoformat() if version and version.published_at else None,
        },
        "fields": [
            {
                "id": str(f.id),
                "field_key": f.field_key,
                "field_name": f.field_name,
                "data_type": f.data_type,
                "is_required": f.is_required,
                "description": f.description,
                "example": f.example,
                "validation": f.validation,
                "normalize": f.normalize,
                "prompt_hint": f.prompt_hint,
                "confidence_threshold": f.confidence_threshold,
                "sort_order": f.sort_order,
                "parent_field_id": str(f.parent_field_id) if f.parent_field_id else None,
            }
            for f in fields
        ],
        "create_time": template.create_time.isoformat() if template.create_time else None,
        "update_time": template.update_time.isoformat() if template.update_time else None,
    }


@router.get("/versions/{version_id}/fields")
def get_template_fields_by_version(
    *,
    session: SessionDep,
    version_id: UUID,
    current_user: CurrentUser,
) -> Any:
    version = session.get(TemplateVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    fields = session.exec(
        select(TemplateField)
        .where(TemplateField.template_version_id == version_id)
        .order_by(TemplateField.sort_order)
    ).all()

    return {
        "version_id": str(version_id),
        "template_id": str(version.template_id),
        "version": version.version,
        "fields": [
            {
                "id": str(f.id),
                "field_key": f.field_key,
                "field_name": f.field_name,
                "data_type": f.data_type,
                "is_required": f.is_required,
                "description": f.description,
                "example": f.example,
                "validation": f.validation,
                "normalize": f.normalize,
                "prompt_hint": f.prompt_hint,
                "confidence_threshold": f.confidence_threshold,
                "sort_order": f.sort_order,
                "parent_field_id": str(f.parent_field_id) if f.parent_field_id else None,
            }
            for f in fields
        ],
    }


@router.post("")
@router.post("/")
def create_template(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: dict = Body(default_factory=dict),
) -> Any:
    """
    创建模板（最小实现）
    前端依赖返回：{ data: { template_id } }
    """
    payload = body or {}
    name = _normalize_str(payload.get("name"))
    template_type = _normalize_str(payload.get("template_type")) or "其他"
    description = payload.get("description")
    status = _safe_template_status(payload.get("status"))
    if not name:
        raise HTTPException(status_code=400, detail="模板名称不能为空")

    # 处理 schema_id 字段
    default_schema_id = None
    if "schema_id" in payload:
        schema_id = payload.get("schema_id")
        if schema_id:
            from app.models.models_invoice import OutputSchema
            schema = session.get(OutputSchema, UUID(schema_id) if isinstance(schema_id, str) else schema_id)
            if not schema:
                raise HTTPException(status_code=400, detail="Schema不存在")
            default_schema_id = schema.id
    elif "default_schema_id" in payload:
        schema_id = payload.get("default_schema_id")
        if schema_id:
            from app.models.models_invoice import OutputSchema
            schema = session.get(OutputSchema, UUID(schema_id) if isinstance(schema_id, str) else schema_id)
            if not schema:
                raise HTTPException(status_code=400, detail="Schema不存在")
            default_schema_id = schema.id

    now = datetime.now()
    template = Template(
        id=uuid4(),
        name=name,
        template_type=template_type,
        description=description,
        status=status,
        default_schema_id=default_schema_id,
        # 注意：current_version_id 有外键约束指向 template_version.id，
        # 不能在首次 INSERT template 时就赋值一个尚不存在的版本ID，否则会触发 FK violation。
        # 这里先插入 template（current_version_id = NULL），再插入 version，最后回写 current_version_id。
        current_version_id=None,
        creator_id=current_user.id,
        create_time=now,
        update_time=None,
    )
    session.add(template)
    session.flush()

    version = TemplateVersion(
        id=uuid4(),
        template_id=template.id,
        version="v1.0.0",
        status="draft",
        schema_snapshot=None,
        accuracy=None,
        etag=None,
        locked_by=None,
        locked_at=None,
        created_by=current_user.id,
        created_at=now,
        published_at=None,
        deprecated_at=None,
    )
    session.add(version)
    session.flush()

    template.current_version_id = version.id
    session.add(template)
    session.commit()

    return {
        "message": "模板创建成功",
        "data": {
            "template_id": str(template.id),
            "template_name": template.name,
            "version_id": str(version.id),
            "version": version.version,
        },
    }


@router.put("/{template_id}")
def update_template(
    *,
    session: SessionDep,
    template_id: UUID,
    current_user: CurrentUser,
    body: dict = Body(default_factory=dict),
) -> Any:
    """
    更新模板基本信息
    """
    template = session.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    payload = body or {}
    if "name" in payload:
        template.name = _normalize_str(payload["name"])
        if not template.name:
            raise HTTPException(status_code=400, detail="模板名称不能为空")
    if "template_type" in payload:
        template.template_type = _normalize_str(payload["template_type"]) or "其他"
    if "description" in payload:
        template.description = payload.get("description")
    if "status" in payload:
        template.status = _safe_template_status(payload["status"])
    
    # 处理 schema_id 字段（前端可能发送 schema_id，需要映射到 default_schema_id）
    if "schema_id" in payload:
        schema_id = payload.get("schema_id")
        if schema_id:
            # 验证 schema 是否存在
            from app.models.models_invoice import OutputSchema
            schema = session.get(OutputSchema, UUID(schema_id) if isinstance(schema_id, str) else schema_id)
            if not schema:
                raise HTTPException(status_code=400, detail="Schema不存在")
            template.default_schema_id = schema.id
        else:
            template.default_schema_id = None
    elif "default_schema_id" in payload:
        schema_id = payload.get("default_schema_id")
        if schema_id:
            from app.models.models_invoice import OutputSchema
            schema = session.get(OutputSchema, UUID(schema_id) if isinstance(schema_id, str) else schema_id)
            if not schema:
                raise HTTPException(status_code=400, detail="Schema不存在")
            template.default_schema_id = schema.id
        else:
            template.default_schema_id = None

    template.update_time = datetime.now()
    session.add(template)
    session.commit()

    return Message(message="模板更新成功")


@router.delete("/{template_id}")
def delete_template(
    *,
    session: SessionDep,
    template_id: UUID,
    current_user: CurrentUser,
) -> Message:
    template = session.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    session.delete(template)
    session.commit()
    return Message(message="模板已删除")


@router.post("/{template_id}/import")
async def import_template(
    *,
    session: SessionDep,
    template_id: UUID,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> Any:
    """
    导入模板配置（Excel）
    """
    # TODO: 实现 Excel 导入逻辑
    raise HTTPException(status_code=501, detail="导入功能开发中")


@router.get("/{template_id}/export")
def export_template(
    *,
    session: SessionDep,
    template_id: UUID,
    current_user: CurrentUser,
) -> Any:
    """
    导出模板配置（Excel）
    """
    # TODO: 实现 Excel 导出逻辑
    raise HTTPException(status_code=501, detail="导出功能开发中")

