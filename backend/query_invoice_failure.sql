-- 查询票据失败原因
-- 使用方法: psql -U your_user -d your_database -f query_invoice_failure.sql

-- 查询指定票据的失败原因
SELECT 
    i.id as invoice_id,
    i.invoice_no,
    i.recognition_status,
    i.create_time as invoice_create_time,
    i.update_time as invoice_update_time,
    rt.id as task_id,
    rt.task_no,
    rt.status as task_status,
    rt.error_code,
    rt.error_message,
    rt.create_time as task_create_time,
    rt.start_time,
    rt.end_time,
    CASE 
        WHEN rt.start_time IS NOT NULL AND rt.end_time IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (rt.end_time - rt.start_time))
        ELSE NULL
    END as duration_seconds,
    rt.request_id,
    rt.trace_id,
    rt.params->>'model_config_id' as model_config_id,
    rt.params->>'output_schema_id' as schema_id,
    f.file_name,
    f.file_path,
    f.external_file_id,
    llm.name as model_config_name,
    llm.is_active as model_config_active,
    llm.endpoint as api_endpoint,
    CASE 
        WHEN llm.api_key IS NOT NULL AND llm.api_key != '' THEN '已配置'
        ELSE '未配置'
    END as api_key_status
FROM invoice i
LEFT JOIN recognition_task rt ON rt.invoice_id = i.id
LEFT JOIN invoice_file f ON i.file_id = f.id
LEFT JOIN llm_config llm ON (rt.params->>'model_config_id')::uuid = llm.id
WHERE i.invoice_no = 'INV-20260128132454-562b946f'
ORDER BY rt.create_time DESC;

-- 如果上面的查询没有结果，尝试只查询票据信息
SELECT 
    id,
    invoice_no,
    recognition_status,
    create_time,
    update_time
FROM invoice
WHERE invoice_no = 'INV-20260128132454-562b946f';

