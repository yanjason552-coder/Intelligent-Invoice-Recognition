from typing import Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func
from datetime import datetime
import json
import logging
from jsonschema import Draft7Validator

from app.api.deps import SessionDep, CurrentUser
from app.models import Message
from app.models.models_invoice import (
    OCRConfig, LLMConfig, RecognitionRule, ModelConfig, OutputSchema,
    Invoice, RecognitionTask, RecognitionResult, SchemaValidationRecord
)
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
        
        # 同步创建或更新 model_config
        try:
            # 优先根据 ID 查找（如果是更新操作，使用共享的 ID）
            existing_model_config = None
            if shared_id:
                existing_model_config = session.get(ModelConfig, shared_id)
            
            # 如果根据 ID 没找到，再根据名称查找
            if not existing_model_config:
                existing_model_config = session.exec(
                    select(ModelConfig).where(ModelConfig.name == config["name"])
                ).first()
            
            # 根据 app_type 设置 allowed_modes
            allowed_modes = ["llm_extract", "ocr_llm", "template"]
            if app_type == "chat":
                # 对话型应用主要使用 llm_extract
                allowed_modes = ["llm_extract", "ocr_llm"]
            elif app_type == "workflow":
                # 工作流应用可以使用所有方式
                allowed_modes = ["llm_extract", "ocr_llm", "template"]
            elif app_type == "completion":
                # 补全型应用主要使用 llm_extract
                allowed_modes = ["llm_extract"]
            
            # 从配置名称中提取模型名称，如果没有则使用默认值
            model_name = config["name"]
            if len(model_name) > 100:
                # 如果名称太长，截取前100个字符（model_name 字段最大长度）
                model_name = model_name[:100]
            
            logger.info(f"准备同步 model_config，名称: {config['name']}, 是否存在: {existing_model_config is not None}")
            
            if existing_model_config:
                # 更新现有的 model_config
                existing_model_config.syntax_endpoint = endpoint
                existing_model_config.syntax_api_key = config["api_key"]
                existing_model_config.syntax_app_id = config.get("app_id")
                existing_model_config.syntax_workflow_id = config.get("workflow_id")
                # 同时更新兼容字段（dify_*）
                existing_model_config.dify_endpoint = endpoint
                existing_model_config.dify_api_key = config["api_key"]
                existing_model_config.dify_app_id = config.get("app_id")
                existing_model_config.dify_workflow_id = config.get("workflow_id")
                existing_model_config.is_active = config.get("is_active", True)
                existing_model_config.description = config.get("description")
                existing_model_config.update_time = datetime.now()
                # 更新模型信息（如果名称改变）
                if existing_model_config.model_name != model_name:
                    existing_model_config.model_name = model_name
                # 更新 allowed_modes
                existing_model_config.allowed_modes = allowed_modes
                session.add(existing_model_config)
                logger.info(f"更新 model_config: {existing_model_config.name} (ID: {existing_model_config.id})")
            else:
                # 创建新的 model_config，使用与 llm_config 相同的 ID
                new_model_config = ModelConfig(
                    id=shared_id,  # 使用与 llm_config 相同的 ID
                    name=config["name"],
                    provider="syntax",
                    syntax_endpoint=endpoint,
                    syntax_api_key=config["api_key"],
                    syntax_app_id=config.get("app_id"),
                    syntax_workflow_id=config.get("workflow_id"),
                    # 同时设置兼容字段（dify_*）
                    dify_endpoint=endpoint,
                    dify_api_key=config["api_key"],
                    dify_app_id=config.get("app_id"),
                    dify_workflow_id=config.get("workflow_id"),
                    model_name=model_name,
                    model_version=None,
                    cost_level="standard",
                    default_mode="llm_extract",
                    allowed_modes=allowed_modes,
                    is_active=config.get("is_active", True),
                    description=config.get("description"),
                    creator_id=current_user.id
                )
                session.add(new_model_config)
                session.flush()  # 确保获取ID
                logger.info(f"创建 model_config: {new_model_config.name} (ID: {new_model_config.id}, 与 llm_config ID 一致)")
        except Exception as e:
            # 如果同步 model_config 失败，记录详细错误信息
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"同步 model_config 失败: {str(e)}\n{error_detail}")
            # 仍然继续执行，不中断主流程
        
        session.commit()
        
        # 验证 model_config 是否创建成功
        try:
            created_model_config = session.exec(
                select(ModelConfig).where(ModelConfig.name == config["name"])
            ).first()
            if created_model_config:
                logger.info(f"验证成功: model_config 已创建/更新，ID: {created_model_config.id}")
            else:
                logger.warning(f"警告: model_config 未找到，名称: {config['name']}")
        except Exception as e:
            logger.warning(f"验证 model_config 时出错: {str(e)}")
        
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


# ==================== Schema配置接口 ====================

@router.get("/schemas")
def get_schema_list(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    name: str | None = None,
    is_active: bool | None = None
) -> Any:
    """
    获取Schema配置列表
    """
    try:
        statement = select(OutputSchema)

        # 构建查询条件
        conditions = []
        if name:
            conditions.append(OutputSchema.name.ilike(f"%{name}%"))
        if is_active is not None:
            conditions.append(OutputSchema.is_active == is_active)

        if conditions:
            from sqlmodel import or_
            statement = statement.where(or_(*conditions))

        # 总数
        count_statement = select(func.count()).select_from(OutputSchema)
        if conditions:
            from sqlmodel import or_
            count_statement = count_statement.where(or_(*conditions))
        total = session.exec(count_statement).one()

        # 分页查询
        schemas = session.exec(
            statement.order_by(OutputSchema.create_time.desc())
            .offset(skip).limit(limit)
        ).all()

        return {
            "data": [
                {
                    "id": str(schema.id),
                    "name": schema.name,
                    "version": schema.version,
                    "schema_definition": schema.schema_definition,
                    "is_active": schema.is_active,
                    "is_default": schema.is_default,
                    "description": schema.description,
                    "create_time": schema.create_time.isoformat() if schema.create_time else None,
                    "update_time": schema.update_time.isoformat() if schema.update_time else None
                }
                for schema in schemas
            ],
            "count": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Schema列表失败: {str(e)}")


@router.get("/schemas/{schema_id}")
def get_schema(
    *,
    session: SessionDep,
    schema_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    获取单个Schema配置
    """
    try:
        schema = session.get(OutputSchema, schema_id)
        if not schema:
            raise HTTPException(status_code=404, detail="Schema不存在")

        return {
            "id": str(schema.id),
            "name": schema.name,
            "version": schema.version,
            "schema_definition": schema.schema_definition,
            "is_active": schema.is_active,
            "is_default": schema.is_default,
            "description": schema.description,
            "create_time": schema.create_time.isoformat() if schema.create_time else None,
            "update_time": schema.update_time.isoformat() if schema.update_time else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Schema失败: {str(e)}")


@router.post("/schemas", response_model=Message)
def create_schema(
    *,
    session: SessionDep,
    schema_data: dict,
    current_user: CurrentUser
) -> Any:
    """
    创建Schema配置
    """
    try:
        # 验证必需字段
        required_fields = ["name", "schema_definition"]
        for field in required_fields:
            if field not in schema_data:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")

        # 验证JSON格式
        try:
            schema_definition = json.loads(schema_data["schema_definition"]) if isinstance(schema_data["schema_definition"], str) else schema_data["schema_definition"]
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="schema_definition不是有效的JSON格式")

        # 验证JSON Schema格式（可选）
        try:
            Draft7Validator.check_schema(schema_definition)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Schema格式不符合JSON Schema规范: {str(e)}")

        # 检查名称是否重复
        existing_schema = session.exec(
            select(OutputSchema).where(OutputSchema.name == schema_data["name"])
        ).first()
        if existing_schema:
            raise HTTPException(status_code=400, detail="Schema名称已存在")

        # 如果设置为默认，先取消其他默认配置
        if schema_data.get("is_default", False):
            existing_defaults = session.exec(
                select(OutputSchema).where(OutputSchema.is_default == True)
            ).all()
            for default_schema in existing_defaults:
                default_schema.is_default = False
                session.add(default_schema)

        # 创建Schema
        schema = OutputSchema(
            name=schema_data["name"],
            version=schema_data.get("version", "1.0.0"),
            schema_definition=schema_definition,
            is_active=schema_data.get("is_active", True),
            is_default=schema_data.get("is_default", False),
            description=schema_data.get("description"),
            creator_id=current_user.id
        )

        session.add(schema)
        session.commit()
        session.refresh(schema)

        return Message(message="Schema创建成功")
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建Schema失败: {str(e)}")


@router.patch("/schemas/{schema_id}", response_model=Message)
def update_schema(
    *,
    session: SessionDep,
    schema_id: UUID,
    schema_data: dict,
    current_user: CurrentUser
) -> Any:
    """
    更新Schema配置
    """
    try:
        schema = session.get(OutputSchema, schema_id)
        if not schema:
            raise HTTPException(status_code=404, detail="Schema不存在")

        # 验证JSON格式（如果提供了schema_definition）
        if "schema_definition" in schema_data:
            try:
                schema_definition = json.loads(schema_data["schema_definition"]) if isinstance(schema_data["schema_definition"], str) else schema_data["schema_definition"]
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="schema_definition不是有效的JSON格式")

            # 验证JSON Schema格式
            try:
                Draft7Validator.check_schema(schema_definition)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Schema格式不符合JSON Schema规范: {str(e)}")

            schema.schema_definition = schema_definition

        # 检查名称重复（排除自己）
        if "name" in schema_data and schema_data["name"] != schema.name:
            existing_schema = session.exec(
                select(OutputSchema).where(
                    OutputSchema.name == schema_data["name"],
                    OutputSchema.id != schema_id
                )
            ).first()
            if existing_schema:
                raise HTTPException(status_code=400, detail="Schema名称已存在")

        # 如果设置为默认，先取消其他默认配置
        if schema_data.get("is_default", False):
            existing_defaults = session.exec(
                select(OutputSchema).where(
                    OutputSchema.is_default == True,
                    OutputSchema.id != schema_id
                )
            ).all()
            for default_schema in existing_defaults:
                default_schema.is_default = False
                session.add(default_schema)

        # 更新字段
        update_fields = ["name", "version", "is_active", "is_default", "description"]
        for field in update_fields:
            if field in schema_data:
                setattr(schema, field, schema_data[field])

        schema.update_time = datetime.now()
        session.add(schema)
        session.commit()

        return Message(message="Schema更新成功")
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新Schema失败: {str(e)}")


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
        schema = session.get(OutputSchema, schema_id)
        if not schema:
            raise HTTPException(status_code=404, detail="Schema不存在")

        # 检查是否被模型配置引用
        referenced_configs = session.exec(
            select(ModelConfig).where(ModelConfig.default_schema_id == schema_id)
        ).all()

        if referenced_configs:
            config_names = [config.name for config in referenced_configs]
            raise HTTPException(
                status_code=400,
                detail=f"Schema被以下模型配置引用，无法删除: {', '.join(config_names)}"
            )

        session.delete(schema)
        session.commit()

        return Message(message=f"Schema '{schema.name}' 删除成功")
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"删除Schema失败: {str(e)}")


@router.get("/invoices/{invoice_id}/schema-validation-status")
def get_invoice_schema_validation_status(
    *,
    session: SessionDep,
    invoice_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    获取发票的Schema验证状态
    """
    try:
        # 获取发票信息
        invoice = session.get(Invoice, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="发票不存在")

        # 获取最新的识别结果
        recognition_result = session.exec(
            select(RecognitionResult).where(
                RecognitionResult.invoice_id == invoice_id,
                RecognitionResult.status.in_(["success", "partial"])
            ).order_by(RecognitionResult.recognition_time.desc())
        ).first()

        if not recognition_result:
            return None  # 没有识别结果

        # 获取识别任务信息
        task = session.get(RecognitionTask, recognition_result.task_id)
        if not task:
            return None

        # 获取模型配置
        model_config = session.get(ModelConfig, task.params.get("model_config_id")) if task.params else None

        # 获取Schema信息
        schema_info = None
        if model_config and model_config.default_schema_id:
            schema = session.get(OutputSchema, model_config.default_schema_id)
            if schema and schema.is_active:
                schema_info = {
                    "id": str(schema.id),
                    "name": schema.name,
                    "version": schema.version
                }

        # 如果没有配置Schema，返回None
        if not schema_info:
            return None

        # 获取Schema验证记录
        validation_record = session.exec(
            select(SchemaValidationRecord).where(
                SchemaValidationRecord.invoice_id == invoice_id,
                SchemaValidationRecord.task_id == recognition_result.task_id
            ).order_by(SchemaValidationRecord.created_at.desc())
        ).first()

        if validation_record:
            # 返回真实的验证记录
            validation_status = {
                "is_valid": validation_record.is_valid,
                "errors": validation_record.validation_errors.get("errors", []) if validation_record.validation_errors else [],
                "warnings": validation_record.validation_warnings.get("warnings", []) if validation_record.validation_warnings else [],
                "validation_time": validation_record.created_at.isoformat(),
                "schema_name": schema_info["name"],
                "schema_version": schema_info["version"],
                "repair_attempted": validation_record.repair_attempted,
                "repair_success": validation_record.repair_success,
                "fallback_type": validation_record.fallback_type
            }
        else:
            # 如果没有验证记录，说明没有进行Schema验证
            validation_status = None

        return validation_status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Schema验证状态失败: {str(e)}")


@router.post("/schemas/validate")
def validate_schema_json(
    *,
    session: SessionDep,
    schema_data: dict,
    current_user: CurrentUser
) -> Any:
    """
    验证Schema JSON格式
    """
    try:
        # 检查是否有schema_definition字段
        if "schema_definition" not in schema_data:
            return {
                "valid": False,
                "message": "缺少schema_definition字段"
            }

        schema_definition = schema_data["schema_definition"]

        # 验证JSON格式
        try:
            if isinstance(schema_definition, str):
                parsed_schema = json.loads(schema_definition)
            else:
                parsed_schema = schema_definition
                # 验证是否可以序列化为JSON
                json.dumps(parsed_schema, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError) as e:
            return {
                "valid": False,
                "message": f"无效的JSON格式: {str(e)}"
            }

        # 验证JSON Schema格式
        try:
            Draft7Validator.check_schema(parsed_schema)
        except Exception as e:
            return {
                "valid": False,
                "message": f"不符合JSON Schema规范: {str(e)}"
            }

        return {
            "valid": True,
            "message": "Schema格式验证通过",
            "schema_info": {
                "type": parsed_schema.get("type"),
                "properties_count": len(parsed_schema.get("properties", {})),
                "required_fields": parsed_schema.get("required", [])
            }
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"验证过程中发生错误: {str(e)}"
        }


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
        # 1. 获取模型配置列表（根据权限过滤）
        model_configs_query = select(ModelConfig).where(ModelConfig.is_active == True)
        model_configs = session.exec(model_configs_query).all()
        
        # 权限过滤：检查用户是否有权限使用该模型
        available_model_configs = []
        for config in model_configs:
            # 如果配置了用户限制，检查当前用户是否在允许列表中
            if config.allowed_user_ids:
                if current_user.id not in [UUID(uid) for uid in config.allowed_user_ids]:
                    continue
            # TODO: 检查角色权限（需要获取用户角色）
            available_model_configs.append({
                "id": str(config.id),
                "name": config.name,
                "provider": config.provider,
                "cost_level": config.cost_level,
                "default_mode": config.default_mode,
                "allowed_modes": config.allowed_modes or [],
                "model_name": config.model_name,
                "model_version": config.model_version,
                "default_schema_id": str(config.default_schema_id) if config.default_schema_id else None
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
        
        # 5. 模板列表（已废弃，返回空列表）
        template_list = []
        
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
