#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过API监控发票识别任务状态（不需要直接连接数据库）
发票ID: a9e353a6-2bef-4918-8af2-18560eb96f5b
"""

import sys
import time
import requests
import json
import os
from datetime import datetime
from pathlib import Path

# 配置
INVOICE_ID = "a9e353a6-2bef-4918-8af2-18560eb96f5b"
BASE_URL = "http://localhost:8000"
CHECK_INTERVAL = 5  # 检查间隔（秒）
MAX_CHECKS = 120  # 最大检查次数（10分钟）

def get_access_token():
    """获取访问令牌"""
    print("=" * 80)
    print("发票识别任务监控（通过API）")
    print("=" * 80)
    print(f"发票ID: {INVOICE_ID}")
    print()
    
    # 方式1: 从命令行参数获取
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print(f"从命令行参数获取 access_token")
    
    # 方式2: 从环境变量获取
    if not token:
        token = os.getenv("ACCESS_TOKEN")
        if token:
            print(f"从环境变量获取 access_token")
    
    # 方式3: 交互式输入
    if not token:
        print("需要访问令牌 (access_token)")
        print("请从浏览器开发者工具中获取:")
        print("  1. 打开浏览器开发者工具 (F12)")
        print("  2. 进入 Application/存储 -> Local Storage")
        print("  3. 找到 access_token 的值")
        print()
        print("或者:")
        print("  - 通过命令行参数: python monitor_invoice_by_api.py <your_token>")
        print("  - 通过环境变量: set ACCESS_TOKEN=<your_token>")
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

def get_invoice_info(token):
    """获取发票信息"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/invoices/{INVOICE_ID}",
            headers=headers
        )
        
        if response.status_code == 200:
            invoice = response.json()
            print("找到发票:")
            print(f"  发票ID: {invoice.get('id')}")
            print(f"  发票编号: {invoice.get('invoice_no', 'N/A')}")
            print(f"  识别状态: {invoice.get('recognition_status', 'N/A')}")
            print(f"  创建时间: {invoice.get('create_time', 'N/A')}")
            print()
            return invoice
        else:
            print(f"获取发票信息失败: HTTP {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"获取发票信息失败: {e}")
        return None

def get_recognition_tasks(token):
    """获取识别任务列表"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 获取所有任务，然后过滤出该发票的任务
        response = requests.get(
            f"{BASE_URL}/api/v1/invoices/recognition-tasks",
            headers=headers,
            params={"limit": 100}
        )
        
        if response.status_code == 200:
            data = response.json()
            tasks = data.get("data", [])
            # 过滤出该发票的任务
            invoice_tasks = [t for t in tasks if t.get("invoice_id") == INVOICE_ID]
            return invoice_tasks
        else:
            print(f"获取任务列表失败: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"获取任务列表失败: {e}")
        return []

def diagnose_pending_status(task, current_time):
    """诊断 pending 状态卡在哪一步"""
    steps = []
    
    # 步骤1: 检查任务是否已创建
    create_time = task.get("create_time")
    if create_time:
        steps.append(("OK", "任务已创建", f"创建时间: {create_time}"))
    
    # 步骤2: 检查任务是否已启动
    start_time = task.get("start_time")
    if start_time:
        steps.append(("OK", "任务已启动", f"启动时间: {start_time}"))
    else:
        if create_time:
            try:
                create_dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                wait_time = (current_time - create_dt.replace(tzinfo=None)).total_seconds()
                steps.append(("WAIT", "任务未启动", f"等待时间: {wait_time:.0f}秒 ({wait_time/60:.1f}分钟)"))
            except:
                steps.append(("WAIT", "任务未启动", "等待启动"))
        steps.append(("TIP", "建议", "调用 /api/v1/invoices/recognition-tasks/{task_id}/start 启动任务"))
    
    # 步骤3: 检查任务参数
    params = task.get("params", {})
    if params:
        model_config_id = params.get("model_config_id")
        template_prompt = params.get("template_prompt")
        
        if model_config_id:
            steps.append(("OK", "模型配置ID", f"已设置: {model_config_id}"))
        else:
            steps.append(("ERROR", "模型配置ID", "未设置"))
        
        if template_prompt:
            steps.append(("OK", "提示词(任务参数)", f"已设置，长度: {len(str(template_prompt))} 字符"))
        else:
            steps.append(("WARN", "提示词(任务参数)", "未设置"))
    else:
        steps.append(("ERROR", "任务参数", "不存在"))
    
    # 步骤4: 检查 Dify API 调用
    request_id = task.get("request_id")
    if request_id:
        steps.append(("OK", "Dify API调用", f"已发起，request_id: {request_id}"))
    elif start_time:
        steps.append(("WAIT", "Dify API调用", "已启动但未获取到 request_id"))
    else:
        steps.append(("PAUSE", "Dify API调用", "未启动"))
    
    # 步骤5: 检查错误信息
    error_code = task.get("error_code")
    error_message = task.get("error_message")
    if error_code:
        steps.append(("ERROR", "错误代码", error_code))
    if error_message:
        steps.append(("ERROR", "错误消息", error_message[:200]))
    
    return steps

def monitor_task(token, task_id):
    """监控识别任务状态"""
    print("=" * 80)
    print(f"开始监控识别任务")
    print(f"任务ID: {task_id}")
    print(f"检查间隔: {CHECK_INTERVAL} 秒")
    print(f"最大检查次数: {MAX_CHECKS} 次")
    print("=" * 80)
    print()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    check_count = 0
    last_status = None
    
    while check_count < MAX_CHECKS:
        check_count += 1
        
        try:
            # 获取任务列表
            response = requests.get(
                f"{BASE_URL}/api/v1/invoices/recognition-tasks",
                headers=headers,
                params={"limit": 100}
            )
            
            if response.status_code != 200:
                print(f"[ERROR] 查询失败: HTTP {response.status_code}")
                time.sleep(CHECK_INTERVAL)
                continue
            
            data = response.json()
            tasks = data.get("data", [])
            task = next((t for t in tasks if t.get("id") == task_id), None)
            
            if not task:
                print(f"[ERROR] 无法找到任务: {task_id}")
                break
            
            current_time = datetime.now()
            status = task.get("status")
            
            # 计算持续时间
            duration = None
            pending_duration = None
            start_time = task.get("start_time")
            create_time = task.get("create_time")
            
            if start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    duration = (current_time - start_dt.replace(tzinfo=None)).total_seconds()
                except:
                    pass
            elif create_time:
                try:
                    create_dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                    pending_duration = (current_time - create_dt.replace(tzinfo=None)).total_seconds()
                except:
                    pass
            
            # 状态变化时显示详细信息
            if status != last_status or check_count == 1:
                print(f"\n[{current_time.strftime('%H:%M:%S')}] {'='*60}")
                print(f"[{current_time.strftime('%H:%M:%S')}] 状态变化: {last_status or 'N/A'} -> {status}")
                print(f"[{current_time.strftime('%H:%M:%S')}] 任务编号: {task.get('task_no', 'N/A')}")
                
                # 如果是 pending 状态，显示详细的步骤诊断
                if status == "pending":
                    print(f"\n[{current_time.strftime('%H:%M:%S')}] 任务流程诊断:")
                    diagnosis = diagnose_pending_status(task, current_time)
                    icon_map = {
                        "OK": "OK",
                        "WAIT": "WAIT",
                        "WARN": "WARN",
                        "ERROR": "ERROR",
                        "TIP": "TIP",
                        "PAUSE": "PAUSE"
                    }
                    for icon, step_name, step_info in diagnosis:
                        print(f"[{current_time.strftime('%H:%M:%S')}]   [{icon_map.get(icon, '?')}] {step_name}: {step_info}")
                
                # 检查模板配置
                params = task.get("params", {})
                if params:
                    template_id = params.get("template_id")
                    template_prompt = params.get("template_prompt")
                    
                    if template_id:
                        print(f"[{current_time.strftime('%H:%M:%S')}] 模板ID: {template_id}")
                    
                    if template_prompt:
                        prompt_str = str(template_prompt)
                        print(f"[{current_time.strftime('%H:%M:%S')}] OK 提示词已包含在任务参数中，长度: {len(prompt_str)} 字符")
                        print(f"[{current_time.strftime('%H:%M:%S')}] 提示词预览: {prompt_str[:100]}...")
                    else:
                        print(f"[{current_time.strftime('%H:%M:%S')}] WARN 提示词未包含在任务参数中")
                
                if start_time:
                    print(f"[{current_time.strftime('%H:%M:%S')}] 开始时间: {start_time}")
                if task.get("end_time"):
                    print(f"[{current_time.strftime('%H:%M:%S')}] 结束时间: {task.get('end_time')}")
                if duration:
                    print(f"[{current_time.strftime('%H:%M:%S')}] 持续时间: {duration:.1f}秒 ({duration/60:.1f}分钟)")
                elif pending_duration:
                    print(f"[{current_time.strftime('%H:%M:%S')}] WAIT 等待启动时间: {pending_duration:.0f}秒 ({pending_duration/60:.1f}分钟)")
                
                # 显示 Dify API 调用信息
                request_id = task.get("request_id")
                trace_id = task.get("trace_id")
                if request_id:
                    print(f"[{current_time.strftime('%H:%M:%S')}] OK Dify API 已调用，request_id: {request_id}")
                if trace_id:
                    print(f"[{current_time.strftime('%H:%M:%S')}] OK Dify API trace_id: {trace_id}")
                
                error_code = task.get("error_code")
                error_message = task.get("error_message")
                if error_code:
                    print(f"[{current_time.strftime('%H:%M:%S')}] ERROR 错误代码: {error_code}")
                if error_message:
                    print(f"[{current_time.strftime('%H:%M:%S')}] ERROR 错误消息: {error_message}")
                
                print(f"[{current_time.strftime('%H:%M:%S')}] {'='*60}")
                last_status = status
            
            # 显示当前状态
            status_line = f"[{current_time.strftime('%H:%M:%S')}] 状态: {status}"
            if duration:
                status_line += f" | 持续时间: {duration:.1f}秒"
            elif pending_duration:
                status_line += f" | 等待启动: {pending_duration:.0f}秒 ({pending_duration/60:.1f}分钟)"
            if error_code:
                status_line += f" | 错误: {error_code}"
            if request_id:
                status_line += f" | request_id: {request_id[:8]}..."
            
            # pending 状态时，每5次检查显示一次诊断
            if status == "pending" and check_count % 5 == 0:
                print("\n")
                print(f"[{current_time.strftime('%H:%M:%S')}] 任务流程诊断 (每5次检查显示):")
                diagnosis = diagnose_pending_status(task, current_time)
                for icon, step_name, step_info in diagnosis:
                    icon_display = {"OK": "OK", "WAIT": "WAIT", "WARN": "WARN", "ERROR": "ERROR", "TIP": "TIP", "PAUSE": "PAUSE"}.get(icon, "?")
                    print(f"[{current_time.strftime('%H:%M:%S')}]   [{icon_display}] {step_name}: {step_info}")
                print(status_line, end='\r')
            else:
                print(status_line, end='\r')
            
            # 如果任务完成或失败，停止监控
            if status in ["completed", "failed"]:
                print("\n")
                print("=" * 80)
                print(f"任务已结束，状态: {status}")
                if task.get("end_time") and start_time:
                    try:
                        end_dt = datetime.fromisoformat(task.get("end_time").replace('Z', '+00:00'))
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        total_duration = (end_dt.replace(tzinfo=None) - start_dt.replace(tzinfo=None)).total_seconds()
                        print(f"总耗时: {total_duration:.1f}秒 ({total_duration/60:.1f}分钟)")
                    except:
                        pass
                if request_id:
                    print(f"Dify API request_id: {request_id}")
                if trace_id:
                    print(f"Dify API trace_id: {trace_id}")
                if error_message:
                    print(f"错误信息: {error_message}")
                print("=" * 80)
                break
        
        except Exception as e:
            print(f"\n[ERROR] 查询任务失败: {e}")
            time.sleep(CHECK_INTERVAL)
            continue
        
        time.sleep(CHECK_INTERVAL)
    
    if check_count >= MAX_CHECKS:
        print("\n")
        print("达到最大检查次数，停止监控")

def main():
    """主函数"""
    # 获取访问令牌
    token = get_access_token()
    if not token:
        return
    
    # 获取发票信息
    invoice = get_invoice_info(token)
    if not invoice:
        return
    
    # 获取识别任务
    tasks = get_recognition_tasks(token)
    
    if not tasks:
        print("当前没有识别任务")
        print("等待识别任务创建...")
        print()
        
        # 等待任务创建
        check_count = 0
        while check_count < 60:  # 最多等待5分钟
            check_count += 1
            tasks = get_recognition_tasks(token)
            if tasks:
                break
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 等待识别任务创建... ({check_count}/60)", end='\r')
            time.sleep(5)
        
        if not tasks:
            print("\n等待超时，未找到识别任务")
            return
        
        print("\n找到识别任务")
    
    # 显示所有任务
    print(f"\n找到 {len(tasks)} 个识别任务:")
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. 任务编号: {task.get('task_no', 'N/A')}")
        print(f"     任务ID: {task.get('id')}")
        print(f"     状态: {task.get('status', 'N/A')}")
        print(f"     创建时间: {task.get('create_time', 'N/A')}")
        if task.get('start_time'):
            print(f"     开始时间: {task.get('start_time')}")
        if task.get('end_time'):
            print(f"     结束时间: {task.get('end_time')}")
        if task.get('request_id'):
            print(f"     Dify request_id: {task.get('request_id')}")
        if task.get('trace_id'):
            print(f"     Dify trace_id: {task.get('trace_id')}")
        print()
    
    # 监控最新的任务
    latest_task = tasks[0]
    print(f"监控最新任务: {latest_task.get('task_no', 'N/A')}")
    print()
    
    monitor_task(token, latest_task.get('id'))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n监控已停止")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()

