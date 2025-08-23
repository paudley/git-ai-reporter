# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Strategy selection utilities for complex heuristic-based selection logic.

This module provides utilities to break down complex strategy selection
into focused, testable helper functions.
"""

from dataclasses import dataclass
from typing import Union

from ..constants import ADAPTIVE_BOOST
from ..constants import CACHING_BOOST
from ..constants import CACHING_LARGE_CONTENT_BOOST
from ..constants import EXPERIMENTAL_PENALTY
from ..constants import FALLBACK_BOOST
from ..constants import LARGE_CONTENT_BOOST
from ..constants import LARGE_CONTENT_THRESHOLD
from ..constants import OVERLAPPING_BOOST
from ..constants import PARALLEL_BOOST
from ..constants import PARALLEL_SMALL_CONTENT_PENALTY
from ..constants import PERFECT_DATA_PRESERVATION_BOOST
from ..constants import PERFORMANCE_BOOST
from ..constants import PERFORMANCE_PRIORITY
from ..constants import QUALITY_PRIORITY
from ..constants import REQUIRED_DATA_PRESERVATION_RATE
from ..constants import SEMANTIC_BOOST
from ..constants import SMALL_CONTENT_OVERLAPPING_BOOST
from ..constants import SMALL_CONTENT_THRESHOLD
from ..constants import STRATEGY_NAME_ADAPTIVE
from ..constants import STRATEGY_NAME_CACHED
from ..constants import STRATEGY_NAME_DIFF_TRUNCATION
from ..constants import STRATEGY_NAME_EXPERIMENTAL
from ..constants import STRATEGY_NAME_FALLBACK
from ..constants import STRATEGY_NAME_LOG_COMPRESSION
from ..constants import STRATEGY_NAME_OVERLAPPING
from ..constants import STRATEGY_NAME_PARALLEL
from ..constants import STRATEGY_NAME_SEMANTIC
from ..constants import StrategyConfidence

# TYPE_CHECKING imports removed to prevent cyclic imports
# All type annotations use Union[str, object] instead of specific enums


@dataclass
class StrategyScoreAdjustment:
    """Parameters for strategy score adjustments."""

    strategy_name: str
    adjustment: float
    reason: str


@dataclass
class ContentTypePreferences:
    """Content type strategy preferences mapping."""

    git_diff_preferences: dict[str, float]
    python_code_preferences: dict[str, float]
    log_file_preferences: dict[str, float]
    plain_text_preferences: dict[str, float]


def create_content_type_preferences() -> ContentTypePreferences:
    """Create standardized content type preferences.

    Returns:
        ContentTypePreferences with all strategy mappings
    """
    return ContentTypePreferences(
        git_diff_preferences={
            STRATEGY_NAME_ADAPTIVE: StrategyConfidence.HIGH,
            STRATEGY_NAME_SEMANTIC: StrategyConfidence.GOOD,
            STRATEGY_NAME_DIFF_TRUNCATION: StrategyConfidence.VERY_HIGH,  # Specialized for diffs
            STRATEGY_NAME_OVERLAPPING: StrategyConfidence.ACCEPTABLE,
            STRATEGY_NAME_PARALLEL: StrategyConfidence.FAIR,
        },
        python_code_preferences={
            STRATEGY_NAME_SEMANTIC: StrategyConfidence.VERY_HIGH,  # Excellent for structured code
            STRATEGY_NAME_ADAPTIVE: StrategyConfidence.HIGH,
            STRATEGY_NAME_OVERLAPPING: StrategyConfidence.ACCEPTABLE,
            STRATEGY_NAME_PARALLEL: StrategyConfidence.GOOD,
            STRATEGY_NAME_CACHED: StrategyConfidence.GOOD,
        },
        log_file_preferences={
            STRATEGY_NAME_LOG_COMPRESSION: StrategyConfidence.VERY_HIGH,  # Specialized for logs
            STRATEGY_NAME_OVERLAPPING: StrategyConfidence.GOOD,
            STRATEGY_NAME_PARALLEL: StrategyConfidence.GOOD,
            STRATEGY_NAME_CACHED: StrategyConfidence.ACCEPTABLE,
            STRATEGY_NAME_ADAPTIVE: StrategyConfidence.FAIR,
        },
        plain_text_preferences={
            STRATEGY_NAME_OVERLAPPING: StrategyConfidence.HIGH,
            STRATEGY_NAME_ADAPTIVE: StrategyConfidence.GOOD,
            STRATEGY_NAME_SEMANTIC: StrategyConfidence.FAIR,
            STRATEGY_NAME_PARALLEL: StrategyConfidence.ACCEPTABLE,
        },  # Safe default
    )


def calculate_complexity_adjustments(
    complexity_level: Union[str, object], base_scores: dict[str, float]
) -> dict[str, float]:
    """Calculate complexity-based strategy adjustments.

    Args:
        complexity_level: Content complexity level (enum or string)
        base_scores: Current strategy scores

    Returns:
        Dictionary of strategy adjustments
    """
    # Use string-based complexity mapping to avoid circular imports
    complexity_name = (
        str(complexity_level).rsplit(".", maxsplit=1)[-1]
        if hasattr(complexity_level, "value")
        else str(complexity_level)
    )

    complexity_adjustments = {
        "SIMPLE": {
            STRATEGY_NAME_OVERLAPPING: OVERLAPPING_BOOST,
            STRATEGY_NAME_SEMANTIC: -OVERLAPPING_BOOST,
        },
        "MODERATE": {STRATEGY_NAME_ADAPTIVE: OVERLAPPING_BOOST},
        "COMPLEX": {
            STRATEGY_NAME_SEMANTIC: FALLBACK_BOOST,
            STRATEGY_NAME_ADAPTIVE: OVERLAPPING_BOOST,
        },
        "HIGHLY_COMPLEX": {
            STRATEGY_NAME_SEMANTIC: PARALLEL_BOOST,
            STRATEGY_NAME_FALLBACK: FALLBACK_BOOST,
        },
    }

    adjustments = complexity_adjustments.get(complexity_name.upper(), {})
    applied_adjustments = {}

    for strategy, adjustment in adjustments.items():
        if strategy in base_scores:
            applied_adjustments[strategy] = adjustment

    return applied_adjustments


def apply_performance_priority_adjustments(
    performance_priority: Union[str, object], base_scores: dict[str, float]
) -> dict[str, float]:
    """Apply performance priority adjustments to strategy scores.

    Args:
        performance_priority: Performance priority level
        base_scores: Current strategy scores

    Returns:
        Dictionary of strategy adjustments
    """
    # Use string-based priority mapping to avoid circular imports
    priority_name = (
        str(performance_priority).rsplit(".", maxsplit=1)[-1]
        if hasattr(performance_priority, "value")
        else str(performance_priority)
    )
    adjustments = {}

    if priority_name.upper() == PERFORMANCE_PRIORITY:
        adjustments[STRATEGY_NAME_PARALLEL] = (
            base_scores.get(STRATEGY_NAME_PARALLEL, StrategyConfidence.DEFAULT) + PARALLEL_BOOST
        )
        adjustments[STRATEGY_NAME_CACHED] = (
            base_scores.get(STRATEGY_NAME_CACHED, StrategyConfidence.DEFAULT) + CACHING_BOOST
        )
        adjustments[STRATEGY_NAME_OVERLAPPING] = (
            base_scores.get(STRATEGY_NAME_OVERLAPPING, StrategyConfidence.DEFAULT)
            + OVERLAPPING_BOOST
        )

    elif priority_name.upper() == QUALITY_PRIORITY:
        adjustments[STRATEGY_NAME_SEMANTIC] = (
            base_scores.get(STRATEGY_NAME_SEMANTIC, StrategyConfidence.DEFAULT) + SEMANTIC_BOOST
        )
        adjustments[STRATEGY_NAME_ADAPTIVE] = (
            base_scores.get(STRATEGY_NAME_ADAPTIVE, StrategyConfidence.DEFAULT) + ADAPTIVE_BOOST
        )
        adjustments[STRATEGY_NAME_FALLBACK] = (
            base_scores.get(STRATEGY_NAME_FALLBACK, StrategyConfidence.DEFAULT) + FALLBACK_BOOST
        )

    return adjustments


def apply_data_integrity_adjustments(
    min_data_preservation: float, base_scores: dict[str, float]
) -> dict[str, float]:
    """Apply data integrity requirement adjustments.

    Args:
        min_data_preservation: Minimum data preservation requirement
        base_scores: Current strategy scores

    Returns:
        Dictionary of strategy adjustments
    """
    adjustments = {}

    if min_data_preservation >= REQUIRED_DATA_PRESERVATION_RATE:
        # Boost strategies known for perfect data preservation
        safe_strategies = (
            STRATEGY_NAME_SEMANTIC,
            STRATEGY_NAME_ADAPTIVE,
            STRATEGY_NAME_OVERLAPPING,
            STRATEGY_NAME_FALLBACK,
        )
        for strategy in safe_strategies:
            if strategy in base_scores:
                adjustments[strategy] = (
                    base_scores.get(strategy, 0.0) + PERFECT_DATA_PRESERVATION_BOOST
                )

        # Penalize any strategy that might not preserve data
        risky_strategies = (STRATEGY_NAME_EXPERIMENTAL,)
        for strategy in risky_strategies:
            if strategy in base_scores:
                adjustments[strategy] = base_scores.get(strategy, 0.0) - EXPERIMENTAL_PENALTY

    return adjustments


def apply_optimization_target_adjustments(
    optimization_target: Union[str, object], base_scores: dict[str, float]
) -> dict[str, float]:
    """Apply optimization target adjustments to strategy scores.

    Args:
        optimization_target: Target optimization goal
        base_scores: Current strategy scores

    Returns:
        Dictionary of strategy adjustments
    """
    # Use string-based target mapping to avoid circular imports
    target_name = (
        str(optimization_target).rsplit(".", maxsplit=1)[-1]
        if hasattr(optimization_target, "value")
        else str(optimization_target)
    )

    target_adjustments = {
        "SPEED": {
            STRATEGY_NAME_PARALLEL: PERFORMANCE_BOOST + OVERLAPPING_BOOST,
            STRATEGY_NAME_CACHED: CACHING_BOOST,
            STRATEGY_NAME_OVERLAPPING: OVERLAPPING_BOOST,
        },
        "MEMORY": {
            STRATEGY_NAME_OVERLAPPING: PARALLEL_BOOST,
            STRATEGY_NAME_SEMANTIC: -OVERLAPPING_BOOST,
            STRATEGY_NAME_PARALLEL: -PARALLEL_BOOST,
        },
        "ACCURACY": {
            STRATEGY_NAME_SEMANTIC: SEMANTIC_BOOST,
            STRATEGY_NAME_ADAPTIVE: PARALLEL_BOOST,
            STRATEGY_NAME_FALLBACK: FALLBACK_BOOST,
        },
        "COMPRESSION_RATIO": {
            STRATEGY_NAME_ADAPTIVE: PERFORMANCE_BOOST + OVERLAPPING_BOOST,
            STRATEGY_NAME_SEMANTIC: PARALLEL_BOOST,
        },
        "TOKEN_EFFICIENCY": {
            STRATEGY_NAME_SEMANTIC: PARALLEL_BOOST,
            STRATEGY_NAME_ADAPTIVE: SEMANTIC_BOOST,
        },
    }

    target_adj = target_adjustments.get(target_name.upper(), {})
    applied_adjustments = {}

    for strategy, adjustment in target_adj.items():
        if strategy in base_scores:
            applied_adjustments[strategy] = base_scores.get(strategy, 0.0) + adjustment

    return applied_adjustments


def apply_content_size_adjustments(
    total_lines: int, base_scores: dict[str, float]
) -> dict[str, float]:
    """Apply content size-based adjustments to strategy scores.

    Args:
        total_lines: Total number of lines in content
        base_scores: Current strategy scores

    Returns:
        Dictionary of strategy adjustments
    """
    adjustments = {}

    if total_lines > LARGE_CONTENT_THRESHOLD:
        adjustments[STRATEGY_NAME_PARALLEL] = (
            base_scores.get(STRATEGY_NAME_PARALLEL, StrategyConfidence.DEFAULT)
            + LARGE_CONTENT_BOOST
        )
        adjustments[STRATEGY_NAME_CACHED] = (
            base_scores.get(STRATEGY_NAME_CACHED, StrategyConfidence.DEFAULT)
            + CACHING_LARGE_CONTENT_BOOST
        )

    if total_lines < SMALL_CONTENT_THRESHOLD:
        adjustments[STRATEGY_NAME_OVERLAPPING] = (
            base_scores.get(STRATEGY_NAME_OVERLAPPING, StrategyConfidence.DEFAULT)
            + SMALL_CONTENT_OVERLAPPING_BOOST
        )
        adjustments[STRATEGY_NAME_PARALLEL] = (
            base_scores.get(STRATEGY_NAME_PARALLEL, StrategyConfidence.DEFAULT)
            - PARALLEL_SMALL_CONTENT_PENALTY
        )

    return adjustments


def normalize_and_sort_scores(scores: dict[str, float]) -> list[tuple[str, float]]:
    """Normalize strategy scores and sort by confidence.

    Args:
        scores: Dictionary of strategy scores

    Returns:
        List of (strategy_name, normalized_score) tuples sorted by score
    """
    if not scores:
        return []

    if (max_score := max(scores.values())) <= 0:
        max_score = StrategyConfidence.DEFAULT * 2

    normalized_scores = [(name, score / max_score) for name, score in scores.items()]
    normalized_scores.sort(key=lambda x: x[1], reverse=True)

    return normalized_scores


def create_strategy_name_mapping() -> dict[str, str]:
    """Create mapping from strategy names to class names.

    Returns:
        Dictionary mapping strategy names to class names
    """
    return {
        STRATEGY_NAME_OVERLAPPING: "OverlappingChunksFitter",
        STRATEGY_NAME_SEMANTIC: "SemanticChunksFitter",
        STRATEGY_NAME_ADAPTIVE: "AdaptiveChunksFitter",
        STRATEGY_NAME_PARALLEL: "ParallelProcessingFitter",
        STRATEGY_NAME_CACHED: "CachedContentFitter",
        STRATEGY_NAME_FALLBACK: "FallbackChainFitter",
        STRATEGY_NAME_DIFF_TRUNCATION: "DiffTruncationFitter",
        STRATEGY_NAME_LOG_COMPRESSION: "LogCompressionFitter",
    }
