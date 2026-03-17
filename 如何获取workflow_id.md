# 如何获取 workflow_id

## 概述

`workflow_id` 是 Dify/SYNTAX 平台中工作流（Workflow）的唯一标识符。当模型配置的应用类型为 `workflow` 时，必须设置此字段才能成功调用 API。

## 获取步骤

### 方法1：从 Dify 平台获取（推荐）

1. **登录 Dify 平台**
   - 访问您的 Dify 平台地址（例如：`http://8.145.33.61`）
   - 使用您的账号登录

2. **进入工作流页面**
   - 在左侧导航栏中找到"工作流"（Workflows）或"应用"（Apps）
   - 点击进入工作流列表

3. **选择目标工作流**
   - 在工作流列表中找到您要使用的工作流（例如："尺寸/孔位类检验记录大模型"对应的工作流）
   - 点击工作流名称进入详情页面

4. **查找 Workflow ID**
   - 在工作流详情页面，查找以下位置：
     - **设置页面**：点击右上角的"设置"（Settings）图标，在"基本信息"或"API设置"中查找
     - **API 文档**：查看工作流的 API 文档，通常会显示 workflow_id
     - **URL 地址**：工作流详情页面的 URL 可能包含 workflow_id，格式如：`/workflows/{workflow_id}`
     - **开发者工具**：打开浏览器开发者工具（F12），在 Network 标签中查看 API 请求，workflow_id 可能出现在请求 URL 或响应中

5. **复制 Workflow ID**
   - 复制完整的 workflow_id（通常是一串字母数字组合，可能包含连字符）
   - 例如：`abc123-def456-ghi789` 或 `workflow_abc123`

### 方法2：从 API 响应中获取

如果您之前成功调用过工作流 API，可以从 API 响应中查找 workflow_id：

1. **查看 API 响应**
   - 打开浏览器开发者工具（F12）
   - 切换到 Network（网络）标签
   - 找到之前调用工作流 API 的请求
   - 查看响应内容，workflow_id 可能出现在响应数据中

2. **查看后端日志**
   - 如果系统之前成功调用过该工作流，后端日志中可能包含 workflow_id
   - 查看日志文件或控制台输出

### 方法3：通过 API 查询

如果您有 Dify API 的访问权限，可以通过 API 查询工作流列表：

```bash
# 使用 curl 查询工作流列表
curl -X GET "http://8.145.33.61/v1/workflows" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

响应中会包含每个工作流的 `id` 字段，这就是 `workflow_id`。

## 在系统中设置

获取到 `workflow_id` 后，按以下步骤在系统中设置：

1. **打开模型配置页面**
   - 登录系统
   - 进入"大模型配置" → "配置列表"

2. **编辑配置**
   - 找到要编辑的配置（例如："尺寸/孔位类检验记录大模型"）
   - 点击"编辑"按钮

3. **设置 Workflow ID**
   - 确认"应用类型"已选择为"工作流 (Workflow)"
   - 在"工作流ID (Workflow ID)"输入框中粘贴您获取的 workflow_id
   - 点击"测试连接"验证配置是否正确
   - 如果测试通过，点击"保存配置"

4. **验证设置**
   - 保存后，重新启动识别任务
   - 查看任务状态，确认 Dify API 调用成功

## 常见问题

### Q1: 找不到 workflow_id 怎么办？

**A:** 尝试以下方法：
- 联系 Dify 平台管理员，询问工作流的 workflow_id
- 查看 Dify 平台的 API 文档
- 检查工作流的设置页面，可能以其他名称显示（如"应用ID"、"工作流标识"等）

### Q2: workflow_id 格式是什么样的？

**A:** workflow_id 通常是：
- 一串字母数字组合，可能包含连字符（`-`）或下划线（`_`）
- 长度通常在 20-50 个字符之间
- 例如：`abc123-def456-ghi789`、`workflow_abc123`、`wfl-abc123def456`

### Q3: 设置了 workflow_id 仍然报错？

**A:** 检查以下几点：
- 确认 workflow_id 是否正确（没有多余的空格或特殊字符）
- 确认 API 端点地址是否正确
- 确认 API 密钥是否有效
- 查看后端日志中的详细错误信息
- 使用"测试连接"功能验证配置

### Q4: 工作流类型必须设置 workflow_id 吗？

**A:** 是的。当应用类型为 `workflow` 时，`workflow_id` 是必填字段。如果不设置，系统会返回错误："应用类型为 workflow 但未设置 workflow_id"。

## 相关文档

- [Dify API 文档](https://docs.dify.ai/api-reference)
- [SYNTAX API 文档](https://docs.syntax.ai/api-reference)

## 联系支持

如果仍然无法获取或设置 workflow_id，请联系技术支持或 Dify 平台管理员。

