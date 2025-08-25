# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Fallback strategy chain system for robust prompt fitting.

This module implements a sophisticated fallback mechanism that tries multiple
fitting strategies in order of preference, ensuring that content can always
be fitted while maintaining data integrity.
"""

import asyncio
from dataclasses import dataclass
import time
from typing import Any, Callable, Generic, Optional

from .constants import BASE_BLACKLIST_DURATION_SECONDS
from .constants import CIRCUIT_BREAKER_FAILURE_THRESHOLD
from .constants import DEFAULT_STRATEGY_TIMEOUT
from .constants import DIFF_DETECTION_SAMPLE_LINES
from .constants import GIT_DIFF_ADD_PREFIX
from .constants import GIT_DIFF_CONTEXT_PREFIX
from .constants import GIT_DIFF_HEADER_PATTERN
from .constants import GIT_DIFF_HUNK_PATTERN
from .constants import GIT_DIFF_REMOVE_PREFIX
from .constants import MAX_BLACKLIST_DURATION_SECONDS
from .constants import MIN_LINES_FOR_OVERLAPPING_CHUNKS
from .constants import PRIMARY_STRATEGY_PRIORITY
from .constants import RETRY_BACKOFF_BASE_SECONDS
from .constants import SECONDARY_STRATEGY_PRIORITY
from .constants import SUCCESS_RATE_PERCENTAGE_MULTIPLIER
from .constants import TERTIARY_STRATEGY_PRIORITY
from .exceptions import PromptFittingError
from .exceptions import StrategyError
from .exceptions import TokenLimitErrorDetails
from .exceptions import TokenLimitExceededError
from .logging import get_logger
from .logging import OperationMetrics
from .prompt_fitting import ContentFitter
from .prompt_fitting import ContentFitterT
from .prompt_fitting import DiffTruncationFitter
from .prompt_fitting import FittingResult
from .prompt_fitting import LogCompressionFitter
from .prompt_fitting import OverlappingChunksFitter
from .prompt_fitting import PromptFittingConfig
from .prompt_fitting import TokenCounter


@dataclass
class StrategyAttempt(Generic[ContentFitterT]):
    """Record of a strategy attempt within the fallback chain."""

    strategy_name: str
    fitter_class: type
    success: bool
    error: Optional[Exception]
    result: Optional[FittingResult[ContentFitterT]]
    duration: float
    metadata: dict[str, Any]


@dataclass
class FallbackStrategyConfig:
    """Parameter class for FallbackStrategy initialization."""

    fitter_class: type[ContentFitter]
    name: str
    priority: int = 0
    condition: Optional[Callable[[str, int, PromptFittingConfig], bool]] = None
    max_retries: int = 1
    timeout_seconds: float = DEFAULT_STRATEGY_TIMEOUT


class FallbackStrategy:
    """Defines a fallback strategy with conditions and priority."""

    def __init__(self, config: FallbackStrategyConfig):
        """Initialize a fallback strategy.

        Args:
            config: FallbackStrategyConfig containing all initialization parameters
        """
        self.fitter_class = config.fitter_class
        self.name = config.name
        self.priority = config.priority
        self.condition = config.condition or (lambda *args: True)
        self.max_retries = config.max_retries
        self.timeout_seconds = config.timeout_seconds

    def applies_to(self, content: str, target_tokens: int, config: PromptFittingConfig) -> bool:
        """Check if this strategy applies to the given content and configuration."""
        try:
            return self.condition(content, target_tokens, config)
        except (TypeError, ValueError, AttributeError):
            return False

    async def create_fitter(
        self, config: PromptFittingConfig, token_counter: TokenCounter
    ) -> ContentFitter:
        """Create a fitter instance for this strategy."""
        return self.fitter_class(config, token_counter)


class FallbackChainFitter(ContentFitter):
    """Meta-fitter that tries multiple strategies in a fallback chain.

    This fitter implements a sophisticated fallback mechanism that:
    1. Tries strategies in priority order
    2. Handles failures gracefully
    3. Provides detailed logging and metrics
    4. Ensures data integrity across all attempts
    5. Implements circuit breaker patterns for failing strategies
    """

    def __init__(
        self,
        config: PromptFittingConfig,
        token_counter: TokenCounter,
        strategies: Optional[list[FallbackStrategy]] = None,
    ):
        """Initialize the fallback chain fitter.

        Args:
            config: Configuration for all strategies
            token_counter: Token counter for all strategies
            strategies: List of fallback strategies (uses defaults if None)
        """
        super().__init__(config, token_counter)
        self.strategies = strategies or self._create_default_strategies()
        self.logger = get_logger(f"{self.__class__.__name__}")

        # Circuit breaker state for strategies
        self.strategy_failures: dict[str, int] = {}
        self.strategy_blacklist: dict[str, float] = {}  # strategy -> blacklist_until_timestamp

        # Performance tracking
        self.attempts_history: list[StrategyAttempt[Any]] = []

    def _create_default_strategies(self) -> list[FallbackStrategy]:
        """Create the default fallback strategy chain."""
        return [
            # Primary strategy: OverlappingChunksFitter (fixed version)
            FallbackStrategy(
                FallbackStrategyConfig(
                    fitter_class=OverlappingChunksFitter,
                    name="overlapping_chunks",
                    priority=PRIMARY_STRATEGY_PRIORITY,
                    condition=lambda content, _tokens, _config: len(content.split("\n"))
                    >= MIN_LINES_FOR_OVERLAPPING_CHUNKS,
                )
            ),
            # Secondary: LogCompressionFitter for sequential content
            FallbackStrategy(
                FallbackStrategyConfig(
                    fitter_class=LogCompressionFitter,
                    name="temporal_log",
                    priority=SECONDARY_STRATEGY_PRIORITY,
                    condition=lambda _content, _tokens, _config: True,  # Always applicable
                )
            ),
            # Tertiary: StructuralDiffFitter for structured content
            FallbackStrategy(
                FallbackStrategyConfig(
                    fitter_class=DiffTruncationFitter,  # Actually StructuralDiffFitter behavior
                    name="structural_diff",
                    priority=TERTIARY_STRATEGY_PRIORITY,
                    condition=lambda content, _tokens, _config: (
                        self._detect_git_diff_content(content)
                    ),
                )
            ),
        ]

    async def fit_content(
        self, content: str, target_tokens: int
    ) -> FittingResult[ContentFitterT]:  # pyright: ignore[reportInvalidTypeVarUse]
        """Fit content using the fallback chain strategy.

        Tries strategies in priority order until one succeeds or all fail.
        Implements circuit breaker pattern and comprehensive error handling.
        """
        if not content.strip():
            raise PromptFittingError("Cannot fit empty content")

        # Filter and sort applicable strategies
        applicable_strategies = [
            strategy
            for strategy in self.strategies
            if strategy.applies_to(content, target_tokens, self.config)
            and not self._is_blacklisted(strategy.name)
        ]

        applicable_strategies.sort(key=lambda s: s.priority, reverse=True)

        if not applicable_strategies:
            raise PromptFittingError("No applicable strategies available for content")

        self.logger.info(
            f"Starting fallback chain with {len(applicable_strategies)} strategies",
            content_size=len(content),
            target_tokens=target_tokens,
            strategies=[s.name for s in applicable_strategies],
        )

        last_error = None
        all_attempts: list[StrategyAttempt[Any]] = []

        for strategy in applicable_strategies:
            strategy_start_time = time.time()
            try:
                async with self.logger.operation(
                    f"fallback_attempt_{strategy.name}",
                    content_size=len(content),
                    expected_tokens=target_tokens,
                    strategy=strategy.name,
                ) as metrics:

                    result: FittingResult[ContentFitterT] = await self._try_strategy(
                        strategy, content, target_tokens, metrics
                    )

                    # Success! Log and return
                    self.logger.info(
                        f"Strategy succeeded: {strategy.name}",
                        duration=f"{metrics.duration:.3f}s",
                        data_preserved=result.data_preserved,
                        compression_ratio=f"{result.compression_ratio:.2f}",
                    )

                    # Reset failure count on success
                    self.strategy_failures.pop(strategy.name, None)

                    # Enhance result with fallback metadata
                    result.metadata.update(
                        {
                            "fallback_attempts": len(all_attempts) + 1,
                            "successful_strategy": strategy.name,
                            "strategies_tried": [attempt.strategy_name for attempt in all_attempts]
                            + [strategy.name],
                        }
                    )

                    return result

            except PromptFittingError as error:
                # Strategy failed, log and continue
                attempt: StrategyAttempt[Any] = StrategyAttempt(
                    strategy_name=strategy.name,
                    fitter_class=strategy.fitter_class,
                    success=False,
                    error=error,
                    result=None,
                    duration=time.time() - strategy_start_time,
                    metadata={"target_tokens": target_tokens, "content_size": len(content)},
                )

                all_attempts.append(attempt)
                self.attempts_history.append(attempt)

                # Update failure tracking
                self._record_strategy_failure(strategy.name)

                self.logger.warning(
                    f"Strategy failed: {strategy.name}",
                    error=str(error),
                    error_type=type(error).__name__,
                )

                last_error = error
                continue

        # All strategies failed
        self.logger.critical(
            "All fallback strategies failed",
            strategies_attempted=len(all_attempts),
            last_error=str(last_error) if last_error else "Unknown",
        )

        # Create comprehensive error with all attempt information
        attempt_info = [
            f"{attempt.strategy_name}: "
            f"{type(attempt.error).__name__ if attempt.error else 'Unknown'}"
            for attempt in all_attempts
        ]

        raise TokenLimitExceededError(
            TokenLimitErrorDetails(
                message=f"All {len(all_attempts)} fallback strategies failed",
                actual_tokens=await self.token_counter.count_tokens(content),
                target_tokens=target_tokens,
                strategies_attempted=[attempt.strategy_name for attempt in all_attempts],
                context={
                    "attempts": attempt_info,
                    "last_error": str(last_error) if last_error else None,
                },
            )
        )

    async def _try_strategy(
        self,
        strategy: FallbackStrategy,
        content: str,
        target_tokens: int,
        metrics: OperationMetrics,
    ) -> FittingResult[ContentFitterT]:  # pyright: ignore[reportInvalidTypeVarUse]
        """Try a single strategy with timeout and retry logic."""
        fitter = await strategy.create_fitter(self.config, self.token_counter)

        for attempt in range(strategy.max_retries + 1):
            try:
                # Apply timeout to the strategy attempt
                result = await asyncio.wait_for(
                    fitter.fit_content(content, target_tokens), timeout=strategy.timeout_seconds
                )

                # Validate the result
                if not self._validate_result(result):
                    raise StrategyError(
                        f"Strategy {strategy.name} produced invalid result",
                        strategy_name=strategy.name,
                    )

                metrics.processing_stats.strategy_used = strategy.name
                metrics.processing_stats.tokens_processed = result.fitted_size
                return result

            except asyncio.TimeoutError as exc:
                error_msg = f"Strategy {strategy.name} timed out after {strategy.timeout_seconds}s"
                if attempt < strategy.max_retries:
                    self.logger.warning(f"{error_msg}, retrying...")
                    continue
                raise StrategyError(error_msg, strategy_name=strategy.name) from exc

            except Exception as error:
                if attempt < strategy.max_retries:
                    self.logger.warning(
                        f"Strategy {strategy.name} failed (attempt {attempt + 1}), retrying...",
                        error=str(error),
                    )
                    await asyncio.sleep(
                        RETRY_BACKOFF_BASE_SECONDS * (attempt + 1)
                    )  # Exponential backoff
                    continue
                raise StrategyError(
                    f"Strategy {strategy.name} failed after {attempt + 1} attempts: {error}",
                    strategy_name=strategy.name,
                    original_error=error,
                ) from error

        # This should never be reached, but satisfy mypy
        raise StrategyError(
            f"Unexpected exit from strategy {strategy.name}", strategy_name=strategy.name
        )

    def _validate_result(self, result: FittingResult[ContentFitterT]) -> bool:
        """Validate that a strategy result meets quality requirements."""
        # Must preserve data (project requirement)
        if not result.data_preserved:
            return False

        # Must have reasonable token counts
        if result.original_size <= 0 or result.fitted_size <= 0:
            return False

        # Must have content
        if not result.fitted_content.strip():
            return False

        # Additional quality checks could go here
        return True

    def _record_strategy_failure(self, strategy_name: str) -> None:
        """Record a strategy failure and implement circuit breaker logic."""
        # Increment failure count
        self.strategy_failures[strategy_name] = self.strategy_failures.get(strategy_name, 0) + 1

        # Implement circuit breaker: blacklist after too many failures
        if (
            failure_count := self.strategy_failures[strategy_name]
        ) >= CIRCUIT_BREAKER_FAILURE_THRESHOLD:  # Blacklist after consecutive failures
            blacklist_duration = min(
                MAX_BLACKLIST_DURATION_SECONDS, BASE_BLACKLIST_DURATION_SECONDS * failure_count
            )  # Max blacklist duration
            self.strategy_blacklist[strategy_name] = time.time() + blacklist_duration

            self.logger.warning(
                f"Strategy {strategy_name} blacklisted for {blacklist_duration}s "
                f"after {failure_count} failures"
            )

    def _is_blacklisted(self, strategy_name: str) -> bool:
        """Check if a strategy is currently blacklisted."""
        if strategy_name not in self.strategy_blacklist:
            return False

        blacklist_until = self.strategy_blacklist[strategy_name]
        if time.time() >= blacklist_until:
            # Blacklist expired, remove it
            del self.strategy_blacklist[strategy_name]
            self.strategy_failures.pop(strategy_name, None)  # Reset failure count
            return False

        return True

    def validate_preservation(self, original: str, fitted: str) -> bool:
        """Delegate validation to the successful strategy."""
        # This is called by the base class, but for fallback chain,
        # validation is handled per-strategy during execution
        return True  # Validation already performed in _validate_result

    def _detect_git_diff_content(self, content: str) -> bool:
        """Detect if content appears to be a Git diff."""
        return (
            GIT_DIFF_HEADER_PATTERN in content
            or GIT_DIFF_HUNK_PATTERN in content
            or any(
                line.startswith(
                    (GIT_DIFF_ADD_PREFIX, GIT_DIFF_REMOVE_PREFIX, GIT_DIFF_CONTEXT_PREFIX)
                )
                for line in content.split("\n")[:DIFF_DETECTION_SAMPLE_LINES]
            )
        )

    def get_strategy_stats(self) -> dict[str, Any]:
        """Get comprehensive statistics about strategy performance."""
        if not self.attempts_history:
            return {"message": "No attempts recorded"}

        stats = {}
        for strategy_name in set(attempt.strategy_name for attempt in self.attempts_history):
            strategy_attempts = [
                a for a in self.attempts_history if a.strategy_name == strategy_name
            ]
            successful = [a for a in strategy_attempts if a.success]
            failed = [a for a in strategy_attempts if not a.success]

            stats[strategy_name] = {
                "total_attempts": len(strategy_attempts),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful)
                / len(strategy_attempts)
                * SUCCESS_RATE_PERCENTAGE_MULTIPLIER,
                "average_duration": sum(a.duration for a in strategy_attempts)
                / len(strategy_attempts),
                "is_blacklisted": self._is_blacklisted(strategy_name),
                "failure_count": self.strategy_failures.get(strategy_name, 0),
            }

        return stats
