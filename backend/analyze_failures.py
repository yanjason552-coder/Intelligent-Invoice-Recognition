#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析发票识别失败原因
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session, select, func, and_
from app.core.db import engine
from app.models.models_invoice import RecognitionTask, Invoice, InvoiceFile, LLMConfig

def analyze_failures():
    """分析失败任务"""
    print("=" * 80)
    print("发票识别失败原因分析")
    print("=" * 80)
    print()
    
    with Session(engine) as session:
        # 1. 统计失败任务
        failed_tasks = session.exec(
            select(RecognitionTask)
            .where(RecognitionTask.status == "failed")
            .order_by(RecognitionTask.create_time.desc())
        ).all()
        
        total_failed = len(failed_tasks)
        print(f"【失败任务总数】: {total_failed}")
        print()
        
        if total_failed == 0:
            print("✓ 没有失败的任务")
            return
        
        # 2. 按错误代码统计
        print("【错误代码统计】")
        print("-" * 80)
        error_codes = Counter()
        error_messages = Counter()
        
        for task in failed_tasks:
            error_code = task.error_code or "UNKNOWN"
            error_codes[error_code] += 1
            
            if task.error_message:
                # 取错误消息的前80个字符作为key
                msg_key = task.error_message[:80]
                error_messages[msg_key] += 1
        
        for error_code, count in error_codes.most_common():
            percentage = (count / total_failed) * 100
            print(f"  {error_code}: {count} 次 ({percentage:.1f}%)")
        
        print()
        
        # 3. 最常见的错误消息
        print("【最常见的错误消息（前10条）】")
        print("-" * 80)
        for msg_key, count in error_messages.most_common(10):
            percentage = (count / total_failed) * 100
            print(f"  [{count} 次 ({percentage:.1f}%)] {msg_key}")
        
        print()
        
        # 4. 最近失败的详细任务
        print("【最近失败的10个任务详情】")
        print("-" * 80)
        
        recent_failed = failed_tasks[:10]
        for i, task in enumerate(recent_failed, 1):
            print(f"\n任务 #{i}:")
            print(f"  任务ID: {task.id}")
            print(f"  任务编号: {task.task_no}")
            print(f"  创建时间: {task.create_time}")
            print(f"  开始时间: {task.start_time or 'N/A'}")
            print(f"  结束时间: {task.end_time or 'N/A'}")
            
            if task.start_time and task.end_time:
                duration = (task.end_time - task.start_time).total_seconds()
                print(f"  耗时: {duration:.2f} 秒 ({duration/60:.1f} 分钟)")
            
            print(f"  错误代码: {task.error_code or 'N/A'}")
            print(f"  错误消息: {task.error_message or 'N/A'}")
            
            # 获取发票和文件信息
            invoice = session.get(Invoice, task.invoice_id)
            if invoice:
                file_info = session.get(InvoiceFile, invoice.file_id)
                if file_info:
                    print(f"  文件名: {file_info.file_name}")
            
            # 获取模型配置信息
            if task.params and task.params.get("model_config_id"):
                try:
                    from uuid import UUID
                    model_config = session.get(LLMConfig, UUID(task.params.get("model_config_id")))
                    if model_config:
                        print(f"  模型配置: {model_config.name}")
                except:
                    pass
            
            print(f"  请求ID: {task.request_id or 'N/A'}")
            print(f"  追踪ID: {task.trace_id or 'N/A'}")
        
        print()
        
        # 5. 按时间段统计
        print("【按时间段统计失败任务】")
        print("-" * 80)
        now = datetime.now()
        time_ranges = [
            ("最近1小时", timedelta(hours=1)),
            ("最近24小时", timedelta(hours=24)),
            ("最近7天", timedelta(days=7)),
            ("最近30天", timedelta(days=30)),
        ]
        
        for label, delta in time_ranges:
            start_time = now - delta
            count = len([t for t in failed_tasks if t.create_time >= start_time])
            print(f"  {label}: {count} 个失败任务")
        
        print()
        
        # 6. 失败率分析
        print("【整体统计】")
        print("-" * 80)
        
        total_tasks = session.exec(select(func.count()).select_from(RecognitionTask)).one()
        completed_tasks = session.exec(
            select(func.count()).select_from(RecognitionTask)
            .where(RecognitionTask.status == "completed")
        ).one()
        
        print(f"  总任务数: {total_tasks}")
        print(f"  已完成: {completed_tasks}")
        print(f"  失败: {total_failed}")
        
        if total_tasks > 0:
            failure_rate = (total_failed / total_tasks) * 100
            success_rate = (completed_tasks / total_tasks) * 100
            print(f"  失败率: {failure_rate:.2f}%")
            print(f"  成功率: {success_rate:.2f}%")
        
        print()
        
        # 7. 错误代码详细说明
        print("【错误代码说明】")
        print("-" * 80)
        error_descriptions = {
            "DIFY_BAD_PARAMS": "任务参数错误（缺少必要参数或参数无效）",
            "FILE_NOT_FOUND": "文件不存在（文件路径错误或文件已被删除）",
            "API_CONFIG_ERROR": "API配置错误（endpoint未配置）",
            "API_AUTH_ERROR": "API认证失败（API key未配置或无效）",
            "FILE_ID_ERROR": "文件缺少外部文件ID（需要使用模型配置上传文件）",
            "DIFY_AUTH_ERROR": "Dify认证失败（API key无效或过期）",
            "DIFY_RATE_LIMIT": "Dify请求频率限制（请求过于频繁）",
            "DIFY_HTTP_ERROR": "Dify HTTP错误（API返回非2xx状态码）",
            "DIFY_TIMEOUT": "Dify请求超时（超过5分钟未响应）",
            "DIFY_ERROR": "Dify API调用失败（其他错误）",
            "INTERNAL_ERROR": "内部错误（系统异常）",
        }
        
        for error_code in error_codes.keys():
            description = error_descriptions.get(error_code, "未知错误")
            print(f"  {error_code}: {description}")
        
        print()
        print("=" * 80)
        print("分析完成")
        print("=" * 80)

if __name__ == "__main__":
    try:
        analyze_failures()
    except Exception as e:
        print(f"分析失败: {str(e)}")
        import traceback
        traceback.print_exc()

