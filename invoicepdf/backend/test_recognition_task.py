#!/usr/bin/env python3
"""
测试识别任务处理脚本
用于诊断发票卡在"识别中"的问题
"""

import logging
import sys
import os
from uuid import UUID
from sqlmodel import select

# 添加backend路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.db import SessionLocal
    from app.models.models_invoice import RecognitionTask, Invoice, InvoiceFile, LLMConfig
    from app.services.dify_service import SyntaxService
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在backend目录中运行此脚本")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_recognition_task(task_id: str = None):
    """测试识别任务处理"""
    
    try:
        with SessionLocal() as session:
            # 如果没有提供任务ID，查找最新的processing状态的任务
            if not task_id:
                task = session.exec(
                    select(RecognitionTask)
                    .where(RecognitionTask.status == "processing")
                    .order_by(RecognitionTask.start_time.desc())
                ).first()
                
                if not task:
                    print("❌ 未找到processing状态的任务")
                    # 查找pending状态的任务
                    task = session.exec(
                        select(RecognitionTask)
                        .where(RecognitionTask.status == "pending")
                        .order_by(RecognitionTask.create_time.desc())
                    ).first()
                    
                    if not task:
                        print("❌ 未找到任何待处理的任务")
                        return
                    else:
                        print(f"找到pending状态的任务: {task.id}")
                else:
                    print(f"找到processing状态的任务: {task.id}")
            else:
                task = session.get(RecognitionTask, UUID(task_id))
                if not task:
                    print(f"❌ 任务不存在: {task_id}")
                    return
            
            print("\n" + "=" * 80)
            print("=== 任务信息 ===")
            print(f"任务ID: {task.id}")
            print(f"任务编号: {task.task_no}")
            print(f"任务状态: {task.status}")
            print(f"创建时间: {task.create_time}")
            print(f"开始时间: {task.start_time}")
            print(f"结束时间: {task.end_time}")
            print(f"错误代码: {getattr(task, 'error_code', None)}")
            print(f"错误消息: {getattr(task, 'error_message', None)}")
            print(f"任务参数: {task.params}")
            
            # 获取票据信息
            invoice = session.get(Invoice, task.invoice_id)
            if invoice:
                print(f"\n票据ID: {invoice.id}")
                print(f"票据编号: {invoice.invoice_no}")
                print(f"识别状态: {invoice.recognition_status}")
                
                # 获取文件信息
                file = session.get(InvoiceFile, invoice.file_id)
                if file:
                    print(f"\n文件ID: {file.id}")
                    print(f"文件名: {file.file_name}")
                    print(f"文件路径: {file.file_path}")
                    print(f"外部文件ID: {file.external_file_id}")
                    print(f"文件是否存在: {os.path.exists(file.file_path) if file.file_path else False}")
            
            # 获取模型配置
            if task.params and task.params.get("model_config_id"):
                model_config_id = task.params.get("model_config_id")
                model_config = session.get(LLMConfig, UUID(model_config_id))
                if model_config:
                    print(f"\n模型配置ID: {model_config.id}")
                    print(f"模型配置名称: {model_config.name}")
                    print(f"API端点: {model_config.endpoint}")
                    print(f"API Key: {'*' * 20 if model_config.api_key else '未设置'}")
                    print(f"是否启用: {model_config.is_active}")
                else:
                    print(f"\n❌ 模型配置不存在: {model_config_id}")
            
            print("=" * 80)
            
            # 询问是否要重新处理任务
            if task.status == "processing":
                print("\n⚠️  任务当前状态为 processing，可能卡住了")
                response = input("是否要重新处理此任务？(y/n): ")
                if response.lower() != 'y':
                    return
                # 重置任务状态为pending
                task.status = "pending"
                session.add(task)
                session.commit()
                print("✅ 任务状态已重置为 pending")
            
            # 处理任务
            print("\n" + "=" * 80)
            print("=== 开始处理任务 ===")
            print("=" * 80)
            
            syntax_service = SyntaxService(session)
            success = syntax_service.process_task(task.id)
            
            print("\n" + "=" * 80)
            if success:
                print("✅ 任务处理成功！")
            else:
                print("❌ 任务处理失败")
                # 重新获取任务以查看错误信息
                task = session.get(RecognitionTask, task.id)
                print(f"错误代码: {getattr(task, 'error_code', None)}")
                print(f"错误消息: {getattr(task, 'error_message', None)}")
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    task_id = sys.argv[1] if len(sys.argv) > 1 else None
    test_recognition_task(task_id)

