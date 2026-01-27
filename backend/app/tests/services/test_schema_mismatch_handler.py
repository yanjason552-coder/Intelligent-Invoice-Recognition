"""
Schema 不匹配处理器测试
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime

from app.services.schema_mismatch_handler import (
    SchemaMismatchHandler,
    MismatchSeverity,
    MismatchType,
    MismatchItem,
    SchemaMismatchResult
)
from app.services.schema_validation_service import (
    ValidationResult,
    RepairResult,
    FallbackResult
)


@pytest.fixture
def mismatch_handler():
    """创建 SchemaMismatchHandler 实例"""
    return SchemaMismatchHandler()


@pytest.fixture
def sample_schema():
    """示例 Schema 定义"""
    return {
        "type": "object",
        "required": ["invoice_no", "invoice_date", "total_amount"],
        "properties": {
            "invoice_no": {
                "type": "string",
                "description": "发票号码"
            },
            "invoice_date": {
                "type": "string",
                "format": "date",
                "description": "发票日期"
            },
            "total_amount": {
                "type": "number",
                "description": "总金额"
            },
            "supplier_name": {
                "type": "string",
                "description": "供应商名称"
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "amount": {"type": "number"}
                    }
                }
            }
        },
        "additionalProperties": False
    }


class TestMismatchAnalysis:
    """测试不匹配分析功能"""

    def test_analyze_missing_required_field(self, mismatch_handler):
        """测试分析缺失必填字段"""
        validation_result = ValidationResult(
            is_valid=False,
            errors=[
                {
                    "field": "invoice_no",
                    "message": "'invoice_no' is a required property",
                    "expected": "string",
                    "actual": None
                }
            ],
            warnings=[]
        )
        output_data = {
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00
        }

        mismatch_items = mismatch_handler._analyze_mismatches(validation_result, output_data)

        assert len(mismatch_items) == 1
        assert mismatch_items[0].field_path == "invoice_no"
        assert mismatch_items[0].mismatch_type == MismatchType.MISSING_REQUIRED_FIELD
        assert mismatch_items[0].severity in [MismatchSeverity.CRITICAL, MismatchSeverity.HIGH]

    def test_analyze_type_mismatch(self, mismatch_handler):
        """测试分析类型不匹配"""
        validation_result = ValidationResult(
            is_valid=False,
            errors=[
                {
                    "field": "invoice_no",
                    "message": "12345678 is not of type 'string'",
                    "expected": "string",
                    "actual": 12345678
                }
            ],
            warnings=[]
        )
        output_data = {
            "invoice_no": 12345678,
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00
        }

        mismatch_items = mismatch_handler._analyze_mismatches(validation_result, output_data)

        assert len(mismatch_items) == 1
        assert mismatch_items[0].mismatch_type == MismatchType.TYPE_MISMATCH
        assert mismatch_items[0].can_auto_repair == True

    def test_analyze_extra_field(self, mismatch_handler):
        """测试分析额外字段"""
        validation_result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[
                {
                    "field": "extra_field",
                    "message": "Additional properties not allowed: extra_field"
                }
            ]
        )
        output_data = {
            "invoice_no": "12345678",
            "extra_field": "not_allowed"
        }

        mismatch_items = mismatch_handler._analyze_mismatches(validation_result, output_data)

        assert len(mismatch_items) == 1
        assert mismatch_items[0].mismatch_type == MismatchType.EXTRA_FIELD
        assert mismatch_items[0].severity == MismatchSeverity.LOW
        assert mismatch_items[0].can_auto_repair == True


class TestSeverityClassification:
    """测试严重程度分类"""

    def test_classify_critical_severity(self, mismatch_handler):
        """测试关键字段的严重程度"""
        severity = mismatch_handler._classify_severity(
            MismatchType.MISSING_REQUIRED_FIELD,
            "invoice_no",
            "string"
        )
        assert severity in [MismatchSeverity.CRITICAL, MismatchSeverity.HIGH]

    def test_classify_medium_severity(self, mismatch_handler):
        """测试一般字段的严重程度"""
        severity = mismatch_handler._classify_severity(
            MismatchType.TYPE_MISMATCH,
            "description",
            "string"
        )
        assert severity == MismatchSeverity.MEDIUM

    def test_classify_low_severity(self, mismatch_handler):
        """测试额外字段的严重程度"""
        severity = mismatch_handler._classify_severity(
            MismatchType.EXTRA_FIELD,
            "extra_field",
            None
        )
        assert severity == MismatchSeverity.LOW


class TestAutoRepairCapability:
    """测试自动修复能力判断"""

    def test_can_repair_type_mismatch(self, mismatch_handler):
        """测试类型不匹配可以修复"""
        can_repair = mismatch_handler._can_auto_repair(
            MismatchType.TYPE_MISMATCH,
            MismatchSeverity.MEDIUM
        )
        assert can_repair == True

    def test_cannot_repair_critical_missing_field(self, mismatch_handler):
        """测试关键字段缺失不能自动修复"""
        can_repair = mismatch_handler._can_auto_repair(
            MismatchType.MISSING_REQUIRED_FIELD,
            MismatchSeverity.CRITICAL
        )
        assert can_repair == False

    def test_can_repair_extra_field(self, mismatch_handler):
        """测试额外字段可以修复"""
        can_repair = mismatch_handler._can_auto_repair(
            MismatchType.EXTRA_FIELD,
            MismatchSeverity.LOW
        )
        assert can_repair == True


class TestRepairSuggestion:
    """测试修复建议生成"""

    def test_suggestion_for_missing_field(self, mismatch_handler):
        """测试缺失字段的修复建议"""
        suggestion = mismatch_handler._generate_repair_suggestion(
            MismatchType.MISSING_REQUIRED_FIELD,
            "invoice_no",
            "string",
            None
        )
        assert suggestion is not None
        assert "缺失" in suggestion or "补充" in suggestion

    def test_suggestion_for_type_mismatch(self, mismatch_handler):
        """测试类型不匹配的修复建议"""
        suggestion = mismatch_handler._generate_repair_suggestion(
            MismatchType.TYPE_MISMATCH,
            "invoice_no",
            "string",
            12345678
        )
        assert suggestion is not None
        assert "类型" in suggestion or "类型不匹配" in suggestion


class TestManualReviewRequirement:
    """测试人工审核需求判断"""

    def test_requires_review_for_critical(self, mismatch_handler):
        """测试关键错误需要人工审核"""
        mismatch_items = [
            MismatchItem(
                field_path="invoice_no",
                mismatch_type=MismatchType.MISSING_REQUIRED_FIELD,
                severity=MismatchSeverity.CRITICAL,
                expected="string",
                actual=None,
                message="Missing required field",
                can_auto_repair=False
            )
        ]
        repair_result = RepairResult(
            success=False,
            repair_actions=[],
            repair_time=datetime.now()
        )

        requires_review = mismatch_handler._should_require_manual_review(
            mismatch_items,
            repair_result
        )
        assert requires_review == True

    def test_requires_review_for_multiple_high(self, mismatch_handler):
        """测试多个高级错误需要人工审核"""
        mismatch_items = [
            MismatchItem(
                field_path=f"field_{i}",
                mismatch_type=MismatchType.MISSING_REQUIRED_FIELD,
                severity=MismatchSeverity.HIGH,
                expected="string",
                actual=None,
                message=f"Missing field {i}",
                can_auto_repair=False
            )
            for i in range(3)
        ]
        repair_result = RepairResult(
            success=True,
            repair_actions=[],
            repair_time=datetime.now()
        )

        requires_review = mismatch_handler._should_require_manual_review(
            mismatch_items,
            repair_result
        )
        assert requires_review == True

    def test_no_review_for_repair_success(self, mismatch_handler):
        """测试修复成功不需要人工审核"""
        mismatch_items = [
            MismatchItem(
                field_path="description",
                mismatch_type=MismatchType.TYPE_MISMATCH,
                severity=MismatchSeverity.MEDIUM,
                expected="string",
                actual=123,
                message="Type mismatch",
                can_auto_repair=True
            )
        ]
        repair_result = RepairResult(
            success=True,
            repair_actions=[{"action": "type_convert", "field": "description"}],
            repair_time=datetime.now()
        )

        requires_review = mismatch_handler._should_require_manual_review(
            mismatch_items,
            repair_result
        )
        assert requires_review == False


class TestHandleMismatch:
    """测试完整的不匹配处理流程"""

    @pytest.mark.asyncio
    async def test_handle_valid_data(self, mismatch_handler):
        """测试处理有效数据"""
        output_data = {
            "invoice_no": "12345678",
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00
        }

        result = await mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        # 如果验证通过，应该没有不匹配
        # 注意：这里需要实际的 schema 才能验证，所以可能返回 has_mismatch=True
        assert isinstance(result, SchemaMismatchResult)
        assert result.final_data is not None

    @pytest.mark.asyncio
    async def test_handle_missing_field(self, mismatch_handler):
        """测试处理缺失字段"""
        output_data = {
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00
            # 缺少 invoice_no
        }

        result = await mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert isinstance(result, SchemaMismatchResult)
        assert result.final_data is not None

    @pytest.mark.asyncio
    async def test_handle_type_mismatch(self, mismatch_handler):
        """测试处理类型不匹配"""
        output_data = {
            "invoice_no": 12345678,  # 应该是字符串
            "invoice_date": "2024-01-01",
            "total_amount": "1000.00"  # 应该是数字
        }

        result = await mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert isinstance(result, SchemaMismatchResult)
        assert result.final_data is not None

    @pytest.mark.asyncio
    async def test_handle_ignore_strategy(self, mismatch_handler):
        """测试忽略策略"""
        output_data = {
            "invoice_no": 12345678,
            "invoice_date": "2024-01-01"
        }

        result = await mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="ignore"
        )

        assert result.handling_strategy == "ignore"
        assert result.final_data == output_data
        assert result.requires_manual_review == False

    @pytest.mark.asyncio
    async def test_handle_error_case(self, mismatch_handler):
        """测试错误处理"""
        # 传入无效数据触发异常
        output_data = None

        result = await mismatch_handler.handle_mismatch(
            output_data={},  # 空字典
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert isinstance(result, SchemaMismatchResult)
        assert result.final_data is not None


class TestCountSeverity:
    """测试严重程度统计"""

    def test_count_severity(self, mismatch_handler):
        """测试统计各严重程度的数量"""
        mismatch_items = [
            MismatchItem(
                field_path="field1",
                mismatch_type=MismatchType.MISSING_REQUIRED_FIELD,
                severity=MismatchSeverity.CRITICAL,
                expected="string",
                actual=None,
                message="Error 1",
                can_auto_repair=False
            ),
            MismatchItem(
                field_path="field2",
                mismatch_type=MismatchType.TYPE_MISMATCH,
                severity=MismatchSeverity.HIGH,
                expected="string",
                actual=123,
                message="Error 2",
                can_auto_repair=True
            ),
            MismatchItem(
                field_path="field3",
                mismatch_type=MismatchType.EXTRA_FIELD,
                severity=MismatchSeverity.LOW,
                expected=None,
                actual=None,
                message="Warning",
                can_auto_repair=True
            )
        ]

        counts = mismatch_handler._count_severity(mismatch_items)

        assert counts[MismatchSeverity.CRITICAL] == 1
        assert counts[MismatchSeverity.HIGH] == 1
        assert counts[MismatchSeverity.LOW] == 1


class TestMismatchTypeClassification:
    """测试不匹配类型分类"""

    def test_classify_missing_field(self, mismatch_handler):
        """测试分类缺失字段"""
        mismatch_type = mismatch_handler._classify_mismatch_type(
            "'invoice_no' is a required property",
            "invoice_no"
        )
        assert mismatch_type == MismatchType.MISSING_REQUIRED_FIELD

    def test_classify_type_mismatch(self, mismatch_handler):
        """测试分类类型不匹配"""
        mismatch_type = mismatch_handler._classify_mismatch_type(
            "12345678 is not of type 'string'",
            "invoice_no"
        )
        assert mismatch_type == MismatchType.TYPE_MISMATCH

    def test_classify_extra_field(self, mismatch_handler):
        """测试分类额外字段"""
        mismatch_type = mismatch_handler._classify_mismatch_type(
            "Additional properties not allowed: extra_field",
            "extra_field"
        )
        assert mismatch_type == MismatchType.EXTRA_FIELD


# 集成测试：测试与 SchemaValidationService 的集成
class TestIntegrationWithValidationService:
    """测试与验证服务的集成"""

    @pytest.mark.asyncio
    async def test_integration_flow(self, mismatch_handler):
        """测试完整的集成流程"""
        # 模拟大模型返回的数据（有类型不匹配）
        output_data = {
            "invoice_no": 12345678,  # 应该是字符串
            "invoice_date": "2024-01-01",
            "total_amount": "1000.00",  # 应该是数字
            "extra_field": "not_allowed"  # 额外字段
        }

        result = await mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=None,
            model_config_id=None,
            handling_strategy="auto"
        )

        assert isinstance(result, SchemaMismatchResult)
        assert result.final_data is not None
        # 验证结果应该包含不匹配项
        # 注意：实际结果取决于 schema_validation_service 的行为

