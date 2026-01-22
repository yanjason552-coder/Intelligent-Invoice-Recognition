# 本地开发环境启动脚本 (Windows PowerShell)
# 使用方法: .\scripts\dev-local.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Starting local development environment..." -ForegroundColor Green

# Check if in correct directory
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Cyan
try {
    $null = docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed"
    }
} catch {
    Write-Host ""
    Write-Host "Error: Docker is not running or not accessible." -ForegroundColor Red
    Write-Host "Please ensure Docker Desktop is started and try again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To start Docker Desktop:" -ForegroundColor Cyan
    Write-Host "  1. Open Docker Desktop application" -ForegroundColor White
    Write-Host "  2. Wait for Docker to fully start (check system tray icon)" -ForegroundColor White
    Write-Host "  3. Verify Docker is running: docker info" -ForegroundColor White
    Write-Host "  4. Run this script again" -ForegroundColor White
    Write-Host ""
    exit 1
}
Write-Host "Docker is running" -ForegroundColor Green

# Load .env file if it exists
if (Test-Path ".env") {
    Write-Host "Loading environment variables from .env file..." -ForegroundColor Cyan
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            if ($key -and $value) {
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
    }
}

# Set required environment variables for Docker Compose
# These are needed even if we only start db and redis, because docker compose
# validates the entire configuration file
if (-not $env:STACK_NAME) { $env:STACK_NAME = "local-dev" }
if (-not $env:DOCKER_IMAGE_BACKEND) { $env:DOCKER_IMAGE_BACKEND = "app-backend" }
if (-not $env:DOCKER_IMAGE_FRONTEND) { $env:DOCKER_IMAGE_FRONTEND = "app-frontend" }
if (-not $env:DOMAIN) { $env:DOMAIN = "localhost" }
if (-not $env:TAG) { $env:TAG = "latest" }
if (-not $env:POSTGRES_USER) { $env:POSTGRES_USER = "postgres" }
if (-not $env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD = "changethis" }
if (-not $env:POSTGRES_DB) { $env:POSTGRES_DB = "app" }
if (-not $env:FRONTEND_HOST) { $env:FRONTEND_HOST = "http://localhost:5173" }
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = "changethis-secret-key-for-local-dev" }
if (-not $env:FIRST_SUPERUSER) { $env:FIRST_SUPERUSER = "admin@example.com" }
if (-not $env:FIRST_SUPERUSER_PASSWORD) { $env:FIRST_SUPERUSER_PASSWORD = "changethis" }
if (-not $env:SMTP_USER) { $env:SMTP_USER = "" }
if (-not $env:SMTP_PASSWORD) { $env:SMTP_PASSWORD = "" }
if (-not $env:SENTRY_DSN) { $env:SENTRY_DSN = "" }
if (-not $env:CI) { $env:CI = "" }

# Start database and redis services
Write-Host "Starting database and redis services..." -ForegroundColor Yellow
docker compose up db redis -d

# Wait for database to start
Write-Host "Waiting for database to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if database is ready
Write-Host "Checking database connection..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$dbReady = $false

while (-not $dbReady -and $attempt -lt $maxAttempts) {
    $attempt++
    Write-Host "Waiting for database ready... (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    docker compose exec -T db pg_isready -U postgres 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $dbReady = $true
    }
}

if (-not $dbReady) {
    Write-Host "Error: Database startup timeout, please check Docker container status" -ForegroundColor Red
    exit 1
}

Write-Host "Database is ready" -ForegroundColor Green

# Get project root directory
$projectRoot = Get-Location

# Start backend development server
Write-Host "Starting backend development server..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    param ($backendPath)
    Set-Location $backendPath
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} -ArgumentList (Join-Path $projectRoot "backend")

# Start frontend development server
Write-Host "Starting frontend development server..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    param ($frontendPath)
    Set-Location $frontendPath
    npm run dev
} -ArgumentList (Join-Path $projectRoot "frontend")

Write-Host ""
Write-Host "Local development environment started!" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "   - Frontend code changes will auto-reload" -ForegroundColor White
Write-Host "   - Backend code changes will auto-restart" -ForegroundColor White
Write-Host "   - Press Ctrl+C to stop all services" -ForegroundColor White
Write-Host ""

# Wait for user interrupt
try {
    while ($true) {
        Start-Sleep -Seconds 1
        # Check if jobs are still running
        if ($backendJob.State -eq "Failed") {
            Write-Host "Error: Backend service failed to start, please check logs" -ForegroundColor Red
            break
        }
        if ($frontendJob.State -eq "Failed") {
            Write-Host "Error: Frontend service failed to start, please check logs" -ForegroundColor Red
            break
        }
    }
}
finally {
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Receive-Job $backendJob -ErrorAction SilentlyContinue | Out-Null
    Receive-Job $frontendJob -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    docker compose down
    Write-Host "Services stopped" -ForegroundColor Green
}
