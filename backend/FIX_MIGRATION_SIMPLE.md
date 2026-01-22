# 修复迁移分支问题 - 简单方案

## 问题

Alembic检测到多个迁移head，错误信息：
```
Multiple head revisions are present for given argument 'head'
```

## 原因

有两个迁移分支从同一个起点分叉：
- 主分支：`e2412789c190` → `9c0a54914c78` → `d98dd8ec85a3` → `1a31ce608336` → `create_invoice_tables_001`
- 独立分支：`e2412789c190` → `remove_material_fk`

## 解决方案

我已经修改了 `remove_material_foreign_key_constraint.py`，将其依赖改为指向主分支的最新迁移 `1a31ce608336`。

现在迁移链变为：
```
e2412789c190 → 9c0a54914c78 → d98dd8ec85a3 → 1a31ce608336
                                                      ├─> create_invoice_tables_001
                                                      └─> remove_material_fk
```

## 执行步骤

### 1. 如果 remove_material_fk 已经应用到数据库

需要先回滚，然后重新应用：

```bash
cd backend

# 查看当前版本
alembic current

# 如果当前是 remove_material_fk，需要回滚
alembic downgrade 1a31ce608336

# 然后重新应用（现在它会正确指向 1a31ce608336）
alembic upgrade head
```

### 2. 如果 remove_material_fk 还没有应用

直接执行：

```bash
cd backend
alembic upgrade head
```

### 3. 如果两个迁移都已应用

需要手动修复数据库中的 alembic_version 表，或者使用合并迁移。

## 验证

执行后验证：

```bash
# 查看当前版本
alembic current

# 应该显示 create_invoice_tables_001 或 remove_material_fk（取决于应用顺序）

# 查看所有head
alembic heads

# 应该只显示一个head（如果还有两个，说明需要合并迁移）
```

## 如果还有问题

如果执行 `alembic heads` 仍然显示两个head，需要创建合并迁移：

```bash
# 创建合并迁移
alembic merge -m "merge branches" create_invoice_tables_001 remove_material_fk

# 然后升级
alembic upgrade head
```


