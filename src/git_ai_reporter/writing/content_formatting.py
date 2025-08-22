# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Content formatting utilities for markdown files.

This module provides utilities for text formatting, wrapping, and
content structure operations used across the writing components.
"""

from datetime import datetime
from typing import Final

from git_ai_reporter.writing.markdown_utils import wrap_markdown_text

# Text wrapping constants
MAX_LINE_LENGTH: Final[int] = 80


def wrap_text_lines(text: str, max_length: int = MAX_LINE_LENGTH) -> str:
    """Wrap text lines to specified maximum length while preserving markdown structure.

    Args:
        text: Text to wrap.
        max_length: Maximum line length.

    Returns:
        Text with wrapped lines.
    """
    return wrap_markdown_text(text, max_length)


def format_week_header_with_counter(
    start_date: datetime, end_date: datetime, week_counter: int
) -> str:
    """Format week header with week number using a counter.

    Args:
        start_date: Week start date.
        end_date: Week end date.
        week_counter: Current week counter value.

    Returns:
        Formatted week header.
    """
    del week_counter  # Intentionally unused - use ISO week number instead
    week_num = start_date.isocalendar()[1]  # ISO week number
    return (
        f"## Week {week_num}: {start_date.strftime('%B %d')} - " f"{end_date.strftime('%B %d, %Y')}"
    )


def insert_content_after_header(content: str, new_content: str, header: str) -> str:
    """Insert new content after a specific header in existing content.

    Args:
        content: Existing file content.
        new_content: Content to insert.
        header: Header to insert content after.

    Returns:
        Updated content with new content inserted.
    """
    if header in content:
        # Find the position after the header
        header_pos = content.find(header)
        header_end = header_pos + len(header)

        # Find the end of the header line
        if (next_newline := content.find("\n", header_end)) == -1:
            next_newline = len(content)

        # Insert new content after the header line
        return content[: next_newline + 1] + "\n" + new_content + content[next_newline + 1 :]
    else:
        # Header not found, append to content
        return content + "\n\n" + header + "\n\n" + new_content


def generate_yaml_frontmatter_with_defaults(
    title: str, description: str, created: datetime | None = None, updated: datetime | None = None
) -> str:
    """Generate YAML frontmatter with default dates.

    Args:
        title: Document title.
        description: Document description.
        created: Creation date (defaults to now).
        updated: Last update date (defaults to now).

    Returns:
        Formatted YAML frontmatter.
    """
    now = datetime.now()
    created = created or now
    updated = updated or now

    return f"""---
title: {title}
description: {description}
created: {created.strftime('%Y-%m-%d')}
updated: {updated.strftime('%Y-%m-%d')}
format: markdown
---
"""


def clean_markdown_content(content: str) -> str:
    """Clean and normalize markdown content.

    Args:
        content: Raw markdown content.

    Returns:
        Cleaned markdown content.
    """
    # Remove excessive whitespace
    lines = content.split("\n")
    cleaned_lines = []

    prev_empty = False
    for line in lines:
        # Skip multiple consecutive empty lines
        if not line.strip():
            if not prev_empty:
                cleaned_lines.append("")
            prev_empty = True
        else:
            cleaned_lines.append(line.rstrip())  # Remove trailing whitespace
            prev_empty = False

    # Remove trailing empty lines
    for _ in range(len(cleaned_lines)):
        if cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()
        else:
            break

    return "\n".join(cleaned_lines)


def extract_content_sections(content: str, section_headers: list[str]) -> dict[str, str]:
    """Extract content sections based on headers.

    Args:
        content: Full markdown content.
        section_headers: List of section headers to extract.

    Returns:
        Dictionary mapping headers to their content.
    """
    sections = {}
    lines = content.split("\n")
    current_section = None
    current_content: list[str] = []

    for line in lines:
        # Check if this line is a section header we're looking for
        for header in section_headers:
            if line.strip() == header:
                # Save previous section if exists
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                current_section = header
                current_content = []
                break
        else:
            # Not a header, add to current section content
            if current_section:
                current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections
