# 项目结构详细说明文档

## 📋 项目概述

这是一个基于 **Full Stack FastAPI Template** 的全栈 Web 应用项目，主要用于**搭切（Nesting）管理系统**。项目采用前后端分离架构，后端使用 FastAPI + SQLModel + PostgreSQL，前端使用 React + TypeScript + Vite + Chakra UI。

---

## 🏗️ 项目整体结构

```
nesting/
├── backend/              # 后端服务（Python/FastAPI）
├── frontend/             # 前端应用（React/TypeScript）
├── scripts/              # 自动化脚本
├── docker-compose.yml    # Docker Compose 配置
├── .env                  # 环境变量配置（需自行创建）
└── README.md             # 项目说明
```

---

## 🔧 后端结构详解 (`backend/`)

### 核心目录结构

```
backend/
├── app/                          # 应用主目录
│   ├── main.py                   # FastAPI 应用入口
│   ├── api/                      # API 路由层
│   │   ├── main.py              # API 路由聚合器
│   │   ├── deps.py              # 依赖注入（认证、数据库会话等）
│   │   └── routes/              # 具体路由模块
│   ├── core/                     # 核心配置模块
│   │   ├── config.py            # 应用配置（从 .env 读取）
│   │   ├── db.py                # 数据库连接和会话管理
│   │   ├── db_config.py         # 数据库配置
│   │   └── security.py          # 安全相关（密码哈希、JWT）
│   ├── models*.py                # 数据模型定义（SQLModel）
│   ├── crud.py                   # CRUD 操作通用函数
│   ├── utils*.py                 # 工具函数
│   ├── alembic/                  # 数据库迁移工具
│   │   └── versions/            # 迁移版本文件
│   ├── tests/                    # 测试代码
│   └── email-templates/          # 邮件模板
├── pyproject.toml                # Python 项目配置和依赖
├── alembic.ini                   # Alembic 迁移配置
└── Dockerfile                    # Docker 镜像构建文件
```

### 关键文件说明

#### 1. `app/main.py` - FastAPI 应用入口
- **功能**：创建 FastAPI 应用实例，配置中间件、CORS、路由
- **关键特性**：
  - 超时中间件（5分钟超时）
  - CORS 配置（允许前端访问）
  - Sentry 错误追踪（生产环境）
  - 自定义路由 ID 生成

#### 2. `app/api/main.py` - API 路由聚合
- **功能**：统一注册所有 API 路由模块
- **包含的路由模块**：
  - `login` - 用户登录
  - `users` - 用户管理
  - `items` - 基础项管理
  - `sales_order_doc_d` - 销售订单
  - `feature` / `feature_d` - 特征管理
  - `material_class` - 材料分类
  - `material` - 材料管理
  - `material_density` - 材料密度
  - `inventory` - 库存管理
  - `surfaceTechnology` - 表面工艺
  - `operation` - 操作管理
  - `nesting_layout` - 搭切布局
  - `production_order` - 生产订单
  - `unified` / `unified_v2` - 统一接口
  - `private` / `login_debug` - 本地开发调试接口

#### 3. `app/core/config.py` - 配置管理
- **功能**：从 `.env` 文件读取配置
- **关键配置项**：
  - `DATABASE_URL` - 业务数据库连接
  - `SYS_DATABASE_URL` - 系统数据库连接
  - `SECRET_KEY` - JWT 密钥
  - `FIRST_SUPERUSER` - 初始超级用户邮箱
  - `FIRST_SUPERUSER_PASSWORD` - 初始超级用户密码
  - `REDIS_*` - Redis 配置
  - `SMTP_*` - 邮件服务配置

#### 4. `app/core/db.py` - 数据库管理
- **功能**：创建数据库引擎、会话管理、初始化数据库
- **特性**：
  - 连接池配置（pool_size, max_overflow）
  - 连接超时和保活设置
  - 自动创建初始超级用户

#### 5. 数据模型文件 (`models*.py`)
- `models.py` - 基础模型（User, Item 等）
- `models_sales_order_doc_d.py` - 销售订单模型
- `models_feature.py` - 特征模型
- `models_material*.py` - 材料相关模型
- `models_inventory.py` - 库存模型
- `models_operation.py` - 操作模型
- `models_nesting_layout.py` - 搭切布局模型
- `models_production_order.py` - 生产订单模型
- `models_surface_technology.py` - 表面工艺模型

#### 6. `app/alembic/` - 数据库迁移
- **功能**：使用 Alembic 管理数据库 schema 变更
- **使用方式**：
  ```bash
  # 创建迁移
  alembic revision --autogenerate -m "描述"
  # 应用迁移
  alembic upgrade head
  ```

### API 路由模块详解

#### 认证相关
- **`login.py`** - 用户登录（JWT Token）
- **`login_debug.py`** - 调试登录（仅本地环境）

#### 用户管理
- **`users.py`** - 用户 CRUD、权限管理

#### 业务模块
- **`sales_order_doc_d.py`** - 销售订单管理
- **`material*.py`** - 材料、材料分类、材料密度管理
- **`inventory.py`** - 库存管理
- **`feature*.py`** - 特征管理
- **`operation.py`** - 操作管理
- **`nesting_layout.py`** - 搭切布局管理
- **`production_order.py`** - 生产订单管理
- **`surfaceTechnology.py`** - 表面工艺管理

#### 工具模块
- **`utils.py`** - 通用工具接口
- **`unified*.py`** - 统一接口（可能用于批量操作）

---

## 🎨 前端结构详解 (`frontend/`)

### 核心目录结构

```
frontend/
├── src/
│   ├── main.tsx                  # 应用入口
│   ├── routes/                   # 路由定义（TanStack Router）
│   │   ├── __root.tsx           # 根路由
│   │   ├── _layout.tsx          # 布局组件
│   │   ├── login.tsx            # 登录页
│   │   └── _layout/             # 布局子路由
│   │       ├── index.tsx        # 首页
│   │       ├── admin.tsx        # 管理员页面
│   │       ├── items.tsx        # 业务项页面
│   │       └── settings.tsx     # 设置页面
│   ├── components/               # React 组件
│   │   ├── Admin/               # 管理员组件
│   │   ├── Common/              # 通用组件
│   │   ├── Items/               # 业务项组件
│   │   ├── Pending/             # 待处理组件
│   │   ├── UserSettings/        # 用户设置组件
│   │   └── ui/                  # UI 基础组件（Chakra UI）
│   ├── client/                   # 自动生成的 API 客户端
│   │   ├── sdk.gen.ts           # API 调用函数
│   │   ├── schemas.gen.ts       # 类型定义
│   │   └── types.gen.ts         # TypeScript 类型
│   ├── hooks/                    # 自定义 Hooks
│   │   ├── useAuth.ts           # 认证 Hook
│   │   └── useCustomToast.ts    # Toast 通知 Hook
│   ├── utils/                    # 工具函数
│   ├── theme.tsx                 # Chakra UI 主题配置
│   └── config/                   # 配置文件
├── public/                       # 静态资源
├── tests/                        # E2E 测试（Playwright）
├── package.json                  # 依赖配置
├── vite.config.ts                # Vite 配置
└── tsconfig.json                 # TypeScript 配置
```

### 关键文件说明

#### 1. `src/main.tsx` - 应用入口
- **功能**：初始化 React 应用、配置路由、Query Client、API 客户端
- **关键配置**：
  - API 基础 URL：`VITE_API_URL`
  - Token 管理：从 localStorage 读取
  - 错误处理：401/403 自动跳转登录

#### 2. `src/routes/` - 路由系统（TanStack Router）
- **路由结构**：
  - `/login` - 登录页
  - `/signup` - 注册页
  - `/recover-password` - 找回密码
  - `/reset-password` - 重置密码
  - `/` - 首页（需登录）
  - `/admin` - 管理员页面
  - `/items` - 业务项管理
  - `/settings` - 用户设置

#### 3. `src/components/` - 组件库

##### `Admin/` - 管理员组件
- `AddUser.tsx` - 添加用户
- `EditUser.tsx` - 编辑用户
- `DeleteUser.tsx` - 删除用户

##### `Common/` - 通用组件
- `Navbar.tsx` - 导航栏
- `Sidebar.tsx` - 侧边栏
- `SidebarItems.tsx` - 侧边栏菜单项
- `TableSelectDialog.tsx` - 表格选择对话框
- `SelectInput.tsx` - 选择输入框

##### `Items/` - 业务项组件
- `Material*.tsx` - 材料相关组件
- `MaterialClass*.tsx` - 材料分类组件
- `MaterialDensity*.tsx` - 材料密度组件
- `Inventory*.tsx` - 库存组件
- `SalesOrder*.tsx` - 销售订单组件
- `Feature*.tsx` - 特征组件
- `Operation*.tsx` - 操作组件
- `Nesting*.tsx` - 搭切布局组件
- `ProductionOrder*.tsx` - 生产订单组件
- `SurfaceTechnology*.tsx` - 表面工艺组件

##### `ui/` - UI 基础组件
- 基于 Chakra UI 的封装组件
- `button.tsx`, `input.tsx`, `dialog.tsx` 等

#### 4. `src/client/` - API 客户端
- **自动生成**：通过 `npm run generate-client` 从后端 OpenAPI schema 生成
- **包含**：
  - `sdk.gen.ts` - API 调用函数
  - `schemas.gen.ts` - 数据模型类型
  - `types.gen.ts` - TypeScript 类型定义

#### 5. `src/hooks/` - 自定义 Hooks
- **`useAuth.ts`** - 认证状态管理
- **`useCustomToast.ts`** - Toast 通知管理

### 前端技术栈

- **框架**：React 18 + TypeScript
- **构建工具**：Vite 6
- **路由**：TanStack Router
- **状态管理**：TanStack Query (React Query)
- **UI 库**：Chakra UI 3
- **表格**：AG Grid + TanStack Table
- **表单**：React Hook Form
- **图表/画布**：Konva + React Konva
- **Excel**：xlsx + file-saver
- **测试**：Playwright

---

## 🛠️ 脚本和工具 (`scripts/`)

### 开发脚本
- **`dev-local.ps1`** / **`dev-local.sh`** - 本地开发启动（使用 Docker）
- **`dev-nodocker.ps1`** - 本地开发启动（不使用 Docker）

### 构建和部署
- **`build.sh`** - 构建 Docker 镜像
- **`deploy.sh`** - 部署脚本
- **`test.sh`** - 运行测试

### 代码生成
- **`generate-client.sh`** - 生成前端 API 客户端

---

## 🗄️ 数据库结构

### 数据库配置
- **业务数据库**：`DATABASE_URL`（主要数据存储）
- **系统数据库**：`SYS_DATABASE_URL`（系统级数据）

### 主要数据表（根据模型推断）
1. **用户表** (`user`) - 用户账户信息
2. **销售订单表** (`sales_order_doc_d`) - 销售订单数据
3. **材料表** (`material`) - 材料信息
4. **材料分类表** (`material_class`) - 材料分类
5. **材料密度表** (`material_density`) - 材料密度
6. **库存表** (`inventory`) - 库存信息
7. **特征表** (`feature`) - 特征定义
8. **操作表** (`operation`) - 操作定义
9. **搭切布局表** (`nesting_layout`) - 搭切布局方案
10. **生产订单表** (`production_order`) - 生产订单
11. **表面工艺表** (`surface_technology`) - 表面工艺

### 数据库迁移
- 使用 **Alembic** 管理数据库 schema 变更
- 迁移文件位于 `backend/app/alembic/versions/`

---

## 🔐 认证和授权

### JWT 认证
- 使用 JWT Token 进行用户认证
- Token 存储在 localStorage
- 自动处理 401/403 错误，跳转登录页

### 用户角色
- **超级用户** (`is_superuser=True`) - 拥有所有权限
- **普通用户** - 基础权限

---

## 📦 依赖管理

### 后端依赖（`pyproject.toml`）
- **Web 框架**：FastAPI
- **ORM**：SQLModel
- **数据库驱动**：psycopg (PostgreSQL)
- **认证**：passlib, pyjwt
- **数据验证**：Pydantic
- **数据库迁移**：Alembic
- **Excel 处理**：pandas, openpyxl
- **测试**：pytest
- **代码质量**：ruff, mypy

### 前端依赖（`package.json`）
- **核心**：React, TypeScript, Vite
- **路由**：@tanstack/react-router
- **状态管理**：@tanstack/react-query
- **UI 库**：@chakra-ui/react
- **表格**：ag-grid-community, @tanstack/react-table
- **表单**：react-hook-form
- **图表**：konva, react-konva
- **Excel**：xlsx, file-saver
- **HTTP 客户端**：axios
- **测试**：@playwright/test

---

## 🚀 开发工作流

### 1. 启动开发环境

#### 方式一：使用 Docker（推荐）
```bash
docker compose watch
```

#### 方式二：不使用 Docker
```powershell
# Windows PowerShell
.\scripts\dev-nodocker.ps1
```

### 2. 后端开发

#### 添加新的 API 路由
1. 在 `backend/app/api/routes/` 创建新的路由文件
2. 在 `backend/app/api/main.py` 注册路由
3. 如需新模型，在 `backend/app/models*.py` 定义
4. 创建数据库迁移：`alembic revision --autogenerate -m "描述"`
5. 应用迁移：`alembic upgrade head`

#### 添加新的数据模型
1. 在 `backend/app/models*.py` 定义 SQLModel 模型
2. 创建迁移：`alembic revision --autogenerate -m "添加新模型"`
3. 应用迁移：`alembic upgrade head`

### 3. 前端开发

#### 添加新页面
1. 在 `frontend/src/routes/` 创建路由文件
2. 在 `frontend/src/components/` 创建对应组件
3. 路由会自动注册（TanStack Router）

#### 更新 API 客户端
```bash
# 确保后端运行
# 然后运行
npm run generate-client
```

### 4. 测试

#### 后端测试
```bash
cd backend
pytest
```

#### 前端 E2E 测试
```bash
cd frontend
npx playwright test
```

---

## 📝 配置文件说明

### `.env` 文件（需自行创建）
```env
# 应用配置
PROJECT_NAME=搭切管理系统
SECRET_KEY=your-secret-key
ENVIRONMENT=local

# 数据库配置
DATABASE_URL=postgresql://user:password@host:port/dbname
SYS_DATABASE_URL=postgresql://user:password@host:port/sysdb

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 用户配置
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=your-password

# API 配置
API_V1_STR=/api/v1
FRONTEND_HOST=http://localhost:5173
```

### `frontend/.env`
```env
VITE_API_URL=http://localhost:8000
```

---

## 🔍 关键业务模块

### 1. 销售订单管理 (`sales_order_doc_d`)
- 销售订单的 CRUD 操作
- 订单查询和筛选

### 2. 材料管理 (`material`)
- 材料信息管理
- 材料分类管理
- 材料密度管理

### 3. 库存管理 (`inventory`)
- 库存查询
- 库存更新

### 4. 搭切布局 (`nesting_layout`)
- 搭切方案管理
- 可视化展示（可能使用 Konva）

### 5. 生产订单 (`production_order`)
- 生产订单管理
- 与销售订单关联

---

## 🐛 调试和故障排查

### 常见问题

1. **数据库连接失败**
   - 检查 `DATABASE_URL` 配置
   - 确认 PostgreSQL 服务运行
   - 检查网络连接

2. **前端无法访问后端**
   - 检查 CORS 配置
   - 确认 `VITE_API_URL` 正确
   - 检查后端服务是否运行

3. **登录失败**
   - 检查用户是否存在
   - 确认密码哈希正确
   - 查看后端日志

4. **数据库迁移失败**
   - 检查模型定义是否正确
   - 确认数据库连接正常
   - 查看迁移文件语法

---

## 📚 相关文档

- [开发指南](./development.md)
- [部署指南](./deployment.md)
- [后端 README](./backend/README.md)
- [前端 README](./frontend/README.md)

---

## 🎯 开发建议

1. **代码规范**
   - 后端使用 `ruff` 进行代码检查
   - 前端使用 `biome` 进行代码检查
   - 提交前运行 `pre-commit` hooks

2. **数据库变更**
   - 始终使用 Alembic 迁移，不要直接修改数据库
   - 迁移前备份数据库

3. **API 设计**
   - 遵循 RESTful 规范
   - 使用统一的错误响应格式
   - 添加适当的 API 文档注释

4. **前端组件**
   - 保持组件单一职责
   - 使用 TypeScript 类型定义
   - 复用通用组件

5. **测试**
   - 编写单元测试
   - 关键功能添加 E2E 测试
   - 保持测试覆盖率

---

## 📞 技术支持

如有问题，请查看：
- 项目 README
- 相关模块的 README 文件
- 代码注释和文档字符串

---

**最后更新**：2025-01-21



