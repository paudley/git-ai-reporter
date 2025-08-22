# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Shared utilities for markdown processing and formatting.

This module provides common markdown operations used across the git-ai-reporter
application, including text wrapping, header formatting, YAML frontmatter
generation, and parsing utilities.
"""

from datetime import datetime
import re
import textwrap
from typing import Final

# Constants for markdown formatting
MAX_LINE_LENGTH: Final[int] = 80
INDENTED_LIST_MARKER: Final[str] = "  "
KEY_VALUE_SEPARATOR: Final[str] = ":"


def generate_yaml_frontmatter(
    title: str, description: str, created: datetime, updated: datetime
) -> str:
    """Generate YAML frontmatter for markdown files.

    Args:
        title: Document title.
        description: Document description.
        created: Creation date.
        updated: Last update date.

    Returns:
        Formatted YAML frontmatter.
    """
    return f"""---
title: {title}
description: {description}
created: {created.strftime('%Y-%m-%d')}
updated: {updated.strftime('%Y-%m-%d')}
format: markdown
---
"""


def format_week_header(start_date: datetime, end_date: datetime) -> str:
    """Format week header with week number.

    Args:
        start_date: Week start date.
        end_date: Week end date.

    Returns:
        Formatted week header.
    """
    week_num = start_date.isocalendar()[1]  # ISO week number
    return (
        f"## Week {week_num}: {start_date.strftime('%B %d')} - " f"{end_date.strftime('%B %d, %Y')}"
    )


def wrap_markdown_text(text: str, max_length: int = MAX_LINE_LENGTH) -> str:
    """Wrap text lines to specified maximum length while preserving markdown structure.

    This function intelligently wraps text while preserving markdown formatting
    like lists, headers, and code blocks.

    Args:
        text: Text to wrap.
        max_length: Maximum line length.

    Returns:
        Text with wrapped lines.
    """
    # Process each paragraph separately
    paragraphs = text.split("\n\n")
    wrapped_paragraphs = []

    for paragraph in paragraphs:
        # Skip lists, headers, and code blocks
        if _should_skip_paragraph_wrapping(paragraph):
            wrapped_paragraphs.append(paragraph)
        else:
            # Wrap normal paragraphs
            wrapped = textwrap.fill(
                paragraph,
                width=max_length,
                break_long_words=False,
                break_on_hyphens=False,
            )
            wrapped_paragraphs.append(wrapped)

    return "\n\n".join(wrapped_paragraphs)


def _should_skip_paragraph_wrapping(paragraph: str) -> bool:
    """Determine if a paragraph should skip text wrapping.

    Args:
        paragraph: Text paragraph to check.

    Returns:
        True if paragraph should not be wrapped.
    """
    return (
        paragraph.startswith(("- ", "* ", "#", "```"))
        or INDENTED_LIST_MARKER in paragraph[:4]  # Indented list items
    )


def parse_week_header(header: str) -> tuple[datetime, datetime] | None:
    """Extract dates from a week header.

    Args:
        header: Week header string like "## Week of 2024-01-01 to 2024-01-07".

    Returns:
        Tuple of (start_date, end_date) or None if parsing fails.
    """
    if date_match := re.match(r"## Week of (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})", header):
        start_date_str, end_date_str = date_match.groups()
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=None)
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=None)
        return start_date, end_date
    return None


def parse_changelog_section(section_text: str) -> dict[str, list[str]]:
    """Parse a changelog section into a dictionary of categories and items.

    Args:
        section_text: The string content of a changelog section.

    Returns:
        A dictionary where keys are category headings (e.g., "### Added")
        and values are lists of changelog item strings.
    """
    changes: dict[str, list[str]] = {}
    current_category = None
    for line in section_text.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("### "):
            current_category = stripped_line
            changes.setdefault(current_category, [])
        elif stripped_line.startswith("- ") and current_category:
            changes[current_category].append(stripped_line[2:])
    return changes


def extract_yaml_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content that may include YAML frontmatter.

    Returns:
        Tuple of (frontmatter_dict, remaining_content).
        If no frontmatter is found, returns (empty_dict, original_content).
    """
    if not content.startswith("---\n"):
        return {}, content

    # Find the closing ---
    if not (end_match := re.search(r"\n---\n", content[4:])):
        return {}, content

    frontmatter_text = content[4 : end_match.start() + 4]
    remaining_content = content[end_match.end() + 4 :]

    # Parse the YAML-like frontmatter (simple key: value pairs)
    frontmatter = {}
    for line in frontmatter_text.splitlines():
        if KEY_VALUE_SEPARATOR in line:
            key, value = line.split(KEY_VALUE_SEPARATOR, 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter, remaining_content


def format_markdown_section(title: str, content: str, level: int = 2) -> str:
    """Format a markdown section with proper header and content.

    Args:
        title: Section title.
        content: Section content.
        level: Header level (number of # characters).

    Returns:
        Formatted markdown section.
    """
    header_prefix = "#" * level
    return f"{header_prefix} {title}\n\n{content.strip()}\n"


def generate_table_of_contents(entries: list[dict[str, str]], max_entries: int = 10) -> str:
    """Generate a table of contents for markdown entries.

    Args:
        entries: List of entries with 'header' keys.
        max_entries: Maximum number of entries to include in TOC.

    Returns:
        Formatted table of contents.
    """
    if not entries:
        return ""

    toc = ["## Table of Contents\n"]
    for i, entry in enumerate(entries[:max_entries], 1):
        header = str(entry["header"]).replace("## ", "")
        # Create anchor link
        anchor = header.lower().replace(" ", "-").replace(",", "")
        toc.append(f"{i}. [{header}](#{anchor})")

    return "\n".join(toc) + "\n"
