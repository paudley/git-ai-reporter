# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Advanced chunking strategies for sophisticated content fitting.

This module implements cutting-edge chunking strategies that go beyond simple
overlap-based approaches, using semantic analysis, structural awareness, and
adaptive algorithms to provide superior content fitting while maintaining
perfect data integrity.
"""

from dataclasses import dataclass
from enum import Enum
import math
import re
from typing import Any

from .logging import get_logger
from .prompt_fitting import ContentFitter
from .prompt_fitting import FittingMetrics
from .prompt_fitting import FittingResult
from .prompt_fitting import FittingStrategy
from .prompt_fitting import PromptFittingConfig
from .prompt_fitting import TokenCounter
from .validation import DataIntegrityValidator

# Constants for magic value replacements
MIN_COMMENT_BLOCK_LINES = 3
MIN_PARAGRAPH_LINES = 2
JSON_OPEN_BRACE = "{"
JSON_CLOSE_BRACE = "}"
HIGH_IMPORTANCE_THRESHOLD = 0.8
MAX_HEADER_LEVEL = 6
BOUNDARY_FLEXIBILITY_MULTIPLIER = 1.5
COMPLEXITY_THRESHOLD = 0.6


@dataclass
class BoundaryChunkingConfig:
    """Configuration for boundary-aware chunking."""

    lines: list[str]
    boundaries: list["StructuralBoundary"]
    target_chunk_size: int
    overlap_ratio: float
    importance_threshold: float


class StructureType(Enum):
    """Types of structural boundaries detected in content."""

    FUNCTION_DEF = "function_definition"
    CLASS_DEF = "class_definition"
    IMPORT_BLOCK = "import_block"
    COMMENT_BLOCK = "comment_block"
    GIT_DIFF_FILE = "git_diff_file"
    GIT_DIFF_HUNK = "git_diff_hunk"
    MARKDOWN_SECTION = "markdown_section"
    JSON_OBJECT = "json_object"
    PARAGRAPH = "paragraph"
    LINE_BLOCK = "line_block"


@dataclass
class StructuralBoundary:
    """Represents a structural boundary in content."""

    start_line: int
    end_line: int
    structure_type: StructureType
    importance: float  # 0.0-1.0, higher means more important to keep together
    metadata: dict[str, Any]

    @property
    def size(self) -> int:
        """Get size in lines."""
        return self.end_line - self.start_line + 1

    def contains(self, line_num: int) -> bool:
        """Check if line number is within this boundary."""
        return self.start_line <= line_num <= self.end_line

    def overlaps(self, other: "StructuralBoundary") -> bool:
        """Check if this boundary overlaps with another."""
        return not (self.end_line < other.start_line or other.end_line < self.start_line)


class ContentAnalyzer:
    """Advanced analyzer for detecting content structure and semantics."""

    def __init__(self) -> None:
        """Initialize the content analyzer."""
        self.logger = get_logger("ContentAnalyzer")

    def analyze_structure(self, content: str) -> list[StructuralBoundary]:
        """Analyze content and identify structural boundaries.

        Args:
            content: Content to analyze

        Returns:
            List of structural boundaries sorted by start line
        """
        lines = content.split("\n")
        boundaries = []

        # Detect different types of structures
        boundaries.extend(self._detect_python_structures(lines))
        boundaries.extend(self._detect_git_diff_structures(lines))
        boundaries.extend(self._detect_markdown_structures(lines))
        boundaries.extend(self._detect_comment_blocks(lines))
        boundaries.extend(self._detect_json_structures(lines))
        boundaries.extend(self._detect_paragraph_structures(lines))

        # Sort by start line and resolve conflicts
        boundaries.sort(key=lambda b: (b.start_line, -b.importance))
        resolved_boundaries = self._resolve_boundary_conflicts(boundaries)

        self.logger.debug(f"Detected {len(resolved_boundaries)} structural boundaries")
        return resolved_boundaries

    def _detect_python_structures(self, lines: list[str]) -> list[StructuralBoundary]:
        """Detect Python code structures."""
        boundaries = []

        # Detect functions and classes
        for i, line in enumerate(lines):
            stripped = line.strip()

            # Function definitions
            if re.match(r"^def\s+\w+\s*\(", stripped):
                # Find end of function by looking for next def/class or end of indentation
                end_line = self._find_python_block_end(lines, i)
                boundaries.append(
                    StructuralBoundary(
                        start_line=i,
                        end_line=end_line,
                        structure_type=StructureType.FUNCTION_DEF,
                        importance=0.9,  # High importance - keep functions together
                        metadata={
                            "function_name": (
                                match.group(1)
                                if (match := re.match(r"^def\s+(\w+)", stripped))
                                else "unknown"
                            )
                        },
                    )
                )

            # Class definitions
            elif re.match(r"^class\s+\w+", stripped):
                end_line = self._find_python_block_end(lines, i)
                boundaries.append(
                    StructuralBoundary(
                        start_line=i,
                        end_line=end_line,
                        structure_type=StructureType.CLASS_DEF,
                        importance=0.95,  # Very high importance
                        metadata={
                            "class_name": (
                                match.group(1)
                                if (match := re.match(r"^class\s+(\w+)", stripped))
                                else "unknown"
                            )
                        },
                    )
                )

        # Detect import blocks
        boundaries.extend(self._detect_import_blocks(lines))

        return boundaries

    def _detect_import_blocks(self, lines: list[str]) -> list[StructuralBoundary]:
        """Detect import blocks in the code."""
        boundaries = []
        import_start = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r"^(import|from)\s+", stripped):
                if import_start is None:
                    import_start = i
                continue

            if import_start is not None:
                block_boundaries = self._process_import_block_end(import_start, i, stripped)
                boundaries.extend(block_boundaries)
                if self._should_end_import_block(import_start, stripped):
                    import_start = None

        # Handle import block at end of file
        if import_start is not None:
            boundaries.append(
                StructuralBoundary(
                    start_line=import_start,
                    end_line=len(lines) - 1,
                    structure_type=StructureType.IMPORT_BLOCK,
                    importance=0.8,
                    metadata={"import_count": len(lines) - import_start},
                )
            )

        return boundaries

    def _process_import_block_end(
        self, import_start: int, current_line: int, stripped: str
    ) -> list[StructuralBoundary]:
        """Process the end of an import block."""
        if self._should_end_import_block(import_start, stripped):
            return [
                StructuralBoundary(
                    start_line=import_start,
                    end_line=current_line - 1,
                    structure_type=StructureType.IMPORT_BLOCK,
                    importance=0.8,
                    metadata={"import_count": current_line - import_start},
                )
            ]
        return []

    def _should_end_import_block(self, import_start: int | None, stripped: str) -> bool:
        """Check if current line should end an import block."""
        return (
            import_start is not None
            and bool(stripped)
            and not re.match(r"^(import|from)\s+", stripped)
        )

    def _detect_git_diff_structures(self, lines: list[str]) -> list[StructuralBoundary]:
        """Detect Git diff structures."""
        boundaries = []

        current_file = None
        current_hunk = None

        for i, line in enumerate(lines):
            # Git diff file header
            if line.startswith("diff --git"):
                # Close previous file if exists
                if current_file is not None:
                    boundaries.append(
                        StructuralBoundary(
                            start_line=current_file,
                            end_line=i - 1,
                            structure_type=StructureType.GIT_DIFF_FILE,
                            importance=0.85,
                            metadata={"file_type": "diff"},
                        )
                    )
                current_file = i

            # Git diff hunk header
            elif line.startswith("@@"):
                if current_hunk is not None:
                    boundaries.append(
                        StructuralBoundary(
                            start_line=current_hunk,
                            end_line=i - 1,
                            structure_type=StructureType.GIT_DIFF_HUNK,
                            importance=0.7,
                            metadata={"hunk_type": "diff"},
                        )
                    )
                current_hunk = i

        # Close final file and hunk
        if current_file is not None:
            boundaries.append(
                StructuralBoundary(
                    start_line=current_file,
                    end_line=len(lines) - 1,
                    structure_type=StructureType.GIT_DIFF_FILE,
                    importance=0.85,
                    metadata={"file_type": "diff"},
                )
            )

        if current_hunk is not None:
            boundaries.append(
                StructuralBoundary(
                    start_line=current_hunk,
                    end_line=len(lines) - 1,
                    structure_type=StructureType.GIT_DIFF_HUNK,
                    importance=0.7,
                    metadata={"hunk_type": "diff"},
                )
            )

        return boundaries

    def _detect_markdown_structures(self, lines: list[str]) -> list[StructuralBoundary]:
        """Detect Markdown structures."""
        boundaries = []

        for i, line in enumerate(lines):
            # Markdown headers
            if re.match(r"^#{1,6}\s+", line.strip()):
                # Find section end (next header of same or higher level, or end of content)
                match = re.match(r"^(#+)", line.strip())
                header_level = len(match.group(1)) if match else 1
                end_line = len(lines) - 1  # Default to end

                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if re.match(r"^#{1,6}\s+", next_line):
                        next_match = re.match(r"^(#+)", next_line)
                        if (len(next_match.group(1)) if next_match else 1) <= header_level:
                            end_line = j - 1
                            break

                boundaries.append(
                    StructuralBoundary(
                        start_line=i,
                        end_line=end_line,
                        structure_type=StructureType.MARKDOWN_SECTION,
                        importance=0.8,
                        metadata={
                            "header_level": header_level,
                            "title": line.strip().lstrip("#").strip(),
                        },
                    )
                )

        return boundaries

    def _detect_comment_blocks(self, lines: list[str]) -> list[StructuralBoundary]:
        """Detect comment blocks."""
        boundaries = []
        comment_start = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Python/Shell style comments
            is_comment = (
                stripped.startswith("#")
                or stripped.startswith("//")
                or stripped.startswith("/*")
                or stripped.startswith("*")
                or stripped.startswith('"""')
                or stripped.startswith("'''")
            )

            if is_comment:
                if comment_start is None:
                    comment_start = i
            else:
                if (
                    comment_start is not None and i - comment_start >= MIN_COMMENT_BLOCK_LINES
                ):  # At least 3 lines
                    boundaries.append(
                        StructuralBoundary(
                            start_line=comment_start,
                            end_line=i - 1,
                            structure_type=StructureType.COMMENT_BLOCK,
                            importance=0.6,
                            metadata={"comment_lines": i - comment_start},
                        )
                    )
                comment_start = None

        # Handle comment block at end
        if comment_start is not None and len(lines) - comment_start >= MIN_COMMENT_BLOCK_LINES:
            boundaries.append(
                StructuralBoundary(
                    start_line=comment_start,
                    end_line=len(lines) - 1,
                    structure_type=StructureType.COMMENT_BLOCK,
                    importance=0.6,
                    metadata={"comment_lines": len(lines) - comment_start},
                )
            )

        return boundaries

    def _detect_json_structures(self, lines: list[str]) -> list[StructuralBoundary]:
        """Detect JSON object structures."""
        boundaries = []
        brace_stack = []

        for i, line in enumerate(lines):
            for char in line:
                if char == JSON_OPEN_BRACE:
                    brace_stack.append(i)
                elif char == JSON_CLOSE_BRACE and brace_stack:
                    start_line = brace_stack.pop()
                    if not brace_stack:  # Top-level object closed
                        boundaries.append(
                            StructuralBoundary(
                                start_line=start_line,
                                end_line=i,
                                structure_type=StructureType.JSON_OBJECT,
                                importance=0.75,
                                metadata={"object_size": i - start_line + 1},
                            )
                        )

        return boundaries

    def _detect_paragraph_structures(self, lines: list[str]) -> list[StructuralBoundary]:
        """Detect paragraph structures (text separated by blank lines)."""
        boundaries = []
        paragraph_start = None

        for i, line in enumerate(lines):
            if not line.strip():
                if (
                    paragraph_start is not None and i - paragraph_start >= MIN_PARAGRAPH_LINES
                ):  # At least 2 lines
                    boundaries.append(
                        StructuralBoundary(
                            start_line=paragraph_start,
                            end_line=i - 1,
                            structure_type=StructureType.PARAGRAPH,
                            importance=0.5,
                            metadata={"paragraph_lines": i - paragraph_start},
                        )
                    )
                paragraph_start = None
            elif paragraph_start is None:
                paragraph_start = i
                if (
                    paragraph_start is not None and i - paragraph_start >= MIN_PARAGRAPH_LINES
                ):  # At least 2 lines
                    boundaries.append(
                        StructuralBoundary(
                            start_line=paragraph_start,
                            end_line=i - 1,
                            structure_type=StructureType.PARAGRAPH,
                            importance=0.5,
                            metadata={"paragraph_lines": i - paragraph_start},
                        )
                    )
                paragraph_start = None

        # Handle final paragraph
        if paragraph_start is not None and len(lines) - paragraph_start >= MIN_PARAGRAPH_LINES:
            boundaries.append(
                StructuralBoundary(
                    start_line=paragraph_start,
                    end_line=len(lines) - 1,
                    structure_type=StructureType.PARAGRAPH,
                    importance=0.5,
                    metadata={"paragraph_lines": len(lines) - paragraph_start},
                )
            )

        return boundaries

    def _find_python_block_end(self, lines: list[str], start_line: int) -> int:
        """Find the end of a Python code block based on indentation."""
        if start_line >= len(lines):
            return start_line

        # Get base indentation level
        base_indent = len(lines[start_line]) - len(lines[start_line].lstrip())

        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if not line.strip():  # Skip blank lines
                continue

            # If we find a line at the same or lower indentation level that's not blank
            if (current_indent := len(line) - len(line.lstrip())) <= base_indent:
                # Check if it's another def/class (same level) or something else
                stripped = line.strip()
                if current_indent == base_indent and (
                    stripped.startswith("def ") or stripped.startswith("class ")
                ):
                    return i - 1
                elif current_indent < base_indent:
                    return i - 1

        return len(lines) - 1

    def _resolve_boundary_conflicts(
        self, boundaries: list[StructuralBoundary]
    ) -> list[StructuralBoundary]:
        """Resolve overlapping boundaries by keeping the most important ones."""
        if not boundaries:
            return boundaries

        resolved = []
        current_boundary = boundaries[0]

        for boundary in boundaries[1:]:
            if current_boundary.overlaps(boundary):
                # Keep the more important boundary
                if boundary.importance > current_boundary.importance:
                    current_boundary = boundary
                # If same importance, keep the smaller (more specific) one
                elif (
                    boundary.importance == current_boundary.importance
                    and boundary.size < current_boundary.size
                ):
                    current_boundary = boundary
            else:
                resolved.append(current_boundary)
                current_boundary = boundary

        resolved.append(current_boundary)
        return resolved


class SemanticChunksFitter(ContentFitter):
    """Advanced fitter that creates chunks based on semantic boundaries.

    This fitter analyzes content structure and creates chunks that respect
    natural boundaries like function definitions, classes, paragraphs, etc.
    """

    def __init__(self, config: PromptFittingConfig, token_counter: TokenCounter):
        """Initialize semantic chunks fitter."""
        super().__init__(config, token_counter)
        self.analyzer = ContentAnalyzer()
        self.validator = DataIntegrityValidator(strict_mode=True)
        self.logger = get_logger("SemanticChunksFitter")

    async def fit_content(
        self, content: str, target_tokens: int
    ) -> FittingResult["SemanticChunksFitter"]:
        """Fit content using semantic boundary analysis."""
        if (original_tokens := await self.token_counter.count_tokens(content)) <= target_tokens:
            return FittingResult(
                fitted_content=content,
                original_size=original_tokens,
                fitted_size=original_tokens,
                strategy_used=FittingStrategy.SEMANTIC_COMPRESSION,
                data_preserved=True,
                metadata={"semantic_chunking": False},
            )

        # Analyze content structure
        boundaries = self.analyzer.analyze_structure(content)
        self.logger.info(f"Detected {len(boundaries)} semantic boundaries")

        # Create semantic chunks
        chunks = self._create_semantic_chunks(content, boundaries, target_tokens)

        # Validate data integrity
        validation_result = self.validator.validate_chunks_coverage(content, chunks)
        validation_result.raise_if_invalid()

        # Prepare final content
        fitted_content = self._prepare_semantic_content(chunks, boundaries)
        fitted_tokens = await self.token_counter.count_tokens(fitted_content)

        return FittingResult(
            fitted_content=fitted_content,
            original_size=original_tokens,
            fitted_size=fitted_tokens,
            strategy_used=FittingStrategy.SEMANTIC_COMPRESSION,
            data_preserved=True,
            metadata={
                "semantic_chunking": True,
                "boundaries_detected": len(boundaries),
                "chunks_created": len(chunks),
                "boundary_types": list(set(b.structure_type.value for b in boundaries)),
            },
            metrics=FittingMetrics(
                chunks_created=len(chunks),
                coverage_percentage=validation_result.coverage_percentage,
            ),
        )

    def _create_semantic_chunks(
        self, content: str, boundaries: list[StructuralBoundary], target_tokens: int
    ) -> list[str]:
        """Create chunks that respect semantic boundaries."""
        lines = content.split("\n")
        chunks = []
        current_chunk_lines = []
        current_chunk_tokens = 0

        # Process lines with explicit increment control
        i = 0
        for _ in range(len(lines)):
            if i >= len(lines):
                break
            # Check if we're at the start of an important boundary
            boundary_at_line = self._find_boundary_at_line(boundaries, i)

            if boundary_at_line and boundary_at_line.importance >= HIGH_IMPORTANCE_THRESHOLD:
                # High-importance boundary - try to keep it together
                boundary_content = "\n".join(
                    lines[boundary_at_line.start_line : boundary_at_line.end_line + 1]
                )
                boundary_tokens = len(boundary_content) // 4  # Rough estimate

                # If boundary fits in current chunk, add it
                if current_chunk_tokens + boundary_tokens <= target_tokens * 0.8:
                    current_chunk_lines.extend(
                        lines[boundary_at_line.start_line : boundary_at_line.end_line + 1]
                    )
                    current_chunk_tokens += boundary_tokens
                    i = boundary_at_line.end_line + 1
                else:
                    # Start new chunk with this boundary
                    if current_chunk_lines:
                        chunks.append("\n".join(current_chunk_lines))

                    current_chunk_lines = lines[
                        boundary_at_line.start_line : boundary_at_line.end_line + 1
                    ]
                    current_chunk_tokens = boundary_tokens
                    i = boundary_at_line.end_line + 1
            else:
                # Regular line or low-importance boundary
                line = lines[i]
                line_tokens = len(line) // 4  # Rough estimate

                if current_chunk_tokens + line_tokens > target_tokens * 0.8 and current_chunk_lines:
                    # Start new chunk
                    chunks.append("\n".join(current_chunk_lines))
                    current_chunk_lines = [line]
                    current_chunk_tokens = line_tokens
                else:
                    current_chunk_lines.append(line)
                    current_chunk_tokens += line_tokens

                i += 1

        # Add final chunk
        if current_chunk_lines:
            chunks.append("\n".join(current_chunk_lines))

        # Ensure we have chunks and add overlap for continuity
        if len(chunks) > 1:
            chunks = self._add_semantic_overlap(chunks, lines)

        return chunks

    def _find_boundary_at_line(
        self, boundaries: list[StructuralBoundary], line_num: int
    ) -> StructuralBoundary | None:
        """Find boundary that starts at the given line number."""
        for boundary in boundaries:
            if boundary.start_line == line_num:
                return boundary
        return None

    def _add_semantic_overlap(self, chunks: list[str], _all_lines: list[str]) -> list[str]:
        """Add semantic overlap between chunks for continuity."""
        if len(chunks) <= 1:
            return chunks

        overlapped_chunks = [chunks[0]]  # First chunk unchanged

        for i in range(1, len(chunks)):
            current_chunk_lines = chunks[i].split("\n")
            prev_chunk_lines = chunks[i - 1].split("\n")

            # Add last few lines of previous chunk for context
            overlap_size = min(3, len(prev_chunk_lines) // 4)  # Up to 3 lines or 25%
            overlap_lines = prev_chunk_lines[-overlap_size:] if overlap_size > 0 else []

            # Combine overlap with current chunk
            overlapped_content = "\n".join(
                overlap_lines + ["--- CONTINUATION ---"] + current_chunk_lines
            )
            overlapped_chunks.append(overlapped_content)

        return overlapped_chunks

    def _prepare_semantic_content(
        self, chunks: list[str], boundaries: list[StructuralBoundary]
    ) -> str:
        """Prepare semantic chunks with descriptive headers."""
        if len(chunks) == 1:
            return chunks[0]

        prepared_chunks = []
        for i, chunk in enumerate(chunks):
            # Create descriptive header based on content
            chunk_lines = chunk.split("\n")
            first_line = next((line.strip() for line in chunk_lines if line.strip()), "")

            # Try to identify the type of content in this chunk
            chunk_type = "Content"
            if first_line.startswith("def "):
                chunk_type = "Function Definition"
            elif first_line.startswith("class "):
                chunk_type = "Class Definition"
            elif first_line.startswith("diff --git"):
                chunk_type = "Git Diff"
            elif first_line.startswith("#"):
                if first_line.count("#") <= MAX_HEADER_LEVEL:
                    chunk_type = "Markdown Section"
                else:
                    chunk_type = "Comment Block"
            elif any(line.strip().startswith(("import ", "from ")) for line in chunk_lines[:5]):
                chunk_type = "Import Block"

            header = f"--- Semantic Chunk {i + 1}: {chunk_type} ({len(chunk_lines)} lines) ---"
            prepared_chunks.append(f"{header}\n{chunk}")

        boundary_summary = (
            f"\n\n--- SEMANTIC ANALYSIS: {len(prepared_chunks)} chunks created "
            f"from {len(boundaries)} structural boundaries ---"
        )
        return "\n\n".join(prepared_chunks) + boundary_summary

    def validate_preservation(self, original: str, fitted: str) -> bool:
        """Validate semantic chunk preservation."""
        try:
            # Use comprehensive validation
            validation_result = self.validator.validate_complete(original, fitted)
            return validation_result.is_valid
        except (ValueError, TypeError, AttributeError):
            return False


class AdaptiveChunksFitter(ContentFitter):
    """Adaptive chunking strategy that dynamically adjusts based on content analysis."""

    def __init__(self, config: PromptFittingConfig, token_counter: TokenCounter):
        """Initialize adaptive chunks fitter."""
        super().__init__(config, token_counter)
        self.analyzer = ContentAnalyzer()
        self.validator = DataIntegrityValidator(strict_mode=True)
        self.logger = get_logger("AdaptiveChunksFitter")

    async def fit_content(
        self, content: str, target_tokens: int
    ) -> FittingResult["AdaptiveChunksFitter"]:
        """Fit content using adaptive chunking based on content analysis."""
        if (original_tokens := await self.token_counter.count_tokens(content)) <= target_tokens:
            return FittingResult(
                fitted_content=content,
                original_size=original_tokens,
                fitted_size=original_tokens,
                strategy_used=FittingStrategy.OVERLAPPING_CHUNKS,
                data_preserved=True,
                metadata={"adaptive_chunking": False},
            )

        # Analyze content to determine optimal strategy
        analysis = self._analyze_content_characteristics(content)
        chunk_strategy = self._select_optimal_chunking(analysis, target_tokens, original_tokens)

        self.logger.info(
            f"Selected {chunk_strategy['name']} strategy for content "
            f"(complexity: {analysis['complexity']:.2f})"
        )

        # Apply selected chunking strategy
        chunks = await self._apply_chunking_strategy(content, chunk_strategy, target_tokens)

        # Validate and prepare result
        validation_result = self.validator.validate_chunks_coverage(content, chunks)
        validation_result.raise_if_invalid()

        fitted_content = self._prepare_adaptive_content(chunks, chunk_strategy)
        fitted_tokens = await self.token_counter.count_tokens(fitted_content)

        return FittingResult(
            fitted_content=fitted_content,
            original_size=original_tokens,
            fitted_size=fitted_tokens,
            strategy_used=FittingStrategy.OVERLAPPING_CHUNKS,
            data_preserved=True,
            metadata={
                "adaptive_chunking": True,
                "strategy_selected": chunk_strategy["name"],
                "content_analysis": analysis,
                "chunks_created": len(chunks),
            },
            metrics=FittingMetrics(
                chunks_created=len(chunks),
                coverage_percentage=validation_result.coverage_percentage,
            ),
        )

    def _analyze_content_characteristics(self, content: str) -> dict[str, Any]:
        """Analyze content to determine its characteristics."""
        lines = content.split("\n")

        # Basic metrics
        total_lines = len(lines)
        non_empty_lines = len([line for line in lines if line.strip()])
        avg_line_length = sum(len(line) for line in lines) / max(1, total_lines)

        # Structure analysis
        boundaries = self.analyzer.analyze_structure(content)

        # Content type detection
        has_code = any(
            re.match(r"^(def|class|import|from)\s+", line.strip()) for line in lines[:20]
        )
        has_git_diff = any(line.startswith(("diff --git", "@@", "+", "-")) for line in lines[:10])
        has_markdown = any(re.match(r"^#{1,6}\s+", line.strip()) for line in lines)
        has_json = JSON_OPEN_BRACE in content and JSON_CLOSE_BRACE in content

        # Calculate complexity score
        complexity_factors = [
            len(boundaries) / max(1, total_lines) * 10,  # Structural complexity
            avg_line_length / 100,  # Line length complexity
            1.0 if has_code else 0.0,  # Code complexity
            0.5 if has_git_diff else 0.0,  # Diff complexity
            0.3 if has_markdown else 0.0,  # Markdown structure
            0.4 if has_json else 0.0,  # JSON structure
        ]
        complexity = min(1.0, sum(complexity_factors))

        return {
            "total_lines": total_lines,
            "non_empty_lines": non_empty_lines,
            "avg_line_length": avg_line_length,
            "boundaries_count": len(boundaries),
            "has_code": has_code,
            "has_git_diff": has_git_diff,
            "has_markdown": has_markdown,
            "has_json": has_json,
            "complexity": complexity,
            "boundaries": boundaries,
        }

    def _select_optimal_chunking(
        self, analysis: dict[str, Any], target_tokens: int, original_tokens: int
    ) -> dict[str, Any]:
        """Select optimal chunking strategy based on content analysis."""

        complexity = analysis["complexity"]
        total_lines = analysis["total_lines"]

        # Strategy selection based on content characteristics
        if analysis["has_git_diff"]:
            # Git diff content - use diff-aware chunking
            return {
                "name": "diff_aware",
                "chunk_size": max(20, min(50, total_lines // 4)),
                "overlap_ratio": 0.25,
                "respect_boundaries": True,
                "boundary_importance_threshold": 0.7,
            }

        elif analysis["has_code"] and complexity > COMPLEXITY_THRESHOLD:
            # Complex code - use semantic chunking
            return {
                "name": "semantic_code",
                "chunk_size": max(15, min(40, total_lines // 5)),
                "overlap_ratio": 0.3,
                "respect_boundaries": True,
                "boundary_importance_threshold": 0.8,
            }

        elif analysis["boundaries_count"] > total_lines * 0.1:
            # Highly structured content - respect boundaries
            return {
                "name": "structure_aware",
                "chunk_size": max(10, min(30, total_lines // 3)),
                "overlap_ratio": 0.2,
                "respect_boundaries": True,
                "boundary_importance_threshold": 0.6,
            }

        else:
            # Simple content - use standard overlapping
            compression_ratio = original_tokens / target_tokens
            chunk_size = max(20, min(100, int(total_lines / math.sqrt(compression_ratio))))

            return {
                "name": "standard_overlap",
                "chunk_size": chunk_size,
                "overlap_ratio": 0.25,
                "respect_boundaries": False,
                "boundary_importance_threshold": 0.9,
            }

    async def _apply_chunking_strategy(
        self, content: str, strategy: dict[str, Any], _target_tokens: int
    ) -> list[str]:
        """Apply the selected chunking strategy."""

        lines = content.split("\n")
        chunk_size = strategy["chunk_size"]
        overlap_ratio = strategy["overlap_ratio"]

        if strategy["respect_boundaries"]:
            # Use boundary-aware chunking
            config = BoundaryChunkingConfig(
                lines=lines,
                boundaries=strategy["boundaries"],
                target_chunk_size=chunk_size,
                overlap_ratio=overlap_ratio,
                importance_threshold=strategy["boundary_importance_threshold"],
            )
            return self._create_boundary_aware_chunks(config)
        else:
            # Use standard overlapping chunks
            return self._create_standard_chunks(lines, chunk_size, overlap_ratio)

    def _create_boundary_aware_chunks(self, config: BoundaryChunkingConfig) -> list[str]:
        """Create chunks that respect structural boundaries."""
        chunks = []
        current_chunk_lines: list[str] = []

        # Process lines with explicit increment control
        i = 0
        for _ in range(len(config.lines)):
            if i >= len(config.lines):
                break
            # Check if we're at an important boundary
            boundary = self._find_boundary_at_line(config.boundaries, i)

            if boundary and boundary.importance >= config.importance_threshold:
                # Important boundary - try to keep it intact
                if len(current_chunk_lines) > 0:
                    # Finish current chunk
                    chunks.append("\n".join(current_chunk_lines))
                    current_chunk_lines = []

                # Add entire boundary as chunk (or start new chunk with it)
                boundary_lines = config.lines[boundary.start_line : boundary.end_line + 1]
                if (
                    len(boundary_lines)
                    <= config.target_chunk_size * BOUNDARY_FLEXIBILITY_MULTIPLIER
                ):  # Allow some flexibility
                    chunks.append("\n".join(boundary_lines))
                    i = boundary.end_line + 1
                else:
                    # Boundary too large, chunk it normally but start fresh
                    current_chunk_lines = boundary_lines[: config.target_chunk_size]
                    chunks.append("\n".join(current_chunk_lines))
                    i = boundary.start_line + config.target_chunk_size
                    current_chunk_lines = []
            else:
                # Regular line
                current_chunk_lines.append(config.lines[i])

                if len(current_chunk_lines) >= config.target_chunk_size:
                    chunks.append("\n".join(current_chunk_lines))

                    # Create overlap for next chunk
                    overlap_size = max(1, int(len(current_chunk_lines) * config.overlap_ratio))
                    current_chunk_lines = current_chunk_lines[-overlap_size:]

                i += 1

        # Add final chunk
        if current_chunk_lines:
            chunks.append("\n".join(current_chunk_lines))

        return chunks

    def _create_standard_chunks(
        self, lines: list[str], chunk_size: int, overlap_ratio: float
    ) -> list[str]:
        """Create standard overlapping chunks."""
        chunks = []
        chunk_step = max(1, int(chunk_size * (1 - overlap_ratio)))

        # Create chunks using range-based iteration
        for i in range(0, len(lines), chunk_step):
            chunk_end = min(i + chunk_size, len(lines))
            chunk_lines = lines[i:chunk_end]
            chunks.append("\n".join(chunk_lines))

        return chunks

    def _find_boundary_at_line(
        self, boundaries: list[StructuralBoundary], line_num: int
    ) -> StructuralBoundary | None:
        """Find boundary that starts at or contains the given line."""
        for boundary in boundaries:
            if boundary.start_line == line_num:
                return boundary
        return None

    def _prepare_adaptive_content(self, chunks: list[str], strategy: dict[str, Any]) -> str:
        """Prepare adaptive chunks with strategy information."""
        if len(chunks) == 1:
            return chunks[0]

        prepared_chunks = []
        for i, chunk in enumerate(chunks):
            header = f"--- Adaptive Chunk {i + 1} ({strategy['name']}) ---"
            prepared_chunks.append(f"{header}\n{chunk}")

        footer = f"\n\n--- ADAPTIVE STRATEGY: {strategy['name']} with {len(chunks)} chunks ---"
        return "\n\n".join(prepared_chunks) + footer

    def validate_preservation(self, original: str, fitted: str) -> bool:
        """Validate adaptive chunk preservation."""
        try:
            validation_result = self.validator.validate_complete(original, fitted)
            return validation_result.is_valid
        except (ValueError, TypeError, AttributeError):
            return False
