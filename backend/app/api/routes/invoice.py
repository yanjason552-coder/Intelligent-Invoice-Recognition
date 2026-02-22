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
from sqlalchemy import inspect, text

from app.api.deps import SessionDep, CurrentUser
from app.models import Message
from app.models.models_invoice import (
    Invoice, InvoiceFile, InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    RecognitionTask, RecognitionTaskCreate, RecognitionTaskResponse, RecognitionTaskBatchCreate,
    RecognitionResult, RecognitionResultResponse,
    RecognitionField, ReviewRecord, InvoiceFileListItem,
    OutputSchema, LLMConfig, InvoiceItem, InvoiceItemUpdate, InvoiceItemsBatchUpdate,
    SchemaValidationRecord, Template
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


# 辅助函数：安全地查询 RecognitionTask，避免查询不存在的 template_version_id 字段
def _safe_get_recognition_task(session: SessionDep, task_id: UUID):
    """
    安全地获取 RecognitionTask，排除可能不存在的 template_version_id 字段
    使用原始 SQL 查询，避免 SQLAlchemy 自动包含模型中的所有字段
    """
    try:
        # 尝试获取表结构
        try:
            inspector = inspect(session.bind)
            columns = [col['name'] for col in inspector.get_columns('recognition_task')]
        except Exception as e:
            logger.warning(f"无法获取表结构，使用默认字段列表: {e}")
            columns = [
                'id', 'task_no', 'invoice_id', 'template_id', 'params', 'status',
                'priority', 'start_time', 'end_time', 'duration', 'error_message',
                'error_code', 'provider', 'request_id', 'trace_id', 'operator_id', 'create_time'
            ]
        
        # 构建基本字段列表
        base_fields = [
            'id', 'task_no', 'invoice_id', 'template_id', 'params', 'status',
            'priority', 'start_time', 'end_time', 'duration', 'error_message',
            'error_code', 'provider', 'request_id', 'trace_id', 'operator_id', 'create_time'
        ]
        
        # 如果 template_version_id 字段存在，也包含它
        if 'template_version_id' in columns:
            base_fields.insert(4, 'template_version_id')
        
        existing_fields = [f for f in base_fields if f in columns]
        if not existing_fields:
            existing_fields = ['id', 'task_no', 'invoice_id', 'template_id', 'params', 'status']
        
        fields_str = ', '.join(existing_fields)
        
        sql = f"""
            SELECT {fields_str}
            FROM recognition_task
            WHERE id = :task_id
        """
        
        result = session.execute(text(sql), {"task_id": str(task_id)})
        row = result.fetchone()
        
        if not row:
            return None
        
        # 创建简单的对象
        class SimpleTask:
            def __init__(self, row_data):
                for field, value in zip(existing_fields, row_data):
                    setattr(self, field, value)
            def __getattr__(self, name):
                return None
        
        return SimpleTask(row)
        
    except Exception as e:
        logger.error(f"安全查询 RecognitionTask 失败: {e}", exc_info=True)
        # 回退到直接查询（可能会失败）
        try:
            return session.get(RecognitionTask, task_id)
        except Exception:
            return None


def _safe_query_recognition_tasks(session: SessionDep, where_clause: str = "", params: dict = None):
    """
    安全地查询 RecognitionTask 列表，排除可能不存在的 template_version_id 字段
    """
    try:
        # 尝试获取表结构
        try:
            inspector = inspect(session.bind)
            columns = [col['name'] for col in inspector.get_columns('recognition_task')]
        except Exception as e:
            logger.warning(f"无法获取表结构，使用默认字段列表: {e}")
            columns = [
                'id', 'task_no', 'invoice_id', 'template_id', 'params', 'status',
                'priority', 'start_time', 'end_time', 'duration', 'error_message',
                'error_code', 'provider', 'request_id', 'trace_id', 'operator_id', 'create_time'
            ]
        
        # 构建基本字段列表
        base_fields = [
            'id', 'task_no', 'invoice_id', 'template_id', 'params', 'status',
            'priority', 'start_time', 'end_time', 'duration', 'error_message',
            'error_code', 'provider', 'request_id', 'trace_id', 'operator_id', 'create_time'
        ]
        
        # 如果 template_version_id 字段存在，也包含它
        if 'template_version_id' in columns:
            base_fields.insert(4, 'template_version_id')
        
        existing_fields = [f for f in base_fields if f in columns]
        if not existing_fields:
            existing_fields = ['id', 'task_no', 'invoice_id', 'template_id', 'params', 'status']
        
        fields_str = ', '.join(existing_fields)
        
        sql = f"""
            SELECT {fields_str}
            FROM recognition_task
            {where_clause}
        """
        
        result = session.execute(text(sql), params or {})
        rows = result.fetchall()
        
        # 创建简单的对象
        class SimpleTask:
            def __init__(self, row_data):
                for field, value in zip(existing_fields, row_data):
                    setattr(self, field, value)
            def __getattr__(self, name):
                return None
        
        return [SimpleTask(row) for row in rows]
        
    except Exception as e:
        logger.error(f"安全查询 RecognitionTask 列表失败: {e}", exc_info=True)
        return []


# 辅助函数：检查用户是否有权限访问发票
def check_invoice_permission(invoice: Invoice, current_user: CurrentUser) -> bool:
    """
    检查用户是否有权限访问发票
    规则：
    1. 超级用户可以访问所有发票
    2. 普通用户只能访问自己公司的发票（user.company_id = invoice.company_id）
    3. 如果用户没有维护所属公司（company_id为null），则无权访问任何发票
    
    Returns:
        bool: True表示有权限，False表示无权限
    """
    # 超级用户可以访问所有发票
    if current_user.is_superuser:
        return True
    
    # 如果用户没有维护所属公司，则无权访问任何发票
    if not current_user.company_id:
        return False
    
    # 用户只能访问自己公司的发票
    return invoice.company_id == current_user.company_id


# 辅助函数：添加公司过滤条件
def add_company_filter(statement, current_user, conditions=None):
    """
    根据用户的公司ID过滤发票查询
    规则：
    1. 超级用户可以查看所有发票
    2. 普通用户只能查看自己公司的发票（user.company_id = invoice.company_id）
    3. 如果用户没有维护所属公司（company_id为null），则不展示任何发票
    """
    if conditions is None:
        conditions = []
    
    # 如果不是超级用户，添加公司过滤条件
    if not current_user.is_superuser:
        if current_user.company_id:
            # 用户有公司ID，只能查看自己公司的发票
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
        # 如果不是超级用户，需要通过发票过滤识别任务
        if not current_user.is_superuser:
            if current_user.company_id:
                # 用户有公司ID，只查询自己公司的发票的识别任务
                # 先查询符合条件的发票ID列表
                invoice_ids = session.exec(
                    select(Invoice.id).where(Invoice.company_id == current_user.company_id)
                ).all()
                if invoice_ids:
                    statement = select(RecognitionTask).where(RecognitionTask.invoice_id.in_(invoice_ids))
                    if status:
                        statement = statement.where(RecognitionTask.status == status)
                else:
                    # 用户没有可访问的发票，返回空结果
                    statement = select(RecognitionTask).where(RecognitionTask.id.is_(None))
                    if status:
                        statement = statement.where(RecognitionTask.status == status)
            else:
                # 用户没有公司ID，返回空结果
                statement = select(RecognitionTask).where(RecognitionTask.id.is_(None))
                if status:
                    statement = statement.where(RecognitionTask.status == status)
        else:
            # 超级用户可以查看所有识别任务
            statement = select(RecognitionTask)
            if status:
                statement = statement.where(RecognitionTask.status == status)
        
        # 总数查询
        count_statement = select(func.count()).select_from(RecognitionTask)
        if not current_user.is_superuser:
            if current_user.company_id:
                invoice_ids = session.exec(
                    select(Invoice.id).where(Invoice.company_id == current_user.company_id)
                ).all()
                if invoice_ids:
                    count_statement = count_statement.where(RecognitionTask.invoice_id.in_(invoice_ids))
                    if status:
                        count_statement = count_statement.where(RecognitionTask.status == status)
                else:
                    count_statement = count_statement.where(RecognitionTask.id.is_(None))
            else:
                count_statement = count_statement.where(RecognitionTask.id.is_(None))
        elif status:
            count_statement = count_statement.where(RecognitionTask.status == status)
        
        total = session.exec(count_statement).one()
        
        # 分页查询 - 使用 try-except 处理字段不存在的问题
        try:
            tasks = session.exec(statement.offset(skip).limit(limit)).all()
        except Exception as query_error:
            logger.warning(f"使用 ORM 查询失败，尝试使用安全查询: {query_error}")
            # 如果 ORM 查询失败（可能是字段不存在），使用安全查询
            try:
                session.rollback()
            except:
                pass
            
            # 构建 WHERE 条件
            where_conditions = []
            params_dict = {}
            
            if not current_user.is_superuser:
                if current_user.company_id:
                    try:
                        invoice_ids = session.exec(
                            select(Invoice.id).where(Invoice.company_id == current_user.company_id)
                        ).all()
                        if invoice_ids:
                            invoice_ids_str = [str(id) for id in invoice_ids]
                            where_conditions.append("invoice_id = ANY(:invoice_ids)")
                            params_dict["invoice_ids"] = invoice_ids_str
                        else:
                            where_conditions.append("1 = 0")
                    except:
                        where_conditions.append("1 = 0")
                else:
                    where_conditions.append("1 = 0")
            
            if status:
                where_conditions.append("status = :status")
                params_dict["status"] = status
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # 添加分页
            where_clause += f" ORDER BY create_time DESC LIMIT :limit OFFSET :offset"
            params_dict["limit"] = limit
            params_dict["offset"] = skip
            
            tasks = _safe_query_recognition_tasks(session, where_clause, params_dict)
        
        # 获取模型配置信息（用于显示模型名称）
        model_config_ids = set()
        for task in tasks:
            try:
                if hasattr(task, 'params') and task.params:
                    model_config_id = task.params.get("model_config_id")
                    if model_config_id:
                        model_config_ids.add(UUID(model_config_id))
            except Exception as e:
                logger.warning(f"提取模型配置ID失败: {e}")
                continue
        
        model_configs_dict = {}
        if model_config_ids:
            try:
                model_configs = session.exec(
                    select(LLMConfig).where(LLMConfig.id.in_(list(model_config_ids)))
                ).all()
                model_configs_dict = {config.id: config for config in model_configs}
            except Exception as e:
                logger.warning(f"获取模型配置失败: {e}")
        
        # 构建响应数据
        result_data = []
        for task in tasks:
            try:
                task_id = task.id if hasattr(task, 'id') else None
                task_no = task.task_no if hasattr(task, 'task_no') else None
                invoice_id = task.invoice_id if hasattr(task, 'invoice_id') else None
                template_id = task.template_id if hasattr(task, 'template_id') else None
                task_params = task.params if hasattr(task, 'params') else None
                task_status = task.status if hasattr(task, 'status') else None
                provider = task.provider if hasattr(task, 'provider') else None
                start_time = task.start_time if hasattr(task, 'start_time') else None
                end_time = task.end_time if hasattr(task, 'end_time') else None
                create_time = task.create_time if hasattr(task, 'create_time') else None
                
                model_name = None
                if task_params and task_params.get("model_config_id"):
                    try:
                        model_config_id = UUID(task_params.get("model_config_id"))
                        if model_config_id in model_configs_dict:
                            model_name = model_configs_dict[model_config_id].name
                    except:
                        pass
                
                recognition_mode = task_params.get("recognition_mode") if task_params else None
                
                result_data.append({
                    "id": str(task_id) if task_id else None,
                    "task_no": task_no,
                    "invoice_id": str(invoice_id) if invoice_id else None,
                    "template_id": str(template_id) if template_id else None,
                    "params": task_params,
                    "status": task_status,
                    "provider": provider,
                    "recognition_mode": recognition_mode,
                    "model_name": model_name,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                    "create_time": create_time.isoformat() if create_time else None
                })
            except Exception as e:
                logger.warning(f"构建任务响应数据失败: {e}")
                continue
        
        return {
            "data": result_data,
            "count": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"查询识别任务失败: {e}", exc_info=True)
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
        
        # 检查权限：使用统一的权限检查函数
        if not check_invoice_permission(invoice, current_user):
            raise HTTPException(status_code=403, detail="无权访问此票据")
        
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
        template_version_id = None
        template_prompt = None
        logger.info(f"模板策略: {task_in.params.template_strategy}, template_id: {task_in.params.template_id}")
        if task_in.params.template_strategy == "fixed":
            # 用户指定模板，获取模板的 prompt 和版本信息
            if task_in.params.template_id:
                # 确保 template_id 是 UUID 类型
                from uuid import UUID
                if isinstance(task_in.params.template_id, str):
                    template_id = UUID(task_in.params.template_id)
                else:
                    template_id = task_in.params.template_id
                
                logger.info(f"设置 template_id: {template_id} (类型: {type(template_id)})")
                from app.models.models_invoice import Template, TemplateVersion
                from sqlmodel import select
                try:
                    template = session.get(Template, template_id)
                    if template:
                        # 优先使用当前版本，但必须是已发布状态
                        if template.current_version_id:
                            template_version = session.get(TemplateVersion, template.current_version_id)
                            if template_version:
                                if template_version.status == "published":
                                    template_version_id = template_version.id
                                    logger.info(f"获取到模板当前版本ID: {template_version_id}, 版本号: {template_version.version} (已发布)")
                                else:
                                    # 当前版本不是已发布状态，查找最新发布的版本
                                    logger.warning(f"模板当前版本 {template_version.version} 状态为 {template_version.status}，查找最新发布的版本")
                                    latest_version = session.exec(
                                        select(TemplateVersion)
                                        .where(TemplateVersion.template_id == template_id)
                                        .where(TemplateVersion.status == "published")
                                        .order_by(TemplateVersion.published_at.desc())
                                    ).first()
                                    if latest_version:
                                        template_version_id = latest_version.id
                                        logger.info(f"获取到模板最新发布版本ID: {template_version_id}, 版本号: {latest_version.version}")
                                    else:
                                        raise HTTPException(
                                            status_code=400, 
                                            detail=f"模板 '{template.name}' 没有已发布的版本，无法用于识别。请先发布模板版本。"
                                        )
                        else:
                            # 如果没有设置当前版本，获取最新发布的版本
                            latest_version = session.exec(
                                select(TemplateVersion)
                                .where(TemplateVersion.template_id == template_id)
                                .where(TemplateVersion.status == "published")
                                .order_by(TemplateVersion.published_at.desc())
                            ).first()
                            if latest_version:
                                template_version_id = latest_version.id
                                logger.info(f"获取到模板最新发布版本ID: {template_version_id}, 版本号: {latest_version.version}")
                            else:
                                raise HTTPException(
                                    status_code=400, 
                                    detail=f"模板 '{template.name}' 没有已发布的版本，无法用于识别。请先发布模板版本。"
                                )
                        
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
        logger.info(f"创建任务，template_id: {template_id} (类型: {type(template_id)}), template_version_id: {template_version_id}")
        logger.info(f"创建任务前，template_id 值: {template_id}, 是否为 None: {template_id is None}")
        try:
            task = RecognitionTask(
                task_no=task_no,
                invoice_id=task_in.invoice_id,
                template_id=template_id,
                template_version_id=template_version_id,  # 保存模板版本ID
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
        # 使用安全查询方法，避免字段不存在的问题
        task = _safe_get_recognition_task(session, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查发票权限
        invoice = session.get(Invoice, task.invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="票据不存在")
        
        # 检查权限：使用统一的权限检查函数
        if not check_invoice_permission(invoice, current_user):
            raise HTTPException(status_code=403, detail="无权访问此票据")
        
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
        
        # 更新任务状态 - 使用原始SQL避免字段不存在的问题
        try:
            # 尝试使用ORM更新
            task.status = "processing"
            task.start_time = datetime.now()
            session.add(task)
            session.commit()
        except Exception as e:
            # 如果ORM更新失败（可能是字段不存在），使用原始SQL
            logger.warning(f"使用ORM更新任务状态失败，改用原始SQL: {e}")
            try:
                session.rollback()
                # 检查表结构，确定哪些字段存在
                inspector = inspect(session.bind)
                columns = [col['name'] for col in inspector.get_columns('recognition_task')]
                
                # 构建UPDATE语句，只更新存在的字段
                update_fields = []
                update_params = {"task_id": str(task_id)}
                
                if 'status' in columns:
                    update_fields.append("status = :status")
                    update_params["status"] = "processing"
                
                if 'start_time' in columns:
                    update_fields.append("start_time = :start_time")
                    update_params["start_time"] = datetime.now()
                
                if update_fields:
                    update_sql = f"""
                        UPDATE recognition_task
                        SET {', '.join(update_fields)}
                        WHERE id = :task_id
                    """
                    session.execute(text(update_sql), update_params)
                    session.commit()
            except Exception as sql_error:
                logger.error(f"使用原始SQL更新任务状态也失败: {sql_error}", exc_info=True)
                session.rollback()
                raise HTTPException(status_code=500, detail=f"更新任务状态失败: {str(sql_error)}")
        
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
                
                # 检查权限：使用统一的权限检查函数
                if not check_invoice_permission(invoice, current_user):
                    logger.warning(f"  用户无权访问票据: invoice_id={invoice.id}, user.company_id={current_user.company_id}, invoice.company_id={invoice.company_id}")
                    raise HTTPException(status_code=403, detail=f"无权访问文件ID {file_id} 对应的票据")
                
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
        
        # 获取模型名称和模板信息（用于更新 invoice_file 表）
        model_name = None
        template_name = None
        template_version_str = None
        template_version_id_for_file = None  # 用于后续创建任务时重用
        
        # 获取模型名称
        if model_config:
            model_name = model_config.name
            logger.info(f"批量任务 - 模型名称: {model_name}")
        
        # 获取模板名称和版本
        if template_id:
            from app.models.models_invoice import Template, TemplateVersion
            template_obj = session.get(Template, template_id)
            if template_obj:
                template_name = template_obj.name
                logger.info(f"批量任务 - 模板名称: {template_name}")
                
                # 获取模板版本ID
                if batch_in.params and hasattr(batch_in.params, 'template_version_id') and batch_in.params.template_version_id:
                    template_version_id_for_file = batch_in.params.template_version_id
                elif template_obj.current_version_id:
                    template_version_id_for_file = template_obj.current_version_id
                
                # 如果还没有找到版本ID，尝试查找最新发布的版本（使用安全查询）
                if not template_version_id_for_file:
                    try:
                        from sqlalchemy.orm import defer
                        latest_version = session.exec(
                            select(TemplateVersion)
                            .where(TemplateVersion.template_id == template_id)
                            .where(TemplateVersion.status == "published")
                            .order_by(TemplateVersion.published_at.desc())
                            .options(
                                defer(TemplateVersion.prompt),
                                defer(TemplateVersion.prompt_status),
                                defer(TemplateVersion.prompt_updated_at),
                                defer(TemplateVersion.prompt_hash),
                                defer(TemplateVersion.prompt_previous_version),
                            )
                        ).first()
                        if latest_version:
                            template_version_id_for_file = latest_version.id
                    except Exception as e:
                        logger.warning(f"批量任务 - 查找最新发布版本失败: {e}，尝试使用原始 SQL")
                        # 如果 defer 失败，使用原始 SQL 查询
                        try:
                            from sqlalchemy import text
                            result = session.execute(
                                text("""
                                    SELECT id FROM template_version 
                                    WHERE template_id = :template_id 
                                    AND status = 'published' 
                                    ORDER BY published_at DESC 
                                    LIMIT 1
                                """),
                                {"template_id": str(template_id)}
                            ).fetchone()
                            if result:
                                template_version_id_for_file = UUID(result[0])
                        except Exception as sql_error:
                            logger.error(f"批量任务 - 使用原始 SQL 查找最新发布版本也失败: {sql_error}")
                
                # 获取模板版本字符串（使用安全查询，避免查询不存在的 prompt 字段）
                if template_version_id_for_file:
                    try:
                        # 尝试使用 defer 排除可能不存在的 prompt 字段
                        from sqlalchemy.orm import defer
                        template_version_obj = session.exec(
                            select(TemplateVersion)
                            .where(TemplateVersion.id == template_version_id_for_file)
                            .options(
                                defer(TemplateVersion.prompt),
                                defer(TemplateVersion.prompt_status),
                                defer(TemplateVersion.prompt_updated_at),
                                defer(TemplateVersion.prompt_hash),
                                defer(TemplateVersion.prompt_previous_version),
                            )
                        ).first()
                        if template_version_obj:
                            template_version_str = template_version_obj.version
                            logger.info(f"批量任务 - 模板版本: {template_version_str} (ID: {template_version_id_for_file})")
                    except Exception as e:
                        logger.warning(f"批量任务 - 使用 defer 查询模板版本失败: {e}，尝试使用原始 SQL")
                        # 如果 defer 失败，使用原始 SQL 查询
                        try:
                            from sqlalchemy import text
                            result = session.execute(
                                text("SELECT version FROM template_version WHERE id = :version_id"),
                                {"version_id": str(template_version_id_for_file)}
                            ).fetchone()
                            if result:
                                template_version_str = result[0]
                                logger.info(f"批量任务 - 模板版本（SQL）: {template_version_str} (ID: {template_version_id_for_file})")
                        except Exception as sql_error:
                            logger.error(f"批量任务 - 使用原始 SQL 查询模板版本也失败: {sql_error}")
                            # 如果都失败，template_version_str 保持为 None
        
        # 批量创建任务
        created_tasks = []
        for invoice in invoices:
            # 生成任务编号
            task_no = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}"
            
            logger.info(f"批量任务 - 创建任务，template_id: {template_id} (类型: {type(template_id)})")
            # 检查 recognition_task 表是否有 template_version_id 字段
            try:
                from sqlalchemy import inspect as sql_inspect
                inspector = sql_inspect(session.bind)
                task_columns = [col['name'] for col in inspector.get_columns('recognition_task')]
                has_template_version_id = 'template_version_id' in task_columns
                logger.info(f"批量任务 - recognition_task 表列: {task_columns}, 是否有 template_version_id: {has_template_version_id}")
            except Exception as e:
                logger.warning(f"批量任务 - 检查表结构失败: {e}，假设没有 template_version_id 字段")
                has_template_version_id = False
            
            # 使用原始 SQL 插入，避免 SQLModel 尝试插入不存在的字段
            try:
                from sqlalchemy import text
                task_id = uuid4()
                
                # 构建插入字段和值
                insert_fields = ["id", "task_no", "invoice_id", "params", "status", "priority", "operator_id", "provider", "create_time"]
                insert_values = {
                    "id": str(task_id),
                    "task_no": task_no,
                    "invoice_id": str(invoice.id),
                    "params": json.dumps(params_dict),
                    "status": "pending",
                    "priority": 0,
                    "operator_id": str(current_user.id),
                    "provider": "dify",
                    "create_time": datetime.now()
                }
                
                # 如果表中有 template_id 字段，添加它
                if 'template_id' in task_columns:
                    insert_fields.append("template_id")
                    insert_values["template_id"] = str(template_id) if template_id else None
                
                # 如果表中有 template_version_id 字段，尝试获取并添加
                if has_template_version_id and template_id:
                    # 重用前面已经获取的 template_version_id_for_file
                    template_version_id_to_use = template_version_id_for_file
                    
                    if template_version_id_to_use:
                        insert_fields.append("template_version_id")
                        insert_values["template_version_id"] = str(template_version_id_to_use)
                        logger.info(f"批量任务 - 设置 template_version_id: {template_version_id_to_use}")
                
                # 使用原始 SQL 插入
                fields_str = ', '.join(insert_fields)
                values_str = ', '.join([f":{field}" for field in insert_fields])
                insert_sql = f"""
                    INSERT INTO recognition_task ({fields_str})
                    VALUES ({values_str})
                """
                session.execute(text(insert_sql), insert_values)
                
                # 创建任务对象用于返回（不添加到session，因为已经用SQL插入了）
                task = RecognitionTask(
                    id=task_id,
                    task_no=task_no,
                    invoice_id=invoice.id,
                    template_id=template_id,
                    params=params_dict,
                    priority=0,
                    operator_id=current_user.id,
                    status="pending",
                    provider="dify"
                )
                created_tasks.append(task)
                logger.info(f"批量任务 - 使用原始SQL成功创建任务: {task_id}")
            except Exception as sql_error:
                logger.error(f"批量任务 - 使用原始SQL创建任务失败: {sql_error}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"创建识别任务失败: {str(sql_error)}")
        
        # 更新 invoice_file 和 invoice 表中的模型和模板信息
        try:
            from app.models.models_invoice import InvoiceFile
            for invoice in invoices:
                # 更新 invoice_file 表
                invoice_file = session.get(InvoiceFile, invoice.file_id)
                if invoice_file:
                    # 更新模型名称、模板名称和模板版本
                    if model_name:
                        invoice_file.model_name = model_name
                        logger.info(f"批量任务 - 更新文件 {invoice_file.file_name} 的模型名称: {model_name}")
                    if template_name:
                        invoice_file.template_name = template_name
                        logger.info(f"批量任务 - 更新文件 {invoice_file.file_name} 的模板名称: {template_name}")
                    if template_version_str:
                        invoice_file.template_version = template_version_str
                        logger.info(f"批量任务 - 更新文件 {invoice_file.file_name} 的模板版本: {template_version_str}")
                    session.add(invoice_file)
                
                # 更新 invoice 表
                if model_name:
                    invoice.model_name = model_name
                    logger.info(f"批量任务 - 更新票据 {invoice.invoice_no} 的模型名称: {model_name}")
                if template_name:
                    invoice.template_name = template_name
                    logger.info(f"批量任务 - 更新票据 {invoice.invoice_no} 的模板名称: {template_name}")
                if template_version_str:
                    invoice.template_version = template_version_str
                    logger.info(f"批量任务 - 更新票据 {invoice.invoice_no} 的模板版本: {template_version_str}")
                session.add(invoice)
        except Exception as e:
            logger.warning(f"批量任务 - 更新 invoice_file 和 invoice 表失败: {e}，但不影响任务创建")
        
        session.commit()
        
        # 刷新所有任务（从数据库重新查询，因为是用原始SQL插入的）
        for task in created_tasks:
            try:
                refreshed_task = session.get(RecognitionTask, task.id)
                if refreshed_task:
                    # 更新任务对象的属性
                    for key, value in refreshed_task.__dict__.items():
                        if not key.startswith('_'):
                            setattr(task, key, value)
            except Exception as e:
                logger.warning(f"批量任务 - 刷新任务 {task.id} 失败: {e}，使用原始对象")
        
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
    model_name: str | None = None,
    template_name: str | None = None,
    current_user: CurrentUser
) -> Any:
    """
    查询票据
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"=== 票据查询开始 ===")
        logger.info(f"查询参数: skip={skip}, limit={limit}, invoice_no={invoice_no}, supplier={supplier}, buyer={buyer}, review_status={review_status}, recognition_status={recognition_status}, model_name={model_name}, template_name={template_name}")
        
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
        if model_name:
            logger.debug(f"添加查询条件: model_name = '{model_name}'")
            conditions.append(Invoice.model_name == model_name)
        if template_name:
            logger.debug(f"添加查询条件: template_name = '{template_name}'")
            conditions.append(Invoice.template_name == template_name)
        
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
                    template_name=getattr(inv, 'template_name', None),
                    template_version=getattr(inv, 'template_version', None),
                    model_name=getattr(inv, 'model_name', None),
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


@router.get("/filter-options/models")
def get_model_filter_options(
    *,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    获取模型筛选选项列表（用于下拉框）
    返回所有启用的模型配置名称
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app.models.models_invoice import LLMConfig
        from sqlalchemy import distinct
        
        # 从 LLMConfig 表获取所有启用的模型配置名称
        configs = session.exec(
            select(LLMConfig.name)
            .where(LLMConfig.is_active == True)
            .distinct()
        ).all()
        
        # 同时从 Invoice 表获取已使用的模型名称（作为补充）
        used_models_query = select(Invoice.model_name).where(Invoice.model_name.isnot(None)).distinct()
        used_models = session.exec(used_models_query).all()
        
        # 合并两个列表，去重并排序
        all_models = set()
        if configs:
            all_models.update([m for m in configs if m])
        if used_models:
            all_models.update([m for m in used_models if m])
        
        return {
            "data": sorted(list(all_models))
        }
    except Exception as e:
        logger.error(f"获取模型选项失败: {str(e)}", exc_info=True)
        # 如果表不存在，返回空列表
        return {"data": []}


@router.get("/filter-options/templates")
def get_template_filter_options(
    *,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    获取模板筛选选项列表（用于下拉框）
    返回所有启用的模板名称
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app.models.models_invoice import Template
        
        # 从 Template 表获取所有启用的模板名称
        templates = session.exec(
            select(Template.name)
            .where(Template.status == "enabled")
            .distinct()
        ).all()
        
        # 同时从 Invoice 表获取已使用的模板名称（作为补充）
        used_templates_query = select(Invoice.template_name).where(Invoice.template_name.isnot(None)).distinct()
        used_templates = session.exec(used_templates_query).all()
        
        # 合并两个列表，去重并排序
        all_templates = set()
        if templates:
            all_templates.update([t for t in templates if t])
        if used_templates:
            all_templates.update([t for t in used_templates if t])
        
        return {
            "data": sorted(list(all_templates))
        }
    except Exception as e:
        logger.error(f"获取模板选项失败: {str(e)}", exc_info=True)
        # 如果表不存在，返回空列表
        return {"data": []}


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
        # 规则：user.company_id = invoice.company_id，如果用户没有company_id则不展示任何发票
        if not current_user.is_superuser:
            if current_user.company_id:
                # 用户有公司ID，只能查看自己公司的发票
                conditions.append(Invoice.company_id == current_user.company_id)
            else:
                # 如果用户没有关联公司，返回空结果（使用一个永远为False的条件）
                conditions.append(Invoice.id.is_(None))
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        # 总数查询
        count_statement = select(func.count()).select_from(InvoiceFile).join(Invoice, Invoice.file_id == InvoiceFile.id)
        if conditions:
            count_statement = count_statement.where(and_(*conditions))
        total = session.exec(count_statement).one()
        
        # 分页查询，按上传时间倒序
        # 使用 try-except 处理字段不存在的情况
        try:
            results = session.exec(
                statement.order_by(InvoiceFile.upload_time.desc()).offset(skip).limit(limit)
            ).all()
        except Exception as e:
            if "does not exist" in str(e) or "UndefinedColumn" in str(e) or "template_name" in str(e):
                # 如果字段不存在，回滚并使用 getattr 安全访问
                logger.warning(f"ORM查询失败（字段不存在），使用安全访问: {e}")
                try:
                    session.rollback()
                except:
                    pass
                # 重新查询，但这次使用原始 SQL 只选择存在的字段
                from sqlalchemy import inspect, text
                inspector = inspect(session.bind)
                invoice_columns = [col['name'] for col in inspector.get_columns('invoice')]
                
                # 构建基本字段列表
                base_invoice_fields = [
                    'id', 'invoice_no', 'invoice_type', 'invoice_date', 'amount', 'tax_amount',
                    'total_amount', 'currency', 'supplier_name', 'supplier_tax_no',
                    'buyer_name', 'buyer_tax_no', 'file_id', 'recognition_accuracy',
                    'recognition_status', 'review_status', 'reviewer_id', 'review_time',
                    'review_comment', 'remark', 'creator_id', 'company_id', 'create_time', 'update_time'
                ]
                
                # 只添加存在的可选字段
                optional_fields = ['template_name', 'template_version', 'model_name']
                for field in optional_fields:
                    if field in invoice_columns:
                        base_invoice_fields.append(field)
                
                # 使用原始 SQL 查询
                invoice_fields_str = ', '.join([f'invoice.{f}' for f in base_invoice_fields])
                invoice_file_fields_str = ', '.join([f'invoice_file.{col["name"]}' for col in inspector.get_columns('invoice_file')])
                
                # 构建 WHERE 条件
                where_parts = []
                sql_params = {}
                param_idx = 1
                
                if file_name:
                    where_parts.append(f"invoice_file.file_name LIKE :p{param_idx}")
                    sql_params[f"p{param_idx}"] = f"%{file_name}%"
                    param_idx += 1
                if invoice_no:
                    where_parts.append(f"invoice.invoice_no LIKE :p{param_idx}")
                    sql_params[f"p{param_idx}"] = f"%{invoice_no}%"
                    param_idx += 1
                if file_status:
                    where_parts.append(f"invoice_file.status = :p{param_idx}")
                    sql_params[f"p{param_idx}"] = file_status
                    param_idx += 1
                if recognition_status:
                    where_parts.append(f"invoice.recognition_status = :p{param_idx}")
                    sql_params[f"p{param_idx}"] = recognition_status
                    param_idx += 1
                if review_status:
                    where_parts.append(f"invoice.review_status = :p{param_idx}")
                    sql_params[f"p{param_idx}"] = review_status
                    param_idx += 1
                if uploader_id:
                    where_parts.append(f"invoice_file.uploader_id = :p{param_idx}")
                    sql_params[f"p{param_idx}"] = str(uploader_id)
                    param_idx += 1
                
                # 公司过滤
                if not current_user.is_superuser:
                    if current_user.company_id:
                        where_parts.append(f"invoice.company_id = :p{param_idx}")
                        sql_params[f"p{param_idx}"] = str(current_user.company_id)
                        param_idx += 1
                    else:
                        where_parts.append("invoice.id IS NULL")
                
                where_clause = " AND ".join(where_parts) if where_parts else "1=1"
                
                sql_params['limit_param'] = limit
                sql_params['offset_param'] = skip
                
                sql = f"""
                    SELECT {invoice_file_fields_str}, {invoice_fields_str}
                    FROM invoice_file
                    JOIN invoice ON invoice.file_id = invoice_file.id
                    WHERE {where_clause}
                    ORDER BY invoice_file.upload_time DESC
                    LIMIT :limit_param OFFSET :offset_param
                """
                
                raw_results = session.execute(text(sql), sql_params).fetchall()
                
                # 转换为对象
                file_cols = [col['name'] for col in inspector.get_columns('invoice_file')]
                
                class SimpleInvoiceFile:
                    def __init__(self, row, file_cols):
                        for i, col in enumerate(file_cols):
                            setattr(self, col, row[i])
                
                class SimpleInvoice:
                    def __init__(self, row, file_cols, invoice_cols):
                        start = len(file_cols)
                        for i, col in enumerate(invoice_cols):
                            setattr(self, col, row[start + i])
                
                results = []
                for row in raw_results:
                    file_obj = SimpleInvoiceFile(row, file_cols)
                    invoice_obj = SimpleInvoice(row, file_cols, base_invoice_fields)
                    results.append((file_obj, invoice_obj))
            else:
                raise
        
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
            # 显式指定需要的列，避免查询不存在的 template_version_id 等字段
            latest_result = session.exec(
                select(
                    RecognitionResult.id,
                    RecognitionResult.invoice_id,
                    RecognitionResult.recognition_time
                )
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
                recognition_time=latest_result[2] if latest_result else None,  # latest_result 是元组 (id, invoice_id, recognition_time)
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
                
                # 模板信息（从 invoice 表读取识别时使用的快照，使用 getattr 安全访问）
                template_id=None,
                template_name=getattr(invoice, 'template_name', None),  # 从 invoice 表读取，字段不存在时返回 None
                template_version=getattr(invoice, 'template_version', None),  # 从 invoice 表读取，字段不存在时返回 None
                model_name=getattr(invoice, 'model_name', None),  # 从 invoice 表读取，字段不存在时返回 None
                
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
    logger.info(f"=== 开始获取发票详情 ===")
    logger.info(f"invoice_id: {invoice_id}")
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="票据不存在")
    
    # 检查权限：使用统一的权限检查函数
    if not check_invoice_permission(invoice, current_user):
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
        try:
            failed_tasks = _safe_query_recognition_tasks(
                session,
                where_clause="WHERE invoice_id = :invoice_id AND status = :status ORDER BY create_time DESC LIMIT 1",
                params={"invoice_id": str(invoice_id), "status": "failed"}
            )
            if failed_tasks:
                failed_task = failed_tasks[0]
                error_code = getattr(failed_task, 'error_code', None)
                error_message = getattr(failed_task, 'error_message', None)
        except Exception as e:
            logger.warning(f"查询失败任务时出错: {e}")
    
    # 获取最新识别结果的模板版本快照信息和字段值
    template_version_id = None
    field_defs_snapshot = None
    template_version = None
    normalized_fields = None
    template_name = None
    
    # 尝试查询识别结果，如果字段不存在则安全处理
    try:
        # #region agent log
        logger.info(f"🔍 DEBUG: 开始查询 recognition_result，invoice_id={invoice_id}, invoice_id类型={type(invoice_id)}")
        # #endregion

        # 首先尝试字符串查询（因为数据库中可能存储为字符串）
        latest_result_row = session.exec(
            select(
                RecognitionResult.id,
                RecognitionResult.invoice_id,
                RecognitionResult.recognition_time
            )
            .where(RecognitionResult.invoice_id == str(invoice_id))
            .order_by(RecognitionResult.recognition_time.desc())
            .limit(1)
        ).first()

        # #region agent log
        logger.info(f"🔍 DEBUG: 字符串查询结果 latest_result_row={latest_result_row is not None}")
        if latest_result_row:
            logger.info(f"🔍 DEBUG: 字符串查询找到记录，result_id={latest_result_row[0]}, invoice_id={latest_result_row[1]}")
        else:
            logger.warning(f"🔍 DEBUG: 字符串查询未找到记录，尝试UUID查询，invoice_id={invoice_id}")
        # #endregion

        # 如果字符串查询没有找到，尝试 UUID 查询
        if not latest_result_row:
            latest_result_row = session.exec(
                select(
                    RecognitionResult.id,
                    RecognitionResult.invoice_id,
                    RecognitionResult.recognition_time
                )
                .where(RecognitionResult.invoice_id == invoice_id)
                .order_by(RecognitionResult.recognition_time.desc())
                .limit(1)
            ).first()

            # #region agent log
            logger.info(f"🔍 DEBUG: UUID查询结果 latest_result_row={latest_result_row is not None}")
            if latest_result_row:
                logger.info(f"🔍 DEBUG: UUID查询找到记录，result_id={latest_result_row[0]}, invoice_id={latest_result_row[1]}")
            else:
                logger.warning(f"🔍 DEBUG: UUID查询也未找到记录，invoice_id={invoice_id}")
            # #endregion
        logger.info(f"查询识别结果: latest_result_row = {latest_result_row is not None}")
        if latest_result_row:
            logger.info(f"识别结果ID: {latest_result_row[0]}")
        
        # 如果查询成功，尝试获取完整对象以访问可能不存在的字段
        if latest_result_row:
            logger.info(f"✅ 找到识别结果记录，result_id: {latest_result_row[0]}")
            try:
                # 使用原始 SQL 查询以确保获取 raw_payload 和 raw_data
                result_row = session.execute(
                    text("""
                        SELECT id, normalized_fields, raw_payload, raw_data, 
                               template_version_id, field_defs_snapshot
                        FROM recognition_result
                        WHERE id = :result_id
                    """),
                    {"result_id": str(latest_result_row[0])}
                ).fetchone()
                
                logger.info(f"SQL 查询结果: result_row = {result_row is not None}")
                
                if result_row:
                    # 解析查询结果
                    result_id, normalized_fields_db, raw_payload_db, raw_data_db, template_version_id_db, field_defs_snapshot_db = result_row
                    
                    # #region agent log
                    logger.info(f"🔍 DEBUG: SQL查询返回结果，result_id={result_id}")
                    logger.info(f"🔍 DEBUG: normalized_fields_db类型={type(normalized_fields_db)}, 值={str(normalized_fields_db)[:500] if normalized_fields_db else 'None'}")
                    logger.info(f"🔍 DEBUG: normalized_fields_db是否为None={normalized_fields_db is None}")
                    logger.info(f"🔍 DEBUG: normalized_fields_db是否为False={normalized_fields_db is False}")
                    if normalized_fields_db:
                        logger.info(f"🔍 DEBUG: normalized_fields_db长度={len(str(normalized_fields_db))}")
                    # #endregion
                    logger.info(f"从数据库查询到的数据:")
                    logger.info(f"  normalized_fields_db 类型: {type(normalized_fields_db)}, 值: {str(normalized_fields_db)[:200] if normalized_fields_db else 'None'}")
                    logger.info(f"  raw_payload_db 类型: {type(raw_payload_db)}, 值: {str(raw_payload_db)[:200] if raw_payload_db else 'None'}")
                    logger.info(f"  raw_data_db 类型: {type(raw_data_db)}, 值: {str(raw_data_db)[:200] if raw_data_db else 'None'}")
                    
                    # 使用数据库中的值
                    template_version_id = template_version_id_db
                    field_defs_snapshot_raw = field_defs_snapshot_db
                    
                    # 处理 normalized_fields：PostgreSQL JSONB 可能返回字符串或字典
                    logger.info(f"🔍 开始处理 normalized_fields_db")
                    logger.info(f"  normalized_fields_db 值: {normalized_fields_db}")
                    logger.info(f"  normalized_fields_db 类型: {type(normalized_fields_db)}")
                    logger.info(f"  normalized_fields_db 是否为 None: {normalized_fields_db is None}")
                    logger.info(f"  normalized_fields_db 是否为 False: {normalized_fields_db is False}")
                    
                    normalized_fields = None
                    if normalized_fields_db:
                        # #region agent log
                        logger.info(f"🔍 DEBUG: normalized_fields_db不为空，开始处理")
                        logger.info(f"🔍 DEBUG: normalized_fields_db完整内容={json.dumps(normalized_fields_db, ensure_ascii=False, default=str)[:1000]}")
                        # #endregion
                        logger.info(f"✅ normalized_fields_db 不为空，开始处理")
                        if isinstance(normalized_fields_db, dict):
                            normalized_fields = normalized_fields_db.copy()  # 使用 copy() 避免引用问题
                            # #region agent log
                            logger.info(f"🔍 DEBUG: normalized_fields是字典，字段数={len(normalized_fields)}, 键={list(normalized_fields.keys())}")
                            # #endregion
                            logger.info(f"✅ normalized_fields 是字典，字段数: {len(normalized_fields)}")
                            logger.info(f"✅ normalized_fields 键: {list(normalized_fields.keys())}")
                            # 验证数据完整性
                            if len(normalized_fields) == 0:
                                logger.error(f"❌ normalized_fields 字典为空！这不应该发生")
                        elif isinstance(normalized_fields_db, str):
                            try:
                                normalized_fields = json.loads(normalized_fields_db)
                                # #region agent log
                                logger.info(f"🔍 DEBUG: normalized_fields字符串解析成功，字段数={len(normalized_fields) if isinstance(normalized_fields, dict) else 'N/A'}")
                                # #endregion
                                logger.info(f"✅ normalized_fields 是字符串，已解析为字典，字段数: {len(normalized_fields) if isinstance(normalized_fields, dict) else 'N/A'}")
                                if isinstance(normalized_fields, dict) and len(normalized_fields) == 0:
                                    logger.error(f"❌ 解析后的 normalized_fields 字典为空！")
                            except Exception as e:
                                # #region agent log
                                logger.error(f"🔍 DEBUG: 解析normalized_fields字符串失败: {e}")
                                # #endregion
                                logger.warning(f"❌ 解析 normalized_fields 字符串失败: {e}")
                        else:
                            normalized_fields = normalized_fields_db
                            # #region agent log
                            logger.info(f"🔍 DEBUG: normalized_fields类型={type(normalized_fields_db)}, 值={str(normalized_fields_db)[:200]}")
                            # #endregion
                            logger.info(f"✅ normalized_fields 类型: {type(normalized_fields_db)}")
                    else:
                        # #region agent log
                        logger.warning(f"🔍 DEBUG: normalized_fields_db为空或False")
                        logger.warning(f"🔍 DEBUG: normalized_fields_db值={normalized_fields_db}, 类型={type(normalized_fields_db)}")
                        # #endregion
                        logger.warning(f"⚠️ normalized_fields_db 为空或为 False，将尝试从 raw_payload 提取")
                    
                    raw_payload = raw_payload_db
                    raw_data = raw_data_db
                    
                    # 如果 normalized_fields 为空，尝试从 raw_payload 或 raw_data 中解析
                    if not normalized_fields:
                        
                        logger.info(f"normalized_fields 为空，尝试从 raw_payload 或 raw_data 提取")
                        logger.info(f"raw_payload 类型: {type(raw_payload)}, 值: {raw_payload[:200] if raw_payload and isinstance(raw_payload, str) else raw_payload}")
                        logger.info(f"raw_data 类型: {type(raw_data)}, 值: {raw_data}")
                        
                        # 尝试从 raw_payload 解析（通常是 JSON 字符串）
                        if raw_payload:
                            try:
                                import json
                                raw_json = json.loads(raw_payload)
                                logger.info(f"raw_payload 解析成功，类型: {type(raw_json)}, 键: {list(raw_json.keys()) if isinstance(raw_json, dict) else 'N/A'}")
                                
                                # 检查是否是 DIFY API 返回的格式
                                if isinstance(raw_json, dict):
                                    # 优先检查 data.outputs.text 路径（工作流返回的常见格式）
                                    if 'data' in raw_json and isinstance(raw_json['data'], dict):
                                        data = raw_json['data']
                                        logger.info(f"✅ 找到 data 字段，键: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                                        if 'outputs' in data and isinstance(data['outputs'], dict):
                                            logger.info(f"✅ 找到 data.outputs，键: {list(data['outputs'].keys()) if isinstance(data['outputs'], dict) else 'N/A'}")
                                            if 'text' in data['outputs'] and isinstance(data['outputs']['text'], dict):
                                                normalized_fields = data['outputs']['text']
                                                logger.info(f"✅ 从 raw_payload.data.outputs.text 提取 normalized_fields，字段数: {len(normalized_fields)}")
                                                logger.info(f"提取的数据键: {list(normalized_fields.keys())}")
                                                if 'items' in normalized_fields:
                                                    items = normalized_fields.get('items', [])
                                                    logger.info(f"包含 items 数组，item数量: {len(items) if isinstance(items, list) else 'N/A'}")
                                            else:
                                                logger.warning(f"data.outputs 中不包含 'text' 字段")
                                        else:
                                            logger.warning(f"data 中不包含 'outputs' 字段")
                                    # 其次检查顶层 text 字段
                                    elif 'text' in raw_json and isinstance(raw_json['text'], dict):
                                        normalized_fields = raw_json['text']
                                        logger.info(f"✅ 从 raw_payload.text 提取 normalized_fields，字段数: {len(normalized_fields)}")
                                    # 最后尝试直接使用 raw_json
                                    else:
                                        normalized_fields = raw_json
                                        logger.info(f"从 raw_payload 直接提取 normalized_fields，字段数: {len(normalized_fields) if isinstance(normalized_fields, dict) else 'N/A'}")
                            except Exception as e:
                                logger.error(f"解析 raw_payload 失败: {e}", exc_info=True)
                        
                        # 如果 raw_payload 解析失败，尝试使用 raw_data
                        if not normalized_fields and raw_data:
                            logger.info(f"尝试从 raw_data 提取")
                            if isinstance(raw_data, dict):
                                # 检查是否是 DIFY API 返回的格式
                                if 'text' in raw_data and isinstance(raw_data['text'], dict):
                                    normalized_fields = raw_data['text']
                                    logger.info(f"从 raw_data.text 提取 normalized_fields，字段数: {len(normalized_fields)}")
                                elif 'data' in raw_data and isinstance(raw_data['data'], dict):
                                    data = raw_data['data']
                                    if 'outputs' in data and isinstance(data['outputs'], dict):
                                        if 'text' in data['outputs'] and isinstance(data['outputs']['text'], dict):
                                            normalized_fields = data['outputs']['text']
                                            logger.info(f"从 raw_data.data.outputs.text 提取 normalized_fields，字段数: {len(normalized_fields)}")
                                else:
                                    normalized_fields = raw_data
                                    logger.info(f"从 raw_data 直接提取 normalized_fields，字段数: {len(normalized_fields) if isinstance(normalized_fields, dict) else 'N/A'}")
                        
                        if normalized_fields:
                            logger.info(f"成功提取 normalized_fields，字段: {list(normalized_fields.keys()) if isinstance(normalized_fields, dict) else 'N/A'}")
                        else:
                            logger.warning(f"无法从 raw_payload 或 raw_data 提取 normalized_fields")

                            # ===== HOLE POSITION RECORD LOGIC START =====
                            print("🚨🚨🚨 ENTERING HOLE POSITION RECORD LOGIC 🚨🚨🚨")
                            print(f"🔥🔥🔥 HOLE POSITION RECORD LOGIC START - normalized_fields: {normalized_fields}, type: {type(normalized_fields)}")
                            debug_info["hole_position_logic_executed"] = True
                            import traceback
                            print("Stack trace:")
                            traceback.print_stack()
                            # 如果 normalized_fields 为空，且模型是"尺寸/孔位类检验记录大模型"，尝试从 HolePositionRecord 和 HolePositionItem 表获取数据
                            model_name = getattr(invoice, 'model_name', None)
                            # #region agent log
                            logger.info(f"🔍 DEBUG: 检查 HolePositionRecord 逻辑，model_name={model_name}, normalized_fields为空={not normalized_fields}, invoice.file_id={getattr(invoice, 'file_id', None)}")
                            # 添加到调试信息
                            debug_info["debug_hole_position_check"] = {
                                "model_name": model_name,
                                "normalized_fields_empty": not normalized_fields,
                                "file_id": str(getattr(invoice, 'file_id', None))
                            }
                            # #endregion
                            logger.info(f"检查是否需要从 HolePositionRecord 表获取数据: model_name={model_name}, normalized_fields为空={not normalized_fields}")
                            if model_name and ('尺寸/孔位类检验记录大模型' in str(model_name) or '检验记录' in str(model_name)):
                                # #region agent log
                                logger.info(f"🔍 DEBUG: 满足 HolePositionRecord 查询条件，file_id={getattr(invoice, 'file_id', None)}")
                                # #endregion
                                logger.info(f"✅ 模型是检验记录表类型，尝试从 HolePositionRecord 表获取数据，file_id: {invoice.file_id}")
                                try:
                                    from app.models.models_invoice import HolePositionRecord, HolePositionItem
                                    from sqlmodel import select
                                    # 通过 file_id 查找记录
                                    hole_position_record = session.exec(
                                        select(HolePositionRecord).where(HolePositionRecord.file_id == invoice.file_id)
                                    ).first()

                                    # 添加到调试信息
                                    debug_info["debug_hole_position_query"] = {
                                        "file_id": str(invoice.file_id),
                                        "found_record": hole_position_record is not None,
                                        "record_id": str(hole_position_record.id) if hole_position_record else None,
                                        "record_no": hole_position_record.record_no if hole_position_record else None
                                    }

                                    logger.info(f"HolePositionRecord 查询结果: {hole_position_record is not None}")
                                    if hole_position_record:
                                        logger.info(f"✅ 找到 HolePositionRecord 记录: {hole_position_record.id}, record_no: {hole_position_record.record_no}")
                                        # 获取行项目
                                        items = session.exec(
                                            select(HolePositionItem)
                                            .where(HolePositionItem.record_id == hole_position_record.id)
                                            .order_by(HolePositionItem.item_no)
                                        ).all()
                                        
                                        logger.info(f"找到 {len(items)} 个行项目")
                                        
                                        # 构建 normalized_fields
                                        normalized_fields = {
                                            "doc_type": hole_position_record.doc_type,
                                            "form_title": hole_position_record.form_title,
                                            "drawing_no": hole_position_record.drawing_no,
                                            "part_name": hole_position_record.part_name,
                                            "part_no": hole_position_record.part_no,
                                            "date": hole_position_record.date.isoformat() if hole_position_record.date else None,
                                            "inspector_name": hole_position_record.inspector_name,
                                            "overall_result": hole_position_record.overall_result,
                                            "remarks": hole_position_record.remarks,
                                            "items": [
                                                {
                                                    "item_no": item.item_no,
                                                    "inspection_item": item.inspection_item,
                                                    "spec_requirement": item.spec_requirement,
                                                    "actual_value": item.actual_value,
                                                    "range_value": item.range_value,
                                                    "judgement": item.judgement,
                                                    "remarks": item.notes  # 注意：数据库字段是 notes，但 API 返回时使用 remarks
                                                }
                                                for item in items
                                            ]
                                        }
                                        logger.info(f"✅ 从 HolePositionRecord 表构建 normalized_fields，字段数: {len(normalized_fields)}, items数量: {len(normalized_fields.get('items', []))}")
                                        logger.info(f"normalized_fields 内容预览: {json.dumps(normalized_fields, ensure_ascii=False, indent=2)[:500]}...")
                                    else:
                                        logger.warning(f"⚠️ 未找到对应的 HolePositionRecord 记录，file_id: {invoice.file_id}")
                                except Exception as e:
                                    logger.error(f"❌ 从 HolePositionRecord 表获取数据失败: {str(e)}", exc_info=True)
                                    import traceback
                                    logger.error(f"完整错误堆栈: {traceback.format_exc()}")
                    
                    # 将字段快照从数组格式转换为对象格式（以 field_key 为键）
                    field_defs_snapshot = None
                    if field_defs_snapshot_raw:
                        if isinstance(field_defs_snapshot_raw, list):
                            # 数组格式转换为对象格式
                            field_defs_snapshot = {
                                field.get("field_key", ""): field
                                for field in field_defs_snapshot_raw
                                if field.get("field_key")
                            }
                        elif isinstance(field_defs_snapshot_raw, dict):
                            # 已经是对象格式，直接使用
                            field_defs_snapshot = field_defs_snapshot_raw
                    
                    # 获取版本号和模板名称
                    if template_version_id:
                        from app.models.models_invoice import TemplateVersion, Template
                        version_obj = session.get(TemplateVersion, template_version_id)
                        if version_obj:
                            template_version = version_obj.version
                            # 获取模板名称
                            template_obj = session.get(Template, version_obj.template_id)
                            if template_obj:
                                template_name = template_obj.name
            except Exception as e:
                # 如果获取完整对象失败（可能是字段不存在），记录详细错误
                logger.error(f"获取识别结果完整信息失败: {str(e)}", exc_info=True)
                logger.error(f"异常类型: {type(e).__name__}")
                import traceback
                logger.error(f"完整堆栈: {traceback.format_exc()}")
            else:
                logger.warning(f"SQL 查询返回空结果，result_id: {latest_result_row[0] if latest_result_row else 'N/A'}")
        else:
            logger.warning(f"未找到识别结果记录，invoice_id: {invoice_id}")
            # 尝试直接使用原始 SQL 查询
            try:
                logger.info("尝试使用原始 SQL 直接查询识别结果")
                direct_result = session.execute(
                    text("""
                        SELECT id, normalized_fields, raw_payload, raw_data
                        FROM recognition_result
                        WHERE invoice_id = :invoice_id
                        ORDER BY recognition_time DESC
                        LIMIT 1
                    """),
                    {"invoice_id": str(invoice_id)}
                ).fetchone()
                
                if direct_result:
                    logger.info(f"直接 SQL 查询成功，找到记录")
                    result_id, normalized_fields_db, raw_payload_db, raw_data_db = direct_result
                    # 处理 normalized_fields
                    if normalized_fields_db:
                        if isinstance(normalized_fields_db, dict):
                            normalized_fields = normalized_fields_db
                        elif isinstance(normalized_fields_db, str):
                            try:
                                normalized_fields = json.loads(normalized_fields_db)
                            except:
                                pass
                        if normalized_fields:
                            logger.info(f"从直接查询获取到 normalized_fields，字段数: {len(normalized_fields) if isinstance(normalized_fields, dict) else 'N/A'}")
                else:
                    logger.warning(f"直接 SQL 查询也未找到记录")
            except Exception as e:
                logger.error(f"直接 SQL 查询失败: {str(e)}", exc_info=True)
    except Exception as e:
        # 如果查询失败，记录日志但不影响主流程
        logger.error(f"获取识别结果模板版本信息失败: {str(e)}", exc_info=True)
    
    # 添加调试日志
    logger.info(f"=== 返回发票详情 ===")
    logger.info(f"invoice_id: {invoice_id}")
    logger.info(f"model_name: {getattr(invoice, 'model_name', None)}")
    logger.info(f"normalized_fields 类型: {type(normalized_fields)}")
    logger.info(f"normalized_fields 是否为空: {not normalized_fields if normalized_fields else True}")
    if normalized_fields:
        if isinstance(normalized_fields, dict):
            logger.info(f"normalized_fields 是字典，字段数: {len(normalized_fields)}")
            logger.info(f"normalized_fields 键: {list(normalized_fields.keys())}")
            if 'items' in normalized_fields:
                items = normalized_fields['items']
                logger.info(f"normalized_fields.items 类型: {type(items)}, 长度: {len(items) if isinstance(items, list) else 'N/A'}")
            logger.info(f"normalized_fields 内容预览: {json.dumps(normalized_fields, ensure_ascii=False, indent=2)[:500]}...")
        else:
            logger.warning(f"normalized_fields 不是字典: {type(normalized_fields)}, 值: {str(normalized_fields)[:200]}")
    else:
        logger.warning(f"normalized_fields 为空，无法返回给前端")
    

    # 在创建响应对象之前，再次确认 normalized_fields 的值
    # #region agent log
    logger.info(f"🔍 DEBUG: 创建响应对象前，normalized_fields={normalized_fields is not None}, 类型={type(normalized_fields)}")
    if normalized_fields:
        logger.info(f"🔍 DEBUG: normalized_fields字段数={len(normalized_fields) if isinstance(normalized_fields, dict) else 'N/A'}, 键={list(normalized_fields.keys()) if isinstance(normalized_fields, dict) else 'N/A'}")
        if isinstance(normalized_fields, dict) and 'items' in normalized_fields:
            logger.info(f"🔍 DEBUG: normalized_fields.items长度={len(normalized_fields['items']) if isinstance(normalized_fields['items'], list) else 'N/A'}")
    # #endregion
    logger.info(f"🔍 创建响应对象前检查：normalized_fields = {normalized_fields}")
    logger.info(f"🔍 创建响应对象前检查：normalized_fields 类型 = {type(normalized_fields)}")
    if normalized_fields:
        field_count = len(normalized_fields) if isinstance(normalized_fields, dict) else 'N/A'
        field_keys = list(normalized_fields.keys()) if isinstance(normalized_fields, dict) else 'N/A'
        logger.info(f"🔍 创建响应对象前检查：normalized_fields 字段数 = {field_count}")
        logger.info(f"🔍 创建响应对象前检查：normalized_fields 键 = {field_keys}")
        
        # 如果 normalized_fields 只有 _debug_info，说明数据丢失了，需要重新查询
        if isinstance(normalized_fields, dict) and len(normalized_fields) == 1 and '_debug_info' in normalized_fields:
            logger.error(f"❌ normalized_fields 只有 _debug_info，数据丢失！尝试重新从数据库查询")
            try:
                direct_result = session.execute(
                    text("""
                        SELECT normalized_fields
                        FROM recognition_result
                        WHERE invoice_id = :invoice_id
                        ORDER BY recognition_time DESC
                        LIMIT 1
                    """),
                    {"invoice_id": str(invoice_id)}
                ).fetchone()
                
                if direct_result and direct_result[0]:
                    normalized_fields_db_recheck = direct_result[0]
                    logger.info(f"✅ 重新查询到 normalized_fields")
                    if isinstance(normalized_fields_db_recheck, dict) and len(normalized_fields_db_recheck) > 0:
                        normalized_fields = normalized_fields_db_recheck.copy()
                        logger.info(f"✅ 恢复 normalized_fields，字段数: {len(normalized_fields)}, 键: {list(normalized_fields.keys())}")
                    elif isinstance(normalized_fields_db_recheck, str):
                        try:
                            import json
                            normalized_fields = json.loads(normalized_fields_db_recheck)
                            if isinstance(normalized_fields, dict) and len(normalized_fields) > 0:
                                logger.info(f"✅ 恢复 normalized_fields（从字符串解析），字段数: {len(normalized_fields)}")
                        except Exception as e:
                            logger.error(f"❌ 解析失败: {e}")
            except Exception as e:
                logger.error(f"❌ 重新查询失败: {e}", exc_info=True)
    else:
        logger.warning(f"⚠️ 创建响应对象前检查：normalized_fields 为空！")
    
    # 构建响应对象
    # #region agent log
    logger.info(f"🔍 DEBUG: 构建响应对象，normalized_fields={normalized_fields is not None}")
    if normalized_fields:
        logger.info(f"🔍 DEBUG: 响应对象normalized_fields字段数={len(normalized_fields) if isinstance(normalized_fields, dict) else 'N/A'}")
    # #endregion

    # 检查 normalized_fields 是否为空，如果为空则尝试从数据库直接查询
    if not normalized_fields or (isinstance(normalized_fields, dict) and len(normalized_fields) == 0):
        logger.warning(f"⚠️ normalized_fields 为空，尝试直接从数据库查询")
        try:
            direct_result = session.execute(
                text("""
                    SELECT normalized_fields
                    FROM recognition_result
                    WHERE invoice_id = :invoice_id
                    ORDER BY recognition_time DESC
                    LIMIT 1
                """),
                {"invoice_id": str(invoice_id)}
            ).fetchone()
            
            if direct_result and direct_result[0]:
                normalized_fields_db_direct = direct_result[0]
                logger.info(f"✅ 直接从数据库查询到 normalized_fields")
                if isinstance(normalized_fields_db_direct, dict):
                    normalized_fields = normalized_fields_db_direct
                    logger.info(f"✅ normalized_fields 是字典，字段数: {len(normalized_fields)}, 键: {list(normalized_fields.keys())}")
                elif isinstance(normalized_fields_db_direct, str):
                    try:
                        import json
                        normalized_fields = json.loads(normalized_fields_db_direct)
                        logger.info(f"✅ normalized_fields 字符串解析成功，字段数: {len(normalized_fields) if isinstance(normalized_fields, dict) else 'N/A'}")
                    except Exception as e:
                        logger.error(f"❌ 解析 normalized_fields 字符串失败: {e}")
        except Exception as e:
            logger.error(f"❌ 直接从数据库查询失败: {e}", exc_info=True)
    
    # 如果 normalized_fields 仍然为空，设置为空字典（避免后续错误）
    if normalized_fields is None:
        normalized_fields = {}
        logger.warning(f"⚠️ normalized_fields 仍为空，设置为空字典")

    # 添加调试信息（但不覆盖现有数据）
    debug_info = {
        "debug_invoice_id": str(invoice_id),
        "debug_model_name": getattr(invoice, 'model_name', None),
        "debug_file_id": str(getattr(invoice, 'file_id', None)),
        "debug_normalized_fields_null": normalized_fields is None,
        "debug_normalized_fields_type": type(normalized_fields).__name__,
        "debug_normalized_fields_len": len(normalized_fields) if hasattr(normalized_fields, '__len__') else 'N/A',
        "debug_normalized_fields_keys": list(normalized_fields.keys()) if isinstance(normalized_fields, dict) else 'N/A',
        "debug_recognition_status": getattr(invoice, 'recognition_status', None),
        "debug_has_recognition_result": "checked"
    }

    # 只在 normalized_fields 不为空时才添加调试信息，避免覆盖数据
    if normalized_fields and isinstance(normalized_fields, dict) and len(normalized_fields) > 0:
        # 只在没有 _debug_info 时才添加，避免重复
        if '_debug_info' not in normalized_fields:
            normalized_fields['_debug_info'] = debug_info
            logger.info(f"🔍 DEBUG: 调试信息已添加到 normalized_fields")
    else:
        # 如果 normalized_fields 为空，添加调试信息以便诊断
        normalized_fields['_debug_info'] = debug_info
        logger.warning(f"⚠️ normalized_fields 为空，仅添加调试信息: {debug_info}")

    response = InvoiceResponse(
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
        error_message=error_message,
        template_version_id=template_version_id,
        field_defs_snapshot=field_defs_snapshot,
        template_version=template_version,
        normalized_fields=normalized_fields,  # 包含调试信息的 normalized_fields
        template_name=template_name,
        model_name=getattr(invoice, 'model_name', None)
    )
    # #region agent log
    logger.info(f"🔍 DEBUG: 响应对象创建完成，response.normalized_fields={response.normalized_fields is not None}")
    if response.normalized_fields:
        logger.info(f"🔍 DEBUG: response.normalized_fields字段数={len(response.normalized_fields) if isinstance(response.normalized_fields, dict) else 'N/A'}")
    # #endregion
    
    # 验证响应对象中的 normalized_fields
    logger.info(f"响应对象创建完成，normalized_fields: {response.normalized_fields}")
    logger.info(f"响应对象 normalized_fields 类型: {type(response.normalized_fields)}")
    logger.info(f"响应对象 normalized_fields 是否为空: {not response.normalized_fields if response.normalized_fields else True}")
    
    # 尝试序列化 normalized_fields 以验证是否可以正确转换为 JSON
    try:
        if response.normalized_fields:
            import json
            json_str = json.dumps(response.normalized_fields, ensure_ascii=False, default=str)
            logger.info(f"✅ normalized_fields 可以序列化为 JSON，长度: {len(json_str)}")
            # 验证反序列化
            parsed_back = json.loads(json_str)
            logger.info(f"✅ normalized_fields JSON 可以反序列化，类型: {type(parsed_back)}")
        else:
            logger.warning(f"⚠️ normalized_fields 为空，无法序列化")
    except Exception as e:
        logger.error(f"❌ normalized_fields 序列化失败: {e}", exc_info=True)
    
    if response.normalized_fields:
        logger.info(f"响应对象 normalized_fields 字段数: {len(response.normalized_fields) if isinstance(response.normalized_fields, dict) else 'N/A'}")
        logger.info(f"响应对象 normalized_fields 键: {list(response.normalized_fields.keys()) if isinstance(response.normalized_fields, dict) else 'N/A'}")
    else:
        logger.error(f"⚠️ 响应对象中的 normalized_fields 为空！")
    
    # 在序列化之前，先保存原始的 normalized_fields 值
    original_normalized_fields = normalized_fields
    logger.info(f"🔍 序列化前检查：original_normalized_fields = {original_normalized_fields}")
    logger.info(f"🔍 序列化前检查：original_normalized_fields 类型 = {type(original_normalized_fields)}")
    logger.info(f"🔍 序列化前检查：response.normalized_fields = {response.normalized_fields}")
    logger.info(f"🔍 序列化前检查：response.normalized_fields 类型 = {type(response.normalized_fields)}")
    
    # 使用 model_dump() 显式序列化，确保 normalized_fields 被正确包含
    try:
        response_dict = response.model_dump(mode='json', exclude_none=False)
        logger.info(f"✅ 响应对象 model_dump() 成功")
        logger.info(f"  model_dump() 中的 normalized_fields: {response_dict.get('normalized_fields')}")
        logger.info(f"  model_dump() normalized_fields 类型: {type(response_dict.get('normalized_fields'))}")
        
        # 如果 model_dump() 中 normalized_fields 为空，但原始值不为空，强制设置
        if not response_dict.get('normalized_fields') and original_normalized_fields:
            logger.warning(f"⚠️ model_dump() 中的 normalized_fields 为空，但原始值不为空，强制设置")
            logger.warning(f"  原始值类型: {type(original_normalized_fields)}")
            logger.warning(f"  原始值内容: {str(original_normalized_fields)[:200]}")
            response_dict['normalized_fields'] = original_normalized_fields
            logger.info(f"  🔄 强制设置 normalized_fields 到响应字典")
            logger.info(f"  设置后的值: {response_dict.get('normalized_fields')}")
            logger.info(f"  设置后的类型: {type(response_dict.get('normalized_fields'))}")
        
        if response_dict.get('normalized_fields'):
            logger.info(f"  model_dump() normalized_fields 字段数: {len(response_dict.get('normalized_fields')) if isinstance(response_dict.get('normalized_fields'), dict) else 'N/A'}")
            logger.info(f"  model_dump() normalized_fields 键: {list(response_dict.get('normalized_fields').keys()) if isinstance(response_dict.get('normalized_fields'), dict) else 'N/A'}")
        
        # 使用 jsonable_encoder 确保 JSON 兼容性
        from fastapi.encoders import jsonable_encoder
        jsonable_response = jsonable_encoder(response_dict)
        logger.info(f"✅ jsonable_encoder 处理完成")
        logger.info(f"  jsonable_encoder 中的 normalized_fields: {jsonable_response.get('normalized_fields')}")
        logger.info(f"  jsonable_encoder normalized_fields 类型: {type(jsonable_response.get('normalized_fields'))}")
        
        # 如果 jsonable_encoder 中 normalized_fields 为空，但原始值不为空，强制设置
        if not jsonable_response.get('normalized_fields') and original_normalized_fields:
            logger.warning(f"⚠️ jsonable_encoder 中 normalized_fields 为空，但原始值不为空，强制设置")
            jsonable_response['normalized_fields'] = jsonable_encoder(original_normalized_fields)
            logger.info(f"  ✅ 强制设置后，normalized_fields: {jsonable_response.get('normalized_fields')}")
            logger.info(f"  强制设置后，normalized_fields 类型: {type(jsonable_response.get('normalized_fields'))}")
        
        # 确保 normalized_fields 在 jsonable_response 中
        if original_normalized_fields and not jsonable_response.get('normalized_fields'):
            logger.warning(f"⚠️ jsonable_response 中 normalized_fields 为空，强制设置原始值")
            jsonable_response['normalized_fields'] = jsonable_encoder(original_normalized_fields)
        
        # 重新创建响应对象，确保 normalized_fields 被正确设置
        # 这样可以保持类型安全，同时确保数据正确
        try:
            final_response = InvoiceResponse(**jsonable_response)
            logger.info(f"✅ 重新创建响应对象完成")
            logger.info(f"  final_response.normalized_fields: {final_response.normalized_fields}")
            logger.info(f"  final_response.normalized_fields 类型: {type(final_response.normalized_fields)}")
            logger.info(f"  final_response.normalized_fields 是否为空: {not final_response.normalized_fields if final_response.normalized_fields else True}")
            
            # 如果最终响应对象中 normalized_fields 仍然为空，但原始值不为空，最后一次强制设置
            if not final_response.normalized_fields and original_normalized_fields:
                logger.error(f"❌ 最终响应对象中 normalized_fields 仍然为空，但原始值不为空！")
                logger.error(f"  原始值类型: {type(original_normalized_fields)}")
                logger.error(f"  原始值内容预览: {str(original_normalized_fields)[:500]}")
                # 直接修改响应对象的属性（如果 Pydantic 允许）
                try:
                    object.__setattr__(final_response, 'normalized_fields', original_normalized_fields)
                    logger.info(f"  🔄 直接设置 final_response.normalized_fields 属性成功")
                    logger.info(f"  设置后: {final_response.normalized_fields is not None}")
                except Exception as e:
                    logger.error(f"  ❌ 无法直接设置属性: {e}")
                    # 如果无法直接设置，返回字典而不是对象
                    jsonable_response['normalized_fields'] = jsonable_encoder(original_normalized_fields)
                    logger.warning(f"  ⚠️ 返回字典而不是对象，以确保 normalized_fields 被包含")
                    logger.info(f"  返回字典中的 normalized_fields: {jsonable_response.get('normalized_fields') is not None}")
                    return jsonable_response
            
            # 最终检查：如果 normalized_fields 仍然为空，记录警告
            if not final_response.normalized_fields:
                logger.warning(f"⚠️ 最终响应对象中 normalized_fields 为空")
                if original_normalized_fields:
                    logger.error(f"  ❌ 原始值不为空，但最终响应中丢失了！")
                    # 最后一次尝试：返回字典
                    jsonable_response['normalized_fields'] = jsonable_encoder(original_normalized_fields)
                    logger.warning(f"  ⚠️ 返回字典以确保 normalized_fields 被包含")
                    return jsonable_response
            
            logger.info(f"✅ 最终响应对象创建成功，normalized_fields: {final_response.normalized_fields is not None}")
            if final_response.normalized_fields:
                logger.info(f"  normalized_fields 字段数: {len(final_response.normalized_fields) if isinstance(final_response.normalized_fields, dict) else 'N/A'}")
            return final_response
        except Exception as create_error:
            logger.error(f"❌ 重新创建响应对象失败: {create_error}", exc_info=True)
            # 如果创建失败，返回字典
            if original_normalized_fields:
                jsonable_response['normalized_fields'] = jsonable_encoder(original_normalized_fields)
            logger.warning(f"⚠️ 返回字典作为备用方案")
            return jsonable_response
    except Exception as e:
        logger.error(f"❌ 响应对象序列化失败: {e}", exc_info=True)
        # 如果序列化失败，仍然返回原始响应对象
        return response


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
    
    # 检查权限：使用统一的权限检查函数
    if not check_invoice_permission(invoice, current_user):
        raise HTTPException(status_code=403, detail="无权访问此票据")
    
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
    
    # 检查权限：使用统一的权限检查函数
    if not check_invoice_permission(invoice, current_user):
        raise HTTPException(status_code=403, detail="无权访问此票据")
    
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
    
    # 检查权限：使用统一的权限检查函数
    if not check_invoice_permission(invoice, current_user):
        raise HTTPException(status_code=403, detail="无权访问此票据")
    
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
    
    # 检查权限：使用统一的权限检查函数
    if not check_invoice_permission(invoice, current_user):
        raise HTTPException(status_code=403, detail="无权访问此票据")
    
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
    
    # 检查权限：使用统一的权限检查函数
    if not check_invoice_permission(invoice, current_user):
        raise HTTPException(status_code=403, detail="无权访问此票据")
    
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
    model_name: str | None = None,
    template_name: str | None = None,
    current_user: CurrentUser
) -> Any:
    """
    获取待审核票据列表（支持按模型和模板筛选）
    """
    try:
        statement = select(Invoice).where(Invoice.review_status == "pending")
        
        # 添加公司过滤条件（超级用户可以查看所有，普通用户只能查看自己公司的）
        conditions = [Invoice.review_status == "pending"]
        
        # 添加模型和模板筛选条件
        if model_name:
            conditions.append(Invoice.model_name == model_name)
        if template_name:
            conditions.append(Invoice.template_name == template_name)
        
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
                    template_name=inv.template_name,  # 添加模板名称
                    template_version=inv.template_version,  # 添加模板版本
                    model_name=inv.model_name,  # 添加模型名称
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
        
        # 检查权限：使用统一的权限检查函数
        if not check_invoice_permission(invoice, current_user):
            raise HTTPException(status_code=403, detail="无权访问此票据")
        
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
        
        # 检查权限：使用统一的权限检查函数
        if not check_invoice_permission(invoice, current_user):
            raise HTTPException(status_code=403, detail="无权访问此票据")
        
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
        # 显式指定需要的列，避免查询不存在的 template_version_id 等字段
        base_columns = [
            RecognitionResult.id,
            RecognitionResult.invoice_id,
            RecognitionResult.total_fields,
            RecognitionResult.recognized_fields,
            RecognitionResult.accuracy,
            RecognitionResult.confidence,
            RecognitionResult.status,
            RecognitionResult.recognition_time
        ]
        
        # 如果不是超级用户，需要通过发票过滤识别结果
        if not current_user.is_superuser:
            if current_user.company_id:
                # 用户有公司ID，只查询自己公司的发票的识别结果
                # 先查询符合条件的发票ID列表
                invoice_ids = session.exec(
                    select(Invoice.id).where(Invoice.company_id == current_user.company_id)
                ).all()
                if invoice_ids:
                    statement = select(*base_columns).where(RecognitionResult.invoice_id.in_(invoice_ids))
                    if invoice_id:
                        # 如果指定了invoice_id，还需要检查权限
                        if invoice_id not in invoice_ids:
                            raise HTTPException(status_code=403, detail="无权访问此票据的识别结果")
                        statement = statement.where(RecognitionResult.invoice_id == invoice_id)
                else:
                    # 用户没有可访问的发票，返回空结果
                    statement = select(*base_columns).where(RecognitionResult.id.is_(None))
            else:
                # 用户没有公司ID，返回空结果
                statement = select(*base_columns).where(RecognitionResult.id.is_(None))
        else:
            # 超级用户可以查看所有识别结果
            statement = select(*base_columns)
            if invoice_id:
                statement = statement.where(RecognitionResult.invoice_id == invoice_id)
        
        # 总数查询
        count_statement = select(func.count()).select_from(RecognitionResult)
        if not current_user.is_superuser:
            if current_user.company_id:
                invoice_ids = session.exec(
                    select(Invoice.id).where(Invoice.company_id == current_user.company_id)
                ).all()
                if invoice_ids:
                    count_statement = count_statement.where(RecognitionResult.invoice_id.in_(invoice_ids))
                    if invoice_id:
                        if invoice_id not in invoice_ids:
                            count_statement = count_statement.where(RecognitionResult.id.is_(None))
                else:
                    count_statement = count_statement.where(RecognitionResult.id.is_(None))
            else:
                count_statement = count_statement.where(RecognitionResult.id.is_(None))
        elif invoice_id:
            count_statement = count_statement.where(RecognitionResult.invoice_id == invoice_id)
        
        total = session.exec(count_statement).one()
        
        # 分页查询
        results = session.exec(statement.order_by(RecognitionResult.recognition_time.desc()).offset(skip).limit(limit)).all()
        
        # 获取模板信息
        result_ids = [r[0] for r in results]
        template_info_map = {}
        if result_ids:
            # 查询识别结果的模板版本信息
            from app.models.models_invoice import TemplateVersion, Template
            result_objects_list = session.exec(
                select(RecognitionResult).where(RecognitionResult.id.in_(result_ids))
            ).all()
            
            version_ids = []
            for r_obj in result_objects_list:
                template_version_id = getattr(r_obj, 'template_version_id', None)
                if template_version_id:
                    version_ids.append(template_version_id)
            
            if version_ids:
                versions = session.exec(
                    select(TemplateVersion).where(TemplateVersion.id.in_(version_ids))
                ).all()
                template_ids = [v.template_id for v in versions]
                templates = session.exec(
                    select(Template).where(Template.id.in_(template_ids))
                ).all()
                template_dict = {t.id: t for t in templates}
                
                for version in versions:
                    template = template_dict.get(version.template_id)
                    if template:
                        template_info_map[version.id] = {
                            "template_name": template.name,
                            "template_version": version.version,
                            "template_type": template.template_type
                        }
        
        # 处理结果：显式列查询返回元组
        result_data = []
        result_objects_list = []
        if result_ids:
            from app.models.models_invoice import TemplateVersion, Template
            result_objects_list = session.exec(
                select(RecognitionResult).where(RecognitionResult.id.in_(result_ids))
            ).all()
        
        for result in results:
            # 元组格式: (id, invoice_id, total_fields, recognized_fields, accuracy, confidence, status, recognition_time)
            result_id = result[0]
            result_obj = None
            for r_obj in result_objects_list:
                if r_obj.id == result_id:
                    result_obj = r_obj
                    break
            
            template_info = None
            if result_obj:
                template_version_id = getattr(result_obj, 'template_version_id', None)
                if template_version_id and template_version_id in template_info_map:
                    template_info = template_info_map[template_version_id]
            
            result_data.append({
                "id": str(result[0]),
                "invoice_id": str(result[1]),
                "total_fields": result[2],
                "recognized_fields": result[3],
                "accuracy": result[4],
                "confidence": result[5],
                "status": result[6],
                "recognition_time": result[7],
                "template_name": template_info["template_name"] if template_info else None,
                "template_version": template_info["template_version"] if template_info else None,
                "template_type": template_info["template_type"] if template_info else None
            })
        
        return {
            "data": result_data,
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
        
        # 检查发票权限
        invoice = session.get(Invoice, result.invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="票据不存在")
        
        # 检查权限：使用统一的权限检查函数
        if not check_invoice_permission(invoice, current_user):
            raise HTTPException(status_code=403, detail="无权访问此票据")
        
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
        
        # 检查权限：使用统一的权限检查函数
        if not check_invoice_permission(invoice, current_user):
            raise HTTPException(status_code=403, detail="无权访问此发票")

        # 获取最新的识别结果（使用安全查询，避免字段不存在的问题）
        recognition_result = None
        recognition_result_task_id = None
        
        try:
            # 先尝试使用模型查询
            recognition_result = session.exec(
                select(RecognitionResult).where(
                    RecognitionResult.invoice_id == invoice_id,
                    RecognitionResult.status.in_(["success", "partial"])
                ).order_by(RecognitionResult.recognition_time.desc())
            ).first()
            
            if recognition_result:
                recognition_result_task_id = recognition_result.task_id
        except Exception as e:
            # 如果模型查询失败（字段不存在），使用原始SQL
            if "does not exist" in str(e) or "UndefinedColumn" in str(e):
                try:
                    session.rollback()
                except:
                    pass
                
                result = session.execute(
                    text("""
                        SELECT id, task_id, status
                        FROM recognition_result
                        WHERE invoice_id = :invoice_id
                          AND status IN ('success', 'partial')
                        ORDER BY recognition_time DESC
                        LIMIT 1
                    """),
                    {"invoice_id": str(invoice_id)}
                )
                row = result.fetchone()
                
                if row:
                    recognition_result_task_id = row[1]
                    # 创建一个简单的对象
                    class SimpleResult:
                        def __init__(self, task_id):
                            self.task_id = task_id
                    recognition_result = SimpleResult(recognition_result_task_id)
            else:
                # 其他错误，回滚后抛出
                try:
                    session.rollback()
                except:
                    pass
                raise

        if not recognition_result or not recognition_result_task_id:
            return None  # 没有识别结果

        # 获取识别任务信息（使用安全查询）
        task = _safe_get_recognition_task(session, recognition_result_task_id)
        if not task:
            return None

        # 获取模型配置（从 llm_config 表）
        model_config = None
        if task.params and task.params.get("model_config_id"):
            try:
                model_config = session.get(LLMConfig, UUID(task.params.get("model_config_id")))
            except:
                pass

        # 获取Schema信息（优先从 template 表的 schema 字段获取）
        schema_info = None
        schema_json = None
        
        # 首先尝试从 template 表获取 schema
        if task.template_id:
            try:
                template = session.get(Template, task.template_id)
                if template and template.schema:
                    schema_json = template.schema
                    schema_info = {
                        "id": str(template.id),
                        "name": template.name,
                        "version": "template_schema",
                        "source": "template"
                    }
                    logger.info(f"从 template 表获取 Schema，template_id: {task.template_id}")
            except Exception as e:
                logger.warning(f"从 template 表获取 Schema 失败: {str(e)}")
        
        # 如果 template 中没有 schema，尝试从任务参数中获取 output_schema_id
        if not schema_info and task.params and task.params.get("output_schema_id"):
            try:
                schema_id = task.params.get("output_schema_id")
                schema = session.get(OutputSchema, UUID(schema_id) if isinstance(schema_id, str) else schema_id)
                if schema and schema.is_active:
                    schema_info = {
                        "id": str(schema.id),
                        "name": schema.name,
                        "version": schema.version,
                        "source": "output_schema"
                    }
                    # OutputSchema 可能没有直接的 schema JSON，这里可能需要从其他地方获取
                    logger.info(f"从 OutputSchema 获取 Schema，schema_id: {schema_id}")
            except Exception as e:
                logger.warning(f"获取 OutputSchema 信息失败: {str(e)}")

        # 如果没有配置Schema，返回None
        if not schema_info:
            logger.warning(f"无法获取 Schema 信息，task.template_id: {task.template_id}, task.params: {task.params}")
            return None

        # 获取Schema验证记录（使用安全查询，避免表不存在的问题）
        validation_record = None
        
        try:
            # 先检查表是否存在
            try:
                # 尝试查询表是否存在
                check_result = session.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'schema_validation_record'
                        );
                    """)
                ).scalar()
                
                if not check_result:
                    logger.info(f"schema_validation_record 表不存在，跳过验证记录查询")
                    validation_record = None
                else:
                    # 表存在，尝试查询验证记录
                    try:
                        # 先尝试使用模型查询
                        validation_record = session.exec(
                            select(SchemaValidationRecord).where(
                                SchemaValidationRecord.invoice_id == invoice_id,
                                SchemaValidationRecord.task_id == recognition_result_task_id
                            ).order_by(SchemaValidationRecord.created_at.desc())
                        ).first()
                    except Exception as model_error:
                        # 如果模型查询失败，使用原始SQL
                        if "does not exist" in str(model_error) or "UndefinedColumn" in str(model_error) or "UndefinedTable" in str(model_error):
                            try:
                                session.rollback()
                            except:
                                pass
                            
                            result = session.execute(
                                text("""
                                    SELECT id, is_valid, validation_errors, validation_warnings, 
                                           created_at, repair_attempted, repair_success, fallback_type
                                    FROM schema_validation_record
                                    WHERE invoice_id = :invoice_id
                                      AND task_id = :task_id
                                    ORDER BY created_at DESC
                                    LIMIT 1
                                """),
                                {
                                    "invoice_id": str(invoice_id),
                                    "task_id": str(recognition_result_task_id)
                                }
                            )
                            row = result.fetchone()
                            
                            if row:
                                # 创建一个简单的对象
                                class SimpleValidationRecord:
                                    def __init__(self, row_data):
                                        self.id = row_data[0]
                                        self.is_valid = row_data[1]
                                        self.validation_errors = row_data[2]
                                        self.validation_warnings = row_data[3]
                                        self.created_at = row_data[4]
                                        self.repair_attempted = row_data[5]
                                        self.repair_success = row_data[6]
                                        self.fallback_type = row_data[7]
                                validation_record = SimpleValidationRecord(row)
                        else:
                            logger.warning(f"查询验证记录失败: {str(model_error)}")
            except Exception as check_error:
                # 如果检查表是否存在失败，假设表不存在
                logger.info(f"无法检查 schema_validation_record 表是否存在: {str(check_error)}，跳过验证记录查询")
                validation_record = None
        except Exception as e:
            # 如果所有查询都失败，记录日志但不抛出错误
            logger.warning(f"获取Schema验证记录失败: {str(e)}，返回 None")
            validation_record = None

        if validation_record:
            # 返回真实的验证记录
            validation_status = {
                "is_valid": validation_record.is_valid,
                "errors": validation_record.validation_errors.get("errors", []) if validation_record.validation_errors else [],
                "warnings": validation_record.validation_warnings.get("warnings", []) if validation_record.validation_warnings else [],
                "validation_time": validation_record.created_at.isoformat() if hasattr(validation_record.created_at, 'isoformat') else str(validation_record.created_at),
                "schema_name": schema_info.get("name", "未知") if schema_info else "未知",
                "schema_version": schema_info.get("version", "未知") if schema_info else "未知",
                "repair_attempted": validation_record.repair_attempted,
                "repair_success": validation_record.repair_success,
                "fallback_type": validation_record.fallback_type
            }
            # 如果 schema_json 存在，也返回它
            if schema_json:
                validation_status["schema_json"] = schema_json
        else:
            # 如果没有验证记录，说明没有进行Schema验证
            # 但仍然返回 schema 信息，表示已找到 schema 但未进行验证
            validation_status = {
                "is_valid": None,
                "errors": [],
                "warnings": [],
                "validation_time": None,
                "schema_name": schema_info.get("name", "未知") if schema_info else "未知",
                "schema_version": schema_info.get("version", "未知") if schema_info else "未知",
                "repair_attempted": False,
                "repair_success": False,
                "fallback_type": None
            }
            # 如果 schema_json 存在，也返回它
            if schema_json:
                validation_status["schema_json"] = schema_json

        return validation_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Schema验证状态失败: {str(e)}", exc_info=True)
        logger.error(f"错误详情 - invoice_id: {invoice_id}, 错误类型: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取Schema验证状态失败: {str(e)}")
