# 修复总结

## 问题描述

1. **任务创建时 template_id 未保存**：虽然 params 中有 template_id，但任务的 template_id 字段为 null
2. **任务创建时 template_prompt 未获取**：虽然模板有 prompt，但创建任务时没有获取并保存到 params 中
3. **任务处理时间过长**：任务处理超过7分钟仍在 processing 状态

## 已完成的修复

### 1. 修复创建任务时的 template_id 保存问题

**文件**: `backend/app/api/routes/invoice.py` 和 `invoicepdf/backend/app/api/routes/invoice.py`

**修改内容**:
- 确保 template_id 是 UUID 类型（如果传入的是字符串，转换为 UUID）
- 即使模板查询失败，也使用 params 中的 template_id
- 添加调试日志

**关键代码**:
```python
if task_in.params.template_id:
    # 确保 template_id 是 UUID 类型
    from uuid import UUID
    if isinstance(task_in.params.template_id, str):
        template_id = UUID(task_in.params.template_id)
    else:
        template_id = task_in.params.template_id
    
    logger.info(f"设置 template_id: {template_id} (类型: {type(template_id)})")
```

### 2. 修复处理任务时的 template_prompt 获取问题

**文件**: `backend/app/services/dify_service.py` 和 `invoicepdf/backend/app/services/dify_service.py`

**修改内容**:
- 添加后备逻辑：如果 task.template_id 为 null，从 task.params.template_id 获取
- 从模板对象获取 prompt 并添加到 DIFY API 的 inputs 中

**关键代码**:
```python
# 优先使用 task.template_id，如果没有则使用 task.params.template_id
if task.template_id:
    template_id_for_prompt = task.template_id
elif task.params and task.params.get("template_id"):
    template_id_for_prompt = task.params.get("template_id")
    logger.info(f"[步骤C3.1] task.template_id 为空，使用 params 中的 template_id: {template_id_for_prompt}")
```

### 3. 修复模型配置排序问题

**文件**: `backend/app/api/routes/config.py` 和 `invoicepdf/backend/app/api/routes/config.py`

**修改内容**:
- 模型列表按优先级排序：默认模型 > v3_JsonSchema > 其他模型

## 需要重启后端服务

**重要**: 所有修复都需要重启后端服务才能生效！

1. 停止当前后端服务（Ctrl+C）
2. 重新启动后端服务
3. 创建新任务进行测试

## 验证修复

重启后端后，创建新任务时应该：

1. **template_id 正确保存**：
   ```javascript
   // 检查新任务的 template_id
   console.log('模板ID (任务字段):', task.template_id); // 应该不是 null
   ```

2. **template_prompt 正确保存**：
   ```javascript
   // 检查新任务的 template_prompt
   console.log('提示词:', task.params?.template_prompt ? '存在' : '不存在'); // 应该是 '存在'
   ```

3. **后端日志应该显示**：
   - `模板策略: fixed, template_id: ...`
   - `设置 template_id: ... (类型: <class 'uuid.UUID'>)`
   - `获取到模板提示词，长度: 787 字符`
   - `任务创建完成，task.template_id: ...`

## 当前任务状态

- **任务**: TASK-20260128113208-bdd401f9
- **状态**: processing（已处理约7分钟）
- **问题**: template_id 为 null，template_prompt 不存在

**建议**:
- 继续监控当前任务
- 如果任务失败或超时，重新创建任务（使用修复后的代码）
- 如果任务成功但没有使用模板，可以重新创建任务

## 下一步

1. **重启后端服务**（必须）
2. **创建新任务测试**
3. **检查后端日志**，确认修复是否生效
4. **监控任务执行**，确认 prompt 是否正确传递给 DIFY API

