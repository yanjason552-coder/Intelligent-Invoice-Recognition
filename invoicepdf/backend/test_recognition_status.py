"""
测试识别情况检查API
"""
import requests
import json
import sys
import io

# 设置标准输出编码为UTF-8（Windows兼容）
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except AttributeError:
        pass

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_recognition_status():
    """测试识别情况检查API"""
    
    # 1. 先登录获取token（需要替换为实际的用户名和密码）
    print("=" * 60)
    print("测试识别情况检查API")
    print("=" * 60)
    print()
    
    # 登录获取token
    login_url = f"{BASE_URL}/login/access-token"
    login_data = {
        "username": "admin@example.com",
        "password": "ChangeMe123!"
    }
    
    print("步骤1: 登录获取token...")
    try:
        response = requests.post(
            login_url,
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("[OK] 登录成功，获取到token")
            print()
        else:
            print(f"[ERROR] 登录失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            print()
            print("提示：请修改脚本中的用户名和密码")
            return
    except Exception as e:
        print(f"[ERROR] 登录请求失败: {str(e)}")
        print()
        print("提示：请确保后端服务正在运行")
        return
    
    # 2. 使用token访问识别情况API
    print("步骤2: 获取识别情况...")
    status_url = f"{BASE_URL}/statistics/recognition-status"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(status_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("[OK] 获取识别情况成功")
            print()
            print("=" * 60)
            print("识别情况报告")
            print("=" * 60)
            print()
            
            # 格式化输出
            task_status = data.get("task_status", {})
            print("【识别任务状态】")
            print(f"  待处理: {task_status.get('pending', 0)}")
            print(f"  处理中: {task_status.get('processing', 0)}")
            print(f"  已完成: {task_status.get('completed', 0)}")
            print(f"  失败: {task_status.get('failed', 0)}")
            print(f"  总计: {task_status.get('total', 0)}")
            print()
            
            stuck_tasks = data.get("stuck_tasks", [])
            if stuck_tasks:
                print(f"【长时间处理中的任务】({len(stuck_tasks)}个)")
                for task in stuck_tasks[:5]:
                    print(f"  - {task.get('task_no')}: 已处理 {task.get('duration_minutes', 0):.1f} 分钟")
                print()
            else:
                print("【长时间处理中的任务】")
                print("  [OK] 没有长时间处理中的任务")
                print()
            
            failed_tasks = data.get("failed_tasks", [])
            if failed_tasks:
                print(f"【最近失败的任务】({len(failed_tasks)}个)")
                for task in failed_tasks[:5]:
                    print(f"  - {task.get('task_no')}: {task.get('error_code', 'N/A')}")
                    if task.get('error_message'):
                        print(f"    错误: {task.get('error_message')[:50]}...")
                print()
            else:
                print("【最近失败的任务】")
                print("  [OK] 没有失败的任务")
                print()
            
            result_status = data.get("result_status", {})
            print("【识别结果统计】")
            print(f"  结果总数: {result_status.get('total', 0)}")
            print(f"  成功: {result_status.get('success', 0)}")
            print(f"  失败: {result_status.get('failed', 0)}")
            print(f"  部分成功: {result_status.get('partial', 0)}")
            if result_status.get('avg_accuracy'):
                print(f"  平均准确率: {result_status.get('avg_accuracy'):.2%}")
            if result_status.get('avg_confidence'):
                print(f"  平均置信度: {result_status.get('avg_confidence'):.2%}")
            print()
            
            prompt_usage = data.get("prompt_usage", {})
            print("【模板提示词使用情况】")
            print(f"  使用提示词的任务数: {prompt_usage.get('tasks_with_prompt', 0)}")
            print(f"  总任务数: {prompt_usage.get('total_tasks', 0)}")
            if prompt_usage.get('usage_rate'):
                print(f"  使用率: {prompt_usage.get('usage_rate'):.2%}")
            print()
            
            model_usage = data.get("model_usage", {})
            if model_usage:
                print("【模型配置使用情况】")
                for model_name, stats in model_usage.items():
                    print(f"  {model_name}:")
                    print(f"    总任务数: {stats.get('total', 0)}")
                    print(f"    已完成: {stats.get('completed', 0)}")
                    print(f"    失败: {stats.get('failed', 0)}")
                    if stats.get('total', 0) > 0:
                        success_rate = stats.get('completed', 0) / stats.get('total', 0) * 100
                        print(f"    成功率: {success_rate:.1f}%")
                print()
            
            print("=" * 60)
            print("完整JSON数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"[ERROR] 获取识别情况失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
    except Exception as e:
        print(f"[ERROR] 请求失败: {str(e)}")

if __name__ == "__main__":
    test_recognition_status()

