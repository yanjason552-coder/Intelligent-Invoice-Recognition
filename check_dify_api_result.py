#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Dify API 调用的详细结果
发票编号: INV-20260205094615-6984b5c4
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlmodel import Session, select
from sqlalchemy import text
from app.core.db import engine
from app.models.models_invoice import Invoice, RecognitionTask, RecognitionResult

# 配置
INVOICE_NO = "INV-20260205094615-6984b5c4"

def check_task_dify_api_result():
    """检查任务的 Dify API 调用结果"""
    print("=" * 80)
    print("检查 Dify API 调用详细结果")
    print("=" * 80)
    print(f"发票编号: {INVOICE_NO}")
    print()
    
    with Session(engine) as session:
        # 查找发票
        invoice = session.exec(
            select(Invoice).where(Invoice.invoice_no == INVOICE_NO)
        ).first()
        
        if not invoice:
            print(f"❌ 未找到发票: {INVOICE_NO}")
            return
        
        print(f"✅ 找到发票:")
        print(f"   发票ID: {invoice.id}")
        print(f"   发票编号: {invoice.invoice_no}")
        print(f"   识别状态: {invoice.recognition_status}")
        print()
        
        # 查找识别任务
        try:
            result = session.execute(
                text("""
                    SELECT id, task_no, invoice_id, template_id, params, status, 
                           priority, start_time, end_time, duration, error_message, 
                           error_code, provider, request_id, trace_id, operator_id, create_time
                    FROM recognition_task
                    WHERE invoice_id = :invoice_id
                    ORDER BY create_time DESC
                    LIMIT 1
                """),
                {"invoice_id": str(invoice.id)}
            )
            row = result.fetchone()
            
            if not row:
                print("❌ 未找到识别任务")
                return
            
            task_id = row[0]
            task_no = row[1]
            status = row[5]
            start_time = row[7]
            end_time = row[8]
            duration = row[9]
            error_message = row[10]
            error_code = row[11]
            request_id = row[13]
            trace_id = row[14]
            create_time = row[16]
            
            print(f"✅ 找到识别任务:")
            print(f"   任务ID: {task_id}")
            print(f"   任务编号: {task_no}")
            print(f"   状态: {status}")
            print(f"   创建时间: {create_time}")
            if start_time:
                print(f"   开始时间: {start_time}")
            if end_time:
                print(f"   结束时间: {end_time}")
            if duration:
                print(f"   耗时: {duration:.2f}秒")
            print()
            
            # 检查任务参数
            params = row[4]
            if params:
                print("=" * 80)
                print("任务参数:")
                print("=" * 80)
                print(json.dumps(params, ensure_ascii=False, indent=2))
                print()
            
            # 检查 Dify API 调用信息
            print("=" * 80)
            print("Dify API 调用信息:")
            print("=" * 80)
            if request_id:
                print(f"✅ 请求ID (request_id): {request_id}")
            else:
                print("⚠️  请求ID (request_id): 未设置（API可能未调用）")
            
            if trace_id:
                print(f"✅ 追踪ID (trace_id): {trace_id}")
            else:
                print("⚠️  追踪ID (trace_id): 未设置")
            
            if error_code:
                print(f"❌ 错误代码: {error_code}")
            if error_message:
                print(f"❌ 错误消息: {error_message}")
            print()
            
            # 检查识别结果
            print("=" * 80)
            print("识别结果:")
            print("=" * 80)
            try:
                results = session.exec(
                    select(RecognitionResult)
                    .where(RecognitionResult.invoice_id == invoice.id)
                    .order_by(RecognitionResult.create_time.desc())
                ).all()
                
                if results:
                    for i, result in enumerate(results, 1):
                        print(f"\n结果 {i}:")
                        print(f"  结果ID: {result.id}")
                        print(f"  创建时间: {result.create_time}")
                        print(f"  识别模式: {result.recognition_mode}")
                        print(f"  准确率: {result.accuracy}")
                        
                        # 检查原始响应
                        if hasattr(result, 'raw_response') and result.raw_response:
                            print(f"  原始响应: {json.dumps(result.raw_response, ensure_ascii=False, indent=2)[:500]}...")
                        
                        # 检查识别字段
                        if hasattr(result, 'normalized_fields') and result.normalized_fields:
                            print(f"  识别字段数量: {len(result.normalized_fields)}")
                            print(f"  识别字段预览:")
                            for key, value in list(result.normalized_fields.items())[:5]:
                                print(f"    {key}: {value}")
                            if len(result.normalized_fields) > 5:
                                print(f"    ... 还有 {len(result.normalized_fields) - 5} 个字段")
                else:
                    print("⚠️  未找到识别结果")
            except Exception as e:
                print(f"⚠️  查询识别结果失败: {e}")
                # 尝试使用原始SQL查询
                try:
                    result_sql = session.execute(
                        text("""
                            SELECT id, invoice_id, recognition_mode, accuracy, normalized_fields, 
                                   raw_response, create_time
                            FROM recognition_result
                            WHERE invoice_id = :invoice_id
                            ORDER BY create_time DESC
                            LIMIT 1
                        """),
                        {"invoice_id": str(invoice.id)}
                    )
                    result_row = result_sql.fetchone()
                    
                    if result_row:
                        print(f"\n✅ 找到识别结果 (通过SQL查询):")
                        print(f"  结果ID: {result_row[0]}")
                        print(f"  创建时间: {result_row[6]}")
                        print(f"  识别模式: {result_row[2]}")
                        print(f"  准确率: {result_row[3]}")
                        
                        if result_row[4]:  # normalized_fields
                            fields = result_row[4]
                            if isinstance(fields, dict):
                                print(f"  识别字段数量: {len(fields)}")
                                print(f"  识别字段预览:")
                                for key, value in list(fields.items())[:5]:
                                    print(f"    {key}: {value}")
                                if len(fields) > 5:
                                    print(f"    ... 还有 {len(fields) - 5} 个字段")
                        
                        if result_row[5]:  # raw_response
                            raw_resp = result_row[5]
                            if isinstance(raw_resp, dict):
                                print(f"  原始响应预览:")
                                print(f"    {json.dumps(raw_resp, ensure_ascii=False, indent=2)[:500]}...")
                    else:
                        print("⚠️  未找到识别结果")
                except Exception as sql_e:
                    print(f"⚠️  SQL查询也失败: {sql_e}")
            
            print()
            
            # 检查日志文件（如果存在）
            print("=" * 80)
            print("日志文件位置:")
            print("=" * 80)
            print("Dify API 调用的详细日志应该在后端服务的控制台输出中")
            print("请查看运行后端服务的终端窗口，查找以下关键词:")
            print("  - '=== 调用SYNTAX API ==='")
            print("  - '=== SYNTAX API 响应 ==='")
            print("  - '完整响应内容:'")
            print("  - '响应关键字段'")
            print()
            
            # 根据任务状态给出建议
            print("=" * 80)
            print("诊断建议:")
            print("=" * 80)
            if status == "pending":
                print("⚠️  任务状态为 pending，尚未启动")
                print("   需要调用启动API: POST /api/v1/invoices/recognition-tasks/{task_id}/start")
            elif status == "processing":
                print("⏳ 任务状态为 processing，正在执行中")
                print("   请查看后端服务日志获取详细调用信息")
            elif status == "completed":
                if request_id:
                    print("✅ 任务已完成，Dify API 已调用")
                    print(f"   请求ID: {request_id}")
                    if trace_id:
                        print(f"   追踪ID: {trace_id}")
                else:
                    print("⚠️  任务已完成，但未找到 request_id")
            elif status == "failed":
                print("❌ 任务失败")
                if error_code:
                    print(f"   错误代码: {error_code}")
                if error_message:
                    print(f"   错误消息: {error_message}")
                print("   请查看后端服务日志获取详细错误信息")
            print()
            
        except Exception as e:
            print(f"❌ 查询任务失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        check_task_dify_api_result()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

