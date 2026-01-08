param (
    [switch]$SkipInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "[INFO] Starting local stack without Docker..." -ForegroundColor Green

$projectRoot = Get-Location

if (-not (Test-Path "$projectRoot\backend\app\main.py") -or -not (Test-Path "$projectRoot\frontend\package.json")) {
    Write-Host "[ERROR] Please run this script from the repository root." -ForegroundColor Red
    exit 1
}

function Test-CommandExists {
    param ([string]$Name)
    return (Get-Command $Name -ErrorAction SilentlyContinue) -ne $null
}

function Install-BackendDeps {
    Push-Location "$projectRoot\backend"
    try {
        if (Test-CommandExists "uv") {
            Write-Host "[STEP] Installing backend deps with uv..." -ForegroundColor Yellow
            uv sync
        } elseif (Test-CommandExists "poetry") {
            Write-Host "[STEP] Installing backend deps with poetry..." -ForegroundColor Yellow
            poetry install
        } else {
            Write-Host "[WARN] Neither uv nor poetry is available. Please install backend dependencies manually." -ForegroundColor Yellow
        }
    } finally {
        Pop-Location
    }
}

function Install-FrontendDeps {
    Push-Location "$projectRoot\frontend"
    try {
        Write-Host "[STEP] Installing frontend deps via npm..." -ForegroundColor Yellow
        npm install
    } finally {
        Pop-Location
    }
}

if (-not $SkipInstall) {
    if (-not (Test-Path "$projectRoot\backend\.venv")) {
        Install-BackendDeps
    } else {
        Write-Host "[OK] backend/.venv already exists, skipping backend install." -ForegroundColor Cyan
    }

    if (-not (Test-Path "$projectRoot\frontend\node_modules")) {
        Install-FrontendDeps
    } else {
        Write-Host "[OK] frontend/node_modules already exists, skipping frontend install." -ForegroundColor Cyan
    }
} else {
    Write-Host "[SKIP] SkipInstall flag detected, skipping dependency checks." -ForegroundColor Yellow
}

function Get-BackendCommand {
    if (Test-CommandExists "uv") {
        return @{Exe = "uv"; Args = @("run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload")}
    } elseif (Test-CommandExists "poetry") {
        return @{Exe = "poetry"; Args = @("run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload")}
    } elseif (Test-CommandExists "python") {
        return @{Exe = "python"; Args = @("-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload")}
    }

    throw "No suitable command found to start the backend (uv/poetry/python)."
}

$backendCmd = Get-BackendCommand

Write-Host "[STEP] Starting backend dev server..." -ForegroundColor Yellow
$backendJob = Start-Job -ArgumentList $backendCmd, $projectRoot -ScriptBlock {
    param ($cmd, $root)
    Set-Location "$root\backend"
    & $cmd.Exe @($cmd.Args)
}

Write-Host "[STEP] Starting frontend dev server..." -ForegroundColor Yellow
$frontendJob = Start-Job -ArgumentList $projectRoot -ScriptBlock {
    param ($root)
    Set-Location "$root\frontend"
    npm run dev
}

Write-Host ""
Write-Host "[OK] Local services are running (no Docker)." -ForegroundColor Green
Write-Host "[URL] Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "[URL] Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "[URL] API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Ensure local PostgreSQL/Redis instances are up and match backend/.env connection values." -ForegroundColor Yellow
Write-Host "[INFO] Use .\scripts\dev-nodocker.ps1 -SkipInstall to skip dependency checks next time." -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        Start-Sleep -Seconds 1
        if ($backendJob.State -eq "Failed") {
            Write-Host "[ERROR] Backend job exited unexpectedly. Check logs for details." -ForegroundColor Red
            break
        }
        if ($frontendJob.State -eq "Failed") {
            Write-Host "[ERROR] Frontend job exited unexpectedly. Check logs for details." -ForegroundColor Red
            break
        }
    }
} finally {
    Write-Host ""
    Write-Host "[STOP] Stopping jobs..." -ForegroundColor Yellow
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Receive-Job $backendJob -ErrorAction SilentlyContinue | Out-Null
    Receive-Job $frontendJob -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Write-Host "[OK] Jobs cleaned up. Bye!" -ForegroundColor Green
}
