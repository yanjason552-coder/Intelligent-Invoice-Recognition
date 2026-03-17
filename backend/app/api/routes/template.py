import json
import shutil
import logging
import httpx
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import UUID, uuid4

import openpyxl
from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models.models import Message
from app.models.models_invoice import Template, TemplateField, TemplateVersion, LLMConfig

logger = logging.getLogger(__name__)

# 模板示例文件上传目录
BACKEND_DIR = Path(__file__).parent.parent.parent.parent
TEMPLATE_SAMPLE_DIR = BACKEND_DIR / "uploads" / "templates"
TEMPLATE_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/templates", tags=["templates"])


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
    from sqlalchemy import and_, func
    
    statement = select(Template)
    conditions: list[Any] = []
    if q:
        # 简化：名称/描述模糊匹配（description 可能为空）
        from sqlalchemy import or_
        # 只有当description不为None时才添加description条件
        q_condition = Template.name.contains(q)
        q_condition = q_condition | (
            Template.description.isnot(None) & Template.description.contains(q)
        )
        conditions.append(q_condition)
    if status:
        conditions.append(Template.status == status)
    if template_type:
        conditions.append(Template.template_type == template_type)
    if conditions:
        statement = statement.where(and_(*conditions))

    # 总数
    count_stmt = select(func.count()).select_from(Template)
    if conditions:
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


@router.put("/{template_id}", response_model=Message)
def update_template(
    *,
    session: SessionDep,
    template_id: UUID,
    current_user: CurrentUser,
    body: dict = Body(default_factory=dict),
) -> Any:
    """
    更新模板基本信息及字段
    """
    template = session.get(Template, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 更新模板基本信息
    if "name" in body:
        template.name = body["name"]
    if "template_type" in body:
        template.template_type = body["template_type"]
    if "description" in body:
        template.description = body.get("description")
    if "status" in body:
        template.status = body["status"]
    if "prompt" in body:
        # 更新 prompt 字段（如果模型中有这个字段）
        if hasattr(template, 'prompt'):
            template.prompt = body["prompt"]
    if "schema" in body:
        # 更新 schema 字段（如果模型中有这个字段）
        if hasattr(template, 'schema'):
            template.schema = body["schema"]
    
    # 更新字段（如果提供了fields字段）
    if "fields" in body and isinstance(body["fields"], list):
        try:
            # 确保模板有当前版本
            if not template.current_version_id:
                # 如果没有版本，创建一个新版本
                version = TemplateVersion(
                    template_id=template_id,
                    version="1.0.0",
                    status="draft",
                    creator_id=current_user.id
                )
                session.add(version)
                session.flush()
                template.current_version_id = version.id
            
            # 删除旧字段
            old_fields = session.exec(
                select(TemplateField).where(
                    TemplateField.template_version_id == template.current_version_id
                )
            ).all()
            for old_field in old_fields:
                session.delete(old_field)
            session.flush()  # 确保删除操作完成
            
            # 第一遍：创建所有字段（不设置 parent_field_id）
            # 建立 field_key 到字段对象的映射，用于后续建立 parent_field_id 关系
            field_key_to_field_map: dict[str, TemplateField] = {}
            # 同时建立前端传入的 parent_field_id（可能是临时ID或field_key）到字段的映射
            parent_ref_to_field_map: dict[str, TemplateField] = {}
            
            # 按 sort_order 排序字段，确保父字段在子字段之前
            sorted_fields_data = sorted(body["fields"], key=lambda x: x.get("sort_order", 999999))
            
            logger.info(f"开始保存 {len(sorted_fields_data)} 个字段")
            
            # 先创建所有字段（不设置 parent_field_id）
            for idx, field_data in enumerate(sorted_fields_data):
                try:
                    data_type_value = field_data.get("data_type", "string")
                    sort_order_value = field_data.get("sort_order", idx)
                    field_key = field_data.get("field_key", "")
                    
                    if not field_key:
                        logger.warning(f"跳过没有 field_key 的字段，索引: {idx}")
                        continue
                    
                    field = TemplateField(
                        template_id=template_id,  # 添加必需的 template_id
                        template_version_id=template.current_version_id,
                        field_key=field_key,
                        field_code=field_key,
                        field_name=field_data.get("field_name", "") or "",  # 确保保存 field_name
                        data_type=data_type_value,
                        field_type=data_type_value,  # field_type 是 data_type 的兼容字段，必须设置
                        is_required=field_data.get("is_required", False),
                        required=field_data.get("is_required", False),  # required 是 is_required 的兼容字段
                        description=field_data.get("description"),
                        example=field_data.get("example"),
                        validation=field_data.get("validation"),
                        normalize=field_data.get("normalize"),
                        prompt_hint=field_data.get("prompt_hint"),
                        confidence_threshold=field_data.get("confidence_threshold"),
                        sort_order=sort_order_value,
                        display_order=sort_order_value,  # display_order 必须设置，使用与 sort_order 相同的值
                        parent_field_id=None  # 先不设置，稍后更新
                    )
                    session.add(field)
                    session.flush()  # 刷新以获取字段的数据库ID
                    
                    # 建立映射
                    if field_key:
                        field_key_to_field_map[field_key] = field
                    # 如果前端传入了ID（临时ID），也建立映射
                    if field_data.get("id"):
                        parent_ref_to_field_map[str(field_data.get("id"))] = field
                except Exception as e:
                    logger.error(f"创建字段失败，field_key: {field_data.get('field_key', 'unknown')}, 错误: {str(e)}", exc_info=True)
                    raise
            
            logger.info(f"成功创建 {len(field_key_to_field_map)} 个字段")
            
            # 第二遍：更新 parent_field_id（根据 field_key 或前端传入的ID建立关系）
            parent_relation_count = 0
            for idx, field_data in enumerate(sorted_fields_data):
                try:
                    field_key = field_data.get("field_key", "")
                    parent_ref = field_data.get("parent_field_id")  # 可能是UUID字符串、临时ID或field_key
                    
                    if not parent_ref or not field_key:
                        continue
                    
                    # 查找当前字段
                    current_field = field_key_to_field_map.get(field_key)
                    if not current_field:
                        continue
                    
                    # 尝试通过多种方式查找父字段
                    parent_field = None
                    
                    # 方式1：如果 parent_ref 是 UUID 字符串，尝试直接使用
                    try:
                        parent_uuid = UUID(str(parent_ref))
                        # 在已创建的字段中查找
                        parent_field = next((f for f in field_key_to_field_map.values() if f.id == parent_uuid), None)
                    except (ValueError, TypeError):
                        pass
                    
                    # 方式2：如果 parent_ref 是临时ID，通过映射查找
                    if not parent_field:
                        parent_field = parent_ref_to_field_map.get(str(parent_ref))
                    
                    # 方式3：如果 parent_ref 是 field_key，直接查找
                    if not parent_field:
                        parent_field = field_key_to_field_map.get(str(parent_ref))
                    
                    # 如果找到父字段，设置 parent_field_id
                    if parent_field:
                        current_field.parent_field_id = parent_field.id
                        parent_relation_count += 1
                        logger.debug(f"建立父子关系: {field_key} -> {parent_field.field_key}")
                    else:
                        # 如果找不到，尝试通过 field_key 的前缀匹配（例如：invoice_array.items -> invoice_array）
                        # 这是一个fallback机制，用于处理嵌套字段
                        parent_key_candidates = []
                        if '.' in field_key:
                            # 如果 field_key 包含点号，尝试提取父级
                            parts = field_key.split('.')
                            for i in range(len(parts) - 1):
                                parent_key_candidates.append('.'.join(parts[:i+1]))
                        else:
                            # 检查是否有明显的父字段（例如：items 的子字段应该在 items 数组下）
                            # 这里可以根据业务逻辑添加更多规则
                            pass
                        
                        # 尝试通过候选父字段key查找
                        for candidate_key in parent_key_candidates:
                            candidate_field = field_key_to_field_map.get(candidate_key)
                            if candidate_field:
                                current_field.parent_field_id = candidate_field.id
                                parent_relation_count += 1
                                logger.debug(f"通过前缀匹配建立父子关系: {field_key} -> {candidate_key}")
                                break
                except Exception as e:
                    logger.error(f"更新字段 parent_field_id 失败，field_key: {field_data.get('field_key', 'unknown')}, 错误: {str(e)}", exc_info=True)
                    # 不抛出异常，继续处理其他字段
            
            logger.info(f"成功建立 {parent_relation_count} 个父子关系")
        except Exception as e:
            logger.error(f"保存字段失败: {str(e)}", exc_info=True)
            session.rollback()
            raise HTTPException(status_code=500, detail=f"保存字段失败: {str(e)}")
    
    template.update_time = datetime.now()
    session.add(template)
    session.commit()
    session.refresh(template)
    
    return Message(message="模板更新成功")


@router.get("/{template_id}")
def get_template(
    *,
    session: SessionDep,
    template_id: UUID,
    current_user: CurrentUser,
) -> Any:
    """
    获取模板详情
    前端依赖返回结构：包含模板基本信息和字段列表
    """
    try:
        template = session.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 获取当前版本的字段
        fields = []
        if template.current_version_id:
            try:
                fields = session.exec(
                    select(TemplateField)
                    .where(TemplateField.template_version_id == template.current_version_id)
                    .order_by(TemplateField.sort_order)
                ).all()
                logger.info(f"获取模板 {template_id} 的字段，数量: {len(fields)}")
            except Exception as e:
                logger.error(f"获取字段失败: {str(e)}", exc_info=True)
                fields = []  # 如果获取字段失败，返回空列表
        
        # 获取版本信息
        version = None
        if template.current_version_id:
            try:
                version = session.get(TemplateVersion, template.current_version_id)
            except Exception as e:
                logger.error(f"获取版本信息失败: {str(e)}", exc_info=True)
                version = None
        
        # 构建返回数据
        try:
            response_data = {
                "id": str(template.id),
                "name": template.name,
                "template_type": template.template_type,
                "description": template.description,
                "status": template.status,
                "schema_id": str(template.default_schema_id) if template.default_schema_id else None,
                "default_schema_id": str(template.default_schema_id) if template.default_schema_id else None,
                "sample_file_path": template.sample_file_path,
                "sample_file_type": template.sample_file_type,
                "prompt": getattr(template, 'prompt', None),  # 获取prompt字段
                "schema": getattr(template, 'schema', None),  # 获取schema字段
                "version": {
                    "id": str(version.id),
                    "version": version.version,
                    "status": getattr(version, 'status', None),
                } if version else None,
                "fields": [
                    {
                        "id": str(f.id),
                        "field_key": f.field_key or "",
                        "field_name": f.field_name or "",  # 确保返回 field_name
                        "data_name": f.field_key or "",  # data_name 使用 field_key（因为模型中没有 data_name 字段）
                        "data_type": f.data_type or "string",
                        "is_required": bool(f.is_required) if f.is_required is not None else False,
                        "description": f.description,
                        "example": f.example,
                        "validation": f.validation,
                        "normalize": f.normalize,
                        "prompt_hint": f.prompt_hint,
                        "confidence_threshold": f.confidence_threshold,
                        "parent_field_id": str(f.parent_field_id) if f.parent_field_id else None,  # 确保返回 parent_field_id
                        "sort_order": f.sort_order if f.sort_order is not None else 0,
                    }
                    for f in fields
                ],
                "create_time": template.create_time,
                "update_time": template.update_time,
            }
            
            logger.info(f"成功获取模板 {template_id}，字段数量: {len(response_data['fields'])}")
            return response_data
        except Exception as e:
            logger.error(f"构建返回数据失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"构建返回数据失败: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模板失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")


@router.post("/{template_id}/upload-sample")
async def upload_template_sample(
    *,
    session: SessionDep,
    template_id: UUID,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> Any:
    """
    上传模板示例文件
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # 1. 验证模板是否存在
        template = session.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 2. 验证文件类型
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}，仅支持 PDF、JPG、PNG"
            )
        
        # 3. 验证文件大小（10MB）并读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="文件为空")
        
        # 4. 生成唯一文件名
        file_ext = Path(file.filename).suffix if file.filename else ".pdf"
        unique_filename = f"{uuid4()}{file_ext}"
        file_path = TEMPLATE_SAMPLE_DIR / unique_filename
        
        # 5. 保存文件（直接写入读取的内容）
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 6. 更新模板的示例文件路径
        sample_file_path = f"/uploads/templates/{unique_filename}"
        sample_file_type = file_ext[1:] if file_ext else "pdf"
        
        # 更新模板记录
        template.sample_file_path = sample_file_path
        template.sample_file_type = sample_file_type
        template.update_time = datetime.now()
        session.add(template)
        session.commit()
        session.refresh(template)
        
        return {
            "message": "示例文件上传成功",
            "data": {
                "file_path": sample_file_path,
                "file_type": sample_file_type,
                "file_name": file.filename
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传示例文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.delete("/{template_id}/sample-file")
async def delete_template_sample(
    *,
    session: SessionDep,
    template_id: UUID,
    current_user: CurrentUser,
) -> Any:
    """
    删除模板示例文件
    """
    import logging
    import os
    logger = logging.getLogger(__name__)
    
    try:
        # 1. 验证模板是否存在
        template = session.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 2. 检查是否有示例文件
        if not template.sample_file_path:
            raise HTTPException(status_code=400, detail="模板没有示例文件")
        
        # 3. 构建文件路径
        file_path_str = template.sample_file_path
        # 移除路径前缀 /uploads/templates/
        if file_path_str.startswith('/uploads/templates/'):
            filename = file_path_str.replace('/uploads/templates/', '')
        elif file_path_str.startswith('uploads/templates/'):
            filename = file_path_str.replace('uploads/templates/', '')
        else:
            filename = file_path_str.split('/')[-1]
        
        file_path = TEMPLATE_SAMPLE_DIR / filename
        
        # 4. 删除文件（如果存在）
        if file_path.exists():
            try:
                os.remove(file_path)
                logger.info(f"已删除示例文件: {file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败（文件可能不存在）: {str(e)}")
        
        # 5. 更新模板记录
        template.sample_file_path = None
        template.sample_file_type = None
        template.update_time = datetime.now()
        session.add(template)
        session.commit()
        session.refresh(template)
        
        return {
            "message": "示例文件删除成功",
            "data": {
                "template_id": str(template_id)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除示例文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/{template_id}/extract")
async def extract_fields_and_generate_prompt(
    *,
    session: SessionDep,
    template_id: UUID,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    mode: str = Form("both"),  # both, extract, prompt_only
    field_definitions: str = Form(...),  # JSON string
) -> Any:
    """
    字段抽取和提示词生成接口
    
    支持三种模式：
    - both: 抽取字段值 + 生成提示词（默认）
    - extract: 仅抽取字段值
    - prompt_only: 仅生成提示词
    """
    import logging
    import httpx
    import tempfile
    import os
    
    logger = logging.getLogger(__name__)
    
    try:
        # 验证模板是否存在
        template = session.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 解析字段定义
        try:
            field_defs = json.loads(field_definitions)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"字段定义JSON格式错误: {str(e)}")
        
        # 验证模式
        if mode not in ("both", "extract", "prompt_only"):
            raise HTTPException(status_code=400, detail="模式必须是 both/extract/prompt_only")
        
        # 获取活跃的LLM配置
        llm_config = session.exec(
            select(LLMConfig).where(LLMConfig.is_active == True)
        ).first()
        
        if not llm_config:
            raise HTTPException(status_code=400, detail="未找到活跃的LLM配置，请在系统配置中设置")
        
        if not llm_config.endpoint or not llm_config.api_key:
            raise HTTPException(status_code=400, detail="LLM配置不完整，请检查endpoint和api_key")
        
        # 保存上传的文件到临时目录
        temp_dir = tempfile.mkdtemp()
        temp_file_path = Path(temp_dir) / file.filename
        
        try:
            # 读取文件内容
            file_content = await file.read()
            with open(temp_file_path, "wb") as f:
                f.write(file_content)
            
            # 构建JSON Schema
            json_schema = _build_json_schema_from_fields(field_defs)
            
            # 构建Dify工作流输入
            workflow_inputs = {
                "field_definitions": json.dumps(field_defs, ensure_ascii=False),
                "json_schema": json.dumps(json_schema, ensure_ascii=False),
                "mode": mode,
                "template_name": template.name,
                "template_type": template.template_type or "其他",
            }
            
            # 调用Dify API
            # 注意：Dify的文件上传API仅支持图片，PDF需要先转换为图片或使用文档解析节点
            if file.content_type and file.content_type.startswith("image/"):
                # 图片文件：直接上传到Dify
                dify_result = await _call_dify_workflow_with_image(
                    llm_config=llm_config,
                    image_path=temp_file_path,
                    inputs=workflow_inputs,
                )
            elif file.content_type == "application/pdf":
                # PDF文件：需要特殊处理（转换为图片或使用文档解析）
                # 这里简化处理，直接读取PDF内容作为文本
                dify_result = await _call_dify_workflow_with_pdf(
                    llm_config=llm_config,
                    pdf_path=temp_file_path,
                    inputs=workflow_inputs,
                )
            else:
                raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}")
            
            # 处理Dify返回结果
            if not dify_result.get("success", False):
                error_msg = dify_result.get("error_message", "Dify API调用失败")
                raise HTTPException(status_code=500, detail=f"Dify API错误: {error_msg}")
            
            # 构建返回结果
            result_data = dify_result.get("data", {})
            
            return {
                "data": {
                    "prompt_suggestion": result_data.get("prompt_suggestion", ""),
                    "extracted_data": result_data.get("extracted_data", {}),
                    "field_status": result_data.get("field_status", []),
                    "warnings": result_data.get("warnings", []),
                    "trace_id": result_data.get("trace_id"),
                }
            }
            
        finally:
            # 清理临时文件
            try:
                if temp_file_path.exists():
                    os.remove(temp_file_path)
                os.rmdir(temp_dir)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {str(e)}")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"字段抽取失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"字段抽取失败: {str(e)}")


@router.post("/{template_id}/versions/{version_id}/publish", response_model=Message)
def publish_version(
    *,
    session: SessionDep,
    template_id: UUID,
    version_id: UUID,
    current_user: CurrentUser,
) -> Any:
    """
    发布模板版本
    """
    try:
        # 验证模板是否存在
        template = session.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 验证版本是否存在
        version = session.get(TemplateVersion, version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")
        
        # 验证版本是否属于该模板
        if version.template_id != template_id:
            raise HTTPException(status_code=400, detail="版本不属于该模板")
        
        # 验证版本状态
        if version.status == "published":
            raise HTTPException(status_code=400, detail="版本已发布，无需重复发布")
        
        # 更新版本状态为已发布
        version.status = "published"
        version.published_at = datetime.now()
        
        # 保存Schema快照（如果模板有schema）
        if template.schema:
            version.schema_snapshot = template.schema
        
        # 更新模板的当前版本ID（如果当前版本不是已发布状态，则更新为最新发布的版本）
        if not template.current_version_id or template.current_version_id != version_id:
            # 检查是否有其他已发布的版本
            existing_published = session.exec(
                select(TemplateVersion)
                .where(TemplateVersion.template_id == template_id)
                .where(TemplateVersion.status == "published")
                .where(TemplateVersion.id != version_id)
            ).first()
            
            # 如果没有其他已发布的版本，或者当前版本就是最新版本，则更新当前版本ID
            if not existing_published:
                template.current_version_id = version_id
        
        session.add(version)
        session.add(template)
        session.commit()
        
        logger.info(f"模板 {template_id} 的版本 {version_id} 已发布")
        return Message(message="版本发布成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发布版本失败: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(status_code=500, detail=f"发布版本失败: {str(e)}")


@router.post("/{template_id}/versions/{version_id}/create-draft", response_model=Message)
def create_draft_version(
    *,
    session: SessionDep,
    template_id: UUID,
    version_id: UUID,
    current_user: CurrentUser,
) -> Any:
    """
    基于已发布版本创建新的草稿版本
    """
    try:
        # 验证模板是否存在
        template = session.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 验证版本是否存在
        source_version = session.get(TemplateVersion, version_id)
        if not source_version:
            raise HTTPException(status_code=404, detail="源版本不存在")
        
        # 验证版本是否属于该模板
        if source_version.template_id != template_id:
            raise HTTPException(status_code=400, detail="版本不属于该模板")
        
        # 生成新版本号（简单递增）
        version_parts = source_version.version.split('.')
        if len(version_parts) >= 3:
            major, minor, patch = int(version_parts[0]), int(version_parts[1]), int(version_parts[2])
            new_version = f"{major}.{minor}.{patch + 1}"
        else:
            new_version = f"{source_version.version}.1"
        
        # 创建新版本
        new_version_obj = TemplateVersion(
            template_id=template_id,
            version=new_version,
            status="draft",
            creator_id=current_user.id,
            schema_snapshot=source_version.schema_snapshot  # 复制Schema快照
        )
        session.add(new_version_obj)
        session.flush()
        
        # 复制字段
        source_fields = session.exec(
            select(TemplateField).where(TemplateField.template_version_id == version_id)
        ).all()
        
        field_id_map = {}  # 用于建立parent_field_id关系
        for source_field in source_fields:
            new_field = TemplateField(
                template_id=template_id,
                template_version_id=new_version_obj.id,
                field_key=source_field.field_key,
                field_code=source_field.field_code,
                field_name=source_field.field_name,
                data_type=source_field.data_type,
                field_type=source_field.field_type,
                is_required=source_field.is_required,
                required=source_field.required,
                default_value=source_field.default_value,
                description=source_field.description,
                example=source_field.example,
                validation=source_field.validation,
                validation_rules=source_field.validation_rules,
                normalize=source_field.normalize,
                prompt_hint=source_field.prompt_hint,
                confidence_threshold=source_field.confidence_threshold,
                canonical_field=source_field.canonical_field,
                parent_field_id=None,  # 稍后设置
                deprecated=source_field.deprecated,
                deprecated_at=source_field.deprecated_at,
                position=source_field.position,
                display_order=source_field.display_order,
                sort_order=source_field.sort_order,
                remark=source_field.remark,
            )
            session.add(new_field)
            session.flush()
            field_id_map[source_field.id] = new_field
        
        # 建立parent_field_id关系
        for source_field in source_fields:
            if source_field.parent_field_id:
                new_field = field_id_map.get(source_field.id)
                parent_field = field_id_map.get(source_field.parent_field_id)
                if new_field and parent_field:
                    new_field.parent_field_id = parent_field.id
        
        # 更新模板的当前版本ID
        template.current_version_id = new_version_obj.id
        
        session.add(template)
        session.commit()
        
        logger.info(f"基于版本 {version_id} 创建了新草稿版本 {new_version_obj.id}")
        return Message(message=f"已创建新版本 {new_version}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建草稿版本失败: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建草稿版本失败: {str(e)}")


@router.post("/{template_id}/versions/{version_id}/deprecate", response_model=Message)
def deprecate_version(
    *,
    session: SessionDep,
    template_id: UUID,
    version_id: UUID,
    current_user: CurrentUser,
) -> Any:
    """
    废弃模板版本
    """
    try:
        # 验证模板是否存在
        template = session.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 验证版本是否存在
        version = session.get(TemplateVersion, version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")
        
        # 验证版本是否属于该模板
        if version.template_id != template_id:
            raise HTTPException(status_code=400, detail="版本不属于该模板")
        
        # 更新版本状态为已废弃
        version.status = "deprecated"
        version.deprecated_at = datetime.now()
        
        # 如果当前版本是被废弃的版本，需要更新模板的当前版本ID
        if template.current_version_id == version_id:
            # 查找最新发布的版本
            latest_published = session.exec(
                select(TemplateVersion)
                .where(TemplateVersion.template_id == template_id)
                .where(TemplateVersion.status == "published")
                .order_by(TemplateVersion.published_at.desc())
            ).first()
            
            if latest_published:
                template.current_version_id = latest_published.id
            else:
                # 如果没有已发布的版本，查找最新的草稿版本
                latest_draft = session.exec(
                    select(TemplateVersion)
                    .where(TemplateVersion.template_id == template_id)
                    .where(TemplateVersion.status == "draft")
                    .order_by(TemplateVersion.created_at.desc())
                ).first()
                
                if latest_draft:
                    template.current_version_id = latest_draft.id
                else:
                    template.current_version_id = None
        
        session.add(version)
        session.add(template)
        session.commit()
        
        logger.info(f"模板 {template_id} 的版本 {version_id} 已废弃")
        return Message(message="版本已废弃")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"废弃版本失败: {str(e)}", exc_info=True)
        session.rollback()
        raise HTTPException(status_code=500, detail=f"废弃版本失败: {str(e)}")


@router.post("/{template_id}/generate-prompt")
async def generate_prompt(
    *,
    session: SessionDep,
    template_id: UUID,
    current_user: CurrentUser,
    body: dict = Body(...),
) -> Any:
    """
    根据字段定义生成提示词（调用DIFY API）
    
    请求体：
    {
        "field_definitions": [...],  # 字段定义数组
        "mode": "generate" | "update",  # 模式：generate=生成，update=更新
        "prompt_text": "..."  # 可选，更新模式时需要
    }
    """
    try:
        # 验证模板是否存在（如果template_id不是'new'）
        if str(template_id) != 'new':
            template = session.get(Template, template_id)
            if not template:
                raise HTTPException(status_code=404, detail="模板不存在")
        else:
            template = None
        
        # 获取字段定义
        field_definitions = body.get("field_definitions", [])
        if not field_definitions:
            raise HTTPException(status_code=400, detail="字段定义不能为空")
        
        mode = body.get("mode", "generate")
        prompt_text = body.get("prompt_text", "")
        llm_config_id = body.get("llm_config_id")  # 支持指定llm_config_id
        
        # 获取LLM配置
        if llm_config_id:
            # 如果指定了llm_config_id，使用指定的配置
            try:
                llm_config = session.get(LLMConfig, UUID(llm_config_id))
            except Exception:
                llm_config = None
            if not llm_config:
                raise HTTPException(status_code=400, detail=f"指定的LLM配置不存在: {llm_config_id}")
        else:
            # 否则使用活跃的LLM配置
            llm_config = session.exec(
                select(LLMConfig).where(LLMConfig.is_active == True)
            ).first()
            if not llm_config:
                raise HTTPException(status_code=400, detail="未找到活跃的LLM配置，请在系统配置中设置")
        
        if not llm_config.endpoint or not llm_config.api_key:
            raise HTTPException(status_code=400, detail="LLM配置不完整，请检查endpoint和api_key")
        
        # 构建Dify工作流输入
        workflow_inputs = {
            "field_definitions": json.dumps(field_definitions, ensure_ascii=False),
            "mode": mode,
        }
        
        if template:
            workflow_inputs["template_name"] = template.name
            workflow_inputs["template_type"] = template.template_type or "其他"
        
        if mode == "update" and prompt_text:
            workflow_inputs["prompt_text"] = prompt_text
        
        # 调用Dify工作流API（不需要文件）
        workflow_url = f"{llm_config.endpoint.rstrip('/')}/workflows/run"
        
        workflow_payload = {
            "inputs": workflow_inputs,
            "response_mode": "blocking",
            "user": str(current_user.id),
        }
        
        workflow_headers = {
            "Authorization": f"Bearer {llm_config.api_key}",
            "Content-Type": "application/json",
        }
        
        logger.info(f"调用Dify生成提示词API: {workflow_url}")
        logger.info(f"请求参数: {json.dumps(workflow_payload, ensure_ascii=False, indent=2)}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            workflow_response = await client.post(
                workflow_url,
                json=workflow_payload,
                headers=workflow_headers,
                timeout=120.0,
            )
            
            if workflow_response.status_code != 200:
                error_text = workflow_response.text
                logger.error(f"Dify API调用失败: {workflow_response.status_code}, {error_text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Dify API调用失败: {error_text}"
                )
            
            workflow_result = workflow_response.json()
            
            # 解析工作流输出
            output_data = workflow_result.get("data", {}).get("outputs", {})
            prompt_suggestion = output_data.get("prompt_suggestion", "") or output_data.get("prompt", "")
            
            if not prompt_suggestion:
                # 如果没有prompt_suggestion，尝试从其他字段获取
                prompt_suggestion = output_data.get("result", "") or output_data.get("text", "")
            
            return {
                "success": True,
                "data": {
                    "prompt": prompt_suggestion,
                    "trace_id": workflow_result.get("id"),
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成提示词失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成提示词失败: {str(e)}")


def _build_json_schema_from_fields(field_defs: list[dict]) -> dict:
    """从字段定义构建JSON Schema"""
    properties = {}
    required = []
    
    for field in field_defs:
        key = field.get("key", "")
        data_type = field.get("dataType", "string")
        is_required = field.get("required", False)
        desc = field.get("desc", "")
        example = field.get("example", "")
        
        # 构建字段schema
        field_schema = {
            "type": _map_data_type_to_json_schema_type(data_type),
            "description": desc,
        }
        
        if example:
            field_schema["examples"] = [example]
        
        # 添加格式约束
        if "format" in field and field["format"]:
            field_schema["pattern"] = field["format"]
        
        properties[key] = field_schema
        
        if is_required:
            required.append(key)
    
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _map_data_type_to_json_schema_type(data_type: str) -> str:
    """映射数据类型到JSON Schema类型"""
    mapping = {
        "string": "string",
        "number": "number",
        "date": "string",
        "datetime": "string",
        "boolean": "boolean",
        "enum": "string",
        "object": "object",
        "array": "array",
    }
    return mapping.get(data_type.lower(), "string")


async def _call_dify_workflow_with_image(
    llm_config: LLMConfig,
    image_path: Path,
    inputs: dict,
) -> dict:
    """调用Dify工作流（图片文件）"""
    import httpx
    
    try:
        # 1. 上传文件到Dify
        upload_url = f"{llm_config.endpoint.rstrip('/')}/files/upload"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # 上传文件
            with open(image_path, "rb") as f:
                files = {"file": (image_path.name, f, "image/jpeg")}
                headers = {
                    "Authorization": f"Bearer {llm_config.api_key}",
                }
                upload_response = await client.post(upload_url, files=files, headers=headers)
                
                if upload_response.status_code != 200:
                    return {
                        "success": False,
                        "error_message": f"文件上传失败: {upload_response.text}",
                    }
                
                upload_result = upload_response.json()
                file_id = upload_result.get("id")
                
                if not file_id:
                    return {
                        "success": False,
                        "error_message": "文件上传成功但未返回文件ID",
                    }
            
            # 2. 调用工作流
            workflow_url = f"{llm_config.endpoint.rstrip('/')}/workflows/run"
            
            workflow_inputs = {
                **inputs,
                "file": file_id,  # 使用上传后的文件ID
            }
            
            workflow_payload = {
                "inputs": workflow_inputs,
                "response_mode": "blocking",
                "user": "system",
            }
            
            workflow_headers = {
                "Authorization": f"Bearer {llm_config.api_key}",
                "Content-Type": "application/json",
            }
            
            workflow_response = await client.post(
                workflow_url,
                json=workflow_payload,
                headers=workflow_headers,
                timeout=120.0,
            )
            
            if workflow_response.status_code != 200:
                return {
                    "success": False,
                    "error_message": f"工作流调用失败: {workflow_response.text}",
                }
            
            workflow_result = workflow_response.json()
            
            # 解析工作流输出
            output_data = workflow_result.get("data", {}).get("outputs", {})
            
            return {
                "success": True,
                "data": {
                    "prompt_suggestion": output_data.get("prompt_suggestion", ""),
                    "extracted_data": output_data.get("extracted_data", {}),
                    "field_status": output_data.get("field_status", []),
                    "warnings": output_data.get("warnings", []),
                    "trace_id": workflow_result.get("id"),
                },
            }
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Dify API调用失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error_message": str(e),
        }


async def _call_dify_workflow_with_pdf(
    llm_config: LLMConfig,
    pdf_path: Path,
    inputs: dict,
) -> dict:
    """调用Dify工作流（PDF文件）"""
    # PDF处理：简化实现，实际应该转换为图片或使用文档解析节点
    # 这里返回一个占位实现
    return {
        "success": False,
        "error_message": "PDF文件处理功能待实现，请先使用图片文件",
    }
