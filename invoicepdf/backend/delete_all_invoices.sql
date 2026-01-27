-- ============================================================
-- 删除所有发票相关数据的 SQL 脚本
-- ============================================================
-- 警告：此操作将永久删除所有发票相关数据，请谨慎操作！
-- 建议：执行前请先备份数据库
-- ============================================================

-- 删除顺序（考虑外键依赖关系）：
-- 1. InvoiceItem (发票行项目)
-- 2. RecognitionResult (识别结果)
-- 3. RecognitionField (识别字段)
-- 4. SchemaValidationRecord (模式验证记录)
-- 5. ReviewRecord (审核记录)
-- 6. RecognitionTask (识别任务)
-- 7. Invoice (发票)
-- 8. InvoiceFile (发票文件)

BEGIN;

-- 1. 删除发票行项目
DELETE FROM invoice_item;
-- 如果需要查看删除数量，可以取消下面的注释
-- SELECT 'invoice_item' as table_name, COUNT(*) as deleted_count FROM invoice_item;

-- 2. 删除识别结果
DELETE FROM recognition_result;

-- 3. 删除识别字段
DELETE FROM recognition_field;

-- 4. 删除模式验证记录
DELETE FROM schema_validation_record;

-- 5. 删除审核记录
DELETE FROM review_record;

-- 6. 删除识别任务
DELETE FROM recognition_task;

-- 7. 删除发票
DELETE FROM invoice;

-- 8. 删除发票文件
DELETE FROM invoice_file;

-- 提交事务
COMMIT;

-- 验证删除结果（可选）
-- SELECT 
--     (SELECT COUNT(*) FROM invoice_item) as invoice_item_count,
--     (SELECT COUNT(*) FROM recognition_result) as recognition_result_count,
--     (SELECT COUNT(*) FROM recognition_field) as recognition_field_count,
--     (SELECT COUNT(*) FROM schema_validation_record) as schema_validation_record_count,
--     (SELECT COUNT(*) FROM review_record) as review_record_count,
--     (SELECT COUNT(*) FROM recognition_task) as recognition_task_count,
--     (SELECT COUNT(*) FROM invoice) as invoice_count,
--     (SELECT COUNT(*) FROM invoice_file) as invoice_file_count;

