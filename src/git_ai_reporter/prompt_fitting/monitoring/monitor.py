# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Prompt fitting monitoring system.

This module contains the main PromptFittingMonitor class that orchestrates
comprehensive monitoring, performance metrics collection, and alerting for
the prompt fitting operations.
"""

import asyncio
from collections import deque
from dataclasses import dataclass
from dataclasses import field
import statistics
import time
from typing import Any, Optional, TYPE_CHECKING

from git_ai_reporter.prompt_fitting.constants import HEALTH_ERROR_RATE_HIGH
from git_ai_reporter.prompt_fitting.constants import HEALTH_ERROR_RATE_WARNING
from git_ai_reporter.prompt_fitting.constants import ThresholdOperator
from git_ai_reporter.prompt_fitting.logging import get_logger
from git_ai_reporter.prompt_fitting.prompt_fitting import ContentFitterT
from git_ai_reporter.prompt_fitting.prompt_fitting import FittingResult

from .backends import InMemoryMonitoringBackend
from .models import Alert
from .models import AlertLifecycle
from .models import AlertMetadata
from .models import AlertSeverity
from .models import MetricType
from .models import MetricValue
from .models import OperationRecordParams
from .models import PerformanceData
from .models import PerformanceMetrics
from .rules import MonitoringConfig
from .rules import RuleMetrics
from .rules import RuleSettings
from .rules import ThresholdRule

if TYPE_CHECKING:
    from .backends import MonitoringBackend


@dataclass
class MonitoringState:
    """Internal state for monitoring system."""

    # Performance tracking
    strategy_metrics: dict[str, PerformanceMetrics] = field(default_factory=dict)
    operation_history: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=1000))

    # Alerting system
    threshold_rules: list[ThresholdRule] = field(default_factory=list)
    active_alerts: dict[str, Alert] = field(default_factory=dict)

    # Runtime state
    monitoring_task: Optional[asyncio.Task[None]] = None
    running: bool = False
    metrics_cache: dict[str, float] = field(default_factory=dict)


class PromptFittingMonitor:
    """Comprehensive monitoring system for prompt fitting operations."""

    def __init__(
        self,
        backend: Optional["MonitoringBackend"] = None,
        enable_performance_tracking: bool = True,
        enable_data_integrity_monitoring: bool = True,
        metric_collection_interval: float = 60.0,
    ):
        """Initialize the monitoring system.

        Args:
            backend: Monitoring backend for metrics and alerts
            enable_performance_tracking: Enable performance metrics collection
            enable_data_integrity_monitoring: Enable project compliance tracking
            metric_collection_interval: Interval for metric collection in seconds
        """
        # Configuration
        self._config = MonitoringConfig(
            backend=backend or InMemoryMonitoringBackend(),
            enable_performance_tracking=enable_performance_tracking,
            enable_data_integrity_monitoring=enable_data_integrity_monitoring,
            metric_collection_interval=metric_collection_interval,
        )

        # Internal state
        self._state = MonitoringState()

        # Logger
        self.logger = get_logger("PromptFittingMonitor")

        # Initialize default threshold rules
        self._setup_default_thresholds()

    @property
    def enable_performance_tracking(self) -> bool:
        """Get performance tracking flag from config."""
        return self._config.enable_performance_tracking

    @property
    def enable_data_integrity_monitoring(self) -> bool:
        """Get data integrity monitoring flag from config."""
        return self._config.enable_data_integrity_monitoring

    @property
    def metric_collection_interval(self) -> float:
        """Get metric collection interval from config."""
        return self._config.metric_collection_interval

    @property
    def backend(self) -> "MonitoringBackend":
        """Get backend from config."""
        # Backend is guaranteed to be set in __init__
        return self._config.backend  # type: ignore[return-value]

    @property
    def strategy_metrics(self) -> dict[str, PerformanceMetrics]:
        """Get strategy metrics from state."""
        return self._state.strategy_metrics

    @property
    def operation_history(self) -> deque[dict[str, Any]]:
        """Get operation history from state."""
        return self._state.operation_history

    @property
    def threshold_rules(self) -> list[ThresholdRule]:
        """Get threshold rules from state."""
        return self._state.threshold_rules

    @property
    def active_alerts(self) -> dict[str, Alert]:
        """Get active alerts from state."""
        return self._state.active_alerts

    @property
    def _monitoring_task(self) -> Optional[asyncio.Task[None]]:
        """Get monitoring task from state."""
        return self._state.monitoring_task

    @_monitoring_task.setter
    def _monitoring_task(self, value: Optional[asyncio.Task[None]]) -> None:
        """Set monitoring task in state."""
        self._state.monitoring_task = value

    @property
    def _running(self) -> bool:
        """Get running flag from state."""
        return self._state.running

    @_running.setter
    def _running(self, value: bool) -> None:
        """Set running flag in state."""
        self._state.running = value

    @property
    def _metrics_cache(self) -> dict[str, float]:
        """Get metrics cache from state."""
        return self._state.metrics_cache

    def _setup_default_thresholds(self) -> None:
        """Setup default monitoring thresholds."""
        default_rules = [
            # Data integrity compliance (project requirement)
            ThresholdRule(
                metrics=RuleMetrics(
                    metric_name="data_integrity_compliance",
                    operator=ThresholdOperator.LT,
                    threshold=100.0,
                    severity=AlertSeverity.CRITICAL,
                ),
                settings=RuleSettings(
                    message_template="Data integrity compliance below 100%: {value}%",
                    consecutive_violations=1,
                ),
            ),
            # Error rate monitoring
            ThresholdRule(
                metrics=RuleMetrics(
                    metric_name="error_rate",
                    operator=ThresholdOperator.GT,
                    threshold=10.0,
                    severity=AlertSeverity.HIGH,
                ),
                settings=RuleSettings(
                    message_template="Error rate too high: {value}%",
                    evaluation_window=300.0,  # 5 minute window
                    consecutive_violations=2,
                ),
            ),
            # Performance degradation
            ThresholdRule(
                metrics=RuleMetrics(
                    metric_name="average_processing_time",
                    operator=ThresholdOperator.GT,
                    threshold=30.0,  # 30 seconds
                    severity=AlertSeverity.MEDIUM,
                ),
                settings=RuleSettings(
                    message_template="Average processing time too high: {value}s",
                    evaluation_window=600.0,  # 10 minute window
                ),
            ),
            # Memory usage
            ThresholdRule(
                metrics=RuleMetrics(
                    metric_name="memory_usage_mb",
                    operator=ThresholdOperator.GT,
                    threshold=1024.0,  # 1GB
                    severity=AlertSeverity.MEDIUM,
                ),
                settings=RuleSettings(
                    message_template="Memory usage high: {value}MB",
                ),
            ),
        ]

        self._state.threshold_rules.extend(default_rules)

    async def start_monitoring(self) -> None:
        """Start the monitoring system."""
        if self._running:
            self.logger.warning("Monitoring already running")
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Prompt fitting monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop the monitoring system."""
        if not self._running:
            return

        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                # Expected when cancelling monitoring task
                self.logger.debug("Monitoring task cancelled as expected")

        self.logger.info("Prompt fitting monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:  # pylint: disable=while-used
            try:
                await self._collect_metrics()
                await self._evaluate_thresholds()
                await asyncio.sleep(self.metric_collection_interval)
            except asyncio.CancelledError:
                break
            except (AttributeError, TypeError, ValueError, RuntimeError) as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def record_operation(self, params: OperationRecordParams) -> None:
        """Record a prompt fitting operation for monitoring.

        Args:
            params: OperationRecordParams containing all operation details
        """
        timestamp = time.time()

        # Update strategy metrics
        if params.strategy_name not in self.strategy_metrics:
            performance_data = PerformanceData(last_updated=timestamp)
            self.strategy_metrics[params.strategy_name] = PerformanceMetrics(
                strategy_name=params.strategy_name, performance=performance_data
            )

        metrics = self.strategy_metrics[params.strategy_name]
        metrics.counts.operation_count += 1
        metrics.performance.total_processing_time += params.processing_time
        metrics.performance.last_updated = timestamp

        if params.error:
            metrics.counts.error_count += 1
        else:
            metrics.counts.success_count += 1

        # Track data integrity violations
        if params.result and not params.result.data_preserved:
            metrics.counts.data_preservation_violations += 1
            await self._send_critical_alert(
                "data_integrity_violation",
                f"Data integrity violation detected in {params.strategy_name}",
                {
                    "strategy": params.strategy_name,
                    "operation": params.operation_type,
                },
            )

        # Update compression metrics
        if params.result:
            old_ratio = metrics.performance.average_compression_ratio
            new_ratio = params.result.compression_ratio
            count = metrics.counts.operation_count
            metrics.performance.average_compression_ratio = (
                old_ratio * (count - 1) + new_ratio
            ) / count

        # Record operation history
        operation_record = {
            "timestamp": timestamp,
            "strategy": params.strategy_name,
            "operation_type": params.operation_type,
            "processing_time": params.processing_time,
            "success": params.error is None,
            "data_preserved": (params.result.data_preserved if params.result else None),
            "compression_ratio": (params.result.compression_ratio if params.result else None),
            "metadata": params.metadata or {},
        }

        self.operation_history.append(operation_record)

        # Send real-time metrics
        if self.enable_performance_tracking:
            await self._send_operation_metrics(params.strategy_name, operation_record)

    async def _send_operation_metrics(
        self, strategy_name: str, operation_record: dict[str, Any]
    ) -> None:
        """Send operation metrics to backend."""
        timestamp = operation_record["timestamp"]
        tags = {"strategy": strategy_name, "operation": operation_record["operation_type"]}

        metrics_to_send = [
            MetricValue(
                name="prompt_fitting_operations_total",
                value=1,
                metric_type=MetricType.COUNTER,
                timestamp=timestamp,
                tags=tags,
            ),
            MetricValue(
                name="prompt_fitting_processing_time_seconds",
                value=operation_record["processing_time"],
                metric_type=MetricType.HISTOGRAM,
                timestamp=timestamp,
                tags=tags,
            ),
        ]

        if operation_record["compression_ratio"]:
            metrics_to_send.append(
                MetricValue(
                    name="prompt_fitting_compression_ratio",
                    value=operation_record["compression_ratio"],
                    metric_type=MetricType.GAUGE,
                    timestamp=timestamp,
                    tags=tags,
                )
            )

        # Send metrics to backend
        for metric in metrics_to_send:
            await self.backend.send_metric(metric)

    async def _collect_metrics(self) -> None:
        """Collect and send aggregated metrics."""
        timestamp = time.time()

        for strategy_name, metrics in self.strategy_metrics.items():
            tags = {"strategy": strategy_name}

            # Performance metrics
            performance_metrics = [
                MetricValue(
                    name="strategy_success_rate",
                    value=metrics.success_rate,
                    metric_type=MetricType.GAUGE,
                    timestamp=timestamp,
                    tags=tags,
                ),
                MetricValue(
                    name="strategy_error_rate",
                    value=metrics.error_rate,
                    metric_type=MetricType.GAUGE,
                    timestamp=timestamp,
                    tags=tags,
                ),
                MetricValue(
                    name="average_processing_time",
                    value=metrics.average_processing_time,
                    metric_type=MetricType.GAUGE,
                    timestamp=timestamp,
                    tags=tags,
                ),
                MetricValue(
                    name="data_integrity_compliance",
                    value=metrics.data_integrity_compliance,
                    metric_type=MetricType.GAUGE,
                    timestamp=timestamp,
                    tags=tags,
                ),
            ]

            # Send metrics
            for metric in performance_metrics:
                await self.backend.send_metric(metric)
                self._metrics_cache[f"{metric.name}_{strategy_name}"] = metric.value

    async def _evaluate_thresholds(self) -> None:
        """Evaluate threshold rules and generate alerts."""
        for rule in self.threshold_rules:
            try:
                await self._evaluate_single_threshold(rule)
            except (AttributeError, TypeError, ValueError, KeyError) as e:
                self.logger.error(f"Error evaluating threshold {rule.metrics.metric_name}: {e}")

    async def _evaluate_single_threshold(self, rule: ThresholdRule) -> None:
        """Evaluate a single threshold rule."""
        # Get recent values for the metric
        current_time = time.time()
        lookback_time = current_time - (rule.settings.evaluation_window or 300.0)

        metric_data = await self.backend.query_metrics(
            [rule.metrics.metric_name], lookback_time, current_time
        )

        values = [m.value for m in metric_data.get(rule.metrics.metric_name, [])]

        if rule.evaluate(values):
            # Check if alert already exists
            if (
                alert_key := f"{rule.metrics.metric_name}_{rule.metrics.threshold}"
            ) not in self.active_alerts:
                current_value = values[-1] if values else 0.0

                alert_metadata = AlertMetadata(
                    metric_value=current_value,
                    threshold_value=rule.metrics.threshold,
                    tags=rule.settings.tags.copy(),
                )
                alert_lifecycle = AlertLifecycle(
                    auto_resolve=rule.settings.auto_resolve,
                )

                alert = Alert(
                    name=rule.metrics.metric_name,
                    message=rule.settings.message_template.format(value=current_value),
                    severity=rule.metrics.severity,
                    timestamp=current_time,
                    metadata=alert_metadata,
                    lifecycle=alert_lifecycle,
                )

                self.active_alerts[alert_key] = alert
                await self.backend.send_alert(alert)

        else:
            # Check for alert resolution
            alert_key = f"{rule.metrics.metric_name}_{rule.metrics.threshold}"
            if alert_key in self.active_alerts and rule.settings.auto_resolve:
                alert = self.active_alerts[alert_key]
                alert.lifecycle.resolved = True
                alert.lifecycle.resolved_at = current_time
                del self.active_alerts[alert_key]

    async def _send_critical_alert(
        self, name: str, message: str, tags: Optional[dict[str, str]] = None
    ) -> None:
        """Send a critical alert immediately."""
        alert_metadata = AlertMetadata(
            tags=tags or {},
        )
        alert_lifecycle = AlertLifecycle(
            auto_resolve=False,
        )

        alert = Alert(
            name=name,
            message=message,
            severity=AlertSeverity.CRITICAL,
            timestamp=time.time(),
            metadata=alert_metadata,
            lifecycle=alert_lifecycle,
        )

        await self.backend.send_alert(alert)

    def add_threshold_rule(self, rule: ThresholdRule) -> None:
        """Add a custom threshold rule."""
        self._state.threshold_rules.append(rule)
        self.logger.info(f"Added threshold rule for {rule.metrics.metric_name}")

    def remove_threshold_rule(self, metric_name: str, threshold: float) -> bool:
        """Remove a threshold rule."""
        initial_count = len(self._state.threshold_rules)
        self._state.threshold_rules = [
            rule
            for rule in self._state.threshold_rules
            if not (rule.metrics.metric_name == metric_name and rule.metrics.threshold == threshold)
        ]

        if removed := len(self._state.threshold_rules) < initial_count:
            self.logger.info(f"Removed threshold rule for {metric_name}")

        return removed

    def get_strategy_metrics(
        self, strategy_name: Optional[str] = None
    ) -> dict[str, PerformanceMetrics]:
        """Get performance metrics for strategies."""
        if strategy_name:
            if (metrics := self.strategy_metrics.get(strategy_name)) is not None:
                return {strategy_name: metrics}
            return {}
        return self.strategy_metrics.copy()

    def get_system_health(self) -> dict[str, Any]:
        """Get overall system health status."""
        total_operations = sum(m.counts.operation_count for m in self.strategy_metrics.values())
        total_errors = sum(m.counts.error_count for m in self.strategy_metrics.values())
        total_violations = sum(
            m.counts.data_preservation_violations for m in self.strategy_metrics.values()
        )

        overall_error_rate = (total_errors / max(1, total_operations)) * 100
        violations_ratio = total_violations / max(1, total_operations)
        overall_compliance = max(0, (1 - violations_ratio)) * 100

        health_status = "healthy"
        if total_violations > 0:
            health_status = "critical"
        elif overall_error_rate > HEALTH_ERROR_RATE_HIGH:
            health_status = "degraded"
        elif overall_error_rate > HEALTH_ERROR_RATE_WARNING:
            health_status = "warning"

        return {
            "status": health_status,
            "total_operations": total_operations,
            "error_rate": overall_error_rate,
            "data_integrity_compliance": overall_compliance,
            "active_alerts": len(self.active_alerts),
            "monitored_strategies": len(self.strategy_metrics),
            "monitoring_uptime": (
                time.time()
                - (
                    self._monitoring_task.get_loop().time()
                    if self._monitoring_task
                    else time.time()
                )
            ),
        }

    async def generate_report(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> dict[str, Any]:
        """Generate comprehensive monitoring report."""
        end_time = end_time or time.time()
        start_time = start_time or (end_time - 86400)  # Default: last 24 hours

        # Query metrics for the time period
        metric_names = [
            "strategy_success_rate",
            "strategy_error_rate",
            "average_processing_time",
            "data_integrity_compliance",
        ]

        historical_data = await self.backend.query_metrics(metric_names, start_time, end_time)

        # Analyze operations in the time period
        period_operations = [
            op for op in self.operation_history if start_time <= op["timestamp"] <= end_time
        ]

        strategy_analysis = {}
        for strategy_name in self.strategy_metrics:
            if strategy_ops := [op for op in period_operations if op["strategy"] == strategy_name]:
                successful_ops = sum(1 for op in strategy_ops if op["success"])
                preserved_ops = sum(1 for op in strategy_ops if op.get("data_preserved", True))
                strategy_analysis[strategy_name] = {
                    "operations": len(strategy_ops),
                    "success_rate": successful_ops / len(strategy_ops) * 100,
                    "avg_processing_time": statistics.mean(
                        op["processing_time"] for op in strategy_ops
                    ),
                    "data_preservation_rate": (preserved_ops / len(strategy_ops) * 100),
                }

        return {
            "period": {"start": start_time, "end": end_time},
            "system_health": self.get_system_health(),
            "strategy_analysis": strategy_analysis,
            "historical_metrics": historical_data,
            "alerts_summary": {
                "active_alerts": len(self.active_alerts),
                "total_threshold_rules": len(self.threshold_rules),
            },
        }


# Global monitoring instance
_global_monitor: Optional[PromptFittingMonitor] = None


def get_prompt_fitting_monitor() -> PromptFittingMonitor:
    """Get the global prompt fitting monitor instance."""
    # pylint: disable=global-statement
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PromptFittingMonitor()
    return _global_monitor


async def record_fitting_operation(
    strategy_name: str,
    operation_type: str,
    processing_time: float,
    result: Optional[FittingResult[ContentFitterT]] = None,
    error: Optional[Exception] = None,
    **kwargs: Any,
) -> None:
    """Convenience function to record fitting operations."""
    monitor = get_prompt_fitting_monitor()
    params = OperationRecordParams(
        strategy_name=strategy_name,
        operation_type=operation_type,
        processing_time=processing_time,
        result=result,
        error=error,
        metadata=kwargs,
    )
    await monitor.record_operation(params)
