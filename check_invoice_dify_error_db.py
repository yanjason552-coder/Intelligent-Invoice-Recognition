#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查发票的 Dify API 调用失败原因（直接查询数据库）
发票编号: INV-20260205111510-5f22ea3b
"""

import sys
import json
import io
from datetime import datetime
from pathlib import Path
from uuid import UUID

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlmodel import Session, select
from sqlalchemy import text, inspect
from app.core.db import engine
from app.models.models_invoice import Invoice, RecognitionTask, LLMConfig, Template

# 配置
INVOICE_NO = "INV-20260205111510-5f22ea3b"

def find_invoice_by_no(session):
    """通过发票编号查找发票"""
    try:
        # 使用SQL查询
        result = session.execute(
            text("SELECT id, invoice_no, recognition_status, error_code, error_message, create_time FROM invoice WHERE invoice_no = :invoice_no"),
            {"invoice_no": INVOICE_NO}
        )
        row = result.fetchone()
        
        if row:
            class SimpleInvoice:
                def __init__(self, row_data):
                    self.id = row_data[0]
                    self.invoice_no = row_data[1]
                    self.recognition_status = row_data[2]
                    self.error_code = row_data[3]
                    self.error_message = row_data[4]
                    self.create_time = row_data[5]
            
            return SimpleInvoice(row)
        return None
    except Exception as e:
        print(f"查询发票失败: {e}")
        return None

def get_recognition_tasks(session, invoice_id):
    """获取识别任务列表"""
    try:
        result = session.execute(
            text("""
                SELECT id, task_no, invoice_id, template_id, params, status,
                       start_time, end_time, error_code, error_message,
                       request_id, trace_id, create_time
                FROM recognition_task
                WHERE invoice_id = :invoice_id
                ORDER BY create_time DESC
            """),
            {"invoice_id": str(invoice_id)}
        )
        rows = result.fetchall()
        
        tasks = []
        for row in rows:
            class SimpleTask:
                def __init__(self, row_data):
                    self.id = row_data[0]
                    self.task_no = row_data[1]
                    self.invoice_id = row_data[2]
                    self.template_id = row_data[3]
                    self.params = row_data[4]
                    self.status = row_data[5]
                    self.start_time = row_data[6]
                    self.end_time = row_data[7]
                    self.error_code = row_data[8]
                    self.error_message = row_data[9]
                    self.request_id = row_data[10]
                    self.trace_id = row_data[11]
                    self.create_time = row_data[12]
            
            tasks.append(SimpleTask(row))
        return tasks
    except Exception as e:
        print(f"查询识别任务失败: {e}")
        return []

def get_llm_config(session, config_id):
    """获取LLM配置"""
    try:
        result = session.execute(
            text("""
                SELECT id, name, endpoint, api_key, app_id, workflow_id, app_type,
                       is_active, is_default, timeout, max_retries, description
                FROM llm_config
                WHERE id = :config_id
            """),
            {"config_id": str(config_id)}
        )
        row = result.fetchone()
        
        if row:
            class SimpleLLMConfig:
                def __init__(self, row_data):
                    self.id = row_data[0]
                    self.name = row_data[1]
                    self.endpoint = row_data[2]
                    self.api_key = row_data[3]
                    self.app_id = row_data[4]
                    self.workflow_id = row_data[5]
                    self.app_type = row_data[6]
                    self.is_active = row_data[7]
                    self.is_default = row_data[8]
                    self.timeout = row_data[9]
                    self.max_retries = row_data[10]
                    self.description = row_data[11]
            
            return SimpleLLMConfig(row)
        return None
    except Exception as e:
        print(f"查询LLM配置失败: {e}")
        return None

def get_template(session, template_id):
    """获取模板信息"""
    try:
        result = session.execute(
            text("""
                SELECT id, name, prompt, schema
                FROM template
                WHERE id = :template_id
            """),
            {"template_id": str(template_id)}
        )
        row = result.fetchone()
        
        if row:
            class SimpleTemplate:
                def __init__(self, row_data):
                    self.id = row_data[0]
                    self.name = row_data[1]
                    self.prompt = row_data[2]
                    self.schema = row_data[3]
            
            return SimpleTemplate(row)
        return None
    except Exception as e:
        print(f"查询模板失败: {e}")
        return None

def diagnose_task(task, session):
    """诊断任务失败原因"""
    print("=" * 80)
    print("任务诊断报告")
    print("=" * 80)
    print()
    
    print(f"任务ID: {task.id}")
    print(f"任务编号: {task.task_no}")
    print(f"状态: {task.status}")
    print(f"创建时间: {task.create_time}")
    print(f"开始时间: {task.start_time or 'N/A'}")
    print(f"结束时间: {task.end_time or 'N/A'}")
    print()
    
    # 检查错误信息
    if task.error_code:
        print(f"❌ 错误代码: {task.error_code}")
    if task.error_message:
        print(f"❌ 错误消息: {task.error_message}")
        print()
    
    # 检查任务参数
    params = task.params
    if params:
        print("任务参数:")
        model_config_id = params.get('model_config_id')
        template_id = params.get('template_id') or task.template_id
        template_prompt = params.get('template_prompt')
        
        if model_config_id:
            print(f"  ✅ 模型配置ID: {model_config_id}")
            
            # 检查模型配置
            llm_config = get_llm_config(session, model_config_id)
            if llm_config:
                print(f"  ✅ 模型配置名称: {llm_config.name}")
                print(f"  ✅ API端点: {llm_config.endpoint}")
                print(f"  ✅ 应用类型: {llm_config.app_type}")
                print(f"  ✅ 工作流ID: {llm_config.workflow_id or 'N/A'}")
                print(f"  ✅ 应用ID: {llm_config.app_id or 'N/A'}")
                print(f"  ✅ 是否启用: {llm_config.is_active}")
                print(f"  ✅ 是否默认: {llm_config.is_default}")
                print(f"  ✅ 超时时间: {llm_config.timeout}秒")
                print(f"  ✅ 最大重试: {llm_config.max_retries}次")
                
                # 检查配置是否完整
                issues = []
                if not llm_config.endpoint:
                    issues.append("API端点地址为空")
                if not llm_config.api_key:
                    issues.append("API密钥为空")
                if llm_config.app_type == 'workflow' and not llm_config.workflow_id:
                    issues.append("工作流类型但未设置 workflow_id")
                if llm_config.app_type == 'chat' and not llm_config.app_id:
                    issues.append("对话类型但未设置 app_id")
                if not llm_config.is_active:
                    issues.append("配置未启用")
                
                if issues:
                    print(f"  ⚠️  配置问题:")
                    for issue in issues:
                        print(f"     - {issue}")
            else:
                print(f"  ❌ 模型配置不存在: {model_config_id}")
        else:
            print(f"  ❌ 模型配置ID未设置")
        
        if template_id:
            print(f"  ✅ 模板ID: {template_id}")
            
            # 检查模板
            template = get_template(session, template_id)
            if template:
                print(f"  ✅ 模板名称: {template.name}")
                if template.prompt:
                    print(f"  ✅ 模板提示词已设置，长度: {len(str(template.prompt))} 字符")
                else:
                    print(f"  ⚠️  模板提示词未设置")
                if template.schema:
                    schema_str = json.dumps(template.schema, ensure_ascii=False) if isinstance(template.schema, dict) else str(template.schema)
                    print(f"  ✅ 模板Schema已设置，长度: {len(schema_str)} 字符")
                else:
                    print(f"  ⚠️  模板Schema未设置")
            else:
                print(f"  ❌ 模板不存在: {template_id}")
        else:
            print(f"  ⚠️  模板ID未设置")
        
        if template_prompt:
            prompt_str = str(template_prompt)
            print(f"  ✅ 提示词已包含在任务参数中，长度: {len(prompt_str)} 字符")
            print(f"  ✅ 提示词预览: {prompt_str[:100]}...")
        else:
            print(f"  ⚠️  提示词未包含在任务参数中")
        print()
    else:
        print("❌ 任务参数不存在")
        print()
    
    # 检查 Dify API 调用信息
    if task.request_id:
        print(f"✅ Dify API 已调用")
        print(f"   Request ID: {task.request_id}")
    else:
        print(f"❌ Dify API 未调用（没有 request_id）")
    
    if task.trace_id:
        print(f"   Trace ID: {task.trace_id}")
    print()
    
    # 根据错误代码提供建议
    if task.error_code:
        print("=" * 80)
        print("错误分析:")
        print("=" * 80)
        
        error_code_upper = task.error_code.upper()
        error_message = task.error_message or ""
        
        if "TIMEOUT" in error_code_upper or "超时" in error_message:
            print("🔍 问题: 请求超时")
            print("💡 建议:")
            print("   1. 检查网络连接")
            print("   2. 检查 Dify API 端点地址是否正确")
            print("   3. 增加超时时间配置")
        
        elif "CONNECT" in error_code_upper or "连接" in error_message or "Connection" in error_message:
            print("🔍 问题: 无法连接到 Dify API")
            print("💡 建议:")
            print("   1. 检查 Dify API 端点地址是否正确")
            print("   2. 检查网络连接")
            print("   3. 检查防火墙设置")
            print("   4. 尝试在浏览器中访问 Dify API 端点")
        
        elif "AUTH" in error_code_upper or "401" in error_message or "403" in error_message or "Unauthorized" in error_message:
            print("🔍 问题: 认证失败")
            print("💡 建议:")
            print("   1. 检查 API 密钥是否正确")
            print("   2. 检查 API 密钥是否过期")
            print("   3. 重新配置 API 密钥")
        
        elif "NOT_FOUND" in error_code_upper or "404" in error_message:
            print("🔍 问题: 资源未找到")
            print("💡 建议:")
            print("   1. 检查 workflow_id 或 app_id 是否正确")
            print("   2. 检查 Dify 平台上的工作流/应用是否存在")
        
        elif "BAD_PARAMS" in error_code_upper:
            print("🔍 问题: 参数错误")
            print("💡 建议:")
            print("   1. 检查模型配置是否完整")
            print("   2. 检查任务参数是否正确")
            print("   3. 检查模板配置是否正确")
        
        elif "FILE_NOT_FOUND" in error_code_upper:
            print("🔍 问题: 文件未找到")
            print("💡 建议:")
            print("   1. 检查发票文件是否存在")
            print("   2. 检查文件路径是否正确")
        
        else:
            print(f"🔍 问题: {task.error_code}")
            print("💡 建议:")
            print("   1. 查看后端日志获取详细错误信息")
            print("   2. 检查 Dify API 配置")
            print("   3. 检查网络连接")
            print(f"   4. 错误消息: {error_message[:200]}")
        
        print()

def main():
    """主函数"""
    print("=" * 80)
    print("发票 Dify API 调用失败诊断工具（数据库查询）")
    print("=" * 80)
    print(f"发票编号: {INVOICE_NO}")
    print()
    
    with Session(engine) as session:
        # 查找发票
        print("正在查找发票...")
        invoice = find_invoice_by_no(session)
        
        if not invoice:
            print("❌ 未找到发票，请检查发票编号是否正确")
            return
        
        invoice_id = invoice.id
        print(f"✅ 找到发票")
        print(f"   发票ID: {invoice_id}")
        print(f"   发票编号: {invoice.invoice_no}")
        print(f"   识别状态: {invoice.recognition_status}")
        if invoice.error_code:
            print(f"   错误代码: {invoice.error_code}")
        if invoice.error_message:
            print(f"   错误消息: {invoice.error_message}")
        print(f"   创建时间: {invoice.create_time}")
        print()
        
        # 获取识别任务
        print("正在查找识别任务...")
        tasks = get_recognition_tasks(session, invoice_id)
        
        if not tasks:
            print("❌ 未找到识别任务")
            return
        
        print(f"✅ 找到 {len(tasks)} 个识别任务")
        print()
        
        # 诊断每个任务
        for i, task in enumerate(tasks, 1):
            print(f"\n任务 {i}/{len(tasks)}:")
            diagnose_task(task, session)
            print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()

