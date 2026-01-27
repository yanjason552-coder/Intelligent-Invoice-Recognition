@echo off
cd /d "%~dp0backend"
python -c "
import psycopg2

# 直接连接数据库
conn = psycopg2.connect(
    host='localhost',
    database='invoice_db',
    user='postgres',
    password='postgres'
)

cursor = conn.cursor()

print('=== 修复卡住的识别任务 ===')

# 查询卡住的任务
cursor.execute('SELECT id, task_no, status, start_time FROM recognition_tasks WHERE status = \'processing\' AND start_time IS NOT NULL')

all_processing = cursor.fetchall()
print(f'发现 {len(all_processing)} 个processing状态的任务')

# 重置运行超过5分钟的任务
updated_count = 0
for task in all_processing:
    task_id, task_no, status, start_time = task
    print(f'检查任务: {task_no} (ID: {task_id})')
    
    # 更新任务状态 - 重置所有processing状态的任务
    cursor.execute('UPDATE recognition_tasks SET status = \'pending\', start_time = NULL, end_time = NULL, error_code = NULL, error_message = \'任务被系统重置\' WHERE id = %s', (task_id,))
    updated_count += 1

conn.commit()
print(f'成功重置 {updated_count} 个卡住的任务')

cursor.close()
conn.close()
"
pause
