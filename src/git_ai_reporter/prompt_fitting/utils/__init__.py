# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Shared utility functions for prompt fitting operations."""

from .boundary_analysis import analyze_structural_integrity
from .boundary_analysis import calculate_all_chunk_overlaps
from .boundary_analysis import calculate_average_overlap
from .boundary_analysis import calculate_chunk_overlap_ratio
from .boundary_analysis import detect_empty_chunks
from .boundary_analysis import get_critical_structure_patterns
from .boundary_analysis import identify_low_overlap_pairs
from .line_analysis import cluster_nearby_indices
from .line_analysis import group_consecutive_indices
from .line_analysis import split_content_into_lines
from .parallel_processing import calculate_batch_indices
from .parallel_processing import create_batch_processing_summary
from .parallel_processing import handle_batch_exception
from .parallel_processing import process_single_batch_with_semaphore
from .parallel_processing import split_into_batches
from .parallel_processing import validate_batch_processing_setup
from .semantic_analysis import analyze_element_preservation
from .semantic_analysis import create_semantic_metadata
from .semantic_analysis import extract_semantic_elements
from .semantic_analysis import find_missing_critical_elements
from .semantic_analysis import generate_loss_warnings_and_errors
from .strategy_selection import apply_content_size_adjustments
from .strategy_selection import apply_data_integrity_adjustments
from .strategy_selection import apply_optimization_target_adjustments
from .strategy_selection import apply_performance_priority_adjustments
from .strategy_selection import calculate_complexity_adjustments
from .strategy_selection import create_content_type_preferences
from .strategy_selection import create_strategy_name_mapping
from .strategy_selection import normalize_and_sort_scores

__all__ = [
    "analyze_element_preservation",
    "analyze_structural_integrity",
    "apply_content_size_adjustments",
    "apply_data_integrity_adjustments",
    "apply_optimization_target_adjustments",
    "apply_performance_priority_adjustments",
    "calculate_all_chunk_overlaps",
    "calculate_average_overlap",
    "calculate_batch_indices",
    "calculate_chunk_overlap_ratio",
    "calculate_complexity_adjustments",
    "cluster_nearby_indices",
    "create_batch_processing_summary",
    "create_content_type_preferences",
    "create_semantic_metadata",
    "create_strategy_name_mapping",
    "detect_empty_chunks",
    "extract_semantic_elements",
    "find_missing_critical_elements",
    "generate_loss_warnings_and_errors",
    "get_critical_structure_patterns",
    "group_consecutive_indices",
    "handle_batch_exception",
    "identify_low_overlap_pairs",
    "normalize_and_sort_scores",
    "process_single_batch_with_semaphore",
    "split_content_into_lines",
    "split_into_batches",
    "validate_batch_processing_setup",
]
