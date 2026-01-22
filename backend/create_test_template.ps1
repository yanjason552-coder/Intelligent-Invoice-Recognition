# 创建测试模板脚本
# 用于测试模板匹配功能

$BaseUrl = "http://localhost:8000"
$Username = "test@example.com"
$Password = "test123456"

Write-Host "=== Create Test Template ===" -ForegroundColor Cyan

# 1. 登录获取token
Write-Host "`n[1/3] Logging in..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = $Username
        password = $Password
    }
    
    $loginResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/login/access-token" `
        -Method POST `
        -ContentType "application/x-www-form-urlencoded" `
        -Body $loginBody
    
    $token = $loginResponse.access_token
    Write-Host "[OK] Login successful, token length: $($token.Length)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. 检查是否已有模板
Write-Host "`n[2/3] Checking existing templates..." -ForegroundColor Yellow
try {
    $headers = @{
        Authorization = "Bearer $token"
    }
    
    $templatesResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/templates/?skip=0&limit=10" `
        -Method GET `
        -Headers $headers
    
    if ($templatesResponse.count -gt 0) {
        Write-Host "[INFO] Found $($templatesResponse.count) existing templates:" -ForegroundColor Cyan
        foreach ($template in $templatesResponse.data) {
            Write-Host "  - $($template.name) (Type: $($template.type), Status: $($template.status))" -ForegroundColor Gray
        }
        
        $activeTemplates = $templatesResponse.data | Where-Object { $_.status -eq "active" }
        if ($activeTemplates.Count -gt 0) {
            Write-Host "[OK] Found $($activeTemplates.Count) active template(s), no need to create" -ForegroundColor Green
            exit 0
        }
    } else {
        Write-Host "[INFO] No templates found" -ForegroundColor Gray
    }
} catch {
    Write-Host "[WARNING] Failed to check templates: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 3. 创建测试模板
Write-Host "`n[3/3] Creating test templates..." -ForegroundColor Yellow

$templates = @(
    @{
        name = "增值税发票模板"
        type = "增值税发票"
        description = "用于识别增值税专用发票和普通发票"
        version = "1.0.0"
    },
    @{
        name = "普通发票模板"
        type = "普通发票"
        description = "用于识别普通发票"
        version = "1.0.0"
    },
    @{
        name = "收据模板"
        type = "收据"
        description = "用于识别收据"
        version = "1.0.0"
    }
)

$createdCount = 0
foreach ($templateData in $templates) {
    try {
        $body = $templateData | ConvertTo-Json
        
        $createResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/templates/" `
            -Method POST `
            -Headers $headers `
            -ContentType "application/json" `
            -Body $body
        
        Write-Host "[OK] Created template: $($createResponse.name) (ID: $($createResponse.id))" -ForegroundColor Green
        $createdCount++
    } catch {
        if ($_.Exception.Response.StatusCode -eq 400 -and $_.ErrorDetails.Message -like "*已存在*") {
            Write-Host "[SKIP] Template already exists: $($templateData.name)" -ForegroundColor Yellow
        } else {
            Write-Host "[ERROR] Failed to create template '$($templateData.name)': $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Created $createdCount template(s)" -ForegroundColor Green
Write-Host "`nYou can now test template matching by uploading files with names containing:" -ForegroundColor Cyan
Write-Host "  - '增值税' or 'VAT' for 增值税发票模板" -ForegroundColor Gray
Write-Host "  - '普通发票' or '普通' for 普通发票模板" -ForegroundColor Gray
Write-Host "  - '收据' or 'receipt' for 收据模板" -ForegroundColor Gray

