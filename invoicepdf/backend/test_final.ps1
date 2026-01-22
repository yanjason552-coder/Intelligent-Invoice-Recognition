param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Username = "test@example.com",
    [string]$Password = "test123456"
)

Write-Host "Script started" -ForegroundColor Green

$separator = [char]38
Write-Host "Separator character code: 38" -ForegroundColor Gray

# 检查后端服务是否运行
Write-Host "`nChecking backend service..." -ForegroundColor Yellow
try {
    $healthCheck = Invoke-WebRequest -Uri "$BaseUrl/docs" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "Backend service is running" -ForegroundColor Green
} catch {
    Write-Host "Backend service is not accessible at $BaseUrl" -ForegroundColor Red
    Write-Host "Please start the backend service: cd backend && uvicorn app.main:app --reload --port 8000" -ForegroundColor Yellow
    exit 1
}

$loginBody = @{
    username = $Username
    password = $Password
}

Write-Host "`nAttempting login to: $BaseUrl/api/v1/login/access-token" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/login/access-token" `
        -Method Post `
        -ContentType "application/x-www-form-urlencoded" `
        -Body $loginBody `
        -ErrorAction Stop
    
    $token = $response.access_token
    Write-Host "Login successful, token length: $($token.Length)" -ForegroundColor Green
    
    $headers = @{ "Authorization" = "Bearer $token" }
    
    $queryParams = @{ skip = 0; limit = 10 }
    $queryParts = @()
    foreach ($key in $queryParams.Keys) {
        $queryParts += "$key=$($queryParams[$key])"
    }
    $queryString = $queryParts -join $separator
    $queryUrl = "$BaseUrl/api/v1/invoices/query?$queryString"
    
    Write-Host "`nQuery URL: $queryUrl" -ForegroundColor Gray
    
    $invoices = Invoke-RestMethod -Uri $queryUrl -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "Found $($invoices.count) invoices" -ForegroundColor Green
    
} catch {
    Write-Host "`nError: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        
        # 尝试读取错误响应体
        try {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
            $stream.Close()
            
            Write-Host "`nError details:" -ForegroundColor Yellow
            Write-Host $responseBody -ForegroundColor Gray
            
            # 尝试解析 JSON 错误
            try {
                $errorObj = $responseBody | ConvertFrom-Json
                if ($errorObj.detail) {
                    Write-Host "`nDetail: $($errorObj.detail)" -ForegroundColor Yellow
                }
            } catch {
                # 不是 JSON，直接显示
            }
        } catch {
            Write-Host "Could not read error response body" -ForegroundColor Gray
        }
    }
    
    # 提供诊断建议
    Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check if backend service is running" -ForegroundColor Gray
    Write-Host "2. Check backend logs for more details" -ForegroundColor Gray
    Write-Host "3. Verify user exists: $Username" -ForegroundColor Gray
    Write-Host "4. Check database connection" -ForegroundColor Gray
}

Write-Host "`nScript completed" -ForegroundColor Green
