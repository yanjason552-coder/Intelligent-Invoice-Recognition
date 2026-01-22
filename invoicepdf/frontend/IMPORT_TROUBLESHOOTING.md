# 导入功能问题排查指南

## 问题描述
导入失败: Failed to execute 'json' on 'Response': Unexpected end of JSON input

## 可能原因和解决方案

### 1. 后端服务器未运行

**症状**: 前端无法连接到后端API

**检查方法**:
```bash
# 检查后端服务是否运行
curl http://localhost:8000/docs
```

**解决方案**:
```bash
# 启动后端服务
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. API代理配置问题

**症状**: 前端请求无法正确转发到后端

**检查方法**:
- 确认 `frontend/vite.config.ts` 中有正确的代理配置
- 检查浏览器网络面板中的请求URL

**解决方案**:
确保 `vite.config.ts` 包含以下配置:
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
    },
  },
},
```

### 3. 访问令牌问题

**症状**: 401未授权错误

**检查方法**:
```javascript
// 在浏览器控制台中运行
console.log('Token:', localStorage.getItem('access_token'))
```

**解决方案**:
- 重新登录获取新的访问令牌
- 检查令牌是否过期

### 4. API路由问题

**症状**: 404未找到错误

**检查方法**:
```bash
# 测试API路由
curl -X POST http://localhost:8000/api/v1/salesOrderDocD/unified \
  -H "Content-Type: application/json" \
  -d '{"action":"list","module":"sales_order_doc_d"}'
```

**解决方案**:
- 确认后端路由正确注册
- 检查 `backend/app/api/main.py` 中的路由配置

### 5. 数据格式问题

**症状**: 400错误或数据解析失败

**检查方法**:
- 查看浏览器控制台中的请求数据
- 检查Excel文件格式是否正确

**解决方案**:
- 确保Excel文件格式正确（第1行字段名，第2行注释，第3行开始数据）
- 检查必要字段是否存在（doc_id, doc_no, sequence）

## 调试步骤

### 步骤1: 检查后端服务
```bash
cd backend
python test_import_api.py
```

### 步骤2: 检查前端API连接
1. 打开浏览器开发者工具
2. 在控制台中运行:
```javascript
// 复制 frontend/debug_api.js 的内容到控制台
```

### 步骤3: 检查网络请求
1. 打开浏览器开发者工具的网络面板
2. 尝试导入操作
3. 查看请求和响应的详细信息

### 步骤4: 检查控制台日志
1. 查看浏览器控制台的错误信息
2. 查看后端服务器的日志输出

## 常见错误和解决方案

### 错误1: CORS错误
**解决方案**: 确保后端配置了正确的CORS设置

### 错误2: 网络连接超时
**解决方案**: 
- 检查网络连接
- 确认后端服务正在运行
- 检查防火墙设置

### 错误3: 文件格式错误
**解决方案**:
- 使用提供的测试文件生成脚本
- 确保Excel文件格式正确

### 错误4: 数据库连接错误
**解决方案**:
- 检查数据库服务是否运行
- 确认数据库连接配置正确

## 测试文件生成

使用提供的脚本生成测试文件:
```bash
cd backend
python create_test_excel.py
```

## 日志查看

### 前端日志
- 浏览器控制台
- 网络面板

### 后端日志
- 终端输出
- 应用日志文件

## 联系支持

如果问题仍然存在，请提供以下信息:
1. 错误截图
2. 浏览器控制台日志
3. 后端服务器日志
4. 使用的Excel文件格式
5. 系统环境信息 