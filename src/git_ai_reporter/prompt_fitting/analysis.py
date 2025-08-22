# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Content analysis framework for intelligent prompt fitting.

This module provides comprehensive content analysis capabilities that enable
intelligent chunking strategies to make informed decisions about how to
process different types of content while maintaining perfect data integrity.
"""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Any

from .advanced_strategies import ContentAnalyzer
from .advanced_strategies import StructuralBoundary
from .constants import CHANGE_LINE_PROXIMITY_THRESHOLD
from .constants import COMPLEXITY_MODERATE_THRESHOLD
from .constants import COMPLEXITY_SIMPLE_THRESHOLD
from .constants import LONG_LINE_THRESHOLD
from .constants import MIN_CHANGE_LINES_FOR_DENSITY
from .constants import MIN_CLUSTER_SIZE
from .constants import MIN_DOCSTRING_QUOTE_COUNT
from .constants import MIN_LOG_MATCHES
from .constants import MIN_LONG_LINES_FOR_PATTERN
from .constants import MIN_MARKDOWN_INDICATORS
from .constants import MIN_PYTHON_INDICATORS
from .constants import MIN_REPETITIONS_FOR_PATTERN
from .constants import MIN_SHELL_INDICATORS
from .constants import MIN_SQL_MATCHES
from .constants import PYTHON_PATTERN_TYPES
from .constants import SUBSTANTIAL_LINE_THRESHOLD
from .logging import get_logger
from .utils.line_analysis import cluster_nearby_indices

# Local constants not yet moved to constants.py
TRIPLE_QUOTES = '"""'
SINGLE_QUOTES = "'''"
STANDARD_IMPORT_TYPE = "standard"
DOT_SEPARATOR = "."
EMPTY_STRING = ""
SHELL_SCRIPT_INDICATOR = "sh"
MIN_CONFIG_MATCHES = 5
COMPLEXITY_COMPLEX_THRESHOLD = 0.9


class ContentType(Enum):
    """Types of content that can be analyzed."""

    PYTHON_CODE = "python_code"
    GIT_DIFF = "git_diff"
    MARKDOWN = "markdown"
    JSON_DATA = "json_data"
    LOG_FILE = "log_file"
    PLAIN_TEXT = "plain_text"
    CONFIG_FILE = "config_file"
    SHELL_SCRIPT = "shell_script"
    SQL_QUERY = "sql_query"
    MIXED_CONTENT = "mixed_content"


class ContentComplexity(Enum):
    """Content complexity levels for processing strategies."""

    SIMPLE = "simple"  # Linear content with minimal structure
    MODERATE = "moderate"  # Some structure but straightforward
    COMPLEX = "complex"  # Rich structure, multiple levels
    HIGHLY_COMPLEX = "highly_complex"  # Deep nesting, intricate relationships


@dataclass
class ContentPattern:
    """Represents a detected pattern in content."""

    pattern_type: str
    confidence: float  # 0.0 - 1.0
    start_line: int
    end_line: int
    metadata: dict[str, Any]
    importance: float = 0.5  # Processing importance weight


@dataclass
class ContentMetrics:
    """Basic content metrics."""

    total_lines: int
    non_empty_lines: int
    average_line_length: float
    max_line_length: int
    indentation_levels: list[int]

    @property
    def content_density(self) -> float:
        """Calculate content density (non-empty lines ratio)."""
        return self.non_empty_lines / max(1, self.total_lines)


@dataclass
class ComplexityParams:
    """Parameters for complexity assessment."""

    lines: list[str]
    boundaries: list[StructuralBoundary]
    patterns: list[ContentPattern]
    content_type: ContentType
    indentation_levels: list[int]


@dataclass
class ContentCharacteristics:
    """Comprehensive analysis of content characteristics."""

    content_type: ContentType
    complexity: ContentComplexity
    metrics: ContentMetrics
    structural_boundaries: list[StructuralBoundary]
    detected_patterns: list[ContentPattern]
    similarity_hash: str
    metadata: dict[str, Any]

    @property
    def structural_density(self) -> float:
        """Calculate structural density (boundaries per line)."""
        return len(self.structural_boundaries) / max(1, self.metrics.total_lines)

    @property
    def content_density(self) -> float:
        """Calculate content density (non-empty lines ratio)."""
        return self.metrics.content_density


class PatternDetector(ABC):
    """Abstract base for content pattern detectors."""

    @abstractmethod
    def detect(self, content: str, lines: list[str]) -> list[ContentPattern]:
        """Detect patterns in the given content."""
        raise NotImplementedError("Subclasses must implement detect method")

    @abstractmethod
    def get_pattern_types(self) -> set[str]:
        """Get the types of patterns this detector can find."""
        raise NotImplementedError("Subclasses must implement get_pattern_types method")


class PythonPatternDetector(PatternDetector):
    """Detector for Python-specific patterns."""

    def detect(self, content: str, lines: list[str]) -> list[ContentPattern]:
        """Detect Python-specific patterns."""
        patterns = []

        # Detect docstring blocks
        patterns.extend(self._detect_docstrings(lines))

        # Detect import patterns
        patterns.extend(self._detect_import_patterns(lines))

        # Detect decorator patterns
        patterns.extend(self._detect_decorators(lines))

        # Detect exception handling
        patterns.extend(self._detect_exception_handling(lines))

        # Detect comprehensions and complex expressions
        patterns.extend(self._detect_complex_expressions(lines))

        return patterns

    def _detect_docstrings(self, lines: list[str]) -> list[ContentPattern]:
        """Detect docstring patterns."""
        patterns = []
        in_docstring = False
        docstring_start = None
        quote_type = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not in_docstring:
                # Look for docstring start
                if TRIPLE_QUOTES in stripped or SINGLE_QUOTES in stripped:
                    quote_type = TRIPLE_QUOTES if TRIPLE_QUOTES in stripped else SINGLE_QUOTES
                    if stripped.count(quote_type) == MIN_DOCSTRING_QUOTE_COUNT:
                        # Single-line docstring
                        patterns.append(
                            ContentPattern(
                                pattern_type="single_line_docstring",
                                confidence=0.9,
                                start_line=i,
                                end_line=i,
                                metadata={"quote_type": quote_type},
                                importance=0.7,
                            )
                        )
                    else:
                        # Multi-line docstring start
                        in_docstring = True
                        docstring_start = i
                continue

            if in_docstring:
                docstring_patterns = self._process_docstring_end(
                    i, stripped, quote_type, docstring_start
                )
                patterns.extend(docstring_patterns)
                if docstring_patterns:  # If we found docstring end
                    in_docstring = False
                    docstring_start = None
                    quote_type = None

        return patterns

    def _process_docstring_end(
        self, line_num: int, stripped: str, quote_type: str | None, docstring_start: int | None
    ) -> list[ContentPattern]:
        """Process potential docstring end."""
        if quote_type is not None and quote_type in stripped and docstring_start is not None:
            return [
                ContentPattern(
                    pattern_type="multi_line_docstring",
                    confidence=0.95,
                    start_line=docstring_start,
                    end_line=line_num,
                    metadata={"quote_type": quote_type, "lines": line_num - docstring_start + 1},
                    importance=0.8,
                )
            ]
        return []

    def _detect_import_patterns(self, lines: list[str]) -> list[ContentPattern]:
        """Detect import block patterns."""
        patterns = []
        import_groups = []
        current_group = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            if self._is_import_line(stripped):
                current_group = self._process_import_line(current_group, stripped, i)
            elif self._should_continue_import_group(current_group, stripped):
                continue  # Skip empty lines within imports
            elif current_group is not None:
                # End of import group
                import_groups.append(self._finalize_import_group(current_group, i - 1))
                current_group = None

        # Handle import group at end of file
        if current_group is not None:
            import_groups.append(self._finalize_import_group(current_group, len(lines) - 1))

        # Create patterns for import groups
        patterns.extend(self._create_import_patterns(import_groups))
        return patterns

    def _is_import_line(self, stripped: str) -> bool:
        """Check if line is an import statement."""
        return bool(re.match(r"^(import|from)\s+", stripped))

    def _process_import_line(
        self, current_group: dict[str, Any] | None, stripped: str, line_index: int
    ) -> dict[str, Any]:
        """Process an import line and update current group."""
        if current_group is None:
            current_group = {"start": line_index, "type": STANDARD_IMPORT_TYPE}

        # Detect import type
        import_type = self._classify_import_type(stripped)
        if import_type != STANDARD_IMPORT_TYPE and current_group["type"] == STANDARD_IMPORT_TYPE:
            current_group["type"] = import_type

        return current_group

    def _classify_import_type(self, stripped: str) -> str:
        """Classify the type of import statement."""
        if stripped.startswith("from __future__"):
            return "future"
        elif any(stdlib in stripped for stdlib in ("os", "sys", "json", "time", "re")):
            return "stdlib"
        elif DOT_SEPARATOR in stripped or any(char in stripped for char in ("-", "_")):
            return "third_party"
        return STANDARD_IMPORT_TYPE

    def _should_continue_import_group(
        self, current_group: dict[str, Any] | None, stripped: str
    ) -> bool:
        """Check if we should continue the current import group."""
        return current_group is not None and stripped == EMPTY_STRING

    def _finalize_import_group(
        self, current_group: dict[str, Any], end_line: int
    ) -> dict[str, Any]:
        """Finalize an import group with end line."""
        return {"start": current_group["start"], "end": end_line, "type": current_group["type"]}

    def _create_import_patterns(self, import_groups: list[dict[str, Any]]) -> list[ContentPattern]:
        """Create ContentPattern objects for import groups."""
        patterns = []
        for group in import_groups:
            if not (isinstance(group["start"], int) and isinstance(group["end"], int)):
                raise ValueError(f"Invalid group format: {group}")
            patterns.append(
                ContentPattern(
                    pattern_type=f"{group['type']}_imports",
                    confidence=0.85,
                    start_line=group["start"],
                    end_line=group["end"],
                    metadata={"import_type": group["type"]},
                    importance=0.6,
                )
            )
        return patterns

    def _detect_decorators(self, lines: list[str]) -> list[ContentPattern]:
        """Detect decorator patterns."""
        patterns = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("@"):
                # Look ahead to find the decorated function/class
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith(("def ", "class ", "async def ")):
                        patterns.append(
                            ContentPattern(
                                pattern_type="decorator_block",
                                confidence=0.9,
                                start_line=i,
                                end_line=j,
                                metadata={
                                    "decorator": stripped,
                                    "target": next_line.split()[1].split("(")[0],
                                },
                                importance=0.8,
                            )
                        )
                        break

        return patterns

    def _detect_exception_handling(self, lines: list[str]) -> list[ContentPattern]:
        """Detect exception handling patterns."""
        patterns = []

        # try_blocks = []  # Variable currently unused
        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith("try:"):
                # Find the entire try-except-finally block
                if (block_end := self._find_exception_block_end(lines, i)) > i:
                    patterns.append(
                        ContentPattern(
                            pattern_type="exception_handling",
                            confidence=0.9,
                            start_line=i,
                            end_line=block_end,
                            metadata={"block_size": block_end - i + 1},
                            importance=0.85,
                        )
                    )

        return patterns

    def _find_exception_block_end(self, lines: list[str], start_line: int) -> int:
        """Find the end of a try-except-finally block."""
        base_indent = len(lines[start_line]) - len(lines[start_line].lstrip())

        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                continue

            current_indent = len(line) - len(line.lstrip())
            stripped = line.strip()

            # Check if we've reached the end of the block
            if current_indent <= base_indent and not stripped.startswith(
                ("except", "finally", "else:")
            ):
                return i - 1

        return len(lines) - 1

    def _detect_complex_expressions(self, lines: list[str]) -> list[ContentPattern]:
        """Detect complex expressions and comprehensions."""
        patterns = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # List/dict/set comprehensions
            comprehension_patterns = [
                (r"\[.+for\s+.+in\s+.+\]", "list_comprehension"),
                (r"\{.+for\s+.+in\s+.+\}", "set_comprehension"),
                (r"\{.+:.+for\s+.+in\s+.+\}", "dict_comprehension"),
                (r"\(.+for\s+.+in\s+.+\)", "generator_expression"),
            ]

            for pattern, name in comprehension_patterns:
                if re.search(pattern, stripped):
                    patterns.append(
                        ContentPattern(
                            pattern_type=name,
                            confidence=0.8,
                            start_line=i,
                            end_line=i,
                            metadata={"expression": stripped[:100]},
                            importance=0.6,
                        )
                    )
                    break

        return patterns

    def get_pattern_types(self) -> set[str]:
        """Get Python pattern types."""
        return PYTHON_PATTERN_TYPES


class GitDiffPatternDetector(PatternDetector):
    """Detector for Git diff patterns."""

    def detect(self, content: str, lines: list[str]) -> list[ContentPattern]:
        """Detect Git diff patterns."""
        patterns = []

        # Detect file change types
        patterns.extend(self._detect_file_changes(lines))

        # Detect hunk patterns
        patterns.extend(self._detect_hunk_patterns(lines))

        # Detect change density
        patterns.extend(self._detect_change_density(lines))

        return patterns

    def _detect_file_changes(self, lines: list[str]) -> list[ContentPattern]:
        """Detect different types of file changes."""
        patterns = []

        for i, line in enumerate(lines):
            if line.startswith("diff --git"):
                # Analyze file change type
                change_type = "modification"  # Default

                # Look ahead for change indicators
                for j in range(i, min(i + 10, len(lines))):
                    next_line = lines[j]
                    if next_line.startswith("new file mode"):
                        change_type = "addition"
                        break
                    if next_line.startswith("deleted file mode"):
                        change_type = "deletion"
                        break
                    if next_line.startswith("rename"):
                        change_type = "rename"
                        break

                # Find end of this file's diff
                file_end = len(lines) - 1
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith("diff --git"):
                        file_end = j - 1
                        break

                patterns.append(
                    ContentPattern(
                        pattern_type=f"file_{change_type}",
                        confidence=0.95,
                        start_line=i,
                        end_line=file_end,
                        metadata={"change_type": change_type},
                        importance=0.9,
                    )
                )

        return patterns

    def _detect_hunk_patterns(self, lines: list[str]) -> list[ContentPattern]:
        """Detect hunk patterns within diffs."""
        patterns = []

        for i, line in enumerate(lines):
            if line.startswith("@@"):
                # Parse hunk header
                if hunk_match := re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", line):
                    old_start = int(hunk_match.group(1))
                    old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
                    new_start = int(hunk_match.group(3))
                    new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1

                    # Find end of hunk
                    hunk_end = i
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith(("@@", "diff --git")):
                            hunk_end = j - 1
                            break
                        hunk_end = j

                    patterns.append(
                        ContentPattern(
                            pattern_type="diff_hunk",
                            confidence=0.9,
                            start_line=i,
                            end_line=hunk_end,
                            metadata={
                                "old_start": old_start,
                                "old_count": old_count,
                                "new_start": new_start,
                                "new_count": new_count,
                                "hunk_size": hunk_end - i + 1,
                            },
                            importance=0.8,
                        )
                    )

        return patterns

    def _detect_change_density(self, lines: list[str]) -> list[ContentPattern]:
        """Detect areas of high change density."""
        patterns: list[ContentPattern] = []

        change_lines = []
        for i, line in enumerate(lines):
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                change_lines.append(i)

        if len(change_lines) < MIN_CHANGE_LINES_FOR_DENSITY:
            return patterns

        # Find clusters of changes using shared utility
        clusters = cluster_nearby_indices(
            change_lines, CHANGE_LINE_PROXIMITY_THRESHOLD, MIN_CLUSTER_SIZE
        )

        # Create patterns for dense change areas
        for cluster in clusters:
            patterns.append(
                ContentPattern(
                    pattern_type="high_change_density",
                    confidence=0.7,
                    start_line=cluster[0],
                    end_line=cluster[-1],
                    metadata={
                        "change_count": len(cluster),
                        "density": len(cluster) / (cluster[-1] - cluster[0] + 1),
                    },
                    importance=0.75,
                )
            )

        return patterns

    def get_pattern_types(self) -> set[str]:
        """Get Git diff pattern types."""
        return {
            "file_addition",
            "file_deletion",
            "file_modification",
            "file_rename",
            "diff_hunk",
            "high_change_density",
        }


class AdvancedContentAnalyzer:
    """Enhanced content analyzer with pattern detection and intelligence."""

    def __init__(self) -> None:
        """Initialize the advanced analyzer."""
        self.base_analyzer = ContentAnalyzer()
        self.pattern_detectors: dict[ContentType, PatternDetector] = {
            ContentType.PYTHON_CODE: PythonPatternDetector(),
            ContentType.GIT_DIFF: GitDiffPatternDetector(),
        }
        self.logger = get_logger("AdvancedContentAnalyzer")

    def analyze(self, content: str) -> ContentCharacteristics:
        """Perform comprehensive content analysis."""
        lines = content.split("\n")

        # Create metrics object
        metrics = self._create_metrics(lines)

        # Content type and structural analysis
        content_type = self._detect_content_type(content, lines)
        boundaries = self.base_analyzer.analyze_structure(content)
        patterns = self._detect_patterns(content, lines, content_type)

        # Complexity assessment
        params = ComplexityParams(
            lines=lines,
            boundaries=boundaries,
            patterns=patterns,
            content_type=content_type,
            indentation_levels=metrics.indentation_levels,
        )
        complexity = self._assess_complexity(params)

        # Generate characteristics
        characteristics = ContentCharacteristics(
            content_type=content_type,
            complexity=complexity,
            metrics=metrics,
            structural_boundaries=boundaries,
            detected_patterns=patterns,
            similarity_hash=self._generate_similarity_hash(content),
            metadata={
                "pattern_types": [p.pattern_type for p in patterns],
                "boundary_types": [b.structure_type.value for b in boundaries],
                "analysis_version": "1.0",
            },
        )

        self.logger.debug(
            "Content analysis complete",
            content_type=content_type.value,
            complexity=complexity.value,
            boundaries=len(boundaries),
            patterns=len(patterns),
            lines=metrics.total_lines,
        )

        return characteristics

    def _create_metrics(self, lines: list[str]) -> ContentMetrics:
        """Create content metrics from lines."""
        total_lines = len(lines)
        non_empty_lines = len([line for line in lines if line.strip()])
        avg_line_length = sum(len(line) for line in lines) / max(1, total_lines)
        max_line_length = max(len(line) for line in lines) if lines else 0
        indentation_levels = self._analyze_indentation(lines)

        return ContentMetrics(
            total_lines=total_lines,
            non_empty_lines=non_empty_lines,
            average_line_length=avg_line_length,
            max_line_length=max_line_length,
            indentation_levels=indentation_levels,
        )

    def _detect_content_type(self, content: str, lines: list[str]) -> ContentType:
        """Detect the primary content type."""
        # Define detection functions for each type
        detectors = [
            (self._is_git_diff, ContentType.GIT_DIFF),
            (self._is_python_code, ContentType.PYTHON_CODE),
            (self._is_markdown, ContentType.MARKDOWN),
            (lambda c, lines: self._is_json(c), ContentType.JSON_DATA),
            (self._is_log_file, ContentType.LOG_FILE),
            (self._is_shell_script, ContentType.SHELL_SCRIPT),
            (self._is_sql_query, ContentType.SQL_QUERY),
            (self._is_config_file, ContentType.CONFIG_FILE),
        ]

        # Apply detectors in priority order
        for detector_func, content_type in detectors:
            if detector_func(content, lines):
                return content_type

        return ContentType.PLAIN_TEXT

    def _is_git_diff(self, _content: str, lines: list[str]) -> bool:
        """Check if content is a Git diff."""
        return any(line.startswith(("diff --git", "@@", "index ")) for line in lines[:10])

    def _is_python_code(self, _content: str, lines: list[str]) -> bool:
        """Check if content is Python code."""
        python_indicators = sum(
            1
            for line in lines[:20]
            if re.match(r"^\s*(def|class|import|from|if __name__|#.*python)", line, re.IGNORECASE)
        )
        return python_indicators >= MIN_PYTHON_INDICATORS

    def _is_markdown(self, _content: str, lines: list[str]) -> bool:
        """Check if content is Markdown."""
        markdown_indicators = sum(1 for line in lines[:10] if re.match(r"^#{1,6}\s+", line))
        return markdown_indicators >= MIN_MARKDOWN_INDICATORS

    def _is_json(self, content: str) -> bool:
        """Check if content is valid JSON."""
        try:
            json.loads(content)
            return True
        except json.JSONDecodeError:
            return False

    def _is_log_file(self, _content: str, lines: list[str]) -> bool:
        """Check if content is a log file."""
        log_patterns = [
            r"\d{4}-\d{2}-\d{2}[\s\d:,-]+",  # Timestamp patterns
            r"(ERROR|WARN|INFO|DEBUG):",  # Log levels
            r"\[\d{4}-\d{2}-\d{2}.*?\]",  # Bracketed timestamps
        ]
        log_matches = sum(
            1 for pattern in log_patterns for line in lines[:20] if re.search(pattern, line)
        )
        return log_matches >= MIN_LOG_MATCHES

    def _is_shell_script(self, _content: str, lines: list[str]) -> bool:
        """Check if content is a shell script."""
        return (lines and lines[0].startswith("#!") and SHELL_SCRIPT_INDICATOR in lines[0]) or sum(
            1 for line in lines[:10] if re.match(r"^\s*(export|echo|cd|ls|grep)\s", line)
        ) >= MIN_SHELL_INDICATORS

    def _is_sql_query(self, _content: str, lines: list[str]) -> bool:
        """Check if content is SQL."""
        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]
        sql_matches = sum(
            1 for keyword in sql_keywords for line in lines[:10] if keyword.upper() in line.upper()
        )
        return sql_matches >= MIN_SQL_MATCHES

    def _is_config_file(self, _content: str, lines: list[str]) -> bool:
        """Check if content is a configuration file."""
        config_patterns = [
            r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*[=:]",  # key=value or key: value
            r"^\s*\[[^\]]+\]",  # [section]
            r"^\s*#.*",  # Comments
        ]
        config_matches = sum(
            1 for pattern in config_patterns for line in lines[:20] if re.match(pattern, line)
        )
        return config_matches >= MIN_CONFIG_MATCHES

    def _analyze_indentation(self, lines: list[str]) -> list[int]:
        """Analyze indentation patterns."""
        indentations = []
        for line in lines:
            if line.strip():  # Only non-empty lines
                indent = len(line) - len(line.lstrip())
                indentations.append(indent)

        # Return unique indentation levels sorted
        return sorted(list(set(indentations)))

    def _detect_patterns(
        self, content: str, lines: list[str], content_type: ContentType
    ) -> list[ContentPattern]:
        """Detect patterns using appropriate detectors."""
        patterns = []

        if content_type in self.pattern_detectors:
            detector = self.pattern_detectors[content_type]
            patterns.extend(detector.detect(content, lines))

        # Universal patterns (apply to all content types)
        patterns.extend(self._detect_universal_patterns(lines))

        return patterns

    def _detect_universal_patterns(self, lines: list[str]) -> list[ContentPattern]:
        """Detect universal patterns that apply to any content."""
        patterns = []

        # Long line blocks
        long_lines = [i for i, line in enumerate(lines) if len(line) > LONG_LINE_THRESHOLD]
        if len(long_lines) >= MIN_LONG_LINES_FOR_PATTERN:
            patterns.append(
                ContentPattern(
                    pattern_type="long_lines",
                    confidence=0.8,
                    start_line=long_lines[0],
                    end_line=long_lines[-1],
                    metadata={"long_line_count": len(long_lines)},
                    importance=0.4,
                )
            )

        # Repeated patterns
        line_frequencies: dict[str, list[int]] = {}
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > SUBSTANTIAL_LINE_THRESHOLD:  # Only consider substantial lines
                if stripped in line_frequencies:
                    line_frequencies[stripped].append(i)
                else:
                    line_frequencies[stripped] = [i]

        # Find repeated patterns
        for line_content, occurrences in line_frequencies.items():
            if len(occurrences) >= MIN_REPETITIONS_FOR_PATTERN:
                patterns.append(
                    ContentPattern(
                        pattern_type="repeated_content",
                        confidence=0.7,
                        start_line=occurrences[0],
                        end_line=occurrences[-1],
                        metadata={
                            "repetitions": len(occurrences),
                            "content_sample": line_content[:50],
                        },
                        importance=0.3,
                    )
                )

        return patterns

    def _assess_complexity(self, params: ComplexityParams) -> ContentComplexity:
        """Assess overall content complexity."""
        total_lines = len(params.lines)
        complexity_score = 0.0

        # Base complexity from content type
        type_complexity = {
            ContentType.PLAIN_TEXT: 0.1,
            ContentType.MARKDOWN: 0.2,
            ContentType.CONFIG_FILE: 0.3,
            ContentType.LOG_FILE: 0.4,
            ContentType.SHELL_SCRIPT: 0.5,
            ContentType.JSON_DATA: 0.6,
            ContentType.SQL_QUERY: 0.7,
            ContentType.GIT_DIFF: 0.8,
            ContentType.PYTHON_CODE: 0.9,
            ContentType.MIXED_CONTENT: 1.0,
        }
        complexity_score += type_complexity.get(params.content_type, 0.5)

        # Structural complexity
        boundary_density = len(params.boundaries) / max(1, total_lines)
        complexity_score += min(0.3, boundary_density * 10)

        # Pattern complexity
        pattern_diversity = len(set(p.pattern_type for p in params.patterns))
        complexity_score += min(0.2, pattern_diversity * 0.02)

        # Indentation complexity
        if len(params.indentation_levels) > 1:
            max_indent = max(params.indentation_levels) - min(params.indentation_levels)
            complexity_score += min(0.2, max_indent * 0.01)

        # Line length variance
        if params.lines:
            line_lengths = [len(line) for line in params.lines]
            avg_length = sum(line_lengths) / len(line_lengths)
            variance = sum((length - avg_length) ** 2 for length in line_lengths) / len(
                line_lengths
            )
            complexity_score += min(0.1, variance / 10000)  # Normalize variance

        # Map score to complexity level
        if complexity_score < COMPLEXITY_SIMPLE_THRESHOLD:
            return ContentComplexity.SIMPLE
        elif complexity_score < COMPLEXITY_MODERATE_THRESHOLD:
            return ContentComplexity.MODERATE
        elif complexity_score < COMPLEXITY_COMPLEX_THRESHOLD:
            return ContentComplexity.COMPLEX
        else:
            return ContentComplexity.HIGHLY_COMPLEX

    def _generate_similarity_hash(self, content: str) -> str:
        """Generate a hash for content similarity matching."""
        # Use structural elements for similarity, not exact content
        lines = content.split("\n")

        # Extract structural signature
        structural_elements = []
        for line in lines:
            if stripped := line.strip():
                # Add line length and first few chars as signature
                structural_elements.append(f"{len(line)}:{stripped[:10]}")

        # Create hash from structural signature
        signature = "|".join(structural_elements[:100])  # Limit to first 100 lines
        return hashlib.sha256(signature.encode(), usedforsecurity=False).hexdigest()[:16]
