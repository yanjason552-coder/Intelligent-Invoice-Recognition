#!/usr/bin/env python3
"""
测试 Dify API 连接性的脚本
"""

import logging
import httpx
import json
import sys
import os
from typing import Dict, Any
from sqlmodel import select

# 添加backend路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.db import SessionLocal
    from app.models.models_invoice import LLMConfig
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在backend目录中运行此脚本")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_dify_api():
    """测试 Dify API 连接"""

    try:
        # 获取第一个活跃的模型配置
        with SessionLocal() as session:
            model_config = session.exec(
                select(LLMConfig).where(LLMConfig.is_active == True)
            ).first()

            if not model_config:
                print("❌ 未找到活跃的模型配置")
                return

            print("=== 模型配置信息 ===")
            print(f"配置名称: {model_config.name}")
            print(f"端点: {model_config.endpoint}")
            print(f"应用ID: {model_config.app_id}")
            print(f"工作流ID: {model_config.workflow_id}")
            print(f"API Key: {'*' * 20 if model_config.api_key else '未设置'}")

            # 获取API配置
            endpoint = model_config.endpoint
            api_key = model_config.api_key

        if not endpoint:
            print("❌ API endpoint 未配置")
            return

        if not api_key:
            print("❌ API key 未配置")
            return

        # 构建测试请求
        url = f"{endpoint.rstrip('/')}/workflows/run"

        payload = {
            "inputs": {
                "test_message": "Hello, this is a test message"
            },
            "response_mode": "blocking",
            "user": "test_user"
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        print("\n=== 发送测试请求 ===")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)

                print("\n=== 响应信息 ===")
                print(f"HTTP状态码: {response.status_code}")
                print(f"响应时间: 30秒超时")
                print(f"响应头: {dict(response.headers)}")

                if response.status_code == 200:
                    print("✅ API 连接成功!")
                    try:
                        result = response.json()
                        print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    except:
                        print(f"响应内容: {response.text[:500]}")
                else:
                    print("❌ API 请求失败")
                    try:
                        error_result = response.json()
                        print(f"错误详情: {json.dumps(error_result, ensure_ascii=False, indent=2)}")
                    except:
                        print(f"错误详情: {response.text[:500]}")

        except httpx.TimeoutException:
            print("❌ 请求超时")
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP 错误: {e.response.status_code}")
            print(f"错误详情: {e.response.text[:500]}")
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"❌ 数据库连接错误: {str(e)}")
        print("请确保数据库服务正在运行")

if __name__ == "__main__":
    test_dify_api()
