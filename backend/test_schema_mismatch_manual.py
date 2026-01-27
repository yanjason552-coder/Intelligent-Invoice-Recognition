"""
Schema 不匹配处理手动测试脚本
用于快速测试和调试
"""

import asyncio
import json
from app.services.schema_mismatch_handler import schema_mismatch_handler


async def test_scenario_1_missing_field():
    """测试场景1: 缺失必填字段"""
    print("\n" + "="*60)
    print("场景1: 缺失必填字段")
    print("="*60)
    
    output_data = {
        "invoice_date": "2024-01-01",
        "total_amount": 1000.00
        # 缺少 invoice_no
    }
    
    print(f"输入数据: {json.dumps(output_data, ensure_ascii=False, indent=2)}")
    
    result = await schema_mismatch_handler.handle_mismatch(
        output_data=output_data,
        schema_id=None,
        model_config_id=None,
        handling_strategy="auto"
    )
    
    print(f"\n不匹配: {result.has_mismatch}")
    print(f"错误数: {result.total_errors}")
    print(f"警告数: {result.total_warnings}")
    print(f"需要人工审核: {result.requires_manual_review}")
    print(f"\n不匹配项:")
    for item in result.mismatch_items:
        print(f"  - {item.field_path}: {item.message} (严重程度: {item.severity.value})")
    
    if result.repair_result:
        print(f"\n修复结果: {'成功' if result.repair_result.success else '失败'}")
        print(f"修复动作: {len(result.repair_result.repair_actions)} 个")
        for action in result.repair_result.repair_actions[:3]:  # 只显示前3个
            print(f"  - {action}")
    
    print(f"\n最终数据: {json.dumps(result.final_data, ensure_ascii=False, indent=2)}")


async def test_scenario_2_type_mismatch():
    """测试场景2: 类型不匹配"""
    print("\n" + "="*60)
    print("场景2: 类型不匹配")
    print("="*60)
    
    output_data = {
        "invoice_no": 12345678,  # 应该是字符串
        "invoice_date": "2024-01-01",
        "total_amount": "1000.00"  # 应该是数字
    }
    
    print(f"输入数据: {json.dumps(output_data, ensure_ascii=False, indent=2)}")
    
    result = await schema_mismatch_handler.handle_mismatch(
        output_data=output_data,
        schema_id=None,
        model_config_id=None,
        handling_strategy="auto"
    )
    
    print(f"\n不匹配: {result.has_mismatch}")
    print(f"错误数: {result.total_errors}")
    print(f"需要人工审核: {result.requires_manual_review}")
    
    if result.repair_result and result.repair_result.success:
        print(f"\n修复成功！")
        print(f"修复后数据: {json.dumps(result.final_data, ensure_ascii=False, indent=2)}")
    else:
        print(f"\n修复失败或未尝试修复")


async def test_scenario_3_extra_field():
    """测试场景3: 额外字段"""
    print("\n" + "="*60)
    print("场景3: 额外字段")
    print("="*60)
    
    output_data = {
        "invoice_no": "12345678",
        "invoice_date": "2024-01-01",
        "total_amount": 1000.00,
        "extra_field": "not_allowed",
        "another_extra": 123
    }
    
    print(f"输入数据: {json.dumps(output_data, ensure_ascii=False, indent=2)}")
    
    result = await schema_mismatch_handler.handle_mismatch(
        output_data=output_data,
        schema_id=None,
        model_config_id=None,
        handling_strategy="auto"
    )
    
    print(f"\n不匹配: {result.has_mismatch}")
    print(f"警告数: {result.total_warnings}")
    print(f"\n最终数据: {json.dumps(result.final_data, ensure_ascii=False, indent=2)}")


async def test_scenario_4_valid_data():
    """测试场景4: 有效数据"""
    print("\n" + "="*60)
    print("场景4: 有效数据")
    print("="*60)
    
    output_data = {
        "invoice_no": "12345678",
        "invoice_date": "2024-01-01",
        "total_amount": 1000.00
    }
    
    print(f"输入数据: {json.dumps(output_data, ensure_ascii=False, indent=2)}")
    
    result = await schema_mismatch_handler.handle_mismatch(
        output_data=output_data,
        schema_id=None,
        model_config_id=None,
        handling_strategy="auto"
    )
    
    print(f"\n不匹配: {result.has_mismatch}")
    print(f"错误数: {result.total_errors}")
    print(f"警告数: {result.total_warnings}")
    
    if not result.has_mismatch:
        print("\n✓ 数据验证通过，无错误")


async def test_scenario_5_ignore_strategy():
    """测试场景5: 忽略策略"""
    print("\n" + "="*60)
    print("场景5: 忽略策略")
    print("="*60)
    
    output_data = {
        "invoice_no": 12345678,  # 类型错误
        "invoice_date": "2024-01-01"
    }
    
    print(f"输入数据: {json.dumps(output_data, ensure_ascii=False, indent=2)}")
    
    result = await schema_mismatch_handler.handle_mismatch(
        output_data=output_data,
        schema_id=None,
        model_config_id=None,
        handling_strategy="ignore"
    )
    
    print(f"\n处理策略: {result.handling_strategy}")
    print(f"最终数据: {json.dumps(result.final_data, ensure_ascii=False, indent=2)}")
    print(f"需要人工审核: {result.requires_manual_review}")
    
    assert result.final_data == output_data, "忽略策略应该返回原始数据"


async def main():
    """运行所有测试场景"""
    print("\n" + "="*60)
    print("Schema 不匹配处理手动测试")
    print("="*60)
    
    try:
        await test_scenario_1_missing_field()
        await test_scenario_2_type_mismatch()
        await test_scenario_3_extra_field()
        await test_scenario_4_valid_data()
        await test_scenario_5_ignore_strategy()
        
        print("\n" + "="*60)
        print("所有测试场景完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n测试出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

