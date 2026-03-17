"""
调试任务创建问题
检查后端日志中是否有相关的调试信息
"""
import requests
import json

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

def check_task_details(token, task_no):
    """检查任务详情"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/invoices/recognition-tasks",
        headers=headers,
        params={"limit": 100}
    )
    
    if response.status_code != 200:
        print(f"[ERROR] 查询失败: {response.status_code}")
        return None
    
    data = response.json()
    tasks = data.get("data", [])
    task = next((t for t in tasks if t.get("task_no") == task_no), None)
    
    if not task:
        print(f"[ERROR] 未找到任务: {task_no}")
        return None
    
    print(f"\n=== 任务详情: {task_no} ===")
    print(f"状态: {task.get('status')}")
    print(f"模板ID (任务字段): {task.get('template_id')}")
    print(f"模板ID (params中): {task.get('params', {}).get('template_id')}")
    print(f"模板策略: {task.get('params', {}).get('template_strategy')}")
    print(f"提示词: {'存在' if task.get('params', {}).get('template_prompt') else '不存在'}")
    
    # 检查 params 的完整内容
    print(f"\n完整 params:")
    print(json.dumps(task.get('params', {}), indent=2, ensure_ascii=False))
    
    return task

if __name__ == "__main__":
    print("=" * 60)
    print("调试任务创建问题")
    print("=" * 60)
    
    token = login()
    
    # 检查最新的任务
    task_no = "TASK-20260128112243-574821f6"
    task = check_task_details(token, task_no)
    
    if task:
        print("\n=== 问题分析 ===")
        params = task.get('params', {})
        
        if params.get('template_strategy') != 'fixed':
            print(f"❌ 模板策略不是 'fixed'，而是: {params.get('template_strategy')}")
            print("   这会导致 template_id 不会被设置")
        elif not params.get('template_id'):
            print(f"❌ params 中没有 template_id")
        else:
            print(f"✓ 模板策略是 'fixed'，params 中有 template_id")
            print(f"  但是任务的 template_id 字段是 null")
            print(f"  可能的原因：")
            print(f"  1. 后端代码没有正确执行（检查后端日志）")
            print(f"  2. UUID 类型转换失败")
            print(f"  3. 数据库保存时出错")
        
        print("\n=== 建议 ===")
        print("1. 检查后端日志，查找以下关键词：")
        print("   - '模板策略'")
        print("   - '设置 template_id'")
        print("   - '创建任务，template_id'")
        print("   - '任务创建完成，task.template_id'")
        print("2. 如果日志中没有这些信息，说明代码没有执行到")
        print("3. 如果日志中有这些信息但 template_id 仍然是 null，可能是数据库保存问题")

