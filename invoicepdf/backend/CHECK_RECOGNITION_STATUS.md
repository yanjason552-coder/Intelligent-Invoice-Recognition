# 检查发票识别情况

## 方法1：使用浏览器开发者工具（最简单）

1. **打开前端页面并登录**
   - 访问前端应用（通常是 http://localhost:5173）
   - 完成登录

2. **获取访问Token**
   - 按 F12 打开开发者工具
   - 切换到 Console（控制台）标签
   - 输入以下命令获取token：
   ```javascript
   localStorage.getItem('access_token')
   ```
   - 复制返回的token值

3. **访问API**
   - 在浏览器地址栏输入：
   ```
   http://localhost:8000/api/v1/statistics/recognition-status
   ```
   - 按 F12 打开开发者工具
   - 切换到 Network（网络）标签
   - 刷新页面
   - 找到 recognition-status 请求
   - 右键点击 → Copy → Copy as cURL
   - 在命令前添加：`curl -H "Authorization: Bearer <你的token>" `

   或者使用浏览器插件（如 ModHeader）添加请求头：
   ```
   Authorization: Bearer <你的token>
   ```

## 方法2：使用 Python 脚本

1. **修改脚本中的登录信息**
   - 编辑 `test_recognition_status.py`
   - 修改用户名和密码：
   ```python
   login_data = {
       "username": "你的邮箱",
       "password": "你的密码"
   }
   ```

2. **运行脚本**
   ```bash
   python invoicepdf/backend/test_recognition_status.py
   ```

## 方法3：使用 curl 命令

1. **先登录获取token**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/login/access-token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=你的邮箱&password=你的密码"
   ```

2. **使用返回的token访问API**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/statistics/recognition-status" \
     -H "Authorization: Bearer <你的token>"
   ```

## 方法4：使用 Postman 或类似工具

1. **设置请求**
   - URL: `http://localhost:8000/api/v1/statistics/recognition-status`
   - Method: GET
   - Headers:
     - Key: `Authorization`
     - Value: `Bearer <你的token>`

## API 返回数据说明

返回的JSON数据包含以下字段：

- **task_status**: 任务状态统计
  - pending: 待处理任务数
  - processing: 处理中任务数
  - completed: 已完成任务数
  - failed: 失败任务数
  - total: 总任务数

- **stuck_tasks**: 长时间处理中的任务列表（超过30分钟）

- **failed_tasks**: 最近失败的任务列表

- **result_status**: 识别结果统计
  - total: 结果总数
  - success: 成功结果数
  - failed: 失败结果数
  - partial: 部分成功结果数
  - avg_accuracy: 平均准确率
  - avg_confidence: 平均置信度

- **recent_completed**: 最近完成的识别任务详情

- **prompt_usage**: 模板提示词使用情况
  - tasks_with_prompt: 使用提示词的任务数
  - total_tasks: 总任务数
  - usage_rate: 使用率

- **model_usage**: 各模型配置的使用情况统计

