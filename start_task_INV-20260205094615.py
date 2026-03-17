#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动发票识别任务
发票编号: INV-20260205094615-6984b5c4
"""

import sys
import requests
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlmodel import Session, select
from app.core.db import engine
from app.models.models_invoice import Invoice, RecognitionTask

# 配置
INVOICE_NO = "INV-20260205094615-6984b5c4"
BASE_URL = "http://localhost:8000"

def get_task_id():
    """获取任务ID"""
    with Session(engine) as session:
        # 查找发票
        invoice = session.exec(
            select(Invoice).where(Invoice.invoice_no == INVOICE_NO)
        ).first()
        
        if not invoice:
            print(f"❌ 未找到发票: {INVOICE_NO}")
            return None
        
        # 查找最新的 pending 任务
        from sqlalchemy import text
        try:
            result = session.execute(
                text("""
                    SELECT id, task_no, status, create_time
                    FROM recognition_task
                    WHERE invoice_id = :invoice_id
                    ORDER BY create_time DESC
                    LIMIT 1
                """),
                {"invoice_id": str(invoice.id)}
            )
            row = result.fetchone()
            
            if row:
                task_id = row[0]
                task_no = row[1]
                status = row[2]
                create_time = row[3]
                
                print(f"✅ 找到任务:")
                print(f"   任务ID: {task_id}")
                print(f"   任务编号: {task_no}")
                print(f"   状态: {status}")
                print(f"   创建时间: {create_time}")
                print()
                
                return str(task_id)
            else:
                print("❌ 未找到识别任务")
                return None
        except Exception as e:
            print(f"❌ 查询任务失败: {e}")
            return None

def start_task(task_id: str):
    """启动任务"""
    # 首先需要登录获取 token
    print("=" * 80)
    print("启动识别任务")
    print("=" * 80)
    print()
    print("⚠️  注意：需要先登录获取 access_token")
    print("请提供 access_token（从浏览器开发者工具中获取）")
    print()
    
    token = input("请输入 access_token（或按 Enter 跳过，使用环境变量）: ").strip()
    
    if not token:
        import os
        token = os.getenv("ACCESS_TOKEN")
        if not token:
            print("❌ 未提供 access_token")
            return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{BASE_URL}/api/v1/invoices/recognition-tasks/{task_id}/start"
    
    print(f"📡 发送请求到: {url}")
    print()
    
    try:
        response = requests.post(url, headers=headers)
        
        print(f"HTTP 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 任务启动成功!")
            print(f"   消息: {result.get('message', 'N/A')}")
            return True
        else:
            print(f"❌ 任务启动失败")
            print(f"   错误: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("启动发票识别任务")
    print("=" * 80)
    print(f"发票编号: {INVOICE_NO}")
    print()
    
    # 获取任务ID
    task_id = get_task_id()
    
    if not task_id:
        return
    
    # 启动任务
    if start_task(task_id):
        print()
        print("=" * 80)
        print("✅ 任务已启动，请运行监控脚本查看进度:")
        print(f"   python monitor_invoice_INV-20260205094615.py")
        print("=" * 80)
    else:
        print()
        print("=" * 80)
        print("❌ 任务启动失败")
        print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

