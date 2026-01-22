import pandas as pd
import sqlite3
import os
import sys

def read_excel_sheet():
    """读取Excel文件中的sales_order_doc_d_feature表定义"""
    try:
        # 读取Excel文件
        excel_file = 'database.xlsx'
        sheet_name = 'sales_order_doc_d_feature'
        
        print(f"正在读取 {excel_file} 中的 {sheet_name} 表定义...")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"文件是否存在: {os.path.exists(excel_file)}")
        
        # 首先列出Excel文件中的所有sheet
        xl_file = pd.ExcelFile(excel_file)
        print(f"Excel文件中的所有sheet: {xl_file.sheet_names}")
        
        if sheet_name not in xl_file.sheet_names:
            print(f"错误: 找不到sheet '{sheet_name}'")
            print(f"可用的sheet: {xl_file.sheet_names}")
            return None
        
        # 读取指定sheet
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        print(f"成功读取sheet '{sheet_name}'")
        print(f"数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")
        
        print("\n原始数据:")
        print(df.to_string(index=False))
        
        return df
        
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        print(f"错误类型: {type(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_create_table_sql(df):
    """根据DataFrame生成CREATE TABLE SQL语句"""
    if df is None or df.empty:
        print("没有数据可以生成SQL")
        return None
    
    print("\n正在生成CREATE TABLE SQL语句...")
    
    # 获取列名
    columns = df.columns.tolist()
    print(f"Excel文件列名: {columns}")
    
    # 生成SQL语句
    sql_parts = []
    sql_parts.append("CREATE TABLE IF NOT EXISTS sales_order_doc_d_feature (")
    
    # 查找实际的字段定义行
    # 从第6行开始是实际的字段定义（根据输出结果判断）
    field_rows = []
    
    for index, row in df.iterrows():
        # 跳过表头信息，只处理实际的字段定义
        if index < 5:  # 跳过前5行表头
            continue
            
        # 检查是否是有效的字段定义行
        field_name = str(row.iloc[0]) if len(row) > 0 and pd.notna(row.iloc[0]) else ""
        
        # 如果字段名为空或包含中文表头信息，跳过
        if not field_name or field_name in ['字段名', '中文名', '业务主键', '索引']:
            continue
            
        # 检查是否是有效的字段名（不包含中文表头）
        if any(char in field_name for char in ['字段名', '中文名', '业务主键', '索引', '返回首页']):
            continue
            
        print(f"处理字段定义行 {index + 1}: {row.tolist()}")
        
        # 解析字段信息
        field_name = str(row.iloc[0]).strip()
        field_comment = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        data_type = str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else "VARCHAR(255)"
        is_nullable = row.iloc[3] if len(row) > 3 and pd.notna(row.iloc[3]) else "YES"
        default_value = row.iloc[4] if len(row) > 4 and pd.notna(row.iloc[4]) else None
        is_primary = row.iloc[5] if len(row) > 5 and pd.notna(row.iloc[5]) else None
        comment = str(row.iloc[6]).strip() if len(row) > 6 and pd.notna(row.iloc[6]) else ""
        
        # 处理数据类型
        if 'varchar' in data_type.lower():
            data_type = 'VARCHAR(200)'
        elif 'vchar' in data_type.lower():
            data_type = 'VARCHAR(20)'
        elif 'timestamp' in data_type.lower():
            data_type = 'DATETIME'
        
        # 构建字段定义
        field_def = f"    {field_name} {data_type}"
        
        # 添加NOT NULL约束
        if is_nullable and str(is_nullable).upper() in ['F', 'NO', 'NOT NULL', 'FALSE', '0', 'N']:
            field_def += " NOT NULL"
        
        # 添加默认值
        if default_value and str(default_value).upper() != 'NAN':
            if isinstance(default_value, str):
                field_def += f" DEFAULT '{default_value}'"
            else:
                field_def += f" DEFAULT {default_value}"
        
        # 添加注释
        if comment and str(comment).upper() != 'NAN':
            field_def += f" -- {comment}"
        
        sql_parts.append(field_def)
        print(f"  生成字段: {field_def}")
        
        field_rows.append({
            'name': field_name,
            'type': data_type,
            'is_primary': is_primary == 'T',
            'comment': comment
        })
    
    # 添加主键约束
    primary_keys = [field['name'] for field in field_rows if field['is_primary']]
    if primary_keys:
        sql_parts.append(f"    PRIMARY KEY ({', '.join(primary_keys)})")
    
    sql_parts.append(");")
    
    # 修复SQL语句，在字段之间添加逗号
    sql_statement = "\n".join(sql_parts)
    
    # 在字段定义之间添加逗号
    lines = sql_statement.split('\n')
    fixed_lines = []
    for i, line in enumerate(lines):
        fixed_lines.append(line)
        # 如果不是最后一行，且下一行不是PRIMARY KEY或结束括号，则添加逗号
        if (i < len(lines) - 1 and 
            line.strip().startswith('    ') and 
            not line.strip().startswith('PRIMARY KEY') and
            not lines[i + 1].strip().startswith('PRIMARY KEY') and
            not lines[i + 1].strip() == ');'):
            fixed_lines.append(',')
    
    sql_statement = '\n'.join(fixed_lines)
    
    print("\n生成的SQL语句:")
    print(sql_statement)
    
    return sql_statement

def create_table_in_database(sql_statement):
    """在数据库中执行CREATE TABLE语句"""
    try:
        # 连接到SQLite数据库
        db_path = 'sales_order.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n正在在数据库 {db_path} 中创建表...")
        
        # 执行SQL语句
        cursor.execute(sql_statement)
        
        # 提交更改
        conn.commit()
        
        print("表创建成功！")
        
        # 验证表是否创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales_order_doc_d_feature';")
        result = cursor.fetchone()
        
        if result:
            print("表验证成功！")
            
            # 显示表结构
            cursor.execute("PRAGMA table_info(sales_order_doc_d_feature);")
            table_info = cursor.fetchall()
            
            print("\n表结构:")
            for column in table_info:
                print(f"  {column[1]} {column[2]} {'NOT NULL' if column[3] else 'NULL'}")
        
        conn.close()
        
    except Exception as e:
        print(f"创建表失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("=== Excel表定义读取和数据库表创建工具 ===\n")
    
    # 1. 读取Excel文件
    df = read_excel_sheet()
    
    if df is not None:
        # 2. 生成SQL语句
        sql_statement = generate_create_table_sql(df)
        
        if sql_statement:
            # 3. 在数据库中创建表
            create_table_in_database(sql_statement)
    
    print("\n=== 完成 ===")

if __name__ == "__main__":
    main() 