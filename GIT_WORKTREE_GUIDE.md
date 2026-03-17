# Git Worktree 在此项目中的使用指南

## 概述

Git worktree 允许在同一个仓库中同时检出多个工作目录，每个工作目录可以指向不同的分支。这对于需要同时处理多个任务或在不同分支间切换的场景非常有用。

## 当前项目状态

- **主工作目录**: `C:/FITS/Project/Invoice/智能发票识别_Final_V2/invoicepdf` (main 分支)
- **现有 worktree**: `C:/Users/IT0598/.cursor/worktrees/invoicepdf/vwm` (detached HEAD)
- **未提交更改**: 主目录有大量修改的文件

## 使用场景

### 场景1: 并行开发多个功能

当需要在开发新功能的同时修复紧急 bug：

```bash
# 在主目录继续开发新功能
# 创建新的 worktree 用于修复 bug
git worktree add ../invoicepdf-hotfix hotfix/fix-critical-bug

# 在 hotfix worktree 中修复问题
cd ../invoicepdf-hotfix
# ... 修复代码 ...
git commit -m "修复关键bug"

# 切换回主目录继续开发
cd ../invoicepdf
```

### 场景2: 同时处理前端和后端任务

```bash
# 创建专门用于后端开发的 worktree
git worktree add ../invoicepdf-backend-feature feature/backend-api-enhancement

# 创建专门用于前端开发的 worktree  
git worktree add ../invoicepdf-frontend-feature feature/frontend-ui-improvement

# 在不同终端中同时工作
# 终端1: cd ../invoicepdf-backend-feature
# 终端2: cd ../invoicepdf-frontend-feature
```

### 场景3: 测试不同版本

```bash
# 创建用于测试生产版本的 worktree
git worktree add ../invoicepdf-production origin/main

# 创建用于测试开发版本的 worktree
git worktree add ../invoicepdf-dev dev

# 在不同目录中启动不同的服务进行对比测试
```

### 场景4: 数据库迁移测试

由于项目有复杂的数据库迁移（如 `backend/FIX_MIGRATION.md` 中提到的多分支迁移问题）：

```bash
# 创建专门用于测试迁移的 worktree
git worktree add ../invoicepdf-migration-test migration/test-alembic-fix

# 在测试 worktree 中安全地测试迁移，不影响主开发环境
cd ../invoicepdf-migration-test
cd backend
alembic upgrade head  # 安全测试迁移
```

### 场景5: 代码审查和对比

```bash
# 创建用于审查 PR 的 worktree
git worktree add ../invoicepdf-review feature/your-feature-branch

# 在主目录和 review worktree 之间对比代码
# 使用 IDE 或 diff 工具对比两个目录
```

## 常用命令

### 查看所有 worktree

```bash
git worktree list
```

### 创建新的 worktree

```bash
# 基本语法
git worktree add <路径> <分支名>

# 如果分支不存在，创建新分支
git worktree add <路径> -b <新分支名>

# 示例
git worktree add ../invoicepdf-feature feature/new-feature
git worktree add ../invoicepdf-bugfix -b bugfix/fix-issue-123
```

### 删除 worktree

```bash
# 先删除工作目录（确保已提交或丢弃更改）
rm -rf ../invoicepdf-feature

# 然后清理 worktree 记录
git worktree remove ../invoicepdf-feature

# 或者使用 prune 自动清理
git worktree prune
```

### 移动 worktree

```bash
git worktree move <旧路径> <新路径>
```

## 项目特定建议

### 1. 管理未提交的更改

由于主目录有大量未提交的更改，建议：

```bash
# 方案A: 先提交或暂存主目录的更改
git add .
git commit -m "WIP: 当前开发进度"

# 方案B: 使用 stash
git stash push -m "当前工作进度"

# 然后创建新的 worktree
git worktree add ../invoicepdf-feature feature/new-feature
```

### 2. Docker 环境隔离

每个 worktree 可以有自己的 Docker 环境：

```bash
# 在 worktree 目录中
cd ../invoicepdf-feature

# 使用不同的 compose 文件或环境变量
cp docker-compose.yml docker-compose.feature.yml
# 修改端口避免冲突
# 然后启动
docker compose -f docker-compose.feature.yml up
```

### 3. 环境变量管理

为每个 worktree 创建独立的环境配置：

```bash
# 在 worktree 目录中
cp .env .env.feature
# 修改数据库名称、端口等避免冲突
```

### 4. 清理现有 worktree

如果不需要现有的 worktree：

```bash
# 查看当前 worktree
git worktree list

# 删除不需要的 worktree
git worktree remove C:/Users/IT0598/.cursor/worktrees/invoicepdf/vwm
```

## 注意事项

1. **共享 .git 目录**: 所有 worktree 共享同一个 `.git` 目录，因此：
   - 提交、分支操作会同步
   - 但工作目录的文件是独立的

2. **避免冲突**:
   - 不同 worktree 不要同时修改同一个文件
   - 使用不同的端口运行服务
   - 使用不同的数据库名称

3. **性能考虑**:
   - 每个 worktree 都是完整的文件系统副本
   - 确保有足够的磁盘空间

4. **IDE 支持**:
   - 大多数 IDE（包括 VS Code/Cursor）可以正常打开 worktree 目录
   - 每个 worktree 可以独立配置 IDE 设置

## 最佳实践

1. **命名规范**: 使用描述性的目录名，如 `invoicepdf-feature-xxx`、`invoicepdf-hotfix-xxx`

2. **定期清理**: 完成工作后及时删除不需要的 worktree

3. **文档记录**: 在项目文档中记录 worktree 的使用情况

4. **团队协作**: 如果团队使用 worktree，在 README 中说明约定

## 示例工作流

```bash
# 1. 开始新功能开发
git worktree add ../invoicepdf-feature-user-permission feature/user-permission-enhancement

# 2. 在 feature worktree 中开发
cd ../invoicepdf-feature-user-permission
# ... 开发代码 ...

# 3. 同时需要修复紧急 bug
git worktree add ../invoicepdf-hotfix-cors hotfix/fix-cors-issue
cd ../invoicepdf-hotfix-cors
# ... 修复 bug ...
git commit -m "修复 CORS 问题"
git push origin hotfix/fix-cors-issue

# 4. 回到功能开发
cd ../invoicepdf-feature-user-permission
# ... 继续开发 ...

# 5. 完成后清理
git worktree remove ../invoicepdf-hotfix-cors
git worktree remove ../invoicepdf-feature-user-permission
```

## Windows PowerShell 特定说明

在 Windows PowerShell 环境中，路径处理可能有所不同：

```powershell
# 创建 worktree（使用相对路径）
git worktree add ..\invoicepdf-feature feature\new-feature

# 或者使用绝对路径
git worktree add C:\FITS\Project\Invoice\智能发票识别_Final_V2\invoicepdf-feature feature\new-feature

# 查看 worktree 列表
git worktree list

# 删除 worktree
git worktree remove ..\invoicepdf-feature
```

## 与项目开发流程集成

### 结合 Docker Compose 使用

```bash
# 在 worktree 目录中创建独立的 Docker 环境
cd ../invoicepdf-feature

# 复制并修改 docker-compose 文件
cp docker-compose.yml docker-compose.feature.yml

# 编辑 docker-compose.feature.yml，修改端口和数据库名称
# 例如：
# - 后端端口: 8000 -> 8001
# - 前端端口: 5173 -> 5174
# - 数据库名称: app -> app_feature

# 启动服务
docker compose -f docker-compose.feature.yml up
```

### 结合数据库迁移使用

```bash
# 在 worktree 中测试数据库迁移
cd ../invoicepdf-migration-test
cd backend

# 使用独立的数据库配置
export DATABASE_URL="postgresql://user:pass@localhost/app_test"

# 安全地测试迁移
alembic upgrade head
alembic downgrade -1  # 如果需要回滚测试
```

## 故障排除

### 问题1: 无法创建 worktree，提示路径已存在

```bash
# 检查路径是否存在
ls -la ../invoicepdf-feature

# 如果存在但不需要，先删除
rm -rf ../invoicepdf-feature

# 然后重新创建
git worktree add ../invoicepdf-feature feature/new-feature
```

### 问题2: worktree 显示为 "locked"

```bash
# 查看锁定的 worktree
git worktree list

# 如果确认可以解锁，删除锁定文件
rm .git/worktrees/invoicepdf-feature/locked

# 或者使用 prune 清理
git worktree prune
```

### 问题3: 端口冲突

确保不同 worktree 使用不同的端口：

```bash
# 在主目录: 使用默认端口 8000, 5173
# 在 feature worktree: 使用 8001, 5174
# 在 hotfix worktree: 使用 8002, 5175
```

## 相关文档

- [Git Worktree 官方文档](https://git-scm.com/docs/git-worktree)
- [项目开发指南](development.md)
- [快速开发指南](QUICK_DEV_GUIDE.md)
- [部署指南](DEPLOYMENT_GUIDE.md)

