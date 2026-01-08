# 票据识别系统数据库表结构说明

## 概述

本文档描述了票据识别系统的数据库表结构，包括所有表、字段、索引和关联关系。

## 表结构

### 1. invoice_file（票据文件表）

存储上传的票据文件信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| file_name | VARCHAR(255) | 文件名 | NOT NULL |
| file_path | VARCHAR(500) | 文件存储路径 | NOT NULL |
| file_size | INTEGER | 文件大小（字节） | NOT NULL |
| file_type | VARCHAR(50) | 文件类型（pdf/jpg/png） | NOT NULL |
| mime_type | VARCHAR(100) | MIME类型 | NOT NULL |
| upload_time | DATETIME | 上传时间 | NOT NULL |
| uploader_id | UUID | 上传人ID | FOREIGN KEY -> user.id |
| status | VARCHAR(20) | 状态：uploaded/processing/processed/error | DEFAULT 'uploaded' |

**索引：**
- file_name

**关联关系：**
- 一对多：Invoice (一个文件可以对应多个票据)

---

### 2. template（模板表）

存储识别模板信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| name | VARCHAR(100) | 模板名称 | NOT NULL |
| type | VARCHAR(50) | 模板类型 | NOT NULL |
| description | TEXT | 模板描述 | |
| status | VARCHAR(20) | 状态：active/inactive/training | DEFAULT 'active' |
| version | VARCHAR(20) | 版本号 | NOT NULL |
| template_file_path | VARCHAR(500) | 模板文件路径 | |
| sample_image_path | VARCHAR(500) | 样例图片路径 | |
| accuracy | FLOAT | 准确率 | |
| training_samples | INTEGER | 训练样本数 | DEFAULT 0 |
| last_training_time | DATETIME | 最后训练时间 | |
| creator_id | UUID | 创建人ID | FOREIGN KEY -> user.id |
| create_time | DATETIME | 创建时间 | NOT NULL |
| update_time | DATETIME | 更新时间 | |

**索引：**
- name

**关联关系：**
- 一对多：TemplateField（一个模板有多个字段）
- 一对多：TemplateTrainingTask（一个模板有多个训练任务）
- 一对多：Invoice（一个模板可以识别多个票据）

---

### 3. template_field（模板字段表）

存储模板字段定义。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| template_id | UUID | 模板ID | FOREIGN KEY -> template.id |
| field_name | VARCHAR(100) | 字段名称 | NOT NULL |
| field_code | VARCHAR(50) | 字段代码 | NOT NULL |
| field_type | VARCHAR(20) | 字段类型（text/number/date等） | NOT NULL |
| is_required | BOOLEAN | 是否必填 | DEFAULT false |
| position | JSON | 字段位置信息 | |
| validation_rules | JSON | 验证规则 | |
| display_order | INTEGER | 显示顺序 | DEFAULT 0 |
| remark | VARCHAR(200) | 备注 | |
| create_time | DATETIME | 创建时间 | NOT NULL |

**关联关系：**
- 多对一：Template（多个字段属于一个模板）
- 一对多：RecognitionField（一个模板字段对应多个识别字段）

---

### 4. template_training_task（模板训练任务表）

存储模板训练任务信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| task_no | VARCHAR(100) | 任务编号 | UNIQUE, NOT NULL |
| template_id | UUID | 模板ID | FOREIGN KEY -> template.id |
| status | VARCHAR(20) | 状态：pending/training/completed/failed | DEFAULT 'pending' |
| training_samples | INTEGER | 训练样本数 | DEFAULT 0 |
| training_data_path | VARCHAR(500) | 训练数据路径 | |
| accuracy | FLOAT | 训练后准确率 | |
| model_path | VARCHAR(500) | 模型文件路径 | |
| start_time | DATETIME | 开始时间 | |
| end_time | DATETIME | 结束时间 | |
| duration | FLOAT | 耗时（秒） | |
| error_message | TEXT | 错误信息 | |
| operator_id | UUID | 操作人ID | FOREIGN KEY -> user.id |
| create_time | DATETIME | 创建时间 | NOT NULL |

**索引：**
- task_no (UNIQUE)

**关联关系：**
- 多对一：Template（多个训练任务属于一个模板）

---

### 5. invoice（票据表）

存储票据基本信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| invoice_no | VARCHAR(100) | 票据编号 | NOT NULL, INDEX |
| invoice_type | VARCHAR(50) | 票据类型 | NOT NULL |
| invoice_date | DATETIME | 开票日期 | |
| amount | FLOAT | 金额（不含税） | |
| tax_amount | FLOAT | 税额 | |
| total_amount | FLOAT | 合计金额 | |
| supplier_name | VARCHAR(200) | 供应商名称 | |
| supplier_tax_no | VARCHAR(50) | 供应商税号 | |
| buyer_name | VARCHAR(200) | 采购方名称 | |
| buyer_tax_no | VARCHAR(50) | 采购方税号 | |
| file_id | UUID | 文件ID | FOREIGN KEY -> invoice_file.id |
| template_id | UUID | 使用的模板ID | FOREIGN KEY -> template.id |
| recognition_accuracy | FLOAT | 识别准确率 | |
| recognition_status | VARCHAR(20) | 识别状态：pending/processing/completed/failed | DEFAULT 'pending' |
| review_status | VARCHAR(20) | 审核状态：pending/approved/rejected | DEFAULT 'pending' |
| reviewer_id | UUID | 审核人ID | FOREIGN KEY -> user.id |
| review_time | DATETIME | 审核时间 | |
| review_comment | TEXT | 审核意见 | |
| remark | VARCHAR(500) | 备注 | |
| creator_id | UUID | 创建人ID | FOREIGN KEY -> user.id |
| create_time | DATETIME | 创建时间 | NOT NULL |
| update_time | DATETIME | 更新时间 | |

**索引：**
- invoice_no

**关联关系：**
- 多对一：InvoiceFile（多个票据可以来自同一个文件）
- 多对一：Template（多个票据使用同一个模板）
- 一对多：RecognitionResult（一个票据可以有多个识别结果）
- 一对多：RecognitionField（一个票据有多个识别字段）
- 一对多：ReviewRecord（一个票据有多条审核记录）

---

### 6. recognition_task（识别任务表）

存储识别任务信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| task_no | VARCHAR(100) | 任务编号 | UNIQUE, NOT NULL |
| invoice_id | UUID | 票据ID | FOREIGN KEY -> invoice.id |
| template_id | UUID | 模板ID | FOREIGN KEY -> template.id |
| status | VARCHAR(20) | 任务状态：pending/processing/completed/failed | DEFAULT 'pending' |
| priority | INTEGER | 优先级 | DEFAULT 0 |
| start_time | DATETIME | 开始时间 | |
| end_time | DATETIME | 结束时间 | |
| duration | FLOAT | 耗时（秒） | |
| error_message | TEXT | 错误信息 | |
| operator_id | UUID | 操作人ID | FOREIGN KEY -> user.id |
| create_time | DATETIME | 创建时间 | NOT NULL |

**索引：**
- task_no (UNIQUE)

**关联关系：**
- 多对一：Invoice（多个任务对应一个票据）
- 多对一：Template（多个任务使用同一个模板）
- 一对一：RecognitionResult（一个任务对应一个识别结果）

---

### 7. recognition_result（识别结果表）

存储识别结果。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| invoice_id | UUID | 票据ID | FOREIGN KEY -> invoice.id |
| task_id | UUID | 任务ID | FOREIGN KEY -> recognition_task.id, UNIQUE |
| total_fields | INTEGER | 总字段数 | DEFAULT 0 |
| recognized_fields | INTEGER | 已识别字段数 | DEFAULT 0 |
| accuracy | FLOAT | 整体准确率 | NOT NULL |
| confidence | FLOAT | 置信度 | NOT NULL |
| status | VARCHAR(20) | 状态：success/failed/partial | DEFAULT 'success' |
| raw_data | JSON | 原始识别数据 | |
| recognition_time | DATETIME | 识别时间 | NOT NULL |
| create_time | DATETIME | 创建时间 | NOT NULL |

**关联关系：**
- 多对一：Invoice（多个结果对应一个票据）
- 一对一：RecognitionTask（一个结果对应一个任务）
- 一对多：RecognitionField（一个结果有多个识别字段）

---

### 8. recognition_field（识别字段表）

存储识别出的具体字段。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| invoice_id | UUID | 票据ID | FOREIGN KEY -> invoice.id |
| result_id | UUID | 识别结果ID | FOREIGN KEY -> recognition_result.id |
| template_field_id | UUID | 模板字段ID | FOREIGN KEY -> template_field.id |
| field_name | VARCHAR(100) | 字段名称 | NOT NULL |
| field_value | TEXT | 字段值 | |
| original_value | TEXT | 原始识别值 | |
| confidence | FLOAT | 置信度 | NOT NULL |
| accuracy | FLOAT | 准确率 | NOT NULL |
| position | JSON | 字段位置信息 | |
| is_manual_corrected | BOOLEAN | 是否手动修正 | DEFAULT false |
| corrected_by | UUID | 修正人ID | FOREIGN KEY -> user.id |
| corrected_time | DATETIME | 修正时间 | |
| create_time | DATETIME | 创建时间 | NOT NULL |

**关联关系：**
- 多对一：Invoice（多个字段属于一个票据）
- 多对一：RecognitionResult（多个字段属于一个识别结果）
- 多对一：TemplateField（多个识别字段对应一个模板字段）

---

### 9. review_record（审核记录表）

存储审核记录。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| invoice_id | UUID | 票据ID | FOREIGN KEY -> invoice.id |
| review_status | VARCHAR(20) | 审核状态：approved/rejected | NOT NULL |
| review_comment | TEXT | 审核意见 | |
| reviewer_id | UUID | 审核人ID | FOREIGN KEY -> user.id |
| review_time | DATETIME | 审核时间 | NOT NULL |
| review_details | JSON | 审核详情（存储修改的字段） | |

**关联关系：**
- 多对一：Invoice（多条审核记录对应一个票据）

---

### 10. ocr_config（OCR配置表）

存储OCR配置。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| config_key | VARCHAR(100) | 配置键 | UNIQUE, NOT NULL |
| config_value | TEXT | 配置值（JSON格式） | NOT NULL |
| description | VARCHAR(200) | 配置描述 | |
| update_time | DATETIME | 更新时间 | NOT NULL |
| updater_id | UUID | 更新人ID | FOREIGN KEY -> user.id |

**索引：**
- config_key (UNIQUE)

---

### 11. recognition_rule（识别规则表）

存储识别规则。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| rule_name | VARCHAR(100) | 规则名称 | NOT NULL |
| rule_type | VARCHAR(50) | 规则类型（validation/format/extract等） | NOT NULL |
| rule_definition | JSON | 规则定义 | NOT NULL |
| template_id | UUID | 应用的模板ID（null表示全局规则） | FOREIGN KEY -> template.id |
| field_name | VARCHAR(100) | 应用的字段名（null表示模板级规则） | |
| is_active | BOOLEAN | 是否启用 | DEFAULT true |
| priority | INTEGER | 优先级 | DEFAULT 0 |
| remark | VARCHAR(200) | 备注 | |
| creator_id | UUID | 创建人ID | FOREIGN KEY -> user.id |
| create_time | DATETIME | 创建时间 | NOT NULL |
| update_time | DATETIME | 更新时间 | |

**关联关系：**
- 多对一：Template（多个规则可以应用于一个模板，null表示全局规则）

---

## 表关系图

```
user
  ├── invoice_file (uploader_id)
  ├── template (creator_id)
  ├── template_training_task (operator_id)
  ├── invoice (creator_id, reviewer_id)
  ├── recognition_task (operator_id)
  ├── recognition_field (corrected_by)
  ├── review_record (reviewer_id)
  ├── ocr_config (updater_id)
  └── recognition_rule (creator_id)

invoice_file
  └── invoice (file_id)

template
  ├── template_field (template_id)
  ├── template_training_task (template_id)
  ├── invoice (template_id)
  ├── recognition_task (template_id)
  └── recognition_rule (template_id)

invoice
  ├── recognition_task (invoice_id)
  ├── recognition_result (invoice_id)
  ├── recognition_field (invoice_id)
  └── review_record (invoice_id)

recognition_task
  └── recognition_result (task_id)

recognition_result
  └── recognition_field (result_id)

template_field
  └── recognition_field (template_field_id)
```

## 数据流程

1. **文件上传流程：**
   - 用户上传文件 → `invoice_file` 表
   - 创建票据记录 → `invoice` 表（关联 `invoice_file`）

2. **识别流程：**
   - 创建识别任务 → `recognition_task` 表
   - 执行识别 → 生成 `recognition_result` 和 `recognition_field`
   - 更新票据状态 → `invoice.recognition_status`

3. **审核流程：**
   - 创建审核记录 → `review_record` 表
   - 更新票据审核状态 → `invoice.review_status`

4. **模板管理流程：**
   - 创建模板 → `template` 表
   - 定义字段 → `template_field` 表
   - 训练模板 → `template_training_task` 表

## 索引建议

为了提高查询性能，建议在以下字段上创建索引：

1. `invoice.invoice_no` - 已创建
2. `invoice.recognition_status` - 用于查询待识别票据
3. `invoice.review_status` - 用于查询待审核票据
4. `invoice.create_time` - 用于按时间排序
5. `recognition_task.status` - 用于查询任务状态
6. `template.status` - 用于查询可用模板

## 注意事项

1. 所有外键都设置了 `ondelete="CASCADE"` 或 `ondelete="SET NULL"`，确保数据一致性
2. JSON 字段用于存储灵活的结构化数据（位置信息、规则定义等）
3. 时间字段使用 `datetime.now` 作为默认值
4. UUID 作为主键，确保分布式环境下的唯一性
5. 状态字段使用字符串类型，便于扩展和查询


