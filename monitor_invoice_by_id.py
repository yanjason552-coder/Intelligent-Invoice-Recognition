#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控发票识别任务状态（通过发票ID）
发票ID: a9e353a6-2bef-4918-8af2-18560eb96f5b
"""

import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from uuid import UUID

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlmodel import Session, select
from app.core.db import engine
from app.models.models_invoice import Invoice, RecognitionTask, Template

# 配置日志
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# 配置
INVOICE_ID = "a9e353a6-2bef-4918-8af2-18560eb96f5b"
CHECK_INTERVAL = 5  # 检查间隔（秒）
MAX_CHECKS = 120  # 最大检查次数（10分钟）

def find_invoice():
    """查找发票信息"""
    with Session(engine) as session:
        invoice = None
        
        # 尝试多种方式查询
        try:
            # 方式1: 使用UUID对象查询
            invoice = session.get(Invoice, UUID(INVOICE_ID))
            if invoice:
                print(f"✅ 通过UUID对象找到发票")
        except Exception as e:
            logger.warning(f"使用UUID对象查询失败: {e}")
        
        if not invoice:
            try:
                # 方式2: 使用字符串UUID查询
                invoice = session.get(Invoice, INVOICE_ID)
                if invoice:
                    print(f"✅ 通过字符串UUID找到发票")
            except Exception as e:
                logger.warning(f"使用字符串UUID查询失败: {e}")
        
        if not invoice:
            try:
                # 方式3: 使用SQL查询
                from sqlalchemy import text, inspect
                inspector = inspect(session.bind)
                columns = [col['name'] for col in inspector.get_columns('invoice')]
                
                result = session.execute(
                    text(f"SELECT {', '.join(columns)} FROM invoice WHERE id = :invoice_id"),
                    {"invoice_id": str(INVOICE_ID)}
                )
                row = result.fetchone()
                if row:
                    # 手动构建发票对象
                    class SimpleInvoice:
                        def __init__(self, row_data, col_names):
                            for col_name, val in zip(col_names, row_data):
                                setattr(self, col_name, val)
                    
                    invoice = SimpleInvoice(row, columns)
                    print(f"✅ 通过SQL查询找到发票")
            except Exception as e:
                logger.warning(f"使用SQL查询失败: {e}")
        
        if not invoice:
            print(f"❌ 未找到发票: {INVOICE_ID}")
            print(f"   请确认发票ID是否正确")
            print()
            # 尝试列出一些发票ID供参考
            try:
                from sqlalchemy import text
                result = session.execute(
                    text("SELECT id, invoice_no FROM invoice ORDER BY create_time DESC LIMIT 5")
                )
                rows = result.fetchall()
                if rows:
                    print("   最近创建的5个发票ID供参考:")
                    for row in rows:
                        print(f"     - ID: {row[0]}, 编号: {row[1] if len(row) > 1 else 'N/A'}")
            except Exception as e:
                logger.warning(f"查询发票列表失败: {e}")
            return None
        
        print(f"✅ 找到发票:")
        print(f"   发票ID: {invoice.id}")
        print(f"   发票编号: {invoice.invoice_no}")
        print(f"   识别状态: {invoice.recognition_status}")
        print(f"   创建时间: {invoice.create_time}")
        print()
        
        # 查找模板信息（如果有）
        if invoice.template_id:
            try:
                template = session.get(Template, invoice.template_id)
                if template:
                    print(f"✅ 关联模板:")
                    print(f"   模板ID: {template.id}")
                    print(f"   模板名称: {template.name}")
                    print(f"   模板类型: {template.template_type}")
                    print()
            except Exception as e:
                logger.warning(f"查询模板失败: {e}")
        
        return invoice

def get_recognition_tasks(invoice_id):
    """获取发票的所有识别任务"""
    with Session(engine) as session:
        from sqlalchemy import text
        
        try:
            # 先尝试使用模型查询
            tasks = session.exec(
                select(RecognitionTask)
                .where(RecognitionTask.invoice_id == invoice_id)
                .order_by(RecognitionTask.create_time.desc())
            ).all()
            return tasks
        except Exception as e:
            # 如果模型查询失败，需要先回滚事务
            if "does not exist" in str(e) or "UndefinedColumn" in str(e) or "InFailedSqlTransaction" in str(e):
                try:
                    session.rollback()
                except:
                    pass
                
                # 使用原始SQL查询
                logger.warning(f"模型查询失败，使用原始SQL查询: {e}")
                try:
                    result = session.execute(
                        text("""
                            SELECT id, task_no, invoice_id, template_id, params, status, 
                                   priority, start_time, end_time, duration, error_message, 
                                   error_code, provider, request_id, trace_id, operator_id, create_time
                            FROM recognition_task
                            WHERE invoice_id = :invoice_id
                            ORDER BY create_time DESC
                        """),
                        {"invoice_id": str(invoice_id)}
                    )
                    rows = result.fetchall()
                    
                    # 手动构建任务对象
                    tasks = []
                    for row in rows:
                        class SimpleTask:
                            def __init__(self, **kwargs):
                                for k, v in kwargs.items():
                                    setattr(self, k, v)
                        tasks.append(SimpleTask(
                            id=row[0],
                            task_no=row[1],
                            invoice_id=row[2],
                            template_id=row[3],
                            params=row[4],
                            status=row[5],
                            priority=row[6],
                            start_time=row[7],
                            end_time=row[8],
                            duration=row[9],
                            error_message=row[10],
                            error_code=row[11],
                            provider=row[12],
                            request_id=row[13],
                            trace_id=row[14],
                            operator_id=row[15],
                            create_time=row[16]
                        ))
                    
                    return tasks
                except Exception as sql_error:
                    try:
                        session.rollback()
                    except:
                        pass
                    raise
            else:
                try:
                    session.rollback()
                except:
                    pass
                raise

def diagnose_pending_status(task_obj, db_session, current_time):
    """诊断 pending 状态卡在哪一步"""
    steps = []
    
    # 步骤1: 检查任务是否已创建
    steps.append(("✅", "任务已创建", f"创建时间: {task_obj.create_time.strftime('%Y-%m-%d %H:%M:%S')}"))
    
    # 步骤2: 检查任务是否已启动
    if task_obj.start_time:
        steps.append(("✅", "任务已启动", f"启动时间: {task_obj.start_time.strftime('%Y-%m-%d %H:%M:%S')}"))
    else:
        wait_time = (current_time - task_obj.create_time).total_seconds()
        steps.append(("⏳", "任务未启动", f"等待时间: {wait_time:.0f}秒 ({wait_time/60:.1f}分钟)"))
        steps.append(("💡", "建议", "调用 /api/v1/invoices/recognition-tasks/{task_id}/start 启动任务"))
    
    # 步骤3: 检查任务参数
    if task_obj.params:
        params = task_obj.params
        model_config_id = params.get("model_config_id")
        template_prompt = params.get("template_prompt")
        
        if model_config_id:
            steps.append(("✅", "模型配置ID", f"已设置: {model_config_id}"))
        else:
            steps.append(("❌", "模型配置ID", "未设置"))
        
        if template_prompt:
            steps.append(("✅", "提示词(任务参数)", f"已设置，长度: {len(str(template_prompt))} 字符"))
        else:
            steps.append(("⚠️", "提示词(任务参数)", "未设置"))
    else:
        steps.append(("❌", "任务参数", "不存在"))
    
    # 步骤3.5: 检查模板配置（从数据库查询）
    template_id = None
    if task_obj.template_id:
        template_id = task_obj.template_id
    elif task_obj.params and task_obj.params.get("template_id"):
        template_id = task_obj.params.get("template_id")
    
    if template_id:
        try:
            from app.models.models_invoice import Template
            template = db_session.get(Template, UUID(template_id) if isinstance(template_id, str) else template_id)
            if template:
                # 检查模板的 prompt 字段
                template_prompt_db = getattr(template, 'prompt', None)
                if template_prompt_db:
                    steps.append(("✅", "提示词(模板对象)", f"已设置，长度: {len(str(template_prompt_db))} 字符"))
                else:
                    steps.append(("⚠️", "提示词(模板对象)", "未设置"))
                
                # 检查模板的 schema 字段（JsonSchema）
                template_schema_db = getattr(template, 'schema', None)
                if template_schema_db:
                    import json
                    schema_str = json.dumps(template_schema_db, ensure_ascii=False) if isinstance(template_schema_db, dict) else str(template_schema_db)
                    steps.append(("✅", "JsonSchema(模板对象)", f"已设置，长度: {len(schema_str)} 字符"))
                else:
                    steps.append(("⚠️", "JsonSchema(模板对象)", "未设置（这是问题所在！）"))
                    steps.append(("💡", "建议", f"请检查模板 '{template.name}' 的 schema 字段是否已设置"))
            else:
                steps.append(("❌", "模板对象", f"不存在，ID: {template_id}"))
        except Exception as e:
            steps.append(("⚠️", "检查模板", f"失败: {str(e)[:100]}"))
    else:
        steps.append(("⚠️", "模板ID", "未设置"))
    
    # 步骤4: 检查 Dify API 调用
    if task_obj.request_id:
        steps.append(("✅", "Dify API调用", f"已发起，request_id: {task_obj.request_id}"))
    elif task_obj.start_time:
        steps.append(("⏳", "Dify API调用", "已启动但未获取到 request_id"))
    else:
        steps.append(("⏸️", "Dify API调用", "未启动"))
    
    # 步骤5: 检查错误信息
    if task_obj.error_code:
        steps.append(("❌", "错误代码", task_obj.error_code))
    if task_obj.error_message:
        steps.append(("❌", "错误消息", task_obj.error_message[:200]))
    
    return steps

def monitor_task(task_id):
    """监控识别任务状态"""
    print("=" * 80)
    print(f"开始监控识别任务")
    print(f"任务ID: {task_id}")
    print(f"检查间隔: {CHECK_INTERVAL} 秒")
    print(f"最大检查次数: {MAX_CHECKS} 次")
    print("=" * 80)
    print()
    
    check_count = 0
    last_status = None
    start_time = None
    
    while check_count < MAX_CHECKS:
        check_count += 1
        
        with Session(engine) as session:
            from sqlalchemy import text
            
            try:
                task = session.get(RecognitionTask, task_id)
            except Exception as e:
                # 如果模型查询失败，需要先回滚事务
                if "does not exist" in str(e) or "UndefinedColumn" in str(e) or "InFailedSqlTransaction" in str(e):
                    try:
                        session.rollback()
                    except:
                        pass
                    
                    # 使用原始SQL查询
                    try:
                        result = session.execute(
                            text("""
                                SELECT id, task_no, invoice_id, template_id, params, status, 
                                       priority, start_time, end_time, duration, error_message, 
                                       error_code, provider, request_id, trace_id, operator_id, create_time
                                FROM recognition_task
                                WHERE id = :task_id
                            """),
                            {"task_id": str(task_id)}
                        )
                        row = result.fetchone()
                        
                        if row:
                            class SimpleTask:
                                def __init__(self, **kwargs):
                                    for k, v in kwargs.items():
                                        setattr(self, k, v)
                            task = SimpleTask(
                                id=row[0],
                                task_no=row[1],
                                invoice_id=row[2],
                                template_id=row[3],
                                params=row[4],
                                status=row[5],
                                priority=row[6],
                                start_time=row[7],
                                end_time=row[8],
                                duration=row[9],
                                error_message=row[10],
                                error_code=row[11],
                                provider=row[12],
                                request_id=row[13],
                                trace_id=row[14],
                                operator_id=row[15],
                                create_time=row[16]
                            )
                        else:
                            task = None
                    except Exception as sql_error:
                        try:
                            session.rollback()
                        except:
                            pass
                        raise
                else:
                    try:
                        session.rollback()
                    except:
                        pass
                    raise
            
            if not task:
                print(f"❌ 任务不存在: {task_id}")
                break
            
            current_time = datetime.now()
            status = task.status
            
            # 计算持续时间
            duration = None
            pending_duration = None
            if task.start_time:
                duration = (current_time - task.start_time).total_seconds()
                if start_time is None:
                    start_time = task.start_time
            else:
                pending_duration = (current_time - task.create_time).total_seconds()
            
            # 状态变化时显示详细信息
            if status != last_status or check_count == 1:
                print(f"\n[{current_time.strftime('%H:%M:%S')}] {'='*60}")
                print(f"[{current_time.strftime('%H:%M:%S')}] 状态变化: {last_status or 'N/A'} -> {status}")
                print(f"[{current_time.strftime('%H:%M:%S')}] 任务编号: {task.task_no}")
                
                # 如果是 pending 状态，显示详细的步骤诊断
                if status == "pending":
                    print(f"\n[{current_time.strftime('%H:%M:%S')}] 📋 任务流程诊断:")
                    diagnosis = diagnose_pending_status(task, session, current_time)
                    for icon, step_name, step_info in diagnosis:
                        print(f"[{current_time.strftime('%H:%M:%S')}]   {icon} {step_name}: {step_info}")
                
                # 检查模板配置
                if task.params:
                    template_id = task.params.get("template_id")
                    template_prompt = task.params.get("template_prompt")
                    
                    if template_id:
                        print(f"[{current_time.strftime('%H:%M:%S')}] 模板ID: {template_id}")
                    
                    if template_prompt:
                        print(f"[{current_time.strftime('%H:%M:%S')}] ✅ 提示词已包含在任务参数中，长度: {len(str(template_prompt))} 字符")
                        print(f"[{current_time.strftime('%H:%M:%S')}] 提示词预览: {str(template_prompt)[:100]}...")
                    else:
                        print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️  提示词未包含在任务参数中")
                
                if task.start_time:
                    print(f"[{current_time.strftime('%H:%M:%S')}] 开始时间: {task.start_time}")
                if task.end_time:
                    print(f"[{current_time.strftime('%H:%M:%S')}] 结束时间: {task.end_time}")
                if duration:
                    print(f"[{current_time.strftime('%H:%M:%S')}] 持续时间: {duration:.1f}秒 ({duration/60:.1f}分钟)")
                elif pending_duration:
                    print(f"[{current_time.strftime('%H:%M:%S')}] ⏳ 等待启动时间: {pending_duration:.0f}秒 ({pending_duration/60:.1f}分钟)")
                
                # 显示 Dify API 调用信息
                if task.request_id:
                    print(f"[{current_time.strftime('%H:%M:%S')}] ✅ Dify API 已调用，request_id: {task.request_id}")
                if task.trace_id:
                    print(f"[{current_time.strftime('%H:%M:%S')}] ✅ Dify API trace_id: {task.trace_id}")
                
                if task.error_code:
                    print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️  错误代码: {task.error_code}")
                if task.error_message:
                    print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️  错误消息: {task.error_message}")
                
                print(f"[{current_time.strftime('%H:%M:%S')}] {'='*60}")
                last_status = status
            
            # 显示当前状态
            status_line = f"[{current_time.strftime('%H:%M:%S')}] 状态: {status}"
            if duration:
                status_line += f" | 持续时间: {duration:.1f}秒"
            elif pending_duration:
                status_line += f" | 等待启动: {pending_duration:.0f}秒 ({pending_duration/60:.1f}分钟)"
            if task.error_code:
                status_line += f" | 错误: {task.error_code}"
            if task.request_id:
                status_line += f" | request_id: {task.request_id[:8]}..."
            
            # pending 状态时，每5次检查显示一次诊断
            if status == "pending" and check_count % 5 == 0:
                print("\n")
                print(f"[{current_time.strftime('%H:%M:%S')}] 📋 任务流程诊断 (每5次检查显示):")
                diagnosis = diagnose_pending_status(task, session, current_time)
                for icon, step_name, step_info in diagnosis:
                    print(f"[{current_time.strftime('%H:%M:%S')}]   {icon} {step_name}: {step_info}")
                print(status_line, end='\r')
            else:
                print(status_line, end='\r')
            
            # 如果任务完成或失败，停止监控
            if status in ["completed", "failed"]:
                print("\n")
                print("=" * 80)
                print(f"任务已结束，状态: {status}")
                if task.end_time and task.start_time:
                    total_duration = (task.end_time - task.start_time).total_seconds()
                    print(f"总耗时: {total_duration:.1f}秒 ({total_duration/60:.1f}分钟)")
                if task.request_id:
                    print(f"Dify API request_id: {task.request_id}")
                if task.trace_id:
                    print(f"Dify API trace_id: {task.trace_id}")
                if task.error_message:
                    print(f"错误信息: {task.error_message}")
                print("=" * 80)
                break
        
        time.sleep(CHECK_INTERVAL)
    
    if check_count >= MAX_CHECKS:
        print("\n")
        print("⚠️  达到最大检查次数，停止监控")

def main():
    """主函数"""
    print("=" * 80)
    print("发票识别任务监控（通过发票ID）")
    print("=" * 80)
    print(f"发票ID: {INVOICE_ID}")
    print()
    
    # 查找发票
    invoice = find_invoice()
    
    if not invoice:
        return
    
    # 获取识别任务
    tasks = get_recognition_tasks(invoice.id)
    
    if not tasks:
        print("ℹ️  当前没有识别任务")
        print("   等待识别任务创建...")
        print()
        
        # 等待任务创建
        check_count = 0
        while check_count < 60:  # 最多等待5分钟
            check_count += 1
            tasks = get_recognition_tasks(invoice.id)
            if tasks:
                break
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 等待识别任务创建... ({check_count}/60)", end='\r')
            time.sleep(5)
        
        if not tasks:
            print("\n❌ 等待超时，未找到识别任务")
            return
        
        print("\n✅ 找到识别任务")
    
    # 显示所有任务
    print(f"\n找到 {len(tasks)} 个识别任务:")
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. 任务编号: {task.task_no}")
        print(f"     任务ID: {task.id}")
        print(f"     状态: {task.status}")
        print(f"     创建时间: {task.create_time}")
        if task.start_time:
            print(f"     开始时间: {task.start_time}")
        if task.end_time:
            print(f"     结束时间: {task.end_time}")
        if task.request_id:
            print(f"     Dify request_id: {task.request_id}")
        if task.trace_id:
            print(f"     Dify trace_id: {task.trace_id}")
        print()
    
    # 监控最新的任务
    latest_task = tasks[0]
    print(f"监控最新任务: {latest_task.task_no}")
    print()
    
    monitor_task(latest_task.id)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n监控已停止")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

