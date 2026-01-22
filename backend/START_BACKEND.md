# 启动后端服务

## 问题
如果前端出现 `请求超时` 错误，说明后端服务没有运行。

## 快速启动

### 方法 1: 使用 PowerShell 脚本（推荐）

```powershell
cd backend
.\start_backend.ps1
```

### 方法 2: 手动启动

```powershell
cd backend

# 激活虚拟环境（如果使用 uv）
.venv\Scripts\activate

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 方法 3: 使用 fastapi CLI

```powershell
cd backend
.venv\Scripts\activate
fastapi run --reload app/main.py
```

## 验证服务是否运行

服务启动后，访问以下地址验证：

- **健康检查**: http://localhost:8000/api/v1/health
- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc

## 常见问题

### 1. 端口被占用

如果 8000 端口被占用，可以修改端口：

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

然后修改前端的 API 地址配置。

### 2. 数据库连接失败

确保数据库服务正在运行，并检查 `.env` 文件中的数据库配置。

### 3. 依赖未安装

如果启动失败，先安装依赖：

```powershell
cd backend
uv sync
```

## 停止服务

在运行服务的终端中按 `Ctrl+C` 停止服务。

