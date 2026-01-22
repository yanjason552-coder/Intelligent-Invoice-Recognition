# 启动后端服务脚本

Write-Host "=== Starting Backend Service ===" -ForegroundColor Cyan
Write-Host ""

# 检查是否在正确的目录
if (-not (Test-Path "backend\app\main.py")) {
    Write-Host "[ERROR] Please run this script from the project root directory" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# 进入后端目录
Set-Location backend

# 检查 .env 文件是否存在
if (-not (Test-Path ".env")) {
    Write-Host "[ERROR] .env file not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create a .env file in the backend directory with the following required variables:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Required variables:" -ForegroundColor Cyan
    Write-Host "  PROJECT_NAME=搭切管理系统" -ForegroundColor Gray
    Write-Host "  SECRET_KEY=your-secret-key-here" -ForegroundColor Gray
    Write-Host "  DATABASE_URL=postgresql+psycopg://user:password@host:port/dbname" -ForegroundColor Gray
    Write-Host "  SYS_DATABASE_URL=postgresql+psycopg://user:password@host:port/sysdb" -ForegroundColor Gray
    Write-Host "  FIRST_SUPERUSER=admin@example.com" -ForegroundColor Gray
    Write-Host "  FIRST_SUPERUSER_PASSWORD=your-password" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Optional variables:" -ForegroundColor Cyan
    Write-Host "  ENVIRONMENT=local" -ForegroundColor Gray
    Write-Host "  REDIS_HOST=localhost" -ForegroundColor Gray
    Write-Host "  REDIS_PORT=6379" -ForegroundColor Gray
    Write-Host "  FRONTEND_HOST=http://localhost:5173" -ForegroundColor Gray
    Write-Host ""
    Write-Host "You can create .env file using one of these methods:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Method 1: Use the interactive script (recommended):" -ForegroundColor Cyan
    Write-Host "  .\create-env.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Method 2: Create manually with these required variables:" -ForegroundColor Cyan
    Write-Host "  PROJECT_NAME=搭切管理系统" -ForegroundColor Gray
    Write-Host "  SECRET_KEY=your-secret-key-here" -ForegroundColor Gray
    Write-Host "  DATABASE_URL=postgresql+psycopg://user:password@host:port/dbname" -ForegroundColor Gray
    Write-Host "  SYS_DATABASE_URL=postgresql+psycopg://user:password@host:port/sysdb" -ForegroundColor Gray
    Write-Host "  FIRST_SUPERUSER=admin@example.com" -ForegroundColor Gray
    Write-Host "  FIRST_SUPERUSER_PASSWORD=your-password" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "[INFO] .env file found" -ForegroundColor Green

# 检查是否有 uv
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
$useUv = $false

if (-not $uvCommand) {
    Write-Host "[WARN] uv is not installed" -ForegroundColor Yellow
    Write-Host "[INFO] Attempting to install uv..." -ForegroundColor Cyan
    
    # 检查是否有 pip
    $pipCommand = Get-Command pip -ErrorAction SilentlyContinue
    if ($pipCommand) {
        Write-Host "[INFO] Installing uv via pip..." -ForegroundColor Cyan
        pip install uv
        if ($LASTEXITCODE -eq 0) {
            # 重新检查 uv 是否可用
            $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
            if ($uvCommand) {
                $useUv = $true
                Write-Host "[SUCCESS] uv installed successfully" -ForegroundColor Green
            }
        }
    }
    
    if (-not $useUv) {
        Write-Host "[WARN] Could not install uv automatically" -ForegroundColor Yellow
        Write-Host "[INFO] Falling back to pip/venv method..." -ForegroundColor Cyan
        Write-Host ""
        $useUv = $false
    }
} else {
    $useUv = $true
    Write-Host "[INFO] Using uv for dependency management" -ForegroundColor Green
}

# 检查虚拟环境，如果不存在或损坏则重新创建
$venvPythonPath = Join-Path (Get-Location) ".venv\Scripts\python.exe"
$venvExists = Test-Path ".venv"
$venvValid = $false

if ($venvExists) {
    # 检查虚拟环境是否有效
    if (Test-Path $venvPythonPath) {
        # 尝试运行 Python 来验证虚拟环境是否有效
        $pythonTest = & $venvPythonPath --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $venvValid = $true
            Write-Host "[INFO] Virtual environment found and valid" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Virtual environment exists but Python is not working" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[WARN] Virtual environment directory exists but Python executable not found" -ForegroundColor Yellow
    }
}

if (-not $venvValid) {
    if ($venvExists) {
        Write-Host "[INFO] Removing corrupted virtual environment..." -ForegroundColor Yellow
        Remove-Item -Path ".venv" -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "[INFO] Creating virtual environment and installing dependencies..." -ForegroundColor Yellow
    
    if ($useUv) {
        # 使用 uv 创建虚拟环境
        uv sync
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to sync dependencies with uv" -ForegroundColor Red
            exit 1
        }
        Write-Host "[INFO] Virtual environment created successfully with uv" -ForegroundColor Green
    } else {
        # 使用 pip/venv 创建虚拟环境
        Write-Host "[INFO] Creating virtual environment with venv..." -ForegroundColor Cyan
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCommand) {
            Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
            Write-Host "[INFO] Please install Python from https://www.python.org/" -ForegroundColor Yellow
            exit 1
        }
        
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
            exit 1
        }
        
        # 重新获取虚拟环境 Python 路径（虚拟环境刚创建）
        $venvPythonPath = Join-Path (Get-Location) ".venv\Scripts\python.exe"
        
        Write-Host "[INFO] Installing dependencies with pip..." -ForegroundColor Cyan
        & $venvPythonPath -m pip install --upgrade pip
        & $venvPythonPath -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
            exit 1
        }
        Write-Host "[INFO] Virtual environment created successfully with pip/venv" -ForegroundColor Green
    }
} else {
    if ($useUv) {
        Write-Host "[INFO] Ensuring dependencies are up to date with uv..." -ForegroundColor Yellow
        uv sync
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARN] uv sync had issues, but continuing..." -ForegroundColor Yellow
        }
    } else {
        # 检查关键依赖是否已安装（特别是 uvicorn）
        Write-Host "[INFO] Checking if dependencies are installed..." -ForegroundColor Yellow
        $uvicornCheck = & $venvPythonPath -m pip show uvicorn 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARN] uvicorn not found, installing dependencies..." -ForegroundColor Yellow
            & $venvPythonPath -m pip install --upgrade pip
            & $venvPythonPath -m pip install -r requirements.txt
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
                exit 1
            }
            Write-Host "[INFO] Dependencies installed successfully" -ForegroundColor Green
        } else {
            Write-Host "[INFO] Virtual environment is ready" -ForegroundColor Green
        }
    }
}

# 检查数据库连接（可选）
Write-Host "[INFO] Starting backend server on http://localhost:8000" -ForegroundColor Green
Write-Host "[INFO] API docs will be available at http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# 启动服务
Write-Host "[INFO] Starting backend server..." -ForegroundColor Cyan
Write-Host ""

# 确保虚拟环境 Python 路径正确
if (-not (Test-Path $venvPythonPath)) {
    Write-Host "[ERROR] Virtual environment Python not found at $venvPythonPath" -ForegroundColor Red
    exit 1
}

# 检查关键依赖是否已安装
Write-Host "[INFO] Verifying critical dependencies..." -ForegroundColor Cyan

# 检查 uvicorn
if ($useUv) {
    $uvicornCheck = uv run python -c "import uvicorn; print(uvicorn.__version__)" 2>&1
} else {
    $uvicornCheck = & $venvPythonPath -c "import uvicorn; print(uvicorn.__version__)" 2>&1
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] uvicorn not found, installing..." -ForegroundColor Yellow
    if ($useUv) {
        uv pip install "uvicorn[standard]"
    } else {
        & $venvPythonPath -m pip install "uvicorn[standard]"
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install uvicorn" -ForegroundColor Red
        exit 1
    }
    Write-Host "[SUCCESS] uvicorn installed" -ForegroundColor Green
} else {
    Write-Host "[OK] uvicorn is available" -ForegroundColor Green
}

# 检查 psycopg3 (psycopg)
if ($useUv) {
    $psycopgCheck = uv run python -c "import psycopg; print('psycopg3 OK')" 2>&1
} else {
    $psycopgCheck = & $venvPythonPath -c "import psycopg; print('psycopg3 OK')" 2>&1
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] psycopg3 (psycopg) not found, installing..." -ForegroundColor Yellow
    if ($useUv) {
        uv pip install "psycopg[binary]"
    } else {
        & $venvPythonPath -m pip install "psycopg[binary]"
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install psycopg[binary]" -ForegroundColor Red
        Write-Host "[INFO] This is required for PostgreSQL database connections" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[SUCCESS] psycopg[binary] installed" -ForegroundColor Green
} else {
    Write-Host "[OK] psycopg3 (psycopg) is available" -ForegroundColor Green
}

if ($useUv) {
    # 使用 uv run（最可靠的方法）
    Write-Host "[INFO] Using uv run to start server..." -ForegroundColor Cyan
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
} else {
    # 使用虚拟环境中的 Python
    Write-Host "[INFO] Using virtual environment Python to start server..." -ForegroundColor Cyan
    & $venvPythonPath -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# 如果启动失败，LASTEXITCODE 会被设置
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Failed to start backend server" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check if port 8000 is available" -ForegroundColor Gray
    Write-Host "2. Verify database connection in .env file" -ForegroundColor Gray
    if ($useUv) {
        Write-Host "3. Try removing .venv and run again: Remove-Item -Recurse -Force .venv; uv sync" -ForegroundColor Gray
        Write-Host "4. Try manually: uv run uvicorn app.main:app --reload" -ForegroundColor Gray
    } else {
        Write-Host "3. Try removing .venv and run again: Remove-Item -Recurse -Force .venv; python -m venv .venv; .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Gray
        Write-Host "4. Try manually: .venv\Scripts\python.exe -m uvicorn app.main:app --reload" -ForegroundColor Gray
    }
    exit 1
}


