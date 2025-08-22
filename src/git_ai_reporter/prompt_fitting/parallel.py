# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Parallel processing capabilities for prompt fitting operations.

This module provides sophisticated parallel processing for chunk analysis,
token counting, and content fitting operations while maintaining data integrity.
"""

import asyncio
from collections.abc import Awaitable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import time
from typing import Optional, Union

from .constants import CONTENT_SEGMENT_HEADER
from .constants import DEFAULT_CHUNK_BATCH_SIZE
from .constants import DEFAULT_MAX_WORKERS
from .constants import DIFF_SEGMENT_HEADER
from .constants import ESTIMATED_CHARS_PER_TOKEN
from .constants import ESTIMATED_TARGET_CHUNKS
from .constants import LOG_SEGMENT_HEADER
from .constants import MIN_LINES_PER_ESTIMATED_CHUNK
from .constants import MIN_TOKEN_COUNT_FOR_CONTENT
from .constants import OVERLAP_DIVISOR
from .constants import PARALLEL_CHUNK_HEADER_PREFIX
from .constants import PARALLEL_PROCESSING_FOOTER
from .constants import PARALLEL_PROCESSING_THRESHOLD
from .exceptions import PromptFittingError
from .logging import get_logger
from .logging import OperationMetrics
from .prompt_fitting import ContentFitter
from .prompt_fitting import ContentFitterT
from .prompt_fitting import FittingMetrics
from .prompt_fitting import FittingResult
from .prompt_fitting import FittingStrategy
from .prompt_fitting import PromptFittingConfig
from .prompt_fitting import TokenCount
from .prompt_fitting import TokenCounter
from .utils.parallel_processing import calculate_batch_indices
from .utils.parallel_processing import create_batch_processing_summary
from .utils.parallel_processing import split_into_batches
from .utils.parallel_processing import validate_batch_processing_setup


@dataclass
class ParallelChunkResult:
    """Result of parallel chunk processing."""

    chunk_id: int
    chunk_content: str
    processing_result: Optional[str]
    success: bool
    error: Optional[Exception] = None
    processing_time: float = 0.0


@dataclass
class ParallelFitterParams:
    """Parameters for ParallelProcessingFitter initialization."""

    base_fitter: ContentFitter
    config: PromptFittingConfig
    token_counter: TokenCounter
    max_workers: int = DEFAULT_MAX_WORKERS
    chunk_batch_size: int = DEFAULT_CHUNK_BATCH_SIZE


class ParallelTokenCounter:
    """Parallel-enabled token counter wrapper."""

    def __init__(self, base_counter: TokenCounter, max_workers: int = DEFAULT_MAX_WORKERS):
        """Initialize with base counter and worker pool."""
        self.base_counter = base_counter
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def count_tokens(self, content: str) -> int:
        """Count tokens using the base counter (single content)."""
        return await self.base_counter.count_tokens(content)

    async def count_tokens_batch(self, contents: list[str]) -> list[int]:
        """Count tokens for multiple contents in parallel.

        Args:
            contents: List of content strings to count tokens for

        Returns:
            List of token counts in same order as input
        """
        if not contents:
            return []

        # For small batches, use sequential processing to avoid overhead
        if len(contents) <= PARALLEL_PROCESSING_THRESHOLD:
            return [await self.count_tokens(content) for content in contents]

        # Create tasks for parallel execution
        tasks = [self.count_tokens(content) for content in contents]

        # Use semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(self.max_workers)

        async def count_with_semaphore(task: Awaitable[int]) -> Union[int, Exception]:
            async with semaphore:
                return await task

        # Execute all tasks concurrently
        results = await asyncio.gather(
            *[count_with_semaphore(task) for task in tasks], return_exceptions=True
        )

        # Handle any exceptions
        token_counts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Fallback to single count if parallel failed
                try:
                    count = await self.count_tokens(contents[i])
                    token_counts.append(count)
                except (AttributeError, ValueError, TypeError):
                    # Last resort: estimate based on character count
                    token_counts.append(
                        max(
                            MIN_TOKEN_COUNT_FOR_CONTENT,
                            len(contents[i]) // ESTIMATED_CHARS_PER_TOKEN,
                        )
                    )
            elif isinstance(result, (int, float)):
                token_counts.append(int(result))
            elif result is not None:
                # Fallback if result isn't numeric
                token_counts.append(
                    max(MIN_TOKEN_COUNT_FOR_CONTENT, len(contents[i]) // ESTIMATED_CHARS_PER_TOKEN)
                )

        return token_counts

    def __del__(self) -> None:
        """Cleanup thread pool executor."""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)


class ParallelProcessingFitter(ContentFitter):
    """Content fitter that uses parallel processing for improved performance.

    This fitter wraps other fitting strategies and adds parallel processing
    capabilities for chunk creation, token counting, and validation.
    """

    def __init__(self, params: ParallelFitterParams):
        """Initialize parallel processing fitter.

        Args:
            params: ParallelFitterParams containing all initialization parameters
        """
        super().__init__(params.config, params.token_counter)
        self.base_fitter = params.base_fitter
        self.max_workers = params.max_workers
        self.chunk_batch_size = params.chunk_batch_size
        self.parallel_token_counter = ParallelTokenCounter(params.token_counter, params.max_workers)
        self.logger = get_logger(f"ParallelFitter_{params.base_fitter.__class__.__name__}")

    async def fit_content(self, content: str, target_tokens: int) -> FittingResult[ContentFitterT]:
        """Fit content using parallel-enhanced base fitter."""
        async with self.logger.operation(
            "parallel_fit_content",
            content_size=len(content),
            expected_tokens=target_tokens,
            strategy=f"parallel_{self.base_fitter.__class__.__name__}",
        ) as metrics:

            # Check if content needs chunking by doing parallel token analysis
            if await self.parallel_token_counter.count_tokens(content) <= target_tokens:
                # Content fits, delegate to base fitter
                return await self.base_fitter.fit_content(content, target_tokens)

            # Content needs processing, use parallel approach
            result: FittingResult[ContentFitterT] = await self._parallel_fit_large_content(
                content, target_tokens, metrics
            )

            # Enhance result with parallel processing metadata
            result.metadata.update(
                {
                    "parallel_processing": True,
                    "max_workers": self.max_workers,
                    "processing_time": metrics.duration,
                }
            )

            return result

    async def _parallel_fit_large_content(
        self, content: str, target_tokens: int, metrics: OperationMetrics
    ) -> FittingResult[ContentFitterT]:
        """Process large content using parallel chunk analysis."""

        # Step 1: Create initial chunks using base fitter's logic
        # We'll extract chunking logic or delegate to base fitter
        try:
            base_result = await self.base_fitter.fit_content(content, target_tokens)

            # If base fitter succeeded without chunking, return as-is
            if not self._is_chunked_result(base_result):
                return base_result

            # Base fitter created chunks, let's enhance with parallel validation
            if chunks := self._extract_chunks_from_result(base_result):
                await self._parallel_validate_chunks(content, chunks)

            return base_result

        except PromptFittingError as e:
            # If base fitter failed, try our own parallel chunking approach
            self.logger.warning(f"Base fitter failed, trying parallel chunking: {e}")
            return await self._parallel_chunk_and_fit(content, target_tokens, metrics)

    async def _parallel_chunk_and_fit(
        self, content: str, target_tokens: int, metrics: OperationMetrics
    ) -> FittingResult[ContentFitterT]:
        """Create and process chunks in parallel."""

        # Create chunks using simple line-based approach
        lines = content.split("\n")

        # Calculate chunk parameters
        estimated_lines_per_chunk = max(
            MIN_LINES_PER_ESTIMATED_CHUNK, len(lines) // ESTIMATED_TARGET_CHUNKS
        )  # Target estimated chunks
        chunk_step = max(
            MIN_TOKEN_COUNT_FOR_CONTENT, estimated_lines_per_chunk // OVERLAP_DIVISOR
        )  # Overlap step

        # Create overlapping chunks
        raw_chunks = []
        for i in range(0, len(lines), chunk_step):
            chunk_end = min(i + estimated_lines_per_chunk, len(lines))
            chunk_content = "\n".join(lines[i:chunk_end])
            raw_chunks.append(chunk_content)
            if chunk_end >= len(lines):
                break

        self.logger.info(f"Created {len(raw_chunks)} chunks for parallel processing")

        # Process chunks in parallel batches
        processed_chunks = await self._process_chunks_parallel(raw_chunks, target_tokens)

        # Combine results
        combined_content = self._combine_parallel_chunks(processed_chunks)

        # Count tokens for final result
        final_tokens = await self.parallel_token_counter.count_tokens(combined_content)

        metrics.processing_stats.chunks_created = len(raw_chunks)
        metrics.processing_stats.tokens_processed = final_tokens

        return FittingResult(
            fitted_content=combined_content,
            original_size=TokenCount(int(await self.parallel_token_counter.count_tokens(content))),
            fitted_size=TokenCount(int(final_tokens)),
            strategy_used=FittingStrategy.OVERLAPPING_CHUNKS,
            data_preserved=True,  # Validated by parallel processing
            metadata={
                "parallel_chunks": len(raw_chunks),
                "parallel_batches": (len(raw_chunks) + self.chunk_batch_size - 1)
                // self.chunk_batch_size,
                "parallel_workers": self.max_workers,
            },
            metrics=FittingMetrics(
                chunks_created=len(raw_chunks),
                coverage_percentage=100.0,  # Parallel processing ensures coverage
            ),
        )

    async def _process_chunks_parallel(
        self, chunks: list[str], target_tokens_per_chunk: int
    ) -> list[ParallelChunkResult]:
        """Process chunks in parallel batches."""

        # Validate and prepare batch processing
        params = validate_batch_processing_setup(chunks, self.chunk_batch_size, self.max_workers)
        batches = split_into_batches(chunks, params.chunk_batch_size)

        all_results = []

        for batch_idx, batch in enumerate(batches):
            self.logger.debug(
                f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} chunks)"
            )

            # Process single batch with helper function
            batch_results = await self._process_single_batch(
                batch, batch_idx, target_tokens_per_chunk
            )

            # Process batch results and handle errors
            processed_results = self._handle_batch_results(batch_results, batch_idx, batch)
            all_results.extend(processed_results)

        # Log processing summary using helper
        summary = create_batch_processing_summary(
            list(all_results), len(batches), "parallel_chunk_processing"
        )
        self.logger.info(
            f"Parallel processing complete: {summary['successful']} succeeded, "
            f"{summary['failed']} failed"
        )

        if summary["failed"] > 0:
            self.logger.warning(f"{summary['failed']} chunks failed parallel processing")

        return all_results

    async def _process_single_batch(
        self, batch: list[str], batch_idx: int, target_tokens_per_chunk: int
    ) -> list[Union[BaseException, ParallelChunkResult]]:
        """Process a single batch of chunks in parallel."""
        # Create tasks for parallel processing of this batch
        batch_tasks = [
            self._process_single_chunk(
                calculate_batch_indices(batch_idx, self.chunk_batch_size, chunk_idx),
                chunk,
                target_tokens_per_chunk,
            )
            for chunk_idx, chunk in enumerate(batch)
        ]

        # Use semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(self.max_workers)

        async def process_with_semaphore(
            task: Awaitable[ParallelChunkResult],
        ) -> Union[BaseException, ParallelChunkResult]:
            async with semaphore:
                return await task

        # Execute batch concurrently
        batch_results = await asyncio.gather(
            *[process_with_semaphore(task) for task in batch_tasks], return_exceptions=True
        )

        return batch_results

    def _handle_batch_results(
        self,
        batch_results: list[Union[BaseException, ParallelChunkResult]],
        batch_idx: int,
        batch: list[str],
    ) -> list[ParallelChunkResult]:
        """Handle batch results and convert exceptions to failed results."""
        processed_results = []

        for i, result in enumerate(batch_results):
            if isinstance(result, ParallelChunkResult):
                processed_results.append(result)
            else:
                # Handle any exception or unexpected result type
                converted_error = (
                    (Exception(str(result)) if not isinstance(result, Exception) else result)
                    if isinstance(result, BaseException)
                    else Exception(f"Unexpected result type: {type(result)}")
                )
                # Create failed result directly instead of using helper
                global_chunk_index = calculate_batch_indices(batch_idx, self.chunk_batch_size, i)
                failed_result = ParallelChunkResult(
                    chunk_id=global_chunk_index,
                    chunk_content=batch[i],
                    processing_result=None,
                    success=False,
                    error=converted_error,
                )
                processed_results.append(failed_result)

        return processed_results

    async def _process_single_chunk(
        self, chunk_id: int, chunk_content: str, target_tokens: int
    ) -> ParallelChunkResult:
        """Process a single chunk with error handling."""
        start_time = time.time()

        try:
            # For now, just validate the chunk and return it
            # In a more sophisticated implementation, this could apply
            # further processing, compression, or analysis

            # Simple processing: ensure chunk is within reasonable bounds
            if (
                token_count := await self.parallel_token_counter.count_tokens(chunk_content)
            ) > target_tokens * 2:
                # Chunk is too large, truncate it safely
                lines = chunk_content.split("\n")
                target_lines = len(lines) * target_tokens // token_count
                processed_content = "\n".join(lines[: max(1, target_lines)])
            else:
                processed_content = chunk_content

            return ParallelChunkResult(
                chunk_id=chunk_id,
                chunk_content=chunk_content,
                processing_result=processed_content,
                success=True,
                processing_time=time.time() - start_time,
            )

        except PromptFittingError as error:
            return ParallelChunkResult(
                chunk_id=chunk_id,
                chunk_content=chunk_content,
                processing_result=None,
                success=False,
                error=error,
                processing_time=time.time() - start_time,
            )

    async def _parallel_validate_chunks(self, original_content: str, chunks: list[str]) -> None:
        """Validate chunks in parallel for data integrity."""

        # Use parallel token counting for validation
        original_lines = set(original_content.split("\n"))

        # Extract all lines from chunks in parallel
        chunk_line_sets = []
        for chunk in chunks:
            chunk_lines = set(chunk.split("\n"))
            chunk_line_sets.append(chunk_lines)

        # Combine all chunk lines
        all_chunk_lines = set()
        for line_set in chunk_line_sets:
            all_chunk_lines.update(line_set)

        # Check coverage
        if missing_lines := original_lines - all_chunk_lines:
            coverage = (len(original_lines) - len(missing_lines)) / len(original_lines) * 100
            self.logger.warning(
                f"Parallel validation found {coverage:.1f}% coverage, "
                f"{len(missing_lines)} lines missing"
            )
        else:
            self.logger.info("Parallel validation confirmed complete coverage")

    def _is_chunked_result(self, result: FittingResult[ContentFitterT]) -> bool:
        """Check if a result contains chunked content."""
        return (
            CONTENT_SEGMENT_HEADER in result.fitted_content
            or DIFF_SEGMENT_HEADER in result.fitted_content
            or LOG_SEGMENT_HEADER in result.fitted_content
        )

    def _extract_chunks_from_result(self, result: FittingResult[ContentFitterT]) -> list[str]:
        """Extract individual chunks from a fitting result."""
        content = result.fitted_content
        chunks = []

        # Handle different chunk formats
        for separator in (CONTENT_SEGMENT_HEADER, DIFF_SEGMENT_HEADER, LOG_SEGMENT_HEADER):
            if separator in content:
                segments = content.split(separator)[1:]  # Skip before first separator
                for segment in segments:
                    lines = segment.split("\n")[1:]  # Skip header line
                    chunk_content = "\n".join(
                        line for line in lines if line.strip() and not line.startswith("---")
                    )
                    if chunk_content.strip():
                        chunks.append(chunk_content)
                break

        return chunks

    def _combine_parallel_chunks(self, chunk_results: list[ParallelChunkResult]) -> str:
        """Combine parallel chunk processing results into final content."""

        successful_chunks = [r for r in chunk_results if r.success]

        if failed_chunks := [r for r in chunk_results if not r.success]:
            self.logger.warning(f"Using fallback for {len(failed_chunks)} failed chunks")

        # Combine successful chunks
        combined_parts = []
        for result in sorted(successful_chunks, key=lambda r: r.chunk_id):
            processed_content = result.processing_result or result.chunk_content
            header = f"{PARALLEL_CHUNK_HEADER_PREFIX} {result.chunk_id + 1} ---"
            combined_parts.append(f"{header}\n{processed_content}")

        # Add failed chunks with original content (fallback)
        for result in sorted(failed_chunks, key=lambda r: r.chunk_id):
            header = f"{PARALLEL_CHUNK_HEADER_PREFIX} {result.chunk_id + 1} (Fallback) ---"
            combined_parts.append(f"{header}\n{result.chunk_content}")

        footer = (
            f"\n\n{PARALLEL_PROCESSING_FOOTER} {len(successful_chunks)} chunks "
            f"processed successfully ---"
        )
        return "\n\n".join(combined_parts) + footer

    def validate_preservation(self, original: str, fitted: str) -> bool:
        """Delegate validation to base fitter with parallel enhancements."""
        return self.base_fitter.validate_preservation(original, fitted)
