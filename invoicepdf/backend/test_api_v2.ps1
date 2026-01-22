# 票据识别系统API测试脚本 V2
# 完全避免特殊字符的版本

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Username = "test@example.com",
    [string]$Password = "test123456"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  票据识别系统 API 测试脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 定义分隔符字符（使用ASCII码）
$querySeparator = [char]38

# 辅助函数：构建查询字符串
function Build-QueryString {
    param([hashtable]$Params)
    $parts = @()
    foreach ($key in $Params.Keys) {
        $value = $Params[$key]
        $parts += "$key=$value"
    }
    if ($parts.Count -gt 0) {
        return $parts -join $querySeparator
    }
    return ""
}

# 1. 登录
Write-Host "[INFO] 步骤1: 登录获取Token..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = $Username
        password = $Password
    }
    
    $loginResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/login/access-token" `
        -Method Post `
        -ContentType "application/x-www-form-urlencoded" `
        -Body $loginBody `
        -ErrorAction Stop
    
    $token = $loginResponse.access_token
    $headers = @{ "Authorization" = "Bearer $token" }
    Write-Host "[OK] 登录成功" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] 登录失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. 查询票据
Write-Host "[INFO] 步骤2: 查询票据列表..." -ForegroundColor Yellow
try {
    $queryParams = @{ skip = 0; limit = 10 }
    $queryString = Build-QueryString -Params $queryParams
    $queryUrl = "$BaseUrl/api/v1/invoices/query?$queryString"
    
    $invoices = Invoke-RestMethod -Uri $queryUrl -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "[OK] 查询成功，找到 $($invoices.count) 条记录" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] 查询失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# 3. 获取OCR配置
Write-Host "[INFO] 步骤3: 获取OCR配置..." -ForegroundColor Yellow
try {
    $config = Invoke-RestMethod -Uri "$BaseUrl/api/v1/config/ocr" -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "[OK] 获取配置成功" -ForegroundColor Green
    Write-Host "  Provider: $($config.provider)" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] 获取配置失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

