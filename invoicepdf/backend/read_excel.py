import pandas as pd

try:
    # 读取Excel文件中的sales_order_doc_d表
    df = pd.read_excel('database.xls', sheet_name='sales_order_doc_d', header=None)
    
    print("=== sales_order_doc_d 表结构 ===")
    print(f"行数: {len(df)}")
    print(f"列数: {len(df.columns)}")
    
    print("\n=== 完整数据 ===")
    for i in range(len(df)):
        row_data = []
        for j in range(len(df.columns)):
            value = df.iloc[i, j]
            if pd.notna(value):
                row_data.append(str(value))
        if row_data:
            print(f"行 {i+1}: {row_data}")
    
    # 尝试找到字段定义部分
    print("\n=== 字段定义部分 ===")
    for i in range(len(df)):
        row = df.iloc[i]
        if any(pd.notna(cell) and '字段名' in str(cell) for cell in row):
            print(f"找到字段定义行 {i+1}: {[str(cell) for cell in row if pd.notna(cell)]}")
            # 显示后续的字段定义
            for j in range(i+1, len(df)):
                next_row = df.iloc[j]
                if any(pd.notna(cell) for cell in next_row):
                    print(f"字段行 {j+1}: {[str(cell) for cell in next_row if pd.notna(cell)]}")
                else:
                    break
            break
        
except Exception as e:
    print(f"读取Excel文件时出错: {e}")
    
    # 尝试列出所有sheet名称
    try:
        xl = pd.ExcelFile('database.xls')
        print(f"\nExcel文件中的所有sheet: {xl.sheet_names}")
    except Exception as e2:
        print(f"无法读取Excel文件: {e2}") 