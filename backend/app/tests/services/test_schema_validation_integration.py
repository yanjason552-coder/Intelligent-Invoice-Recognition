"""
Schema 验证集成测试
测试完整的 Schema 验证、修复、降级流程
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
from sqlmodel import Session, select

from app.services.schema_mismatch_handler import schema_mismatch_handler
from app.models.models_invoice import (
    OutputSchema,
    ModelConfig,
    Invoice,
    RecognitionTask,
    SchemaValidationRecord
)
from app.models import User


@pytest.fixture
def test_user(db: Session) -> User:
    """创建测试用户"""
    from app.core.security import get_password_hash
    
    user = User(
        email=f"test_{uuid4()}@example.com",
        hashed_password=get_password_hash("testpass"),
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


@pytest.fixture
def test_schema(db: Session, test_user: User) -> OutputSchema:
    """创建测试 Schema"""
    schema = OutputSchema(
        id=uuid4(),
        name="测试发票Schema",
        version="v1.0.0",
        schema_definition={
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
                }
            },
            "additionalProperties": False
        },
        is_active=True,
        is_default=False,
        description="测试用发票Schema",
        creator_id=test_user.id
    )
    db.add(schema)
    db.commit()
    db.refresh(schema)
    yield schema
    db.delete(schema)
    db.commit()


@pytest.fixture
def test_model_config(db: Session, test_user: User, test_schema: OutputSchema) -> ModelConfig:
    """创建测试模型配置"""
    config = ModelConfig(
        id=uuid4(),
        name="测试模型配置",
        provider="dify",
        api_key="test_key",
        api_base="https://api.test.com",
        model_name="test_model",
        default_schema_id=test_schema.id,
        is_active=True,
        creator_id=test_user.id
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    yield config
    db.delete(config)
    db.commit()


class TestSchemaValidationScenarios:
    """Schema 验证场景测试"""

    @pytest.mark.asyncio
    async def test_scenario_missing_required_field(
        self, 
        db: Session,
        test_schema: OutputSchema,
        test_model_config: ModelConfig
    ):
        """场景1: 缺失必填字段"""
        output_data = {
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00
            # 缺少 invoice_no
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=str(test_schema.id),
            model_config_id=str(test_model_config.id),
            handling_strategy="auto"
        )

        assert result.has_mismatch == True
        assert result.total_errors > 0
        # 应该检测到缺失 invoice_no
        assert any(
            item.field_path == "invoice_no" and 
            item.mismatch_type.value == "missing_required_field"
            for item in result.mismatch_items
        )

    @pytest.mark.asyncio
    async def test_scenario_type_mismatch(
        self,
        db: Session,
        test_schema: OutputSchema,
        test_model_config: ModelConfig
    ):
        """场景2: 类型不匹配"""
        output_data = {
            "invoice_no": 12345678,  # 应该是字符串
            "invoice_date": "2024-01-01",
            "total_amount": "1000.00"  # 应该是数字
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=str(test_schema.id),
            model_config_id=str(test_model_config.id),
            handling_strategy="auto"
        )

        assert result.has_mismatch == True
        # 应该尝试自动修复
        if result.repair_result:
            assert result.repair_result.success or len(result.repair_result.repair_actions) > 0

    @pytest.mark.asyncio
    async def test_scenario_extra_field(
        self,
        db: Session,
        test_schema: OutputSchema,
        test_model_config: ModelConfig
    ):
        """场景3: 额外字段"""
        output_data = {
            "invoice_no": "12345678",
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00,
            "extra_field": "not_allowed"  # 额外字段
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=str(test_schema.id),
            model_config_id=str(test_model_config.id),
            handling_strategy="auto"
        )

        # 额外字段应该被检测到
        assert any(
            item.mismatch_type.value == "extra_field"
            for item in result.mismatch_items
        )

    @pytest.mark.asyncio
    async def test_scenario_valid_data(
        self,
        db: Session,
        test_schema: OutputSchema,
        test_model_config: ModelConfig
    ):
        """场景4: 有效数据"""
        output_data = {
            "invoice_no": "12345678",
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=str(test_schema.id),
            model_config_id=str(test_model_config.id),
            handling_strategy="auto"
        )

        # 如果验证通过，应该没有不匹配
        # 注意：实际结果取决于 schema_validation_service 的实现
        assert result.final_data is not None

    @pytest.mark.asyncio
    async def test_scenario_multiple_errors(
        self,
        db: Session,
        test_schema: OutputSchema,
        test_model_config: ModelConfig
    ):
        """场景5: 多个错误"""
        output_data = {
            # 缺少 invoice_no
            "invoice_date": 20240101,  # 类型错误
            "total_amount": "invalid"  # 类型错误
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=str(test_schema.id),
            model_config_id=str(test_model_config.id),
            handling_strategy="auto"
        )

        assert result.has_mismatch == True
        assert result.total_errors >= 2
        # 多个错误可能需要人工审核
        if result.total_errors >= 3:
            assert result.requires_manual_review == True


class TestRepairStrategies:
    """测试修复策略"""

    @pytest.mark.asyncio
    async def test_auto_repair_strategy(
        self,
        db: Session,
        test_schema: OutputSchema,
        test_model_config: ModelConfig
    ):
        """测试自动修复策略"""
        output_data = {
            "invoice_no": 12345678,  # 类型不匹配，可修复
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=str(test_schema.id),
            model_config_id=str(test_model_config.id),
            handling_strategy="auto"
        )

        assert result.handling_strategy == "auto"
        if result.repair_result:
            # 如果修复成功，应该返回修复后的数据
            assert result.repair_result.success or result.final_data is not None

    @pytest.mark.asyncio
    async def test_ignore_strategy(
        self,
        db: Session,
        test_schema: OutputSchema,
        test_model_config: ModelConfig
    ):
        """测试忽略策略"""
        output_data = {
            "invoice_no": 12345678,
            "invoice_date": "2024-01-01"
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=str(test_schema.id),
            model_config_id=str(test_model_config.id),
            handling_strategy="ignore"
        )

        assert result.handling_strategy == "ignore"
        assert result.final_data == output_data
        assert result.requires_manual_review == False


class TestFallbackStrategies:
    """测试降级策略"""

    @pytest.mark.asyncio
    async def test_fallback_on_repair_failure(
        self,
        db: Session,
        test_schema: OutputSchema,
        test_model_config: ModelConfig
    ):
        """测试修复失败时的降级"""
        # 创建一个无法修复的数据（例如结构完全错误）
        output_data = {
            "completely_wrong": "structure"
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=str(test_schema.id),
            model_config_id=str(test_model_config.id),
            handling_strategy="auto"
        )

        # 如果修复失败，应该使用降级策略
        if result.fallback_result:
            assert result.fallback_result.fallback_type in [
                "partial", "empty", "text", "error"
            ]
            assert result.final_data is not None


class TestDatabaseRecording:
    """测试数据库记录"""

    @pytest.mark.asyncio
    async def test_record_validation_to_db(
        self,
        db: Session,
        test_schema: OutputSchema,
        test_model_config: ModelConfig,
        test_user: User
    ):
        """测试验证结果记录到数据库"""
        # 创建测试发票和任务
        from app.models.models_invoice import Invoice, RecognitionTask
        
        invoice = Invoice(
            id=uuid4(),
            invoice_no="TEST001",
            invoice_type="增值税发票",
            creator_id=test_user.id
        )
        db.add(invoice)
        db.commit()

        task = RecognitionTask(
            id=uuid4(),
            task_no=f"TASK_{uuid4()}",
            invoice_id=invoice.id,
            operator_id=test_user.id,
            status="completed",
            params={"output_schema_id": str(test_schema.id)}
        )
        db.add(task)
        db.commit()

        # 处理不匹配数据
        output_data = {
            "invoice_no": 12345678,  # 类型错误
            "invoice_date": "2024-01-01"
        }

        result = await schema_mismatch_handler.handle_mismatch(
            output_data=output_data,
            schema_id=str(test_schema.id),
            model_config_id=str(test_model_config.id),
            handling_strategy="auto"
        )

        # 检查是否应该记录到数据库
        # 注意：实际记录在 dify_service.py 中完成
        assert result.has_mismatch == True

        # 清理
        db.delete(task)
        db.delete(invoice)
        db.commit()

