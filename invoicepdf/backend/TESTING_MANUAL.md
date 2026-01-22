# 票据识别系统测试操作手册

## 📋 目录

1. [测试环境准备](#测试环境准备)
2. [数据库迁移](#数据库迁移)
3. [启动服务](#启动服务)
4. [API测试](#api测试)
5. [前端测试](#前端测试)
6. [集成测试](#集成测试)
7. [常见问题](#常见问题)

---

## 测试环境准备

### 1. 检查依赖

```bash
# 进入后端目录
cd backend

# 激活虚拟环境（如果使用）
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 检查Python版本（需要3.9+）
python --version

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置数据库

确保PostgreSQL数据库已启动并配置正确：

```bash
# 检查数据库连接配置
# 编辑 backend/app/core/config.py 或使用环境变量
```

环境变量配置示例：
```bash
# Windows PowerShell
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="changethis"
$env:POSTGRES_SERVER="localhost"
$env:POSTGRES_PORT="5432"
$env:POSTGRES_DB="app"

# Linux/Mac
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="changethis"
export POSTGRES_SERVER="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="app"
```

---

## 数据库迁移

### 1. 检查当前迁移状态

```bash
cd backend
alembic current
```

### 2. 执行迁移

```bash
# 升级到最新版本
alembic upgrade head
```

### 3. 验证表是否创建

使用数据库客户端（如pgAdmin、DBeaver）或命令行：

```sql
-- 连接到数据库
psql -U postgres -d app

-- 查看所有表
\dt

-- 或者使用SQL查询
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND (table_name LIKE 'invoice%' 
     OR table_name LIKE 'template%' 
     OR table_name LIKE 'recognition%' 
     OR table_name LIKE 'review%' 
     OR table_name LIKE 'ocr%');
```

应该看到11个表：
- invoice_file
- invoice
- template
- template_field
- template_training_task
- recognition_task
- recognition_result
- recognition_field
- review_record
- ocr_config
- recognition_rule

---

## 启动服务

### 1. 启动后端服务

```bash
cd backend

# 方式1：使用uvicorn直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式2：使用项目脚本（如果有）
python -m app.main
```

服务启动后，访问：
- API文档：http://localhost:8000/docs
- ReDoc文档：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/api/v1/health

### 2. 启动前端服务（可选）

```bash
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

前端服务通常在：http://localhost:5173

---

## API测试

### 准备工作：获取认证Token

#### 1. 创建测试用户（如果还没有）

```bash
# 使用Python脚本创建用户
python -c "
from app.core.security import get_password_hash
from app.models import User
from app.core.db import SessionLocal

db = SessionLocal()
user = User(
    email='test@example.com',
    hashed_password=get_password_hash('test123456'),
    full_name='Test User',
    is_active=True,
    is_superuser=True
)
db.add(user)
db.commit()
print('User created:', user.email)
db.close()
"
```

#### 2. 获取Token

**使用Swagger UI（推荐）：**

1. 访问 http://localhost:8000/docs
2. 找到 `/api/v1/login/access-token` 端点
3. 点击 "Try it out"
4. 输入用户名和密码：
   ```json
   {
     "username": "test@example.com",
     "password": "test123456"
   }
   ```
5. 点击 "Execute"
6. 复制返回的 `access_token`

**使用curl：**

```bash
# 登录获取token
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123456"

# 从响应中复制 access_token，然后设置环境变量
export TOKEN="your_access_token_here"
```

**使用PowerShell：**

```powershell
# 登录获取token
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/login/access-token" `
  -Method Post `
  -ContentType "application/x-www-form-urlencoded" `
  -Body @{username="test@example.com"; password="test123456"}

$token = $response.access_token
$headers = @{
    "Authorization" = "Bearer $token"
}
```

---

## 详细API测试步骤

### 1. 票据上传测试

#### 使用curl

```bash
# 准备测试文件（创建一个假的PDF文件用于测试）
echo "fake pdf content" > test_invoice.pdf

# 上传文件
curl -X POST "http://localhost:8000/api/v1/invoices/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_invoice.pdf"
```

#### 使用PowerShell

```powershell
# 创建测试文件
"fake pdf content" | Out-File -FilePath "test_invoice.pdf" -Encoding utf8

# 上传文件
$filePath = "test_invoice.pdf"
$uri = "http://localhost:8000/api/v1/invoices/upload"

$form = @{
    file = Get-Item -Path $filePath
}

Invoke-RestMethod -Uri $uri `
  -Method Post `
  -Headers $headers `
  -Form $form
```

#### 使用Swagger UI

1. 访问 http://localhost:8000/docs
2. 找到 `POST /api/v1/invoices/upload`
3. 点击 "Try it out"
4. 点击 "Choose File" 选择文件
5. 点击 "Execute"
6. 查看响应，应该返回成功消息和票据编号

**预期响应：**
```json
{
  "message": "文件上传成功，票据编号: INV-20240115120000-xxxxxxxx"
}
```

**保存返回的票据ID**，后续测试会用到。

---

### 2. 查询票据列表

```bash
# 使用curl
curl -X GET "http://localhost:8000/api/v1/invoices/query?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

```powershell
# 使用PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/invoices/query?skip=0&limit=10" `
  -Method Get `
  -Headers $headers
```

**预期响应：**
```json
{
  "data": [
    {
      "id": "uuid-here",
      "invoice_no": "INV-20240115120000-xxxxxxxx",
      "invoice_type": "未知",
      "recognition_status": "pending",
      "review_status": "pending",
      ...
    }
  ],
  "count": 1,
  "skip": 0,
  "limit": 10
}
```

---

### 3. 获取票据详情

```bash
# 替换 {invoice_id} 为实际的票据ID
curl -X GET "http://localhost:8000/api/v1/invoices/{invoice_id}" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 4. 更新票据信息

```bash
curl -X PATCH "http://localhost:8000/api/v1/invoices/{invoice_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000.00,
    "tax_amount": 130.00,
    "total_amount": 1130.00,
    "supplier_name": "测试供应商有限公司",
    "supplier_tax_no": "91110000123456789X",
    "buyer_name": "测试购买方有限公司",
    "buyer_tax_no": "91110000987654321Y"
  }'
```

```powershell
$body = @{
    amount = 1000.00
    tax_amount = 130.00
    total_amount = 1130.00
    supplier_name = "测试供应商有限公司"
    supplier_tax_no = "91110000123456789X"
    buyer_name = "测试购买方有限公司"
    buyer_tax_no = "91110000987654321Y"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/invoices/{invoice_id}" `
  -Method Patch `
  -Headers $headers `
  -Body $body `
  -ContentType "application/json"
```

---

### 5. 创建识别任务

首先需要创建模板：

```bash
# 创建模板
curl -X POST "http://localhost:8000/api/v1/templates/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "增值税发票模板",
    "type": "增值税发票",
    "description": "标准增值税发票模板",
    "version": "1.0.0"
  }'
```

保存返回的模板ID，然后创建识别任务：

```bash
curl -X POST "http://localhost:8000/api/v1/invoices/recognition-tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "{invoice_id}",
    "template_id": "{template_id}",
    "priority": 5
  }'
```

---

### 6. 启动识别任务

```bash
curl -X POST "http://localhost:8000/api/v1/invoices/recognition-tasks/{task_id}/start" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 7. 获取待审核票据

```bash
curl -X GET "http://localhost:8000/api/v1/invoices/review/pending?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 8. 审核通过票据

```bash
curl -X POST "http://localhost:8000/api/v1/invoices/review/{invoice_id}/approve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "审核通过，数据完整"
  }'
```

---

### 9. 审核拒绝票据

```bash
curl -X POST "http://localhost:8000/api/v1/invoices/review/{invoice_id}/reject" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "数据不完整，需要补充"
  }'
```

---

### 10. 模板管理测试

#### 获取模板列表

```bash
curl -X GET "http://localhost:8000/api/v1/templates/?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

#### 获取模板详情

```bash
curl -X GET "http://localhost:8000/api/v1/templates/{template_id}" \
  -H "Authorization: Bearer $TOKEN"
```

#### 更新模板

```bash
curl -X PATCH "http://localhost:8000/api/v1/templates/{template_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "更新后的描述",
    "status": "active"
  }'
```

#### 删除模板

```bash
curl -X DELETE "http://localhost:8000/api/v1/templates/{template_id}" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 11. 配置管理测试

#### 获取OCR配置

```bash
curl -X GET "http://localhost:8000/api/v1/config/ocr" \
  -H "Authorization: Bearer $TOKEN"
```

#### 更新OCR配置

```bash
curl -X POST "http://localhost:8000/api/v1/config/ocr" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "tesseract",
    "language": "chi_sim+eng",
    "enable_preprocessing": true,
    "enable_postprocessing": true,
    "confidence_threshold": 80,
    "max_file_size": 10,
    "supported_formats": ["pdf", "jpg", "png"]
  }'
```

#### 获取识别规则

```bash
curl -X GET "http://localhost:8000/api/v1/config/recognition-rules?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

#### 创建识别规则

```bash
curl -X POST "http://localhost:8000/api/v1/config/recognition-rules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "金额验证规则",
    "rule_type": "validation",
    "rule_definition": "{\"min\": 0, \"max\": 999999999.99}",
    "field_name": "amount",
    "is_active": true,
    "priority": 10,
    "remark": "验证金额范围"
  }'
```

---

## 前端测试

### 1. 启动前端服务

```bash
cd frontend
npm install  # 首次运行
npm run dev
```

### 2. 测试流程

1. **登录测试**
   - 访问 http://localhost:5173
   - 使用测试账号登录

2. **票据上传测试**
   - 导航到"票据管理" > "票据上传"
   - 拖拽或选择文件上传
   - 验证上传成功提示

3. **票据查询测试**
   - 导航到"票据管理" > "票据查询"
   - 输入查询条件
   - 验证结果列表显示

4. **票据审核测试**
   - 导航到"票据管理" > "票据审核"
   - 查看待审核列表
   - 执行审核操作（通过/拒绝）

5. **模板管理测试**
   - 导航到"模板管理" > "模板配置"
   - 创建、编辑、删除模板

6. **系统配置测试**
   - 导航到"系统配置" > "OCR配置"
   - 修改配置并保存

---

## 集成测试

### 完整业务流程测试

#### 场景1：完整的票据识别流程

1. **上传票据文件**
   ```bash
   POST /api/v1/invoices/upload
   ```
   - 保存返回的票据ID

2. **创建识别任务**
   ```bash
   POST /api/v1/invoices/recognition-tasks
   ```
   - 使用票据ID和模板ID

3. **启动识别任务**
   ```bash
   POST /api/v1/invoices/recognition-tasks/{task_id}/start
   ```

4. **查询识别结果**
   ```bash
   GET /api/v1/invoices/recognition-results?invoice_id={invoice_id}
   ```

5. **更新票据信息**（根据识别结果）
   ```bash
   PATCH /api/v1/invoices/{invoice_id}
   ```

6. **提交审核**
   ```bash
   POST /api/v1/invoices/review/{invoice_id}/approve
   ```

#### 场景2：模板训练流程

1. **创建模板**
   ```bash
   POST /api/v1/templates/
   ```

2. **添加模板字段**
   ```bash
   POST /api/v1/templates/{template_id}/fields
   ```

3. **启动训练**
   ```bash
   POST /api/v1/templates/{template_id}/train
   ```

4. **查询训练任务**
   ```bash
   GET /api/v1/templates/{template_id}/training-tasks
   ```

---

## 自动化测试

### 运行单元测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest app/tests/api/routes/test_invoice.py -v

# 运行特定测试用例
pytest app/tests/api/routes/test_invoice.py::test_query_invoices -v

# 显示覆盖率
pytest --cov=app --cov-report=html
```

### 测试覆盖率报告

```bash
# 生成HTML报告
pytest --cov=app --cov-report=html

# 查看报告
# 打开 htmlcov/index.html
```

---

## 使用Postman测试

### 1. 导入API集合

1. 打开Postman
2. 点击 "Import"
3. 选择 "Raw text"
4. 粘贴以下JSON（需要根据实际情况调整）：

```json
{
  "info": {
    "name": "票据识别系统API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000",
      "type": "string"
    },
    {
      "key": "token",
      "value": "",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "登录",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/x-www-form-urlencoded"
          }
        ],
        "body": {
          "mode": "urlencoded",
          "urlencoded": [
            {
              "key": "username",
              "value": "test@example.com"
            },
            {
              "key": "password",
              "value": "test123456"
            }
          ]
        },
        "url": {
          "raw": "{{base_url}}/api/v1/login/access-token",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "auth", "login"]
        }
      }
    },
    {
      "name": "上传票据",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{token}}"
          }
        ],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "file",
              "type": "file",
              "src": []
            }
          ]
        },
        "url": {
          "raw": "{{base_url}}/api/v1/invoices/upload",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "invoices", "upload"]
        }
      }
    }
  ]
}
```

### 2. 设置环境变量

在Postman中创建环境：
- `base_url`: http://localhost:8000
- `token`: (从登录响应中获取)

### 3. 测试脚本

在登录请求的 "Tests" 标签中添加：

```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("token", jsonData.access_token);
}
```

---

## 常见问题

### 1. 数据库连接失败

**错误信息：**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决方案：**
- 检查PostgreSQL服务是否启动
- 验证数据库连接配置（用户名、密码、主机、端口）
- 检查防火墙设置

### 2. 迁移失败

**错误信息：**
```
alembic.util.exc.CommandError: Target database is not up to date
```

**解决方案：**
```bash
# 查看迁移历史
alembic history

# 检查当前版本
alembic current

# 手动升级
alembic upgrade head
```

### 3. Token过期

**错误信息：**
```
401 Unauthorized
```

**解决方案：**
- 重新登录获取新token
- 检查token是否正确设置
- 验证用户账号是否激活

### 4. 文件上传失败

**错误信息：**
```
400 Bad Request: 不支持的文件类型
```

**解决方案：**
- 确保文件类型为PDF、JPG或PNG
- 检查文件大小是否超过10MB
- 验证文件是否损坏

### 5. 外键约束错误

**错误信息：**
```
IntegrityError: foreign key constraint failed
```

**解决方案：**
- 确保引用的记录存在（如用户、模板等）
- 检查外键关系是否正确

### 6. 端口被占用

**错误信息：**
```
Address already in use
```

**解决方案：**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

---

## 测试检查清单

### 功能测试

- [ ] 用户登录/登出
- [ ] 票据文件上传
- [ ] 票据查询（各种条件）
- [ ] 票据详情查看
- [ ] 票据信息更新
- [ ] 识别任务创建
- [ ] 识别任务启动
- [ ] 识别结果查询
- [ ] 待审核列表查询
- [ ] 审核通过
- [ ] 审核拒绝
- [ ] 模板创建
- [ ] 模板查询
- [ ] 模板更新
- [ ] 模板删除
- [ ] OCR配置获取/更新
- [ ] 识别规则管理

### 边界测试

- [ ] 空文件上传
- [ ] 超大文件上传（>10MB）
- [ ] 不支持的文件类型
- [ ] 无效的票据ID
- [ ] 无效的模板ID
- [ ] 空查询条件
- [ ] 分页边界（skip=0, limit=0等）

### 错误处理测试

- [ ] 未授权访问（无token）
- [ ] Token过期
- [ ] 无效的请求数据
- [ ] 数据库连接失败
- [ ] 文件系统错误

### 性能测试

- [ ] 批量上传（10个文件）
- [ ] 大量数据查询（1000+记录）
- [ ] 并发请求测试

---

## 测试报告模板

```markdown
# 测试报告

**测试日期：** 2024-01-15
**测试人员：** [姓名]
**测试环境：** [开发/测试/生产]

## 测试结果摘要

- 总测试用例：XX
- 通过：XX
- 失败：XX
- 跳过：XX
- 通过率：XX%

## 详细结果

### API测试
- [ ] 票据上传：通过/失败
- [ ] 票据查询：通过/失败
- ...

### 前端测试
- [ ] 登录功能：通过/失败
- [ ] 上传界面：通过/失败
- ...

## 发现的问题

1. [问题描述]
   - 严重程度：高/中/低
   - 状态：已修复/待修复

## 建议

1. [建议内容]
```

---

## 联系支持

如遇到问题，请：
1. 查看日志文件
2. 检查数据库状态
3. 参考项目文档
4. 联系开发团队

---

**最后更新：** 2024-01-15

