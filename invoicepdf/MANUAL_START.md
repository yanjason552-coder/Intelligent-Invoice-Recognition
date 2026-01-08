# 手动启动前后端服务指南

## 前置条件

1. **确保数据库服务运行**
   - PostgreSQL 数据库正在运行
   - Redis 服务正在运行（如果使用）
   - 数据库已运行迁移：`alembic upgrade head`

2. **检查环境配置**
   - `backend/.env` 文件配置正确
   - 数据库连接字符串正确

## 启动步骤

### 方式一：使用两个终端窗口（推荐）

#### 终端 1：启动后端服务

```powershell
# 1. 进入后端目录
cd D:\Product\invoicePDF\backend

# 2. 激活虚拟环境（如果使用）
# 如果使用 uv:
.\.venv\Scripts\Activate.ps1
# 或者如果使用 poetry:
# poetry shell

# 3. 启动后端服务
uvicorn app.main:app --reload --port 8000

# 或者使用 fastapi 命令（如果已安装）:
# fastapi dev app/main.py
```

**后端服务将在以下地址运行：**
- API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

#### 终端 2：启动前端服务

```powershell
# 1. 进入前端目录
cd D:\Product\invoicePDF\frontend

# 2. 安装依赖（首次运行或依赖更新后）
npm install

# 3. 启动前端开发服务器
npm run dev
```

**前端服务将在以下地址运行：**
- 前端应用: http://localhost:5173

---

### 方式二：使用 PowerShell 后台作业

#### 启动后端（后台）

```powershell
cd D:\Product\invoicePDF\backend
Start-Job -ScriptBlock {
    Set-Location D:\Product\invoicePDF\backend
    uvicorn app.main:app --reload --port 8000
}
```

#### 启动前端（后台）

```powershell
cd D:\Product\invoicePDF\frontend
Start-Job -ScriptBlock {
    Set-Location D:\Product\invoicePDF\frontend
    npm run dev
}
```

#### 查看后台作业状态

```powershell
# 查看所有作业
Get-Job

# 查看后端输出
Receive-Job -Id <JobId> -Keep

# 停止作业
Stop-Job -Id <JobId>
Remove-Job -Id <JobId>
```

---

### 方式三：使用项目提供的脚本

```powershell
# 在项目根目录运行
cd D:\Product\invoicePDF
.\scripts\dev-nodocker.ps1
```

这个脚本会：
- 自动检查并安装依赖
- 并行启动后端和前端
- 按 Ctrl+C 停止所有服务

---

## 验证服务是否启动成功

### 检查后端服务

```powershell
# 方法1: 使用 curl
curl http://localhost:8000/docs

# 方法2: 使用 PowerShell
Invoke-WebRequest -Uri http://localhost:8000/docs -Method Get

# 方法3: 在浏览器中打开
# http://localhost:8000/docs
```

### 检查前端服务

```powershell
# 方法1: 使用 curl
curl http://localhost:5173

# 方法2: 使用 PowerShell
Invoke-WebRequest -Uri http://localhost:5173 -Method Get

# 方法3: 在浏览器中打开
# http://localhost:5173
```

---

## 常见问题

### 1. 后端启动失败

**问题：端口被占用**
```powershell
# 检查端口占用
netstat -ano | findstr :8000

# 停止占用端口的进程
taskkill /PID <进程ID> /F
```

**问题：数据库连接失败**
- 检查 `backend/.env` 中的 `DATABASE_URL`
- 确认 PostgreSQL 服务正在运行
- 检查数据库用户权限

**问题：模块导入错误**
```powershell
# 确保虚拟环境已激活
cd backend
.\.venv\Scripts\Activate.ps1

# 重新安装依赖
pip install -r requirements.txt
# 或使用 uv:
uv sync
```

### 2. 前端启动失败

**问题：端口被占用**
```powershell
# 检查端口占用
netstat -ano | findstr :5173

# 停止占用端口的进程
taskkill /PID <进程ID> /F
```

**问题：依赖未安装**
```powershell
cd frontend
npm install
```

**问题：Node.js 版本不兼容**
```powershell
# 检查 Node.js 版本
node --version

# 应该使用 Node.js 18+ 或 20+
```

---

## 停止服务

### 方式一：在运行服务的终端中
按 `Ctrl+C` 停止服务

### 方式二：停止后台作业
```powershell
# 查看所有作业
Get-Job

# 停止所有作业
Get-Job | Stop-Job
Get-Job | Remove-Job
```

### 方式三：通过进程名停止
```powershell
# 停止 uvicorn 进程
Get-Process | Where-Object {$_.ProcessName -like "*uvicorn*"} | Stop-Process

# 停止 node 进程（前端）
Get-Process | Where-Object {$_.ProcessName -like "*node*"} | Stop-Process
```

---

## 快速启动脚本

你也可以创建自己的快速启动脚本：

### start-backend.ps1
```powershell
cd D:\Product\invoicePDF\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### start-frontend.ps1
```powershell
cd D:\Product\invoicePDF\frontend
npm run dev
```

然后分别运行：
```powershell
.\start-backend.ps1
.\start-frontend.ps1
```

---

## 服务地址总结

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost:5173 | React 开发服务器 |
| 后端 API | http://localhost:8000 | FastAPI 服务器 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| OpenAPI JSON | http://localhost:8000/openapi.json | OpenAPI 规范 |


