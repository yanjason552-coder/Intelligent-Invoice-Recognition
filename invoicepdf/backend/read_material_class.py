#!/usr/bin/env python3
"""
读取 database.xlsx 中 material_class 表的结构
"""

import pandas as pd

def read_material_class_structure():
    """读取 material_class 表的结构"""
    try:
        # 读取 Excel 文件，跳过前几行标题
        df = pd.read_excel('database.xlsx', sheet_name='material_class', header=None)
        
        print("=== material_class 表结构定义 ===")
        
        # 从第6行开始解析字段定义（索引5）
        field_definitions = []
        for i in range(6, len(df)):
            row = df.iloc[i]
            if pd.isna(row[0]) or str(row[0]).strip() == '':
                continue
                
            field_name = str(row[0]).strip()
            field_desc = str(row[1]).strip() if not pd.isna(row[1]) else ''
            data_type = str(row[2]).strip() if not pd.isna(row[2]) else ''
            allow_null = str(row[3]).strip() if not pd.isna(row[3]) else ''
            default_value = str(row[4]).strip() if not pd.isna(row[4]) else ''
            is_primary = str(row[5]).strip() if not pd.isna(row[5]) else ''
            description = str(row[6]).strip() if not pd.isna(row[6]) else ''
            
            field_definitions.append({
                'field_name': field_name,
                'field_desc': field_desc,
                'data_type': data_type,
                'allow_null': allow_null,
                'default_value': default_value,
                'is_primary': is_primary,
                'description': description
            })
            
            print(f"字段 {len(field_definitions)}: {field_name}")
            print(f"  描述: {field_desc}")
            print(f"  数据类型: {data_type}")
            print(f"  允许NULL: {allow_null}")
            print(f"  默认值: {default_value}")
            print(f"  主键: {is_primary}")
            print(f"  说明: {description}")
            print()
        
        return field_definitions
        
    except Exception as e:
        print(f"读取失败: {e}")
        return None

if __name__ == "__main__":
    read_material_class_structure() 