# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Additional tests for changelog_utils to improve coverage."""

import allure
import pytest_check as check

from git_ai_reporter.writing.changelog_utils import format_changelog_item
from git_ai_reporter.writing.changelog_utils import format_changelog_section


@allure.epic("Test Coverage")
@allure.feature("Changelog Utils Coverage")
@allure.story("Changelog Formatting Operations")
class TestChangelogUtilsCoverage:
    """Tests to cover specific uncovered lines in changelog_utils."""

    @allure.title("Handle empty changelog section")
    @allure.description(
        "Tests that format_changelog_section returns empty string when no items provided"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("changelog", "coverage", "empty-section", "edge-cases")
    def test_format_changelog_section_empty_items(self) -> None:
        """Test format_changelog_section with empty items list - covers line 182."""
        with allure.step("Format changelog section with empty items list"):
            result = format_changelog_section("### Added", [])

        with allure.step("Verify empty string is returned"):
            check.equal(result, "")

    @allure.title("Format changelog items with various list markers")
    @allure.description(
        "Tests that format_changelog_item properly handles different list marker types"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("changelog", "coverage", "list-markers", "formatting")
    def test_format_changelog_item_with_list_markers(self) -> None:
        """Test format_changelog_item with various list markers - covers line 208."""
        with allure.step("Test formatting with dash marker"):
            result = format_changelog_item("- some feature")
            check.equal(result, "Some feature.")

        with allure.step("Test formatting with asterisk marker"):
            result = format_changelog_item("* another feature")
            check.equal(result, "Another feature.")

        with allure.step("Test formatting with plus marker"):
            result = format_changelog_item("+ third feature")
            check.equal(result, "Third feature.")

    @allure.title("Format changelog items with lowercase start")
    @allure.description("Tests that format_changelog_item capitalizes lowercase items properly")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("changelog", "coverage", "capitalization", "formatting")
    def test_format_changelog_item_lowercase_start(self) -> None:
        """Test format_changelog_item with lowercase start - covers line 212."""
        with allure.step("Test capitalizing plain lowercase item"):
            result = format_changelog_item("lowercase item")
            check.equal(result, "Lowercase item.")

        with allure.step("Test capitalizing lowercase item with dash marker"):
            result = format_changelog_item("- lowercase with dash")
            check.equal(result, "Lowercase with dash.")
