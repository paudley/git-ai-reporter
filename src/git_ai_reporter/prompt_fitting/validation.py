# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Comprehensive validation framework for data integrity enforcement.

This module provides sophisticated validation capabilities to ensure 100%
data preservation across all prompt fitting operations, as required by the project.
"""

from dataclasses import dataclass
from typing import Any

from .constants import BROKEN_STRUCTURE_PENALTY
from .constants import MIN_OVERLAP_THRESHOLD
from .constants import PERFECT_COVERAGE_PERCENTAGE
from .constants import PERFECT_PRESERVATION_SCORE
from .exceptions import DataIntegrityViolationError
from .utils.boundary_analysis import analyze_structural_integrity
from .utils.boundary_analysis import calculate_all_chunk_overlaps
from .utils.boundary_analysis import calculate_average_overlap
from .utils.boundary_analysis import detect_empty_chunks
from .utils.boundary_analysis import identify_low_overlap_pairs
from .utils.line_analysis import calculate_line_coverage_percentage
from .utils.line_analysis import find_line_matches
from .utils.line_analysis import group_consecutive_indices
from .utils.line_analysis import split_content_into_lines
from .utils.semantic_analysis import analyze_element_preservation
from .utils.semantic_analysis import create_semantic_metadata
from .utils.semantic_analysis import extract_semantic_elements
from .utils.semantic_analysis import generate_loss_warnings_and_errors


@dataclass
class ValidationResult:
    """Result of a data integrity validation operation.

    This class captures detailed information about validation results,
    including coverage metrics, identified issues, and recommendations.
    """

    is_valid: bool
    coverage_percentage: float
    missing_sections: list[tuple[int, int]]
    warnings: list[str]
    errors: list[str]
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate the validation result itself."""
        if self.coverage_percentage < 0 or self.coverage_percentage > PERFECT_COVERAGE_PERCENTAGE:
            raise ValueError(f"Invalid coverage percentage: {self.coverage_percentage}")

    def raise_if_invalid(self) -> None:
        """Raise DataIntegrityViolationError if validation failed.

        This method enforces the project requirement for 100% data integrity
        by raising an exception if any data loss is detected.
        """
        if not self.is_valid:
            error_msg = f"Data integrity validation failed: {'; '.join(self.errors)}"
            raise DataIntegrityViolationError(
                error_msg,
                coverage_percentage=self.coverage_percentage,
                missing_sections=self.missing_sections,
                context={"warnings": self.warnings, "metadata": self.metadata},
            )


class DataIntegrityValidator:
    """Comprehensive validator for data preservation across prompt fitting operations.

    This validator implements multiple validation strategies to ensure that
    fitted content preserves 100% of the original information, as mandated
    by project requirements.
    """

    def __init__(self, strict_mode: bool = True, min_coverage: float = 100.0):
        """Initialize the validator with configuration.

        Args:
            strict_mode: If True, enforces 100% data integrity requirements
            min_coverage: Minimum required coverage percentage (default: 100.0)
        """
        self.strict_mode = strict_mode
        self.min_coverage = min_coverage if strict_mode else max(min_coverage, 95.0)

    def validate_chunks_coverage(self, original: str, chunks: list[str]) -> ValidationResult:
        """Validate that chunks provide complete coverage of original content.

        This method ensures that overlapping chunks cover every line/character
        of the original content with no gaps or data loss.

        Args:
            original: Original content before chunking
            chunks: List of content chunks

        Returns:
            ValidationResult with detailed coverage analysis
        """
        if not chunks:
            return self._create_empty_chunks_result(original)

        original_lines = split_content_into_lines(original)
        chunk_coverage, covered_lines = self._analyze_chunk_coverage(original_lines, chunks)
        coverage_percentage = self._calculate_coverage_percentage(original_lines, covered_lines)
        missing_sections = self._identify_missing_sections(original_lines, covered_lines)
        warnings, errors = self._generate_coverage_diagnostics(
            coverage_percentage, missing_sections
        )

        return ValidationResult(
            is_valid=len(errors) == 0,
            coverage_percentage=coverage_percentage,
            missing_sections=missing_sections,
            warnings=warnings,
            errors=errors,
            metadata={
                "original_lines": len(original_lines),
                "covered_lines": len(covered_lines),
                "chunk_count": len(chunks),
                "chunk_coverage": chunk_coverage,
            },
        )

    def validate_boundary_preservation(self, _original: str, chunks: list[str]) -> ValidationResult:
        """Validate that chunk boundaries preserve important context.

        This method checks that chunks maintain proper overlap and don't
        break critical structures like function definitions or file headers.

        Args:
            chunks: List of content chunks

        Returns:
            ValidationResult with boundary analysis
        """
        warnings, errors = self._validate_chunk_integrity(chunks)
        overlap_ratios = calculate_all_chunk_overlaps(chunks)
        overlap_warnings = self._generate_overlap_warnings(overlap_ratios)
        warnings.extend(overlap_warnings)

        broken_structures, structure_warnings = analyze_structural_integrity(chunks)
        warnings.extend(structure_warnings)

        coverage_percentage = self._calculate_boundary_coverage_percentage(broken_structures)
        avg_overlap = calculate_average_overlap(overlap_ratios)

        return ValidationResult(
            is_valid=len(errors) == 0,
            coverage_percentage=coverage_percentage,
            missing_sections=[],
            warnings=warnings,
            errors=errors,
            metadata={
                "average_overlap": avg_overlap,
                "overlap_ratios": overlap_ratios,
                "broken_structures": broken_structures,
            },
        )

    def validate_semantic_integrity(self, original: str, fitted: str) -> ValidationResult:
        """Validate that semantic information is preserved in fitted content.

        This method checks that key semantic elements (file names, function names,
        important keywords) are preserved in the fitted content.

        Args:
            original: Original content before fitting
            fitted: Fitted content after processing

        Returns:
            ValidationResult with semantic preservation analysis
        """
        original_elements = extract_semantic_elements(original)
        preservation_analysis = analyze_element_preservation(original_elements, fitted)
        warnings, errors = generate_loss_warnings_and_errors(preservation_analysis.loss_analysis)
        metadata = create_semantic_metadata(preservation_analysis)

        return ValidationResult(
            is_valid=len(errors) == 0
            and preservation_analysis.preservation_percentage >= self.min_coverage,
            coverage_percentage=preservation_analysis.preservation_percentage,
            missing_sections=[],
            warnings=warnings,
            errors=errors,
            metadata=metadata,
        )

    def validate_complete(
        self, original: str, fitted: str, chunks: list[str] | None = None
    ) -> ValidationResult:
        """Perform complete validation of fitted content.

        This method runs all validation checks and returns a comprehensive
        result indicating overall data integrity preservation.

        Args:
            original: Original content before fitting
            fitted: Fitted content after processing
            chunks: Optional list of chunks used in fitting

        Returns:
            Comprehensive ValidationResult
        """
        results = []

        # Run semantic validation
        semantic_result = self.validate_semantic_integrity(original, fitted)
        results.append(("semantic", semantic_result))

        # Run chunk validation if chunks provided
        if chunks:
            chunk_result = self.validate_chunks_coverage(original, chunks)
            results.append(("chunks", chunk_result))

            boundary_result = self.validate_boundary_preservation(original, chunks)
            results.append(("boundaries", boundary_result))

        # Combine results
        all_errors = []
        all_warnings = []
        all_metadata = {}

        for validation_type, result in results:
            all_errors.extend([f"{validation_type}: {error}" for error in result.errors])
            all_warnings.extend([f"{validation_type}: {warning}" for warning in result.warnings])
            all_metadata[validation_type] = result.metadata

        # Calculate overall coverage as minimum of all validations
        min_coverage = min((result.coverage_percentage for _, result in results), default=0.0)

        # Collect all missing sections
        all_missing_sections = []
        for _, result in results:
            all_missing_sections.extend(result.missing_sections)

        return ValidationResult(
            is_valid=len(all_errors) == 0 and min_coverage >= self.min_coverage,
            coverage_percentage=min_coverage,
            missing_sections=all_missing_sections,
            warnings=all_warnings,
            errors=all_errors,
            metadata=all_metadata,
        )

    def _create_empty_chunks_result(self, original: str) -> ValidationResult:
        """Create validation result for empty chunks scenario.

        Args:
            original: Original content

        Returns:
            ValidationResult indicating no chunks provided
        """
        return ValidationResult(
            is_valid=False,
            coverage_percentage=0.0,
            missing_sections=[(0, len(original))],
            warnings=[],
            errors=["No chunks provided"],
            metadata={"original_length": len(original)},
        )

    def _analyze_chunk_coverage(
        self, original_lines: list[str], chunks: list[str]
    ) -> tuple[list[set[int]], set[int]]:
        """Analyze which lines each chunk covers in the original content.

        Args:
            original_lines: Lines from original content
            chunks: List of content chunks

        Returns:
            Tuple of (chunk_coverage, covered_lines)
        """
        covered_lines: set[int] = set()
        chunk_coverage: list[set[int]] = []

        for chunk in chunks:
            chunk_lines = chunk.split("\n")
            chunk_covered = self._find_chunk_line_matches(original_lines, chunk_lines)
            covered_lines.update(chunk_covered)
            chunk_coverage.append(chunk_covered)

        return chunk_coverage, covered_lines

    def _find_chunk_line_matches(
        self, original_lines: list[str], chunk_lines: list[str]
    ) -> set[int]:
        """Find which original lines appear in a chunk.

        Args:
            original_lines: Lines from original content
            chunk_lines: Lines from current chunk

        Returns:
            Set of line indices that match
        """
        return find_line_matches(original_lines, chunk_lines)

    def _calculate_coverage_percentage(
        self, original_lines: list[str], covered_lines: set[int]
    ) -> float:
        """Calculate percentage of lines covered by chunks.

        Args:
            original_lines: Lines from original content
            covered_lines: Set of covered line indices

        Returns:
            Coverage percentage (0.0-100.0)
        """
        return calculate_line_coverage_percentage(len(original_lines), len(covered_lines))

    def _identify_missing_sections(
        self, original_lines: list[str], covered_lines: set[int]
    ) -> list[tuple[int, int]]:
        """Identify consecutive sections of missing lines.

        Args:
            original_lines: Lines from original content
            covered_lines: Set of covered line indices

        Returns:
            List of (start, end) tuples for missing sections
        """
        total_lines = len(original_lines)

        if not (missing_lines := set(range(total_lines)) - covered_lines):
            return []

        return self._group_consecutive_missing_lines(missing_lines)

    def _group_consecutive_missing_lines(self, missing_lines: set[int]) -> list[tuple[int, int]]:
        """Group consecutive missing lines into sections.

        Args:
            missing_lines: Set of missing line indices

        Returns:
            List of (start, end) tuples for consecutive sections
        """
        return group_consecutive_indices(missing_lines)

    def _generate_coverage_diagnostics(
        self, coverage_percentage: float, missing_sections: list[tuple[int, int]]
    ) -> tuple[list[str], list[str]]:
        """Generate warnings and errors based on coverage analysis.

        Args:
            coverage_percentage: Calculated coverage percentage
            missing_sections: List of missing section ranges

        Returns:
            Tuple of (warnings, errors) lists
        """
        warnings: list[str] = []
        errors: list[str] = []

        # Check coverage threshold
        if coverage_percentage < self.min_coverage:
            error_msg = f"Coverage {coverage_percentage:.1f}% below required {self.min_coverage}%"
            if self.strict_mode:
                errors.append(error_msg)
            else:
                warnings.append(error_msg)

        # Check for missing sections
        if missing_sections:
            missing_count = sum(end - start + 1 for start, end in missing_sections)
            error_msg = f"{missing_count} lines not covered by any chunk"
            if self.strict_mode:
                errors.append(error_msg)
            else:
                warnings.append(error_msg)

        return warnings, errors

    def _validate_chunk_integrity(self, chunks: list[str]) -> tuple[list[str], list[str]]:
        """Validate basic chunk integrity (detect empty chunks).

        Args:
            chunks: List of chunks to validate

        Returns:
            Tuple of (warnings, errors) lists
        """
        warnings: list[str] = []
        errors: list[str] = []

        empty_chunk_indices = detect_empty_chunks(chunks)
        for index in empty_chunk_indices:
            errors.append(f"Empty chunk {index} detected")

        return warnings, errors

    def _generate_overlap_warnings(self, overlap_ratios: list[float]) -> list[str]:
        """Generate warnings for chunks with insufficient overlap.

        Args:
            overlap_ratios: List of overlap ratios between adjacent chunks

        Returns:
            List of warning messages
        """
        warnings: list[str] = []

        low_overlap_pairs = identify_low_overlap_pairs(overlap_ratios, MIN_OVERLAP_THRESHOLD)
        for chunk_index, overlap_ratio in low_overlap_pairs:
            warnings.append(
                f"Low overlap between chunks {chunk_index} and {chunk_index + 1}: "
                f"{overlap_ratio:.1%}"
            )

        return warnings

    def _calculate_boundary_coverage_percentage(self, broken_structures: int) -> float:
        """Calculate coverage percentage based on structural integrity.

        Args:
            broken_structures: Number of broken structural patterns

        Returns:
            Coverage percentage (penalized for broken structures)
        """
        penalty = broken_structures * BROKEN_STRUCTURE_PENALTY
        return max(0.0, PERFECT_PRESERVATION_SCORE - penalty)
