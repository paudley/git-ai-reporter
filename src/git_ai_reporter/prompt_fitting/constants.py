# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Constants and type literals for prompt fitting system.

This module centralizes all magic numbers, thresholds, and configuration values
used throughout the prompt fitting system. All constants use appropriate typing
with Final, Literal, and Enum as specified by pylint requirements.
"""

from enum import Enum
from enum import IntEnum
from typing import Final, Literal

# =============================================================================
# DATA INTEGRITY AND PRESERVATION CONSTANTS
# =============================================================================

# CLAUDE.md mandates 100% data preservation
REQUIRED_DATA_PRESERVATION_RATE: Final[float] = 100.0
MAX_DATA_PRESERVATION_RATE: Final[float] = 100.0
PERFECT_SUCCESS_RATE: Final[float] = 100.0
PERFECT_COVERAGE_PERCENTAGE: Final[int] = 100  # Used for coverage calculations

# =============================================================================
# CHUNKING AND OVERLAP CONSTANTS
# =============================================================================

# Overlap ratios for maintaining data continuity
DEFAULT_OVERLAP_RATIO: Final[float] = 0.25  # 25% overlap
COMPLEX_CONTENT_OVERLAP_RATIO: Final[float] = 0.3  # 30% for complex content
HIGH_PRECISION_OVERLAP_RATIO: Final[float] = 0.35  # For critical content
DIFF_OVERLAP_RATIO: Final[float] = 0.25  # Diff-specific overlap ratio

# Chunk size parameters
MIN_CHUNK_SIZE: Final[int] = 10
MAX_CHUNK_SIZE: Final[int] = 100
DEFAULT_SMALL_CHUNK_SIZE: Final[int] = 15
DEFAULT_MEDIUM_CHUNK_SIZE: Final[int] = 20
DEFAULT_LARGE_CHUNK_SIZE: Final[int] = 50

# Specialized chunk size limits
MIN_LINES_PER_CHUNK: Final[int] = 10  # Minimum lines per chunk
MIN_DIFF_LINES_PER_CHUNK: Final[int] = 50  # Minimum lines per diff chunk
MIN_OVERLAP_LINES: Final[int] = 10  # Minimum overlap lines
TARGET_CHUNKS_DIVISOR: Final[int] = 8  # Target chunk divisor for estimation
OVERLAP_DIVISOR: Final[int] = 2  # 50% overlap divisor

# Maximum overlap lines for boundary preservation
MAX_OVERLAP_LINES: Final[int] = 3
OVERLAP_PERCENTAGE_DIVISOR: Final[int] = 4  # Up to 25%

# File boundary and extension handling
FILE_BOUNDARY_EXTENSION_RATIO: Final[float] = 0.2  # File boundary extension threshold

# =============================================================================
# TOKEN AND SIZE LIMITS
# =============================================================================

# Standard token limits for testing and processing
STANDARD_TOKEN_TARGET: Final[int] = 1000
TEST_TOKEN_LIMIT: Final[int] = 100
LARGE_CONTENT_THRESHOLD: Final[int] = 1000
SMALL_CONTENT_THRESHOLD: Final[int] = 50

# Content sampling and hashing
CONTENT_SAMPLE_SIZE: Final[int] = 1024
CONTENT_HASH_THRESHOLD: Final[int] = 2048
HASH_LENGTH: Final[int] = 16
CONFIG_HASH_LENGTH: Final[int] = 8

# Token calculation and estimation
ESTIMATED_CHARS_PER_TOKEN: Final[int] = 4  # Characters per token estimation
CHUNK_TOKEN_UTILIZATION_RATIO: Final[float] = 0.4  # Token utilization for chunks
LOG_TOKEN_UTILIZATION_RATIO: Final[float] = 0.3  # Token utilization for log compression
TOKEN_TOLERANCE_MULTIPLIER: Final[float] = 1.1  # 10% token tolerance
CHUNK_TRUNCATION_MULTIPLIER: Final[int] = 2  # Token size multiplier for truncation

# Processing and performance thresholds
PARALLEL_PROCESSING_THRESHOLD: Final[int] = 2  # Threshold for parallel vs sequential
PROCESSING_TIME_PENALTY_THRESHOLD: Final[float] = 5.0  # Processing time penalty threshold
MIN_TIME_PENALTY: Final[float] = 0.5  # Minimum time penalty
TIME_PENALTY_DIVISOR: Final[float] = 10.0  # Time penalty calculation divisor

# Parallel processing configuration
DEFAULT_MAX_WORKERS: Final[int] = 4  # Default worker count for parallel processing
DEFAULT_CHUNK_BATCH_SIZE: Final[int] = 10  # Default batch size for chunk processing
MIN_TOKEN_COUNT_FOR_CONTENT: Final[int] = 1  # Minimum tokens per content piece
ESTIMATED_TARGET_CHUNKS: Final[int] = 8  # Target number of chunks
MIN_LINES_PER_ESTIMATED_CHUNK: Final[int] = 10  # Minimum lines per chunk estimate

# =============================================================================
# CACHING CONFIGURATION
# =============================================================================

# Cache size limits
DEFAULT_CACHE_MAX_ENTRIES: Final[int] = 1000
MEMORY_CACHE_DEFAULT_SIZE: Final[int] = 100
FACTORY_CACHE_SIZE: Final[int] = 100  # For MemoryCacheBackend in factory
SIMILARITY_SEARCH_LIMIT: Final[int] = 100

# Cache key and display limits
CACHE_KEY_DISPLAY_LENGTH: Final[int] = 32
CONTENT_DISPLAY_SAMPLE_LENGTH: Final[int] = 50

# Time conversion constants
HOURS_TO_SECONDS_MULTIPLIER: Final[int] = 3600

# Similarity matching thresholds
SIMILARITY_LENGTH_TOLERANCE: Final[float] = 0.8
SIMILARITY_LENGTH_UPPER_BOUND: Final[float] = 1.2

# =============================================================================
# ANALYSIS AND PATTERN DETECTION
# =============================================================================

# Line analysis thresholds
LONG_LINE_THRESHOLD: Final[int] = 120
SUBSTANTIAL_LINE_THRESHOLD: Final[int] = 10
MIN_LONG_LINES_FOR_PATTERN: Final[int] = 3
MIN_REPETITIONS_FOR_PATTERN: Final[int] = 3

# Comment and block detection
MIN_COMMENT_BLOCK_LINES: Final[int] = 3
MIN_PARAGRAPH_LINES: Final[int] = 2

# Proximity and grouping
CHANGE_LINE_PROXIMITY_THRESHOLD: Final[int] = 3
MIN_CLUSTER_SIZE: Final[int] = 5
MIN_CHANGE_LINES_FOR_DENSITY: Final[int] = 5
MIN_DOCSTRING_QUOTE_COUNT: Final[int] = 2

# Content type detection sample sizes
PYTHON_DETECTION_SAMPLE_LINES: Final[int] = 20
GIT_DIFF_DETECTION_SAMPLE_LINES: Final[int] = 10
MARKDOWN_DETECTION_SAMPLE_LINES: Final[int] = 10
LOG_DETECTION_SAMPLE_LINES: Final[int] = 20
SHELL_DETECTION_SAMPLE_LINES: Final[int] = 10
SQL_DETECTION_SAMPLE_LINES: Final[int] = 10
CONFIG_DETECTION_SAMPLE_LINES: Final[int] = 20

# Pattern matching requirements
MIN_LOG_MATCHES: Final[int] = 3
MIN_PYTHON_INDICATORS: Final[int] = 2
MIN_MARKDOWN_INDICATORS: Final[int] = 1
MIN_SHELL_INDICATORS: Final[int] = 2
MIN_SQL_MATCHES: Final[int] = 2
MIN_CONFIG_MATCHES: Final[int] = 5

# Boundary preservation and overlap validation
MIN_OVERLAP_THRESHOLD: Final[float] = 0.1  # 10% minimum overlap between chunks
BROKEN_STRUCTURE_PENALTY: Final[float] = 5.0  # Penalty per broken structure
SIGNIFICANT_LOSS_THRESHOLD: Final[float] = 0.1  # 10% loss threshold
PERFECT_PRESERVATION_SCORE: Final[float] = 100.0  # Perfect preservation baseline

# =============================================================================
# IMPORTANCE AND CONFIDENCE SCORING
# =============================================================================

# High confidence thresholds
HIGH_IMPORTANCE_THRESHOLD: Final[float] = 0.8
HIGH_CONFIDENCE_THRESHOLD: Final[float] = 0.85
VERY_HIGH_CONFIDENCE: Final[float] = 0.9

# Medium confidence ranges
MEDIUM_CONFIDENCE: Final[float] = 0.8
MEDIUM_IMPORTANCE: Final[float] = 0.6

# Low confidence baselines
LOW_IMPORTANCE: Final[float] = 0.3
DEFAULT_IMPORTANCE: Final[float] = 0.5

# =============================================================================
# COMPLEXITY ASSESSMENT
# =============================================================================

# Complexity scoring thresholds
COMPLEXITY_SIMPLE_THRESHOLD: Final[float] = 0.3
COMPLEXITY_MODERATE_THRESHOLD: Final[float] = 0.6
COMPLEXITY_THRESHOLD: Final[float] = 0.6

# Boundary and structural analysis
BOUNDARY_FLEXIBILITY_MULTIPLIER: Final[float] = 1.5
BOUNDARY_DENSITY_MULTIPLIER: Final[int] = 10
MAX_COMPLEXITY_CONTRIBUTION: Final[float] = 0.3
VARIANCE_NORMALIZER: Final[int] = 10000
MAX_VARIANCE_CONTRIBUTION: Final[float] = 0.1

# =============================================================================
# STRATEGY SELECTION AND SCORING
# =============================================================================

# Strategy priority values for fallback chain
PRIMARY_STRATEGY_PRIORITY: Final[int] = 100  # Highest priority strategies
SECONDARY_STRATEGY_PRIORITY: Final[int] = 90  # Secondary strategies
TERTIARY_STRATEGY_PRIORITY: Final[int] = 80  # Tertiary strategies

# Strategy condition thresholds
MIN_LINES_FOR_OVERLAPPING_CHUNKS: Final[int] = 3  # Minimum lines for chunk strategy
DIFF_DETECTION_SAMPLE_LINES: Final[int] = 10  # Lines to check for diff patterns


# Base strategy confidence scores
class StrategyConfidence:
    """Strategy confidence score constants."""

    VERY_HIGH: Final[float] = 0.95  # Specialized strategies (diff_truncation for diffs)
    HIGH: Final[float] = 0.9  # Well-suited strategies (semantic for Python)
    GOOD: Final[float] = 0.8  # Good match strategies
    ACCEPTABLE: Final[float] = 0.7  # Acceptable fallback options
    FAIR: Final[float] = 0.6  # Fair options for content type
    DEFAULT: Final[float] = 0.5  # Default baseline confidence


# Strategy selection adjustments
PERFORMANCE_BOOST: Final[float] = 0.2
QUALITY_BOOST: Final[float] = 0.25
CACHING_BOOST: Final[float] = 0.25
PARALLEL_BOOST: Final[float] = 0.2
SEMANTIC_BOOST: Final[float] = 0.25
ADAPTIVE_BOOST: Final[float] = 0.2
FALLBACK_BOOST: Final[float] = 0.15
OVERLAPPING_BOOST: Final[float] = 0.1

# Penalty values
EXPERIMENTAL_PENALTY: Final[float] = 0.3
MEMORY_INTENSIVE_PENALTY: Final[float] = 0.2
PARALLEL_SMALL_CONTENT_PENALTY: Final[float] = 0.2

# Data integrity requirements
PERFECT_DATA_PRESERVATION_BOOST: Final[float] = 0.1

# Content size thresholds for strategy selection
LARGE_CONTENT_BOOST: Final[float] = 0.2
CACHING_LARGE_CONTENT_BOOST: Final[float] = 0.15
SMALL_CONTENT_OVERLAPPING_BOOST: Final[float] = 0.15

# =============================================================================
# PLUGIN SYSTEM CONSTANTS
# =============================================================================


class PluginPriorityValues(IntEnum):
    """Plugin priority value constants."""

    CRITICAL = 100  # System-critical plugins (highest priority)
    HIGH = 75  # High-priority custom strategies
    NORMAL = 50  # Standard plugins (default)
    LOW = 25  # Fallback or experimental strategies
    EXPERIMENTAL = 10  # Lowest priority for testing


# Plugin validation
PLUGIN_TEST_TOKEN_LIMIT: Final[int] = 100
PLUGIN_VALIDATION_CONTENT: Final[str] = "This is a test content for plugin validation."

# Python version requirement
MIN_PYTHON_VERSION: Final[str] = "3.12"

# =============================================================================
# FACTORY AND SELECTION CONSTANTS
# =============================================================================

# Selection history management
MAX_SELECTION_HISTORY_SIZE: Final[int] = 1000
TOP_STRATEGIES_COUNT: Final[int] = 3

# Factory statistics and performance
CONFIDENCE_MULTIPLIER_FOR_PRIORITY: Final[int] = 100
MAX_FALLBACK_RETRIES: Final[int] = 1

# =============================================================================
# FALLBACK AND RETRY CONFIGURATION
# =============================================================================

# Timeout values
DEFAULT_STRATEGY_TIMEOUT: Final[float] = 300.0  # 5 minutes
FALLBACK_TIMEOUT_SECONDS: Final[float] = 300.0

# Retry and failure handling
MAX_CONSECUTIVE_FAILURES: Final[int] = 5
FAILURE_THRESHOLD_FOR_DISABLE: Final[int] = 3

# Retry timing and backoff
RETRY_BACKOFF_BASE_SECONDS: Final[float] = 0.1  # Exponential backoff multiplier
CIRCUIT_BREAKER_FAILURE_THRESHOLD: Final[int] = 3  # Circuit breaker activation threshold
MAX_BLACKLIST_DURATION_SECONDS: Final[int] = 300  # 5 minute maximum blacklist
BASE_BLACKLIST_DURATION_SECONDS: Final[int] = 60  # 1 minute base blacklist

# =============================================================================
# LOGGING AND MONITORING
# =============================================================================

# Performance metrics formatting
TIMING_PRECISION_DIGITS: Final[int] = 3  # For f"{duration:.3f}s"
HIT_RATE_PERCENTAGE_MULTIPLIER: Final[int] = 100
SUCCESS_RATE_PERCENTAGE_MULTIPLIER: Final[int] = 100  # For success rate calculations
PERCENTAGE_PRECISION_DIGITS: Final[int] = 1  # For f"{value:.1%}"
FLOAT_PRECISION_DIGITS: Final[int] = 1  # For f"{value:.1f}"

# Content display limits
STRUCTURAL_ELEMENTS_LIMIT: Final[int] = 100
EXPRESSION_DISPLAY_LENGTH: Final[int] = 100
LINE_CONTENT_PREVIEW_LENGTH: Final[int] = 10

# Search and analysis limits
HUNK_SEARCH_WINDOW: Final[int] = 10
PATTERN_SEARCH_LOOKAHEAD: Final[int] = 10

# Monitoring threshold values
ERROR_RATE_THRESHOLD: Final[float] = 10.0  # Error rate monitoring threshold
PROCESSING_TIME_THRESHOLD: Final[float] = 30.0  # Processing time threshold
MEMORY_USAGE_THRESHOLD_MB: Final[float] = 1024.0  # Memory usage threshold in MB
DEFAULT_EVALUATION_WINDOW_SECONDS: Final[float] = 300.0  # Default evaluation window
HEALTH_DEGRADED_ERROR_RATE_THRESHOLD: Final[float] = 10.0  # Health degraded threshold
HEALTH_WARNING_ERROR_RATE_THRESHOLD: Final[float] = 5.0  # Health warning threshold

# =============================================================================
# MATHEMATICAL AND STATISTICAL CONSTANTS
# =============================================================================

# Percentage calculations
FULL_PERCENTAGE: Final[int] = 100
QUARTER_PERCENTAGE: Final[float] = 0.25

# Division safety
MIN_DIVISOR: Final[int] = 1  # Prevents division by zero

# Chunking calculations
CHUNK_SIZE_SQRT_DIVISOR_BASE: Final[int] = 1  # For math.sqrt usage
ADAPTIVE_CHUNK_DIVISORS = {
    "small": 5,  # total_lines // 5
    "medium": 4,  # total_lines // 4
    "large": 3,  # total_lines // 3
}

# =============================================================================
# STRING AND CONTENT CONSTANTS
# =============================================================================

# Strategy name mappings and identifiers
STRATEGY_NAME_OVERLAPPING: Final[str] = "overlapping"
STRATEGY_NAME_SEMANTIC: Final[str] = "semantic"
STRATEGY_NAME_ADAPTIVE: Final[str] = "adaptive"
STRATEGY_NAME_PARALLEL: Final[str] = "parallel"
STRATEGY_NAME_CACHED: Final[str] = "cached"
STRATEGY_NAME_FALLBACK: Final[str] = "fallback"
STRATEGY_NAME_DIFF_TRUNCATION: Final[str] = "diff_truncation"
STRATEGY_NAME_LOG_COMPRESSION: Final[str] = "log_compression"
STRATEGY_NAME_EXPERIMENTAL: Final[str] = "experimental"

# Performance priority levels
PERFORMANCE_PRIORITY: Final[str] = "PERFORMANCE"
QUALITY_PRIORITY: Final[str] = "QUALITY"

# System health thresholds
HEALTH_ERROR_RATE_HIGH: Final[int] = 10  # Error rate threshold for degraded health
HEALTH_ERROR_RATE_WARNING: Final[int] = 5  # Error rate threshold for warning health

# Validation and constraint thresholds
MIN_DATA_PRESERVATION_RATIO: Final[float] = 0.6  # Minimum acceptable data preservation
MIN_TARGET_TOKENS: Final[int] = 1000  # Minimum target tokens for validation
EFFICIENCY_SCORE_DIVISOR: Final[float] = 5.0  # Divisor for efficiency score calculation
OVERLAP_WARNING_THRESHOLD: Final[float] = 0.6  # Warning threshold for high overlap ratios
MIN_PRACTICAL_TOKEN_LIMIT: Final[int] = 1000  # Minimum tokens for practical use


# Git diff detection patterns
GIT_DIFF_HEADER_PATTERN: Final[str] = "diff --git"
GIT_DIFF_HUNK_PATTERN: Final[str] = "@@"
GIT_DIFF_ADD_PREFIX: Final[str] = "+"
GIT_DIFF_REMOVE_PREFIX: Final[str] = "-"
GIT_DIFF_CONTEXT_PREFIX: Final[str] = " "

# JSON structure markers
JSON_OPEN_BRACE: Final[str] = "{"
JSON_CLOSE_BRACE: Final[str] = "}"

# Chunk segment headers for content organization
CONTENT_SEGMENT_HEADER: Final[str] = "--- Content Segment"
DIFF_SEGMENT_HEADER: Final[str] = "--- Diff Segment"
LOG_SEGMENT_HEADER: Final[str] = "--- Log Segment"
PARALLEL_CHUNK_HEADER_PREFIX: Final[str] = "--- Parallel Chunk"
PARALLEL_PROCESSING_FOOTER: Final[str] = "--- PARALLEL PROCESSING:"
OVERLAPPING_CHUNKS_FOOTER: Final[str] = "--- OVERLAPPING CHUNKS:"

# Content type indicators (using Literal for type safety)
DocstringMarkers = Literal['"""', "'''"]
TRIPLE_QUOTE_DOUBLE: Final[str] = '"""'
TRIPLE_QUOTE_SINGLE: Final[str] = "'''"

# File extension and pattern markers
PYTHON_FILE_EXTENSIONS: Final[tuple[str, ...]] = (".py", ".pyi", ".pyw")
CONFIG_FILE_EXTENSIONS: Final[tuple[str, ...]] = (
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".conf",
    ".cfg",
)

# Content headers and separators
CHUNK_CONTINUATION_MARKER: Final[str] = "--- CONTINUATION ---"
SEMANTIC_CHUNK_HEADER_PREFIX: Final[str] = "--- Semantic Chunk"
SEMANTIC_ANALYSIS_FOOTER_PREFIX: Final[str] = "--- SEMANTIC ANALYSIS:"
FALLBACK_CHUNK_SUFFIX: Final[str] = "(Fallback)"
PARALLEL_PROCESSING_FOOTER_PREFIX: Final[str] = "--- PARALLEL PROCESSING:"

# Content size and type indicators
LARGE_DIFF_CONTENT_PREFIX: Final[str] = "[LARGE_DIFF_CONTENT:"
LARGE_LOG_CONTENT_PREFIX: Final[str] = "[LARGE_LOG_CONTENT:"
SHELL_SCRIPT_SHEBANG_INDICATOR: Final[str] = "sh"

# Plugin validation error messages
PLUGIN_VALIDATION_ERROR_NOT_CONTENTFITTER: Final[str] = "does not create ContentFitter instance"
PLUGIN_VALIDATION_ERROR_NOT_FITTINGRESULT: Final[str] = "does not return FittingResult"
DATA_INTEGRITY_VIOLATION_MESSAGE: Final[str] = "violates data integrity requirement"

# =============================================================================
# VALIDATION AND ERROR HANDLING
# =============================================================================

# Test content for validation
VALIDATION_TEST_CONTENT: Final[str] = "This is a test content for plugin validation."

# Error threshold percentages converted to ratios
TOKEN_USAGE_THRESHOLD_RATIO: Final[float] = 0.8  # 80% of target tokens
PROCESSING_EFFICIENCY_TARGET: Final[float] = 0.8  # 80% efficiency target

# Test and validation constants
VALIDATION_SEGMENT_MARKER: Final[str] = "Segment"
TEST_DATA_PRESERVATION_RATIO: Final[float] = 0.8
TEST_TARGET_TOKENS: Final[int] = 50
PERFECT_COVERAGE_TEST_VALUE: Final[float] = 100.0
TEST_CHUNK_DIVISOR: Final[int] = 4
MIN_CHUNK_SIZE_FOR_OVERLAP: Final[int] = 4

# Complexity and structure constants
CODE_IMPROVEMENT_TARGET: Final[float] = 0.1  # 10% improvement target
STRUCTURAL_IMPROVEMENT_TARGET: Final[float] = 0.05  # 5% improvement

# Processing constants for external services
MAX_CHUNK_PAIRS: Final[int] = 3  # Maximum chunk pairs to process
MAX_LOG_REDUCTION_LINES: Final[int] = 20  # Maximum lines for log reduction
ORCHESTRATOR_SAMPLED_MARKER: Final[str] = "sampled"  # Orchestrator sampling marker

# Test constants for plugin system
TEST_PLUGIN_NAME: Final[str] = "test_plugin"
SPECIAL_CONTENT_MARKER: Final[str] = "special_content"
DECORATED_PLUGIN_NAME: Final[str] = "decorated_plugin"
DECORATED_PLUGIN_VERSION: Final[str] = "2.0.0"
AVERAGE_USAGE_STAT: Final[str] = "average_usage"
ERROR_RATE_STAT: Final[str] = "error_rate"

# =============================================================================
# PATTERN TYPE CONSTANTS
# =============================================================================

# Python pattern types for analysis
PATTERN_TYPE_COMPREHENSION: Final[str] = "comprehension"
PATTERN_TYPE_GENERATOR: Final[str] = "generator"
PATTERN_TYPE_FILE_MODIFICATION: Final[str] = "file_modification"
PATTERN_TYPE_FILE_ADDITION: Final[str] = "file_addition"
PATTERN_TYPE_DIFF_HUNK: Final[str] = "diff_hunk"

# Complete set of Python pattern types (used by analyzer)
PYTHON_PATTERN_TYPES: Final[set[str]] = {
    "single_line_docstring",
    "multi_line_docstring",
    "future_imports",
    "stdlib_imports",
    "third_party_imports",
    "decorator_block",
    "exception_handling",
    "list_comprehension",
    "set_comprehension",
    "dict_comprehension",
    "generator_expression",
}

# Git diff pattern constants
MAGIC_NUMBER_FOUR: Final[int] = 4
MAGIC_NUMBER_TEN: Final[int] = 10
MAGIC_NUMBER_SEVEN: Final[int] = 7
MAGIC_NUMBER_EIGHT: Final[int] = 8
MAGIC_NUMBER_TWO: Final[int] = 2
MAGIC_NUMBER_THREE: Final[int] = 3
MAGIC_NUMBER_FIVE: Final[int] = 5
MAGIC_NUMBER_FIFTEEN: Final[int] = 15
MAGIC_NUMBER_TWENTY: Final[int] = 20

# Pattern type constants
PATTERN_TYPE_HIGH_CHANGE_DENSITY: Final[str] = "high_change_density"
PATTERN_TYPE_IMPORT: Final[str] = "import"
PATTERN_TYPE_DIFF: Final[str] = "diff"
PATTERN_TYPE_FILE: Final[str] = "file"
PATTERN_TYPE_MARKDOWN_SECTION: Final[str] = "markdown_section"
VALIDATION_FAILED_MESSAGE: Final[str] = "validation failed"
LOW_PRIORITY_PLUGIN_NAME: Final[str] = "low_priority_plugin"

# Metadata keys for analysis
PATTERN_TYPES_KEY: Final[str] = "pattern_types"
BOUNDARY_TYPES_KEY: Final[str] = "boundary_types"
ANALYSIS_VERSION_KEY: Final[str] = "analysis_version"

# Additional magic numbers
MAGIC_NUMBER_FIFTY: Final[int] = 50
MAGIC_NUMBER_HUNDRED: Final[float] = 100.0

# Plugin test constants
PLUGIN_VERSION_1_0_0: Final[str] = "1.0.0"
TESTING_TAG: Final[str] = "testing"
GIT_DIFF_CONTENT_TYPE: Final[str] = "git_diff"

# Content segment markers
CONTENT_SEGMENT_MARKER: Final[str] = "--- Content Segment"

# Test-specific constants
TEST_TOKEN_LIMIT_1000: Final[int] = 1000
TEST_COVERAGE_100_PERCENT: Final[float] = 100.0
CHUNKS_VALIDATION_KEY: Final[str] = "chunks"
TEST_CHANGE_COUNT_FIVE: Final[int] = 5
TEST_BOUNDARY_COUNT_FIFTY: Final[int] = 50
IMPORT_KEYWORD: Final[str] = "import"
DIFF_KEYWORD: Final[str] = "diff"
FILE_KEYWORD: Final[str] = "file"
FILE_REFERENCE_LOSS_MESSAGE: Final[str] = "file reference loss"
OVERLAP_KEYWORD: Final[str] = "overlap"
CONFIDENCE_THRESHOLD_90: Final[float] = 0.9
INVALID_CONTENT_MESSAGE: Final[str] = "invalid content"
EMPTY_CONTENT_MESSAGE: Final[str] = "empty content"
TEST_CONTENT_TEXT: Final[str] = "test content"
VERSION_1_0_0: Final[str] = "1.0.0"

# Monitoring test constants
TEST_METRIC_NAME: Final[str] = "test_metric"
TEST_METRIC_VALUE: Final[float] = 42.5
TEST_TAG_VALUE: Final[str] = "test"
TEST_METRIC_DESCRIPTION: Final[str] = "Test metric"
TEST_ALERT_NAME: Final[str] = "test_alert"
ALERT_THRESHOLD_75: Final[float] = 75.0
PERFORMANCE_THRESHOLD_95: Final[float] = 95.0
ERROR_RATE_5: Final[float] = 5.0
RESPONSE_TIME_2_5: Final[float] = 2.5
CACHE_HIT_RATE_98: Final[float] = 98.0
METRIC_VALUE_10: Final[float] = 10.0
COUNT_VALUE_2: Final[int] = 2
ALERT_2_NAME: Final[str] = "alert2"
ALERT_3_NAME: Final[str] = "alert3"
TEST_STRATEGY_NAME: Final[str] = "test_strategy"
DURATION_1_5: Final[float] = 1.5
DATA_INTEGRITY_VIOLATION: Final[str] = "data_integrity_violation"
STRATEGY_1_NAME: Final[str] = "strategy1"
STRATEGY_2_NAME: Final[str] = "strategy2"
ERROR_COUNT_150: Final[int] = 150
CRITICAL_LEVEL: Final[str] = "critical"
OPERATION_COUNT_4: Final[int] = 4
PERIOD_KEY: Final[str] = "period"
SYSTEM_HEALTH_KEY: Final[str] = "system_health"
STRATEGY_ANALYSIS_KEY: Final[str] = "strategy_analysis"
ALERTS_SUMMARY_KEY: Final[str] = "alerts_summary"
SUCCESS_RATE_80: Final[float] = 80.0
GLOBAL_TEST_NAME: Final[str] = "global_test"
DATA_INTEGRITY_KEY: Final[str] = "data_integrity"

# =============================================================================
# TYPE ALIASES AND ENUMS
# =============================================================================

# Commonly used type literals
CacheHitType = Literal["hit", "miss", "similarity_match"]
StrategyType = Literal[
    "overlapping",
    "semantic",
    "adaptive",
    "parallel",
    "cached",
    "fallback",
    "diff_truncation",
    "log_compression",
]
ProcessingStage = Literal["analysis", "chunking", "fitting", "validation", "caching"]


class ContentTypeIndicator(Enum):
    """Content type detection indicators."""

    PYTHON_CODE = "python_code"
    GIT_DIFF = "git_diff"
    MARKDOWN = "markdown"
    JSON_DATA = "json_data"
    LOG_FILE = "log_file"
    PLAIN_TEXT = "plain_text"
    CONFIG_FILE = "config_file"
    SHELL_SCRIPT = "shell_script"
    SQL_QUERY = "sql_query"
    MIXED_CONTENT = "mixed_content"


class ComplexityLevel(Enum):
    """Content complexity assessment levels."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    HIGHLY_COMPLEX = "highly_complex"


class ThresholdOperator(Enum):
    """Threshold comparison operators for monitoring rules."""

    GT = "gt"  # Greater than
    LT = "lt"  # Less than
    GTE = "gte"  # Greater than or equal
    LTE = "lte"  # Less than or equal
    EQ = "eq"  # Equal
    NE = "ne"  # Not equal


# =============================================================================
# CONTENT TYPE COMPLEXITY MAPPING
# =============================================================================

# Complexity weights by content type
CONTENT_TYPE_COMPLEXITY_WEIGHTS: Final[dict[str, float]] = {
    "plain_text": 0.1,
    "markdown": 0.2,
    "config_file": 0.3,
    "log_file": 0.4,
    "shell_script": 0.5,
    "json_data": 0.6,
    "sql_query": 0.7,
    "python_code": 0.8,
    "git_diff": 0.8,
    "mixed_content": 0.9,
}

# Test environment detection
PYTEST_MARKER: Final[str] = "pytest"  # Used to detect pytest test environment
