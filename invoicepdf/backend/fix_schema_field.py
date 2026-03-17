#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""删除Template模型中的schema字段"""

import re

import os
file_path = os.path.join(os.path.dirname(__file__), 'app', 'models', 'models_invoice.py')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 删除schema字段及其注释
pattern = r'\n    # Schema JSON（新增）\n    schema: Optional\[dict\] = Field\(default=None, sa_column=Column\(JSON\), description="模板 Schema JSON 定义"\)\n'
new_content = re.sub(pattern, '\n', content)

if new_content != content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('✓ 已成功删除schema字段')
else:
    print('⚠ 未找到schema字段，可能已经被删除')

