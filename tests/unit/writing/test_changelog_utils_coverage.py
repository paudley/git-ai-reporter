# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Additional tests for changelog_utils to improve coverage."""

import pytest_check as check

from git_ai_reporter.writing.changelog_utils import format_changelog_item
from git_ai_reporter.writing.changelog_utils import format_changelog_section


class TestChangelogUtilsCoverage:
    """Tests to cover specific uncovered lines in changelog_utils."""

    def test_format_changelog_section_empty_items(self) -> None:
        """Test format_changelog_section with empty items list - covers line 182."""
        result = format_changelog_section("### Added", [])
        check.equal(result, "")

    def test_format_changelog_item_with_list_markers(self) -> None:
        """Test format_changelog_item with various list markers - covers line 208."""
        # Test with dash marker
        result = format_changelog_item("- some feature")
        check.equal(result, "Some feature.")

        # Test with asterisk marker
        result = format_changelog_item("* another feature")
        check.equal(result, "Another feature.")

        # Test with plus marker
        result = format_changelog_item("+ third feature")
        check.equal(result, "Third feature.")

    def test_format_changelog_item_lowercase_start(self) -> None:
        """Test format_changelog_item with lowercase start - covers line 212."""
        result = format_changelog_item("lowercase item")
        check.equal(result, "Lowercase item.")

        # Test with existing dash but lowercase
        result = format_changelog_item("- lowercase with dash")
        check.equal(result, "Lowercase with dash.")
