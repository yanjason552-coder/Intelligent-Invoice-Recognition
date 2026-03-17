#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询特定票据的失败原因
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session, select
from app.core.db import engine
from app.models.models_invoice import Invoice, RecognitionTask, RecognitionResult, InvoiceFile, LLMConfig

def check_invoice_failure(invoice_no: str):
    """查询票据失败原因"""
    print("=" * 80)
    print(f"查询票据失败原因: {invoice_no}")
    print("=" * 80)
    print()
    
    with Session(engine) as session:
        # 1. 查找票据
        invoice = session.exec(
            select(Invoice).where(Invoice.invoice_no == invoice_no)
        ).first()
        
        if not invoice:
            print(f"❌ 未找到票据: {invoice_no}")
            return
        
        print(f"【票据信息】")
        print(f"  票据ID: {invoice.id}")
        print(f"  票据编号: {invoice.invoice_no}")
        print(f"  识别状态: {invoice.recognition_status}")
        print(f"  创建时间: {invoice.create_time}")
        print(f"  更新时间: {invoice.update_time}")
        print()
        
        # 2. 查找文件信息
        file_info = session.get(InvoiceFile, invoice.file_id)
        if file_info:
            print(f"【文件信息】")
            print(f"  文件ID: {file_info.id}")
            print(f"  文件名: {file_info.file_name}")
            print(f"  文件路径: {file_info.file_path}")
            print(f"  外部文件ID: {file_info.external_file_id}")
            print(f"  文件大小: {file_info.file_size} bytes")
            print()
        
        # 3. 查找识别任务
        tasks = session.exec(
            select(RecognitionTask)
            .where(RecognitionTask.invoice_id == invoice.id)
            .order_by(RecognitionTask.create_time.desc())
        ).all()
        
        if not tasks:
            print("❌ 未找到识别任务")
            return
        
        print(f"【识别任务】共找到 {len(tasks)} 个任务")
        print()
        
        for i, task in enumerate(tasks, 1):
            print(f"任务 #{i}:")
            print(f"  任务ID: {task.id}")
            print(f"  任务编号: {task.task_no}")
            print(f"  状态: {task.status}")
            print(f"  创建时间: {task.create_time}")
            print(f"  开始时间: {task.start_time or 'N/A'}")
            print(f"  结束时间: {task.end_time or 'N/A'}")
            
            if task.start_time and task.end_time:
                duration = (task.end_time - task.start_time).total_seconds()
                print(f"  耗时: {duration:.2f} 秒 ({duration/60:.1f} 分钟)")
            
            # 显示错误信息
            if task.status == "failed":
                print(f"  ❌ 错误代码: {task.error_code or 'N/A'}")
                print(f"  ❌ 错误消息: {task.error_message or 'N/A'}")
            
            # 显示任务参数
            if task.params:
                print(f"  模型配置ID: {task.params.get('model_config_id', 'N/A')}")
                print(f"  Schema ID: {task.params.get('output_schema_id', 'N/A')}")
                
                # 获取模型配置信息
                if task.params.get("model_config_id"):
                    try:
                        from uuid import UUID
                        model_config = session.get(LLMConfig, UUID(task.params.get("model_config_id")))
                        if model_config:
                            print(f"  模型配置名称: {model_config.name}")
                            print(f"  模型配置状态: {'启用' if model_config.is_active else '禁用'}")
                            print(f"  API Endpoint: {model_config.endpoint or 'N/A'}")
                            print(f"  API Key: {'已配置' if model_config.api_key else '未配置'}")
                    except Exception as e:
                        print(f"  获取模型配置失败: {str(e)}")
            
            print(f"  请求ID: {task.request_id or 'N/A'}")
            print(f"  追踪ID: {task.trace_id or 'N/A'}")
            print()
        
        # 4. 查找识别结果
        results = session.exec(
            select(RecognitionResult)
            .where(RecognitionResult.invoice_id == invoice.id)
            .order_by(RecognitionResult.recognition_time.desc())
        ).all()
        
        if results:
            print(f"【识别结果】共找到 {len(results)} 个结果")
            for i, result in enumerate(results, 1):
                print(f"  结果 #{i}:")
                print(f"    状态: {result.status}")
                print(f"    识别时间: {result.recognition_time}")
                print(f"    准确率: {result.accuracy}")
                print(f"    置信度: {result.confidence}")
                print()
        else:
            print("【识别结果】未找到识别结果")
            print()
        
        # 5. 失败原因分析
        failed_tasks = [t for t in tasks if t.status == "failed"]
        if failed_tasks:
            print("=" * 80)
            print("【失败原因分析】")
            print("=" * 80)
            
            for task in failed_tasks:
                error_code = task.error_code or "UNKNOWN"
                error_message = task.error_message or "无错误消息"
                
                print(f"\n错误代码: {error_code}")
                print(f"错误消息: {error_message}")
                
                # 根据错误代码提供建议
                suggestions = {
                    "DIFY_BAD_PARAMS": "检查任务参数是否正确，特别是 model_config_id 和 output_schema_id",
                    "FILE_NOT_FOUND": "检查文件是否存在，文件路径是否正确",
                    "API_CONFIG_ERROR": "检查模型配置的 API endpoint 是否配置",
                    "API_AUTH_ERROR": "检查模型配置的 API key 是否配置且有效",
                    "FILE_ID_ERROR": "文件缺少外部文件ID，需要使用模型配置上传文件",
                    "DIFY_AUTH_ERROR": "Dify API 认证失败，检查 API key 是否有效",
                    "DIFY_RATE_LIMIT": "Dify API 请求频率限制，请稍后重试",
                    "DIFY_HTTP_ERROR": "Dify API 返回 HTTP 错误，检查 API 服务状态",
                    "DIFY_TIMEOUT": "Dify API 请求超时，可能是网络问题或 API 服务响应慢",
                    "DIFY_ERROR": "Dify API 调用失败，查看详细错误消息",
                    "INTERNAL_ERROR": "系统内部错误，查看后端日志获取详细信息"
                }
                
                if error_code in suggestions:
                    print(f"建议: {suggestions[error_code]}")
                
                # 检查常见问题
                if error_code == "FILE_NOT_FOUND" and file_info:
                    import os
                    if not os.path.exists(file_info.file_path):
                        print(f"  ⚠️  文件路径不存在: {file_info.file_path}")
                    if not file_info.external_file_id:
                        print(f"  ⚠️  文件缺少外部文件ID，需要使用模型配置上传文件")
                
                if error_code in ["API_CONFIG_ERROR", "API_AUTH_ERROR", "DIFY_AUTH_ERROR"]:
                    if task.params and task.params.get("model_config_id"):
                        try:
                            from uuid import UUID
                            model_config = session.get(LLMConfig, UUID(task.params.get("model_config_id")))
                            if model_config:
                                if not model_config.endpoint:
                                    print(f"  ⚠️  模型配置缺少 API endpoint")
                                if not model_config.api_key:
                                    print(f"  ⚠️  模型配置缺少 API key")
                                if not model_config.is_active:
                                    print(f"  ⚠️  模型配置未启用")
                        except:
                            pass
        
        print()
        print("=" * 80)
        print("查询完成")
        print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        invoice_no = sys.argv[1]
    else:
        invoice_no = "INV-20260128132454-562b946f"
    
    try:
        check_invoice_failure(invoice_no)
    except Exception as e:
        print(f"查询失败: {str(e)}")
        import traceback
        traceback.print_exc()

