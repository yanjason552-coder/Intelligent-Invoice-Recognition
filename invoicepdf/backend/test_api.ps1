# 票据识别系统API测试脚本
# 使用方法: .\test_api.ps1

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Username = "test@example.com",
    [string]$Password = "test123456"
)

# #region agent log
$logPath = Join-Path $PSScriptRoot "..\.cursor\debug.log"
try {
    $logDir = Split-Path $logPath -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    $logEntry = @{
        sessionId = "debug-session"
        runId = "run1"
        hypothesisId = "A"
        location = "test_api.ps1:15"
        message = "Script started successfully"
        data = @{
            BaseUrl = $BaseUrl
            Username = $Username
            ScriptPath = $PSCommandPath
        }
        timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    } | ConvertTo-Json -Compress
    Add-Content -Path $logPath -Value $logEntry -ErrorAction SilentlyContinue
} catch {
    # 忽略日志错误
}
# #endregion

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  票据识别系统 API 测试脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 颜色函数
function Write-Success { 
    param($msg) 
    Write-Host "[OK] $msg" -ForegroundColor Green 
}

function Write-Error { 
    param($msg) 
    Write-Host "[ERROR] $msg" -ForegroundColor Red 
}

function Write-Info { 
    param($msg) 
    Write-Host "[INFO] $msg" -ForegroundColor Yellow 
}

# 辅助函数：构建查询字符串（使用字符代码，完全避免特殊字符）
function Build-UrlWithQuery {
    param(
        [string]$BaseUrl,
        [string]$Path,
        [hashtable]$QueryParams
    )
    
    # #region agent log
    try {
        $logPath = Join-Path $PSScriptRoot "..\.cursor\debug.log"
        $logEntry = @{
            sessionId = "debug-session"
            runId = "run1"
            hypothesisId = "C"
            location = "test_api.ps1:Build-UrlWithQuery"
            message = "Building URL with query params"
            data = @{
                BaseUrl = $BaseUrl
                Path = $Path
                ParamCount = $QueryParams.Count
            }
            timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        } | ConvertTo-Json -Compress
        Add-Content -Path $logPath -Value $logEntry -ErrorAction SilentlyContinue
    } catch {}
    # #endregion
    
    $uri = New-Object System.UriBuilder($BaseUrl)
    $uri.Path = $Path
    
    if ($QueryParams -and $QueryParams.Count -gt 0) {
        $queryParts = @()
        foreach ($key in $QueryParams.Keys) {
            $value = $QueryParams[$key]
            $encodedKey = [System.Uri]::EscapeDataString($key)
            $encodedValue = [System.Uri]::EscapeDataString([string]$value)
            $queryParts += "$encodedKey=$encodedValue"
        }
        $separatorChar = [char]38
        $uri.Query = $queryParts -join $separatorChar
    }
    
    return $uri.Uri.ToString()
}

# 1. 登录获取Token
Write-Info "步骤1: 登录获取Token..."
try {
    # #region agent log
    try {
        $logEntry = @{
            sessionId = "debug-session"
            runId = "run1"
            hypothesisId = "A"
            location = "test_api.ps1:95"
            message = "Constructing login body"
            data = @{
                Username = $Username
                PasswordLength = $Password.Length
            }
            timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        } | ConvertTo-Json -Compress
        Add-Content -Path $logPath -Value $logEntry -ErrorAction SilentlyContinue
    } catch {}
    # #endregion
    
    # 使用哈希表构建表单数据
    $loginBody = @{
        username = $Username
        password = $Password
    }
    
    # #region agent log
    try {
        $logEntry = @{
            sessionId = "debug-session"
            runId = "run1"
            hypothesisId = "A"
            location = "test_api.ps1:115"
            message = "Login body constructed as hashtable"
            data = @{
                HasUsername = $loginBody.ContainsKey('username')
                HasPassword = $loginBody.ContainsKey('password')
            }
            timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        } | ConvertTo-Json -Compress
        Add-Content -Path $logPath -Value $logEntry -ErrorAction SilentlyContinue
    } catch {}
    # #endregion
    
    $loginResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/login/access-token" `
        -Method Post `
        -ContentType "application/x-www-form-urlencoded" `
        -Body $loginBody `
        -ErrorAction Stop
    
    $token = $loginResponse.access_token
    $headers = @{ "Authorization" = "Bearer $token" }
    Write-Success "登录成功，Token已获取"
    
    # #region agent log
    try {
        $logEntry = @{
            sessionId = "debug-session"
            runId = "run1"
            hypothesisId = "A"
            location = "test_api.ps1:140"
            message = "Login successful"
            data = @{
                TokenLength = $token.Length
            }
            timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        } | ConvertTo-Json -Compress
        Add-Content -Path $logPath -Value $logEntry -ErrorAction SilentlyContinue
    } catch {}
    # #endregion
} catch {
    Write-Error "登录失败: $($_.Exception.Message)"
    Write-Host "请检查：" -ForegroundColor Yellow
    Write-Host "  1. 后端服务是否启动 ($BaseUrl)" -ForegroundColor Gray
    Write-Host "  2. 用户名和密码是否正确" -ForegroundColor Gray
    Write-Host "  3. 用户是否已创建" -ForegroundColor Gray
    exit 1
}

Write-Host ""

# 2. 查询票据列表
Write-Info "步骤2: 查询票据列表..."
try {
    $queryParams = @{
        skip = 0
        limit = 10
    }
    $queryUrl = Build-UrlWithQuery -BaseUrl $BaseUrl -Path "/api/v1/invoices/query" -QueryParams $queryParams
    
    # #region agent log
    try {
        $logEntry = @{
            sessionId = "debug-session"
            runId = "run1"
            hypothesisId = "B"
            location = "test_api.ps1:180"
            message = "Query URL constructed"
            data = @{
                QueryUrl = $queryUrl
            }
            timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        } | ConvertTo-Json -Compress
        Add-Content -Path $logPath -Value $logEntry -ErrorAction SilentlyContinue
    } catch {}
    # #endregion
    
    $invoices = Invoke-RestMethod -Uri $queryUrl `
        -Method Get `
        -Headers $headers `
        -ErrorAction Stop
    
    Write-Success "查询成功，找到 $($invoices.count) 条记录"
    if ($invoices.data.Count -gt 0) {
        Write-Host "  第一条记录: $($invoices.data[0].invoice_no)" -ForegroundColor Gray
    }
} catch {
    Write-Error "查询失败: $($_.Exception.Message)"
}

Write-Host ""

# 3. 获取OCR配置
Write-Info "步骤3: 获取OCR配置..."
try {
    $config = Invoke-RestMethod -Uri "$BaseUrl/api/v1/config/ocr" `
        -Method Get `
        -Headers $headers `
        -ErrorAction Stop
    
    Write-Success "获取配置成功"
    Write-Host "  Provider: $($config.provider)" -ForegroundColor Gray
    Write-Host "  Language: $($config.language)" -ForegroundColor Gray
    Write-Host "  Confidence Threshold: $($config.confidence_threshold)" -ForegroundColor Gray
} catch {
    Write-Error "获取配置失败: $($_.Exception.Message)"
}

Write-Host ""

# 4. 获取模板列表
Write-Info "步骤4: 获取模板列表..."
try {
    $templateParams = @{
        skip = 0
        limit = 10
    }
    $templateUrl = Build-UrlWithQuery -BaseUrl $BaseUrl -Path "/api/v1/templates/" -QueryParams $templateParams
    
    $templates = Invoke-RestMethod -Uri $templateUrl `
        -Method Get `
        -Headers $headers `
        -ErrorAction Stop
    
    Write-Success "查询成功，找到 $($templates.count) 个模板"
} catch {
    Write-Error "查询失败: $($_.Exception.Message)"
}

Write-Host ""

# 5. 获取待审核票据
Write-Info "步骤5: 获取待审核票据..."
try {
    $pendingParams = @{
        skip = 0
        limit = 10
    }
    $pendingUrl = Build-UrlWithQuery -BaseUrl $BaseUrl -Path "/api/v1/invoices/review/pending" -QueryParams $pendingParams
    
    $pending = Invoke-RestMethod -Uri $pendingUrl `
        -Method Get `
        -Headers $headers `
        -ErrorAction Stop
    
    Write-Success "查询成功，找到 $($pending.count) 条待审核记录"
} catch {
    Write-Error "查询失败: $($_.Exception.Message)"
}

Write-Host ""

# 6. 获取识别规则
Write-Info "步骤6: 获取识别规则..."
try {
    $rulesParams = @{
        skip = 0
        limit = 10
    }
    $rulesUrl = Build-UrlWithQuery -BaseUrl $BaseUrl -Path "/api/v1/config/recognition-rules" -QueryParams $rulesParams
    
    $rules = Invoke-RestMethod -Uri $rulesUrl `
        -Method Get `
        -Headers $headers `
        -ErrorAction Stop
    
    Write-Success "查询成功，找到 $($rules.count) 条规则"
} catch {
    Write-Error "查询失败: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示：" -ForegroundColor Yellow
Write-Host "  - 访问 $BaseUrl/docs 查看完整API文档" -ForegroundColor Gray
Write-Host "  - 详细测试手册: backend/TESTING_MANUAL.md" -ForegroundColor Gray
Write-Host ""
