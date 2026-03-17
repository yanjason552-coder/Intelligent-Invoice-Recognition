-- 查询发票处理情况
-- 发票编号: INV-20260204220829-47f7d8db

-- 1. 查询发票基本信息
SELECT 
    id,
    invoice_no,
    recognition_status,
    review_status,
    recognition_accuracy,
    create_time,
    file_id
FROM invoice 
WHERE invoice_no = 'INV-20260204220829-47f7d8db';

-- 2. 查询识别任务（替换 :invoice_id 为上面查询到的 id）
SELECT 
    id,
    task_no,
    status,
    start_time,
    end_time,
    duration,
    error_message,
    error_code,
    create_time
FROM recognition_task 
WHERE invoice_id = (
    SELECT id FROM invoice WHERE invoice_no = 'INV-20260204220829-47f7d8db'
)
ORDER BY create_time DESC;

-- 3. 查询识别结果
SELECT 
    id,
    task_id,
    status,
    total_fields,
    recognized_fields,
    accuracy,
    confidence,
    recognition_time
FROM recognition_result 
WHERE invoice_id = (
    SELECT id FROM invoice WHERE invoice_no = 'INV-20260204220829-47f7d8db'
)
ORDER BY recognition_time DESC;

-- 4. 查询审核记录
SELECT 
    id,
    review_status,
    review_comment,
    reviewer_id,
    review_time
FROM review_record 
WHERE invoice_id = (
    SELECT id FROM invoice WHERE invoice_no = 'INV-20260204220829-47f7d8db'
)
ORDER BY review_time DESC;

-- 5. 综合查询（一次性查看所有信息）
SELECT 
    i.id as invoice_id,
    i.invoice_no,
    i.recognition_status,
    i.review_status,
    i.recognition_accuracy,
    i.create_time as invoice_create_time,
    t.id as task_id,
    t.task_no,
    t.status as task_status,
    t.start_time,
    t.end_time,
    t.duration,
    t.error_message,
    r.id as result_id,
    r.status as result_status,
    r.total_fields,
    r.recognized_fields,
    r.accuracy as result_accuracy,
    r.recognition_time
FROM invoice i
LEFT JOIN recognition_task t ON t.invoice_id = i.id
LEFT JOIN recognition_result r ON r.task_id = t.id
WHERE i.invoice_no = 'INV-20260204220829-47f7d8db'
ORDER BY t.create_time DESC, r.recognition_time DESC;

