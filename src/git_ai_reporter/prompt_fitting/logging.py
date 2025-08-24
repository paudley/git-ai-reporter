# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Comprehensive logging system for prompt fitting operations.

This module provides structured logging capabilities for debugging,
monitoring, and performance analysis of prompt fitting strategies.

NOTE: This module intentionally shadows the Python builtin 'logging' module
for domain-specific prompt fitting logging functionality.
"""

# flake8: noqa: A005

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
import logging
from pathlib import Path
import time
from typing import Any, Optional

from .constants import FLOAT_PRECISION_DIGITS
from .constants import PERCENTAGE_PRECISION_DIGITS
from .constants import SUCCESS_RATE_PERCENTAGE_MULTIPLIER
from .constants import TIMING_PRECISION_DIGITS


class LogLevel(Enum):
    """Enhanced log levels for prompt fitting operations."""

    DEBUG = "DEBUG"  # Detailed debugging information
    INFO = "INFO"  # General information
    WARNING = "WARNING"  # Warning conditions
    ERROR = "ERROR"  # Error conditions
    CRITICAL = "CRITICAL"  # Critical failures
    PERFORMANCE = "PERFORMANCE"  # Performance metrics
    INTEGRITY = "INTEGRITY"  # Data integrity checks


@dataclass
class ProcessingStats:
    """Processing statistics from prompt fitting operation."""

    content_size: int = 0
    tokens_processed: int = 0
    chunks_created: int = 0
    strategy_used: str = ""


@dataclass
class ExecutionResult:
    """Execution result information."""

    success: bool = False
    error_message: str = ""


@dataclass
class OperationMetrics:
    """Metrics collected during prompt fitting operations."""

    operation_name: str
    processing_stats: ProcessingStats = field(default_factory=ProcessingStats)
    execution_result: ExecutionResult = field(default_factory=ExecutionResult)
    metadata: dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    @property
    def duration(self) -> float:
        """Calculate operation duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def tokens_per_second(self) -> float:
        """Calculate token processing rate."""
        duration = self.duration
        return self.processing_stats.tokens_processed / duration if duration > 0 else 0.0

    def finish(self, success: bool = True, error: Optional[Exception] = None) -> None:
        """Mark the operation as finished."""
        self.end_time = time.time()
        self.execution_result.success = success
        if error:
            self.execution_result.error_message = str(error)


@dataclass
class IntegrityViolationParams:
    """Parameters for logging data integrity violations."""

    original_size: int
    fitted_size: int
    coverage_percentage: float
    missing_sections: list[tuple[int, int]]  # Tuple of start and end positions for missing sections
    strategy_used: str


@dataclass
class LoggerConfig:
    """Configuration for PromptFittingLogger."""

    name: str = "prompt_fitting"
    level: LogLevel = LogLevel.INFO
    log_file: Optional[Path] = None
    enable_performance_logging: bool = True
    enable_integrity_logging: bool = True


@dataclass
class StrategySelectionParams:
    """Parameters for logging strategy selection decisions."""

    content_type: str
    content_size: int
    target_tokens: int
    selected_strategy: str
    reason: str


class PromptFittingLogger:
    """Enhanced logger for prompt fitting operations with structured output."""

    def __init__(self, config: Optional[LoggerConfig] = None):
        """Initialize the prompt fitting logger.

        Args:
            config: LoggerConfig containing all initialization parameters
        """
        config = config or LoggerConfig()
        self.name = config.name
        self.level = config.level
        self.enable_performance = config.enable_performance_logging
        self.enable_integrity = config.enable_integrity_logging

        # Set up Python logger
        self._logger = logging.getLogger(config.name)
        self._logger.setLevel(getattr(logging, config.level.value))

        # Configure handlers
        if not self._logger.handlers:
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

            # File handler (if specified)
            if config.log_file:
                file_handler = logging.FileHandler(config.log_file)
                file_handler.setFormatter(formatter)
                self._logger.addHandler(file_handler)

        # Metrics collection
        self.metrics_history: list[OperationMetrics] = []
        self.current_operation: Optional[OperationMetrics] = None

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with optional metadata."""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with optional metadata."""
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with optional metadata."""
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, error: Optional[Exception] = None, **kwargs: Any) -> None:
        """Log error message with optional exception details."""
        if error:
            message = f"{message}: {error}"
            kwargs.setdefault("error_type", type(error).__name__)
            kwargs.setdefault("error_details", str(error))
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, error: Optional[Exception] = None, **kwargs: Any) -> None:
        """Log critical message with optional exception details."""
        if error:
            message = f"{message}: {error}"
            kwargs.setdefault("error_type", type(error).__name__)
            kwargs.setdefault("error_details", str(error))
        self._log(LogLevel.CRITICAL, message, **kwargs)

    def performance(self, message: str, metrics: OperationMetrics, **kwargs: Any) -> None:
        """Log performance metrics if enabled."""
        if not self.enable_performance:
            return

        kwargs.update(
            {
                "duration": f"{metrics.duration:.3f}s",
                "tokens_per_second": f"{metrics.tokens_per_second:.1f}",
                "content_size": metrics.processing_stats.content_size,
                "tokens_processed": metrics.processing_stats.tokens_processed,
                "chunks_created": metrics.processing_stats.chunks_created,
                "strategy": metrics.processing_stats.strategy_used,
            }
        )

        self._log(LogLevel.PERFORMANCE, message, **kwargs)

    def integrity(self, message: str, **kwargs: Any) -> None:
        """Log data integrity information if enabled."""
        if not self.enable_integrity:
            return
        self._log(LogLevel.INTEGRITY, message, **kwargs)

    def _log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """Internal logging method with structured metadata."""
        # Add metadata to message if present
        if kwargs:
            metadata_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message = f"{message} | {metadata_str}"

        # Log to Python logger
        log_method = getattr(self._logger, level.value.lower())
        log_method(message)

    @asynccontextmanager
    async def operation(
        self,
        name: str,
        content_size: int = 0,
        expected_tokens: int = 0,
        strategy: str = "",
        **metadata: Any,
    ) -> AsyncGenerator[OperationMetrics]:
        """Context manager for tracking operation metrics.

        Usage:
            async with logger.operation("chunking", content_size=1000) as metrics:
                # Perform operation
                metrics.processing_stats.chunks_created = 5
                # Metrics are automatically logged on exit
        """
        metrics = OperationMetrics(operation_name=name)
        metrics.processing_stats.content_size = content_size
        metrics.processing_stats.tokens_processed = expected_tokens
        metrics.processing_stats.strategy_used = strategy
        metrics.metadata = metadata

        self.current_operation = metrics
        self.debug(f"Starting operation: {name}", **metadata)

        try:
            yield metrics
            metrics.finish(success=True)
            self.performance(f"Operation completed: {name}", metrics)

        except Exception as error:
            metrics.finish(success=False, error=error)
            self.error(f"Operation failed: {name}", error=error, **metadata)
            raise

        finally:
            self.metrics_history.append(metrics)
            self.current_operation = None

    def get_performance_summary(self, last_n_operations: Optional[int] = None) -> dict[str, Any]:
        """Get performance summary for recent operations.

        Args:
            last_n_operations: Number of recent operations to analyze (all if None)

        Returns:
            Dictionary with performance statistics
        """
        operations = self.metrics_history
        if last_n_operations:
            operations = operations[-last_n_operations:]

        if not operations:
            return {"message": "No operations recorded"}

        successful_ops = [op for op in operations if op.execution_result.success]
        failed_ops = [op for op in operations if not op.execution_result.success]

        total_duration = sum(op.duration for op in operations)
        total_tokens = sum(op.processing_stats.tokens_processed for op in operations)

        return {
            "total_operations": len(operations),
            "successful": len(successful_ops),
            "failed": len(failed_ops),
            "success_rate": len(successful_ops)
            / len(operations)
            * SUCCESS_RATE_PERCENTAGE_MULTIPLIER,
            "total_duration": f"{total_duration:.{TIMING_PRECISION_DIGITS}f}s",
            "average_duration": f"{total_duration / len(operations):.{TIMING_PRECISION_DIGITS}f}s",
            "total_tokens_processed": total_tokens,
            "average_tokens_per_second": total_tokens / total_duration if total_duration > 0 else 0,
            "strategies_used": list(
                set(
                    op.processing_stats.strategy_used
                    for op in operations
                    if op.processing_stats.strategy_used
                )
            ),
        }

    def log_integrity_violation(self, params: IntegrityViolationParams) -> None:
        """Log a data integrity violation with detailed information."""
        self.critical(
            "DATA INTEGRITY VIOLATION DETECTED",
            original_size=params.original_size,
            fitted_size=params.fitted_size,
            coverage=f"{params.coverage_percentage:.{FLOAT_PRECISION_DIGITS}f}%",
            missing_sections_count=len(params.missing_sections),
            strategy=params.strategy_used,
            violation_type="data_loss",
        )

    def log_chunk_analysis(
        self,
        total_chunks: int,
        average_overlap: float,
        coverage_percentage: float,
        strategy_used: str,
    ) -> None:
        """Log chunk analysis results."""
        self.integrity(
            "Chunk analysis completed",
            total_chunks=total_chunks,
            average_overlap=f"{average_overlap:.{PERCENTAGE_PRECISION_DIGITS}%}",
            coverage=f"{coverage_percentage:.{FLOAT_PRECISION_DIGITS}f}%",
            strategy=strategy_used,
        )

    def log_strategy_selection(self, params: StrategySelectionParams) -> None:
        """Log strategy selection decision."""
        self.info(
            f"Strategy selected: {params.selected_strategy}",
            content_type=params.content_type,
            content_size=params.content_size,
            target_tokens=params.target_tokens,
            reason=params.reason,
        )


def get_logger(name: str = "prompt_fitting") -> PromptFittingLogger:
    """Get or create a prompt fitting logger instance."""
    if not hasattr(get_logger, "_cache"):
        get_logger._cache = {}  # type: ignore[attr-defined]

    if name not in get_logger._cache:  # type: ignore[attr-defined]
        logger_config = LoggerConfig(name=name)
        get_logger._cache[name] = PromptFittingLogger(logger_config)  # type: ignore[attr-defined]

    cached_logger = get_logger._cache[name]  # type: ignore[attr-defined]
    return cached_logger  # type: ignore[no-any-return]


def set_log_level(level: LogLevel) -> None:
    """Set the global log level for prompt fitting operations."""
    logger = get_logger()
    logger.level = level
    logger._logger.setLevel(getattr(logging, level.value))
