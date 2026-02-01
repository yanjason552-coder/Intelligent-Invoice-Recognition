# 修复模型选择问题

## 问题描述

1. **任务使用了错误的模型**：当前任务使用的是 `SYNTAX-AI-API_V2`，但应该使用 `API_V3_JsonSchema`
2. **前端默认选择第一个模型**：前端代码默认选择模型列表中的第一个模型
3. **模型列表顺序问题**：后端返回的模型列表顺序导致 `SYNTAX-AI-API_V2` 排在 `API_V3_JsonSchema` 之前

## 解决方案

### 1. 修改后端API排序逻辑

已修改 `backend/app/api/routes/config.py` 和 `invoicepdf/backend/app/api/routes/config.py` 中的 `get_recognition_config_options` 函数：

**修改前：**
```python
llm_configs_query = select(LLMConfig).where(LLMConfig.is_active == True)
llm_configs = session.exec(llm_configs_query).all()
```

**修改后：**
```python
from sqlalchemy import case
llm_configs_query = select(LLMConfig).where(LLMConfig.is_active == True).order_by(
    LLMConfig.is_default.desc(),  # 默认模型排在前面
    case(
        (LLMConfig.name.ilike('%v3_jsonschema%'), 0),
        (LLMConfig.name.ilike('%jsonschema%'), 1),
        else_=2
    ),  # 包含 JsonSchema 的模型优先
    LLMConfig.name  # 最后按名称排序
)
llm_configs = session.exec(llm_configs_query).all()
```

### 2. 排序优先级

1. **第一优先级**：`is_default=True` 的模型
2. **第二优先级**：名称包含 `v3_jsonschema` 的模型（不区分大小写）
3. **第三优先级**：名称包含 `jsonschema` 的模型（不区分大小写）
4. **最后**：按名称字母顺序排序

## 验证方法

### 方法1：重启后端服务后测试

1. 重启后端服务
2. 打开前端页面
3. 点击"批量启动识别"
4. 在参数选择弹窗中，检查"模型配置"下拉框的第一个选项是否为 `API_V3_JsonSchema`

### 方法2：使用浏览器控制台检查

在浏览器控制台运行：

```javascript
const token = localStorage.getItem('access_token');
fetch('http://localhost:8000/api/v1/config/recognition-config/options', {
    headers: { 'Authorization': `Bearer ${token}` }
})
.then(r => r.json())
.then(data => {
    console.log('模型配置列表顺序:');
    data.model_configs.forEach((m, i) => {
        console.log(`${i + 1}. ${m.name} (ID: ${m.id})`);
    });
});
```

应该看到 `API_V3_JsonSchema` 排在第一位（或 `is_default=True` 的模型排在第一位）。

## 当前任务的处理

当前处理中的任务 `TASK-20260128103644-2da8af48` 已经使用了错误的模型，无法修改。建议：

1. **等待当前任务完成或取消**
2. **创建新任务时**，确保选择 `API_V3_JsonSchema` 模型
3. **如果任务可以取消**，可以取消后重新创建

## 设置默认模型（可选）

如果需要将 `API_V3_JsonSchema` 设置为默认模型，可以在数据库中执行：

```sql
-- 先取消其他模型的默认标志
UPDATE llm_config SET is_default = false WHERE is_default = true;

-- 设置 API_V3_JsonSchema 为默认模型
UPDATE llm_config 
SET is_default = true 
WHERE name ILIKE '%v3_jsonschema%' OR name ILIKE '%API_V3_JsonSchema%';
```

## 注意事项

1. **重启后端服务**：修改代码后需要重启后端服务才能生效
2. **前端缓存**：如果前端有缓存，可能需要刷新页面
3. **新任务**：只有新创建的任务才会使用新的排序逻辑，已存在的任务不会受影响

