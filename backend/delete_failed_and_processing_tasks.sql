-- 删除状态为"失败"和"识别中"的识别任务
-- 注意：此脚本会删除所有状态为 'failed' 和 'processing' 的识别任务及其关联数据

-- 1. 查看要删除的任务数量
SELECT 
    status,
    COUNT(*) as count
FROM recognition_task
WHERE status IN ('failed', 'processing')
GROUP BY status;

-- 2. 查看要删除的任务总数
SELECT COUNT(*) as total_count
FROM recognition_task
WHERE status IN ('failed', 'processing');

-- 3. 开始删除（请谨慎执行）
BEGIN;

-- 3.1 删除关联的识别结果
DELETE FROM recognition_result
WHERE task_id IN (
    SELECT id FROM recognition_task WHERE status IN ('failed', 'processing')
);

-- 3.2 删除关联的Schema验证记录
DELETE FROM schema_validation_record
WHERE task_id IN (
    SELECT id FROM recognition_task WHERE status IN ('failed', 'processing')
);

-- 3.3 删除识别任务
DELETE FROM recognition_task
WHERE status IN ('failed', 'processing');

-- 4. 查看删除后的统计
SELECT 
    status,
    COUNT(*) as count
FROM recognition_task
GROUP BY status;

-- 5. 如果确认无误，执行 COMMIT；否则执行 ROLLBACK
-- COMMIT;
-- ROLLBACK;
