"""
监控发票识别任务
用于监控指定发票文件的识别进度和结果
"""
import requests
import time
import json
from datetime import datetime
from typing import Optional

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

class InvoiceTaskMonitor:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def login(self, username: str, password: str) -> str:
        """登录获取token"""
        login_url = f"{BASE_URL}/login/access-token"
        login_data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(
            login_url,
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.token = token_data.get("access_token")
            self.headers["Authorization"] = f"Bearer {self.token}"
            print(f"[OK] 登录成功")
            return self.token
        else:
            raise Exception(f"登录失败: {response.status_code} - {response.text}")
    
    def find_invoice_by_filename(self, filename: str) -> Optional[dict]:
        """根据文件名查找发票"""
        print(f"\n正在查找发票文件: {filename}...")
        
        # 查询发票列表
        response = requests.get(
            f"{BASE_URL}/invoices/query",
            headers=self.headers,
            params={"limit": 100}
        )
        
        if response.status_code != 200:
            print(f"[ERROR] 查询发票列表失败: {response.status_code}")
            return None
        
        data = response.json()
        invoices = data.get("data", [])
        
        # 查找匹配的文件名
        print(f"正在搜索文件，当前共有 {len(invoices)} 个发票...")
        matching_files = []
        
        for invoice in invoices:
            files = invoice.get("files", [])
            for file in files:
                file_name = file.get("filename", "")
                if filename.lower() in file_name.lower():
                    matching_files.append({
                        "invoice": invoice,
                        "file": file
                    })
        
        if matching_files:
            if len(matching_files) == 1:
                result = matching_files[0]
                print(f"[OK] 找到发票:")
                print(f"  发票ID: {result['invoice'].get('id')}")
                print(f"  文件名: {result['file'].get('filename')}")
                print(f"  文件ID: {result['file'].get('id')}")
                return result
            else:
                print(f"[INFO] 找到 {len(matching_files)} 个匹配的发票:")
                for i, match in enumerate(matching_files, 1):
                    print(f"  {i}. {match['file'].get('filename')} (发票ID: {match['invoice'].get('id')})")
                # 返回第一个匹配的
                return matching_files[0]
        
        # 如果没找到，显示所有文件名帮助调试
        print(f"[WARNING] 未找到文件名为 '{filename}' 的发票")
        print(f"\n最近的发票文件列表（前10个）:")
        file_count = 0
        for invoice in invoices[:10]:
            files = invoice.get("files", [])
            for file in files:
                if file_count < 10:
                    print(f"  - {file.get('filename', 'N/A')}")
                    file_count += 1
        
        return None
    
    def get_invoice_tasks(self, invoice_id: str) -> list:
        """获取发票的所有识别任务"""
        print(f"\n正在查询发票 {invoice_id} 的识别任务...")
        
        response = requests.get(
            f"{BASE_URL}/invoices/recognition-tasks",
            headers=self.headers,
            params={"limit": 100}
        )
        
        if response.status_code != 200:
            print(f"[ERROR] 查询任务列表失败: {response.status_code}")
            return []
        
        data = response.json()
        tasks = data.get("data", [])
        
        # 过滤出该发票的任务
        invoice_tasks = [t for t in tasks if t.get("invoice_id") == invoice_id]
        
        print(f"[OK] 找到 {len(invoice_tasks)} 个任务")
        return invoice_tasks
    
    def get_task_details(self, task_id: str) -> Optional[dict]:
        """获取任务详情"""
        # 从任务列表中查找
        response = requests.get(
            f"{BASE_URL}/invoices/recognition-tasks",
            headers=self.headers,
            params={"limit": 100}
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        tasks = data.get("data", [])
        
        for task in tasks:
            if task.get("id") == task_id:
                return task
        
        return None
    
    def monitor_task(self, task_id: str, check_interval: int = 5, max_checks: int = 60):
        """监控任务执行状态"""
        print(f"\n开始监控任务: {task_id}")
        print(f"检查间隔: {check_interval} 秒")
        print(f"最大检查次数: {max_checks}")
        print("=" * 60)
        
        check_count = 0
        last_status = None
        
        while check_count < max_checks:
            check_count += 1
            task = self.get_task_details(task_id)
            
            if not task:
                print(f"[ERROR] 无法获取任务详情")
                break
            
            status = task.get("status")
            task_no = task.get("task_no")
            model_name = task.get("model_name", "N/A")
            template_id = task.get("template_id")
            has_prompt = bool(task.get("params", {}).get("template_prompt"))
            
            # 状态变化时打印详细信息
            if status != last_status:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 任务状态变化:")
                print(f"  任务编号: {task_no}")
                print(f"  状态: {status}")
                print(f"  使用的模型: {model_name}")
                print(f"  模板ID: {template_id or 'N/A'}")
                print(f"  包含提示词: {'✓ 是' if has_prompt else '✗ 否'}")
                
                if task.get("start_time"):
                    print(f"  开始时间: {task.get('start_time')}")
                if task.get("end_time"):
                    print(f"  结束时间: {task.get('end_time')}")
                
                # 检查模型是否正确
                if "v3" in model_name.lower() or "jsonschema" in model_name.lower():
                    print(f"  ⭐ 使用正确的模型: {model_name}")
                else:
                    print(f"  ⚠ 使用的模型可能不正确: {model_name}")
                
                last_status = status
            
            # 任务完成或失败
            if status in ["completed", "failed"]:
                print(f"\n任务已{('完成' if status == 'completed' else '失败')}")
                
                if status == "completed":
                    # 获取识别结果
                    self.get_recognition_result(task_id)
                elif status == "failed":
                    print(f"  错误信息: {task.get('params', {}).get('error_message', 'N/A')}")
                
                break
            
            # 显示进度（如果是处理中）
            if status == "processing":
                elapsed = ""
                if task.get("start_time"):
                    try:
                        from datetime import datetime as dt
                        start = dt.fromisoformat(task.get("start_time").replace('Z', '+00:00'))
                        elapsed_seconds = (datetime.now(start.tzinfo) - start).total_seconds()
                        elapsed = f" (已处理 {elapsed_seconds:.0f} 秒)"
                    except:
                        pass
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] 处理中{elapsed}...", end='\r')
            
            time.sleep(check_interval)
        
        if check_count >= max_checks:
            print(f"\n[WARNING] 达到最大检查次数，停止监控")
    
    def get_recognition_result(self, task_id: str):
        """获取识别结果"""
        print(f"\n正在获取识别结果...")
        
        response = requests.get(
            f"{BASE_URL}/invoices/recognition-results",
            headers=self.headers,
            params={"task_id": task_id, "limit": 10}
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("data", [])
            
            if results:
                result = results[0]
                print(f"[OK] 识别结果:")
                print(f"  状态: {result.get('status')}")
                print(f"  准确率: {result.get('accuracy', 0):.2%}" if result.get('accuracy') else "  准确率: N/A")
                print(f"  置信度: {result.get('confidence', 0):.2%}" if result.get('confidence') else "  置信度: N/A")
                print(f"  识别字段数: {result.get('recognized_fields', 0)}/{result.get('total_fields', 0)}")
                
                # 获取字段详情
                result_id = result.get("id")
                if result_id:
                    self.get_result_fields(result_id)
            else:
                print("[WARNING] 未找到识别结果")
        else:
            print(f"[ERROR] 获取识别结果失败: {response.status_code}")
    
    def get_result_fields(self, result_id: str):
        """获取识别字段详情"""
        response = requests.get(
            f"{BASE_URL}/invoices/recognition-results/{result_id}/fields",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            fields = data.get("data", [])
            
            if fields:
                print(f"\n识别字段详情 (共 {len(fields)} 个字段):")
                print("-" * 60)
                for field in fields[:20]:  # 只显示前20个字段
                    field_name = field.get("field_name", "N/A")
                    field_value = field.get("field_value", "")
                    confidence = field.get("confidence", 0)
                    status = field.get("status", "N/A")
                    
                    # 截断过长的值
                    if field_value and len(str(field_value)) > 50:
                        field_value = str(field_value)[:50] + "..."
                    
                    print(f"  {field_name}: {field_value}")
                    print(f"    置信度: {confidence:.2%}, 状态: {status}")
                
                if len(fields) > 20:
                    print(f"  ... 还有 {len(fields) - 20} 个字段")
        else:
            print(f"[WARNING] 获取字段详情失败: {response.status_code}")


def main():
    """主函数"""
    print("=" * 60)
    print("发票识别任务监控工具")
    print("=" * 60)
    
    # 初始化监控器
    monitor = InvoiceTaskMonitor("")
    
    # 登录
    try:
        monitor.login("admin@example.com", "ChangeMe123!")
    except Exception as e:
        print(f"[ERROR] 登录失败: {e}")
        return
    
    # 查找发票
    filename = "China SY inv 1.PDF"
    invoice_info = monitor.find_invoice_by_filename(filename)
    
    if not invoice_info:
        print("\n[ERROR] 未找到发票，请检查文件名是否正确")
        return
    
    invoice_id = invoice_info["invoice"]["id"]
    
    # 获取任务列表
    tasks = monitor.get_invoice_tasks(invoice_id)
    
    if not tasks:
        print("\n[INFO] 该发票还没有识别任务")
        print("请在前端创建识别任务，然后重新运行此脚本")
        return
    
    # 显示所有任务
    print(f"\n找到 {len(tasks)} 个任务:")
    for i, task in enumerate(tasks, 1):
        print(f"\n任务 {i}:")
        print(f"  任务ID: {task.get('id')}")
        print(f"  任务编号: {task.get('task_no')}")
        print(f"  状态: {task.get('status')}")
        print(f"  模型: {task.get('model_name', 'N/A')}")
        print(f"  创建时间: {task.get('create_time')}")
    
    # 选择最新的任务进行监控
    latest_task = tasks[0]  # 假设第一个是最新的
    task_id = latest_task.get("id")
    
    print(f"\n选择任务进行监控: {latest_task.get('task_no')}")
    
    # 开始监控
    monitor.monitor_task(task_id, check_interval=5, max_checks=120)  # 最多监控10分钟
    
    print("\n" + "=" * 60)
    print("监控结束")
    print("=" * 60)


if __name__ == "__main__":
    main()

