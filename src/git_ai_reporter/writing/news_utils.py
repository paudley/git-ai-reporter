# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Utilities for news file operations and weekly entry management.

This module provides specialized utilities for working with NEWS.md files,
including weekly entry parsing, duplicate detection, and content formatting.
"""

from datetime import datetime
import re
from typing import Final

from git_ai_reporter.writing.markdown_utils import format_week_header
from git_ai_reporter.writing.markdown_utils import generate_yaml_frontmatter
from git_ai_reporter.writing.markdown_utils import wrap_markdown_text

# Constants for news file operations
NEWS_HEADER: Final[str] = "# Project News"
MAX_LINE_LENGTH: Final[int] = 80


def parse_weekly_entries(content: str) -> list[dict[str, str | datetime]]:
    """Parse existing NEWS.md content to extract weekly entries.

    Args:
        content: The full content of the NEWS.md file.

    Returns:
        List of dictionaries containing header, content, start_date, and end_date.
    """
    entries = []

    # Find all weekly sections
    weekly_sections = re.findall(r"(## Week of .*?)(?=\n## Week of|\Z)", content, re.DOTALL)

    for section in weekly_sections:
        lines = section.strip().split("\n")
        header = lines[0]
        content_lines = lines[1:]

        # Extract dates from header
        if date_match := re.match(r"## Week of (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})", header):
            start_date_str, end_date_str = date_match.groups()
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=None)
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=None)

            # Remove empty lines at the beginning
            first_non_empty = next((i for i, line in enumerate(content_lines) if line.strip()), 0)
            content_lines = content_lines[first_non_empty:]

            entries.append(
                {
                    "header": header,
                    "content": "\n".join(content_lines),
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

    return entries


def create_new_news_entry(
    narrative: str,
    start_date: datetime,
    metrics: dict[str, int] | None = None,
) -> str:
    """Create a new news entry with proper formatting.

    Args:
        narrative: The narrative content.
        start_date: Week start date for YAML frontmatter.
        metrics: Optional metrics dict.

    Returns:
        Formatted content block for new entry.
    """
    # Add YAML frontmatter
    yaml_front = generate_yaml_frontmatter(
        "Project News",
        "Development summaries and project updates",
        start_date,
        datetime.now(),
    )

    # Create week header
    week_header = format_week_header(start_date, start_date)  # Simplified for new entry

    # Wrap narrative text
    wrapped_narrative = wrap_markdown_text(narrative)

    # Add summary metrics if provided
    metrics_section = ""
    if metrics and metrics.get("commits_analyzed", 0) > 0:
        metrics_section = f"\n{generate_summary_metrics_from_dict(metrics)}\n"

    return f"{yaml_front}\n{week_header}\n\n{wrapped_narrative}{metrics_section}\n"


def find_duplicate_week_groups(
    entries: list[dict[str, str | datetime]],
) -> dict[str, list[dict[str, str | datetime]]]:
    """Group entries by week header to find duplicates.

    Args:
        entries: List of weekly entries.

    Returns:
        Dictionary mapping headers to lists of entries.
    """
    week_groups: dict[str, list[dict[str, str | datetime]]] = {}
    for entry in entries:
        if (header := str(entry["header"])) not in week_groups:
            week_groups[header] = []
        week_groups[header].append(entry)
    return week_groups


def normalize_entry_dates(
    entries: list[dict[str, str | datetime]],
) -> list[dict[str, str | datetime]]:
    """Ensure all dates in entries are timezone-naive for sorting.

    Args:
        entries: List of entries to normalize.

    Returns:
        List of entries with normalized dates.
    """
    for entry in entries:
        if isinstance(entry["start_date"], datetime) and entry["start_date"].tzinfo is not None:
            entry["start_date"] = entry["start_date"].replace(tzinfo=None)
        if isinstance(entry["end_date"], datetime) and entry["end_date"].tzinfo is not None:
            entry["end_date"] = entry["end_date"].replace(tzinfo=None)
    return entries


def generate_summary_metrics_from_dict(metrics: dict[str, int]) -> str:
    """Generate summary metrics table from metrics dictionary.

    Args:
        metrics: Dictionary with keys: commits_analyzed, files_changed, lines_added, lines_removed.

    Returns:
        Formatted metrics table.
    """
    commits_analyzed = metrics.get("commits_analyzed", 0)
    files_changed = metrics.get("files_changed", 0)
    lines_added = metrics.get("lines_added", 0)
    lines_removed = metrics.get("lines_removed", 0)

    return generate_summary_metrics(commits_analyzed, files_changed, lines_added, lines_removed)


def generate_summary_metrics(
    commits_analyzed: int, files_changed: int, lines_added: int, lines_removed: int
) -> str:
    """Generate summary metrics table.

    Args:
        commits_analyzed: Number of commits analyzed.
        files_changed: Number of files changed.
        lines_added: Lines added.
        lines_removed: Lines removed.

    Returns:
        Formatted metrics table.
    """
    return f"""### Week Statistics

| Metric | Value |
|--------|-------|
| Commits Analyzed | {commits_analyzed:,} |
| Files Changed | {files_changed:,} |
| Lines Added | +{lines_added:,} |
| Lines Removed | -{lines_removed:,} |
| Net Lines | {lines_added - lines_removed:+,} |
"""


def generate_table_of_contents(
    weekly_entries: list[dict[str, str | datetime]], max_entries: int = 10
) -> str:
    """Generate a table of contents for NEWS.md.

    Args:
        weekly_entries: List of weekly entries.
        max_entries: Maximum number of entries to include in TOC.

    Returns:
        Formatted table of contents.
    """
    if not weekly_entries:
        return ""

    toc = ["## Table of Contents\n"]
    for i, entry in enumerate(weekly_entries[:max_entries], 1):
        header = str(entry["header"]).replace("## ", "")
        # Create anchor link
        anchor = header.lower().replace(" ", "-").replace(",", "")
        toc.append(f"{i}. [{header}](#{anchor})")

    return "\n".join(toc) + "\n"
