-- ============================================================
-- 查询发票 INV-20260206144930-bb24635b 的详细信息
-- 包括：调用的模型、识别结果、字段显示逻辑
-- ============================================================

-- 1. 查询发票基本信息（包括模型和模板快照）
SELECT 
    id,
    invoice_no,
    invoice_type,
    recognition_status,
    review_status,
    recognition_accuracy,
    model_name,              -- 模型名称（快照）
    template_name,           -- 模板名称（快照）
    template_version,        -- 模板版本（快照）
    template_version_id,     -- 模板版本ID
    field_defs_snapshot,    -- 字段定义快照
    create_time,
    update_time
FROM invoice 
WHERE invoice_no = 'INV-20260206144930-bb24635b';

-- 2. 查询识别任务信息（包括模型配置）
SELECT 
    rt.id,
    rt.task_no,
    rt.status,
    rt.start_time,
    rt.end_time,
    rt.duration,
    rt.error_code,
    rt.error_message,
    rt.params->>'model_config_id' as model_config_id,  -- 模型配置ID
    rt.params->>'output_schema_id' as schema_id,      -- Schema ID
    rt.create_time
FROM recognition_task rt
WHERE rt.invoice_id = (
    SELECT id FROM invoice WHERE invoice_no = 'INV-20260206144930-bb24635b'
)
ORDER BY rt.create_time DESC;

-- 3. 查询模型配置信息（如果任务中有 model_config_id）
SELECT 
    lc.id,
    lc.name,
    lc.provider,
    lc.model_name,
    lc.endpoint,
    lc.is_active,
    lc.create_time
FROM llm_config lc
WHERE lc.id IN (
    SELECT (params->>'model_config_id')::uuid
    FROM recognition_task
    WHERE invoice_id = (
        SELECT id FROM invoice WHERE invoice_no = 'INV-20260206144930-bb24635b'
    )
    AND params->>'model_config_id' IS NOT NULL
    ORDER BY create_time DESC
    LIMIT 1
);

-- 4. 查询识别结果（包括标准化字段）
SELECT 
    rr.id,
    rr.task_id,
    rr.status,
    rr.total_fields,
    rr.recognized_fields,
    rr.accuracy,
    rr.confidence,
    rr.template_version_id,
    rr.model_usage,          -- 模型使用统计（token、耗时、费用）
    rr.normalized_fields,    -- 标准化字段（这是前端显示的主要数据源）
    rr.recognition_time,
    rr.create_time
FROM recognition_result rr
WHERE rr.invoice_id = (
    SELECT id FROM invoice WHERE invoice_no = 'INV-20260206144930-bb24635b'
)
ORDER BY rr.recognition_time DESC
LIMIT 1;

-- 5. 查询模板版本信息（如果识别结果中有 template_version_id）
SELECT 
    tv.id,
    tv.version,
    tv.template_id,
    tv.status,
    t.name as template_name,
    t.template_type,
    tv.field_defs,           -- 字段定义（JSON格式）
    tv.created_at
FROM template_version tv
JOIN template t ON t.id = tv.template_id
WHERE tv.id IN (
    SELECT template_version_id
    FROM recognition_result
    WHERE invoice_id = (
        SELECT id FROM invoice WHERE invoice_no = 'INV-20260206144930-bb24635b'
    )
    AND template_version_id IS NOT NULL
    ORDER BY recognition_time DESC
    LIMIT 1
);

-- 6. 综合查询（一次性查看所有关键信息）
SELECT 
    i.invoice_no,
    i.model_name as invoice_model_name,
    i.template_name as invoice_template_name,
    i.template_version as invoice_template_version,
    i.recognition_status,
    i.review_status,
    rt.task_no,
    rt.status as task_status,
    rt.params->>'model_config_id' as model_config_id,
    lc.name as model_config_name,
    lc.model_name as actual_model_name,
    rr.status as result_status,
    rr.total_fields,
    rr.recognized_fields,
    rr.accuracy,
    rr.template_version_id,
    tv.version as template_version_number,
    CASE 
        WHEN rr.normalized_fields IS NOT NULL THEN '有标准化字段数据'
        ELSE '无标准化字段数据'
    END as has_normalized_fields,
    CASE 
        WHEN i.field_defs_snapshot IS NOT NULL THEN '有字段定义快照'
        ELSE '无字段定义快照'
    END as has_field_defs_snapshot
FROM invoice i
LEFT JOIN recognition_task rt ON rt.invoice_id = i.id
LEFT JOIN llm_config lc ON lc.id::text = rt.params->>'model_config_id'
LEFT JOIN recognition_result rr ON rr.invoice_id = i.id
LEFT JOIN template_version tv ON tv.id = rr.template_version_id
WHERE i.invoice_no = 'INV-20260206144930-bb24635b'
ORDER BY rt.create_time DESC, rr.recognition_time DESC
LIMIT 1;

-- ============================================================
-- 字段显示逻辑说明：
-- ============================================================
-- 1. 在待审核页面（InvoiceReviewPending.tsx）显示：
--    - 模型名称：i.model_name
--    - 模板名称：i.template_name  
--    - 模板版本：i.template_version
--
-- 2. 在发票详情弹窗（InvoiceDetailModal.tsx）中：
--    - 字段定义来源（优先级）：
--      a) i.field_defs_snapshot（字段定义快照）
--      b) tv.field_defs（模板版本的字段定义）
--      c) 从 rr.normalized_fields 的键自动生成
--
--    - 字段值来源：
--      rr.normalized_fields（标准化字段数据）
--
-- 3. 模型信息：
--    - 识别时使用的模型：i.model_name（快照）
--    - 实际模型配置：lc.name, lc.model_name
--    - 模型使用统计：rr.model_usage（token、耗时、费用）
-- ============================================================

