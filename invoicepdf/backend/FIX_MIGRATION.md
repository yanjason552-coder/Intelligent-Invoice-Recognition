# 修复迁移分支问题

## 问题描述

Alembic检测到多个迁移head，无法确定升级目标。

## 迁移分支情况

当前有两个迁移分支：

**分支1（主分支）：**
```
e2412789c190 (initialize_models)
  └─> 9c0a54914c78 (add_max_length)
      └─> d98dd8ec85a3 (replace_id_integers)
          └─> 1a31ce608336 (add_cascade_delete)
              └─> create_invoice_tables_001
```

**分支2（独立分支）：**
```
e2412789c190 (initialize_models)
  └─> remove_material_fk
```

## 解决方案

### 方案1：创建合并迁移（推荐）

我已经创建了合并迁移文件 `merge_migration_branches.py`。

执行步骤：

```bash
cd backend

# 1. 先升级到两个head
alembic upgrade create_invoice_tables_001
alembic upgrade remove_material_fk

# 2. 然后升级合并迁移
alembic upgrade merge_branches_001
```

### 方案2：修改remove_material_fk依赖（如果该迁移未应用）

如果 `remove_material_fk` 迁移还没有应用到数据库，可以修改它的依赖：

编辑 `backend/app/alembic/versions/remove_material_foreign_key_constraint.py`：

```python
down_revision = '1a31ce608336'  # 改为指向主分支的最新迁移
```

然后删除合并迁移文件。

### 方案3：删除不需要的迁移（如果remove_material_fk不需要）

如果 `remove_material_fk` 迁移不需要，可以：

1. 删除文件 `remove_material_foreign_key_constraint.py`
2. 如果已应用到数据库，需要先回滚：
   ```bash
   alembic downgrade e2412789c190
   ```

## 推荐操作步骤

1. **检查当前数据库迁移状态**：
   ```bash
   # 连接到数据库查看 alembic_version 表
   psql -U postgres -d app -c "SELECT * FROM alembic_version;"
   ```

2. **根据状态选择方案**：
   - 如果两个迁移都已应用 → 使用方案1（合并迁移）
   - 如果只有主分支应用 → 使用方案2或方案3
   - 如果都没有应用 → 使用方案2

3. **执行迁移**：
   ```bash
   alembic upgrade head
   ```


