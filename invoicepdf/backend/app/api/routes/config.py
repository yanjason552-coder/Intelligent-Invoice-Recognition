from typing import Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func
from datetime import datetime
import json
import logging

from app.api.deps import SessionDep, CurrentUser
from app.models import Message
from app.models.models_invoice import OCRConfig, LLMConfig, RecognitionRule, OutputSchema, Template, TemplateVersion
from sqlalchemy import JSON

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])


# ==================== 大模型配置接口 ====================

@router.get("/llm")
def get_llm_config(
    *,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    获取大模型配置（默认配置）
    """
    try:
        # 获取默认配置
        config = session.exec(
            select(LLMConfig).where(LLMConfig.is_default == True, LLMConfig.is_active == True)
        ).first()
        
        if config:
            return {
                "id": str(config.id),
                "name": config.name,
                "endpoint": config.endpoint,
                "api_key": config.api_key,  # 注意：实际使用时应该脱敏
                "app_id": config.app_id,
                "workflow_id": config.workflow_id,
                "app_type": config.app_type,
                "timeout": config.timeout,
                "max_retries": config.max_retries,
                "is_active": config.is_active,
                "description": config.description
            }
        else:
            # 返回空配置（需要用户配置）
            return {
                "id": None,
                "name": "",
                "endpoint": "",
                "api_key": "",
                "app_id": "",
                "workflow_id": "",
                "app_type": "workflow",
                "timeout": 300,
                "max_retries": 3,
                "is_active": True,
                "description": ""
            }
    except Exception as e:
        # 如果表不存在或其他数据库错误，返回空配置而不是抛出错误
        logger.warning(f"获取LLM配置失败（可能是表不存在）: {str(e)}")
        # 返回空配置（需要用户配置）
        return {
            "id": None,
            "name": "",
            "endpoint": "",
            "api_key": "",
            "app_id": "",
            "workflow_id": "",
            "app_type": "workflow",
            "timeout": 300,
            "max_retries": 3,
            "is_active": True,
            "description": ""
        }


@router.post("/llm", response_model=Message)
def update_llm_config(
    *,
    session: SessionDep,
    config: dict,
    current_user: CurrentUser
) -> Any:
    """
    更新大模型配置
    """
    try:
        # 验证配置数据
        required_fields = ["name", "endpoint", "api_key"]
        for field in required_fields:
            if field not in config or not config[field]:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")
        
        # 验证endpoint格式
        endpoint = config.get("endpoint", "").strip()
        if not endpoint.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="endpoint必须是有效的URL（以http://或https://开头）")
        
        # 验证app_type
        app_type = config.get("app_type", "workflow")
        if app_type not in ["chat", "workflow", "completion"]:
            raise HTTPException(status_code=400, detail="app_type必须是chat、workflow或completion之一")
        
        # 如果设置为默认，先取消其他默认配置
        if config.get("is_default", False):
            existing_defaults = session.exec(
                select(LLMConfig).where(LLMConfig.is_default == True)
            ).all()
            for default_config in existing_defaults:
                default_config.is_default = False
                session.add(default_config)
        
        # 查找或创建配置
        config_id = config.get("id")
        llm_config_obj = None
        shared_id = None  # 用于保持两个表的 id 一致
        
        if config_id:
            existing_config = session.get(LLMConfig, UUID(config_id))
            if not existing_config:
                raise HTTPException(status_code=404, detail="配置不存在")
            
            # 更新配置
            existing_config.name = config["name"]
            existing_config.endpoint = endpoint
            existing_config.api_key = config["api_key"]
            existing_config.app_id = config.get("app_id")
            existing_config.workflow_id = config.get("workflow_id")
            existing_config.app_type = app_type
            existing_config.timeout = config.get("timeout", 300)
            existing_config.max_retries = config.get("max_retries", 3)
            existing_config.is_active = config.get("is_active", True)
            existing_config.is_default = config.get("is_default", False)
            existing_config.description = config.get("description")
            existing_config.update_time = datetime.now()
            existing_config.updater_id = current_user.id
            session.add(existing_config)
            llm_config_obj = existing_config
            shared_id = existing_config.id  # 使用现有的 ID
        else:
            # 创建新配置 - 先生成共享的 UUID
            shared_id = uuid4()
            new_config = LLMConfig(
                id=shared_id,  # 使用共享的 ID
                name=config["name"],
                endpoint=endpoint,
                api_key=config["api_key"],
                app_id=config.get("app_id"),
                workflow_id=config.get("workflow_id"),
                app_type=app_type,
                timeout=config.get("timeout", 300),
                max_retries=config.get("max_retries", 3),
                is_active=config.get("is_active", True),
                is_default=config.get("is_default", False),
                description=config.get("description"),
                creator_id=current_user.id
            )
            session.add(new_config)
            session.flush()  # 获取新创建的ID
            llm_config_obj = new_config
        
        session.commit()
        
        return Message(message="大模型配置保存成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/llm/list")
def get_llm_config_list(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    获取大模型配置列表
    """
    try:
        configs = session.exec(
            select(LLMConfig)
            .where(LLMConfig.is_active == True)
            .offset(skip)
            .limit(limit)
        ).all()
        
        return {
            "data": [
                {
                    "id": str(config.id),
                    "name": config.name,
                    "endpoint": config.endpoint,
                    "api_key": config.api_key,  # 返回 api_key 供前端使用
                    "app_id": config.app_id,
                    "workflow_id": config.workflow_id,
                    "app_type": config.app_type,
                    "is_default": config.is_default,
                    "is_active": config.is_active,
                    "description": config.description,
                    "create_time": config.create_time.isoformat() if config.create_time else None,
                    "update_time": config.update_time.isoformat() if config.update_time else None
                }
                for config in configs
            ],
            "count": len(configs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置列表失败: {str(e)}")


@router.delete("/llm/{config_id}", response_model=Message)
def delete_llm_config(
    *,
    session: SessionDep,
    config_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    删除大模型配置（通过SQL直接删除数据库表中的对应行项目）
    """
    try:
        from sqlalchemy import text
        
        # 首先检查配置是否存在
        config = session.get(LLMConfig, config_id)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        # 使用SQL直接删除
        delete_sql = text("DELETE FROM llm_config WHERE id = :config_id")
        session.execute(delete_sql, {"config_id": config_id})
        session.commit()
        
        logger.info(f"用户 {current_user.id} 删除了LLM配置 {config_id} (名称: {config.name})")
        return Message(message=f"配置 '{config.name}' 删除成功")
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"删除LLM配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除配置失败: {str(e)}")


@router.post("/llm/test")
def test_llm_connection(
    *,
    session: SessionDep,
    config: dict,
    current_user: CurrentUser
) -> Any:
    """
    测试SYNTAX API连接
    """
    try:
        import httpx
        
        endpoint = config.get("endpoint", "").strip()
        api_key = config.get("api_key", "")
        app_id = config.get("app_id")
        workflow_id = config.get("workflow_id")
        app_type = config.get("app_type", "workflow")
        
        if not endpoint or not api_key:
            return {
                "success": False,
                "message": "endpoint和api_key不能为空"
            }
        
        # 根据应用类型选择测试端点
        if app_type == "workflow" and workflow_id:
            test_url = f"{endpoint.rstrip('/')}/workflows/run"
            test_data = {
                "inputs": {},
                "response_mode": "blocking"
            }
        elif app_type == "chat" and app_id:
            test_url = f"{endpoint.rstrip('/')}/chat-messages"
            test_data = {
                "query": "test",
                "response_mode": "blocking"
            }
        else:
            # 简单测试：检查API是否可访问
            test_url = f"{endpoint.rstrip('/')}/info"
            test_data = {}
        
        # 发送测试请求
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(test_url, headers=headers, json=test_data)
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "message": "连接测试成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"连接失败：{response.status_code} {response.text[:200]}"
                }
    except httpx.TimeoutException:
        return {
            "success": False,
            "message": "连接超时，请检查endpoint地址"
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "message": "无法连接到服务器，请检查endpoint地址"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"测试失败：{str(e)}"
        }


# ==================== OCR配置接口（保留用于兼容） ====================

@router.get("/ocr")
def get_ocr_config(
    *,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    获取OCR配置（已废弃，保留用于兼容）
    """
    try:
        config = session.exec(
            select(OCRConfig).where(OCRConfig.config_key == "ocr_settings")
        ).first()
        
        if config:
            config_value = json.loads(config.config_value)
            return config_value
        else:
            return {
                "provider": "tesseract",
                "language": "chi_sim+eng",
                "enable_preprocessing": True,
                "enable_postprocessing": True,
                "confidence_threshold": 80,
                "max_file_size": 10,
                "supported_formats": ["pdf", "jpg", "png"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/ocr", response_model=Message)
def update_ocr_config(
    *,
    session: SessionDep,
    config: dict,
    current_user: CurrentUser
) -> Any:
    """
    更新OCR配置（已废弃，保留用于兼容）
    """
    try:
        required_fields = ["provider", "language", "confidence_threshold", "max_file_size"]
        for field in required_fields:
            if field not in config:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")
        
        existing_config = session.exec(
            select(OCRConfig).where(OCRConfig.config_key == "ocr_settings")
        ).first()
        
        config_value = json.dumps(config, ensure_ascii=False)
        
        if existing_config:
            existing_config.config_value = config_value
            existing_config.update_time = datetime.now()
            existing_config.updater_id = current_user.id
            session.add(existing_config)
        else:
            new_config = OCRConfig(
                config_key="ocr_settings",
                config_value=config_value,
                description="OCR引擎配置",
                updater_id=current_user.id
            )
            session.add(new_config)
        
        session.commit()
        return Message(message="配置保存成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/recognition-rules")
def get_recognition_rules(
    *,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    template_id: UUID | None = None,
    is_active: bool | None = None,
    current_user: CurrentUser
) -> Any:
    """
    获取识别规则列表
    """
    try:
        statement = select(RecognitionRule)
        
        # 构建查询条件
        conditions = []
        if template_id:
            conditions.append(RecognitionRule.template_id == template_id)
        if is_active is not None:
            conditions.append(RecognitionRule.is_active == is_active)
        
        if conditions:
            from sqlmodel import or_
            statement = statement.where(or_(*conditions))
        
        # 总数
        count_statement = select(func.count()).select_from(RecognitionRule)
        if conditions:
            from sqlmodel import or_
            count_statement = count_statement.where(or_(*conditions))
        total = session.exec(count_statement).one()
        
        # 分页查询
        rules = session.exec(
            statement.order_by(RecognitionRule.priority.desc(), RecognitionRule.create_time.desc())
            .offset(skip).limit(limit)
        ).all()
        
        return {
            "data": [
                {
                    "id": str(rule.id),
                    "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type,
                    "rule_definition": rule.rule_definition,
                    "template_id": str(rule.template_id) if rule.template_id else None,
                    "field_name": rule.field_name,
                    "is_active": rule.is_active,
                    "priority": rule.priority,
                    "remark": rule.remark,
                    "create_time": rule.create_time.isoformat()
                }
                for rule in rules
            ],
            "count": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/recognition-rules", response_model=Message)
def create_recognition_rule(
    *,
    session: SessionDep,
    rule_data: dict,
    current_user: CurrentUser
) -> Any:
    """
    创建识别规则
    """
    try:
        # 验证必需字段
        required_fields = ["rule_name", "rule_type", "rule_definition"]
        for field in required_fields:
            if field not in rule_data:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")
        
        # 如果指定了模板ID，跳过验证（模板功能已废弃）
        if rule_data.get("template_id"):
            pass  # 模板功能已废弃，不再验证
        
        rule = RecognitionRule(
            rule_name=rule_data["rule_name"],
            rule_type=rule_data["rule_type"],
            rule_definition=rule_data["rule_definition"],
            template_id=UUID(rule_data["template_id"]) if rule_data.get("template_id") else None,
            field_name=rule_data.get("field_name"),
            is_active=rule_data.get("is_active", True),
            priority=rule_data.get("priority", 0),
            remark=rule_data.get("remark"),
            creator_id=current_user.id
        )
        session.add(rule)
        session.commit()
        
        return Message(message="规则创建成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建规则失败: {str(e)}")


@router.patch("/recognition-rules/{rule_id}", response_model=Message)
def update_recognition_rule(
    *,
    session: SessionDep,
    rule_id: UUID,
    rule_data: dict,
    current_user: CurrentUser
) -> Any:
    """
    更新识别规则
    """
    rule = session.get(RecognitionRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    # 更新字段
    update_fields = ["rule_name", "rule_type", "rule_definition", "field_name", "is_active", "priority", "remark"]
    for field in update_fields:
        if field in rule_data:
            setattr(rule, field, rule_data[field])
    
    if "template_id" in rule_data:
        rule.template_id = UUID(rule_data["template_id"]) if rule_data["template_id"] else None
    
    rule.update_time = datetime.now()
    session.add(rule)
    session.commit()
    
    return Message(message="规则更新成功")


@router.delete("/recognition-rules/{rule_id}", response_model=Message)
def delete_recognition_rule(
    *,
    session: SessionDep,
    rule_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    删除识别规则
    """
    rule = session.get(RecognitionRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    session.delete(rule)
    session.commit()
    
    return Message(message="规则删除成功")


@router.get("/review-workflow")
def get_review_workflow(
    *,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    获取审核流程配置
    """
    try:
        # 从配置表读取审核流程配置
        config = session.exec(
            select(OCRConfig).where(OCRConfig.config_key == "review_workflow")
        ).first()
        
        if config:
            workflow = json.loads(config.config_value)
            return {"workflow": workflow}
        else:
            # 返回默认审核流程
            return {
                "workflow": [
                    {
                        "step": 1,
                        "name": "自动识别",
                        "required": True,
                        "auto": True
                    },
                    {
                        "step": 2,
                        "name": "人工审核",
                        "required": True,
                        "auto": False,
                        "roles": ["reviewer", "admin"]
                    },
                    {
                        "step": 3,
                        "name": "归档",
                        "required": False,
                        "auto": True
                    }
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取审核流程失败: {str(e)}")


@router.post("/review-workflow", response_model=Message)
def update_review_workflow(
    *,
    session: SessionDep,
    workflow: dict,
    current_user: CurrentUser
) -> Any:
    """
    更新审核流程配置
    """
    try:
        # 查找或创建配置
        existing_config = session.exec(
            select(OCRConfig).where(OCRConfig.config_key == "review_workflow")
        ).first()
        
        config_value = json.dumps(workflow, ensure_ascii=False)
        
        if existing_config:
            existing_config.config_value = config_value
            existing_config.update_time = datetime.now()
            existing_config.updater_id = current_user.id
            session.add(existing_config)
        else:
            new_config = OCRConfig(
                config_key="review_workflow",
                config_value=config_value,
                description="审核流程配置",
                updater_id=current_user.id
            )
            session.add(new_config)
        
        session.commit()
        return Message(message="审核流程配置保存成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


# ==================== 识别配置接口 ====================

@router.get("/recognition-config/options")
def get_recognition_config_options(
    *,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    获取识别配置选项（用于参数选择界面）
    返回：模型配置列表、识别方式列表、输出结构标准列表、模板策略列表等
    """
    try:
        # 1. 获取模型配置列表（从 llm_config 表查询）
        # 优先返回默认模型，然后按名称排序
        from sqlalchemy import case
        llm_configs_query = select(LLMConfig).where(LLMConfig.is_active == True).order_by(
            LLMConfig.is_default.desc(),  # 默认模型排在前面
            case(
                (LLMConfig.name.ilike('%v3_jsonschema%'), 0),
                (LLMConfig.name.ilike('%jsonschema%'), 1),
                else_=2
            ),  # 包含 JsonSchema 的模型优先
            LLMConfig.name  # 最后按名称排序
        )
        llm_configs = session.exec(llm_configs_query).all()
        
        # 转换为模型配置格式
        available_model_configs = []
        for config in llm_configs:
            # 根据 app_type 设置 allowed_modes
            allowed_modes = ["llm_extract", "ocr_llm", "template"]
            if config.app_type == "chat":
                allowed_modes = ["llm_extract", "ocr_llm"]
            elif config.app_type == "workflow":
                allowed_modes = ["llm_extract", "ocr_llm", "template"]
            elif config.app_type == "completion":
                allowed_modes = ["llm_extract"]
            
            # 设置默认识别方式
            default_mode = "llm_extract"
            if config.app_type == "chat":
                default_mode = "llm_extract"
            elif config.app_type == "workflow":
                default_mode = "llm_extract"
            elif config.app_type == "completion":
                default_mode = "llm_extract"
            
            available_model_configs.append({
                "id": str(config.id),
                "name": config.name,
                "provider": "syntax",  # llm_config 默认使用 syntax
                "cost_level": "standard",  # 默认标准成本级别
                "default_mode": default_mode,
                "allowed_modes": allowed_modes,
                "model_name": config.name,  # 使用配置名称作为模型名称
                "model_version": None,  # llm_config 没有版本字段
                "default_schema_id": None  # llm_config 没有 default_schema_id 字段
            })
        
        # 2. 获取识别方式列表（从模型配置中提取所有唯一的方式）
        all_modes = set()
        for config in available_model_configs:
            all_modes.update(config.get("allowed_modes", []))
        # 添加标准识别方式
        all_modes.update(["llm_extract", "ocr_llm", "template"])
        modes = [
            {"value": "llm_extract", "label": "结构化抽取（LLM Extract）"},
            {"value": "ocr_llm", "label": "OCR + 结构化抽取（OCR→LLM）"},
            {"value": "template", "label": "模板驱动抽取（Template）"}
        ]
        
        # 3. 获取输出结构标准列表
        schemas_query = select(OutputSchema).where(OutputSchema.is_active == True)
        schemas = session.exec(schemas_query).all()
        schema_list = [
            {
                "id": str(schema.id),
                "name": schema.name,
                "version": schema.version,
                "is_default": schema.is_default,
                "description": schema.description
            }
            for schema in schemas
        ]
        
        # 4. 获取模板策略列表
        template_strategies = [
            {"value": "auto", "label": "自动匹配/自动识别票据类型"},
            {"value": "fixed", "label": "用户指定模板"},
            {"value": "none", "label": "不使用模板，仅抽取通用字段"}
        ]
        
        # 5. 模板列表（用于 template_strategy=fixed 的下拉选择）
        # 只返回启用模板，避免误选停用/废弃模板
        templates = session.exec(
            select(Template).where(Template.status == "enabled").order_by(Template.update_time.desc().nulls_last(), Template.create_time.desc())
        ).all()

        version_ids = [t.current_version_id for t in templates if t.current_version_id]
        versions_map = {}
        if version_ids:
            versions = session.exec(select(TemplateVersion).where(TemplateVersion.id.in_(version_ids))).all()
            versions_map = {v.id: v for v in versions}

        def _strip_leading_v(ver: str | None) -> str:
            if not ver:
                return ""
            return ver[1:] if ver.lower().startswith("v") else ver

        # 批量获取所有模板的 prompt 字段（使用 SQL 查询，避免模型字段未加载的问题）
        template_ids = [t.id for t in templates]
        prompt_map = {}
        if template_ids:
            try:
                from sqlalchemy import text
                from sqlalchemy.dialects.postgresql import array
                # 使用 PostgreSQL 数组参数
                result = session.execute(
                    text("SELECT id::text, prompt FROM template WHERE id = ANY(:ids)"),
                    {"ids": array(template_ids)}
                ).fetchall()
                for row in result:
                    template_id_str = str(row[0])
                    prompt_map[template_id_str] = row[1] if row[1] else None
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"批量获取模板 prompt 字段失败: {str(e)}，将逐个查询")
                # 如果批量查询失败，逐个查询
                for template in templates:
                    try:
                        from sqlalchemy import text
                        result = session.execute(
                            text("SELECT prompt FROM template WHERE id = :id"),
                            {"id": str(template.id)}
                        ).fetchone()
                        if result:
                            prompt_map[str(template.id)] = result[0] if result[0] else None
                        else:
                            prompt_map[str(template.id)] = None
                    except Exception:
                        prompt_map[str(template.id)] = None
        
        template_list = []
        for t in templates:
            v = versions_map.get(t.current_version_id) if t.current_version_id else None
            # 从 prompt_map 中获取 prompt 值
            prompt_value = prompt_map.get(str(t.id))
            
            template_list.append(
                {
                    "id": str(t.id),
                    "name": t.name,
                    "template_type": t.template_type,
                    "type": t.template_type,  # 保持向后兼容
                    "description": t.description,
                    "status": t.status,
                    "schema_id": str(t.default_schema_id) if t.default_schema_id else None,
                    "default_schema_id": str(t.default_schema_id) if t.default_schema_id else None,
                    "current_version": v.version if v else None,
                    "version": _strip_leading_v(v.version) if v else "",  # 保持向后兼容
                    "accuracy": t.accuracy,
                    "prompt": prompt_value,  # 添加 prompt 字段
                }
            )
        
        return {
            "model_configs": available_model_configs,
            "modes": modes,
            "schemas": schema_list,
            "template_strategies": template_strategies,
            "templates": template_list,
            "defaults": {
                "language": "zh-CN",
                "confidence_threshold": 0.8,
                "page_range": "all",
                "enhance_options": "auto"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置选项失败: {str(e)}")


@router.delete("/schemas/{schema_id}", response_model=Message)
def delete_schema(
    *,
    session: SessionDep,
    schema_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    删除Schema配置
    """
    try:
        from sqlalchemy import text
        
        # 先使用SQL查询获取Schema名称（避免SQLModel关系加载）
        get_schema_sql = text("SELECT name FROM output_schema WHERE id = :schema_id")
        result = session.execute(get_schema_sql, {"schema_id": str(schema_id)}).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Schema不存在")
        
        schema_name = result[0]
        
        # 先尝试删除关联的验证记录（如果表存在）
        # 使用原始SQL避免SQLModel关系加载问题
        try:
            # 检查表是否存在，如果存在则删除关联记录
            delete_validation_records = text("""
                DELETE FROM schema_validation_record 
                WHERE schema_id = :schema_id
            """)
            session.execute(delete_validation_records, {"schema_id": str(schema_id)})
            logger.info(f"已删除Schema {schema_id} 的验证记录")
        except Exception as e:
            # 如果表不存在或删除失败，需要回滚事务并重新开始
            error_msg = str(e)
            if "does not exist" in error_msg or "relation" in error_msg.lower() or "aborted" in error_msg.lower():
                logger.info(f"schema_validation_record表不存在，回滚事务后继续删除Schema")
                session.rollback()
                # 重新获取Schema名称（因为事务已回滚）
                result = session.execute(get_schema_sql, {"schema_id": str(schema_id)}).first()
                if not result:
                    raise HTTPException(status_code=404, detail="Schema不存在")
                schema_name = result[0]
            else:
                logger.warning(f"删除验证记录时出错: {error_msg}")
                session.rollback()
                raise HTTPException(status_code=500, detail=f"删除Schema失败: {error_msg}")

        # 使用SQL直接删除Schema，避免SQLModel关系加载问题
        delete_schema_sql = text("DELETE FROM output_schema WHERE id = :schema_id")
        delete_result = session.execute(delete_schema_sql, {"schema_id": str(schema_id)})
        session.commit()
        
        if delete_result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Schema不存在")

        return Message(message=f"Schema '{schema_name}' 删除成功")
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"删除Schema失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除Schema失败: {str(e)}")