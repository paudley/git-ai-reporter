# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Parameter classes for reducing function argument counts.

This module provides structured parameter classes to improve function signatures
and reduce the number of positional arguments in function calls, addressing
pylint warnings about too many arguments.
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Any, Optional

from .prompt_fitting import PromptFittingConfig
from .prompt_fitting import TokenCounter


@dataclass
class FitterCreationParams:
    """Parameters for creating optimal content fitters through the factory system.

    This dataclass encapsulates all parameters needed for the ContentFitterFactory
    to analyze content characteristics, select optimal strategies, and create
    enhanced fitters with caching and fallback capabilities.

    Args:
        content: The input content string to be fitted within token limits.
            This content will be analyzed for type, complexity, and structure
            to determine the most suitable fitting strategy.
        config: Complete prompt fitting configuration containing token limits,
            quality settings, validation rules, and strategy preferences.
        token_counter: Token counting service for measuring content size and
            ensuring fitting results stay within specified limits.
        requirements: Optional strategy selection requirements including data
            preservation thresholds, performance priorities, and feature flags.
            Defaults to balanced requirements if not specified.
        enable_caching: Whether to enable intelligent caching for repeated
            content patterns. Caching can significantly improve performance
            for similar content but requires additional memory.
        enable_fallback: Whether to create fallback chains for robust error
            handling. Fallback chains try multiple strategies if primary
            strategy fails, improving overall reliability.

    Example:
        >>> params = FitterCreationParams(
        ...     content="Large Python code file...",
        ...     config=my_config,
        ...     token_counter=my_counter,
        ...     enable_caching=True,
        ...     enable_fallback=True
        ... )
        >>> fitter = await factory.create_optimal_fitter(params)
    """

    content: str
    config: PromptFittingConfig
    token_counter: TokenCounter
    requirements: Optional[Any] = None  # StrategyRequirements to avoid circular imports
    enable_caching: bool = True
    enable_fallback: bool = True


@dataclass
class NamedFitterCreationParams:
    """Parameters for creating specific fitters by strategy name.

    This dataclass is used when you want to create a specific fitting strategy
    by name, bypassing the automatic strategy selection process. Useful for
    testing specific strategies or when you have domain knowledge about which
    strategy works best for your content type.

    Args:
        strategy_name: Name of the specific strategy to create. Must match one
            of the available strategy names like 'OverlappingChunksFitter',
            'SemanticChunksFitter', or 'ParallelProcessingFitter'.
        config: Prompt fitting configuration with token limits and settings
            that will be applied to the created fitter instance.
        token_counter: Token counting service used by the fitter to measure
            content size and ensure compliance with token limits.
        enable_caching: Whether to wrap the created fitter with caching
            capabilities. Generally disabled for named creation since
            caching is typically applied at the factory level.
        enable_fallback: Whether to create fallback chains for the named
            strategy. Usually disabled since named creation implies you
            want that specific strategy without alternatives.

    Example:
        >>> params = NamedFitterCreationParams(
        ...     strategy_name="SemanticChunksFitter",
        ...     config=my_config,
        ...     token_counter=my_counter,
        ...     enable_caching=False,
        ...     enable_fallback=False
        ... )
        >>> fitter = await factory.create_fitter_by_name(params)
    """

    strategy_name: str
    config: PromptFittingConfig
    token_counter: TokenCounter
    enable_caching: bool = False
    enable_fallback: bool = False


@dataclass
class EnhancementParams:
    """Parameters for applying enhancements to base content fitters.

    This dataclass controls the enhancement process that wraps base fitters
    with additional capabilities like caching, fallback chains, and monitoring.
    Enhancements are applied in a specific order to ensure optimal performance
    and reliability.

    Args:
        base_fitter: The core content fitter to be enhanced. This is the
            fundamental strategy (like OverlappingChunksFitter) that will
            be wrapped with additional capabilities.
        config: Prompt fitting configuration that will be used by all
            enhancement layers, ensuring consistent behavior across
            the enhanced fitter stack.
        token_counter: Token counting service shared across all enhancement
            layers for consistent token measurement and limit enforcement.
        enable_caching: Whether to wrap the base fitter with intelligent
            caching capabilities. Caching stores results for similar content
            patterns and can dramatically improve performance for repeated
            content types.
        enable_fallback: Whether to create fallback chains using the
            strategy rankings. Fallback chains try alternative strategies
            if the primary strategy fails, improving overall reliability.
        strategy_rankings: Ordered list of strategy names with confidence
            scores used to build fallback chains. Higher confidence strategies
            are tried first, with lower confidence as fallbacks. Empty list
            disables fallback chain creation.

    Note:
        Enhancement order is: base_fitter -> caching -> fallback -> monitoring.
        This ensures optimal performance characteristics and error handling.

    Example:
        >>> params = EnhancementParams(
        ...     base_fitter=semantic_fitter,
        ...     config=my_config,
        ...     token_counter=my_counter,
        ...     enable_caching=True,
        ...     enable_fallback=True,
        ...     strategy_rankings=[("semantic", 0.95), ("overlapping", 0.80)]
        ... )
        >>> enhanced_fitter = await factory._apply_enhancements(params)
    """

    base_fitter: Any  # ContentFitter to avoid circular imports
    config: PromptFittingConfig
    token_counter: TokenCounter
    enable_caching: bool
    enable_fallback: bool
    strategy_rankings: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class BenchmarkParams:
    """Parameters for comprehensive strategy performance benchmarking.

    This dataclass encapsulates all parameters needed to benchmark a single
    fitting strategy against test content, measuring performance metrics like
    processing time, success rate, data preservation, and compression efficiency.

    Args:
        strategy_name: Human-readable name of the strategy being benchmarked.
            Used for reporting and logging benchmark results. Should match
            the strategy's display name for consistency.
        strategy_class: The actual class type of the strategy to benchmark.
            Must be a subclass of ContentFitter and have a constructor that
            accepts config and token_counter parameters.
        test_content: List of diverse content samples to test the strategy
            against. Should include various content types, sizes, and complexity
            levels to get comprehensive performance metrics. Each string
            represents one test case.
        config: Prompt fitting configuration used for all benchmark runs.
            Should use consistent settings across all strategy benchmarks
            for fair comparison of performance metrics.
        token_counter: Token counting service used to measure input and output
            sizes during benchmarking. Must be the same instance across all
            benchmarks for consistent token measurement methodology.

    Note:
        Benchmark results include success_rate, average_processing_time,
        data_preservation_rate, compression_ratio, and error_count metrics.

    Example:
        >>> test_samples = [
        ...     "Short Python function...",
        ...     "Large Git diff with many changes...",
        ...     "Complex JSON configuration..."
        ... ]
        >>> params = BenchmarkParams(
        ...     strategy_name="SemanticChunksFitter",
        ...     strategy_class=SemanticChunksFitter,
        ...     test_content=test_samples,
        ...     config=standard_config,
        ...     token_counter=shared_counter
        ... )
        >>> metrics = await factory._benchmark_single_strategy(params)
    """

    strategy_name: str
    strategy_class: type
    test_content: list[str]
    config: PromptFittingConfig
    token_counter: TokenCounter


@dataclass
class ExceptionParams:
    """Common parameters for creating custom prompt fitting exceptions.

    This dataclass standardizes the creation of custom exceptions throughout
    the prompt fitting system, ensuring consistent error reporting with
    comprehensive context information for debugging and monitoring.

    Args:
        message: Primary error message describing what went wrong. Should be
            clear, actionable, and suitable for both logging and user display.
            Avoid technical jargon when possible and include suggested solutions.
        strategy_name: Name of the fitting strategy that encountered the error.
            Useful for identifying which strategy failed and enabling fallback
            logic. None if the error occurred outside strategy execution.
        content_size: Size of the content being processed when error occurred,
            measured in characters or tokens depending on context. Helps
            identify if errors are related to content size limits.
        token_limit: The token limit that was active when the error occurred.
            Combined with content_size, helps diagnose limit-related issues
            and guides optimization efforts.
        details: Additional context-specific error details as key-value pairs.
            Common keys include 'error_code', 'retry_count', 'processing_time',
            'chunk_count', 'coverage_percentage', and 'validation_failures'.

    Note:
        This parameter class is used by StrategyError, ValidationError,
        TokenLimitError, and other custom exception types for consistent
        error context across the entire prompt fitting system.

    Example:
        >>> params = ExceptionParams(
        ...     message="Semantic analysis failed: insufficient content structure",
        ...     strategy_name="SemanticChunksFitter",
        ...     content_size=15420,
        ...     token_limit=8000,
        ...     details={
        ...         'error_code': 'SEMANTIC_PARSE_FAILURE',
        ...         'chunk_count': 0,
        ...         'processing_time': 2.34
        ...     }
        ... )
        >>> raise StrategyError(params)
    """

    message: str
    strategy_name: Optional[str] = None
    content_size: Optional[int] = None
    token_limit: Optional[int] = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringParams:
    """Parameters for recording and monitoring prompt fitting operations.

    This dataclass captures essential metrics and context for monitoring
    the performance and reliability of prompt fitting operations. Data
    is used for performance analysis, alerting, and optimization decisions.

    Args:
        operation_type: Type of operation being monitored such as 'fit_content',
            'validate_chunks', 'semantic_analysis', or 'cache_lookup'. Used
            for categorizing metrics and identifying performance bottlenecks.
        processing_time: Total time taken for the operation in seconds,
            measured from start to completion. Includes all sub-operations
            and waiting time but excludes queue time before processing starts.
        content_size: Size of the content being processed, measured in
            characters. Used for correlating performance with input size
            and identifying scaling characteristics of different strategies.
        tokens_used: Number of tokens consumed during processing, including
            both input tokens and any generated intermediate representations.
            Critical for cost analysis and resource planning.
        success: Whether the operation completed successfully without errors.
            Failed operations still provide valuable monitoring data for
            reliability analysis and error pattern identification.
        error_message: Human-readable error description if operation failed.
            Should include enough context for debugging without exposing
            sensitive information. None for successful operations.
        metadata: Additional operation-specific metrics and context as
            key-value pairs. Common keys include 'strategy_name', 'chunk_count',
            'compression_ratio', 'cache_hit', 'retry_count', and 'memory_peak'.

    Note:
        This data feeds into dashboards, alerts, and automated optimization
        systems. Ensure consistent field usage across all monitored operations.

    Example:
        >>> params = MonitoringParams(
        ...     operation_type="fit_content",
        ...     processing_time=1.23,
        ...     content_size=8500,
        ...     tokens_used=2100,
        ...     success=True,
        ...     error_message=None,
        ...     metadata={
        ...         'strategy_name': 'SemanticChunksFitter',
        ...         'chunk_count': 4,
        ...         'compression_ratio': 0.75,
        ...         'cache_hit': False
        ...     }
        ... )
        >>> await monitor.record_operation(params)
    """

    operation_type: str
    processing_time: float
    content_size: int
    tokens_used: int
    success: bool
    error_message: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoggingParams:
    """Parameters for structured logging throughout the prompt fitting system.

    This dataclass standardizes logging operations across all components,
    ensuring consistent log formatting, appropriate log levels, and
    comprehensive context for debugging and monitoring purposes.

    Args:
        level: Log level following standard Python logging levels: 'DEBUG',
            'INFO', 'WARNING', 'ERROR', or 'CRITICAL'. Use INFO for normal
            operations, WARNING for recoverable issues, ERROR for failures
            that don't stop processing, and CRITICAL for system failures.
        component: Name of the component generating the log entry such as
            'OverlappingChunksFitter', 'CacheManager', or 'ValidationEngine'.
            Used for filtering logs by subsystem and identifying issue sources.
        operation: Specific operation being logged such as 'fit_content',
            'validate_data_preservation', 'cache_store', or 'strategy_selection'.
            Provides fine-grained visibility into system behavior.
        message: Human-readable log message describing what happened. Should
            be clear, actionable, and include relevant metrics or identifiers.
            Avoid sensitive information and use consistent formatting.
        context: Additional structured data relevant to the log entry as
            key-value pairs. Common keys include 'content_size', 'processing_time',
            'strategy_name', 'success_rate', 'error_code', and 'user_id'.
            Used for log analysis and alerting.
        exception: Exception object if logging an error condition. The
            exception's type, message, and stack trace will be included
            in the log entry. None for non-error log entries.

    Note:
        All logs are structured for machine parsing and include timestamps,
        correlation IDs, and performance metrics for comprehensive observability.

    Example:
        >>> params = LoggingParams(
        ...     level="ERROR",
        ...     component="SemanticChunksFitter",
        ...     operation="fit_content",
        ...     message="Failed to parse content structure, falling back to overlapping chunks",
        ...     context={
        ...         'content_size': 12500,
        ...         'processing_time': 2.1,
        ...         'fallback_strategy': 'OverlappingChunksFitter',
        ...         'error_code': 'PARSE_FAILURE'
        ...     },
        ...     exception=semantic_error
        ... )
        >>> logger.log_operation(params)
    """

    level: str
    component: str
    operation: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    exception: Optional[Exception] = None


@dataclass
class FallbackStrategyParams:
    """Parameters for configuring individual fallback strategies in chains.

    This dataclass defines the configuration for a single fallback strategy
    within a fallback chain, including retry behavior, timeouts, and priority
    ordering. Multiple fallback strategies form resilient processing chains.

    Args:
        fitter_class: The ContentFitter class to instantiate for this fallback
            strategy. Must have a constructor accepting (config, token_counter)
            parameters and implement the ContentFitter interface completely.
        name: Human-readable name for this fallback strategy, used in logging
            and monitoring. Should be descriptive and unique within the chain
            to enable easy identification in error messages and metrics.
        priority: Execution priority within the fallback chain, with higher
            numbers indicating higher priority. Primary strategy should have
            highest priority, with progressively lower priorities for fallbacks.
            Strategies execute in descending priority order.
        max_retries: Maximum number of retry attempts for this strategy before
            moving to the next fallback. Each retry uses exponential backoff
            based on retry_delay. Zero disables retries for this strategy.
        timeout_seconds: Maximum time allowed for this strategy to complete,
            in seconds. If exceeded, strategy is considered failed and next
            fallback is attempted. None disables timeout enforcement.
        retry_delay: Base delay between retries in seconds. Actual delay uses
            exponential backoff: delay * (2 ^ retry_attempt). Prevents
            overwhelming resources during transient failures.
        enable_caching: Whether this specific fallback strategy should use
            caching. Generally false since caching is applied at chain level,
            but can be true for expensive fallback strategies.

    Note:
        Fallback chains are constructed by sorting strategies by priority
        and attempting each one until success or chain exhaustion.

    Example:
        >>> primary = FallbackStrategyParams(
        ...     fitter_class=SemanticChunksFitter,
        ...     name="semantic_primary",
        ...     priority=100,
        ...     max_retries=2,
        ...     timeout_seconds=30.0,
        ...     retry_delay=1.0
        ... )
        >>> fallback = FallbackStrategyParams(
        ...     fitter_class=OverlappingChunksFitter,
        ...     name="overlapping_fallback",
        ...     priority=50,
        ...     max_retries=1,
        ...     timeout_seconds=15.0,
        ...     retry_delay=0.5
        ... )
        >>> chain = FallbackChain([primary, fallback])
    """

    fitter_class: type
    name: str
    priority: int
    max_retries: int
    timeout_seconds: Optional[float] = None
    retry_delay: float = 1.0
    enable_caching: bool = False


@dataclass
class ParallelProcessingParams:
    """Parameters for configuring parallel processing capabilities in content fitters.

    This dataclass encapsulates all parameters needed to configure parallel processing
    features for content fitting operations, including worker management, chunk sizing
    optimization, and load balancing strategies for optimal performance across
    different content types and system resources.

    Args:
        config: Complete prompt fitting configuration containing token limits,
            quality settings, validation rules, and performance parameters.
            Used to ensure all parallel workers operate with consistent
            settings and maintain compliance with system requirements.
        token_counter: Token counting service shared across all parallel workers
            for consistent token measurement and limit enforcement. Must be
            thread-safe and efficient for concurrent access patterns.
        max_workers: Maximum number of parallel workers to use for concurrent
            processing operations. Higher values increase throughput but consume
            more system resources. Should be tuned based on available CPU cores
            and memory constraints. Typical range: 2-16 workers.
        chunk_size_multiplier: Multiplier applied to base chunk sizes for parallel
            processing optimization. Values > 1.0 create larger chunks to reduce
            coordination overhead, while values < 1.0 create smaller chunks for
            better load distribution. Default 1.5 provides good balance.
        enable_load_balancing: Whether to enable dynamic load balancing across
            parallel workers. When enabled, the system monitors worker performance
            and redistributes work to optimize throughput. Adds slight overhead
            but improves performance for heterogeneous workloads.

    Note:
        Parallel processing is most effective for large content sizes (>1000 tokens)
        and CPU-intensive operations like semantic analysis. For small content,
        sequential processing may be faster due to reduced coordination overhead.

    Example:
        >>> params = ParallelProcessingParams(
        ...     config=production_config,
        ...     token_counter=shared_counter,
        ...     max_workers=8,
        ...     chunk_size_multiplier=2.0,  # Larger chunks for efficiency
        ...     enable_load_balancing=True
        ... )
        >>> parallel_fitter = ParallelProcessingFitter(params)
        >>> result = await parallel_fitter.fit_content(large_content, 4000)
    """

    config: PromptFittingConfig
    token_counter: TokenCounter
    max_workers: int
    chunk_size_multiplier: float = 1.5
    enable_load_balancing: bool = True
