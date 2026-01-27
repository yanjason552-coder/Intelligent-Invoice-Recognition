#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细的发票识别测试脚本
用于追踪识别流程的每一步，定位卡住的具体位置
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加backend路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.db import SessionLocal
    from app.models.models_invoice import (
        Invoice, InvoiceFile, RecognitionTask, LLMConfig
    )
    from app.services.dify_service import SyntaxService
    from sqlmodel import select
except ImportError as e:
    print(f"[错误] 导入失败: {e}")
    print("请确保在backend目录中运行此脚本，并且已安装所有依赖")
    sys.exit(1)

# 日志文件
LOG_FILE = Path(__file__).parent / "recognition_test_log.txt"

def log_step(step_num, step_name, status, details=None, error=None):
    """记录测试步骤"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    log_entry = {
        "timestamp": timestamp,
        "step": step_num,
        "step_name": step_name,
        "status": status,  # "start", "success", "failed", "info"
        "details": details or {},
        "error": str(error) if error else None
    }
    
    # 输出到控制台
    status_symbol = {
        "start": "▶",
        "success": "✓",
        "failed": "✗",
        "info": "ℹ"
    }.get(status, "?")
    
    print(f"\n[{timestamp}] {status_symbol} 步骤 {step_num}: {step_name}")
    if details:
        for key, value in details.items():
            print(f"    {key}: {value}")
    if error:
        print(f"    [错误] {error}")
    
    # 写入日志文件
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"    [警告] 写入日志文件失败: {e}")

def test_invoice_recognition(file_name="China SY inv 1.PDF"):
    """测试发票识别流程"""
    
    # 清空日志文件
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    
    print("=" * 80)
    print("发票识别详细测试")
    print("=" * 80)
    print(f"测试文件: {file_name}")
    print(f"日志文件: {LOG_FILE}")
    print("=" * 80)
    
    step = 0
    session = None
    
    try:
        # 步骤1: 连接数据库
        step += 1
        log_step(step, "连接数据库", "start")
        session = SessionLocal()
        log_step(step, "连接数据库", "success", {"message": "数据库连接成功"})
        
        # 步骤2: 查找文件
        step += 1
        log_step(step, "查找文件记录", "start", {"file_name": file_name})
        
        invoice_file = session.exec(
            select(InvoiceFile).where(InvoiceFile.file_name == file_name)
        ).first()
        
        if not invoice_file:
            log_step(step, "查找文件记录", "failed", {"error": f"未找到文件: {file_name}"})
            print("\n[错误] 未找到文件记录")
            print("请先上传文件")
            return
        
        log_step(step, "查找文件记录", "success", {
            "file_id": str(invoice_file.id),
            "file_name": invoice_file.file_name,
            "file_path": invoice_file.file_path,
            "file_type": invoice_file.file_type,
            "file_size": invoice_file.file_size,
            "external_file_id": invoice_file.external_file_id or "未设置",
            "status": invoice_file.status
        })
        
        # 步骤3: 检查本地文件是否存在
        step += 1
        log_step(step, "检查本地文件", "start", {"file_path": invoice_file.file_path})
        
        file_path = Path(invoice_file.file_path)
        if not file_path.exists():
            log_step(step, "检查本地文件", "failed", {"error": f"文件不存在: {file_path}"})
            print(f"\n[错误] 本地文件不存在: {file_path}")
            return
        
        file_size = file_path.stat().st_size
        log_step(step, "检查本地文件", "success", {
            "file_exists": True,
            "file_size": file_size,
            "absolute_path": str(file_path.absolute())
        })
        
        # 步骤4: 查找关联的发票记录
        step += 1
        log_step(step, "查找发票记录", "start", {"file_id": str(invoice_file.id)})
        
        invoice = session.exec(
            select(Invoice).where(Invoice.file_id == invoice_file.id)
        ).first()
        
        if not invoice:
            log_step(step, "查找发票记录", "failed", {"error": "未找到关联的发票记录"})
            print("\n[错误] 未找到关联的发票记录")
            return
        
        log_step(step, "查找发票记录", "success", {
            "invoice_id": str(invoice.id),
            "invoice_no": invoice.invoice_no,
            "recognition_status": invoice.recognition_status,
            "review_status": invoice.review_status
        })
        
        # 步骤5: 查找识别任务
        step += 1
        log_step(step, "查找识别任务", "start", {"invoice_id": str(invoice.id)})
        
        tasks = session.exec(
            select(RecognitionTask)
            .where(RecognitionTask.invoice_id == invoice.id)
            .order_by(RecognitionTask.create_time.desc())
        ).all()
        
        if not tasks:
            log_step(step, "查找识别任务", "failed", {"error": "未找到识别任务"})
            print("\n[错误] 未找到识别任务")
            print("请先创建识别任务")
            return
        
        task = tasks[0]  # 使用最新的任务
        log_step(step, "查找识别任务", "success", {
            "task_id": str(task.id),
            "task_no": task.task_no,
            "status": task.status,
            "create_time": str(task.create_time),
            "start_time": str(task.start_time) if task.start_time else None,
            "end_time": str(task.end_time) if task.end_time else None,
            "error_code": getattr(task, "error_code", None),
            "error_message": getattr(task, "error_message", None)
        })
        
        # 步骤6: 检查任务参数
        step += 1
        log_step(step, "检查任务参数", "start")
        
        if not task.params:
            log_step(step, "检查任务参数", "failed", {"error": "任务参数为空"})
            return
        
        params = task.params
        model_config_id = params.get("model_config_id")
        
        if not model_config_id:
            log_step(step, "检查任务参数", "failed", {"error": "缺少 model_config_id"})
            return
        
        log_step(step, "检查任务参数", "success", {
            "model_config_id": str(model_config_id),
            "recognition_mode": params.get("recognition_mode"),
            "output_schema_id": params.get("output_schema_id"),
            "template_strategy": params.get("template_strategy")
        })
        
        # 步骤7: 查找模型配置
        step += 1
        log_step(step, "查找模型配置", "start", {"model_config_id": str(model_config_id)})
        
        model_config = session.get(LLMConfig, UUID(model_config_id))
        
        if not model_config:
            log_step(step, "查找模型配置", "failed", {"error": f"模型配置不存在: {model_config_id}"})
            return
        
        if not model_config.is_active:
            log_step(step, "查找模型配置", "failed", {"error": "模型配置未启用"})
            return
        
        log_step(step, "查找模型配置", "success", {
            "config_id": str(model_config.id),
            "config_name": model_config.name,
            "endpoint": model_config.endpoint,
            "api_key": model_config.api_key[:10] + "..." if model_config.api_key else "未设置",
            "app_type": model_config.app_type,
            "workflow_id": model_config.workflow_id,
            "is_active": model_config.is_active
        })
        
        # 步骤8: 检查 API 配置
        step += 1
        log_step(step, "检查API配置", "start")
        
        endpoint = model_config.endpoint
        api_key = model_config.api_key
        
        if not endpoint:
            log_step(step, "检查API配置", "failed", {"error": "API endpoint未配置"})
            return
        
        if not api_key:
            log_step(step, "检查API配置", "failed", {"error": "API key未配置"})
            return
        
        log_step(step, "检查API配置", "success", {
            "endpoint": endpoint,
            "api_key_length": len(api_key) if api_key else 0
        })
        
        # 步骤9: 检查 external_file_id
        step += 1
        log_step(step, "检查external_file_id", "start")
        
        if not invoice_file.external_file_id:
            log_step(step, "检查external_file_id", "info", {
                "message": "文件缺少external_file_id，将在识别时自动上传"
            })
        else:
            log_step(step, "检查external_file_id", "success", {
                "external_file_id": invoice_file.external_file_id
            })
        
        # 步骤10: 检查任务状态
        step += 1
        log_step(step, "检查任务状态", "start")
        
        if task.status == "processing":
            log_step(step, "检查任务状态", "info", {
                "status": "processing",
                "message": "任务当前状态为processing，可能卡住了",
                "start_time": str(task.start_time),
                "duration_seconds": (datetime.now() - task.start_time).total_seconds() if task.start_time else None
            })
        elif task.status == "pending":
            log_step(step, "检查任务状态", "info", {
                "status": "pending",
                "message": "任务状态为pending，可以启动"
            })
        else:
            log_step(step, "检查任务状态", "info", {
                "status": task.status,
                "message": f"任务状态: {task.status}"
            })
        
        # 步骤11: 如果任务状态是pending，尝试启动
        if task.status == "pending":
            step += 1
            log_step(step, "启动识别任务", "start")
            
            try:
                # 更新任务状态
                task.status = "processing"
                task.start_time = datetime.now()
                invoice.recognition_status = "processing"
                session.add(task)
                session.add(invoice)
                session.commit()
                session.refresh(task)
                
                log_step(step, "启动识别任务", "success", {
                    "message": "任务状态已更新为processing"
                })
            except Exception as e:
                log_step(step, "启动识别任务", "failed", {"error": str(e)})
                return
        
        # 步骤12: 调用识别服务
        step += 1
        log_step(step, "调用识别服务", "start", {
            "task_id": str(task.id),
            "service": "SyntaxService.process_task"
        })
        
        start_time = time.time()
        
        try:
            syntax_service = SyntaxService(session)
            log_step(step, "调用识别服务", "info", {"message": "SyntaxService实例已创建"})
            
            # 调用处理任务
            log_step(step, "调用识别服务", "info", {"message": "开始调用process_task..."})
            success = syntax_service.process_task(task.id)
            
            elapsed_time = time.time() - start_time
            
            if success:
                log_step(step, "调用识别服务", "success", {
                    "result": "成功",
                    "elapsed_time_seconds": round(elapsed_time, 2)
                })
                
                # 刷新任务和发票状态
                session.refresh(task)
                session.refresh(invoice)
                
                log_step(step + 1, "检查最终状态", "success", {
                    "task_status": task.status,
                    "invoice_recognition_status": invoice.recognition_status,
                    "task_error_code": getattr(task, "error_code", None),
                    "task_error_message": getattr(task, "error_message", None)
                })
            else:
                log_step(step, "调用识别服务", "failed", {
                    "result": "失败",
                    "elapsed_time_seconds": round(elapsed_time, 2)
                })
                
                # 刷新任务以获取错误信息
                session.refresh(task)
                log_step(step + 1, "获取错误信息", "info", {
                    "task_status": task.status,
                    "error_code": getattr(task, "error_code", None),
                    "error_message": getattr(task, "error_message", None)
                })
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            log_step(step, "调用识别服务", "failed", {
                "error": str(e),
                "elapsed_time_seconds": round(elapsed_time, 2)
            })
            import traceback
            error_trace = traceback.format_exc()
            log_step(step, "调用识别服务", "info", {"traceback": error_trace})
            raise
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        print(f"详细日志已保存到: {LOG_FILE}")
        
    except Exception as e:
        log_step(step + 1, "测试异常", "failed", {"error": str(e)})
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n[错误] 测试过程中发生异常:")
        print(error_trace)
        log_step(step + 1, "测试异常", "info", {"traceback": error_trace})
    finally:
        if session:
            session.close()

if __name__ == "__main__":
    # 可以通过命令行参数指定文件名
    file_name = sys.argv[1] if len(sys.argv) > 1 else "China SY inv 1.PDF"
    test_invoice_recognition(file_name)

