# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Threshold rules and evaluation logic.

This module contains threshold rule definitions and evaluation
logic for automated monitoring and alerting.
"""

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
import statistics
from typing import Optional, TYPE_CHECKING

from ..constants import ThresholdOperator
from .models import AlertSeverity

if TYPE_CHECKING:
    from .backends import MonitoringBackend


@dataclass
class RuleMetrics:
    """Threshold rule metrics and thresholds."""

    metric_name: str
    operator: ThresholdOperator
    threshold: float
    severity: AlertSeverity


@dataclass
class RuleSettings:
    """Threshold rule settings and configuration."""

    message_template: str
    evaluation_window: Optional[float] = None  # Time window for evaluation
    consecutive_violations: int = 1  # Required consecutive violations
    auto_resolve: bool = True
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Configuration for monitoring system."""

    backend: Optional["MonitoringBackend"] = None  # MonitoringBackend to avoid circular imports
    enable_performance_tracking: bool = True
    enable_data_integrity_monitoring: bool = True
    metric_collection_interval: float = 60.0


@dataclass
class ThresholdRule:
    """Threshold-based alerting rule."""

    # Grouped attributes
    metrics: RuleMetrics
    settings: RuleSettings

    def evaluate(self, values: list[float]) -> bool:
        """Evaluate threshold against values."""
        if not values:
            return False

        # Use the most recent value or average over window
        test_value = values[-1] if not self.settings.evaluation_window else statistics.mean(values)

        # Define operator evaluation functions
        operator_functions: dict[ThresholdOperator, Callable[[float, float], bool]] = {
            ThresholdOperator.GT: lambda v, t: v > t,
            ThresholdOperator.LT: lambda v, t: v < t,
            ThresholdOperator.GTE: lambda v, t: v >= t,
            ThresholdOperator.LTE: lambda v, t: v <= t,
            ThresholdOperator.EQ: lambda v, t: v == t,
            ThresholdOperator.NE: lambda v, t: v != t,
        }

        if self.metrics.operator not in operator_functions:
            raise ValueError(f"Unknown threshold operator: {self.metrics.operator}")

        return operator_functions[self.metrics.operator](test_value, self.metrics.threshold)
