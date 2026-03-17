# 创建"孔类模板"脚本使用说明

## 运行方式

在项目根目录（invoicepdf）下运行：

```bash
python backend/scripts/create_dimension_inspection_template.py
```

或者在 backend 目录下运行：

```bash
cd backend
python scripts/create_dimension_inspection_template.py
```

## 脚本功能

1. 检查是否存在名为"孔类模板"的模板
   - 如果存在，会删除其所有版本和字段，然后重新创建
   - 如果不存在，会创建新模板

2. 创建模板版本（v1.0.0，draft状态）

3. 根据 `SCHEMA_JSON` 解析并创建所有字段：
   - 顶层字段（doc_type, form_title, drawing_no等）
   - items 数组及其子字段
   - items.measurements 数组及其子字段

4. 建立字段的父子关系（parent_field_id）

5. 设置字段的详细属性（字段名称、描述、示例值等）

## 注意事项

- 脚本需要数据库连接正常
- 脚本需要至少有一个用户存在于数据库中（用于 creator_id）
- 如果数据库表结构不完整（如缺少 prompt 字段），脚本会使用原始 SQL 来避免查询不存在的字段

## 字段定义

所有字段的详细属性定义在脚本的 `FIELD_DEFINITIONS` 字典中，包括：
- 字段名称（中文）
- 数据名称（英文）
- 数据类型
- 是否必填
- 描述
- 示例值

## 替代方案

如果脚本运行遇到问题，也可以通过前端界面创建模板：

1. 在前端创建新模板，名称为"孔类模板"
2. 使用"从 Schema 更新"功能，系统会自动读取 `frontend/public/dimension_inspection_schema.json`
3. 手动编辑字段属性（如果需要）

