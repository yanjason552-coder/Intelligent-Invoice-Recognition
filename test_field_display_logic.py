#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字段显示逻辑 - 模拟前端代码逻辑
"""

# 模拟数据库中的 normalized_fields
normalized_fields_db = {
    'date': '2023-10-18',
    'items': [
        {
            'item_no': 4,
            'inspection_item': '盘车支架台面',
            'spec_requirement': 'Φ110(0.035/0)',
            'actual_value': '110.23',
            'judgement': 'pass',
            'range_value': None,
            'notes': None
        }
    ],
    'part_no': '5-4X110?6',
    'remarks': None,
    'doc_type': 'dimension_inspection',
    'part_name': '盘车支架',
    'drawing_no': 'EL8',
    'form_title': '输入法兰喷油?',
    'inspector_name': '?',
    'overall_result': 'pass'
}

print("=" * 80)
print("测试字段显示逻辑")
print("=" * 80)
print()

# 模拟前端代码逻辑（第1104-1119行）
print("【模拟前端字段生成逻辑】")
print(f"normalized_fields 类型: {type(normalized_fields_db)}")
print(f"normalized_fields 是否为字典: {isinstance(normalized_fields_db, dict)}")
print(f"normalized_fields 是否为空: {not normalized_fields_db}")
print()

# 模拟前端代码：Object.keys(invoiceDetail.normalized_fields)
all_keys = list(normalized_fields_db.keys())
print(f"所有字段键: {all_keys}")
print()

# 模拟前端代码：过滤 items 和 null/undefined 字段
filtered_keys = [
    key for key in all_keys
    if key != 'items'  # 排除 items 数组
    and normalized_fields_db[key] is not None  # 排除 null
    and normalized_fields_db[key] is not ...  # 排除 undefined（Python中没有undefined）
]

print(f"过滤后的字段键（排除 items 和 null）: {filtered_keys}")
print()

# 模拟字段名称映射
fieldNameMap = {
    'doc_type': '文档类型',
    'form_title': '表单标题',
    'drawing_no': '图号',
    'part_name': '零件名称',
    'part_no': '零件号',
    'date': '日期',
    'inspector_name': '检验员',
    'overall_result': '总体结果',
    'remarks': '备注',
}

# 生成字段列表
fields = []
for index, key in enumerate(filtered_keys):
    field_name = fieldNameMap.get(key, key.split('_')[0].capitalize() + ' ' + ' '.join(key.split('_')[1:]))
    data_type = 'array' if isinstance(normalized_fields_db[key], list) else type(normalized_fields_db[key]).__name__
    
    fields.append({
        'field_key': key,
        'field_name': field_name,
        'data_type': data_type,
        'is_required': False,
        'description': '',
        'sort_order': index
    })

print(f"生成的字段列表（共 {len(fields)} 个）:")
for field in fields:
    value = normalized_fields_db[field['field_key']]
    print(f"  - {field['field_name']} ({field['field_key']}): {value} [{field['data_type']}]")
print()

# 检查是否会显示
if len(fields) == 0:
    print("[问题] fields.length === 0，前端会返回 null，不显示任何字段")
else:
    print(f"[正常] fields.length = {len(fields)}，前端会显示字段表格")
print()

# 检查前端条件判断
print("【前端条件判断检查】")
print(f"1. invoiceDetail.normalized_fields 存在: {normalized_fields_db is not None}")
print(f"2. fields.length > 0: {len(fields) > 0}")
print(f"3. 是否会显示字段: {normalized_fields_db is not None and len(fields) > 0}")
print()

# 检查是否有 field_defs_snapshot
field_defs_snapshot = None
print(f"field_defs_snapshot: {field_defs_snapshot}")
if field_defs_snapshot:
    print("  [有] 会使用 field_defs_snapshot 生成字段")
else:
    print("  [无] 会从 normalized_fields 自动生成字段")
print()

print("=" * 80)
print("测试完成")
print("=" * 80)

