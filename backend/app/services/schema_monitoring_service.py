"""
Schema监控服务
记录和统计Schema验证、修复、降级的各种指标
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from pydantic import BaseModel, Field
import json

from app.core.db import engine
from sqlmodel import Session
from app.models.models_invoice import LLMConfig, OutputSchema
from sqlmodel import select, func

logger = logging.getLogger(__name__)


class MonitoringMetrics(BaseModel):
    """监控指标"""
    # 验证相关
    validation_total: int = Field(default=0, description="总验证次数")
    validation_success: int = Field(default=0, description="验证成功次数")
    validation_success_rate: float = Field(default=0.0, description="验证成功率")

    # 修复相关
    repair_total: int = Field(default=0, description="总修复次数")
    repair_success: int = Field(default=0, description="修复成功次数")
    repair_success_rate: float = Field(default=0.0, description="修复成功率")

    # 降级相关
    fallback_total: int = Field(default=0, description="总降级次数")
    fallback_by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计的降级次数")
    fallback_rate: float = Field(default=0, description="降级率")

    # 性能指标
    avg_validation_time: float = Field(default=0.0, description="平均验证耗时(毫秒)")
    avg_repair_time: float = Field(default=0.0, description="平均修复耗时(毫秒)")
    avg_total_time: float = Field(default=0.0, description="平均总耗时(毫秒)")

    # 时间戳
    last_updated: datetime = Field(default_factory=datetime.now)


class ValidationRecord(BaseModel):
    """验证记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_config_id: Optional[str] = None
    schema_id: Optional[str] = None
    is_valid: bool
    error_count: int = 0
    warning_count: int = 0
    validation_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class RepairRecord(BaseModel):
    """修复记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    validation_record_id: str
    success: bool
    repair_actions_count: int = 0
    repair_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class FallbackRecord(BaseModel):
    """降级记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    validation_record_id: str
    repair_record_id: Optional[str] = None
    fallback_type: str
    fallback_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class SchemaMonitoringService:
    """Schema监控服务"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 内存缓存，用于实时统计
        self._metrics_cache: Dict[str, MonitoringMetrics] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)  # 缓存5分钟

    async def record_validation(
        self,
        model_config_id: Optional[str],
        schema_id: Optional[str],
        is_valid: bool,
        error_count: int = 0,
        warning_count: int = 0,
        validation_time_ms: float = 0.0
    ) -> str:
        """
        记录验证操作

        Args:
            model_config_id: 模型配置ID
            schema_id: Schema ID
            is_valid: 是否验证成功
            error_count: 错误数量
            warning_count: 警告数量
            validation_time_ms: 验证耗时(毫秒)

        Returns:
            str: 验证记录ID
        """
        record = ValidationRecord(
            model_config_id=model_config_id,
            schema_id=schema_id,
            is_valid=is_valid,
            error_count=error_count,
            warning_count=warning_count,
            validation_time_ms=validation_time_ms
        )

        try:
            # 这里可以选择持久化存储或只做内存统计
            # 为了简化实现，先只做内存统计和日志记录
            self.logger.info(
                f"Schema validation recorded: model={model_config_id}, schema={schema_id}, "
                f"valid={is_valid}, errors={error_count}, warnings={warning_count}, "
                f"time={validation_time_ms}ms"
            )

            # 更新缓存的统计信息
            await self._update_metrics_cache("global", record)

            return record.id

        except Exception as e:
            self.logger.error(f"Failed to record validation: {str(e)}")
            return record.id

    async def record_repair(
        self,
        validation_record_id: str,
        success: bool,
        repair_actions_count: int = 0,
        repair_time_ms: float = 0.0
    ) -> str:
        """
        记录修复操作

        Args:
            validation_record_id: 验证记录ID
            success: 是否修复成功
            repair_actions_count: 修复动作数量
            repair_time_ms: 修复耗时(毫秒)

        Returns:
            str: 修复记录ID
        """
        record = RepairRecord(
            validation_record_id=validation_record_id,
            success=success,
            repair_actions_count=repair_actions_count,
            repair_time_ms=repair_time_ms
        )

        try:
            self.logger.info(
                f"Schema repair recorded: validation_id={validation_record_id}, "
                f"success={success}, actions={repair_actions_count}, time={repair_time_ms}ms"
            )

            # 更新缓存的统计信息
            await self._update_metrics_cache("global", repair_record=record)

            return record.id

        except Exception as e:
            self.logger.error(f"Failed to record repair: {str(e)}")
            return record.id

    async def record_fallback(
        self,
        validation_record_id: str,
        repair_record_id: Optional[str],
        fallback_type: str,
        fallback_time_ms: float = 0.0
    ) -> str:
        """
        记录降级操作

        Args:
            validation_record_id: 验证记录ID
            repair_record_id: 修复记录ID
            fallback_type: 降级类型
            fallback_time_ms: 降级耗时(毫秒)

        Returns:
            str: 降级记录ID
        """
        record = FallbackRecord(
            validation_record_id=validation_record_id,
            repair_record_id=repair_record_id,
            fallback_type=fallback_type,
            fallback_time_ms=fallback_time_ms
        )

        try:
            self.logger.info(
                f"Schema fallback recorded: validation_id={validation_record_id}, "
                f"repair_id={repair_record_id}, type={fallback_type}, time={fallback_time_ms}ms"
            )

            # 更新缓存的统计信息
            await self._update_metrics_cache("global", fallback_record=record)

            return record.id

        except Exception as e:
            self.logger.error(f"Failed to record fallback: {str(e)}")
            return record.id

    async def get_metrics(
        self,
        scope: str = "global",
        model_config_id: Optional[str] = None,
        schema_id: Optional[str] = None,
        time_range_hours: int = 24
    ) -> MonitoringMetrics:
        """
        获取监控指标

        Args:
            scope: 统计范围 (global/model/schema)
            model_config_id: 模型配置ID
            schema_id: Schema ID
            time_range_hours: 时间范围(小时)

        Returns:
            MonitoringMetrics: 监控指标
        """
        cache_key = f"{scope}_{model_config_id}_{schema_id}_{time_range_hours}"

        # 检查缓存
        if cache_key in self._metrics_cache and self._cache_expiry.get(cache_key, datetime.min) > datetime.now():
            return self._metrics_cache[cache_key]

        # 重新计算指标
        metrics = await self._calculate_metrics(scope, model_config_id, schema_id, time_range_hours)

        # 更新缓存
        self._metrics_cache[cache_key] = metrics
        self._cache_expiry[cache_key] = datetime.now() + self._cache_ttl

        return metrics

    async def _update_metrics_cache(
        self,
        cache_key: str,
        validation_record: Optional[ValidationRecord] = None,
        repair_record: Optional[RepairRecord] = None,
        fallback_record: Optional[FallbackRecord] = None
    ):
        """更新指标缓存"""
        if cache_key not in self._metrics_cache:
            self._metrics_cache[cache_key] = MonitoringMetrics()

        metrics = self._metrics_cache[cache_key]

        if validation_record:
            metrics.validation_total += 1
            if validation_record.is_valid:
                metrics.validation_success += 1
            metrics.avg_validation_time = (
                (metrics.avg_validation_time * (metrics.validation_total - 1) + validation_record.validation_time_ms)
                / metrics.validation_total
            )

        if repair_record:
            metrics.repair_total += 1
            if repair_record.success:
                metrics.repair_success += 1
            metrics.avg_repair_time = (
                (metrics.avg_repair_time * (metrics.repair_total - 1) + repair_record.repair_time_ms)
                / metrics.repair_total
            )

        if fallback_record:
            metrics.fallback_total += 1
            metrics.fallback_by_type[fallback_record.fallback_type] = (
                metrics.fallback_by_type.get(fallback_record.fallback_type, 0) + 1
            )

        # 计算比率
        metrics.validation_success_rate = (
            metrics.validation_success / metrics.validation_total if metrics.validation_total > 0 else 0
        )
        metrics.repair_success_rate = (
            metrics.repair_success / metrics.repair_total if metrics.repair_total > 0 else 0
        )
        metrics.fallback_rate = (
            metrics.fallback_total / metrics.validation_total if metrics.validation_total > 0 else 0
        )

        # 计算平均总时间
        if metrics.validation_total > 0 and metrics.repair_total > 0:
            metrics.avg_total_time = metrics.avg_validation_time + (
                metrics.avg_repair_time * (metrics.repair_total / metrics.validation_total)
            )

        metrics.last_updated = datetime.now()

    async def _calculate_metrics(
        self,
        scope: str,
        model_config_id: Optional[str],
        schema_id: Optional[str],
        time_range_hours: int
    ) -> MonitoringMetrics:
        """
        计算监控指标（这里是简化实现，实际应该从数据库查询）
        """
        # 由于当前没有实际的监控数据表，这里返回缓存的指标或默认值
        cache_key = f"{scope}_{model_config_id}_{schema_id}_{time_range_hours}"

        if cache_key in self._metrics_cache:
            return self._metrics_cache[cache_key]

        # 返回默认指标
        return MonitoringMetrics()

    async def get_model_config_stats(self) -> Dict[str, Any]:
        """获取模型配置统计信息"""
        try:
            with Session(engine) as session:
                # 统计活跃的模型配置
                active_configs = session.exec(
                    select(func.count(LLMConfig.id)).where(LLMConfig.is_active == True)
                ).first()

                # 统计活跃的Schema
                active_schemas = session.exec(
                    select(func.count(OutputSchema.id)).where(OutputSchema.is_active == True)
                ).first()

                # 统计有默认Schema的模型配置
                configs_with_schema = session.exec(
                    # 注意：LLMConfig 没有 default_schema_id 字段，所以这里返回 0
                    # select(func.count(LLMConfig.id)).where(
                    #     LLMConfig.is_active == True,
                    #     LLMConfig.default_schema_id.isnot(None)
                    # )
                    select(func.count()).select_from(LLMConfig).where(
                        LLMConfig.is_active == True
                    ).where(False)  # 返回 0，因为 LLMConfig 没有 default_schema_id
                ).first()

                return {
                    "active_model_configs": active_configs or 0,
                    "active_schemas": active_schemas or 0,
                    "configs_with_default_schema": configs_with_schema or 0,
                    "schema_coverage_rate": (
                        (configs_with_schema or 0) / (active_configs or 1) * 100
                    )
                }

        except Exception as e:
            self.logger.error(f"Failed to get model config stats: {str(e)}")
            return {
                "active_model_configs": 0,
                "active_schemas": 0,
                "configs_with_default_schema": 0,
                "schema_coverage_rate": 0.0
            }

    async def export_metrics_report(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """导出指标报告"""
        global_metrics = await self.get_metrics("global", time_range_hours=time_range_hours)
        model_stats = await self.get_model_config_stats()

        return {
            "summary": {
                "time_range_hours": time_range_hours,
                "generated_at": datetime.now().isoformat()
            },
            "validation_metrics": {
                "total_validations": global_metrics.validation_total,
                "success_rate": f"{global_metrics.validation_success_rate:.2%}",
                "avg_time_ms": f"{global_metrics.avg_validation_time:.2f}"
            },
            "repair_metrics": {
                "total_repairs": global_metrics.repair_total,
                "success_rate": f"{global_metrics.repair_success_rate:.2%}",
                "avg_time_ms": f"{global_metrics.avg_repair_time:.2f}"
            },
            "fallback_metrics": {
                "total_fallbacks": global_metrics.fallback_total,
                "fallback_rate": f"{global_metrics.fallback_rate:.2%}",
                "fallback_types": global_metrics.fallback_by_type
            },
            "performance_metrics": {
                "avg_total_time_ms": f"{global_metrics.avg_total_time:.2f}"
            },
            "system_stats": model_stats
        }


# 创建全局服务实例
schema_monitoring_service = SchemaMonitoringService()
