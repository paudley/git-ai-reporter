# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Utilities for boundary analysis and structural pattern detection.

This module provides reusable functions for analyzing chunk boundaries,
calculating overlap ratios, and detecting structural patterns in content.
"""

import re
from typing import Optional

from ..constants import MIN_DIVISOR


def calculate_chunk_overlap_ratio(chunk1: str, chunk2: str) -> float:
    """Calculate overlap ratio between two chunks based on common lines.

    Args:
        chunk1: First chunk content
        chunk2: Second chunk content

    Returns:
        Overlap ratio (0.0-1.0) based on common lines in chunk1

    Examples:
        >>> calculate_chunk_overlap_ratio("line1\\nline2\\nline3", "line2\\nline3\\nline4")
        0.667  # 2 out of 3 lines from chunk1 overlap (~66.7%)
    """
    if not chunk1.strip():
        return 0.0

    chunk1_lines = set(chunk1.split("\n"))
    chunk2_lines = set(chunk2.split("\n"))
    overlap_lines = chunk1_lines & chunk2_lines

    return len(overlap_lines) / max(MIN_DIVISOR, len(chunk1_lines))


def calculate_all_chunk_overlaps(chunks: list[str]) -> list[float]:
    """Calculate overlap ratios for all adjacent chunk pairs.

    Args:
        chunks: List of content chunks

    Returns:
        List of overlap ratios between adjacent chunks
    """
    overlap_ratios: list[float] = []

    for i in range(len(chunks) - 1):
        overlap_ratio = calculate_chunk_overlap_ratio(chunks[i], chunks[i + 1])
        overlap_ratios.append(overlap_ratio)

    return overlap_ratios


def get_critical_structure_patterns() -> list[str]:
    """Get list of regex patterns for critical code structures.

    Returns:
        List of regex patterns that shouldn't be broken across chunks
    """
    return [
        r"^diff --git",  # Git diff headers
        r"^@@.*@@",  # Git diff hunk headers (NOT an email pattern)
        r"^def\s+\w+",  # Python function definitions
        r"^class\s+\w+",  # Python class definitions
        r"^function\s+\w+",  # JavaScript functions
        r"^import\s+\w+",  # Import statements
        r"^from\s+\w+",  # From imports
        r"^#\s*\w+",  # Header comments
    ]


def find_pattern_matches(content: str, pattern: str) -> tuple[list[str], list[str]]:
    """Find complete and incomplete matches for a structural pattern.

    Args:
        content: Content to search in
        pattern: Regex pattern to match

    Returns:
        Tuple of (complete_matches, incomplete_matches)
    """
    lines = content.split("\n")
    complete_matches: list[str] = []
    incomplete_matches: list[str] = []

    for line in lines:
        stripped_line = line.strip()
        if re.match(pattern, stripped_line):
            complete_matches.append(line)
        elif pattern.replace("^", "") in line and not re.match(pattern, stripped_line):
            # Potential broken structure - contains pattern text but doesn't match fully
            incomplete_matches.append(line)

    return complete_matches, incomplete_matches


def analyze_structural_integrity(
    chunks: list[str], patterns: Optional[list[str]] = None
) -> tuple[int, list[str]]:
    """Analyze chunks for structural integrity violations.

    Args:
        chunks: List of content chunks to analyze
        patterns: Optional list of patterns to check (uses defaults if None)

    Returns:
        Tuple of (broken_structure_count, warnings)
    """
    if patterns is None:
        patterns = get_critical_structure_patterns()

    broken_structures = 0
    warnings: list[str] = []

    for chunk in chunks:
        for pattern in patterns:
            _, incomplete_matches = find_pattern_matches(chunk, pattern)

            if incomplete_matches:
                broken_structures += len(incomplete_matches)
                warnings.append(f"Potential broken structure in chunk: {pattern}")

    return broken_structures, warnings


def detect_empty_chunks(chunks: list[str]) -> list[int]:
    """Detect empty or whitespace-only chunks.

    Args:
        chunks: List of chunks to check

    Returns:
        List of indices of empty chunks
    """
    empty_indices: list[int] = []

    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            empty_indices.append(i)

    return empty_indices


def calculate_average_overlap(overlap_ratios: list[float]) -> float:
    """Calculate average overlap ratio with safe division.

    Args:
        overlap_ratios: List of overlap ratios

    Returns:
        Average overlap ratio (0.0 if no ratios provided)
    """
    if not overlap_ratios:
        return 0.0

    return sum(overlap_ratios) / len(overlap_ratios)


def identify_low_overlap_pairs(
    overlap_ratios: list[float], threshold: float
) -> list[tuple[int, float]]:
    """Identify chunk pairs with overlap below threshold.

    Args:
        overlap_ratios: List of overlap ratios between adjacent chunks
        threshold: Minimum acceptable overlap ratio

    Returns:
        List of (chunk_index, overlap_ratio) tuples for low-overlap pairs
    """
    low_overlap_pairs: list[tuple[int, float]] = []

    for i, ratio in enumerate(overlap_ratios):
        if ratio < threshold:
            low_overlap_pairs.append((i, ratio))

    return low_overlap_pairs
