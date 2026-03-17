#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查发票 INV-20260206144930-bb24635b 的详细信息
包括：调用的模型、识别结果、字段显示逻辑
"""

import sys
import json
import os
from pathlib import Path

# 设置输出编码为UTF-8，避免Windows控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlmodel import Session, select, text, create_engine
from app.models.models_invoice import Invoice, RecognitionTask, RecognitionResult, InvoiceFile, Template, TemplateVersion
import time
import urllib.parse

# 直接使用提供的数据库信息创建连接
DB_HOST = "219.151.188.129"
DB_PORT = 50510
DB_USER = "postgres"
DB_PASSWORD = "Post.&0055"
DB_NAME = "app"

# 构建数据库连接字符串（需要对密码进行URL编码）
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
database_url = f"postgresql+psycopg://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 创建数据库引擎
from sqlalchemy import event
from sqlalchemy.exc import DisconnectionError

connect_args = {
    "connect_timeout": 30,
    "options": "-c statement_timeout=300000 -c application_name=invoice_check",
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 10,
    "keepalives_count": 5,
}

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=60,
    pool_size=5,
    max_overflow=10,
    echo=False,
    connect_args=connect_args,
)

def test_db_connection():
    """测试数据库连接"""
    print("正在测试数据库连接...")
    print(f"数据库服务器: {DB_HOST}:{DB_PORT}")
    print(f"数据库名称: {DB_NAME}")
    print(f"用户名: {DB_USER}")
    try:
        with engine.connect() as conn:
            result = conn.exec_driver_sql("SELECT 1")
            result.fetchone()
        print("[成功] 数据库连接成功")
        return True
    except Exception as e:
        print(f"[失败] 数据库连接失败: {e}")
        return False

def check_invoice(invoice_no: str):
    """检查发票详细信息"""
    print("=" * 80)
    print(f"检查发票: {invoice_no}")
    print("=" * 80)
    print()
    
    with Session(engine) as session:
        # 1. 查找票据基本信息
        invoice = session.exec(
            select(Invoice).where(Invoice.invoice_no == invoice_no)
        ).first()
        
        if not invoice:
            print(f"[错误] 未找到发票: {invoice_no}")
            return
        
        print(f"【发票基本信息】")
        print(f"  发票ID: {invoice.id}")
        print(f"  发票编号: {invoice.invoice_no}")
        print(f"  发票类型: {invoice.invoice_type}")
        print(f"  识别状态: {invoice.recognition_status}")
        print(f"  审核状态: {invoice.review_status}")
        print(f"  识别准确率: {invoice.recognition_accuracy}")
        print(f"  创建时间: {invoice.create_time}")
        print()
        
        # 2. 检查模型和模板信息（快照字段）
        print(f"【模型和模板信息（快照）】")
        model_name = getattr(invoice, 'model_name', None)
        template_name = getattr(invoice, 'template_name', None)
        template_version_str = getattr(invoice, 'template_version', None)
        template_version_id = getattr(invoice, 'template_version_id', None)
        
        print(f"  模型名称 (model_name): {model_name or '未设置'}")
        print(f"  模板名称 (template_name): {template_name or '未设置'}")
        print(f"  模板版本 (template_version): {template_version_str or '未设置'}")
        print(f"  模板版本ID (template_version_id): {template_version_id or '未设置'}")
        print()
        
        # 3. 查找识别任务（使用原始SQL避免字段不存在的问题）
        try:
            task_rows = session.execute(
                text("""
                    SELECT id, task_no, invoice_id, template_id, params, status, 
                           priority, start_time, end_time, duration, error_message, 
                           error_code, provider, request_id, trace_id, operator_id, create_time
                    FROM recognition_task
                    WHERE invoice_id = :invoice_id
                    ORDER BY create_time DESC
                """),
                {"invoice_id": str(invoice.id)}
            ).fetchall()
            
            # 将结果转换为字典列表
            tasks = []
            for row in task_rows:
                task_dict = {
                    'id': row[0],
                    'task_no': row[1],
                    'invoice_id': row[2],
                    'template_id': row[3],
                    'params': row[4],
                    'status': row[5],
                    'priority': row[6],
                    'start_time': row[7],
                    'end_time': row[8],
                    'duration': row[9],
                    'error_message': row[10],
                    'error_code': row[11],
                    'provider': row[12],
                    'request_id': row[13],
                    'trace_id': row[14],
                    'operator_id': row[15],
                    'create_time': row[16]
                }
                tasks.append(task_dict)
        except Exception as e:
            print(f"查询识别任务时出错: {e}")
            tasks = []
        
        if tasks:
            print(f"【识别任务】共找到 {len(tasks)} 个任务")
            print()
            
            latest_task = tasks[0]  # 最新的任务
            print(f"最新任务:")
            print(f"  任务ID: {latest_task['id']}")
            print(f"  任务编号: {latest_task['task_no']}")
            print(f"  状态: {latest_task['status']}")
            print(f"  创建时间: {latest_task['create_time']}")
            print(f"  开始时间: {latest_task['start_time'] or 'N/A'}")
            print(f"  结束时间: {latest_task['end_time'] or 'N/A'}")
            
            if latest_task['start_time'] and latest_task['end_time']:
                duration = (latest_task['end_time'] - latest_task['start_time']).total_seconds()
                print(f"  耗时: {duration:.2f} 秒")
            
            # 显示任务参数中的模型配置
            params = latest_task.get('params')
            if params:
                if isinstance(params, dict):
                    model_config_id = params.get('model_config_id')
                    schema_id = params.get('output_schema_id')
                else:
                    import json
                    try:
                        params_dict = json.loads(params) if isinstance(params, str) else params
                        model_config_id = params_dict.get('model_config_id')
                        schema_id = params_dict.get('output_schema_id')
                    except:
                        model_config_id = None
                        schema_id = None
                
                print(f"  模型配置ID: {model_config_id or 'N/A'}")
                print(f"  Schema ID: {schema_id or 'N/A'}")
                
                # 获取模型配置信息
                if model_config_id:
                    try:
                        from app.models.models_llm import LLMConfig
                        from uuid import UUID
                        model_config = session.get(LLMConfig, UUID(model_config_id))
                        if model_config:
                            print(f"  模型配置名称: {model_config.name}")
                            print(f"  模型配置状态: {'[启用]' if model_config.is_active else '[禁用]'}")
                            print(f"  API Endpoint: {model_config.endpoint or '[未配置]'}")
                            print(f"  模型提供商: {model_config.provider or 'N/A'}")
                            print(f"  模型名称: {model_config.model_name or 'N/A'}")
                    except Exception as e:
                        print(f"  获取模型配置失败: {str(e)}")
            
            if latest_task['status'] == "failed":
                print(f"  [错误] 错误代码: {latest_task['error_code'] or 'N/A'}")
                print(f"  [错误] 错误消息: {latest_task['error_message'] or 'N/A'}")
            print()
        
        # 4. 查找识别结果（使用原始SQL避免字段不存在的问题）
        try:
            result_rows = session.execute(
                text("""
                    SELECT id, invoice_id, task_id, total_fields, recognized_fields, 
                           accuracy, confidence, status, raw_data, raw_payload, 
                           normalized_fields, model_usage, recognition_time, create_time
                    FROM recognition_result
                    WHERE invoice_id = :invoice_id
                    ORDER BY recognition_time DESC
                    LIMIT 1
                """),
                {"invoice_id": str(invoice.id)}
            ).fetchone()
            
            if result_rows:
                result_dict = {
                    'id': result_rows[0],
                    'invoice_id': result_rows[1],
                    'task_id': result_rows[2],
                    'total_fields': result_rows[3],
                    'recognized_fields': result_rows[4],
                    'accuracy': result_rows[5],
                    'confidence': result_rows[6],
                    'status': result_rows[7],
                    'raw_data': result_rows[8],
                    'raw_payload': result_rows[9],
                    'normalized_fields': result_rows[10],
                    'model_usage': result_rows[11],
                    'recognition_time': result_rows[12],
                    'create_time': result_rows[13]
                }
                
                print(f"【识别结果】")
                print()
                print(f"最新识别结果:")
                print(f"  结果ID: {result_dict['id']}")
                print(f"  任务ID: {result_dict['task_id']}")
                print(f"  状态: {result_dict['status']}")
                print(f"  总字段数: {result_dict['total_fields']}")
                print(f"  已识别字段数: {result_dict['recognized_fields']}")
                print(f"  准确率: {result_dict['accuracy']}")
                print(f"  置信度: {result_dict['confidence']}")
                print(f"  识别时间: {result_dict['recognition_time']}")
                
                # 显示模型使用统计
                if result_dict['model_usage']:
                    print(f"  模型使用统计:")
                    if isinstance(result_dict['model_usage'], dict):
                        print(f"    {json.dumps(result_dict['model_usage'], ensure_ascii=False, indent=4)}")
                    else:
                        print(f"    {result_dict['model_usage']}")
                
                print()
                
                # 5. 检查标准化字段
                print(f"【标准化字段 (normalized_fields)】")
                normalized_fields = result_dict['normalized_fields']
                if normalized_fields:
                    if isinstance(normalized_fields, dict):
                        print(f"  字段数量: {len(normalized_fields)}")
                        print(f"  字段键列表:")
                        for key in normalized_fields.keys():
                            value = normalized_fields[key]
                            if isinstance(value, list):
                                print(f"    - {key}: [列表，共 {len(value)} 项]")
                            elif isinstance(value, dict):
                                print(f"    - {key}: {{字典，共 {len(value)} 个键}}")
                            else:
                                value_str = str(value)[:50]
                                print(f"    - {key}: {value_str}")
                        
                        # 显示部分字段值（前5个）
                        print(f"\n  字段值预览（前5个）:")
                        count = 0
                        for key, value in normalized_fields.items():
                            if count >= 5:
                                break
                            if not isinstance(value, (list, dict)):
                                print(f"    {key}: {value}")
                                count += 1
                    else:
                        print(f"  类型: {type(normalized_fields)}")
                        print(f"  值: {str(normalized_fields)[:200]}")
                else:
                    print(f"  [提示] normalized_fields 为空")
                print()
                
                # 6. 检查模板版本和字段定义（从发票表获取template_version_id）
                template_version_id = getattr(invoice, 'template_version_id', None)
                if template_version_id:
                    template_version = session.get(TemplateVersion, template_version_id)
                    if template_version:
                        print(f"【模板版本信息】")
                        print(f"  模板版本ID: {template_version.id}")
                        print(f"  版本号: {template_version.version}")
                        print(f"  模板ID: {template_version.template_id}")
                        
                        # 获取模板信息
                        template = session.get(Template, template_version.template_id)
                        if template:
                            print(f"  模板名称: {template.name}")
                            print(f"  模板类型: {template.template_type}")
                        
                        # 获取字段定义
                        if template_version.field_defs:
                            print(f"  字段定义数量: {len(template_version.field_defs)}")
                            print(f"  字段定义列表（前10个）:")
                            for i, field_def in enumerate(template_version.field_defs[:10]):
                                print(f"    {i+1}. {field_def.get('field_name', 'N/A')} ({field_def.get('field_key', 'N/A')})")
                                if field_def.get('is_required'):
                                    print(f"       [必填]")
                        print()
            else:
                print("[提示] 未找到识别结果")
                print()
        except Exception as e:
            print(f"[错误] 查询识别结果失败: {e}")
            print()
        
        # 7. 检查发票响应中的字段定义快照
        print(f"【字段定义快照 (field_defs_snapshot)】")
        field_defs_snapshot = getattr(invoice, 'field_defs_snapshot', None)
        if field_defs_snapshot:
            if isinstance(field_defs_snapshot, dict):
                print(f"  快照类型: 字典")
                print(f"  键: {list(field_defs_snapshot.keys())}")
            elif isinstance(field_defs_snapshot, list):
                print(f"  字段定义数量: {len(field_defs_snapshot)}")
                print(f"  字段定义列表（前10个）:")
                for i, field_def in enumerate(field_defs_snapshot[:10]):
                    if isinstance(field_def, dict):
                        print(f"    {i+1}. {field_def.get('field_name', 'N/A')} ({field_def.get('field_key', 'N/A')})")
                        if field_def.get('is_required'):
                            print(f"       [必填]")
            else:
                print(f"  类型: {type(field_defs_snapshot)}")
                print(f"  值: {str(field_defs_snapshot)[:200]}")
        else:
            print(f"  [提示] field_defs_snapshot 为空")
        print()
        
        # 8. 字段显示逻辑说明
        print(f"【字段显示逻辑说明】")
        print(f"  1. 在待审核页面，发票会显示以下信息：")
        print(f"     - 发票编号、供应商、金额等基本信息")
        print(f"     - 模型名称 (model_name): {model_name or '未设置'}")
        print(f"     - 模板名称 (template_name): {template_name or '未设置'}")
        print()
        print(f"  2. 在发票详情弹窗中，字段显示逻辑：")
        print(f"     - 如果有 template_version_id，会加载该版本的字段定义")
        print(f"     - 如果有 field_defs_snapshot，会使用快照中的字段定义")
        print(f"     - 字段值从 normalized_fields 中获取")
        print(f"     - 字段会按照模板定义的顺序和格式显示")
        print()
        print(f"  3. 当前发票的字段显示情况：")
        if template_version_id:
            print(f"     ✅ 有模板版本ID: {template_version_id}")
        else:
            print(f"     ⚠️  无模板版本ID")
        
        if field_defs_snapshot:
            print(f"     ✅ 有字段定义快照")
        else:
            print(f"     ⚠️  无字段定义快照")
        
        if normalized_fields:
            print(f"     ✅ 有标准化字段数据")
        else:
            print(f"     ⚠️  无标准化字段数据")
        print()
        
        print("=" * 80)
        print("检查完成")
        print("=" * 80)

if __name__ == "__main__":
    invoice_no = "INV-20260206144930-bb24635b"
    
    # 先测试数据库连接
    if not test_db_connection():
        print("\n无法连接到数据库，请检查数据库配置和网络连接")
        print("提示：请确保数据库服务正在运行，并且 .env 文件中的数据库配置正确")
        sys.exit(1)
    
    print()
    try:
        check_invoice(invoice_no)
    except Exception as e:
        print(f"检查失败: {str(e)}")
        import traceback
        traceback.print_exc()

