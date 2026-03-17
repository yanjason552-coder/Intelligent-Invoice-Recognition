#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查发票的 Dify API 调用失败原因
发票编号: INV-20260205111510-5f22ea3b
"""

import sys
import requests
import json
import os
from datetime import datetime

# 配置
INVOICE_NO = "INV-20260205111510-5f22ea3b"
BASE_URL = "http://localhost:8000"

def get_access_token():
    """获取访问令牌"""
    # 方式1: 从命令行参数获取
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1]
    
    # 方式2: 从环境变量获取
    if not token:
        token = os.getenv("ACCESS_TOKEN")
    
    # 方式3: 交互式输入
    if not token:
        print("需要访问令牌 (access_token)")
        print("请从浏览器开发者工具中获取:")
        print("  1. 打开浏览器开发者工具 (F12)")
        print("  2. 进入 Application/存储 -> Local Storage")
        print("  3. 找到 access_token 的值")
        print()
        try:
            token = input("请输入 access_token: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n未提供 access_token，无法继续")
            return None
    
    if not token:
        print("未提供 access_token，无法继续")
        return None
    
    return token

def find_invoice_by_no(token, invoice_no):
    """通过发票编号查找发票"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 获取发票列表，搜索匹配的发票编号
        response = requests.get(
            f"{BASE_URL}/api/v1/invoices",
            headers=headers,
            params={"limit": 1000}
        )
        
        if response.status_code == 200:
            data = response.json()
            invoices = data.get("data", [])
            
            # 查找匹配的发票编号
            for invoice in invoices:
                if invoice.get("invoice_no") == invoice_no:
                    return invoice
            
            print(f"未找到发票编号: {invoice_no}")
            print(f"共查询到 {len(invoices)} 个发票")
            return None
        else:
            print(f"查询发票列表失败: HTTP {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"查询发票列表失败: {e}")
        return None

def get_invoice_detail(token, invoice_id):
    """获取发票详情"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/invoices/{invoice_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"获取发票详情失败: HTTP {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"获取发票详情失败: {e}")
        return None

def get_recognition_tasks(token, invoice_id):
    """获取识别任务列表"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/invoices/recognition-tasks",
            headers=headers,
            params={"limit": 100}
        )
        
        if response.status_code == 200:
            data = response.json()
            tasks = data.get("data", [])
            # 过滤出该发票的任务
            invoice_tasks = [t for t in tasks if t.get("invoice_id") == invoice_id]
            return invoice_tasks
        else:
            print(f"获取任务列表失败: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"获取任务列表失败: {e}")
        return []

def get_llm_config(token, config_id):
    """获取LLM配置"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 获取配置列表
        response = requests.get(
            f"{BASE_URL}/api/v1/config/llm/list",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            configs = data.get("data", [])
            for config in configs:
                if config.get("id") == config_id:
                    return config
            return None
        else:
            return None
    except Exception as e:
        print(f"获取LLM配置失败: {e}")
        return None

def diagnose_task(task, token):
    """诊断任务失败原因"""
    print("=" * 80)
    print("任务诊断报告")
    print("=" * 80)
    print()
    
    print(f"任务ID: {task.get('id')}")
    print(f"任务编号: {task.get('task_no', 'N/A')}")
    print(f"状态: {task.get('status', 'N/A')}")
    print(f"创建时间: {task.get('create_time', 'N/A')}")
    print(f"开始时间: {task.get('start_time', 'N/A')}")
    print(f"结束时间: {task.get('end_time', 'N/A')}")
    print()
    
    # 检查错误信息
    error_code = task.get('error_code')
    error_message = task.get('error_message')
    
    if error_code:
        print(f"❌ 错误代码: {error_code}")
    if error_message:
        print(f"❌ 错误消息: {error_message}")
        print()
    
    # 检查任务参数
    params = task.get('params', {})
    if params:
        print("任务参数:")
        model_config_id = params.get('model_config_id')
        template_id = params.get('template_id')
        template_prompt = params.get('template_prompt')
        
        if model_config_id:
            print(f"  ✅ 模型配置ID: {model_config_id}")
            
            # 检查模型配置
            llm_config = get_llm_config(token, model_config_id)
            if llm_config:
                print(f"  ✅ 模型配置名称: {llm_config.get('name', 'N/A')}")
                print(f"  ✅ API端点: {llm_config.get('endpoint', 'N/A')}")
                print(f"  ✅ 应用类型: {llm_config.get('app_type', 'N/A')}")
                print(f"  ✅ 工作流ID: {llm_config.get('workflow_id', 'N/A')}")
                print(f"  ✅ 应用ID: {llm_config.get('app_id', 'N/A')}")
                print(f"  ✅ 是否启用: {llm_config.get('is_active', False)}")
                print(f"  ✅ 是否默认: {llm_config.get('is_default', False)}")
                
                # 检查配置是否完整
                if not llm_config.get('endpoint'):
                    print(f"  ❌ 警告: API端点地址为空")
                if not llm_config.get('api_key'):
                    print(f"  ❌ 警告: API密钥为空")
                if llm_config.get('app_type') == 'workflow' and not llm_config.get('workflow_id'):
                    print(f"  ❌ 警告: 工作流类型但未设置 workflow_id")
                if llm_config.get('app_type') == 'chat' and not llm_config.get('app_id'):
                    print(f"  ❌ 警告: 对话类型但未设置 app_id")
            else:
                print(f"  ❌ 模型配置不存在: {model_config_id}")
        else:
            print(f"  ❌ 模型配置ID未设置")
        
        if template_id:
            print(f"  ✅ 模板ID: {template_id}")
        else:
            print(f"  ⚠️  模板ID未设置")
        
        if template_prompt:
            prompt_str = str(template_prompt)
            print(f"  ✅ 提示词已设置，长度: {len(prompt_str)} 字符")
            print(f"  ✅ 提示词预览: {prompt_str[:100]}...")
        else:
            print(f"  ⚠️  提示词未设置")
        print()
    else:
        print("❌ 任务参数不存在")
        print()
    
    # 检查 Dify API 调用信息
    request_id = task.get('request_id')
    trace_id = task.get('trace_id')
    
    if request_id:
        print(f"✅ Dify API 已调用")
        print(f"   Request ID: {request_id}")
    else:
        print(f"❌ Dify API 未调用（没有 request_id）")
    
    if trace_id:
        print(f"   Trace ID: {trace_id}")
    print()
    
    # 根据错误代码提供建议
    if error_code:
        print("=" * 80)
        print("错误分析:")
        print("=" * 80)
        
        error_code_upper = error_code.upper()
        
        if "TIMEOUT" in error_code_upper or "超时" in error_message:
            print("🔍 问题: 请求超时")
            print("💡 建议:")
            print("   1. 检查网络连接")
            print("   2. 检查 Dify API 端点地址是否正确")
            print("   3. 增加超时时间配置")
        
        elif "CONNECT" in error_code_upper or "连接" in error_message:
            print("🔍 问题: 无法连接到 Dify API")
            print("💡 建议:")
            print("   1. 检查 Dify API 端点地址是否正确")
            print("   2. 检查网络连接")
            print("   3. 检查防火墙设置")
        
        elif "AUTH" in error_code_upper or "401" in error_message or "403" in error_message:
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
            print(f"🔍 问题: {error_code}")
            print("💡 建议:")
            print("   1. 查看后端日志获取详细错误信息")
            print("   2. 检查 Dify API 配置")
            print("   3. 检查网络连接")
        
        print()

def main():
    """主函数"""
    print("=" * 80)
    print("发票 Dify API 调用失败诊断工具")
    print("=" * 80)
    print(f"发票编号: {INVOICE_NO}")
    print()
    
    # 获取访问令牌
    token = get_access_token()
    if not token:
        return
    
    # 查找发票
    print("正在查找发票...")
    invoice = find_invoice_by_no(token, INVOICE_NO)
    
    if not invoice:
        print("未找到发票，请检查发票编号是否正确")
        return
    
    invoice_id = invoice.get('id')
    print(f"✅ 找到发票")
    print(f"   发票ID: {invoice_id}")
    print(f"   发票编号: {invoice.get('invoice_no', 'N/A')}")
    print(f"   识别状态: {invoice.get('recognition_status', 'N/A')}")
    print()
    
    # 获取发票详情
    invoice_detail = get_invoice_detail(token, invoice_id)
    if invoice_detail:
        print("发票详情:")
        print(f"   创建时间: {invoice_detail.get('create_time', 'N/A')}")
        if invoice_detail.get('error_code'):
            print(f"   错误代码: {invoice_detail.get('error_code')}")
        if invoice_detail.get('error_message'):
            print(f"   错误消息: {invoice_detail.get('error_message')}")
        print()
    
    # 获取识别任务
    print("正在查找识别任务...")
    tasks = get_recognition_tasks(token, invoice_id)
    
    if not tasks:
        print("❌ 未找到识别任务")
        return
    
    print(f"✅ 找到 {len(tasks)} 个识别任务")
    print()
    
    # 诊断每个任务
    for i, task in enumerate(tasks, 1):
        print(f"\n任务 {i}/{len(tasks)}:")
        diagnose_task(task, token)
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n诊断已停止")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()

