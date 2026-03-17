"""
列出所有发票并选择监控
"""
import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def login(username="admin@example.com", password="ChangeMe123!"):
    """登录获取token"""
    login_url = f"{BASE_URL}/login/access-token"
    response = requests.post(
        login_url,
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    raise Exception(f"登录失败: {response.status_code}")

def list_invoices(token):
    """列出所有发票"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/invoices/query", headers=headers, params={"limit": 100})
    
    if response.status_code != 200:
        print(f"[ERROR] 查询失败: {response.status_code}")
        return []
    
    data = response.json()
    invoices = data.get("data", [])
    
    print(f"\n找到 {len(invoices)} 个发票:\n")
    for i, invoice in enumerate(invoices, 1):
        files = invoice.get("files", [])
        file_names = [f.get("filename", "N/A") for f in files]
        print(f"{i}. 发票ID: {invoice.get('id')}")
        print(f"   文件: {', '.join(file_names[:3])}")
        if len(file_names) > 3:
            print(f"   ... 还有 {len(file_names) - 3} 个文件")
        print()
    
    return invoices

def find_invoice_by_keyword(token, keyword):
    """根据关键词查找发票"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/invoices/query", headers=headers, params={"limit": 100})
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    invoices = data.get("data", [])
    
    for invoice in invoices:
        files = invoice.get("files", [])
        for file in files:
            if keyword.lower() in file.get("filename", "").lower():
                return invoice, file
    
    return None

def get_tasks_for_invoice(token, invoice_id):
    """获取发票的所有任务"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/invoices/recognition-tasks", headers=headers, params={"limit": 100})
    
    if response.status_code != 200:
        return []
    
    data = response.json()
    all_tasks = data.get("data", [])
    return [t for t in all_tasks if t.get("invoice_id") == invoice_id]

def monitor_task(token, task_id, check_interval=5, max_checks=120):
    """监控任务"""
    headers = {"Authorization": f"Bearer {token}"}
    check_count = 0
    last_status = None
    
    print(f"\n开始监控任务 {task_id}")
    print("=" * 60)
    
    while check_count < max_checks:
        check_count += 1
        
        response = requests.get(f"{BASE_URL}/invoices/recognition-tasks", headers=headers, params={"limit": 100})
        if response.status_code != 200:
            print(f"[ERROR] 查询失败")
            break
        
        data = response.json()
        tasks = data.get("data", [])
        task = next((t for t in tasks if t.get("id") == task_id), None)
        
        if not task:
            print("[ERROR] 无法找到任务")
            break
        
        status = task.get("status")
        now = datetime.now().strftime("%H:%M:%S")
        
        if status != last_status:
            print(f"\n[{now}] 状态: {status}")
            print(f"  任务编号: {task.get('task_no')}")
            print(f"  模型: {task.get('model_name', 'N/A')}")
            print(f"  模板ID: {task.get('template_id', 'N/A')}")
            print(f"  包含提示词: {'✓' if task.get('params', {}).get('template_prompt') else '✗'}")
            
            model_name = (task.get('model_name') or '').lower()
            if 'v3' in model_name or 'jsonschema' in model_name:
                print("  ⭐ 使用正确的模型")
            else:
                print("  ⚠ 模型可能不正确")
            
            if task.get('start_time'):
                print(f"  开始时间: {task.get('start_time')}")
            if task.get('end_time'):
                print(f"  结束时间: {task.get('end_time')}")
            
            last_status = status
        
        if status == 'processing':
            elapsed = ""
            if task.get('start_time'):
                try:
                    start = datetime.fromisoformat(task.get('start_time').replace('Z', '+00:00'))
                    elapsed = f" (已处理 {(datetime.now(start.tzinfo) - start).total_seconds():.0f}秒)"
                except:
                    pass
            print(f"[{now}] 处理中{elapsed}...", end='\r')
        
        if status in ['completed', 'failed']:
            print(f"\n\n任务{'完成' if status == 'completed' else '失败'}")
            if status == 'completed':
                # 获取结果
                result_response = requests.get(
                    f"{BASE_URL}/invoices/recognition-results",
                    headers=headers,
                    params={"task_id": task_id}
                )
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    results = result_data.get("data", [])
                    if results:
                        result = results[0]
                        print(f"\n识别结果:")
                        print(f"  准确率: {result.get('accuracy', 0):.2%}" if result.get('accuracy') else "  准确率: N/A")
                        print(f"  置信度: {result.get('confidence', 0):.2%}" if result.get('confidence') else "  置信度: N/A")
                        print(f"  字段数: {result.get('recognized_fields', 0)}/{result.get('total_fields', 0)}")
            break
        
        time.sleep(check_interval)
    
    if check_count >= max_checks:
        print("\n[WARNING] 达到最大检查次数")

if __name__ == "__main__":
    print("=" * 60)
    print("发票识别任务监控工具")
    print("=" * 60)
    
    token = login()
    
    # 查找发票
    keyword = "China SY inv 1"
    result = find_invoice_by_keyword(token, keyword)
    
    if not result:
        print(f"\n未找到包含 '{keyword}' 的发票")
        print("\n所有发票列表:")
        invoices = list_invoices(token)
        if invoices:
            print("\n请手动输入发票ID进行监控")
        exit(0)
    
    invoice, file = result
    print(f"\n找到发票:")
    print(f"  发票ID: {invoice.get('id')}")
    print(f"  文件名: {file.get('filename')}")
    
    # 获取任务
    tasks = get_tasks_for_invoice(token, invoice.get('id'))
    
    if not tasks:
        print("\n该发票还没有识别任务")
        print("请在前端创建识别任务后重新运行此脚本")
    else:
        print(f"\n找到 {len(tasks)} 个任务:")
        for i, task in enumerate(tasks, 1):
            print(f"{i}. {task.get('task_no')} - {task.get('status')}")
        
        # 监控最新的任务
        latest_task = tasks[0]
        monitor_task(token, latest_task.get('id'))

