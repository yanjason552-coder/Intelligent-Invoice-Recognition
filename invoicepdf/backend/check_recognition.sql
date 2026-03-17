-- 检查发票识别情况的 SQL 查询脚本

-- 1. 识别任务状态统计
SELECT 
    status,
    COUNT(*) as count,
    CASE status
        WHEN 'pending' THEN '待处理'
        WHEN 'processing' THEN '处理中'
        WHEN 'completed' THEN '已完成'
        WHEN 'failed' THEN '失败'
        ELSE status
    END as status_label
FROM recognition_task
GROUP BY status
ORDER BY 
    CASE status
        WHEN 'pending' THEN 1
        WHEN 'processing' THEN 2
        WHEN 'completed' THEN 3
        WHEN 'failed' THEN 4
        ELSE 5
    END;

-- 2. 识别结果统计
SELECT 
    status,
    COUNT(*) as count,
    CASE status
        WHEN 'success' THEN '成功'
        WHEN 'failed' THEN '失败'
        WHEN 'partial' THEN '部分成功'
        ELSE status
    END as status_label
FROM recognition_result
GROUP BY status;

-- 3. 平均准确率和置信度
SELECT 
    AVG(accuracy) as avg_accuracy,
    AVG(confidence) as avg_confidence,
    COUNT(*) as total_results
FROM recognition_result;

-- 4. 长时间处理中的任务（超过30分钟）
SELECT 
    id,
    task_no,
    status,
    start_time,
    EXTRACT(EPOCH FROM (NOW() - start_time))/60 as minutes_elapsed,
    error_message
FROM recognition_task
WHERE status = 'processing' 
  AND start_time < NOW() - INTERVAL '30 minutes'
ORDER BY start_time;

-- 5. 最近失败的任务
SELECT 
    id,
    task_no,
    status,
    error_code,
    error_message,
    create_time
FROM recognition_task
WHERE status = 'failed'
ORDER BY create_time DESC
LIMIT 10;

-- 6. 使用模板提示词的任务数
SELECT 
    COUNT(*) as tasks_with_prompt
FROM recognition_task
WHERE params IS NOT NULL 
  AND params::text LIKE '%template_prompt%'
  AND params->>'template_prompt' IS NOT NULL
  AND params->>'template_prompt' != 'null'
  AND params->>'template_prompt' != '';

-- 7. 最近完成的识别任务（带结果信息）
SELECT 
    rt.task_no,
    rt.end_time,
    rt.duration,
    rr.accuracy,
    rr.confidence,
    rr.recognized_fields,
    rr.total_fields
FROM recognition_task rt
LEFT JOIN recognition_result rr ON rt.id = rr.task_id
WHERE rt.status = 'completed'
ORDER BY rt.end_time DESC
LIMIT 5;

