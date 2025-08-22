# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Comprehensive exception hierarchy for prompt fitting operations.

This module provides structured exception classes for different types of
failures that can occur during prompt fitting operations, enabling precise
error handling and debugging.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class TokenLimitErrorDetails:
    """Parameter class for TokenLimitExceededError initialization."""

    message: str
    actual_tokens: int | None = None
    target_tokens: int | None = None
    strategies_attempted: list[str] | None = None
    context: dict[str, Any] | None = None


@dataclass
class ChunkingErrorDetails:
    """Parameter class for ChunkingError initialization."""

    message: str
    strategy_name: str | None = None
    chunk_count: int | None = None
    content_size: int | None = None
    context: dict[str, Any] | None = None


@dataclass
class ValidationErrorDetails:
    """Parameter class for ValidationError initialization."""

    message: str
    validation_type: str | None = None
    expected_value: Any = None
    actual_value: Any = None
    context: dict[str, Any] | None = None


class PromptFittingError(Exception):
    """Base exception for all prompt fitting errors.

    All prompt fitting exceptions inherit from this base class to enable
    comprehensive error handling at the module level.
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        """Initialize with message and optional context.

        Args:
            message: Human-readable error description
            context: Additional context data for debugging
        """
        super().__init__(message)
        self.context = context or {}


class DataIntegrityViolationError(PromptFittingError):
    """Raised when data integrity cannot be preserved.

    This is a critical error that indicates a violation of CLAUDE.md
    requirements for 100% data preservation. It should trigger immediate
    system failure and investigation.
    """

    def __init__(
        self,
        message: str,
        coverage_percentage: float | None = None,
        missing_sections: list[tuple[int, int]] | None = None,
        context: dict[str, Any] | None = None,
    ):
        """Initialize with data integrity violation details.

        Args:
            message: Description of the integrity violation
            coverage_percentage: Actual coverage achieved (if measurable)
            missing_sections: List of (start, end) ranges that were lost
            context: Additional debugging context
        """
        super().__init__(message, context)
        self.coverage_percentage = coverage_percentage
        self.missing_sections = missing_sections or []


class TokenLimitExceededError(PromptFittingError):
    """Raised when content cannot fit within token limits.

    This error occurs when all fitting strategies fail to reduce content
    to within the specified token limits while maintaining data integrity.
    """

    def __init__(self, details: TokenLimitErrorDetails):
        """Initialize with token limit details.

        Args:
            details: TokenLimitErrorDetails containing all initialization parameters
        """
        super().__init__(details.message, details.context)
        self.actual_tokens = details.actual_tokens
        self.target_tokens = details.target_tokens
        self.strategies_attempted = details.strategies_attempted or []


class ChunkingError(PromptFittingError):
    """Raised when chunking strategy fails.

    This error occurs when the chunking algorithm encounters content
    that cannot be properly chunked while maintaining data integrity.
    """

    def __init__(self, details: ChunkingErrorDetails):
        """Initialize with chunking failure details.

        Args:
            details: ChunkingErrorDetails containing all initialization parameters
        """
        super().__init__(details.message, details.context)
        self.strategy_name = details.strategy_name
        self.chunk_count = details.chunk_count
        self.content_size = details.content_size


class ValidationError(PromptFittingError):
    """Raised when content validation fails.

    This error occurs during validation of fitting results when the
    output doesn't meet quality or preservation requirements.
    """

    def __init__(self, details: ValidationErrorDetails):
        """Initialize with validation failure details.

        Args:
            details: ValidationErrorDetails containing all initialization parameters
        """
        super().__init__(details.message, details.context)
        self.validation_type = details.validation_type
        self.expected_value = details.expected_value
        self.actual_value = details.actual_value


class ConfigurationError(PromptFittingError):
    """Raised when configuration is invalid or inconsistent.

    This error occurs when the prompt fitting configuration contains
    invalid values or inconsistent settings that prevent operation.
    """

    def __init__(
        self,
        message: str,
        config_field: str | None = None,
        config_value: Any = None,
        context: dict[str, Any] | None = None,
    ):
        """Initialize with configuration error details.

        Args:
            message: Description of the configuration error
            config_field: Name of the configuration field with invalid value
            config_value: The invalid configuration value
            context: Additional debugging context
        """
        super().__init__(message, context)
        self.config_field = config_field
        self.config_value = config_value


class StrategyError(PromptFittingError):
    """Raised when a specific fitting strategy fails.

    This error occurs when a particular fitting strategy encounters
    an error during execution, allowing fallback to other strategies.
    """

    def __init__(
        self,
        message: str,
        strategy_name: str | None = None,
        original_error: Exception | None = None,
        context: dict[str, Any] | None = None,
    ):
        """Initialize with strategy error details.

        Args:
            message: Description of the strategy error
            strategy_name: Name of the strategy that failed
            original_error: Original exception that caused the failure
            context: Additional debugging context
        """
        super().__init__(message, context)
        self.strategy_name = strategy_name
        self.original_error = original_error


class ContentTypeError(PromptFittingError):
    """Raised when content type is unsupported or invalid.

    This error occurs when attempting to process content of an
    unsupported type or when content type detection fails.
    """

    def __init__(
        self,
        message: str,
        content_type: str | None = None,
        supported_types: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ):
        """Initialize with content type error details.

        Args:
            message: Description of the content type error
            content_type: The unsupported content type
            supported_types: List of supported content types
            context: Additional debugging context
        """
        super().__init__(message, context)
        self.content_type = content_type
        self.supported_types = supported_types or []
