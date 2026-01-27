#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的发票识别测试脚本 - 直接连接数据库，不依赖应用配置
用于追踪识别流程的每一步，定位卡住的具体位置
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("[错误] 需要安装 psycopg2: pip install psycopg2-binary")
    sys.exit(1)

# 数据库连接信息
DB_HOST = "219.151.188.129"
DB_PORT = "50510"
DB_USER = "postgres"
DB_PASSWORD = "Post.&0055"
# 尝试多个数据库
DB_NAMES = ["app", "ruoyi_db"]  # 按优先级顺序尝试
DB_NAME = None  # 将在运行时确定

# 日志文件
LOG_FILE = Path(__file__).parent / "recognition_test_log.txt"

def log_step(step_num, step_name, status, details=None, error=None):
    """记录测试步骤"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    log_entry = {
        "timestamp": timestamp,
        "step": step_num,
        "step_name": step_name,
        "status": status,
        "details": details or {},
        "error": str(error) if error else None
    }
    
    # 输出到控制台
    status_symbol = {
        "start": "▶",
        "success": "✓",
        "failed": "✗",
        "info": "ℹ"
    }.get(status, "?")
    
    print(f"\n[{timestamp}] {status_symbol} 步骤 {step_num}: {step_name}")
    if details:
        for key, value in details.items():
            if key != "traceback":  # traceback 单独处理
                print(f"    {key}: {value}")
    if error:
        print(f"    [错误] {error}")
    
    # 写入日志文件
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"    [警告] 写入日志文件失败: {e}")

def get_db_connection(db_name=None):
    """获取数据库连接"""
    db_names_to_try = [db_name] if db_name else DB_NAMES
    
    for db in db_names_to_try:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=db
            )
            return conn, db
        except Exception as e:
            continue
    
    print(f"[错误] 无法连接到任何数据库")
    return None, None

def test_invoice_recognition(file_name="China SY inv 1.PDF"):
    """测试发票识别流程"""
    
    # 清空日志文件
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    
    print("=" * 80)
    print("发票识别详细测试 (独立版)")
    print("=" * 80)
    print(f"测试文件: {file_name}")
    print(f"数据库: {', '.join(DB_NAMES)} @ {DB_HOST}:{DB_PORT}")
    print(f"日志文件: {LOG_FILE}")
    print("=" * 80)
    
    step = 0
    conn = None
    
    try:
        # 步骤1: 连接数据库
        step += 1
        log_step(step, "连接数据库", "start", {
            "host": DB_HOST,
            "port": DB_PORT,
            "databases_to_try": DB_NAMES
        })
        
        conn, actual_db_name = get_db_connection()
        if not conn:
            log_step(step, "连接数据库", "failed")
            return
        
        log_step(step, "连接数据库", "success", {
            "connected_database": actual_db_name
        })
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 步骤2: 检查表是否存在
        step += 1
        log_step(step, "检查数据库表", "start")
        
        tables_to_check = ['invoice_file', 'invoice', 'recognition_task', 'llm_config']
        existing_tables = []
        missing_tables = []
        
        for table_name in tables_to_check:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                ) as exists;
            """, (table_name,))
            result = cur.fetchone()
            exists = result['exists'] if isinstance(result, dict) else result[0]
            
            if exists:
                existing_tables.append(table_name)
            else:
                missing_tables.append(table_name)
        
        if missing_tables:
            log_step(step, "检查数据库表", "failed", {
                "missing_tables": missing_tables,
                "existing_tables": existing_tables
            })
            print(f"\n[错误] 缺少以下表: {', '.join(missing_tables)}")
            print("可能的原因:")
            print("  1. 数据库迁移未执行")
            print("  2. 使用了错误的数据库")
            print("  3. 表在不同的 schema 中")
            return
        
        log_step(step, "检查数据库表", "success", {
            "all_tables_exist": True
        })
        
        # 步骤3: 查找文件记录
        step += 1
        log_step(step, "查找文件记录", "start", {"file_name": file_name})
        
        cur.execute("""
            SELECT id, file_name, file_path, file_type, file_size, 
                   external_file_id, status, upload_time
            FROM invoice_file
            WHERE file_name = %s
            ORDER BY upload_time DESC
            LIMIT 1;
        """, (file_name,))
        
        file_record = cur.fetchone()
        
        if not file_record:
            log_step(step, "查找文件记录", "failed", {
                "error": f"未找到文件: {file_name}"
            })
            print("\n[错误] 未找到文件记录")
            print("请先上传文件")
            
            # 列出所有文件
            cur.execute("SELECT file_name FROM invoice_file ORDER BY upload_time DESC LIMIT 10;")
            files = cur.fetchall()
            if files:
                print("\n最近上传的文件:")
                for f in files:
                    print(f"  - {f['file_name']}")
            return
        
        log_step(step, "查找文件记录", "success", {
            "file_id": str(file_record['id']),
            "file_name": file_record['file_name'],
            "file_path": file_record['file_path'],
            "file_type": file_record['file_type'],
            "file_size": file_record['file_size'],
            "external_file_id": file_record['external_file_id'] or "未设置",
            "status": file_record['status']
        })
        
        # 步骤4: 检查本地文件是否存在
        step += 1
        log_step(step, "检查本地文件", "start", {"file_path": file_record['file_path']})
        
        file_path = Path(file_record['file_path'])
        if not file_path.exists():
            # 尝试相对路径
            backend_dir = Path(__file__).parent
            file_path = backend_dir / file_record['file_path']
        
        if not file_path.exists():
            log_step(step, "检查本地文件", "failed", {
                "error": f"文件不存在: {file_record['file_path']}",
                "tried_path": str(file_path.absolute())
            })
            print(f"\n[错误] 本地文件不存在: {file_record['file_path']}")
            return
        
        file_size = file_path.stat().st_size
        log_step(step, "检查本地文件", "success", {
            "file_exists": True,
            "file_size": file_size,
            "absolute_path": str(file_path.absolute())
        })
        
        # 步骤5: 查找关联的发票记录
        step += 1
        log_step(step, "查找发票记录", "start", {"file_id": str(file_record['id'])})
        
        cur.execute("""
            SELECT id, invoice_no, recognition_status, review_status, create_time
            FROM invoice
            WHERE file_id = %s
            ORDER BY create_time DESC
            LIMIT 1;
        """, (file_record['id'],))
        
        invoice_record = cur.fetchone()
        
        if not invoice_record:
            log_step(step, "查找发票记录", "failed", {
                "error": "未找到关联的发票记录"
            })
            print("\n[错误] 未找到关联的发票记录")
            return
        
        log_step(step, "查找发票记录", "success", {
            "invoice_id": str(invoice_record['id']),
            "invoice_no": invoice_record['invoice_no'],
            "recognition_status": invoice_record['recognition_status'],
            "review_status": invoice_record['review_status']
        })
        
        # 步骤6: 查找识别任务
        step += 1
        log_step(step, "查找识别任务", "start", {"invoice_id": str(invoice_record['id'])})
        
        cur.execute("""
            SELECT id, task_no, status, start_time, end_time, 
                   error_code, error_message, create_time, params
            FROM recognition_task
            WHERE invoice_id = %s
            ORDER BY create_time DESC
            LIMIT 1;
        """, (invoice_record['id'],))
        
        task_record = cur.fetchone()
        
        if not task_record:
            log_step(step, "查找识别任务", "failed", {
                "error": "未找到识别任务"
            })
            print("\n[错误] 未找到识别任务")
            print("请先创建识别任务")
            
            # 检查是否有其他任务
            cur.execute("""
                SELECT COUNT(*) as count
                FROM recognition_task
                WHERE invoice_id = %s;
            """, (invoice_record['id'],))
            task_count = cur.fetchone()['count']
            
            if task_count == 0:
                print("\n提示:")
                print("1. 在前端界面选择此发票")
                print("2. 点击'创建识别任务'或'批量创建任务'")
                print("3. 选择模型配置和识别方式")
                print("4. 创建任务后，点击'启动识别'")
            else:
                print(f"\n找到 {task_count} 个任务，但查询失败")
            
            return
        
        log_step(step, "查找识别任务", "success", {
            "task_id": str(task_record['id']),
            "task_no": task_record['task_no'],
            "status": task_record['status'],
            "create_time": str(task_record['create_time']),
            "start_time": str(task_record['start_time']) if task_record['start_time'] else None,
            "end_time": str(task_record['end_time']) if task_record['end_time'] else None,
            "error_code": task_record['error_code'],
            "error_message": task_record['error_message']
        })
        
        # 步骤7: 检查任务参数
        step += 1
        log_step(step, "检查任务参数", "start")
        
        if not task_record['params']:
            log_step(step, "检查任务参数", "failed", {
                "error": "任务参数为空"
            })
            return
        
        params = task_record['params']
        model_config_id = params.get("model_config_id")
        
        if not model_config_id:
            log_step(step, "检查任务参数", "failed", {
                "error": "缺少 model_config_id"
            })
            return
        
        log_step(step, "检查任务参数", "success", {
            "model_config_id": str(model_config_id),
            "recognition_mode": params.get("recognition_mode"),
            "output_schema_id": params.get("output_schema_id"),
            "template_strategy": params.get("template_strategy")
        })
        
        # 步骤8: 查找模型配置
        step += 1
        log_step(step, "查找模型配置", "start", {"model_config_id": str(model_config_id)})
        
        cur.execute("""
            SELECT id, name, endpoint, api_key, app_type, workflow_id, 
                   app_id, is_active, timeout, max_retries
            FROM llm_config
            WHERE id = %s;
        """, (model_config_id,))
        
        model_config_record = cur.fetchone()
        
        if not model_config_record:
            log_step(step, "查找模型配置", "failed", {
                "error": f"模型配置不存在: {model_config_id}"
            })
            return
        
        if not model_config_record['is_active']:
            log_step(step, "查找模型配置", "failed", {
                "error": "模型配置未启用"
            })
            return
        
        log_step(step, "查找模型配置", "success", {
            "config_id": str(model_config_record['id']),
            "config_name": model_config_record['name'],
            "endpoint": model_config_record['endpoint'],
            "api_key_length": len(model_config_record['api_key']) if model_config_record['api_key'] else 0,
            "app_type": model_config_record['app_type'],
            "workflow_id": model_config_record['workflow_id'],
            "is_active": model_config_record['is_active']
        })
        
        # 步骤9: 检查 API 配置
        step += 1
        log_step(step, "检查API配置", "start")
        
        endpoint = model_config_record['endpoint']
        api_key = model_config_record['api_key']
        
        if not endpoint:
            log_step(step, "检查API配置", "failed", {
                "error": "API endpoint未配置"
            })
            return
        
        if not api_key:
            log_step(step, "检查API配置", "failed", {
                "error": "API key未配置"
            })
            return
        
        if not endpoint.startswith(("http://", "https://")):
            log_step(step, "检查API配置", "failed", {
                "error": f"endpoint格式不正确: {endpoint}"
            })
            return
        
        log_step(step, "检查API配置", "success", {
            "endpoint": endpoint,
            "api_key_length": len(api_key)
        })
        
        # 步骤10: 检查 external_file_id
        step += 1
        log_step(step, "检查external_file_id", "start")
        
        if not file_record['external_file_id']:
            log_step(step, "检查external_file_id", "info", {
                "message": "文件缺少external_file_id，将在识别时自动上传"
            })
        else:
            log_step(step, "检查external_file_id", "success", {
                "external_file_id": file_record['external_file_id']
            })
        
        # 步骤11: 检查任务状态
        step += 1
        log_step(step, "检查任务状态", "start")
        
        if task_record['status'] == "processing":
            duration = None
            if task_record['start_time']:
                duration = (datetime.now() - task_record['start_time']).total_seconds()
            
            log_step(step, "检查任务状态", "info", {
                "status": "processing",
                "message": "任务当前状态为processing，可能卡住了",
                "start_time": str(task_record['start_time']),
                "duration_seconds": round(duration, 2) if duration else None,
                "error_code": task_record['error_code'],
                "error_message": task_record['error_message']
            })
            
            print("\n" + "=" * 80)
            print("⚠️  任务卡在 processing 状态")
            print("=" * 80)
            if duration:
                print(f"持续时间: {duration:.2f} 秒 ({duration/60:.2f} 分钟)")
            if task_record['error_code']:
                print(f"错误代码: {task_record['error_code']}")
            if task_record['error_message']:
                print(f"错误消息: {task_record['error_message']}")
            print("=" * 80)
            
        elif task_record['status'] == "pending":
            log_step(step, "检查任务状态", "info", {
                "status": "pending",
                "message": "任务状态为pending，可以启动"
            })
        elif task_record['status'] == "completed":
            log_step(step, "检查任务状态", "success", {
                "status": "completed",
                "message": "任务已完成"
            })
        elif task_record['status'] == "failed":
            log_step(step, "检查任务状态", "failed", {
                "status": "failed",
                "error_code": task_record['error_code'],
                "error_message": task_record['error_message']
            })
        else:
            log_step(step, "检查任务状态", "info", {
                "status": task_record['status'],
                "message": f"任务状态: {task_record['status']}"
            })
        
        # 步骤12: 总结检查结果
        step += 1
        log_step(step, "检查结果总结", "start")
        
        summary = {
            "file_found": True,
            "file_exists": True,
            "invoice_found": True,
            "task_found": True,
            "task_params_valid": True,
            "model_config_found": True,
            "model_config_active": model_config_record['is_active'],
            "api_config_valid": bool(endpoint and api_key),
            "external_file_id_set": bool(file_record['external_file_id']),
            "task_status": task_record['status']
        }
        
        log_step(step, "检查结果总结", "success", summary)
        
        print("\n" + "=" * 80)
        print("检查结果总结")
        print("=" * 80)
        for key, value in summary.items():
            status = "✓" if value else "✗"
            print(f"{status} {key}: {value}")
        print("=" * 80)
        
        # 如果任务卡在processing，提供建议
        if task_record['status'] == "processing":
            print("\n建议:")
            print("1. 查看后端服务日志，查找错误信息")
            print("2. 检查 API endpoint 是否可访问")
            print("3. 检查 API key 是否有效")
            print("4. 检查网络连接")
            print("5. 如果任务卡住超过5分钟，可能需要重置任务状态")
        
        cur.close()
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        print(f"详细日志已保存到: {LOG_FILE}")
        
    except Exception as e:
        log_step(step + 1, "测试异常", "failed", {"error": str(e)})
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n[错误] 测试过程中发生异常:")
        print(error_trace)
        log_step(step + 1, "测试异常", "info", {"traceback": error_trace})
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # 可以通过命令行参数指定文件名
    file_name = sys.argv[1] if len(sys.argv) > 1 else "China SY inv 1.PDF"
    test_invoice_recognition(file_name)

