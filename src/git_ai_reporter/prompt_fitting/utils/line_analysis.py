# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Shared utilities for analyzing and processing line-based content.

This module provides reusable functions for common operations on text lines,
including consecutive grouping, clustering, coverage analysis, and content splitting.
"""

from collections.abc import Iterable


def group_consecutive_indices(indices: Iterable[int]) -> list[tuple[int, int]]:
    """Group consecutive indices into (start, end) ranges.

    This utility function groups consecutive integer indices into ranges,
    which is useful for identifying missing sections, clustering changes,
    or any other consecutive grouping operation.

    Args:
        indices: Iterable of integer indices to group

    Returns:
        List of (start, end) tuples representing consecutive ranges

    Examples:
        >>> group_consecutive_indices([1, 2, 3, 5, 6, 8])
        [(1, 3), (5, 6), (8, 8)]
        >>> group_consecutive_indices({4, 1, 2, 10})
        [(1, 2), (4, 4), (10, 10)]
    """
    if not (sorted_indices := sorted(set(indices))):
        return []

    ranges: list[tuple[int, int]] = []
    start = sorted_indices[0]
    end = start

    for index in sorted_indices[1:]:
        if index == end + 1:
            end = index
        else:
            ranges.append((start, end))
            start = end = index
    ranges.append((start, end))

    return ranges


def split_content_into_lines(content: str) -> list[str]:
    """Split content into lines, handling various line ending formats.

    Args:
        content: Content to split into lines

    Returns:
        List of lines
    """
    return content.split("\n")


def calculate_line_coverage_percentage(total_lines: int, covered_lines: int) -> float:
    """Calculate coverage percentage with proper division by zero handling.

    Args:
        total_lines: Total number of lines
        covered_lines: Number of covered lines

    Returns:
        Coverage percentage (0.0-100.0)
    """
    if total_lines <= 0:
        return 0.0
    return (covered_lines / total_lines) * 100.0


def find_line_matches(target_lines: list[str], search_lines: list[str]) -> set[int]:
    """Find indices of target lines that appear in search lines.

    Args:
        target_lines: Lines to search within
        search_lines: Lines to search for

    Returns:
        Set of indices in target_lines that match search_lines
    """
    matches: set[int] = set()
    for i, target_line in enumerate(target_lines):
        if target_line in search_lines:
            matches.add(i)
    return matches


def cluster_nearby_indices(
    indices: list[int], max_distance: int, min_cluster_size: int = 1
) -> list[list[int]]:
    """Cluster indices that are within a maximum distance of each other.

    This function groups indices into clusters where each index in a cluster
    is within max_distance of at least one other index in the same cluster.
    Only clusters meeting the minimum size requirement are returned.

    Args:
        indices: List of indices to cluster
        max_distance: Maximum distance between indices to be in same cluster
        min_cluster_size: Minimum number of indices required for a valid cluster

    Returns:
        List of clusters, where each cluster is a list of indices

    Examples:
        >>> cluster_nearby_indices([1, 2, 3, 10, 11, 20], max_distance=2, min_cluster_size=2)
        [[1, 2, 3], [10, 11]]
        >>> cluster_nearby_indices([1, 5, 6, 15], max_distance=1, min_cluster_size=2)
        [[5, 6]]
    """
    if not indices:
        return []

    sorted_indices = sorted(indices)
    clusters: list[list[int]] = []
    current_cluster = [sorted_indices[0]]

    for i in range(1, len(sorted_indices)):
        if sorted_indices[i] - sorted_indices[i - 1] <= max_distance:
            current_cluster.append(sorted_indices[i])
        else:
            if len(current_cluster) >= min_cluster_size:
                clusters.append(current_cluster)
            current_cluster = [sorted_indices[i]]

    # Don't forget the last cluster
    if len(current_cluster) >= min_cluster_size:
        clusters.append(current_cluster)

    return clusters
