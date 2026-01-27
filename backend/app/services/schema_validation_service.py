"""
Schema验证服务
提供JSON Schema验证、自动修复和降级返回功能
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from jsonschema import validate, ValidationError, Draft7Validator
from pydantic import BaseModel, Field
import uuid

from app.core.db import SessionLocal
from app.models.models_invoice import OutputSchema, LLMConfig
from sqlmodel import select

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """验证结果"""
    is_valid: bool
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    validation_time: datetime = Field(default_factory=datetime.now)


class RepairResult(BaseModel):
    """修复结果"""
    success: bool
    repaired_data: Optional[Dict[str, Any]] = None
    repair_actions: List[Dict[str, Any]] = Field(default_factory=list)
    repair_time: datetime = Field(default_factory=datetime.now)


class FallbackResult(BaseModel):
    """降级结果"""
    fallback_type: str  # "partial", "empty", "text", "error"
    fallback_data: Optional[Dict[str, Any]] = None
    fallback_message: str
    fallback_time: datetime = Field(default_factory=datetime.now)


class SchemaValidationService:
    """Schema验证服务"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def validate_output(
        self,
        output_data: Dict[str, Any],
        schema_id: Optional[str] = None,
        model_config_id: Optional[str] = None
    ) -> ValidationResult:
        """
        验证输出数据是否符合Schema

        Args:
            output_data: LLM输出的数据
            schema_id: Schema ID
            model_config_id: 模型配置ID

        Returns:
            ValidationResult: 验证结果
        """
        start_time = datetime.now()

        try:
            # 获取Schema定义
            schema_def = await self._get_schema_definition(schema_id, model_config_id)
            if not schema_def:
                self.logger.warning(f"No schema found for schema_id: {schema_id}, model_config_id: {model_config_id}")
                return ValidationResult(
                    is_valid=True,  # 如果没有Schema，认为是有效的
                    warnings=[{"message": "No schema defined for validation"}],
                    validation_time=start_time
                )

            # 验证JSON格式
            if not isinstance(output_data, dict):
                return ValidationResult(
                    is_valid=False,
                    errors=[{"field": "root", "message": "Output must be a JSON object"}],
                    validation_time=start_time
                )

            # 验证Schema
            errors = []
            try:
                validate(instance=output_data, schema=schema_def)
            except ValidationError as e:
                errors.append({
                    "field": ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root",
                    "message": e.message,
                    "expected": str(e.schema) if e.schema else None,
                    "actual": str(e.instance) if e.instance else None
                })

            # 检查额外字段
            warnings = []
            if schema_def.get("additionalProperties") == False:
                schema_fields = set()
                self._extract_schema_fields(schema_def, schema_fields)

                output_fields = set(output_data.keys())
                extra_fields = output_fields - schema_fields

                if extra_fields:
                    warnings.append({
                        "message": f"Additional properties not allowed: {', '.join(extra_fields)}"
                    })

            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                validation_time=start_time
            )

        except Exception as e:
            self.logger.error(f"Schema validation error: {str(e)}")
            return ValidationResult(
                is_valid=False,
                errors=[{"field": "system", "message": f"Validation system error: {str(e)}"}],
                validation_time=start_time
            )

    async def repair_output(
        self,
        output_data: Dict[str, Any],
        validation_result: ValidationResult,
        schema_id: Optional[str] = None,
        model_config_id: Optional[str] = None
    ) -> RepairResult:
        """
        尝试修复不符合Schema的数据

        Args:
            output_data: 原始输出数据
            validation_result: 验证结果
            schema_id: Schema ID
            model_config_id: 模型配置ID

        Returns:
            RepairResult: 修复结果
        """
        start_time = datetime.now()
        repair_actions = []

        try:
            # 获取Schema定义
            schema_def = await self._get_schema_definition(schema_id, model_config_id)
            if not schema_def:
                return RepairResult(
                    success=False,
                    repair_actions=[{"action": "skip", "reason": "No schema found"}],
                    repair_time=start_time
                )

            repaired_data = output_data.copy()

            # 处理缺失的必填字段
            required_fields = schema_def.get("required", [])
            for field in required_fields:
                if field not in repaired_data:
                    field_schema = schema_def.get("properties", {}).get(field, {})
                    default_value = self._get_default_value(field_schema)
                    if default_value is not None:
                        repaired_data[field] = default_value
                        repair_actions.append({
                            "action": "add_default",
                            "field": field,
                            "value": default_value
                        })
                    else:
                        # 尝试推断类型并设置空值
                        field_type = field_schema.get("type", "string")
                        empty_value = self._get_empty_value_for_type(field_type)
                        repaired_data[field] = empty_value
                        repair_actions.append({
                            "action": "add_empty",
                            "field": field,
                            "type": field_type,
                            "value": empty_value
                        })

            # 处理类型不匹配的字段
            properties = schema_def.get("properties", {})
            for field, field_schema in properties.items():
                if field in repaired_data:
                    expected_type = field_schema.get("type")
                    if expected_type:
                        try:
                            repaired_data[field] = self._convert_value_type(
                                repaired_data[field], expected_type
                            )
                            repair_actions.append({
                                "action": "type_convert",
                                "field": field,
                                "from_type": type(repaired_data[field]).__name__,
                                "to_type": expected_type
                            })
                        except (ValueError, TypeError):
                            # 类型转换失败，设置默认值
                            default_value = self._get_default_value(field_schema)
                            if default_value is not None:
                                repaired_data[field] = default_value
                                repair_actions.append({
                                    "action": "replace_with_default",
                                    "field": field,
                                    "reason": "Type conversion failed"
                                })

            # 移除不允许的额外字段
            if schema_def.get("additionalProperties") == False:
                schema_fields = set()
                self._extract_schema_fields(schema_def, schema_fields)
                output_fields = set(repaired_data.keys())
                extra_fields = output_fields - schema_fields

                for field in extra_fields:
                    del repaired_data[field]
                    repair_actions.append({
                        "action": "remove_extra_field",
                        "field": field
                    })

            # 再次验证修复后的数据
            final_validation = await self.validate_output(repaired_data, schema_id, model_config_id)

            return RepairResult(
                success=final_validation.is_valid,
                repaired_data=repaired_data if final_validation.is_valid else None,
                repair_actions=repair_actions,
                repair_time=start_time
            )

        except Exception as e:
            self.logger.error(f"Schema repair error: {str(e)}")
            return RepairResult(
                success=False,
                repair_actions=[{"action": "error", "message": str(e)}],
                repair_time=start_time
            )

    async def fallback_output(
        self,
        output_data: Dict[str, Any],
        validation_result: ValidationResult,
        repair_result: RepairResult,
        fallback_strategy: str = "auto"
    ) -> FallbackResult:
        """
        根据策略生成降级返回结果

        Args:
            output_data: 原始输出数据
            validation_result: 验证结果
            repair_result: 修复结果
            fallback_strategy: 降级策略 (auto/partial/empty/text/error)

        Returns:
            FallbackResult: 降级结果
        """
        start_time = datetime.now()

        try:
            if fallback_strategy == "auto":
                # 自动选择降级策略
                if repair_result.success and repair_result.repaired_data:
                    return FallbackResult(
                        fallback_type="partial",
                        fallback_data=repair_result.repaired_data,
                        fallback_message="Data repaired successfully",
                        fallback_time=start_time
                    )
                elif validation_result.warnings and not validation_result.errors:
                    # 只有警告，没有错误
                    return FallbackResult(
                        fallback_type="partial",
                        fallback_data=output_data,
                        fallback_message="Data has warnings but is usable",
                        fallback_time=start_time
                    )
                else:
                    # 严重错误，返回空数据
                    return FallbackResult(
                        fallback_type="empty",
                        fallback_data={},
                        fallback_message="Data validation failed, returning empty result",
                        fallback_time=start_time
                    )

            elif fallback_strategy == "partial":
                return FallbackResult(
                    fallback_type="partial",
                    fallback_data=repair_result.repaired_data or output_data,
                    fallback_message="Returning partial data",
                    fallback_time=start_time
                )

            elif fallback_strategy == "empty":
                return FallbackResult(
                    fallback_type="empty",
                    fallback_data={},
                    fallback_message="Returning empty data due to validation failure",
                    fallback_time=start_time
                )

            elif fallback_strategy == "text":
                return FallbackResult(
                    fallback_type="text",
                    fallback_data={"raw_text": json.dumps(output_data, ensure_ascii=False)},
                    fallback_message="Returning raw text due to validation failure",
                    fallback_time=start_time
                )

            elif fallback_strategy == "error":
                return FallbackResult(
                    fallback_type="error",
                    fallback_data=None,
                    fallback_message="Data validation failed completely",
                    fallback_time=start_time
                )

            else:
                return FallbackResult(
                    fallback_type="error",
                    fallback_data=None,
                    fallback_message=f"Unknown fallback strategy: {fallback_strategy}",
                    fallback_time=start_time
                )

        except Exception as e:
            self.logger.error(f"Fallback processing error: {str(e)}")
            return FallbackResult(
                fallback_type="error",
                fallback_data=None,
                fallback_message=f"Fallback processing failed: {str(e)}",
                fallback_time=start_time
            )

    async def _get_schema_definition(
        self,
        schema_id: Optional[str] = None,
        model_config_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取Schema定义"""
        try:
            with SessionLocal() as session:
                if schema_id:
                    # 直接通过Schema ID获取
                    schema_obj = session.get(OutputSchema, schema_id)
                    if schema_obj and schema_obj.is_active:
                        return schema_obj.schema_definition

                if model_config_id:
                    # 注意：LLMConfig 没有 default_schema_id 字段
                    # 如果需要通过模型配置获取默认Schema，需要从任务参数中获取 output_schema_id
                    # 这里暂时跳过，因为 LLMConfig 不包含默认 schema 信息
                    pass

                # 返回默认的发票Schema（如果存在）
                default_schema = session.exec(
                    select(OutputSchema).where(
                        OutputSchema.is_default == True,
                        OutputSchema.is_active == True
                    )
                ).first()

                if default_schema:
                    return default_schema.schema_definition

        except Exception as e:
            self.logger.error(f"Error getting schema definition: {str(e)}")

        return None

    def _extract_schema_fields(self, schema: Dict[str, Any], fields: set, prefix: str = ""):
        """递归提取Schema中的所有字段名"""
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            full_name = f"{prefix}.{field_name}" if prefix else field_name
            fields.add(field_name)  # 只添加直接字段名，不添加完整路径

            # 递归处理嵌套对象
            if field_schema.get("type") == "object":
                self._extract_schema_fields(field_schema, fields, full_name)

    def _get_default_value(self, field_schema: Dict[str, Any]) -> Any:
        """获取字段的默认值"""
        if "default" in field_schema:
            return field_schema["default"]

        field_type = field_schema.get("type", "string")
        if field_type == "string":
            return ""
        elif field_type == "number" or field_type == "integer":
            return 0
        elif field_type == "boolean":
            return False
        elif field_type == "array":
            return []
        elif field_type == "object":
            return {}
        else:
            return None

    def _get_empty_value_for_type(self, field_type: str) -> Any:
        """根据类型获取空值"""
        if field_type == "string":
            return ""
        elif field_type == "number" or field_type == "integer":
            return 0
        elif field_type == "boolean":
            return False
        elif field_type == "array":
            return []
        elif field_type == "object":
            return {}
        else:
            return None

    def _convert_value_type(self, value: Any, target_type: str) -> Any:
        """尝试转换值类型"""
        if target_type == "string":
            return str(value)
        elif target_type == "number":
            return float(value) if value != "" else 0.0
        elif target_type == "integer":
            return int(float(value)) if value != "" else 0
        elif target_type == "boolean":
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        else:
            return value


# 创建全局服务实例
schema_validation_service = SchemaValidationService()
