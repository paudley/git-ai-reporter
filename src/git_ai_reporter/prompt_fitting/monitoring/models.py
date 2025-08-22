# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Core monitoring data models and enums.

This module contains all the data classes, enums, and value objects
used throughout the monitoring system.
"""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any, Optional, Union

from ..prompt_fitting import FittingResult


class MetricType(Enum):
    """Types of metrics collected by the monitoring system."""

    COUNTER = "counter"  # Incremental count (operations, errors)
    GAUGE = "gauge"  # Point-in-time value (memory, token count)
    HISTOGRAM = "histogram"  # Distribution of values (response times)
    TIMER = "timer"  # Duration measurements
    SUMMARY = "summary"  # Statistical summaries


class AlertSeverity(Enum):
    """Severity levels for monitoring alerts."""

    CRITICAL = "critical"  # System failure, data loss
    HIGH = "high"  # Performance degradation, compliance violation
    MEDIUM = "medium"  # Resource usage warnings
    LOW = "low"  # Informational alerts
    INFO = "info"  # Status updates


@dataclass
class MetricValue:
    """Individual metric value with metadata."""

    name: str
    value: float
    metric_type: MetricType
    timestamp: float
    tags: dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None


@dataclass
class AlertMetadata:
    """Alert metadata and values."""

    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class AlertLifecycle:
    """Alert lifecycle tracking."""

    auto_resolve: bool = True
    resolved: bool = False
    resolved_at: Optional[float] = None


@dataclass
class Alert:
    """Monitoring alert with context and severity."""

    name: str
    message: str
    severity: AlertSeverity
    timestamp: float

    # Grouped attributes
    metadata: AlertMetadata = field(default_factory=AlertMetadata)
    lifecycle: AlertLifecycle = field(default_factory=AlertLifecycle)

    @property
    def resolved(self) -> bool:
        """Get resolved status from lifecycle."""
        return self.lifecycle.resolved

    @property
    def resolved_at(self) -> Optional[float]:
        """Get resolved timestamp from lifecycle."""
        return self.lifecycle.resolved_at

    @property
    def metric_value(self) -> Optional[float]:
        """Get metric value from metadata."""
        return self.metadata.metric_value


@dataclass
class OperationCounts:
    """Operation counts and success metrics."""

    operation_count: int = 0
    success_count: int = 0
    error_count: int = 0
    data_preservation_violations: int = 0


@dataclass
class PerformanceData:
    """Performance and efficiency metrics."""

    total_processing_time: float = 0.0
    average_compression_ratio: float = 1.0
    token_efficiency_score: float = 0.0
    memory_peak_usage: int = 0
    last_updated: float = 0.0


@dataclass
class PerformanceMetrics:
    """Performance metrics for strategy analysis."""

    strategy_name: str

    # Grouped metrics
    counts: OperationCounts = field(default_factory=OperationCounts)
    performance: PerformanceData = field(default_factory=PerformanceData)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        return (self.counts.success_count / max(1, self.counts.operation_count)) * 100

    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage."""
        return (self.counts.error_count / max(1, self.counts.operation_count)) * 100

    @property
    def average_processing_time(self) -> float:
        """Calculate average processing time."""
        return self.performance.total_processing_time / max(1, self.counts.operation_count)

    @property
    def data_integrity_compliance(self) -> float:
        """Calculate data integrity compliance as percentage."""
        violations = self.counts.data_preservation_violations
        return (
            max(0, (self.counts.operation_count - violations) / max(1, self.counts.operation_count))
            * 100
        )


@dataclass
class OperationRecordParams:
    """Parameters for recording monitoring operations."""

    strategy_name: str
    operation_type: str
    processing_time: float
    result: Optional[FittingResult[Any]] = None  # Forward reference for type safety
    error: Optional[Exception] = None
    metadata: Optional[dict[str, Union[str, int, float, bool]]] = None
