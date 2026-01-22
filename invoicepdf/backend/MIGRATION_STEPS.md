# 迁移执行步骤

## 问题
Alembic检测到多个迁移head，需要先合并分支。

## 解决方案

我已经创建了合并迁移文件 `merge_invoice_and_material.py`，它会合并两个分支：
- `create_invoice_tables_001` (票据识别表)
- `remove_material_fk` (移除material外键)

## 执行步骤

### 方法1：使用脚本（推荐）

```powershell
cd backend
.\RUN_MIGRATION.ps1
```

### 方法2：手动执行

```powershell
cd backend

# 步骤1: 升级到第一个head
python -m alembic upgrade create_invoice_tables_001

# 步骤2: 升级到第二个head
python -m alembic upgrade remove_material_fk

# 步骤3: 升级合并迁移
python -m alembic upgrade merge_001
```

### 方法3：如果两个迁移都已应用

如果数据库已经应用了这两个迁移，只需要应用合并迁移：

```powershell
cd backend
python -m alembic upgrade merge_001
```

## 验证

迁移成功后：

```powershell
# 查看当前版本（应该显示 merge_001）
python -m alembic current

# 查看所有head（应该只显示一个）
python -m alembic heads
```

## 如果遇到错误

### 错误1: "Target database is not up to date"

说明某个迁移还没有应用，需要先应用它：

```powershell
# 查看当前版本
python -m alembic current

# 查看历史
python -m alembic history

# 根据情况升级到需要的版本
python -m alembic upgrade <revision_id>
```

### 错误2: "Can't locate revision identified by"

说明迁移文件有问题，检查：
1. 迁移文件是否存在
2. revision 和 down_revision 是否正确

### 错误3: 表已存在

如果表已经存在，可以：
1. 删除表后重新迁移
2. 或者修改迁移文件，使用 `if_not_exists=True`


