# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Factory pattern system for intelligent prompt fitting strategy selection.

This module provides sophisticated factory patterns for creating and selecting
optimal prompt fitting strategies based on content analysis, performance
requirements, and data integrity constraints from CLAUDE.md.
"""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
import time
from typing import Any, cast, Optional, Protocol, TypedDict, Union

from .advanced_strategies import AdaptiveChunksFitter
from .advanced_strategies import SemanticChunksFitter
from .analysis import AdvancedContentAnalyzer
from .analysis import ContentCharacteristics
from .analysis import ContentType
from .caching import CachedContentFitter
from .caching import CachedContentFitterConfig
from .caching import MemoryCacheBackend
from .constants import CONFIDENCE_MULTIPLIER_FOR_PRIORITY
from .constants import FACTORY_CACHE_SIZE
from .constants import FULL_PERCENTAGE
from .constants import MAX_FALLBACK_RETRIES
from .constants import MAX_SELECTION_HISTORY_SIZE
from .constants import PERFECT_SUCCESS_RATE
from .constants import REQUIRED_DATA_PRESERVATION_RATE
from .constants import STANDARD_TOKEN_TARGET
from .constants import StrategyConfidence
from .constants import TOP_STRATEGIES_COUNT
from .exceptions import StrategyError
from .fallback import FallbackChainFitter
from .fallback import FallbackStrategy
from .fallback import FallbackStrategyConfig
from .logging import get_logger
from .parallel import ParallelProcessingFitter
from .parameters import BenchmarkParams
from .parameters import EnhancementParams
from .parameters import FitterCreationParams
from .parameters import NamedFitterCreationParams
from .plugins import get_plugin_registry
from .plugins import PluginRegistry
from .prompt_fitting import ContentFitter
from .prompt_fitting import DiffTruncationFitter
from .prompt_fitting import LogCompressionFitter
from .prompt_fitting import OverlappingChunksFitter
from .prompt_fitting import PromptFittingConfig
from .prompt_fitting import TokenCounter
from .utils.strategy_selection import apply_content_size_adjustments
from .utils.strategy_selection import apply_data_integrity_adjustments
from .utils.strategy_selection import apply_optimization_target_adjustments
from .utils.strategy_selection import apply_performance_priority_adjustments
from .utils.strategy_selection import calculate_complexity_adjustments
from .utils.strategy_selection import create_content_type_preferences
from .utils.strategy_selection import create_strategy_name_mapping
from .utils.strategy_selection import normalize_and_sort_scores


class SelectionRecord(TypedDict):
    """Structure for selection history records."""

    timestamp: float
    content_type: str
    complexity: str
    content_size: int
    requirements: dict[str, Union[str, bool]]
    selected_strategy: str
    confidence: float


class FactoryStats(TypedDict):
    """Structure for factory statistics."""

    total_creations: int
    selections_recorded: int
    strategy_distribution: dict[str, int]
    content_type_distribution: dict[str, int]
    complexity_distribution: dict[str, int]
    average_confidence: float
    available_strategies: int
    plugin_count: int


class NoStatsMessage(TypedDict):
    """Message when no statistics are available."""

    message: str


class SelectionCriteria(Enum):
    """Criteria for strategy selection."""

    PERFORMANCE = "performance"  # Optimize for speed
    QUALITY = "quality"  # Optimize for best results
    BALANCED = "balanced"  # Balance performance and quality
    DATA_INTEGRITY = "data_integrity"  # Maximum data preservation (CLAUDE.md)
    EXPERIMENTAL = "experimental"  # Use cutting-edge strategies
    RELIABILITY = "reliability"  # Most stable strategies


class OptimizationTarget(Enum):
    """Optimization targets for strategy selection."""

    SPEED = "speed"  # Minimize processing time
    MEMORY = "memory"  # Minimize memory usage
    ACCURACY = "accuracy"  # Maximize fitting accuracy
    COMPRESSION_RATIO = "compression"  # Optimize compression efficiency
    TOKEN_EFFICIENCY = "tokens"  # Maximize token utilization  # nosec B105


@dataclass
class PerformanceConstraints:
    """Performance and resource constraints."""

    max_processing_time: Optional[float] = None
    max_memory_usage: Optional[int] = None


@dataclass
class StrategyFilters:
    """Strategy inclusion/exclusion filters."""

    required_features: list[str] = field(default_factory=list)
    excluded_strategies: list[str] = field(default_factory=list)
    feature_flags: dict[str, bool] = field(
        default_factory=lambda: {"allow_experimental": False, "require_validation": True}
    )

    @property
    def allow_experimental(self) -> bool:
        """Check if experimental strategies are allowed."""
        return self.feature_flags.get("allow_experimental", False)

    @property
    def require_validation(self) -> bool:
        """Check if validation is required."""
        return self.feature_flags.get("require_validation", True)


@dataclass
class StrategyRequirements:
    """Requirements and constraints for strategy selection."""

    # Core requirements
    min_data_preservation: float = REQUIRED_DATA_PRESERVATION_RATE  # CLAUDE.md requires 100%
    performance_priority: SelectionCriteria = SelectionCriteria.BALANCED
    optimization_target: OptimizationTarget = OptimizationTarget.ACCURACY

    # Grouped constraints
    performance: PerformanceConstraints = field(default_factory=PerformanceConstraints)
    filters: StrategyFilters = field(default_factory=StrategyFilters)

    @property
    def allow_experimental(self) -> bool:
        """Check if experimental strategies are allowed."""
        return self.filters.allow_experimental

    @property
    def require_validation(self) -> bool:
        """Check if validation is required."""
        return self.filters.require_validation


@dataclass
class StrategyPerformanceMetrics:
    """Performance metrics for a strategy."""

    # Primary metrics
    success_rate: float = PERFECT_SUCCESS_RATE
    data_preservation_rate: float = REQUIRED_DATA_PRESERVATION_RATE

    # Performance timings
    average_processing_time: float = 0.0
    last_updated: float = 0.0

    # Resource usage
    memory_peak_usage: int = 0
    token_efficiency: float = 0.0

    # Compression metrics (consolidate related metrics)
    compression_metrics: dict[str, float] = field(
        default_factory=lambda: {
            "average_ratio": 1.0,
            "usage_count": 0,
        }  # neutral compression baseline
    )

    @property
    def average_compression_ratio(self) -> float:
        """Get average compression ratio."""
        return self.compression_metrics.get("average_ratio", 1.0)

    @property
    def usage_count(self) -> int:
        """Get usage count."""
        return int(self.compression_metrics.get("usage_count", 0))


class StrategySelector(Protocol):
    """Protocol for strategy selection algorithms."""

    def select_strategy(
        self,
        content_characteristics: ContentCharacteristics,
        requirements: StrategyRequirements,
        available_strategies: dict[str, type[ContentFitter]],
    ) -> list[tuple[str, float]]:
        """Select strategies with confidence scores."""
        ...  # pylint: disable=unnecessary-ellipsis


class HeuristicStrategySelector:
    """Heuristic-based strategy selector using rules and patterns."""

    def __init__(self) -> None:
        self.logger = get_logger("HeuristicStrategySelector")

    def select_strategy(
        self,
        content_characteristics: ContentCharacteristics,
        requirements: StrategyRequirements,
        available_strategies: dict[str, type[ContentFitter]],
    ) -> list[tuple[str, float]]:
        """Select strategies using heuristic rules."""
        # Start with base strategy scores based on content type
        scores = self._get_base_strategy_scores(content_characteristics, available_strategies)

        # Apply complexity-based adjustments
        complexity_adj = calculate_complexity_adjustments(
            content_characteristics.complexity, scores
        )
        self._apply_score_adjustments(scores, complexity_adj)

        # Apply performance priority adjustments
        performance_adj = apply_performance_priority_adjustments(
            requirements.performance_priority, scores
        )
        self._apply_score_adjustments(scores, performance_adj)

        # Apply data integrity adjustments
        integrity_adj = apply_data_integrity_adjustments(requirements.min_data_preservation, scores)
        self._apply_score_adjustments(scores, integrity_adj)

        # Apply optimization target adjustments
        target_adj = apply_optimization_target_adjustments(requirements.optimization_target, scores)
        self._apply_score_adjustments(scores, target_adj)

        # Apply content size adjustments
        size_adj = apply_content_size_adjustments(
            content_characteristics.metrics.total_lines, scores
        )
        self._apply_score_adjustments(scores, size_adj)

        # Normalize and sort scores
        normalized_scores = normalize_and_sort_scores(scores)
        self.logger.debug(f"Strategy selection scores: {normalized_scores}")
        return normalized_scores

    def _get_base_strategy_scores(
        self,
        content_characteristics: ContentCharacteristics,
        available_strategies: dict[str, type[ContentFitter]],
    ) -> dict[str, float]:
        """Get base strategy scores based on content type."""
        preferences = create_content_type_preferences()

        # Select appropriate preferences based on content type
        if content_characteristics.content_type == ContentType.GIT_DIFF:
            base_scores = preferences.git_diff_preferences
        elif content_characteristics.content_type == ContentType.PYTHON_CODE:
            base_scores = preferences.python_code_preferences
        elif content_characteristics.content_type == ContentType.LOG_FILE:
            base_scores = preferences.log_file_preferences
        else:
            base_scores = preferences.plain_text_preferences  # Safe default

        # Only include available strategies
        scores = {}
        for strategy, score in base_scores.items():
            if self._strategy_available(strategy, available_strategies):
                scores[strategy] = score

        # Add fallback for empty scores
        if not scores:
            scores = {
                "overlapping": StrategyConfidence.GOOD,
                "adaptive": StrategyConfidence.ACCEPTABLE,
            }

        return scores

    def _apply_score_adjustments(
        self, scores: dict[str, float], adjustments: dict[str, float]
    ) -> None:
        """Apply adjustments to strategy scores in place."""
        for strategy, adjustment in adjustments.items():
            if strategy in scores:
                scores[strategy] = adjustment

    def _strategy_available(
        self, strategy_name: str, available_strategies: dict[str, type[ContentFitter]]
    ) -> bool:
        """Check if a strategy is available."""
        strategy_mapping = create_strategy_name_mapping()
        class_name = strategy_mapping.get(strategy_name, strategy_name)
        return any(cls.__name__ == class_name for cls in available_strategies.values())


class MLStrategySelector:
    """Machine learning-based strategy selector (placeholder for future ML integration)."""

    def __init__(self) -> None:
        self.logger = get_logger("MLStrategySelector")
        self.model_trained = False

    def select_strategy(
        self,
        content_characteristics: ContentCharacteristics,
        requirements: StrategyRequirements,
        available_strategies: dict[str, type[ContentFitter]],
    ) -> list[tuple[str, float]]:
        """Select strategies using ML model (placeholder implementation)."""

        # For now, fall back to heuristic selection
        # In the future, this would use a trained ML model
        self.logger.info("ML-based selection not yet implemented, falling back to heuristics")

        heuristic_selector = HeuristicStrategySelector()
        return heuristic_selector.select_strategy(
            content_characteristics, requirements, available_strategies
        )


@dataclass
class FactoryConfiguration:
    """Configuration for ContentFitterFactory."""

    # Core services
    content_analyzer: AdvancedContentAnalyzer
    strategy_selector: StrategySelector
    plugin_registry: PluginRegistry

    # Settings
    performance_tracking: bool = True

    # Statistics (consolidate related tracking data)
    statistics: dict[str, Union[int, list[SelectionRecord]]] = field(
        default_factory=lambda: {"creation_count": 0, "selection_history": []}
    )


@dataclass
class FactoryState:
    """Internal state for ContentFitterFactory."""

    # Performance metrics
    strategy_metrics: dict[str, StrategyPerformanceMetrics] = field(default_factory=dict)

    # Factory statistics
    creation_count: int = 0
    selection_history: list[SelectionRecord] = field(default_factory=list)


class ContentFitterFactory:
    """Intelligent factory for creating optimal content fitters."""

    def __init__(
        self,
        content_analyzer: Optional[AdvancedContentAnalyzer] = None,
        strategy_selector: Optional[StrategySelector] = None,
        plugin_registry: Optional[PluginRegistry] = None,
        performance_tracking: bool = True,
    ):
        """Initialize the content fitter factory.

        Args:
            content_analyzer: Content analyzer for understanding input
            strategy_selector: Algorithm for selecting optimal strategies
            plugin_registry: Registry for additional strategies
            performance_tracking: Enable performance metrics tracking
        """
        # Core services and configuration
        self.content_analyzer = content_analyzer or AdvancedContentAnalyzer()
        self.strategy_selector = strategy_selector or HeuristicStrategySelector()
        self.plugin_registry = plugin_registry or get_plugin_registry()
        self.performance_tracking = performance_tracking
        self.logger = get_logger("ContentFitterFactory")

        # Strategy registry
        self.built_in_strategies: dict[str, type[ContentFitter]] = {
            "OverlappingChunksFitter": OverlappingChunksFitter,
            "SemanticChunksFitter": SemanticChunksFitter,
            "AdaptiveChunksFitter": AdaptiveChunksFitter,
            "ParallelProcessingFitter": ParallelProcessingFitter,
            "FallbackChainFitter": FallbackChainFitter,
            "DiffTruncationFitter": DiffTruncationFitter,
            "LogCompressionFitter": LogCompressionFitter,
        }

        # Consolidated state management
        self._state = FactoryState()

    async def create_optimal_fitter(self, params: FitterCreationParams) -> ContentFitter:
        """Create the optimal content fitter for the given content and requirements.

        Args:
            params: Creation parameters containing all configuration options

        Returns:
            ContentFitter: Optimally configured content fitter
        """
        # Analyze content characteristics
        content_characteristics = self.content_analyzer.analyze(params.content)
        self.logger.info(
            f"Content analysis complete: {content_characteristics.content_type.value} "
            f"({content_characteristics.complexity.value})"
        )

        # Use default requirements if none provided
        requirements = params.requirements or StrategyRequirements()

        # Get available strategies (built-in + plugins)
        available_strategies = self._get_available_strategies()

        # Select optimal strategy
        strategy_rankings = self.strategy_selector.select_strategy(
            content_characteristics, requirements, available_strategies
        )

        if not strategy_rankings:
            raise StrategyError("No suitable strategies found for content")

        # Get the top strategy
        best_strategy_name, confidence = strategy_rankings[0]
        self.logger.info(f"Selected strategy: {best_strategy_name} (confidence: {confidence:.2f})")

        # Create the base fitter
        base_fitter = await self._create_strategy_fitter(
            best_strategy_name, params.config, params.token_counter
        )

        # Apply enhancements
        enhancement_params = EnhancementParams(
            base_fitter=base_fitter,
            config=params.config,
            token_counter=params.token_counter,
            enable_caching=params.enable_caching,
            enable_fallback=params.enable_fallback,
            strategy_rankings=strategy_rankings,
        )
        enhanced_fitter = await self._apply_enhancements(enhancement_params)

        # Record selection for analytics
        self._record_selection(
            content_characteristics, requirements, best_strategy_name, confidence
        )

        self._state.creation_count += 1
        return enhanced_fitter

    async def create_fitter_by_name(self, params: NamedFitterCreationParams) -> ContentFitter:
        """Create a specific fitter by strategy name.

        Args:
            params: Named fitter creation parameters

        Returns:
            ContentFitter: The requested fitter
        """
        base_fitter = await self._create_strategy_fitter(
            params.strategy_name, params.config, params.token_counter
        )

        # Apply enhancements if requested
        if params.enable_caching or params.enable_fallback:
            enhancement_params = EnhancementParams(
                base_fitter=base_fitter,
                config=params.config,
                token_counter=params.token_counter,
                enable_caching=params.enable_caching,
                enable_fallback=params.enable_fallback,
                strategy_rankings=[],
            )
            enhanced_fitter = await self._apply_enhancements(enhancement_params)
            return enhanced_fitter

        return base_fitter

    def _get_available_strategies(self) -> dict[str, type[ContentFitter]]:
        """Get all available strategies (built-in + plugins)."""
        strategies = self.built_in_strategies.copy()

        # Add plugin strategies (validated plugin classes are ContentFitter-compatible)
        plugin_strategies: dict[str, type[ContentFitter]] = {}
        for plugin_name, registration in self.plugin_registry.plugins.items():
            if (
                registration.core.status.value in {"loaded", "active"}
                and registration.core.instance
            ):
                # Plugin classes are validated to be ContentFitter-compatible during registration
                # Safe cast since plugin validation ensures ContentFitter compatibility
                plugin_strategies[plugin_name] = cast(
                    type[ContentFitter], registration.core.plugin_class
                )

        strategies.update(plugin_strategies)
        return strategies

    async def _create_strategy_fitter(
        self,
        strategy_name: str,
        config: PromptFittingConfig,
        token_counter: TokenCounter,
    ) -> ContentFitter:
        """Create a specific strategy fitter."""

        # Check built-in strategies first
        for class_name, strategy_class in self.built_in_strategies.items():
            if (
                class_name.lower().replace("fitter", "") in strategy_name.lower()
                or strategy_name in class_name.lower()
            ):
                fitter_instance: ContentFitter = strategy_class(config, token_counter)
                return fitter_instance

        # Check plugin strategies
        if strategy_name in self.plugin_registry.plugins:
            registration = self.plugin_registry.plugins[strategy_name]
            if registration.core.instance:
                plugin_fitter = registration.core.instance.create_fitter(config, token_counter)
                return plugin_fitter

        # Fallback to overlapping chunks if strategy not found
        self.logger.warning(
            f"Strategy '{strategy_name}' not found, falling back to OverlappingChunksFitter"
        )
        return OverlappingChunksFitter(config, token_counter)

    async def _apply_enhancements(self, params: EnhancementParams) -> ContentFitter:
        """Apply enhancements like caching and fallback to the base fitter."""
        fitter: ContentFitter = params.base_fitter

        if params.enable_caching:
            fitter = self._apply_caching_enhancement(params, fitter)

        if params.enable_fallback and len(params.strategy_rankings) > 1:
            fitter = self._apply_fallback_enhancement(params, fitter)

        return fitter

    def _apply_caching_enhancement(
        self, params: EnhancementParams, fitter: ContentFitter
    ) -> ContentFitter:
        """Apply caching enhancement to fitter."""
        cache_backend = MemoryCacheBackend(max_entries=FACTORY_CACHE_SIZE)
        cached_config = CachedContentFitterConfig(
            config=params.config,
            token_counter=params.token_counter,
            base_fitter=fitter,
            cache_backend=cache_backend,
            cache_ttl_hours=1.0,  # Keep as-is: reasonable cache duration
            enable_similarity_matching=True,
        )
        enhanced_fitter = CachedContentFitter(cached_config)
        self.logger.debug("Applied caching enhancement")
        return enhanced_fitter

    def _apply_fallback_enhancement(
        self, params: EnhancementParams, fitter: ContentFitter
    ) -> ContentFitter:
        """Apply fallback enhancement to fitter."""
        if fallback_strategies := self._create_fallback_strategies(params.strategy_rankings):
            enhanced_fitter = FallbackChainFitter(
                params.config, params.token_counter, fallback_strategies
            )
            self.logger.debug(f"Applied fallback chain with {len(fallback_strategies)} strategies")
            return enhanced_fitter

        return fitter

    def _create_fallback_strategies(
        self, strategy_rankings: list[tuple[str, float]]
    ) -> list[FallbackStrategy]:
        """Create fallback strategies from rankings."""
        fallback_strategies = []

        for strategy_name, confidence in strategy_rankings[:TOP_STRATEGIES_COUNT]:
            try:
                if strategy_class := self._find_strategy_class(strategy_name):
                    strategy_config = FallbackStrategyConfig(
                        fitter_class=strategy_class,
                        name=strategy_name,
                        priority=int(confidence * CONFIDENCE_MULTIPLIER_FOR_PRIORITY),
                        max_retries=MAX_FALLBACK_RETRIES,
                    )
                    fallback_strategy = FallbackStrategy(strategy_config)
                    fallback_strategies.append(fallback_strategy)

            except (TypeError, ValueError, AttributeError) as e:
                self.logger.warning(f"Failed to create fallback strategy {strategy_name}: {e}")

        return fallback_strategies

    def _find_strategy_class(self, strategy_name: str) -> Optional[type[ContentFitter]]:
        """Find strategy class by name."""
        for class_name, cls in self.built_in_strategies.items():
            if strategy_name.lower() in class_name.lower():
                return cls  # This is safe as built_in_strategies contains ContentFitter types
        return None

    def _record_selection(
        self,
        content_characteristics: ContentCharacteristics,
        requirements: StrategyRequirements,
        selected_strategy: str,
        confidence: float,
    ) -> None:
        """Record strategy selection for analytics."""

        selection_record: SelectionRecord = {
            "timestamp": time.time(),
            "content_type": content_characteristics.content_type.value,
            "complexity": content_characteristics.complexity.value,
            "content_size": content_characteristics.metrics.total_lines,
            "requirements": {
                "performance_priority": requirements.performance_priority.value,
                "optimization_target": requirements.optimization_target.value,
                "allow_experimental": requirements.allow_experimental,
            },
            "selected_strategy": selected_strategy,
            "confidence": confidence,
        }

        self._state.selection_history.append(selection_record)

        # Keep only last 1000 selections to prevent memory bloat
        if len(self._state.selection_history) > MAX_SELECTION_HISTORY_SIZE:
            self._state.selection_history = self._state.selection_history[
                -MAX_SELECTION_HISTORY_SIZE:
            ]

    def get_factory_stats(self) -> Union[FactoryStats, NoStatsMessage]:
        """Get comprehensive factory statistics."""

        if not self._state.selection_history:
            return {"message": "No selections recorded"}

        # Analyze selection patterns
        strategy_counts: dict[str, int] = {}
        content_type_counts: dict[str, int] = {}
        complexity_counts: dict[str, int] = {}

        for record in self._state.selection_history:
            strategy = record["selected_strategy"]
            content_type = record["content_type"]
            complexity = record["complexity"]

            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1

        # Calculate average confidence
        avg_confidence = sum(r["confidence"] for r in self._state.selection_history) / len(
            self._state.selection_history
        )

        return {
            "total_creations": self._state.creation_count,
            "selections_recorded": len(self._state.selection_history),
            "strategy_distribution": strategy_counts,
            "content_type_distribution": content_type_counts,
            "complexity_distribution": complexity_counts,
            "average_confidence": avg_confidence,
            "available_strategies": len(self._get_available_strategies()),
            "plugin_count": len(self.plugin_registry.plugins),
        }

    async def benchmark_strategies(
        self, test_content: list[str], config: PromptFittingConfig, token_counter: TokenCounter
    ) -> dict[str, StrategyPerformanceMetrics]:
        """Benchmark all available strategies on test content.

        Args:
            test_content: List of test content samples
            config: Configuration to use for testing
            token_counter: Token counter to use

        Returns:
            Performance metrics for each strategy
        """

        self.logger.info(f"Starting strategy benchmark with {len(test_content)} samples")

        available_strategies = self._get_available_strategies()
        results = {}

        for strategy_name, strategy_class in available_strategies.items():
            try:
                benchmark_params = BenchmarkParams(
                    strategy_name=strategy_name,
                    strategy_class=strategy_class,
                    test_content=test_content,
                    config=config,
                    token_counter=token_counter,
                )
                metrics = await self._benchmark_single_strategy(benchmark_params)
                results[strategy_name] = metrics
                self.logger.info(
                    f"Benchmarked {strategy_name}: {metrics.success_rate:.1f}% success rate"
                )

            except (TypeError, ValueError, AttributeError, RuntimeError) as e:
                self.logger.error(f"Benchmark failed for {strategy_name}: {e}")
                results[strategy_name] = StrategyPerformanceMetrics(
                    success_rate=0.0, last_updated=time.time()
                )

        # Update stored metrics
        self._state.strategy_metrics.update(results)

        self.logger.info(f"Strategy benchmark complete: {len(results)} strategies tested")
        return results

    async def _benchmark_single_strategy(
        self, params: BenchmarkParams
    ) -> StrategyPerformanceMetrics:
        """Benchmark a single strategy."""

        fitter = params.strategy_class(params.config, params.token_counter)

        processing_times = []
        compression_ratios = []
        data_preservation_scores = []
        successes = 0

        for content in params.test_content:
            try:
                start_time = time.time()
                result = await fitter.fit_content(content, STANDARD_TOKEN_TARGET)  # Standard target
                processing_time = time.time() - start_time

                processing_times.append(processing_time)
                compression_ratios.append(result.compression_ratio)
                data_preservation_scores.append(
                    REQUIRED_DATA_PRESERVATION_RATE if result.data_preserved else 0.0
                )
                successes += 1

            except (TypeError, ValueError, AttributeError, RuntimeError):
                processing_times.append(float("inf"))
                compression_ratios.append(1.0)
                data_preservation_scores.append(0.0)

        avg_compression_ratio = sum(compression_ratios) / len(compression_ratios)
        usage_count = len(params.test_content)

        return StrategyPerformanceMetrics(
            average_processing_time=sum(processing_times) / len(processing_times),
            success_rate=(successes / len(params.test_content)) * FULL_PERCENTAGE,
            data_preservation_rate=sum(data_preservation_scores) / len(data_preservation_scores),
            token_efficiency=sum(r for r in compression_ratios if r != float("inf"))
            / max(1, successes),
            compression_metrics={
                "average_ratio": avg_compression_ratio,
                "usage_count": usage_count,
            },
            last_updated=time.time(),
        )


class _FactorySingleton:
    """Singleton holder for ContentFitterFactory."""

    _instance: Optional[ContentFitterFactory] = None

    @classmethod
    def get_instance(cls) -> ContentFitterFactory:
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = ContentFitterFactory()
        return cls._instance


def get_content_fitter_factory() -> ContentFitterFactory:
    """Get the global content fitter factory instance."""
    return _FactorySingleton.get_instance()


async def create_optimal_fitter(
    content: str, config: PromptFittingConfig, token_counter: TokenCounter, **kwargs: Any
) -> ContentFitter:
    """Convenience function to create optimal fitter using global factory."""
    factory = get_content_fitter_factory()
    params = FitterCreationParams(
        content=content, config=config, token_counter=token_counter, **kwargs
    )
    return await factory.create_optimal_fitter(params)
