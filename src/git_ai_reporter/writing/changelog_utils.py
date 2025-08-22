# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Utilities for changelog file operations and formatting.

This module provides specialized utilities for working with changelog files,
including section parsing, rebuilding, and formatting according to the
"Keep a Changelog" standard.
"""

from datetime import datetime
import re
from typing import Final

from git_ai_reporter.models import COMMIT_CATEGORIES
from git_ai_reporter.writing.markdown_utils import generate_yaml_frontmatter

# Define the order in which categories should appear in the changelog.
CHANGELOG_CATEGORY_ORDER: Final[list[str]] = [
    "Breaking Change",
    "New Feature",
    "Bug Fix",
    "Performance",
    "Security",
    "Refactoring",
    "Revert",
    "Tests",
    "Documentation",
    "Styling",
    "Build",
    "CI/CD",
    "Infrastructure",
    "Chore",
    "Developer Experience",
    "Deprecated",
    "Removed",
]

# Create the full, ordered list of Markdown headings.
SORTED_CHANGELOG_HEADINGS: Final[list[str]] = [
    f"### {COMMIT_CATEGORIES[name]} {name}".strip() for name in CHANGELOG_CATEGORY_ORDER
]


def create_changelog_template() -> str:
    """Create a Keep a Changelog compliant template with YAML frontmatter.

    Returns:
        Formatted changelog template.
    """
    yaml_front = generate_yaml_frontmatter(
        "Changelog",
        "All notable changes to this project documented following Keep a Changelog format",
        datetime.now(),
        datetime.now(),
    )

    return f"""{yaml_front}
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Summary

Changes that have been made but not yet released.

"""


def find_unreleased_section(content: str) -> tuple[str, str, str] | None:
    """Find and extract unreleased section parts.

    Args:
        content: Full changelog content.

    Returns:
        Tuple of (prefix, existing_entries, suffix) or None if not found.
    """
    if not (
        unreleased_section_match := re.search(
            r"(## \[Unreleased\]\n)(.*?)(\n## |$)", content, re.DOTALL
        )
    ):
        return None

    prefix = unreleased_section_match.group(1)
    existing_entries = unreleased_section_match.group(2)
    suffix = unreleased_section_match.group(3)

    return prefix, existing_entries, suffix


def merge_changelog_changes(
    new_changes: dict[str, list[str]], existing_changes: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Merge new changes into existing changes.

    Args:
        new_changes: New changes to add.
        existing_changes: Existing changes to merge into.

    Returns:
        Merged changes dictionary.
    """
    for category, items in new_changes.items():
        if category in existing_changes:
            existing_changes[category].extend(items)
        else:
            existing_changes[category] = items
    return existing_changes


def reconstruct_changelog(
    content: str, updated_section: str, prefix: str, suffix: str, original_match: str
) -> str:
    """Reconstruct the full changelog content.

    Args:
        content: Original content.
        updated_section: Updated unreleased section content.
        prefix: Section prefix.
        suffix: Section suffix.
        original_match: Original matched section to replace.

    Returns:
        Reconstructed changelog content.
    """
    return content.replace(original_match, f"{prefix}{updated_section}{suffix}")


def rebuild_unreleased_section(all_changes: dict[str, list[str]]) -> str:
    """Rebuild the content of the [Unreleased] section in the correct order.

    Uses enhanced formatting with emojis, proper wrapping, and Keep a Changelog structure.

    Args:
        all_changes: A dictionary of all changes, with categories as keys.

    Returns:
        A formatted string of the rebuilt section.
    """
    # Add summary section if there are changes
    updated_entries_str = "### Summary\n\n"
    if all_changes:
        total_changes = sum(len(items) for items in all_changes.values())
        updated_entries_str += f"This release includes {total_changes} changes across "
        updated_entries_str += f"{len(all_changes)} categories.\n\n"
    else:
        updated_entries_str += "No changes recorded yet.\n\n"

    # Sort categories according to the predefined order
    sorted_headings = []
    for heading in SORTED_CHANGELOG_HEADINGS:
        if heading in all_changes and all_changes[heading]:
            sorted_headings.append(heading)

    # Add each category section
    for heading in sorted_headings:
        if items := all_changes[heading]:
            formatted_section = format_changelog_section(heading, items)
            updated_entries_str += formatted_section

    return updated_entries_str


def format_changelog_section(category: str, items: list[str]) -> str:
    """Format a changelog section with proper structure.

    Args:
        category: The category heading (e.g., "### Added").
        items: List of changelog items for this category.

    Returns:
        Formatted section string.
    """
    if not items:
        return ""

    # Build the section header
    section_lines = [f"{category}\n"]

    # Add each item with proper formatting
    for item in items:
        formatted_item = format_changelog_item(item)
        section_lines.append(f"- {formatted_item}")

    section_lines.append("")  # Add blank line after section
    return "\n".join(section_lines)


def format_changelog_item(item: str) -> str:
    """Format a single changelog item with consistent styling.

    Args:
        item: The raw changelog item text.

    Returns:
        Formatted item string.
    """
    # Remove any existing list markers and extra whitespace
    cleaned_item = item.strip()
    if cleaned_item.startswith(("- ", "* ", "+ ")):
        cleaned_item = cleaned_item[2:].strip()

    # Ensure proper capitalization
    if cleaned_item and not cleaned_item[0].isupper():
        cleaned_item = cleaned_item[0].upper() + cleaned_item[1:]

    # Ensure proper ending punctuation
    if cleaned_item and not cleaned_item.endswith((".", "!", "?")):
        cleaned_item += "."

    return cleaned_item
