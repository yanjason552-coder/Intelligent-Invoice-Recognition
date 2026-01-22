param(
    [string]$BaseUrl = "http://localhost:8000"
)

Write-Host "=== Database Connection Check ===" -ForegroundColor Cyan
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

# Check database connection via API
Write-Host "[2/3] Checking database connection..." -ForegroundColor Yellow
Write-Host "  Note: This requires a valid user to test database connection" -ForegroundColor Gray
Write-Host "  If login fails with 500 error, check backend logs for database errors" -ForegroundColor Gray

# Try to get OpenAPI schema (this should work without auth)
Write-Host "[3/3] Checking API availability..." -ForegroundColor Yellow
try {
    $schema = Invoke-RestMethod -Uri "$BaseUrl/openapi.json" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  [OK] API is accessible" -ForegroundColor Green
    Write-Host "  API Title: $($schema.info.title)" -ForegroundColor Gray
} catch {
    Write-Host "  [WARNING] Could not fetch API schema: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n=== Recommendations ===" -ForegroundColor Cyan
Write-Host "1. Check backend console logs for detailed error messages" -ForegroundColor Gray
Write-Host "2. Verify database is running and accessible" -ForegroundColor Gray
Write-Host "3. Check if database migrations have been applied" -ForegroundColor Gray
Write-Host "4. Verify user exists in database: test@example.com" -ForegroundColor Gray
Write-Host "5. Check .env file for correct DATABASE_URL" -ForegroundColor Gray
Write-Host ""


