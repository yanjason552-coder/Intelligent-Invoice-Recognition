# 孔位类模板字段属性表（参考）

根据提供的 JSON Schema，以下是"孔位类"模板应该包含的字段：

## 顶层字段（10个）

| 序号 | 字段标识 | 字段名称 | 数据名称 | 数据类型 | 是否必填 | 描述 |
|------|---------|---------|---------|---------|---------|------|
| 1 | doc_type | 文档类型 | doc_type | string | 是 | 固定值 dimension_inspection，用于区分表单类型 |
| 2 | form_title | 表单标题 | form_title | string \| null | 是 | 表单标题/名称；图片没有明确出现则为 null |
| 3 | drawing_no | 图号/项目号 | drawing_no | string \| null | 是 | 图号/图纸编号/项目号（若能识别） |
| 4 | part_name | 零件名称 | part_name | string \| null | 是 | 零件名称（若能识别） |
| 5 | part_no | 零件号/编号 | part_no | string \| null | 是 | 零件号/编号（若能识别） |
| 6 | date | 日期 | date | string \| null | 是 | 日期，建议输出 YYYY-MM-DD；若无法规范化则保留原字符串 |
| 7 | inspector_name | 检验员 | inspector_name | string \| null | 是 | 检验员/检验员签字（手写名） |
| 8 | overall_result | 整单结论 | overall_result | enum | 是 | 整单结论（若表上有总体合格/不合格，否则 unknown），枚举值：pass/fail/unknown |
| 9 | remarks | 备注 | remarks | string \| null | 是 | 备注（如有） |
| 10 | items | 明细行列表 | items | array | 是 | 明细行（每个检验项一行） |

## items[]（明细行）字段（7个）

| 序号 | 字段标识 | 字段名称 | 数据名称 | 数据类型 | 是否必填 | 描述 |
|------|---------|---------|---------|---------|---------|------|
| 11 | items.item_no | 明细序号 | item_no | integer \| null | 是 | 序号（如 4、5、6...）；若无法识别可为 null |
| 12 | items.inspection_item | 检验项目 | inspection_item | string \| null | 是 | 检验项目/检验项名称 |
| 13 | items.spec_requirement | 要求/规格 | spec_requirement | string \| null | 是 | 要求/规格（尽量保留φ、±、深、M螺纹等符号） |
| 14 | items.actual_value | 实际值 | actual_value | string \| null | 是 | 实际值（可能是数值/多个数值/OK/角度测点组合；优先保留原含义） |
| 15 | items.judgement | 判定 | judgement | enum | 是 | 判定：根据合格/不合格勾选框，枚举值：pass/fail/unknown |
| 16 | items.measurements | 多测点明细 | measurements | array | 是 | 可选：如果能明确拆分多个测点/角度值，请填入 |
| 17 | items.notes | 行备注 | notes | string \| null | 是 | 该行备注（若有） |

## items[].measurements[]（多测点/角度值）字段（3个）

| 序号 | 字段标识 | 字段名称 | 数据名称 | 数据类型 | 是否必填 | 描述 |
|------|---------|---------|---------|---------|---------|------|
| 18 | items.measurements.angle | 角度 | angle | string \| null | 是 | 角度，如 0°, 90°, 180°；不确定则 null |
| 19 | items.measurements.point_label | 测点标签 | point_label | string \| null | 是 | 测点标签，如 A点/B点/上/下/左/右；不确定则 null |
| 20 | items.measurements.value | 测点实测值 | value | string \| null | 是 | 该测点的实测值（保持原文） |

## 总计：20个字段

**注意**：
- 此模板是尺寸检验记录模板，**不包含**发票相关字段（如发票抬头、发票号码、采购订单号等）
- 如果发现模板中有发票相关字段，说明字段定义有误，需要清理

