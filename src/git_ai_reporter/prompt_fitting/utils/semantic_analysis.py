# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Utilities for semantic content analysis and preservation validation.

This module provides reusable functions for extracting and analyzing
semantic elements in code and text content, including file references,
function names, imports, and other structurally significant elements.
"""

from dataclasses import dataclass
import re
from typing import Any

from ..constants import FULL_PERCENTAGE
from ..constants import MIN_DIVISOR
from ..constants import SIGNIFICANT_LOSS_THRESHOLD


@dataclass
class SemanticElements:
    """Container for extracted semantic elements from content."""

    files: list[str]
    functions: list[str]
    imports: list[str]
    classes: list[str]
    variables: list[str]

    @property
    def total_count(self) -> int:
        """Get total count of all semantic elements."""
        return (
            len(self.files)
            + len(self.functions)
            + len(self.imports)
            + len(self.classes)
            + len(self.variables)
        )

    def get_counts_by_type(self) -> dict[str, int]:
        """Get counts of elements by type."""
        return {
            "files": len(self.files),
            "functions": len(self.functions),
            "imports": len(self.imports),
            "classes": len(self.classes),
            "variables": len(self.variables),
        }


@dataclass
class PreservationAnalysis:
    """Analysis of semantic element preservation between original and fitted content."""

    original_elements: SemanticElements
    preserved_counts: dict[str, int]
    preservation_percentage: float
    loss_analysis: dict[str, dict[str, Any]]


def get_semantic_element_patterns() -> dict[str, str]:
    """Get regex patterns for extracting semantic elements.

    Returns:
        Dictionary mapping element type to regex pattern
    """
    return {
        "files": r"\b[\w/.-]+\.(py|js|ts|md|txt|yml|json|go|rs|html|css|sh|sql)\b",
        "functions": r"\b(?:def|function|async\s+def)\s+(\w+)",
        "classes": r"\b(?:class|interface)\s+(\w+)",
        "imports": r"\b(?:import|from)\s+(\w+)",
        "variables": r"\b(?:var|let|const)\s+(\w+)",  # JavaScript/TypeScript variables
    }


def extract_semantic_elements(
    content: str, patterns: dict[str, str] | None = None
) -> SemanticElements:
    """Extract semantic elements from content using regex patterns.

    Args:
        content: Content to analyze
        patterns: Optional custom patterns (uses defaults if None)

    Returns:
        SemanticElements containing all extracted elements
    """
    if patterns is None:
        patterns = get_semantic_element_patterns()

    return SemanticElements(
        files=re.findall(patterns["files"], content),
        functions=re.findall(patterns["functions"], content),
        classes=re.findall(patterns["classes"], content),
        imports=re.findall(patterns["imports"], content),
        variables=re.findall(patterns["variables"], content),
    )


def count_preserved_elements(original_elements: list[str], fitted_content: str) -> int:
    """Count how many original elements are preserved in fitted content.

    Args:
        original_elements: List of elements from original content
        fitted_content: Fitted content to search in

    Returns:
        Number of preserved elements
    """
    return len([element for element in original_elements if element in fitted_content])


def calculate_preservation_percentage(preserved_count: int, total_count: int) -> float:
    """Calculate preservation percentage with safe division.

    Args:
        preserved_count: Number of preserved elements
        total_count: Total number of original elements

    Returns:
        Preservation percentage (0.0-100.0)
    """
    if total_count <= 0:
        return FULL_PERCENTAGE  # Perfect preservation if nothing to preserve

    return (preserved_count / max(MIN_DIVISOR, total_count)) * FULL_PERCENTAGE


def analyze_element_preservation(
    original_elements: SemanticElements, fitted_content: str
) -> PreservationAnalysis:
    """Analyze preservation of semantic elements between original and fitted content.

    Args:
        original_elements: Semantic elements from original content
        fitted_content: Fitted content to check preservation in

    Returns:
        Comprehensive preservation analysis
    """
    preserved_counts = {}
    element_types = {
        "files": original_elements.files,
        "functions": original_elements.functions,
        "classes": original_elements.classes,
        "imports": original_elements.imports,
        "variables": original_elements.variables,
    }

    # Count preserved elements by type
    for element_type, elements in element_types.items():
        preserved_counts[element_type] = count_preserved_elements(elements, fitted_content)

    # Calculate overall preservation percentage
    total_preserved = sum(preserved_counts.values())
    total_original = original_elements.total_count
    preservation_percentage = calculate_preservation_percentage(total_preserved, total_original)

    # Analyze losses by type
    loss_analysis = {}
    for element_type, elements in element_types.items():
        original_count = len(elements)
        preserved_count = preserved_counts[element_type]
        lost_count = original_count - preserved_count

        if original_count > 0:
            loss_ratio = lost_count / original_count
            loss_analysis[element_type] = {
                "original_count": original_count,
                "preserved_count": preserved_count,
                "lost_count": lost_count,
                "loss_ratio": loss_ratio,
                "is_significant_loss": loss_ratio > SIGNIFICANT_LOSS_THRESHOLD,
            }

    return PreservationAnalysis(
        original_elements=original_elements,
        preserved_counts=preserved_counts,
        preservation_percentage=preservation_percentage,
        loss_analysis=loss_analysis,
    )


def generate_loss_warnings_and_errors(
    loss_analysis: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str]]:
    """Generate warnings and errors based on loss analysis.

    Args:
        loss_analysis: Analysis of losses by element type

    Returns:
        Tuple of (warnings, errors) lists
    """
    warnings: list[str] = []
    errors: list[str] = []

    for element_type, analysis in loss_analysis.items():
        if analysis["lost_count"] > 0:
            lost_count = analysis["lost_count"]

            if analysis["is_significant_loss"]:
                errors.append(
                    f"Significant {element_type} reference loss: "
                    f"{lost_count} {element_type} missing"
                )
            else:
                warnings.append(
                    f"Minor {element_type} reference loss: {lost_count} {element_type} missing"
                )

    return warnings, errors


def create_semantic_metadata(analysis: PreservationAnalysis) -> dict[str, Any]:
    """Create comprehensive metadata for semantic preservation results.

    Args:
        analysis: Preservation analysis results

    Returns:
        Metadata dictionary with detailed preservation information
    """
    metadata = {
        "semantic_preservation": analysis.preservation_percentage,
        "total_elements": analysis.original_elements.total_count,
        "total_preserved": sum(analysis.preserved_counts.values()),
    }

    # Add counts by type
    original_counts = analysis.original_elements.get_counts_by_type()
    for element_type in original_counts:
        metadata[f"total_{element_type}"] = original_counts[element_type]
        metadata[f"preserved_{element_type}"] = analysis.preserved_counts[element_type]

    return metadata


def find_missing_critical_elements(
    original_elements: SemanticElements,
    fitted_content: str,
    critical_element_types: list[str] | None = None,
) -> dict[str, list[str]]:
    """Find specific missing elements that are considered critical.

    Args:
        original_elements: Original semantic elements
        fitted_content: Fitted content to check
        critical_element_types: Types to consider critical (defaults to functions and classes)

    Returns:
        Dictionary mapping element type to list of missing critical elements
    """
    if critical_element_types is None:
        critical_element_types = ["functions", "classes"]

    missing_elements: dict[str, list[str]] = {}
    element_mapping = {
        "files": original_elements.files,
        "functions": original_elements.functions,
        "classes": original_elements.classes,
        "imports": original_elements.imports,
        "variables": original_elements.variables,
    }

    for element_type in critical_element_types:
        if element_type in element_mapping:
            elements = element_mapping[element_type]
            if missing := [elem for elem in elements if elem not in fitted_content]:
                missing_elements[element_type] = missing

    return missing_elements
