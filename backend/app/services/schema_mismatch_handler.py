"""
Schema 不匹配处理服务
处理大模型 API 返回的 schema 与系统 schema 不一致的情况
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from app.services.schema_validation_service import (
    ValidationResult, 
    RepairResult, 
    FallbackResult,
    schema_validation_service
)

logger = logging.getLogger(__name__)


class MismatchSeverity(str, Enum):
    """不匹配严重程度"""
    CRITICAL = "critical"  # 关键字段缺失或类型错误，无法修复
    HIGH = "high"  # 重要字段问题，需要人工介入
    MEDIUM = "medium"  # 一般字段问题，可自动修复
    LOW = "low"  # 警告级别，不影响使用
    INFO = "info"  # 信息级别，仅记录


class MismatchType(str, Enum):
    """不匹配类型"""
    MISSING_REQUIRED_FIELD = "missing_required_field"  # 缺失必填字段
    TYPE_MISMATCH = "type_mismatch"  # 类型不匹配
    EXTRA_FIELD = "extra_field"  # 额外字段（不允许）
    VALUE_VALIDATION_FAILED = "value_validation_failed"  # 值验证失败
    SCHEMA_VERSION_MISMATCH = "schema_version_mismatch"  # Schema 版本不匹配
    STRUCTURE_MISMATCH = "structure_mismatch"  # 结构不匹配（嵌套对象/数组）


class MismatchItem(BaseModel):
    """单个不匹配项"""
    field_path: str  # 字段路径，如 "invoice_no" 或 "items[0].amount"
    mismatch_type: MismatchType
    severity: MismatchSeverity
    expected: Any  # 期望的值/类型
    actual: Any  # 实际的值/类型
    message: str  # 错误消息
    can_auto_repair: bool = False  # 是否可以自动修复
    repair_suggestion: Optional[str] = None  # 修复建议


class SchemaMismatchResult(BaseModel):
    """Schema 不匹配处理结果"""
    has_mismatch: bool
    mismatch_items: List[MismatchItem] = Field(default_factory=list)
    validation_result: Optional[ValidationResult] = None
    repair_result: Optional[RepairResult] = None
    fallback_result: Optional[FallbackResult] = None
    
    # 处理策略
    handling_strategy: str = "auto"  # auto/manual/ignore
    final_data: Optional[Dict[str, Any]] = None  # 最终返回的数据
    requires_manual_review: bool = False  # 是否需要人工审核
    
    # 统计信息
    total_errors: int = 0
    total_warnings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    
    # 元数据
    schema_id: Optional[str] = None
    model_config_id: Optional[str] = None
    processing_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class SchemaMismatchHandler:
    """Schema 不匹配处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def handle_mismatch(
        self,
        output_data: Dict[str, Any],
        schema_id: Optional[str] = None,
        model_config_id: Optional[str] = None,
        handling_strategy: str = "auto"
    ) -> SchemaMismatchResult:
        """
        处理 Schema 不匹配
        
        Args:
            output_data: 大模型返回的原始数据
            schema_id: Schema ID
            model_config_id: 模型配置 ID
            handling_strategy: 处理策略 (auto/manual/ignore)
        
        Returns:
            SchemaMismatchResult: 处理结果
        """
        start_time = datetime.now()
        
        try:
            # 1. 执行 Schema 验证
            validation_result = await schema_validation_service.validate_output(
                output_data=output_data,
                schema_id=schema_id,
                model_config_id=model_config_id
            )
            
            # 2. 分析不匹配项
            mismatch_items = self._analyze_mismatches(validation_result, output_data)
            
            # 3. 评估严重程度
            severity_counts = self._count_severity(mismatch_items)
            
            # 4. 根据策略处理
            if handling_strategy == "ignore":
                # 忽略不匹配，直接返回原始数据
                return SchemaMismatchResult(
                    has_mismatch=not validation_result.is_valid,
                    mismatch_items=mismatch_items,
                    validation_result=validation_result,
                    handling_strategy="ignore",
                    final_data=output_data,
                    requires_manual_review=False,
                    total_errors=len(validation_result.errors),
                    total_warnings=len(validation_result.warnings),
                    critical_count=severity_counts.get(MismatchSeverity.CRITICAL, 0),
                    high_count=severity_counts.get(MismatchSeverity.HIGH, 0),
                    medium_count=severity_counts.get(MismatchSeverity.MEDIUM, 0),
                    schema_id=schema_id,
                    model_config_id=model_config_id,
                    processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    timestamp=datetime.now()
                )
            
            # 5. 尝试自动修复
            repair_result = None
            if handling_strategy == "auto" and not validation_result.is_valid:
                repair_result = await schema_validation_service.repair_output(
                    output_data=output_data,
                    validation_result=validation_result,
                    schema_id=schema_id,
                    model_config_id=model_config_id
                )
            
            # 6. 判断是否需要人工审核
            requires_manual_review = self._should_require_manual_review(
                mismatch_items, repair_result
            )
            
            # 7. 如果修复失败或需要人工审核，使用降级策略
            fallback_result = None
            final_data = output_data
            
            if repair_result and repair_result.success:
                final_data = repair_result.repaired_data
            elif requires_manual_review or (repair_result and not repair_result.success):
                fallback_result = await schema_validation_service.fallback_output(
                    output_data=output_data,
                    validation_result=validation_result,
                    repair_result=repair_result or RepairResult(
                        success=False,
                        repair_actions=[],
                        repair_time=datetime.now()
                    ),
                    fallback_strategy="auto"
                )
                final_data = fallback_result.fallback_data or output_data
            
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return SchemaMismatchResult(
                has_mismatch=not validation_result.is_valid,
                mismatch_items=mismatch_items,
                validation_result=validation_result,
                repair_result=repair_result,
                fallback_result=fallback_result,
                handling_strategy=handling_strategy,
                final_data=final_data,
                requires_manual_review=requires_manual_review,
                total_errors=len(validation_result.errors),
                total_warnings=len(validation_result.warnings),
                critical_count=severity_counts.get(MismatchSeverity.CRITICAL, 0),
                high_count=severity_counts.get(MismatchSeverity.HIGH, 0),
                medium_count=severity_counts.get(MismatchSeverity.MEDIUM, 0),
                schema_id=schema_id,
                model_config_id=model_config_id,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Schema 不匹配处理失败: {str(e)}", exc_info=True)
            return SchemaMismatchResult(
                has_mismatch=True,
                mismatch_items=[MismatchItem(
                    field_path="system",
                    mismatch_type=MismatchType.STRUCTURE_MISMATCH,
                    severity=MismatchSeverity.CRITICAL,
                    expected="valid_schema",
                    actual="error",
                    message=f"处理过程出错: {str(e)}",
                    can_auto_repair=False
                )],
                handling_strategy=handling_strategy,
                final_data=output_data,  # 出错时返回原始数据
                requires_manual_review=True,
                schema_id=schema_id,
                model_config_id=model_config_id,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                timestamp=datetime.now()
            )
    
    def _analyze_mismatches(
        self, 
        validation_result: ValidationResult,
        output_data: Dict[str, Any]
    ) -> List[MismatchItem]:
        """分析验证错误，生成不匹配项列表"""
        mismatch_items = []
        
        for error in validation_result.errors:
            field_path = error.get("field", "root")
            message = error.get("message", "")
            expected = error.get("expected")
            actual = error.get("actual")
            
            # 判断不匹配类型
            mismatch_type = self._classify_mismatch_type(message, field_path)
            
            # 判断严重程度
            severity = self._classify_severity(mismatch_type, field_path, expected)
            
            # 判断是否可以自动修复
            can_auto_repair = self._can_auto_repair(mismatch_type, severity)
            
            # 生成修复建议
            repair_suggestion = self._generate_repair_suggestion(
                mismatch_type, field_path, expected, actual
            )
            
            mismatch_items.append(MismatchItem(
                field_path=field_path,
                mismatch_type=mismatch_type,
                severity=severity,
                expected=expected,
                actual=actual,
                message=message,
                can_auto_repair=can_auto_repair,
                repair_suggestion=repair_suggestion
            ))
        
        # 处理警告
        for warning in validation_result.warnings:
            mismatch_items.append(MismatchItem(
                field_path=warning.get("field", "root"),
                mismatch_type=MismatchType.EXTRA_FIELD,
                severity=MismatchSeverity.LOW,
                expected=None,
                actual=None,
                message=warning.get("message", ""),
                can_auto_repair=True,
                repair_suggestion="移除额外字段"
            ))
        
        return mismatch_items
    
    def _classify_mismatch_type(self, message: str, field_path: str) -> MismatchType:
        """根据错误消息分类不匹配类型"""
        message_lower = message.lower()
        
        if "required" in message_lower or "missing" in message_lower:
            return MismatchType.MISSING_REQUIRED_FIELD
        elif "type" in message_lower or "expected" in message_lower:
            return MismatchType.TYPE_MISMATCH
        elif "additional" in message_lower or "extra" in message_lower:
            return MismatchType.EXTRA_FIELD
        elif "validation" in message_lower or "format" in message_lower:
            return MismatchType.VALUE_VALIDATION_FAILED
        elif "structure" in message_lower or "schema" in message_lower:
            return MismatchType.STRUCTURE_MISMATCH
        else:
            return MismatchType.TYPE_MISMATCH
    
    def _classify_severity(
        self, 
        mismatch_type: MismatchType,
        field_path: str,
        expected: Any
    ) -> MismatchSeverity:
        """判断严重程度"""
        # 关键字段列表（可根据业务需求配置）
        critical_fields = [
            "invoice_no", "invoice_number", "invoice_date", 
            "total_amount", "amount", "supplier_name"
        ]
        
        if mismatch_type == MismatchType.MISSING_REQUIRED_FIELD:
            if any(cf in field_path.lower() for cf in critical_fields):
                return MismatchSeverity.CRITICAL
            return MismatchSeverity.HIGH
        elif mismatch_type == MismatchType.TYPE_MISMATCH:
            if any(cf in field_path.lower() for cf in critical_fields):
                return MismatchSeverity.HIGH
            return MismatchSeverity.MEDIUM
        elif mismatch_type == MismatchType.EXTRA_FIELD:
            return MismatchSeverity.LOW
        elif mismatch_type == MismatchType.VALUE_VALIDATION_FAILED:
            return MismatchSeverity.MEDIUM
        elif mismatch_type == MismatchType.STRUCTURE_MISMATCH:
            return MismatchSeverity.CRITICAL
        else:
            return MismatchSeverity.MEDIUM
    
    def _can_auto_repair(
        self, 
        mismatch_type: MismatchType,
        severity: MismatchSeverity
    ) -> bool:
        """判断是否可以自动修复"""
        if severity == MismatchSeverity.CRITICAL:
            return False
        elif severity == MismatchSeverity.HIGH:
            return mismatch_type in [
                MismatchType.TYPE_MISMATCH,
                MismatchType.VALUE_VALIDATION_FAILED
            ]
        else:
            return True
    
    def _generate_repair_suggestion(
        self,
        mismatch_type: MismatchType,
        field_path: str,
        expected: Any,
        actual: Any
    ) -> Optional[str]:
        """生成修复建议"""
        if mismatch_type == MismatchType.MISSING_REQUIRED_FIELD:
            return f"字段 {field_path} 缺失，建议补充该字段"
        elif mismatch_type == MismatchType.TYPE_MISMATCH:
            return f"字段 {field_path} 类型不匹配，期望 {expected}，实际 {type(actual).__name__}"
        elif mismatch_type == MismatchType.EXTRA_FIELD:
            return f"字段 {field_path} 不在 Schema 定义中，建议移除"
        elif mismatch_type == MismatchType.VALUE_VALIDATION_FAILED:
            return f"字段 {field_path} 的值不符合验证规则"
        else:
            return None
    
    def _count_severity(self, mismatch_items: List[MismatchItem]) -> Dict[MismatchSeverity, int]:
        """统计各严重程度的数量"""
        counts = {}
        for item in mismatch_items:
            counts[item.severity] = counts.get(item.severity, 0) + 1
        return counts
    
    def _should_require_manual_review(
        self,
        mismatch_items: List[MismatchItem],
        repair_result: Optional[RepairResult]
    ) -> bool:
        """判断是否需要人工审核"""
        # 如果有 CRITICAL 级别的不匹配，需要人工审核
        if any(item.severity == MismatchSeverity.CRITICAL for item in mismatch_items):
            return True
        
        # 如果有多个 HIGH 级别的不匹配，需要人工审核
        high_count = sum(1 for item in mismatch_items if item.severity == MismatchSeverity.HIGH)
        if high_count >= 3:
            return True
        
        # 如果自动修复失败，需要人工审核
        if repair_result and not repair_result.success:
            return True
        
        return False


# 全局实例
schema_mismatch_handler = SchemaMismatchHandler()

