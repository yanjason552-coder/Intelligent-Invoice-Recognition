# 模板管理 API 文档

## 概述
模板管理 API 提供了完整的模板配置、版本管理和字段定义功能。

## 数据库结构

### 1. template 表（模板主表）
存储模板的基础信息和元数据。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(100) | 模板名称 |
| template_type | VARCHAR(50) | 模板类型（增值税发票/采购订单等） |
| description | TEXT | 模板描述 |
| status | VARCHAR(20) | 状态：enabled/disabled/deprecated |
| current_version_id | UUID | 当前版本ID（外键） |
| accuracy | FLOAT | 准确率（统计值） |
| creator_id | UUID | 创建人ID（外键） |
| create_time | DATETIME | 创建时间 |
| update_time | DATETIME | 更新时间 |

**索引：**
- `ix_template_name` - name 字段索引
- `ix_template_template_type` - template_type 字段索引

### 2. template_version 表（模板版本表）
存储模板的版本信息和发布状态。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| template_id | UUID | 模板ID（外键） |
| version | VARCHAR(50) | 版本号（如：v1.0.0） |
| status | VARCHAR(20) | 状态：draft/published/deprecated |
| schema_snapshot | JSONB | Schema快照（发布时生成，不可变） |
| accuracy | FLOAT | 准确率（从评估回写） |
| etag | VARCHAR(100) | 版本标签（用于乐观锁） |
| locked_by | UUID | 锁定人ID（草稿编辑锁） |
| locked_at | DATETIME | 锁定时间 |
| created_by | UUID | 创建人ID（外键） |
| created_at | DATETIME | 创建时间 |
| published_at | DATETIME | 发布时间 |
| deprecated_at | DATETIME | 废弃时间 |

**索引：**
- `ix_template_version_version` - version 字段索引
- `ix_template_version_template_id` - template_id 字段索引

### 3. template_field 表（模板字段表）
存储模板字段的定义和配置。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| template_id | UUID | 模板ID（外键） |
| template_version_id | UUID | 模板版本ID（外键） |
| field_key | VARCHAR(100) | 字段标识（英文/下划线） |
| field_name | VARCHAR(200) | 字段名称（中文展示） |
| data_type | VARCHAR(50) | 数据类型：string/number/date/datetime/boolean/enum/object/array |
| is_required | BOOLEAN | 是否必填 |
| required | BOOLEAN | 是否必填（兼容字段） |
| default_value | TEXT | 默认值 |
| description | TEXT | 字段说明 |
| example | TEXT | 示例值 |
| validation | JSON | 校验规则（regex/min/max/length等） |
| validation_rules | JSON | 校验规则（兼容字段） |
| normalize | JSON | 格式化规则（trim/upper/lower等） |
| prompt_hint | TEXT | 对LLM的补充提示 |
| confidence_threshold | FLOAT | 字段级置信度阈值 |
| canonical_field | VARCHAR(100) | 映射到系统通用字段 |
| parent_field_id | UUID | 父字段ID（用于嵌套结构） |
| deprecated | BOOLEAN | 是否废弃 |
| deprecated_at | DATETIME | 废弃时间 |
| position | INTEGER | 位置（兼容字段） |
| display_order | INTEGER | 显示顺序 |
| sort_order | INTEGER | 排序顺序 |
| remark | TEXT | 备注 |
| create_time | DATETIME | 创建时间 |

**索引：**
- `ix_template_field_field_key` - field_key 字段索引
- `ix_template_field_template_id` - template_id 字段索引
- `ix_template_field_template_version_id` - template_version_id 字段索引

## API 端点

### 1. 获取模板列表
**GET** `/api/v1/templates`

**查询参数：**
- `skip` (int, 默认: 0) - 跳过记录数
- `limit` (int, 默认: 100) - 返回记录数
- `q` (string, 可选) - 搜索关键词（模板名称或描述）
- `template_type` (string, 可选) - 按类型筛选
- `status` (string, 可选) - 按状态筛选

**响应示例：**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "增值税发票模板",
      "template_type": "增值税发票",
      "description": "标准增值税发票模板",
      "status": "enabled",
      "current_version": "v1.0.0",
      "accuracy": 0.95,
      "create_time": "2024-12-20T10:00:00",
      "update_time": "2024-12-20T15:00:00"
    }
  ],
  "count": 10,
  "skip": 0,
  "limit": 100
}
```

### 2. 获取模板详情
**GET** `/api/v1/templates/{template_id}`

**查询参数：**
- `version` (string, 可选) - 指定版本号，不传则返回最新发布版本

**响应示例：**
```json
{
  "id": "uuid",
  "name": "增值税发票模板",
  "template_type": "增值税发票",
  "description": "标准增值税发票模板",
  "status": "enabled",
  "current_version": {
    "id": "uuid",
    "version": "v1.0.0",
    "status": "published",
    "created_at": "2024-12-20T10:00:00",
    "published_at": "2024-12-20T12:00:00"
  },
  "fields": [
    {
      "id": "uuid",
      "field_key": "invoice_no",
      "field_name": "发票号码",
      "data_type": "string",
      "is_required": true,
      "description": "发票号码",
      "example": "12345678",
      "validation": {
        "regex": "^[0-9]{8,12}$"
      },
      "sort_order": 0
    }
  ]
}
```

### 3. 创建模板
**POST** `/api/v1/templates`

**请求体：**
```json
{
  "name": "增值税发票模板",
  "template_type": "增值税发票",
  "description": "标准增值税发票模板",
  "status": "enabled"
}
```

**响应示例：**
```json
{
  "message": "模板创建成功",
  "data": {
    "template_id": "uuid"
  }
}
```

### 4. 更新模板
**PUT** `/api/v1/templates/{template_id}`

**请求体：**
```json
{
  "name": "增值税发票模板（更新）",
  "template_type": "增值税发票",
  "description": "更新后的描述",
  "status": "enabled"
}
```

**响应示例：**
```json
{
  "message": "模板更新成功"
}
```

### 5. 获取模板Schema
**GET** `/api/v1/templates/{template_id}/schema`

**查询参数：**
- `version` (string, 可选) - 指定版本号，默认为最新发布版本

**响应示例：**
```json
{
  "template": {
    "id": "uuid",
    "name": "增值税发票模板",
    "type": "增值税发票",
    "version": "v1.0.0"
  },
  "fields": [
    {
      "key": "invoice_no",
      "name": "发票号码",
      "type": "string",
      "required": true,
      "example": "12345678",
      "validation": {
        "regex": "^[0-9]{8,12}$"
      },
      "hint": "发票号码通常是8-12位数字"
    }
  ]
}
```

## 使用说明

### 1. 创建模板流程
1. 调用 `POST /api/v1/templates` 创建模板基础信息
2. 系统自动创建初始草稿版本（v1.0.0）
3. 通过模板编辑接口添加字段
4. 发布版本后生成 schema_snapshot

### 2. 版本管理
- **草稿（draft）**：可编辑状态
- **已发布（published）**：冻结状态，生成 schema_snapshot
- **已废弃（deprecated）**：不再使用

### 3. Schema快照
- 发布版本时自动生成 schema_snapshot
- schema_snapshot 是不可变的 JSON 结构
- 用于识别任务时传递给 Dify/LLM

### 4. 字段嵌套
- 支持通过 `parent_field_id` 实现字段嵌套
- 适用于明细行等复杂结构（如发票明细）

## 数据库迁移

运行以下命令创建数据库表：

```bash
cd backend
alembic upgrade head
```

迁移文件：`backend/app/alembic/versions/add_template_management_tables.py`

