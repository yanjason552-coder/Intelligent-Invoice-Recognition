# 🚀 快速开发指南

## 高效开发方法对比

### ❌ 不推荐的方法
```bash
# 每次修改都要重新构建整个Docker环境
docker-compose up --build --force-recreate
```
**问题：** 耗时5-10分钟，效率极低

### ✅ 推荐的方法

#### 方法1: 本地开发服务器（最推荐）
```bash
# 1. 启动数据库和邮件服务
docker compose up db mailcatcher -d

# 2. 启动后端开发服务器
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 3. 启动前端开发服务器（新终端）
cd frontend
npm run dev
```

#### 方法2: 使用开发脚本
```bash
# Windows PowerShell
.\scripts\dev-local.ps1

# Linux/Mac
./scripts/dev-local.sh
```

#### 方法3: Docker Compose Watch模式
```bash
# 只重建修改的服务
docker compose watch
```

## 🎯 开发流程

### 1. 首次启动
```bash
# 使用开发脚本（推荐）
.\scripts\dev-local.ps1
```

### 2. 日常开发
- 修改前端代码 → 自动热重载（1-2秒）
- 修改后端代码 → 自动重启（3-5秒）
- 修改数据库 → 需要重启后端服务

### 3. 测试功能
- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- 邮件测试: http://localhost:1080

## ⚡ 性能对比

| 方法 | 启动时间 | 代码修改响应时间 | 推荐度 |
|------|----------|------------------|--------|
| Docker --force-recreate | 5-10分钟 | 5-10分钟 | ❌ |
| Docker watch | 2-3分钟 | 30秒-2分钟 | ⚠️ |
| 本地开发服务器 | 30秒 | 1-5秒 | ✅ |

## 🔧 常见问题

### Q: 数据库连接失败？
```bash
# 检查数据库状态
docker compose ps db

# 重启数据库
docker compose restart db
```

### Q: 端口被占用？
```bash
# 查看端口占用
netstat -ano | findstr :5173
netstat -ano | findstr :8000

# 杀死进程
taskkill /PID <进程ID> /F
```

### Q: 前端热重载不工作？
```bash
# 重启前端服务
cd frontend
npm run dev
```

### Q: 后端自动重启不工作？
```bash
# 重启后端服务
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 💡 开发技巧

### 1. 使用多个终端
- 终端1: 运行开发脚本
- 终端2: 查看日志 `docker compose logs -f`
- 终端3: 运行测试

### 2. 浏览器开发者工具
- 打开 Network 标签页监控API请求
- 使用 Console 调试前端代码
- 使用 Application 标签页查看存储

### 3. 快速测试
```bash
# 测试后端API
curl http://localhost:8000/api/v1/

# 测试前端构建
cd frontend && npm run build
```

## 🎉 总结

使用本地开发服务器可以让你：
- ✅ 代码修改后1-5秒内看到效果
- ✅ 节省大量等待时间
- ✅ 提高开发效率
- ✅ 更好的调试体验

**建议：** 日常开发使用本地开发服务器，部署前使用Docker进行完整测试。 