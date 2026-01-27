#!/usr/bin/env python3
"""
检查 llm_config 配置和文件 external_file_id 的脚本
"""

import sys
import os
from sqlmodel import select

# 添加backend路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.db import SessionLocal
    from app.models.models_invoice import LLMConfig, InvoiceFile, Invoice, RecognitionTask
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在backend目录中运行此脚本")
    sys.exit(1)

def check_llm_config():
    """检查 llm_config 表配置"""
    print("=" * 80)
    print("=== 检查 llm_config 表配置 ===")
    print("=" * 80)
    
    with SessionLocal() as session:
        # 查询所有配置
        configs = session.exec(select(LLMConfig)).all()
        
        if not configs:
            print("❌ llm_config 表中没有配置")
            return False
        
        print(f"\n找到 {len(configs)} 个配置:\n")
        
        all_valid = True
        for idx, config in enumerate(configs, 1):
            print(f"--- 配置 {idx}: {config.name} (ID: {config.id}) ---")
            
            # 检查必需字段
            issues = []
            
            # 1. 检查 name（必需）
            if not config.name or not config.name.strip():
                issues.append("❌ name: 配置名称不能为空")
            else:
                print(f"✅ name: {config.name}")
            
            # 2. 检查 endpoint（必需）
            if not config.endpoint or not config.endpoint.strip():
                issues.append("❌ endpoint: API端点地址不能为空")
            else:
                endpoint = config.endpoint.strip()
                if not endpoint.startswith(("http://", "https://")):
                    issues.append(f"⚠️  endpoint: 格式可能不正确（应以 http:// 或 https:// 开头）: {endpoint}")
                else:
                    print(f"✅ endpoint: {endpoint}")
            
            # 3. 检查 api_key（必需）
            if not config.api_key or not config.api_key.strip():
                issues.append("❌ api_key: API密钥不能为空")
            else:
                masked_key = config.api_key[:10] + "*" * (len(config.api_key) - 10) if len(config.api_key) > 10 else "*" * len(config.api_key)
                print(f"✅ api_key: {masked_key} (已隐藏)")
            
            # 4. 检查 is_active
            if not config.is_active:
                issues.append("⚠️  is_active: 配置未启用")
            else:
                print(f"✅ is_active: {config.is_active}")
            
            # 5. 检查 app_type（可选，但有默认值）
            print(f"ℹ️  app_type: {config.app_type}")
            
            # 6. 检查 workflow_id（如果 app_type 是 workflow，建议配置）
            if config.app_type == "workflow":
                if not config.workflow_id:
                    issues.append("⚠️  workflow_id: app_type 为 workflow 时，建议配置 workflow_id")
                else:
                    print(f"✅ workflow_id: {config.workflow_id}")
            
            # 7. 检查 app_id（如果 app_type 是 chat，建议配置）
            if config.app_type == "chat":
                if not config.app_id:
                    issues.append("⚠️  app_id: app_type 为 chat 时，建议配置 app_id")
                else:
                    print(f"✅ app_id: {config.app_id}")
            
            # 8. 检查超时配置
            print(f"ℹ️  timeout: {config.timeout} 秒")
            print(f"ℹ️  max_retries: {config.max_retries}")
            
            # 9. 检查 creator_id
            if not config.creator_id:
                issues.append("⚠️  creator_id: 创建人ID为空")
            else:
                print(f"✅ creator_id: {config.creator_id}")
            
            # 显示问题
            if issues:
                print("\n⚠️  发现以下问题:")
                for issue in issues:
                    print(f"  {issue}")
                all_valid = False
            else:
                print("\n✅ 配置检查通过")
            
            print()
        
        return all_valid

def check_external_file_id():
    """检查文件的 external_file_id"""
    print("=" * 80)
    print("=== 检查文件的 external_file_id ===")
    print("=" * 80)
    
    with SessionLocal() as session:
        # 查询所有文件
        files = session.exec(select(InvoiceFile)).all()
        
        if not files:
            print("❌ invoice_file 表中没有文件")
            return
        
        print(f"\n找到 {len(files)} 个文件:\n")
        
        files_without_external_id = []
        files_with_external_id = []
        
        for idx, file in enumerate(files, 1):
            print(f"--- 文件 {idx}: {file.file_name} (ID: {file.id}) ---")
            print(f"  文件路径: {file.file_path}")
            print(f"  文件类型: {file.file_type}")
            print(f"  文件大小: {file.file_size} 字节")
            
            if file.external_file_id:
                print(f"  ✅ external_file_id: {file.external_file_id}")
                files_with_external_id.append(file)
            else:
                print(f"  ❌ external_file_id: 未设置")
                files_without_external_id.append(file)
            
            # 检查文件是否存在
            if file.file_path:
                import os
                if os.path.exists(file.file_path):
                    print(f"  ✅ 本地文件存在")
                else:
                    print(f"  ❌ 本地文件不存在: {file.file_path}")
            
            print()
        
        # 统计信息
        print("=" * 80)
        print("=== 统计信息 ===")
        print(f"总文件数: {len(files)}")
        print(f"有 external_file_id: {len(files_with_external_id)}")
        print(f"无 external_file_id: {len(files_with_external_id)}")
        
        if files_without_external_id:
            print("\n⚠️  以下文件缺少 external_file_id:")
            for file in files_without_external_id:
                print(f"  - {file.file_name} (ID: {file.id})")
            print("\n提示: 这些文件在识别时会自动上传到外部API并获取 external_file_id")

def check_processing_tasks():
    """检查卡在 processing 状态的任务"""
    print("=" * 80)
    print("=== 检查 processing 状态的任务 ===")
    print("=" * 80)
    
    with SessionLocal() as session:
        # 查询 processing 状态的任务
        processing_tasks = session.exec(
            select(RecognitionTask).where(RecognitionTask.status == "processing")
        ).all()
        
        if not processing_tasks:
            print("✅ 没有卡在 processing 状态的任务")
            return
        
        print(f"\n⚠️  找到 {len(processing_tasks)} 个 processing 状态的任务:\n")
        
        for idx, task in enumerate(processing_tasks, 1):
            print(f"--- 任务 {idx}: {task.task_no} (ID: {task.id}) ---")
            print(f"  状态: {task.status}")
            print(f"  开始时间: {task.start_time}")
            print(f"  创建时间: {task.create_time}")
            
            if task.error_code:
                print(f"  错误代码: {task.error_code}")
            if task.error_message:
                print(f"  错误消息: {task.error_message}")
            
            # 获取关联的票据和文件
            invoice = session.get(Invoice, task.invoice_id)
            if invoice:
                print(f"  票据ID: {invoice.id}")
                print(f"  票据编号: {invoice.invoice_no}")
                print(f"  票据识别状态: {invoice.recognition_status}")
                
                file = session.get(InvoiceFile, invoice.file_id)
                if file:
                    print(f"  文件ID: {file.id}")
                    print(f"  文件名: {file.file_name}")
                    print(f"  external_file_id: {file.external_file_id or '未设置'}")
            
            # 获取模型配置ID
            if task.params and task.params.get("model_config_id"):
                model_config_id = task.params.get("model_config_id")
                model_config = session.get(LLMConfig, model_config_id)
                if model_config:
                    print(f"  模型配置: {model_config.name} (ID: {model_config.id})")
                    print(f"  模型配置启用状态: {model_config.is_active}")
                else:
                    print(f"  ⚠️  模型配置不存在: {model_config_id}")
            
            print()

def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("配置和文件检查工具")
    print("=" * 80 + "\n")
    
    # 1. 检查 llm_config 配置
    config_valid = check_llm_config()
    
    print("\n")
    
    # 2. 检查 external_file_id
    check_external_file_id()
    
    print("\n")
    
    # 3. 检查 processing 状态的任务
    check_processing_tasks()
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)
    
    if not config_valid:
        print("\n⚠️  发现配置问题，请修复后再进行识别任务")

if __name__ == "__main__":
    main()

