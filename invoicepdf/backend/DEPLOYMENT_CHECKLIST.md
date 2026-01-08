# 票据识别系统 - 部署检查清单

## 已实现的功能

### ✅ 1. 文件唯一性校验
- **位置**: `backend/app/models/models_invoice.py` - `InvoiceFile` 模型
- **功能**: 基于文件内容哈希值（SHA256）进行唯一性校验
- **数据库迁移**: `11367c892248_add_file_hash_to_invoice_file.py`

### ✅ 2. 票据文件列表API
- **位置**: `backend/app/api/routes/invoice.py` - `get_invoice_files_list` 函数
- **路径**: `GET /api/v1/invoices/files/list`
- **功能**: 提供完整的文件列表，包含文件、票据、识别、审核等综合信息
- **响应模型**: `InvoiceFileListItem`

### ✅ 3. 模板自动匹配
- **位置**: `backend/app/services/template_matcher.py` - `TemplateMatcher` 类
- **功能**: 上传时自动匹配最合适的模板
- **集成**: 已集成到 `upload_invoice` 接口

## 部署步骤

### 步骤 1: 运行数据库迁移

```powershell
cd backend
python -m alembic upgrade head
```

**检查迁移状态**:
```powershell
python -m alembic current
```

**预期输出**: 应该显示 `11367c892248 (head)` 或更高版本

### 步骤 2: 验证代码文件

确认以下文件已创建/更新：

- ✅ `backend/app/models/models_invoice.py` - 包含 `file_hash` 字段和 `InvoiceFileListItem` 模型
- ✅ `backend/app/api/routes/invoice.py` - 包含文件唯一性校验、模板匹配和列表API
- ✅ `backend/app/services/template_matcher.py` - 模板匹配服务
- ✅ `backend/app/services/__init__.py` - 服务模块初始化
- ✅ `backend/app/alembic/versions/11367c892248_add_file_hash_to_invoice_file.py` - 数据库迁移文件

### 步骤 3: 重启后端服务

如果后端服务正在运行，需要重启以加载新代码：

```powershell
# 停止当前服务（Ctrl+C）
# 然后重新启动
cd backend
uvicorn app.main:app --reload --port 8000
```

### 步骤 4: 验证功能

#### 4.1 测试文件唯一性校验

```powershell
# 上传同一个文件两次，第二次应该返回错误
.\test_invoice_upload.ps1
```

#### 4.2 测试模板匹配

```powershell
# 上传文件，检查返回消息中是否包含模板匹配信息
# 预期: "文件上传成功，票据编号: XXX，已匹配模板: XXX（匹配度: XX%）"
```

#### 4.3 测试文件列表API

```powershell
# 调用文件列表API
$token = "your_token_here"
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/invoices/files/list?skip=0&limit=10" -Headers @{Authorization="Bearer $token"}
$response | ConvertTo-Json -Depth 5
```

## 功能验证清单

- [ ] 数据库迁移已成功运行
- [ ] 后端服务已重启
- [ ] 文件上传功能正常
- [ ] 文件唯一性校验生效（重复上传返回错误）
- [ ] 模板自动匹配功能正常（上传时自动匹配模板）
- [ ] 文件列表API返回完整数据
- [ ] 日志中可以看到模板匹配信息

## 常见问题

### Q1: 迁移失败，提示 "Multiple head revisions"
**解决方案**: 运行合并迁移
```powershell
python -m alembic merge -m "merge_heads" heads
python -m alembic upgrade head
```

### Q2: 模板匹配返回 None
**原因**: 数据库中没有激活的模板
**解决方案**: 在模板管理模块中创建并激活模板

### Q3: 文件列表API返回空数据
**原因**: 可能没有上传过文件，或者查询条件太严格
**解决方案**: 先上传一些测试文件，然后查询

## 回滚步骤（如果需要）

如果部署出现问题，可以回滚：

```powershell
# 回滚到上一个版本
python -m alembic downgrade -1
```

**注意**: 回滚会删除 `file_hash` 字段，但不会删除已上传的文件。

