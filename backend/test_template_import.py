"""
测试模板导入功能
用于调试导入过程中的问题
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from io import BytesIO
from app.api.routes.template import _parse_excel_template, _generate_field_key, _infer_data_type
import openpyxl

def test_excel_parsing():
    """测试Excel解析"""
    # 创建一个简单的测试Excel文件
    wb = openpyxl.Workbook()
    ws = wb.active
    
    # 添加测试数据（第一行为字段名）
    headers = ['发票号码', '开票日期', '金额', '供应商名称', '购买方名称']
    ws.append(headers)
    
    # 保存到内存
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    # 测试解析
    try:
        fields = _parse_excel_template(buffer.getvalue(), 'xlsx')
        print(f"✓ 解析成功，识别到 {len(fields)} 个字段")
        for field in fields:
            print(f"  - {field['field_name']} ({field['field_key']}) - {field['data_type']}")
        return True
    except Exception as e:
        print(f"✗ 解析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_field_key_generation():
    """测试字段标识生成"""
    test_cases = [
        ('发票号码', 0),
        ('开票日期', 1),
        ('金额', 2),
        ('供应商名称', 3),
        ('', 4),
        ('测试字段', 5),
    ]
    
    print("\n测试字段标识生成:")
    for field_name, idx in test_cases:
        key = _generate_field_key(field_name, idx)
        print(f"  '{field_name}' -> '{key}'")

if __name__ == "__main__":
    print("=" * 60)
    print("测试模板导入功能")
    print("=" * 60)
    
    test_field_key_generation()
    print()
    test_excel_parsing()

