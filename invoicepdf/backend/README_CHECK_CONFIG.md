# 配置和文件检查指南

## 方法1: 使用 Python 脚本（推荐）

### 简化版脚本（不需要环境变量）

```powershell
cd invoicepdf\backend
python check_config_simple.py
```

**注意**: 如果数据库连接信息不是默认值，请设置环境变量：
```powershell
$env:POSTGRES_SERVER="localhost"
$env:POSTGRES_PORT="5432"
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="your_password"
$env:POSTGRES_DB="app"
python check_config_simple.py
```

### 完整版脚本（需要应用环境变量）

如果后端服务正在运行，可以使用完整版脚本：
```powershell
cd invoicepdf\backend
python check_config_and_files.py
```

## 方法2: 使用 SQL 查询（最简单）

直接在数据库管理工具（如 pgAdmin、DBeaver、psql）中执行以下 SQL：

### 检查 llm_config 配置

```sql
-- 1. 查看所有配置及其必需字段状态
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
    CASE 
        WHEN name IS NULL OR name = '' THEN '❌'
        WHEN endpoint IS NULL OR endpoint = '' THEN '❌'
        WHEN api_key IS NULL OR api_key = '' THEN '❌'
        WHEN is_active = false THEN '⚠️'
        ELSE '✅'
    END as 配置状态
FROM llm_config
ORDER BY create_time DESC;
```

### 检查文件的 external_file_id

```sql
-- 2. 查看所有文件及其 external_file_id 状态
SELECT 
    id,
    file_name,
    file_type,
    file_size,
    CASE 
        WHEN external_file_id IS NULL OR external_file_id = '' THEN '❌ 未设置'
        ELSE '✅ ' || external_file_id
    END as external_file_id_status,
    upload_time
FROM invoice_file
ORDER BY upload_time DESC;
```

### 统计信息

```sql
-- 3. 统计 external_file_id 情况
SELECT 
    COUNT(*) as 总文件数,
    COUNT(external_file_id) as 有external_file_id,
    COUNT(*) - COUNT(external_file_id) as 无external_file_id
FROM invoice_file;
```

### 检查卡在 processing 状态的任务

```sql
-- 4. 查看 processing 状态的任务
SELECT 
    t.id,
    t.task_no,
    t.status,
    t.start_time,
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
```

## llm_config 表必需字段

### ✅ 必需字段（不能为空）

1. **name** - 配置名称
   - 不能为空
   - 必须唯一

2. **endpoint** - API端点地址
   - 不能为空
   - 必须以 `http://` 或 `https://` 开头
   - 示例: `https://api.syntax.ai/v1`

3. **api_key** - API密钥
   - 不能为空
   - 用于API认证

4. **creator_id** - 创建人ID
   - 不能为空
   - 必须是有效的用户ID

5. **is_active** - 是否启用
   - 默认值: `true`
   - 只有 `is_active = true` 的配置才能使用

### ⚠️ 建议配置的字段

根据 `app_type` 的不同：

- **如果 `app_type = "workflow"`**:
  - `workflow_id` - 工作流ID（建议配置）

- **如果 `app_type = "chat"`**:
  - `app_id` - 应用ID（建议配置）

## external_file_id 说明

### 什么是 external_file_id？

`external_file_id` 是文件上传到外部API（DIFY/SYNTAX）后返回的文件ID，用于后续调用识别API。

### 如果文件没有 external_file_id 会怎样？

系统会自动处理：
1. 检测到文件缺少 `external_file_id`
2. 自动调用 `/files/upload` API 上传文件
3. 获取 `external_file_id` 并保存到数据库
4. 使用该 `external_file_id` 调用识别API

**注意**: 如果自动上传失败，任务会失败并记录错误信息。

## 快速检查清单

- [ ] `llm_config` 表中有至少一个配置
- [ ] 配置的 `name` 不为空
- [ ] 配置的 `endpoint` 不为空且格式正确（以 http:// 或 https:// 开头）
- [ ] 配置的 `api_key` 不为空
- [ ] 配置的 `is_active = true`
- [ ] 如果 `app_type = "workflow"`，建议配置 `workflow_id`
- [ ] 文件有 `external_file_id`（如果没有，系统会自动上传）

