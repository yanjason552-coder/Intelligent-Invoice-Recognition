param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Email = "test@example.com",
    [string]$Password = "test123456",
    [string]$FullName = "Test User"
)

Write-Host "=== Create Test User ===" -ForegroundColor Cyan
Write-Host ""

# Check if backend is running
Write-Host "[1/3] Checking backend service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/docs" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  [OK] Backend service is running" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Backend service is not accessible" -ForegroundColor Red
    Write-Host "  Please start backend service first" -ForegroundColor Yellow
    exit 1
}

# Try to create user using signup endpoint
Write-Host "[2/3] Creating user via signup endpoint..." -ForegroundColor Yellow
try {
    $userData = @{
        email = $Email
        password = $Password
        full_name = $FullName
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/users/signup" `
        -Method Post `
        -ContentType "application/json" `
        -Body $userData `
        -ErrorAction Stop
    
    Write-Host "  [OK] User created successfully!" -ForegroundColor Green
    Write-Host "  Email: $($response.email)" -ForegroundColor Gray
    Write-Host "  Full Name: $($response.full_name)" -ForegroundColor Gray
    Write-Host "  ID: $($response.id)" -ForegroundColor Gray
    
} catch {
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode
        if ($statusCode -eq 400) {
            Write-Host "  [INFO] User may already exist (400 Bad Request)" -ForegroundColor Yellow
            Write-Host "  Attempting to login to verify..." -ForegroundColor Gray
            
            # Try to login to verify user exists
            try {
                $loginBody = @{
                    username = $Email
                    password = $Password
                }
                
                $loginResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/login/access-token" `
                    -Method Post `
                    -ContentType "application/x-www-form-urlencoded" `
                    -Body $loginBody `
                    -ErrorAction Stop
                
                Write-Host "  [OK] User exists and can login!" -ForegroundColor Green
                Write-Host "  Token received: $($loginResponse.access_token.Substring(0, 20))..." -ForegroundColor Gray
                
            } catch {
                Write-Host "  [ERROR] User exists but login failed" -ForegroundColor Red
                Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
                Write-Host "`n  Possible issues:" -ForegroundColor Cyan
                Write-Host "  1. Password is incorrect" -ForegroundColor Gray
                Write-Host "  2. User is inactive" -ForegroundColor Gray
                Write-Host "  3. Database issue" -ForegroundColor Gray
            }
        } else {
            Write-Host "  [ERROR] Failed to create user: $($_.Exception.Message)" -ForegroundColor Red
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $responseBody = $reader.ReadToEnd()
                $reader.Close()
                $stream.Close()
                Write-Host "  Error details: $responseBody" -ForegroundColor Yellow
            } catch {}
        }
    } else {
        Write-Host "  [ERROR] Failed to create user: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n[3/3] Summary" -ForegroundColor Yellow
Write-Host "  Email: $Email" -ForegroundColor Gray
Write-Host "  Password: $Password" -ForegroundColor Gray
Write-Host "  You can now use these credentials to login" -ForegroundColor Gray
Write-Host ""


