# 快速测试指南

## 🚀 5分钟快速测试

### 1. 启动服务

```bash
# 终端1：启动后端
cd backend
uvicorn app.main:app --reload --port 8000

# 终端2：启动前端（可选）
cd frontend
npm run dev
```

### 2. 获取Token

访问 http://localhost:8000/docs，使用 `/api/v1/login/access-token` 登录获取token。

或使用curl：

```bash
# Windows PowerShell
$loginBody = @{username="test@example.com"; password="test123456"}
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/login/access-token" `
  -Method Post -ContentType "application/x-www-form-urlencoded" -Body $loginBody
$token = $response.access_token
```

### 3. 测试核心功能

#### 测试1：上传文件

```powershell
# 创建测试文件
"test content" | Out-File test.pdf

# 上传
$headers = @{ "Authorization" = "Bearer $token" }
$form = @{ file = Get-Item test.pdf }
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/invoices/upload" `
  -Method Post -Headers $headers -Form $form
```

#### 测试2：查询票据

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/invoices/query" `
  -Method Get -Headers $headers
```

#### 测试3：获取OCR配置

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/config/ocr" `
  -Method Get -Headers $headers
```

### 4. 验证结果

所有请求应返回200状态码，检查响应数据是否正确。

---

## 📝 完整测试脚本

保存为 `test_api.ps1`：

```powershell
# 配置
$baseUrl = "http://localhost:8000"
$username = "test@example.com"
$password = "test123456"

# 1. 登录
Write-Host "1. 登录..." -ForegroundColor Yellow
$loginBody = "username=$username&password=$password"
$loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/login/access-token" `
    -Method Post -ContentType "application/x-www-form-urlencoded" -Body $loginBody
$token = $loginResponse.access_token
$headers = @{ "Authorization" = "Bearer $token" }
Write-Host "✓ 登录成功" -ForegroundColor Green

# 2. 查询票据
Write-Host "2. 查询票据..." -ForegroundColor Yellow
$invoices = Invoke-RestMethod -Uri "$baseUrl/api/v1/invoices/query?skip=0&limit=10" `
    -Method Get -Headers $headers
Write-Host "✓ 找到 $($invoices.count) 条记录" -ForegroundColor Green

# 3. 获取OCR配置
Write-Host "3. 获取OCR配置..." -ForegroundColor Yellow
$config = Invoke-RestMethod -Uri "$baseUrl/api/v1/config/ocr" `
    -Method Get -Headers $headers
Write-Host "✓ OCR Provider: $($config.provider)" -ForegroundColor Green

# 4. 获取模板列表
Write-Host "4. 获取模板列表..." -ForegroundColor Yellow
$templates = Invoke-RestMethod -Uri "$baseUrl/api/v1/templates/?skip=0&limit=10" `
    -Method Get -Headers $headers
Write-Host "✓ 找到 $($templates.count) 个模板" -ForegroundColor Green

Write-Host "`n所有测试通过！" -ForegroundColor Green
```

运行：
```powershell
.\test_api.ps1
```

