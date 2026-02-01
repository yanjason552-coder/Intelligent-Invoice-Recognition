from typing import Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Form
from sqlmodel import select, func, or_, and_
from datetime import datetime
import os
import shutil
import logging
import json
from pathlib import Path

from app.api.deps import SessionDep, CurrentUser
from app.models import Message
from app.models.models_invoice import (
    Invoice, InvoiceFile, InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    RecognitionTask, RecognitionTaskCreate, RecognitionTaskResponse, RecognitionTaskBatchCreate,
    RecognitionResult, RecognitionResultResponse,
    RecognitionField, ReviewRecord, InvoiceFileListItem,
    OutputSchema, LLMConfig, InvoiceItem, InvoiceItemUpdate, InvoiceItemsBatchUpdate,
    SchemaValidationRecord
)
from sqlmodel import SQLModel, Field

router = APIRouter(prefix="/invoices", tags=["invoices"])

# 配置日志 - 确保日志级别为INFO
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 文件上传目录配置
# 使用绝对路径，基于后端运行目录
import os
BACKEND_DIR = Path(__file__).parent.parent.parent.parent  # 从 routes/invoice.py 到 backend 目录
UPLOAD_DIR = BACKEND_DIR / "uploads" / "invoices"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# 辅助函数：添加公司过滤条件
def add_company_filter(statement, current_user, conditions=None):
    """
    根据用户的公司ID过滤发票查询
    超级用户可以查看所有发票，普通用户只能查看自己公司的发票
    """
    if conditions is None:
        conditions = []
    
    # 如果不是超级用户，添加公司过滤条件
    if not current_user.is_superuser:
        if current_user.company_id:
            conditions.append(Invoice.company_id == current_user.company_id)
        else:
            # 如果用户没有关联公司，返回空结果（使用一个永远为False的条件）
            conditions.append(Invoice.id.is_(None))
    
    if conditions:
        statement = statement.where(and_(*conditions))
    
    return statement, conditions


@router.post("/upload", response_model=Message)
def upload_invoice(
    *,
    session: SessionDep,
    file: UploadFile = File(...),
    current_user: CurrentUser
) -> Any:
    """
    上传票据文件
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"=== 票据上传开始 ===")
        logger.info(f"文件名: {file.filename}")
        logger.info(f"Content-Type: {file.content_type}")
        logger.info(f"上传用户ID: {current_user.id}")
        
        # 1. 验证文件类型
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
        logger.debug(f"检查文件类型: {file.content_type} in {allowed_types}")
        if file.content_type not in allowed_types:
            logger.warning(f"不支持的文件类型: {file.content_type}")
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}，仅支持 PDF、JPG、PNG"
            )
        logger.debug("文件类型验证通过")
        
        # 2. 验证文件大小（10MB）并读取文件内容
        file_content = file.file.read()
        file_size = len(file_content)
        logger.debug(f"文件大小: {file_size} 字节")
        if file_size > 10 * 1024 * 1024:
            logger.warning(f"文件大小超过限制: {file_size} 字节")
            raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
        logger.debug("文件大小验证通过")
        
        # 3. 计算文件哈希值（用于唯一性校验）
        import hashlib
        file_hash = hashlib.sha256(file_content).hexdigest()
        logger.info(f"文件哈希值: {file_hash}")
        
        # 4. 检查文件是否已存在（基于哈希值）
        existing_file = session.exec(
            select(InvoiceFile).where(InvoiceFile.file_hash == file_hash)
        ).first()
        
        if existing_file:
            logger.warning(f"文件已存在，哈希值: {file_hash}, 文件ID: {existing_file.id}")
            # 检查是否属于当前用户
            if existing_file.uploader_id == current_user.id:
                raise HTTPException(
                    status_code=400,
                    detail=f"该文件已上传过，文件名: {existing_file.file_name}，上传时间: {existing_file.upload_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="该文件已被其他用户上传，不能重复上传"
                )
        logger.debug("文件唯一性校验通过")
        
        # 5. 生成唯一文件名
        file_ext = Path(file.filename).suffix if file.filename else ".pdf"
        unique_filename = f"{uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        logger.info(f"上传目录: {UPLOAD_DIR}")
        logger.info(f"上传目录绝对路径: {UPLOAD_DIR.absolute()}")
        logger.info(f"生成文件路径: {file_path}")
        logger.info(f"文件路径绝对路径: {file_path.absolute()}")
        
        # 6. 保存文件
        file.file.seek(0)  # 重置文件指针
        logger.info("开始保存文件到磁盘")
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info(f"文件已保存: {file_path.absolute()}")
            
            # 验证文件是否真的存在
            if file_path.exists():
                actual_size = file_path.stat().st_size
                logger.info(f"文件保存成功，实际大小: {actual_size} 字节，期望大小: {file_size} 字节")
                if actual_size != file_size:
                    logger.warning(f"文件大小不匹配！实际: {actual_size}, 期望: {file_size}")
            else:
                logger.error(f"文件保存后不存在！路径: {file_path.absolute()}")
                raise Exception(f"文件保存失败，文件不存在: {file_path.absolute()}")
        except Exception as save_error:
            logger.error(f"保存文件时出错: {str(save_error)}", exc_info=True)
            raise
        
        # 7. 创建文件记录
        logger.debug("创建文件记录")
        invoice_file = InvoiceFile(
            file_name=file.filename or "unknown",
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_ext[1:] if file_ext else "pdf",
            mime_type=file.content_type or "application/pdf",
            file_hash=file_hash,
            uploader_id=current_user.id,
            status="uploaded"
        )
        session.add(invoice_file)
        session.commit()
        session.refresh(invoice_file)
        logger.info(f"文件记录已创建: {invoice_file.id}")
        
        # 8. 自动创建票据记录
        logger.debug("创建票据记录")
        invoice = Invoice(
            invoice_no=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}",
            invoice_type="未知",
            file_id=invoice_file.id,
            creator_id=current_user.id,
            company_id=current_user.company_id,  # 自动设置用户的公司ID
            recognition_status="pending",
            review_status="pending"
        )
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        logger.info(f"票据记录已创建: {invoice.id}, 票据编号: {invoice.invoice_no}")
        
        # 构建返回消息
        message = f"文件上传成功，票据编号: {invoice.invoice_no}"
        
        logger.info("=== 票据上传成功 ===")
        return Message(message=message)
    
    except HTTPException:
        logger.error(f"HTTP异常: {file.filename if file else 'unknown'}")
        raise
    except Exception as e:
        logger.error(f"上传失败异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/upload-external", response_model=Message)
def upload_invoice_external(
    *,
    session: SessionDep,
    file: UploadFile = File(...),
    external_file_id: str = Form(...),
    current_user: CurrentUser
) -> Any:
    """
    上传票据文件（从外部API上传后保存到本地数据库）
    用于保存通过模型配置上传到外部API的文件信息
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"=== 外部API文件上传保存开始 ===")
        logger.info(f"文件名: {file.filename}")
        logger.info(f"外部文件ID: {external_file_id}")
        logger.info(f"上传用户ID: {current_user.id}")
        
        if not external_file_id:
            raise HTTPException(status_code=400, detail="缺少外部文件ID")
        
        # 1. 验证文件类型
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}，仅支持 PDF、JPG、PNG"
            )
        
        # 2. 验证文件大小（10MB）并读取文件内容
        file_content = file.file.read()
        file_size = len(file_content)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
        
        # 3. 计算文件哈希值（用于唯一性校验）
        import hashlib
        file_hash = hashlib.sha256(file_content).hexdigest()
        logger.info(f"文件哈希值: {file_hash}")
        
        # 4. 检查文件是否已存在（基于哈希值）
        existing_file = session.exec(
            select(InvoiceFile).where(InvoiceFile.file_hash == file_hash)
        ).first()
        
        if existing_file:
            logger.warning(f"文件已存在，哈希值: {file_hash}, 文件ID: {existing_file.id}")
            if existing_file.uploader_id == current_user.id:
                raise HTTPException(
                    status_code=400,
                    detail=f"该文件已上传过，文件名: {existing_file.file_name}，上传时间: {existing_file.upload_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="该文件已被其他用户上传，不能重复上传"
                )
        
        # 5. 生成唯一文件名
        file_ext = Path(file.filename).suffix if file.filename else ".pdf"
        unique_filename = f"{uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        logger.info(f"生成文件路径: {file_path}")
        
        # 6. 保存文件
        file.file.seek(0)  # 重置文件指针
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info(f"文件已保存: {file_path.absolute()}")
        except Exception as save_error:
            logger.error(f"保存文件时出错: {str(save_error)}", exc_info=True)
            raise
        
        # 7. 创建文件记录（包含外部文件ID）
        logger.debug("创建文件记录")
        invoice_file = InvoiceFile(
            file_name=file.filename or "unknown",
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_ext[1:] if file_ext else "pdf",
            mime_type=file.content_type or "application/pdf",
            file_hash=file_hash,
            uploader_id=current_user.id,
            status="uploaded",
            external_file_id=external_file_id  # 保存外部API返回的文件ID
        )
        session.add(invoice_file)
        session.commit()
        session.refresh(invoice_file)
        logger.info(f"文件记录已创建: {invoice_file.id}, 外部文件ID: {external_file_id}")
        
        # 8. 自动创建票据记录
        logger.debug("创建票据记录")
        invoice = Invoice(
            invoice_no=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}",
            invoice_type="未知",
            file_id=invoice_file.id,
            creator_id=current_user.id,
            company_id=current_user.company_id,  # 自动设置用户的公司ID
            recognition_status="pending",
            review_status="pending"
        )
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        logger.info(f"票据记录已创建: {invoice.id}, 票据编号: {invoice.invoice_no}")
        
        # 构建返回消息
        message = f"文件上传成功，票据编号: {invoice.invoice_no}, 外部文件ID: {external_file_id}"
        
        logger.info("=== 外部API文件上传保存成功 ===")
        return Message(message=message)
    
    except HTTPException:
        logger.error(f"HTTP异常: {file.filename if file else 'unknown'}")
        raise
    except Exception as e:
        logger.error(f"上传失败异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/recognition-tasks")
def get_recognition_tasks(
    *,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    current_user: CurrentUser
) -> Any:
    """
    获取识别任务列表
    """
    try:
        statement = select(RecognitionTask)
        
        # 状态过滤
        if status:
            statement = statement.where(RecognitionTask.status == status)
        
        # 总数
        count_statement = select(func.count()).select_from(RecognitionTask)
        if status:
            count_statement = count_statement.where(RecognitionTask.status == status)
        total = session.exec(count_statement).one()
        
        # 分页查询
        tasks = session.exec(statement.offset(skip).limit(limit)).all()
        
        # 获取模型配置信息（用于显示模型名称）
        model_config_ids = {UUID(task.params.get("model_config_id")) for task in tasks if task.params and task.params.get("model_config_id")}
        model_configs_dict = {}
        if model_config_ids:
            model_configs = session.exec(
                select(LLMConfig).where(LLMConfig.id.in_(list(model_config_ids)))
            ).all()
            model_configs_dict = {config.id: config for config in model_configs}
        
        return {
            "data": [
                RecognitionTaskResponse(
                    id=task.id,
                    task_no=task.task_no,
                    invoice_id=task.invoice_id,
                    template_id=task.template_id,
                    params=task.params,
                    status=task.status,
                    provider=task.provider,
                    recognition_mode=task.params.get("recognition_mode") if task.params else None,
                    model_name=model_configs_dict.get(UUID(task.params.get("model_config_id"))).name if task.params and task.params.get("model_config_id") and UUID(task.params.get("model_config_id")) in model_configs_dict else None,
                    start_time=task.start_time,
                    end_time=task.end_time,
                    create_time=task.create_time
                ).model_dump()
                for task in tasks
            ],
            "count": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/recognition-tasks", response_model=RecognitionTaskResponse)
def create_recognition_task(
    *,
    session: SessionDep,
    task_in: RecognitionTaskCreate,
    current_user: CurrentUser
) -> Any:
    """
    创建识别任务（含参数选择）
    """
    try:
        # 验证票据是否存在
        invoice = session.get(Invoice, task_in.invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="票据不存在")
        
        # 检查文件状态：只要文件状态不是成功状态（processed），都可以再次识别
        if invoice.file_id:
            from app.models.models_invoice import InvoiceFile
            invoice_file = session.get(InvoiceFile, invoice.file_id)
            if invoice_file:
                # 如果文件状态是 "processed"（成功状态），不允许再次识别
                if invoice_file.status == "processed":
                    raise HTTPException(
                        status_code=400, 
                        detail=f"文件状态为成功（processed），不允许再次识别。文件: {invoice_file.file_name}"
                    )
                logger.info(f"文件状态检查通过：文件ID={invoice_file.id}, 状态={invoice_file.status}, 允许创建识别任务")
        
        # 验证模型配置是否存在且可用
        model_config = session.get(LLMConfig, task_in.params.model_config_id)
        if not model_config:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        if not model_config.is_active:
            raise HTTPException(status_code=400, detail="模型配置未启用")
        
        # 根据 app_type 验证识别方式是否在允许列表中
        allowed_modes = ["llm_extract", "ocr_llm", "template"]
        if model_config.app_type == "chat":
            allowed_modes = ["llm_extract", "ocr_llm"]
        elif model_config.app_type == "workflow":
            allowed_modes = ["llm_extract", "ocr_llm", "template"]
        elif model_config.app_type == "completion":
            allowed_modes = ["llm_extract"]
        
        if task_in.params.recognition_mode not in allowed_modes:
            raise HTTPException(status_code=400, detail=f"识别方式 {task_in.params.recognition_mode} 不在允许列表中")
        
        # 模板策略处理
        template_id = None
        template_prompt = None
        logger.info(f"模板策略: {task_in.params.template_strategy}, template_id: {task_in.params.template_id}")
        if task_in.params.template_strategy == "fixed":
            # 用户指定模板，获取模板的 prompt
            if task_in.params.template_id:
                # 确保 template_id 是 UUID 类型
                from uuid import UUID
                if isinstance(task_in.params.template_id, str):
                    template_id = UUID(task_in.params.template_id)
                else:
                    template_id = task_in.params.template_id
                
                logger.info(f"设置 template_id: {template_id} (类型: {type(template_id)})")
                from app.models.models_invoice import Template
                try:
                    template = session.get(Template, template_id)
                    if template:
                        # 安全获取 prompt 字段
                        try:
                            template_prompt = getattr(template, 'prompt', None)
                        except Exception:
                            # 如果获取失败，尝试使用 SQL 查询
                            try:
                                from sqlalchemy import text
                                result = session.execute(
                                    text("SELECT prompt FROM template WHERE id = :id"),
                                    {"id": str(template.id)}
                                ).fetchone()
                                if result:
                                    template_prompt = result[0] if result[0] else None
                            except Exception as e:
                                logger.warning(f"通过SQL查询模板prompt失败: {str(e)}")
                                template_prompt = None
                        
                        if template_prompt:
                            logger.info(f"获取到模板提示词，长度: {len(template_prompt)} 字符")
                        else:
                            logger.warning(f"模板 {template_id} 没有设置 prompt 字段")
                    else:
                        logger.warning(f"模板 {template_id} 不存在，但会使用 params 中的 template_id")
                except Exception as e:
                    logger.error(f"查询模板失败: {str(e)}，但会使用 params 中的 template_id")
        elif task_in.params.template_strategy == "auto":
            # 自动匹配模板（暂时不支持）
            template_id = None
        
        # 验证输出结构标准（如果提供）
        if task_in.params.output_schema_id:
            schema = session.get(OutputSchema, task_in.params.output_schema_id)
            if not schema:
                raise HTTPException(status_code=404, detail="输出结构标准不存在")
        
        # 生成任务编号
        task_no = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}"
        
        # 构建参数快照（将UUID转换为字符串以便JSON序列化）
        params_dict = task_in.params.model_dump()
        # 如果获取到模板提示词，添加到参数中
        if template_prompt:
            params_dict["template_prompt"] = template_prompt
        # 将UUID对象转换为字符串
        def convert_uuid_to_str(obj):
            """递归将UUID对象转换为字符串"""
            if isinstance(obj, UUID):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_uuid_to_str(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_uuid_to_str(item) for item in obj]
            else:
                return obj
        
        params_dict = convert_uuid_to_str(params_dict)
        
        # 创建任务
        logger.info(f"创建任务，template_id: {template_id} (类型: {type(template_id)})")
        logger.info(f"创建任务前，template_id 值: {template_id}, 是否为 None: {template_id is None}")
        try:
            task = RecognitionTask(
                task_no=task_no,
                invoice_id=task_in.invoice_id,
                template_id=template_id,
                params=params_dict,
                priority=task_in.priority,
                operator_id=current_user.id,
                status="pending",
                provider="dify"
            )
            logger.info(f"任务对象创建完成，task.template_id: {task.template_id}")
            session.add(task)
            logger.info(f"任务已添加到session，准备提交")
            session.commit()
            logger.info(f"任务已提交到数据库")
            session.refresh(task)
            logger.info(f"任务刷新完成，task.template_id: {task.template_id}")
        except Exception as e:
            logger.error(f"创建任务时出错: {str(e)}", exc_info=True)
            raise
        
        # 获取模型名称用于响应
        model_name = model_config.name
        
        return RecognitionTaskResponse(
            id=task.id,
            task_no=task.task_no,
            invoice_id=task.invoice_id,
            template_id=task.template_id,
            params=task.params,
            status=task.status,
            provider=task.provider,
            recognition_mode=task_in.params.recognition_mode,
            model_name=model_name,
            start_time=task.start_time,
            end_time=task.end_time,
            create_time=task.create_time
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/recognition-tasks/{task_id}/start", response_model=Message)
def start_recognition(
    *,
    session: SessionDep,
    task_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    启动识别任务（校验参数并调用Dify）
    """
    try:
        task = session.get(RecognitionTask, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.status != "pending":
            raise HTTPException(status_code=400, detail=f"任务状态为 {task.status}，无法启动")
        
        # 验证参数
        if not task.params:
            raise HTTPException(status_code=400, detail="任务参数不存在")
        
        params = task.params
        model_config_id = params.get("model_config_id")
        if not model_config_id:
            raise HTTPException(status_code=400, detail="任务参数中缺少model_config_id")
        
        # 验证模型配置
        model_config = session.get(LLMConfig, UUID(model_config_id))
        if not model_config:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        if not model_config.is_active:
            raise HTTPException(status_code=400, detail="模型配置未启用")
        
        # 验证文件存在性
        invoice = session.get(Invoice, task.invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="票据不存在")
        
        file = session.get(InvoiceFile, invoice.file_id)
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not os.path.exists(file.file_path):
            raise HTTPException(status_code=404, detail="文件路径不存在")
        
        # 更新任务状态
        task.status = "processing"
        task.start_time = datetime.now()
        session.add(task)
        
        # 更新票据状态
        invoice.recognition_status = "processing"
        session.add(invoice)
        
        session.commit()
        
        # 调用SYNTAX服务（同步执行，实际生产环境应该使用异步队列）
        try:
            from app.services.dify_service import SyntaxService
            syntax_service = SyntaxService(session)
            # 注意：这里同步执行，实际应该使用异步任务队列（如Celery）
            # 暂时同步执行以便测试，生产环境应该改为异步
            success = syntax_service.process_task(task.id)
            if success:
                return Message(message="识别任务已完成")
            else:
                return Message(message="识别任务已启动，但执行失败，请查看任务详情")
        except Exception as e:
            logger.error(f"调用Dify服务失败: {str(e)}", exc_info=True)
            # 即使Dify调用失败，任务状态已更新为processing，返回成功消息
            return Message(message="识别任务已启动")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动任务失败: {str(e)}")


@router.post("/recognition-tasks/batch", response_model=dict)
async def batch_create_recognition_tasks(
    request: Request,
    session: SessionDep,
    batch_in: RecognitionTaskBatchCreate,
    current_user: CurrentUser
) -> Any:
    """
    批量创建识别任务（同一批使用同一参数）
    """
    # 详细日志记录
    logger.info("=" * 80)
    logger.info("=== 批量创建识别任务开始 ===")
    logger.info("=" * 80)
    
    # 记录请求基本信息
    logger.info(f"请求URL: {request.url}")
    logger.info(f"请求方法: {request.method}")
    logger.info(f"用户ID: {current_user.id}")
    logger.info(f"用户邮箱: {getattr(current_user, 'email', 'N/A')}")
    
    # 记录请求头
    logger.info("--- 请求头 ---")
    for header_name, header_value in request.headers.items():
        # 隐藏敏感信息
        if header_name.lower() == 'authorization':
            logger.info(f"{header_name}: Bearer ***")
        else:
            logger.info(f"{header_name}: {header_value}")
    
    # 记录原始请求体（用于调试）
    try:
        body = await request.body()
        body_str = body.decode('utf-8')
        logger.info("--- 原始请求体 ---")
        logger.info(f"请求体长度: {len(body_str)} 字符")
        logger.info(f"请求体内容: {body_str}")
        
        # 尝试解析JSON
        try:
            import json
            body_json = json.loads(body_str)
            logger.info("--- 解析后的JSON ---")
            logger.info(f"uploaded_file_ids: {body_json.get('uploaded_file_ids', 'N/A')}")
            logger.info(f"uploaded_file_ids 类型: {type(body_json.get('uploaded_file_ids', []))}")
            logger.info(f"uploaded_file_ids 长度: {len(body_json.get('uploaded_file_ids', []))}")
            if body_json.get('params'):
                logger.info(f"params: {json.dumps(body_json.get('params'), ensure_ascii=False, indent=2)}")
        except json.JSONDecodeError as e:
            logger.warning(f"无法解析JSON: {str(e)}")
    except Exception as e:
        logger.warning(f"无法读取请求体: {str(e)}")
    
    # 记录解析后的参数
    logger.info("--- 解析后的参数对象 ---")
    logger.info(f"batch_in 类型: {type(batch_in)}")
    logger.info(f"uploaded_file_ids: {batch_in.uploaded_file_ids}")
    logger.info(f"uploaded_file_ids 类型: {type(batch_in.uploaded_file_ids)}")
    logger.info(f"uploaded_file_ids 长度: {len(batch_in.uploaded_file_ids)}")
    for idx, file_id in enumerate(batch_in.uploaded_file_ids):
        logger.info(f"  [{idx}] file_id: {file_id} (类型: {type(file_id)})")
    
    logger.info(f"params 对象: {batch_in.params}")
    logger.info(f"params.model_config_id: {batch_in.params.model_config_id}")
    logger.info(f"params.recognition_mode: {batch_in.params.recognition_mode}")
    logger.info(f"params.template_strategy: {batch_in.params.template_strategy}")
    logger.info(f"params.output_schema_id: {batch_in.params.output_schema_id}")
    
    try:
        # 验证模型配置
        model_config = session.get(LLMConfig, batch_in.params.model_config_id)
        if not model_config:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        if not model_config.is_active:
            raise HTTPException(status_code=400, detail="模型配置未启用")
        
        # 根据 app_type 验证识别方式是否在允许列表中
        allowed_modes = ["llm_extract", "ocr_llm", "template"]
        if model_config.app_type == "chat":
            allowed_modes = ["llm_extract", "ocr_llm"]
        elif model_config.app_type == "workflow":
            allowed_modes = ["llm_extract", "ocr_llm", "template"]
        elif model_config.app_type == "completion":
            allowed_modes = ["llm_extract"]
        
        if batch_in.params.recognition_mode not in allowed_modes:
            raise HTTPException(status_code=400, detail=f"识别方式 {batch_in.params.recognition_mode} 不在允许列表中")
        
        # 验证所有文件是否存在
        logger.info("--- 验证文件 ---")
        invoices = []
        for idx, file_id in enumerate(batch_in.uploaded_file_ids):
            logger.info(f"验证文件 [{idx}]: file_id={file_id} (类型: {type(file_id)})")
            try:
                # 如果file_id是字符串，尝试转换为UUID
                from uuid import UUID
                if isinstance(file_id, str):
                    file_uuid = UUID(file_id)
                else:
                    file_uuid = file_id
                
                # 检查文件状态：只要文件状态不是成功状态（processed），都可以再次识别
                from app.models.models_invoice import InvoiceFile
                invoice_file = session.get(InvoiceFile, file_uuid)
                if invoice_file:
                    # 如果文件状态是 "processed"（成功状态），不允许再次识别
                    if invoice_file.status == "processed":
                        logger.warning(f"文件 [{idx}] 状态为成功（processed），跳过创建识别任务。文件: {invoice_file.file_name}")
                        continue  # 跳过这个文件，继续处理下一个
                    logger.info(f"文件 [{idx}] 状态检查通过：文件ID={invoice_file.id}, 状态={invoice_file.status}, 允许创建识别任务")
                
                logger.info(f"  转换后的UUID: {file_uuid}")
                
                # 通过file_id查找invoice
                invoice = session.exec(
                    select(Invoice).where(Invoice.file_id == file_uuid)
                ).first()
                
                if not invoice:
                    logger.error(f"  文件ID {file_id} 对应的票据不存在")
                    raise HTTPException(status_code=404, detail=f"文件ID {file_id} 对应的票据不存在")
                
                logger.info(f"  找到票据: invoice_id={invoice.id}, invoice_no={invoice.invoice_no}")
                invoices.append(invoice)
            except ValueError as e:
                logger.error(f"  文件ID格式错误: {file_id}, 错误: {str(e)}")
                raise HTTPException(status_code=400, detail=f"文件ID格式错误: {file_id}")
            except Exception as e:
                logger.error(f"  验证文件时出错: {str(e)}")
                raise
        
        # 构建参数快照（将UUID转换为字符串以便JSON序列化）
        params_dict = batch_in.params.model_dump()
        # 将UUID对象转换为字符串
        def convert_uuid_to_str(obj):
            """递归将UUID对象转换为字符串"""
            if isinstance(obj, UUID):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_uuid_to_str(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_uuid_to_str(item) for item in obj]
            else:
                return obj
        
        # 模板策略处理（批量任务也支持模板）
        template_id = None
        template_prompt = None
        logger.info(f"批量任务 - 模板策略: {batch_in.params.template_strategy}, template_id: {batch_in.params.template_id}")
        if batch_in.params.template_strategy == "fixed":
            # 用户指定模板，获取模板的 prompt
            if batch_in.params.template_id:
                # 确保 template_id 是 UUID 类型
                from uuid import UUID
                if isinstance(batch_in.params.template_id, str):
                    template_id = UUID(batch_in.params.template_id)
                else:
                    template_id = batch_in.params.template_id
                
                logger.info(f"批量任务 - 设置 template_id: {template_id} (类型: {type(template_id)})")
                from app.models.models_invoice import Template
                try:
                    template = session.get(Template, template_id)
                    if template:
                        # 安全获取 prompt 字段
                        template_prompt = None
                        try:
                            # 首先尝试直接获取
                            template_prompt = getattr(template, 'prompt', None)
                            logger.info(f"批量任务 - getattr获取prompt结果: {template_prompt is not None}, 值长度: {len(template_prompt) if template_prompt else 0}")
                        except Exception as e:
                            logger.warning(f"批量任务 - getattr获取prompt失败: {str(e)}")
                        
                        # 如果 getattr 返回 None 或空字符串，尝试使用 SQL 查询
                        if not template_prompt:
                            try:
                                from sqlalchemy import text
                                logger.info(f"批量任务 - 尝试通过SQL查询模板prompt")
                                result = session.execute(
                                    text("SELECT prompt FROM template WHERE id = :id"),
                                    {"id": str(template.id)}
                                ).fetchone()
                                if result and result[0]:
                                    template_prompt = result[0]
                                    logger.info(f"批量任务 - SQL查询成功获取prompt，长度: {len(template_prompt)} 字符")
                                else:
                                    logger.warning(f"批量任务 - SQL查询返回空结果")
                            except Exception as e:
                                logger.warning(f"批量任务 - 通过SQL查询模板prompt失败: {str(e)}")
                        
                        if template_prompt:
                            logger.info(f"批量任务 - 最终获取到模板提示词，长度: {len(template_prompt)} 字符")
                        else:
                            logger.warning(f"批量任务 - 模板 {template_id} 没有设置 prompt 字段")
                    else:
                        logger.warning(f"批量任务 - 模板 {template_id} 不存在，但会使用 params 中的 template_id")
                except Exception as e:
                    logger.error(f"批量任务 - 查询模板失败: {str(e)}，但会使用 params 中的 template_id")
        
        # 如果获取到模板提示词，添加到参数中
        if template_prompt:
            params_dict["template_prompt"] = template_prompt
        
        params_dict = convert_uuid_to_str(params_dict)
        logger.info(f"转换后的参数字典: {json.dumps(params_dict, ensure_ascii=False, indent=2)}")
        
        # 批量创建任务
        created_tasks = []
        for invoice in invoices:
            # 生成任务编号
            task_no = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}"
            
            logger.info(f"批量任务 - 创建任务，template_id: {template_id} (类型: {type(template_id)})")
            task = RecognitionTask(
                task_no=task_no,
                invoice_id=invoice.id,
                template_id=template_id,
                params=params_dict,
                priority=0,
                operator_id=current_user.id,
                status="pending",
                provider="dify"
            )
            session.add(task)
            created_tasks.append(task)
        
        session.commit()
        
        # 刷新所有任务
        for task in created_tasks:
            session.refresh(task)
        
        result = {
            "batch_id": str(uuid4()),
            "count": len(created_tasks),
            "task_ids": [str(task.id) for task in created_tasks],
            "message": f"成功创建 {len(created_tasks)} 个识别任务"
        }
        
        logger.info("--- 创建结果 ---")
        logger.info(f"成功创建任务数: {len(created_tasks)}")
        logger.info(f"任务ID列表: {result['task_ids']}")
        logger.info("=" * 80)
        logger.info("=== 批量创建识别任务完成 ===")
        logger.info("=" * 80)
        
        return result
    except HTTPException as e:
        logger.error(f"HTTP异常: {e.status_code} - {e.detail}")
        logger.info("=" * 80)
        raise
    except Exception as e:
        logger.error(f"批量创建任务失败: {str(e)}", exc_info=True)
        logger.info("=" * 80)
        raise HTTPException(status_code=500, detail=f"批量创建任务失败: {str(e)}")


@router.get("/query")
def query_invoices(
    *,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    invoice_no: str | None = None,
    supplier: str | None = None,
    buyer: str | None = None,
    review_status: str | None = None,
    recognition_status: str | None = None,
    current_user: CurrentUser
) -> Any:
    """
    查询票据
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"=== 票据查询开始 ===")
        logger.info(f"查询参数: skip={skip}, limit={limit}, invoice_no={invoice_no}, supplier={supplier}, buyer={buyer}, review_status={review_status}, recognition_status={recognition_status}")
        
        statement = select(Invoice)
        
        # 构建查询条件（使用 AND 关系，不是 OR）
        conditions = []
        if invoice_no:
            logger.debug(f"添加查询条件: invoice_no contains '{invoice_no}'")
            conditions.append(Invoice.invoice_no.contains(invoice_no))
        if supplier:
            logger.debug(f"添加查询条件: supplier_name contains '{supplier}'")
            conditions.append(Invoice.supplier_name.contains(supplier))
        if buyer:
            logger.debug(f"添加查询条件: buyer_name contains '{buyer}'")
            conditions.append(Invoice.buyer_name.contains(buyer))
        if review_status:
            logger.debug(f"添加查询条件: review_status = '{review_status}'")
            conditions.append(Invoice.review_status == review_status)
        if recognition_status:
            logger.debug(f"添加查询条件: recognition_status = '{recognition_status}'")
            conditions.append(Invoice.recognition_status == recognition_status)
        
        # 添加公司过滤条件（超级用户可以查看所有，普通用户只能查看自己公司的）
        statement, conditions = add_company_filter(statement, current_user, conditions)
        logger.debug(f"应用了 {len(conditions)} 个查询条件（AND关系）")
        
        # 总数
        count_statement = select(func.count()).select_from(Invoice)
        if conditions:
            count_statement = count_statement.where(and_(*conditions))
        total = session.exec(count_statement).one()
        logger.info(f"查询总数: {total}")
        
        # 分页查询
        invoices = session.exec(statement.order_by(Invoice.create_time.desc()).offset(skip).limit(limit)).all()
        logger.info(f"返回记录数: {len(invoices)}")
        
        # 批量获取公司代码
        from app.models.models_company import Company
        company_ids = set()
        for inv in invoices:
            # 安全地获取company_id，如果字段不存在则返回None
            try:
                company_id = getattr(inv, 'company_id', None)
                if company_id:
                    company_ids.add(company_id)
            except Exception:
                pass
        
        companies_dict = {}
        if company_ids:
            try:
                companies = session.exec(select(Company).where(Company.id.in_(list(company_ids)))).all()
                companies_dict = {c.id: c.code for c in companies}
            except Exception as e:
                logger.warning(f"获取公司代码失败: {str(e)}")
        
        logger.info("=== 票据查询结束 ===")
        
        return {
            "data": [
                InvoiceResponse(
                    id=inv.id,
                    invoice_no=inv.invoice_no,
                    invoice_type=inv.invoice_type,
                    invoice_date=inv.invoice_date,
                    amount=inv.amount,
                    tax_amount=inv.tax_amount,
                    total_amount=inv.total_amount,
                    currency=inv.currency,
                    supplier_name=inv.supplier_name,
                    supplier_tax_no=inv.supplier_tax_no,
                    buyer_name=inv.buyer_name,
                    buyer_tax_no=inv.buyer_tax_no,
                    recognition_accuracy=inv.recognition_accuracy,
                    recognition_status=inv.recognition_status,
                    review_status=inv.review_status,
                    company_id=getattr(inv, 'company_id', None),
                    company_code=companies_dict.get(getattr(inv, 'company_id', None)) if getattr(inv, 'company_id', None) else None,
                    create_time=inv.create_time
                ).model_dump()
                for inv in invoices
            ],
            "count": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"查询失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/files/list")
def get_invoice_files_list(
    *,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    file_name: str | None = None,
    invoice_no: str | None = None,
    file_status: str | None = None,
    recognition_status: str | None = None,
    review_status: str | None = None,
    uploader_id: UUID | None = None,
    current_user: CurrentUser
) -> Any:
    """
    获取票据文件列表 - 用于状态追踪和管理
    包含文件、票据、识别、审核等综合信息
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"=== 获取票据文件列表 ===")
        logger.info(f"查询参数: skip={skip}, limit={limit}, file_name={file_name}, invoice_no={invoice_no}, file_status={file_status}, recognition_status={recognition_status}, review_status={review_status}, uploader_id={uploader_id}")
        
        # 导入User模型
        from app.models.models import User
        
        # 构建查询：从InvoiceFile开始，关联Invoice
        statement = select(InvoiceFile, Invoice).join(Invoice, Invoice.file_id == InvoiceFile.id)
        
        # 构建查询条件
        conditions = []
        if file_name:
            conditions.append(InvoiceFile.file_name.contains(file_name))
        if invoice_no:
            conditions.append(Invoice.invoice_no.contains(invoice_no))
        if file_status:
            conditions.append(InvoiceFile.status == file_status)
        if recognition_status:
            conditions.append(Invoice.recognition_status == recognition_status)
        if review_status:
            conditions.append(Invoice.review_status == review_status)
        if uploader_id:
            conditions.append(InvoiceFile.uploader_id == uploader_id)
        
        # 添加公司过滤条件（超级用户可以查看所有，普通用户只能查看自己公司的）
        if not current_user.is_superuser:
            if current_user.company_id:
                conditions.append(Invoice.company_id == current_user.company_id)
            else:
                # 如果用户没有关联公司，返回空结果
                conditions.append(Invoice.company_id.is_(None))
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        # 总数查询
        count_statement = select(func.count()).select_from(InvoiceFile).join(Invoice, Invoice.file_id == InvoiceFile.id)
        if conditions:
            count_statement = count_statement.where(and_(*conditions))
        total = session.exec(count_statement).one()
        
        # 分页查询，按上传时间倒序
        results = session.exec(
            statement.order_by(InvoiceFile.upload_time.desc()).offset(skip).limit(limit)
        ).all()
        
        # 获取所有相关的用户ID
        user_ids = set()
        invoice_ids = []
        
        for invoice_file, invoice in results:
            user_ids.add(invoice_file.uploader_id)
            user_ids.add(invoice.creator_id)
            if invoice.reviewer_id:
                user_ids.add(invoice.reviewer_id)
            invoice_ids.append(invoice.id)
        
        # 批量查询用户信息
        users_dict = {}
        if user_ids:
            users = session.exec(select(User).where(User.id.in_(list(user_ids)))).all()
            users_dict = {user.id: user for user in users}
        
        # 模板信息查询（模板功能已废弃，返回空字典）
        templates_dict = {}
        
        # 批量查询识别任务数量
        task_counts = {}
        if invoice_ids:
            # 一次性查询所有任务，然后在Python中处理（避免UUID的max()问题和N+1查询）
            # 显式指定需要的列，避免 SQLModel 元数据缓存问题
            from sqlalchemy import desc
            all_tasks = session.exec(
                select(
                    RecognitionTask.id,
                    RecognitionTask.invoice_id,
                    RecognitionTask.create_time
                )
                .where(RecognitionTask.invoice_id.in_(invoice_ids))
                .order_by(RecognitionTask.invoice_id, RecognitionTask.create_time.desc())
            ).all()
            
            # 按invoice_id分组，统计数量和最新任务ID
            for row in all_tasks:
                # row 是元组 (id, invoice_id, create_time)
                task_id, invoice_id, _ = row
                if invoice_id not in task_counts:
                    task_counts[invoice_id] = {'count': 0, 'last_task_id': None}
                task_counts[invoice_id]['count'] += 1
                # 第一个任务（按create_time倒序）就是最新的
                if task_counts[invoice_id]['last_task_id'] is None:
                    task_counts[invoice_id]['last_task_id'] = task_id
        
        # 批量获取公司代码
        from app.models.models_company import Company
        company_ids = {inv.company_id for _, inv in results if getattr(inv, 'company_id', None)}
        companies_dict = {}
        if company_ids:
            companies = session.exec(select(Company).where(Company.id.in_(list(company_ids)))).all()
            companies_dict = {c.id: c.code for c in companies}
        
        # 构建响应数据
        list_items = []
        for invoice_file, invoice in results:
            # 获取用户名称
            uploader = users_dict.get(invoice_file.uploader_id)
            creator = users_dict.get(invoice.creator_id)
            reviewer = users_dict.get(invoice.reviewer_id) if invoice.reviewer_id else None
            
            # 模板信息（模板功能已废弃）
            # template = None  # 模板功能已废弃，不再查询
            
            # 获取识别任务信息
            task_info = task_counts.get(invoice.id, {'count': 0, 'last_task_id': None})
            
            # 获取最新识别结果的时间
            latest_result = session.exec(
                select(RecognitionResult)
                .where(RecognitionResult.invoice_id == invoice.id)
                .order_by(RecognitionResult.recognition_time.desc())
                .limit(1)
            ).first()
            
            list_item = InvoiceFileListItem(
                # 文件基本信息
                file_id=invoice_file.id,
                file_name=invoice_file.file_name,
                file_size=invoice_file.file_size,
                file_type=invoice_file.file_type,
                file_hash=invoice_file.file_hash,
                upload_time=invoice_file.upload_time,
                
                # 票据基本信息
                invoice_id=invoice.id,
                invoice_no=invoice.invoice_no,
                invoice_type=invoice.invoice_type,
                invoice_date=invoice.invoice_date,
                
                # 金额信息
                amount=invoice.amount,
                tax_amount=invoice.tax_amount,
                total_amount=invoice.total_amount,
                
                # 供应商和采购方信息
                supplier_name=invoice.supplier_name,
                supplier_tax_no=invoice.supplier_tax_no,
                buyer_name=invoice.buyer_name,
                buyer_tax_no=invoice.buyer_tax_no,
                
                # 状态信息
                file_status=invoice_file.status,
                recognition_status=invoice.recognition_status,
                review_status=invoice.review_status,
                
                # 识别信息
                recognition_accuracy=invoice.recognition_accuracy,
                recognition_time=latest_result.recognition_time if latest_result else None,
                recognition_task_count=task_info['count'],
                last_recognition_task_id=task_info['last_task_id'],
                
                # 审核信息
                reviewer_name=reviewer.email if reviewer else None,
                review_time=invoice.review_time,
                review_comment=invoice.review_comment,
                
                # 用户信息
                uploader_name=uploader.email if uploader else None,
                creator_name=creator.email if creator else None,
                
                # 公司信息
                company_id=getattr(invoice, 'company_id', None),
                company_code=companies_dict.get(getattr(invoice, 'company_id', None)) if getattr(invoice, 'company_id', None) else None,
                
                # 模板信息（模板功能已废弃）
                template_id=None,
                template_name=None,  # 模板功能已废弃
                
                # 时间信息
                create_time=invoice.create_time,
                update_time=invoice.update_time,
                
                # 备注
                remark=invoice.remark
            )
            list_items.append(list_item)
        
        logger.info(f"查询完成，共 {total} 条记录，返回 {len(list_items)} 条")
        
        return {
            "data": [item.model_dump() for item in list_items],
            "count": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    *,
    session: SessionDep,
    invoice_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    获取票据详情
    """
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="票据不存在")
    
    # 检查权限：如果不是超级用户，只能查看自己公司的发票
    if not current_user.is_superuser:
        if invoice.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="无权访问此票据")
    
    # 获取公司代码
    company_code = None
    if invoice.company_id:
        from app.models.models_company import Company
        company = session.get(Company, invoice.company_id)
        if company:
            company_code = company.code
    
    # 获取最新失败任务的错误信息
    error_code = None
    error_message = None
    if invoice.recognition_status == "failed":
        failed_task = session.exec(
            select(RecognitionTask)
            .where(
                RecognitionTask.invoice_id == invoice_id,
                RecognitionTask.status == "failed"
            )
            .order_by(RecognitionTask.create_time.desc())
        ).first()
        if failed_task:
            error_code = failed_task.error_code
            error_message = failed_task.error_message
    
    return InvoiceResponse(
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
        company_code=company_code,
        create_time=invoice.create_time,
        error_code=error_code,
        error_message=error_message
    )


@router.get("/{invoice_id}/file")
def get_invoice_file(
    *,
    session: SessionDep,
    invoice_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    获取票据关联的文件信息
    """
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="票据不存在")
    
    invoice_file = session.get(InvoiceFile, invoice.file_id)
    if not invoice_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return {
        "id": str(invoice_file.id),
        "file_name": invoice_file.file_name,
        "file_path": invoice_file.file_path,
        "file_hash": invoice_file.file_hash,
        "mime_type": invoice_file.mime_type,
        "file_type": invoice_file.file_type
    }


@router.get("/{invoice_id}/file/download")
def download_invoice_file(
    *,
    session: SessionDep,
    invoice_id: UUID,
    current_user: CurrentUser
):
    """
    下载票据关联的文件
    """
    from fastapi.responses import FileResponse
    
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="票据不存在")
    
    invoice_file = session.get(InvoiceFile, invoice.file_id)
    if not invoice_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_path = Path(invoice_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在于服务器")
    
    return FileResponse(
        path=str(file_path),
        filename=invoice_file.file_name,
        media_type=invoice_file.mime_type
    )


@router.get("/{invoice_id}/items")
def get_invoice_items(
    *,
    session: SessionDep,
    invoice_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    获取票据行项目列表
    """
    # 验证票据是否存在
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="票据不存在")
    
    # 查询该票据的所有行项目
    items = session.exec(
        select(InvoiceItem).where(InvoiceItem.id == invoice_id).order_by(InvoiceItem.line_no)
    ).all()
    
    return {
        "data": [
            {
                "line_no": item.line_no,
                "name": item.name,
                "part_no": item.part_no,
                "supplier_partno": item.supplier_partno,
                "unit": item.unit,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "amount": item.amount,
                "tax_rate": item.tax_rate,
                "tax_amount": item.tax_amount
            }
            for item in items
        ],
        "count": len(items)
    }


@router.put("/{invoice_id}/items", response_model=Message)
def update_invoice_items(
    *,
    session: SessionDep,
    invoice_id: UUID,
    items_in: InvoiceItemsBatchUpdate,
    current_user: CurrentUser
) -> Any:
    """
    批量更新票据行项目
    """
    # 验证票据是否存在
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="票据不存在")
    
    # 获取当前所有行项目
    existing_items = session.exec(
        select(InvoiceItem).where(InvoiceItem.id == invoice_id).order_by(InvoiceItem.line_no)
    ).all()
    
    # 创建行号到行项目的映射
    item_map = {(item.id, item.invoice_no, item.line_no): item for item in existing_items}
    
    # 更新或创建行项目
    for item_update in items_in.items:
        key = (invoice_id, invoice.invoice_no, item_update.line_no)
        if key in item_map:
            # 更新现有行项目
            item = item_map[key]
            update_data = item_update.model_dump(exclude_unset=True, exclude={'line_no'})
            for field, value in update_data.items():
                setattr(item, field, value)
            item.update_time = datetime.now()
            session.add(item)
        else:
            # 创建新行项目
            new_item = InvoiceItem(
                id=invoice_id,
                invoice_no=invoice.invoice_no,
                line_no=item_update.line_no,
                **item_update.model_dump(exclude_unset=True, exclude={'line_no'})
            )
            session.add(new_item)
    
    session.commit()
    return Message(message="行项目更新成功")


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    *,
    session: SessionDep,
    invoice_id: UUID,
    invoice_in: InvoiceUpdate,
    current_user: CurrentUser
) -> Any:
    """
    更新票据信息
    """
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="票据不存在")
    
    # 更新字段
    update_data = invoice_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    invoice.update_time = datetime.now()
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    
    return InvoiceResponse(
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
        create_time=invoice.create_time
    )


@router.get("/review/pending")
def get_pending_reviews(
    *,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    current_user: CurrentUser
) -> Any:
    """
    获取待审核票据列表
    """
    try:
        statement = select(Invoice).where(Invoice.review_status == "pending")
        
        # 添加公司过滤条件（超级用户可以查看所有，普通用户只能查看自己公司的）
        conditions = [Invoice.review_status == "pending"]
        statement, conditions = add_company_filter(statement, current_user, conditions)
        
        # 总数
        count_statement = select(func.count()).select_from(Invoice).where(and_(*conditions))
        total = session.exec(count_statement).one()
        
        # 分页查询
        invoices = session.exec(statement.order_by(Invoice.create_time.desc()).offset(skip).limit(limit)).all()
        
        # 批量获取公司代码
        from app.models.models_company import Company
        company_ids = {inv.company_id for inv in invoices if inv.company_id}
        companies_dict = {}
        if company_ids:
            companies = session.exec(select(Company).where(Company.id.in_(list(company_ids)))).all()
            companies_dict = {c.id: c.code for c in companies}
        
        return {
            "data": [
                InvoiceResponse(
                    id=inv.id,
                    invoice_no=inv.invoice_no,
                    invoice_type=inv.invoice_type,
                    invoice_date=inv.invoice_date,
                    amount=inv.amount,
                    tax_amount=inv.tax_amount,
                    total_amount=inv.total_amount,
                    currency=inv.currency,
                    supplier_name=inv.supplier_name,
                    supplier_tax_no=inv.supplier_tax_no,
                    buyer_name=inv.buyer_name,
                    buyer_tax_no=inv.buyer_tax_no,
                    recognition_accuracy=inv.recognition_accuracy,
                    recognition_status=inv.recognition_status,
                    review_status=inv.review_status,
                    company_id=inv.company_id,
                    company_code=companies_dict.get(inv.company_id) if inv.company_id else None,
                    create_time=inv.create_time
                ).model_dump()
                for inv in invoices
            ],
            "count": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


class ReviewRequest(SQLModel):
    comment: str | None = None


@router.post("/review/{invoice_id}/approve", response_model=Message)
def approve_invoice(
    *,
    session: SessionDep,
    invoice_id: UUID,
    review_request: ReviewRequest | None = None,
    current_user: CurrentUser
) -> Any:
    """
    审核通过票据
    """
    try:
        invoice = session.get(Invoice, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="票据不存在")
        
        if invoice.review_status != "pending":
            raise HTTPException(status_code=400, detail=f"票据状态为 {invoice.review_status}，无法审核")
        
        comment = review_request.comment if review_request else None
        
        # 更新票据审核状态
        invoice.review_status = "approved"
        invoice.reviewer_id = current_user.id
        invoice.review_time = datetime.now()
        if comment:
            invoice.review_comment = comment
        session.add(invoice)
        
        # 创建审核记录
        review_record = ReviewRecord(
            invoice_id=invoice_id,
            review_status="approved",
            review_comment=comment,
            reviewer_id=current_user.id
        )
        session.add(review_record)
        session.commit()
        
        return Message(message="审核通过")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")


class RejectRequest(SQLModel):
    comment: str = Field(..., description="审核意见（必填）")


@router.post("/review/{invoice_id}/reject", response_model=Message)
def reject_invoice(
    *,
    session: SessionDep,
    invoice_id: UUID,
    reject_request: RejectRequest,
    current_user: CurrentUser
) -> Any:
    """
    审核拒绝票据
    """
    try:
        invoice = session.get(Invoice, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="票据不存在")
        
        if invoice.review_status != "pending":
            raise HTTPException(status_code=400, detail=f"票据状态为 {invoice.review_status}，无法审核")
        
        if not reject_request.comment or len(reject_request.comment.strip()) == 0:
            raise HTTPException(status_code=400, detail="拒绝审核必须提供审核意见")
        
        # 更新票据审核状态
        invoice.review_status = "rejected"
        invoice.reviewer_id = current_user.id
        invoice.review_time = datetime.now()
        invoice.review_comment = reject_request.comment
        session.add(invoice)
        
        # 创建审核记录
        review_record = ReviewRecord(
            invoice_id=invoice_id,
            review_status="rejected",
            review_comment=reject_request.comment,
            reviewer_id=current_user.id
        )
        session.add(review_record)
        session.commit()
        
        return Message(message="已拒绝")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")


@router.get("/recognition-results")
def get_recognition_results(
    *,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    invoice_id: UUID | None = None,
    current_user: CurrentUser
) -> Any:
    """
    获取识别结果列表
    """
    try:
        statement = select(RecognitionResult)
        
        if invoice_id:
            statement = statement.where(RecognitionResult.invoice_id == invoice_id)
        
        # 总数
        count_statement = select(func.count()).select_from(RecognitionResult)
        if invoice_id:
            count_statement = count_statement.where(RecognitionResult.invoice_id == invoice_id)
        total = session.exec(count_statement).one()
        
        # 分页查询
        results = session.exec(statement.order_by(RecognitionResult.recognition_time.desc()).offset(skip).limit(limit)).all()
        
        return {
            "data": [
                RecognitionResultResponse(
                    id=result.id,
                    invoice_id=result.invoice_id,
                    total_fields=result.total_fields,
                    recognized_fields=result.recognized_fields,
                    accuracy=result.accuracy,
                    confidence=result.confidence,
                    status=result.status,
                    recognition_time=result.recognition_time
                ).model_dump()
                for result in results
            ],
            "count": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/recognition-results/{result_id}/fields")
def get_recognition_fields(
    *,
    session: SessionDep,
    result_id: UUID,
    current_user: CurrentUser
) -> Any:
    """
    获取识别结果的所有字段
    """
    try:
        result = session.get(RecognitionResult, result_id)
        if not result:
            raise HTTPException(status_code=404, detail="识别结果不存在")
        
        statement = select(RecognitionField).where(RecognitionField.result_id == result_id)
        fields = session.exec(statement).all()
        
        return {
            "data": [
                {
                    "id": str(field.id),
                    "field_name": field.field_name,
                    "field_value": field.field_value,
                    "original_value": field.original_value,
                    "confidence": field.confidence,
                    "accuracy": field.accuracy,
                    "is_manual_corrected": field.is_manual_corrected
                }
                for field in fields
            ],
            "count": len(fields)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{invoice_id}/schema-validation-status")
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

        # 获取模型配置（从 llm_config 表）
        model_config = None
        if task.params and task.params.get("model_config_id"):
            try:
                model_config = session.get(LLMConfig, UUID(task.params.get("model_config_id")))
            except:
                pass

        # 获取Schema信息（从任务参数中获取 output_schema_id）
        schema_info = None
        if task.params and task.params.get("output_schema_id"):
            try:
                schema_id = task.params.get("output_schema_id")
                schema = session.get(OutputSchema, UUID(schema_id) if isinstance(schema_id, str) else schema_id)
                if schema and schema.is_active:
                    schema_info = {
                        "id": str(schema.id),
                        "name": schema.name,
                        "version": schema.version
                    }
            except Exception as e:
                logger.warning(f"获取Schema信息失败: {str(e)}")

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
        logger.error(f"获取Schema验证状态失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取Schema验证状态失败: {str(e)}")
