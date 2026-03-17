#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询票据失败原因
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session, select
from app.core.db import engine
from app.models.models_invoice import Invoice, RecognitionTask, RecognitionResult, InvoiceFile, LLMConfig

def query_invoice(invoice_no: str):
    """查询票据详情和失败原因"""
    print("=" * 80)
    print(f"查询票据: {invoice_no}")
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
            print(f"  外部文件ID: {file_info.external_file_id or '未设置'}")
            print(f"  文件大小: {file_info.file_size} bytes")
            print()
        
        # 3. 查找所有识别任务
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
                model_config_id = task.params.get('model_config_id')
                schema_id = task.params.get('output_schema_id')
                print(f"  模型配置ID: {model_config_id or 'N/A'}")
                print(f"  Schema ID: {schema_id or 'N/A'}")
                
                # 获取模型配置信息
                if model_config_id:
                    try:
                        from uuid import UUID
                        model_config = session.get(LLMConfig, UUID(model_config_id))
                        if model_config:
                            print(f"  模型配置名称: {model_config.name}")
                            print(f"  模型配置状态: {'✅ 启用' if model_config.is_active else '❌ 禁用'}")
                            print(f"  API Endpoint: {model_config.endpoint or '❌ 未配置'}")
                            print(f"  API Key: {'✅ 已配置' if model_config.api_key else '❌ 未配置'}")
                    except Exception as e:
                        print(f"  获取模型配置失败: {str(e)}")
            
            print(f"  请求ID: {task.request_id or 'N/A'}")
            print(f"  追踪ID: {task.trace_id or 'N/A'}")
            print()
        
        # 4. 失败原因分析
        failed_tasks = [t for t in tasks if t.status == "failed"]
        if failed_tasks:
            print("=" * 80)
            print("【失败原因分析】")
            print("=" * 80)
            
            latest_failed = failed_tasks[0]  # 最新的失败任务
            error_code = latest_failed.error_code or "UNKNOWN"
            error_message = latest_failed.error_message or "无错误消息"
            
            print(f"\n最新失败任务:")
            print(f"  任务编号: {latest_failed.task_no}")
            print(f"  错误代码: {error_code}")
            print(f"  错误消息: {error_message}")
            print()
            
            # 根据错误代码提供详细分析和建议
            error_analysis = {
                "DIFY_BAD_PARAMS": {
                    "原因": "任务参数错误",
                    "可能原因": [
                        "任务参数不存在",
                        "缺少 model_config_id",
                        "模型配置不存在或未启用"
                    ],
                    "解决方案": [
                        "检查任务参数是否完整",
                        "确认模型配置ID是否正确",
                        "确认模型配置是否存在且已启用"
                    ]
                },
                "FILE_NOT_FOUND": {
                    "原因": "文件不存在",
                    "可能原因": [
                        "文件路径不存在",
                        "文件已被删除",
                        "文件路径配置错误"
                    ],
                    "解决方案": [
                        "检查文件路径是否正确",
                        "确认文件是否存在于服务器",
                        "如果文件不存在，需要重新上传"
                    ]
                },
                "API_CONFIG_ERROR": {
                    "原因": "API配置错误",
                    "可能原因": [
                        "API endpoint未配置",
                        "API endpoint配置错误"
                    ],
                    "解决方案": [
                        "检查模型配置中的API endpoint设置",
                        "确认endpoint URL格式正确"
                    ]
                },
                "API_AUTH_ERROR": {
                    "原因": "API认证失败",
                    "可能原因": [
                        "API key未配置",
                        "API key无效或过期"
                    ],
                    "解决方案": [
                        "检查模型配置中的API key设置",
                        "确认API key是否有效",
                        "如果API key过期，需要更新"
                    ]
                },
                "FILE_ID_ERROR": {
                    "原因": "文件缺少外部文件ID",
                    "可能原因": [
                        "文件未通过模型配置上传",
                        "文件缺少external_file_id字段"
                    ],
                    "解决方案": [
                        "使用模型配置上传文件",
                        "确保文件有external_file_id"
                    ]
                },
                "DIFY_AUTH_ERROR": {
                    "原因": "Dify API认证失败",
                    "可能原因": [
                        "API key无效",
                        "API key过期",
                        "API key权限不足"
                    ],
                    "解决方案": [
                        "检查API key是否正确",
                        "确认API key是否过期",
                        "检查API key权限"
                    ]
                },
                "DIFY_RATE_LIMIT": {
                    "原因": "Dify API请求频率限制",
                    "可能原因": [
                        "请求过于频繁",
                        "超过API调用限制"
                    ],
                    "解决方案": [
                        "等待一段时间后重试",
                        "检查API调用频率限制",
                        "考虑升级API套餐"
                    ]
                },
                "DIFY_HTTP_ERROR": {
                    "原因": "Dify API HTTP错误",
                    "可能原因": [
                        "API服务返回非2xx状态码",
                        "API服务异常"
                    ],
                    "解决方案": [
                        "检查Dify API服务状态",
                        "查看详细错误消息",
                        "联系API服务提供商"
                    ]
                },
                "DIFY_TIMEOUT": {
                    "原因": "Dify API请求超时",
                    "可能原因": [
                        "网络连接问题",
                        "API服务响应慢",
                        "请求处理时间过长"
                    ],
                    "解决方案": [
                        "检查网络连接",
                        "稍后重试",
                        "检查API服务状态"
                    ]
                },
                "DIFY_ERROR": {
                    "原因": "Dify API调用失败",
                    "可能原因": [
                        "API调用异常",
                        "请求参数错误",
                        "API服务异常"
                    ],
                    "解决方案": [
                        "查看详细错误消息",
                        "检查请求参数",
                        "检查API服务状态"
                    ]
                },
                "INTERNAL_ERROR": {
                    "原因": "系统内部错误",
                    "可能原因": [
                        "系统异常",
                        "数据库操作失败",
                        "代码逻辑错误"
                    ],
                    "解决方案": [
                        "查看后端日志获取详细信息",
                        "检查系统状态",
                        "联系技术支持"
                    ]
                }
            }
            
            if error_code in error_analysis:
                analysis = error_analysis[error_code]
                print(f"错误类型: {analysis['原因']}")
                print(f"\n可能原因:")
                for reason in analysis['可能原因']:
                    print(f"  • {reason}")
                print(f"\n解决方案:")
                for solution in analysis['解决方案']:
                    print(f"  • {solution}")
            else:
                print(f"未知错误代码: {error_code}")
                print(f"错误消息: {error_message}")
            
            # 检查常见问题
            print(f"\n【问题检查】")
            if error_code == "FILE_NOT_FOUND" and file_info:
                import os
                if not os.path.exists(file_info.file_path):
                    print(f"  ❌ 文件路径不存在: {file_info.file_path}")
                else:
                    print(f"  ✅ 文件路径存在: {file_info.file_path}")
                if not file_info.external_file_id:
                    print(f"  ❌ 文件缺少外部文件ID")
                else:
                    print(f"  ✅ 文件有外部文件ID: {file_info.external_file_id}")
            
            if error_code in ["API_CONFIG_ERROR", "API_AUTH_ERROR", "DIFY_AUTH_ERROR"]:
                if latest_failed.params and latest_failed.params.get("model_config_id"):
                    try:
                        from uuid import UUID
                        model_config = session.get(LLMConfig, UUID(latest_failed.params.get("model_config_id")))
                        if model_config:
                            if not model_config.endpoint:
                                print(f"  ❌ 模型配置缺少 API endpoint")
                            else:
                                print(f"  ✅ API endpoint: {model_config.endpoint}")
                            if not model_config.api_key:
                                print(f"  ❌ 模型配置缺少 API key")
                            else:
                                print(f"  ✅ API key已配置")
                            if not model_config.is_active:
                                print(f"  ❌ 模型配置未启用")
                            else:
                                print(f"  ✅ 模型配置已启用")
                    except Exception as e:
                        print(f"  ⚠️  获取模型配置信息失败: {str(e)}")
        
        print()
        print("=" * 80)
        print("查询完成")
        print("=" * 80)

if __name__ == "__main__":
    invoice_no = "INV-20260128132454-562b946f"
    try:
        query_invoice(invoice_no)
    except Exception as e:
        print(f"查询失败: {str(e)}")
        import traceback
        traceback.print_exc()

