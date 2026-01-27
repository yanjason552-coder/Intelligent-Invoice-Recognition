-- ============================================
-- 检查 llm_config 表配置的 SQL 查询
-- ============================================

-- 1. 查看所有 llm_config 配置
SELECT 
    id,
    name,
    endpoint,
    CASE 
        WHEN api_key IS NULL OR api_key = '' THEN '❌ 未设置'
        ELSE '✅ 已设置'
    END as api_key_status,
    app_type,
    workflow_id,
    app_id,
    is_active,
    is_default,
    timeout,
    max_retries,
    creator_id,
    create_time,
    update_time
FROM llm_config
ORDER BY create_time DESC;

-- 2. 检查必需字段是否为空
SELECT 
    id,
    name,
    CASE 
        WHEN name IS NULL OR name = '' THEN '❌ name 为空'
        ELSE '✅'
    END as name_check,
    CASE 
        WHEN endpoint IS NULL OR endpoint = '' THEN '❌ endpoint 为空'
        ELSE '✅'
    END as endpoint_check,
    CASE 
        WHEN api_key IS NULL OR api_key = '' THEN '❌ api_key 为空'
        ELSE '✅'
    END as api_key_check,
    CASE 
        WHEN is_active = false THEN '⚠️  未启用'
        ELSE '✅'
    END as active_check
FROM llm_config;

-- 3. 检查 endpoint 格式是否正确
SELECT 
    id,
    name,
    endpoint,
    CASE 
        WHEN endpoint NOT LIKE 'http://%' AND endpoint NOT LIKE 'https://%' THEN '⚠️  格式不正确'
        ELSE '✅'
    END as endpoint_format_check
FROM llm_config
WHERE endpoint IS NOT NULL AND endpoint != '';

-- 4. 检查 workflow 类型配置是否缺少 workflow_id
SELECT 
    id,
    name,
    app_type,
    workflow_id,
    CASE 
        WHEN app_type = 'workflow' AND (workflow_id IS NULL OR workflow_id = '') THEN '⚠️  缺少 workflow_id'
        ELSE '✅'
    END as workflow_id_check
FROM llm_config
WHERE app_type = 'workflow';

-- 5. 检查 chat 类型配置是否缺少 app_id
SELECT 
    id,
    name,
    app_type,
    app_id,
    CASE 
        WHEN app_type = 'chat' AND (app_id IS NULL OR app_id = '') THEN '⚠️  缺少 app_id'
        ELSE '✅'
    END as app_id_check
FROM llm_config
WHERE app_type = 'chat';

-- ============================================
-- 检查文件的 external_file_id
-- ============================================

-- 1. 查看所有文件及其 external_file_id
SELECT 
    id,
    file_name,
    file_path,
    file_type,
    file_size,
    CASE 
        WHEN external_file_id IS NULL OR external_file_id = '' THEN '❌ 未设置'
        ELSE '✅ ' || external_file_id
    END as external_file_id_status,
    upload_time
FROM invoice_file
ORDER BY upload_time DESC;

-- 2. 统计 external_file_id 情况
SELECT 
    COUNT(*) as total_files,
    COUNT(external_file_id) as files_with_external_id,
    COUNT(*) - COUNT(external_file_id) as files_without_external_id
FROM invoice_file;

-- 3. 查看缺少 external_file_id 的文件
SELECT 
    id,
    file_name,
    file_path,
    file_type,
    upload_time
FROM invoice_file
WHERE external_file_id IS NULL OR external_file_id = ''
ORDER BY upload_time DESC;

-- ============================================
-- 检查卡在 processing 状态的任务
-- ============================================

-- 1. 查看所有 processing 状态的任务
SELECT 
    t.id,
    t.task_no,
    t.status,
    t.start_time,
    t.create_time,
    t.error_code,
    t.error_message,
    i.invoice_no,
    i.recognition_status,
    f.file_name,
    f.external_file_id,
    t.params->>'model_config_id' as model_config_id
FROM recognition_task t
LEFT JOIN invoice i ON t.invoice_id = i.id
LEFT JOIN invoice_file f ON i.file_id = f.id
WHERE t.status = 'processing'
ORDER BY t.start_time DESC;

-- 2. 统计各状态的任务数量
SELECT 
    status,
    COUNT(*) as count
FROM recognition_task
GROUP BY status
ORDER BY count DESC;

