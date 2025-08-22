# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Advanced prompt window fitting for data-preserving token management.

This module provides sophisticated strategies for fitting large content into
LLM token limits while preserving 100% data integrity. It implements various
research-backed approaches for content compression without information loss.

The module supports multiple fitting strategies:
- Overlapping chunks for maintaining continuity
- Intelligent diff truncation preserving structure
- Data-preserving log compression with overlapping chunks
- Extensible framework for custom strategies

All strategies are validated to ensure zero data loss while efficiently
working within language model constraints.
"""

from .advanced_strategies import AdaptiveChunksFitter
from .advanced_strategies import ContentAnalyzer
from .advanced_strategies import SemanticChunksFitter
from .analysis import AdvancedContentAnalyzer
from .analysis import ContentCharacteristics
from .analysis import ContentComplexity
from .analysis import ContentPattern
from .analysis import ContentType as AnalysisContentType
from .analysis import PatternDetector
from .caching import CachedContentFitter
from .caching import CachedContentFitterConfig
from .caching import FileCacheBackend
from .caching import MemoryCacheBackend
# Constants and type definitions
from .constants import BASE_BLACKLIST_DURATION_SECONDS
from .constants import BROKEN_STRUCTURE_PENALTY
from .constants import CHANGE_LINE_PROXIMITY_THRESHOLD
from .constants import CHUNK_CONTINUATION_MARKER
from .constants import CHUNK_TOKEN_UTILIZATION_RATIO
from .constants import CHUNK_TRUNCATION_MULTIPLIER
from .constants import CIRCUIT_BREAKER_FAILURE_THRESHOLD
from .constants import ComplexityLevel
from .constants import CONTENT_TYPE_COMPLEXITY_WEIGHTS
from .constants import ContentTypeIndicator
from .constants import DATA_INTEGRITY_VIOLATION_MESSAGE
from .constants import DEFAULT_CHUNK_BATCH_SIZE
from .constants import DEFAULT_EVALUATION_WINDOW_SECONDS
from .constants import DEFAULT_MAX_WORKERS
from .constants import DEFAULT_OVERLAP_RATIO
from .constants import DEFAULT_STRATEGY_TIMEOUT
from .constants import DIFF_DETECTION_SAMPLE_LINES
from .constants import DIFF_OVERLAP_RATIO
from .constants import ERROR_RATE_THRESHOLD
from .constants import ESTIMATED_CHARS_PER_TOKEN
from .constants import ESTIMATED_TARGET_CHUNKS
from .constants import FALLBACK_CHUNK_SUFFIX
from .constants import FILE_BOUNDARY_EXTENSION_RATIO
from .constants import FLOAT_PRECISION_DIGITS
from .constants import HEALTH_DEGRADED_ERROR_RATE_THRESHOLD
from .constants import HEALTH_WARNING_ERROR_RATE_THRESHOLD
from .constants import HIGH_IMPORTANCE_THRESHOLD
from .constants import LARGE_CONTENT_THRESHOLD
from .constants import LARGE_DIFF_CONTENT_PREFIX
from .constants import LARGE_LOG_CONTENT_PREFIX
from .constants import LOG_TOKEN_UTILIZATION_RATIO
from .constants import MAX_BLACKLIST_DURATION_SECONDS
from .constants import MAX_CHUNK_SIZE
from .constants import MEMORY_USAGE_THRESHOLD_MB
from .constants import MIN_CHANGE_LINES_FOR_DENSITY
from .constants import MIN_CHUNK_SIZE
from .constants import MIN_CLUSTER_SIZE
from .constants import MIN_DIFF_LINES_PER_CHUNK
from .constants import MIN_DOCSTRING_QUOTE_COUNT
from .constants import MIN_LINES_FOR_OVERLAPPING_CHUNKS
from .constants import MIN_LINES_PER_CHUNK
from .constants import MIN_LINES_PER_ESTIMATED_CHUNK
from .constants import MIN_OVERLAP_LINES
from .constants import MIN_OVERLAP_THRESHOLD
from .constants import MIN_TIME_PENALTY
from .constants import MIN_TOKEN_COUNT_FOR_CONTENT
from .constants import OVERLAP_DIVISOR
from .constants import PARALLEL_CHUNK_HEADER_PREFIX
from .constants import PARALLEL_PROCESSING_FOOTER_PREFIX
from .constants import PARALLEL_PROCESSING_THRESHOLD
from .constants import PERCENTAGE_PRECISION_DIGITS
from .constants import PERFECT_DATA_PRESERVATION_BOOST
from .constants import PERFECT_PRESERVATION_SCORE
from .constants import PLUGIN_VALIDATION_ERROR_NOT_CONTENTFITTER
from .constants import PLUGIN_VALIDATION_ERROR_NOT_FITTINGRESULT
from .constants import PluginPriorityValues
from .constants import PRIMARY_STRATEGY_PRIORITY
from .constants import PROCESSING_TIME_PENALTY_THRESHOLD
from .constants import PROCESSING_TIME_THRESHOLD
from .constants import REQUIRED_DATA_PRESERVATION_RATE
from .constants import RETRY_BACKOFF_BASE_SECONDS
from .constants import SECONDARY_STRATEGY_PRIORITY
from .constants import SEMANTIC_ANALYSIS_FOOTER_PREFIX
from .constants import SEMANTIC_CHUNK_HEADER_PREFIX
from .constants import SHELL_SCRIPT_SHEBANG_INDICATOR
from .constants import SIGNIFICANT_LOSS_THRESHOLD
from .constants import SMALL_CONTENT_THRESHOLD
from .constants import STANDARD_TOKEN_TARGET
from .constants import StrategyConfidence
from .constants import SUCCESS_RATE_PERCENTAGE_MULTIPLIER
from .constants import TARGET_CHUNKS_DIVISOR
from .constants import TERTIARY_STRATEGY_PRIORITY
from .constants import TIME_PENALTY_DIVISOR
from .constants import TOKEN_TOLERANCE_MULTIPLIER
from .exceptions import ChunkingError
from .exceptions import ChunkingErrorDetails
from .exceptions import ConfigurationError
from .exceptions import ContentTypeError
from .exceptions import DataIntegrityViolationError
from .exceptions import PromptFittingError
from .exceptions import StrategyError
from .exceptions import TokenLimitErrorDetails
from .exceptions import TokenLimitExceededError
from .exceptions import ValidationError
from .exceptions import ValidationErrorDetails
# Factory and plugin system
from .factory import ContentFitterFactory
from .factory import get_content_fitter_factory
from .factory import HeuristicStrategySelector
from .factory import MLStrategySelector
from .factory import OptimizationTarget
from .factory import SelectionCriteria
from .factory import StrategyPerformanceMetrics
from .factory import StrategyRequirements
# Advanced strategies and components
from .fallback import FallbackChainFitter
from .fallback import FallbackStrategy
from .fallback import FallbackStrategyConfig
from .logging import get_logger
from .logging import LogLevel
from .logging import OperationMetrics
from .logging import set_log_level
# Monitoring system
from .monitoring import Alert
from .monitoring import AlertSeverity
from .monitoring import get_prompt_fitting_monitor
from .monitoring import InMemoryMonitoringBackend
from .monitoring import MetricType
from .monitoring import MetricValue
from .monitoring import PerformanceMetrics
from .monitoring import PrometheusMonitoringBackend
from .monitoring import PromptFittingMonitor
from .monitoring import record_fitting_operation
from .monitoring import ThresholdRule
from .parallel import ParallelProcessingFitter
from .parallel import ParallelTokenCounter
from .plugins import BasePlugin
from .plugins import get_plugin_registry
from .plugins import PluginMetadata
from .plugins import PluginPriority
from .plugins import PluginRegistry
from .plugins import PluginStatus
from .plugins import prompt_fitting_plugin
from .plugins import register_plugin
from .prompt_fitting import ContentFitter
from .prompt_fitting import ContentType
from .prompt_fitting import DiffTruncationFitter
from .prompt_fitting import fit_commit_log
from .prompt_fitting import fit_git_diff
from .prompt_fitting import fit_with_overlapping_chunks
from .prompt_fitting import FittingResult
from .prompt_fitting import FittingStrategy
from .prompt_fitting import LogCompressionFitter
from .prompt_fitting import OverlappingChunksFitter
from .prompt_fitting import PromptFitter
from .prompt_fitting import PromptFittingConfig
from .prompt_fitting import TokenCounter
from .utils import analyze_structural_integrity
from .utils import calculate_all_chunk_overlaps
from .utils import calculate_average_overlap
from .utils import calculate_chunk_overlap_ratio
from .utils import cluster_nearby_indices
from .utils import detect_empty_chunks
from .utils import get_critical_structure_patterns
from .utils import group_consecutive_indices
from .utils import identify_low_overlap_pairs
from .utils import split_content_into_lines
from .validation import DataIntegrityValidator
from .validation import ValidationResult

__all__ = ['AdaptiveChunksFitter', 'AdvancedContentAnalyzer', 'Alert', 'AlertSeverity', 'AnalysisContentType',
 'BasePlugin', 'CHANGE_LINE_PROXIMITY_THRESHOLD', 'CONTENT_TYPE_COMPLEXITY_WEIGHTS',
 'CachedContentFitter', 'CachedContentFitterConfig', 'ChunkingError', 'ChunkingErrorDetails',
 'ComplexityLevel', 'ConfigurationError', 'ContentAnalyzer', 'ContentCharacteristics',
 'ContentComplexity', 'ContentFitter', 'ContentFitterFactory', 'ContentPattern', 'ContentType',
 'ContentTypeError', 'ContentTypeIndicator', 'DEFAULT_OVERLAP_RATIO', 'DataIntegrityValidator',
 'DataIntegrityViolationError', 'DiffTruncationFitter', 'FallbackChainFitter', 'FallbackStrategy',
 'FallbackStrategyConfig', 'FileCacheBackend', 'FittingResult', 'LARGE_CONTENT_THRESHOLD',
 'LogCompressionFitter', 'LogLevel', 'MAX_CHUNK_SIZE', 'MIN_CHANGE_LINES_FOR_DENSITY',
 'MIN_CHUNK_SIZE', 'MIN_CLUSTER_SIZE', 'MIN_DOCSTRING_QUOTE_COUNT', 'MLStrategySelector',
 'MemoryCacheBackend', 'MetricType', 'MetricValue', 'OperationMetrics', 'OptimizationTarget',
 'OverlappingChunksFitter', 'PERFECT_DATA_PRESERVATION_BOOST', 'ParallelProcessingFitter',
 'ParallelTokenCounter', 'PatternDetector', 'PerformanceMetrics', 'PluginMetadata',
 'PluginPriority', 'PluginPriorityValues', 'PluginRegistry', 'PluginStatus',
 'PrometheusMonitoringBackend', 'PromptFitter', 'PromptFittingConfig', 'PromptFittingError',
 'PromptFittingMonitor', 'REQUIRED_DATA_PRESERVATION_RATE', 'SMALL_CONTENT_THRESHOLD',
 'STANDARD_TOKEN_TARGET', 'SelectionCriteria', 'SemanticChunksFitter', 'StrategyConfidence',
 'StrategyError', 'StrategyPerformanceMetrics', 'StrategyRequirements', 'ThresholdRule',
 'TokenCounter', 'TokenLimitErrorDetails', 'TokenLimitExceededError', 'ValidationError',
 'ValidationErrorDetails', 'ValidationResult', 'cluster_nearby_indices', 'fit_commit_log',
 'fit_git_diff', 'fit_with_overlapping_chunks', 'get_content_fitter_factory', 'get_logger',
 'get_plugin_registry', 'get_prompt_fitting_monitor', 'group_consecutive_indices',
 'prompt_fitting_plugin', 'record_fitting_operation', 'register_plugin', 'set_log_level',
 'split_content_into_lines']
