# 检查用户是否存在并验证登录

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Email = "test@example.com",
    [string]$Password = "test123456"
)

Write-Host "=== User Check and Login Test ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check backend service
Write-Host "[1/3] Checking backend service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/docs" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  [OK] Backend service is running" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Backend service is not accessible" -ForegroundColor Red
    exit 1
}

# Step 2: Try to login
Write-Host "[2/3] Attempting login..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = $Email
        password = $Password
    }
    
    Write-Host "  Email: $Email" -ForegroundColor Gray
    Write-Host "  Password: [REDACTED]" -ForegroundColor Gray
    
    $loginResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/login/access-token" `
        -Method Post `
        -ContentType "application/x-www-form-urlencoded" `
        -Body $loginBody `
        -ErrorAction Stop
    
    $token = $loginResponse.access_token
    Write-Host "  [OK] Login successful!" -ForegroundColor Green
    Write-Host "  Token length: $($token.Length)" -ForegroundColor Gray
    Write-Host "  Token type: $($loginResponse.token_type)" -ForegroundColor Gray
    
} catch {
    Write-Host "  [ERROR] Login failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode
        Write-Host "  Status Code: $statusCode" -ForegroundColor Yellow
        
        try {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
            $stream.Close()
            
            Write-Host "  Response Body: $responseBody" -ForegroundColor Yellow
            
            try {
                $errorObj = $responseBody | ConvertFrom-Json
                if ($errorObj.detail) {
                    Write-Host "  Detail: $($errorObj.detail)" -ForegroundColor Red
                }
            } catch {
                Write-Host "  (Could not parse as JSON)" -ForegroundColor Gray
            }
        } catch {
            Write-Host "  (Could not read response body)" -ForegroundColor Gray
        }
    }
    
    Write-Host "`n  Troubleshooting:" -ForegroundColor Cyan
    Write-Host "  1. Check if user exists in database" -ForegroundColor Gray
    Write-Host "  2. Verify password is correct" -ForegroundColor Gray
    Write-Host "  3. Check backend logs for detailed error" -ForegroundColor Gray
    Write-Host "  4. Try creating user: .\create_test_user.ps1" -ForegroundColor Gray
    
    exit 1
}

# Step 3: Test token
Write-Host "[3/3] Testing token..." -ForegroundColor Yellow
try {
    $headers = @{ "Authorization" = "Bearer $token" }
    $userResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/login/test-token" `
        -Method Post `
        -Headers $headers `
        -ErrorAction Stop
    
    Write-Host "  [OK] Token is valid" -ForegroundColor Green
    Write-Host "  User Email: $($userResponse.email)" -ForegroundColor Gray
    Write-Host "  User ID: $($userResponse.id)" -ForegroundColor Gray
    Write-Host "  Is Active: $($userResponse.is_active)" -ForegroundColor Gray
    Write-Host "  Is Superuser: $($userResponse.is_superuser)" -ForegroundColor Gray
    
} catch {
    Write-Host "  [ERROR] Token test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "User credentials are valid and can login successfully!" -ForegroundColor Green
Write-Host ""


