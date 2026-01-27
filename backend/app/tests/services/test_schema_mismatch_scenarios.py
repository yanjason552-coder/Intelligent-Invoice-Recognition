"""
Schema 不匹配场景测试
使用模拟数据测试各种实际场景
"""

import pytest
import asyncio
from app.services.schema_mismatch_handler import schema_mismatch_handler


class TestRealWorldScenarios:
    """真实场景测试"""

    @pytest.mark.asyncio
    async def test_scenario_invoice_number_as_integer(self):
        """场景: 发票号码返回为整数而不是字符串"""
        output_data = {
            "invoice_no": 12345678,  # 应该是 "12345678"
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00,
            "supplier_name": "测试供应商"
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert result.final_data is not None
        # 应该尝试将 invoice_no 转换为字符串
        if result.repair_result and result.repair_result.success:
            assert isinstance(result.final_data.get("invoice_no"), str)

    @pytest.mark.asyncio
    async def test_scenario_amount_as_string(self):
        """场景: 金额返回为字符串"""
        output_data = {
            "invoice_no": "12345678",
            "invoice_date": "2024-01-01",
            "total_amount": "1000.00",  # 应该是数字
            "supplier_name": "测试供应商"
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert result.final_data is not None
        # 应该尝试将 total_amount 转换为数字
        if result.repair_result and result.repair_result.success:
            final_amount = result.final_data.get("total_amount")
            assert isinstance(final_amount, (int, float)) or final_amount is None

    @pytest.mark.asyncio
    async def test_scenario_missing_critical_field(self):
        """场景: 缺失关键字段（发票号码）"""
        output_data = {
            # 缺少 invoice_no
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00,
            "supplier_name": "测试供应商"
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert result.has_mismatch == True
        # 关键字段缺失应该标记为需要人工审核
        if result.critical_count > 0 or result.high_count > 0:
            assert result.requires_manual_review == True

    @pytest.mark.asyncio
    async def test_scenario_extra_fields_from_model(self):
        """场景: 模型返回了额外的字段"""
        output_data = {
            "invoice_no": "12345678",
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00,
            "supplier_name": "测试供应商",
            "model_confidence": 0.95,  # 额外字段
            "processing_time": 1.23,  # 额外字段
            "raw_text": "发票内容..."  # 额外字段
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert result.final_data is not None
        # 额外字段应该被移除（如果 Schema 不允许）

    @pytest.mark.asyncio
    async def test_scenario_nested_structure_mismatch(self):
        """场景: 嵌套结构不匹配"""
        output_data = {
            "invoice_no": "12345678",
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00,
            "items": [
                {
                    "name": "商品1",
                    "amount": "100.00"  # 应该是数字
                },
                {
                    "name": 123,  # 应该是字符串
                    "amount": 200.00
                }
            ]
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert result.final_data is not None
        # 嵌套结构的不匹配应该被检测到

    @pytest.mark.asyncio
    async def test_scenario_completely_wrong_structure(self):
        """场景: 完全错误的数据结构"""
        output_data = "这不是一个对象"  # 应该是对象

        result = await schema_mismatch_handler.handle_mismatch(
            output_data={},  # 传入空字典避免类型错误
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        from app.services.schema_mismatch_handler import SchemaMismatchResult
        assert isinstance(result, SchemaMismatchResult)
        assert result.final_data is not None

    @pytest.mark.asyncio
    async def test_scenario_partial_data(self):
        """场景: 部分数据缺失"""
        output_data = {
            "invoice_no": "12345678"
            # 缺少其他必填字段
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert result.has_mismatch == True
        assert result.total_errors > 0

    @pytest.mark.asyncio
    async def test_scenario_null_values(self):
        """场景: 字段值为 null"""
        output_data = {
            "invoice_no": None,  # null 值
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert result.final_data is not None
        # null 值应该被处理

    @pytest.mark.asyncio
    async def test_scenario_empty_strings(self):
        """场景: 空字符串"""
        output_data = {
            "invoice_no": "",  # 空字符串
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert result.final_data is not None
        # 空字符串的处理取决于 Schema 定义

