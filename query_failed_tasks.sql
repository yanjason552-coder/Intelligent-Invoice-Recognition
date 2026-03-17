-- 查询失败的识别任务
-- 按创建时间倒序，显示最近的失败任务

SELECT 
    t.id,
    t.task_no,
    t.status,
    t.error_code,
    t.error_message,
    t.create_time,
    t.start_time,
    t.end_time,
    CASE 
        WHEN t.start_time IS NOT NULL AND t.end_time IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (t.end_time - t.start_time))
        ELSE NULL
    END as duration_seconds,
    f.file_name,
    llm.name as model_config_name,
    i.invoice_no
FROM recognition_task t
LEFT JOIN invoice i ON t.invoice_id = i.id
LEFT JOIN invoice_file f ON i.file_id = f.id
LEFT JOIN llm_config llm ON (t.params->>'model_config_id')::uuid = llm.id
WHERE t.status = 'failed'
ORDER BY t.create_time DESC
LIMIT 20;

-- 按错误代码统计
SELECT 
    error_code,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM recognition_task WHERE status = 'failed'), 2) as percentage
FROM recognition_task
WHERE status = 'failed'
GROUP BY error_code
ORDER BY count DESC;

-- 最常见的错误消息（前10条）
SELECT 
    LEFT(error_message, 100) as error_message_preview,
    COUNT(*) as count
FROM recognition_task
WHERE status = 'failed' AND error_message IS NOT NULL
GROUP BY LEFT(error_message, 100)
ORDER BY count DESC
LIMIT 10;

