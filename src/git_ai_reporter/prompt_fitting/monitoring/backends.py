# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Monitoring backend implementations.

This module contains all monitoring backend implementations including
in-memory storage and external service integrations.
"""

from collections import deque
from typing import Protocol

from ..logging import get_logger
from .models import Alert
from .models import MetricValue


class MonitoringBackend(Protocol):
    """Protocol for monitoring backend implementations."""

    async def send_metric(self, metric: MetricValue) -> bool:
        """Send a metric to the monitoring backend."""
        raise NotImplementedError

    async def send_alert(self, alert: Alert) -> bool:
        """Send an alert to the monitoring backend."""
        raise NotImplementedError

    async def query_metrics(
        self, metric_names: list[str], start_time: float, end_time: float
    ) -> dict[str, list[MetricValue]]:
        """Query historical metrics."""
        raise NotImplementedError


class InMemoryMonitoringBackend:
    """In-memory monitoring backend for testing and development."""

    def __init__(self, max_metrics: int = 10000, max_alerts: int = 1000):
        """Initialize in-memory backend."""
        self.metrics: dict[str, deque[MetricValue]] = {}
        self.alerts: deque[Alert] = deque(maxlen=max_alerts)
        self.max_metrics_per_name = max_metrics
        self.logger = get_logger("InMemoryMonitoringBackend")

    async def send_metric(self, metric: MetricValue) -> bool:
        """Store metric in memory."""
        try:
            if metric.name not in self.metrics:
                self.metrics[metric.name] = deque(maxlen=self.max_metrics_per_name)

            self.metrics[metric.name].append(metric)
            return True
        except (AttributeError, TypeError, ValueError) as e:
            self.logger.error(f"Failed to store metric {metric.name}: {e}")
            return False

    async def send_alert(self, alert: Alert) -> bool:
        """Store alert in memory."""
        try:
            self.alerts.append(alert)
            self.logger.warning(f"Alert: {alert.name} - {alert.message}")
            return True
        except (AttributeError, TypeError, ValueError) as e:
            self.logger.error(f"Failed to store alert {alert.name}: {e}")
            return False

    async def query_metrics(
        self, metric_names: list[str], start_time: float, end_time: float
    ) -> dict[str, list[MetricValue]]:
        """Query metrics from memory."""
        results = {}

        for name in metric_names:
            if name in self.metrics:
                filtered_metrics = [
                    m for m in self.metrics[name] if start_time <= m.timestamp <= end_time
                ]
                results[name] = filtered_metrics
            else:
                results[name] = []

        return results

    def get_recent_alerts(self, count: int = 10) -> list[Alert]:
        """Get recent alerts."""
        return list(self.alerts)[-count:]

    def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        self.metrics.clear()

    def clear_alerts(self) -> None:
        """Clear all stored alerts."""
        self.alerts.clear()


class PrometheusMonitoringBackend:
    """Prometheus monitoring backend (placeholder for future implementation)."""

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        """Initialize Prometheus backend."""
        self.prometheus_url = prometheus_url
        self.logger = get_logger("PrometheusMonitoringBackend")

    async def send_metric(self, metric: MetricValue) -> bool:
        """Send metric to Prometheus (placeholder)."""
        self.logger.info(f"Would send to Prometheus: {metric.name}={metric.value}")
        return True

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Alertmanager (placeholder)."""
        self.logger.info(f"Would send alert to Alertmanager: {alert.name}")
        return True

    async def query_metrics(
        self, metric_names: list[str], start_time: float, end_time: float
    ) -> dict[str, list[MetricValue]]:
        """Query metrics from Prometheus (placeholder)."""
        # NOTE: Placeholder implementation - Prometheus integration pending
        # pylint: disable=unused-argument
        self.logger.info(f"Would query Prometheus for metrics: {metric_names}")
        return {name: [] for name in metric_names}
