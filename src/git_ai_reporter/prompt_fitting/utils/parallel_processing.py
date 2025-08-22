# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Parallel processing utilities for complex batch processing operations.

This module provides utilities to break down complex parallel processing
into focused, testable helper functions.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypedDict, TypeVar, Union

from typing_extensions import Protocol

T = TypeVar("T")


class ChunkResultProtocol(Protocol):
    """Protocol for chunk result objects."""

    chunk_id: int
    chunk_content: str
    processing_result: Union[str, None]
    success: bool
    error: Union[Exception, None]


class BatchSummary(TypedDict):
    """Type definition for batch processing summary."""

    operation: str
    total_batches: int
    total_chunks: int
    successful: int
    failed: int
    success_rate: float
    chunks_per_batch: float


@dataclass
class BatchProcessingParams:
    """Parameters for batch processing configuration."""

    chunk_batch_size: int
    max_workers: int
    total_batches: int
    process_function_name: str


@dataclass
class BatchProcessingResult:
    """Result of batch processing operation."""

    batch_index: int
    total_results: int
    successful_results: int
    failed_results: int
    processing_errors: list[Exception]


@dataclass
class SemaphoreBatchParams:
    """Parameters for semaphore-controlled batch processing."""

    batch: list[str]
    batch_index: int
    batch_size: int
    max_workers: int
    process_single_chunk_func: Callable[[int, str, int], Awaitable[object]]
    target_tokens: int


def split_into_batches(chunks: list[str], batch_size: int) -> list[list[str]]:
    """Split chunks into batches for parallel processing.

    Args:
        chunks: List of content chunks to process
        batch_size: Maximum size per batch

    Returns:
        List of batch lists
    """
    return [chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)]


def calculate_batch_indices(batch_index: int, batch_size: int, chunk_index: int) -> int:
    """Calculate global chunk index from batch and local indices.

    Args:
        batch_index: Index of current batch
        batch_size: Size of each batch
        chunk_index: Index within current batch

    Returns:
        Global chunk index
    """
    return chunk_index + batch_index * batch_size


async def create_semaphore_wrapper(
    semaphore: asyncio.Semaphore, task: Awaitable[T]
) -> Union[T, Exception]:
    """Wrap a task with semaphore-based concurrency control.

    Args:
        semaphore: Semaphore for limiting concurrency
        task: Async task to execute

    Returns:
        Task result
    """
    async with semaphore:
        return await task


def create_batch_processing_summary(
    all_results: list[object], batch_count: int, process_name: str
) -> BatchSummary:
    """Create summary statistics for batch processing results.

    Args:
        all_results: List of all processing results
        batch_count: Total number of batches processed
        process_name: Name of processing operation

    Returns:
        Dictionary with processing statistics
    """
    successful = sum(1 for r in all_results if hasattr(r, "success") and r.success)
    failed = len(all_results) - successful

    return BatchSummary(
        operation=process_name,
        total_batches=batch_count,
        total_chunks=len(all_results),
        successful=successful,
        failed=failed,
        success_rate=(successful / len(all_results) * 100) if all_results else 0.0,
        chunks_per_batch=len(all_results) / batch_count if batch_count > 0 else 0.0,
    )


def handle_batch_exception(
    exception: Exception,
    batch_index: int,
    chunk_index: int,
    chunk_content: str,
    chunk_result_class: Callable[..., ChunkResultProtocol],
) -> ChunkResultProtocol:
    """Handle exceptions during batch processing by creating failed result objects.

    Args:
        exception: Exception that occurred
        batch_index: Index of batch where exception occurred
        chunk_index: Index of chunk within batch
        chunk_content: Content of the chunk being processed
        chunk_result_class: Class to create for failed result

    Returns:
        Failed result object
    """
    global_chunk_index = calculate_batch_indices(
        batch_index, 0, chunk_index
    )  # batch_size=0 for direct mapping

    return chunk_result_class(
        chunk_id=global_chunk_index,
        chunk_content=chunk_content,
        processing_result=None,
        success=False,
        error=exception,
    )


def validate_batch_processing_setup(
    chunks: list[str], batch_size: int, max_workers: int
) -> BatchProcessingParams:
    """Validate and prepare batch processing parameters.

    Args:
        chunks: List of chunks to process
        batch_size: Desired batch size
        max_workers: Maximum number of workers

    Returns:
        Validated batch processing parameters

    Raises:
        ValueError: If parameters are invalid
    """
    if not chunks:
        raise ValueError("Cannot process empty chunks list")

    if batch_size <= 0:
        raise ValueError(f"Invalid batch size: {batch_size}")

    if max_workers <= 0:
        raise ValueError(f"Invalid max workers: {max_workers}")

    batches = split_into_batches(chunks, batch_size)

    return BatchProcessingParams(
        chunk_batch_size=batch_size,
        max_workers=max_workers,
        total_batches=len(batches),
        process_function_name="parallel_batch_processing",
    )


async def process_single_batch_with_semaphore(
    params: SemaphoreBatchParams,
) -> list[Union[Exception, object]]:
    """Process a single batch with semaphore-controlled concurrency.

    Args:
        params: SemaphoreBatchParams containing all processing parameters

    Returns:
        List of processing results for this batch
    """
    # Create tasks for parallel processing of this batch
    batch_tasks = [
        params.process_single_chunk_func(
            calculate_batch_indices(params.batch_index, params.batch_size, chunk_idx),
            chunk,
            params.target_tokens,
        )
        for chunk_idx, chunk in enumerate(params.batch)
    ]

    # Use semaphore to limit concurrent processing
    semaphore = asyncio.Semaphore(params.max_workers)

    # Execute batch concurrently with semaphore control
    batch_results = await asyncio.gather(
        *[create_semaphore_wrapper(semaphore, task) for task in batch_tasks], return_exceptions=True
    )

    return batch_results
