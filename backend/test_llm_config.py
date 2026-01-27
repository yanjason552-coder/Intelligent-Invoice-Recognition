#!/usr/bin/env python3
"""
测试大模型配置
"""

import sys
import os
import requests
import json

# 设置API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_llm_config():
    """测试大模型配置"""

    print("=== 测试大模型配置 ===")

    # 首先获取当前配置
    try:
        response = requests.get(f"{BASE_URL}/config/llm")
        if response.status_code == 200:
            config = response.json()
            print("[OK] 获取配置成功")
            print(f"配置名称: {config.get('name', 'N/A')}")
            print(f"端点: {config.get('endpoint', 'N/A')}")
            print(f"应用类型: {config.get('app_type', 'N/A')}")
            print(f"是否启用: {config.get('is_active', False)}")

            # 如果有配置，测试连接
            if config.get('endpoint') and config.get('api_key'):
                print("\n=== 测试API连接 ===")
                test_data = {
                    "endpoint": config['endpoint'],
                    "api_key": config['api_key'],
                    "app_id": config.get('app_id'),
                    "workflow_id": config.get('workflow_id'),
                    "app_type": config.get('app_type', 'workflow')
                }

                test_response = requests.post(f"{BASE_URL}/config/llm/test", json=test_data)
                if test_response.status_code == 200:
                    result = test_response.json()
                    if result.get('success'):
                        print("[OK] API连接测试成功!")
                        print(f"消息: {result.get('message')}")
                    else:
                        print("[FAIL] API连接测试失败!")
                        print(f"消息: {result.get('message')}")
                else:
                    print(f"[FAIL] 测试请求失败: {test_response.status_code}")
                    print(test_response.text)
            else:
                print("[WARN] 缺少必要的配置信息 (endpoint 或 api_key)")
        else:
            print(f"[FAIL] 获取配置失败: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("[FAIL] 无法连接到后端服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"[FAIL] 测试出错: {str(e)}")

if __name__ == "__main__":
    test_llm_config()
