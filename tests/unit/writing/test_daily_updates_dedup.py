# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Tests for daily updates deduplication and sorting functionality."""
# pylint: disable=redefined-outer-name,too-many-locals,duplicate-code

from pathlib import Path
import re

import allure
import pytest
import pytest_check as check
from rich.console import Console

from git_ai_reporter.writing.artifact_writer import ArtifactWriter


@pytest.fixture
def artifact_writer(tmp_path: Path) -> ArtifactWriter:
    """Create an ArtifactWriter instance for testing."""
    news_file = tmp_path / "NEWS.md"
    changelog_file = tmp_path / "CHANGELOG.txt"
    daily_updates_file = tmp_path / "DAILY_UPDATES.md"
    console = Console()
    return ArtifactWriter(
        str(news_file),
        str(changelog_file),
        str(daily_updates_file),
        console,
    )


@allure.epic("Writing System")
@allure.feature("Daily Updates Management")
@allure.story("Deduplication and Sorting Operations")
class TestDailyUpdatesDeduplication:
    """Test cases for daily updates deduplication and sorting."""

    @allure.title("Read from non-existent daily summaries file")
    @allure.description("Tests that reading from non-existent file returns empty dictionary")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("daily-updates", "read-operation", "empty-file", "edge-cases")
    @pytest.mark.asyncio
    async def test_read_existing_daily_summaries_empty_file(
        self, artifact_writer: ArtifactWriter
    ) -> None:
        """Test reading from non-existent file returns empty dict."""
        with allure.step("Attempt to read from non-existent daily summaries file"):
            summaries = await artifact_writer.read_existing_daily_summaries()

        with allure.step("Verify empty dictionary is returned"):
            check.equal(summaries, {})

    @allure.title("Read existing daily summaries from file")
    @allure.description(
        "Tests reading and parsing existing daily summaries with proper content extraction"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("daily-updates", "read-operation", "content-parsing", "file-processing")
    @pytest.mark.asyncio
    async def test_read_existing_daily_summaries_with_content(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test reading existing summaries from file."""
        with allure.step("Create daily updates file with existing summaries"):
            daily_file = tmp_path / "DAILY_UPDATES.md"
            content = """# Daily Updates
### 2025-08-10

Summary for August 10.

### 2025-08-09

Summary for August 9.

### 2025-08-08

Summary for August 8.
"""
            daily_file.write_text(content)

        with allure.step("Read existing daily summaries from file"):
            summaries = await artifact_writer.read_existing_daily_summaries()

        with allure.step("Verify correct number of summaries parsed"):
            check.equal(len(summaries), 3)
            check.is_in("2025-08-10", summaries)
            check.is_in("2025-08-09", summaries)
            check.is_in("2025-08-08", summaries)

        with allure.step("Verify full content is preserved for each summary"):
            check.is_in("Summary for August 10", summaries["2025-08-10"])
            check.is_in("Summary for August 9", summaries["2025-08-09"])
            check.is_in("Summary for August 8", summaries["2025-08-08"])

    @allure.title("Prevent duplicate dates in daily updates")
    @allure.description(
        "Tests that duplicate dates are not added and existing summaries are preserved"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("daily-updates", "deduplication", "date-handling", "data-integrity")
    @pytest.mark.asyncio
    async def test_update_daily_updates_no_duplicates(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test that duplicate dates are not added."""
        with allure.step("Create existing daily updates file"):
            daily_file = tmp_path / "DAILY_UPDATES.md"
            existing_content = """# Daily Updates
### 2025-08-10

Existing summary for August 10.

### 2025-08-09

Existing summary for August 9.
"""
            daily_file.write_text(existing_content)

        with allure.step("Attempt to add summaries including duplicate date"):
            new_summaries = [
                "### 2025-08-11\n\nNew summary for August 11.",
                "### 2025-08-10\n\nDifferent summary for August 10 (should be ignored).",
                "### 2025-08-08\n\nNew summary for August 8.",
            ]
            await artifact_writer.update_daily_updates_file(new_summaries)

        with allure.step("Verify file structure and new dates added"):
            content = daily_file.read_text(encoding="utf-8")
            check.is_in("# Daily Updates", content)
            check.is_in("2025-08-11", content)
            check.is_in("New summary for August 11", content)
            check.is_in("2025-08-08", content)
            check.is_in("New summary for August 8", content)

        with allure.step("Verify existing summary preserved and duplicate rejected"):
            check.is_in("Existing summary for August 10", content)
            different_summary_text = "Different summary for August 10"
            check.is_false(different_summary_text in content)

        with allure.step("Verify no duplicate date entries exist"):
            count_08_10 = content.count("### 2025-08-10")
            check.equal(count_08_10, 1)

    @allure.title("Sort daily updates with newest dates first")
    @allure.description(
        "Tests that daily updates are automatically sorted in descending date order"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("daily-updates", "sorting", "date-ordering", "chronological")
    @pytest.mark.asyncio
    async def test_update_daily_updates_sorted_newest_first(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test that daily updates are sorted with newest dates first."""
        with allure.step("Create summaries in random date order"):
            summaries = [
                "### 2025-08-05\n\nSummary for August 5.",
                "### 2025-08-10\n\nSummary for August 10.",
                "### 2025-08-07\n\nSummary for August 7.",
                "### 2025-08-12\n\nSummary for August 12.",
                "### 2025-08-03\n\nSummary for August 3.",
            ]

        with allure.step("Update daily updates file with random-ordered summaries"):
            await artifact_writer.update_daily_updates_file(summaries)

        with allure.step("Extract dates from updated file"):
            daily_file = tmp_path / "DAILY_UPDATES.md"
            content = daily_file.read_text(encoding="utf-8")
            dates_in_file = re.findall(r"### (\d{4}-\d{2}-\d{2})", content)

        with allure.step("Verify dates are sorted newest first"):
            expected_order = [
                "2025-08-12",
                "2025-08-10",
                "2025-08-07",
                "2025-08-05",
                "2025-08-03",
            ]
            check.equal(dates_in_file, expected_order)

    @allure.title("Preserve multiline summary content")
    @allure.description("Tests that complex multiline summaries are preserved without content loss")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("daily-updates", "multiline-content", "content-preservation", "formatting")
    @pytest.mark.asyncio
    async def test_update_daily_updates_preserves_multiline_summaries(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test that multiline summaries are preserved correctly."""
        with allure.step("Create complex multiline summary with various content types"):
            summary = """### 2025-08-10

Major refactoring completed today.

The following changes were made:
- Updated the core module
- Fixed critical bugs
- Improved performance by 50%

This was a very productive day with multiple team members contributing."""

        with allure.step("Update daily updates file with multiline summary"):
            await artifact_writer.update_daily_updates_file([summary])

        with allure.step("Verify entire multiline summary content is preserved"):
            daily_file = tmp_path / "DAILY_UPDATES.md"
            content = daily_file.read_text(encoding="utf-8")
            check.is_in("Major refactoring completed today", content)
            check.is_in("Updated the core module", content)
            check.is_in("Fixed critical bugs", content)
            check.is_in("Improved performance by 50%", content)
            check.is_in("This was a very productive day", content)

    @allure.title("Merge and sort new summaries with existing ones")
    @allure.description(
        "Tests merging new summaries with existing ones while maintaining proper sort order"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("daily-updates", "merging", "sorting", "date-ordering", "integration")
    @pytest.mark.asyncio
    async def test_update_daily_updates_merge_and_sort(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test merging new summaries with existing ones and sorting."""
        with allure.step("Create existing daily updates file with some dates"):
            daily_file = tmp_path / "DAILY_UPDATES.md"
            existing_content = """# Daily Updates
### 2025-08-07

Summary for August 7.

### 2025-08-05

Summary for August 5.

### 2025-08-03

Summary for August 3.
"""
            daily_file.write_text(existing_content)

        with allure.step("Add new summaries with dates before, after, and between existing ones"):
            new_summaries = [
                "### 2025-08-10\n\nSummary for August 10.",
                "### 2025-08-06\n\nSummary for August 6.",
                "### 2025-08-04\n\nSummary for August 4.",
                "### 2025-08-01\n\nSummary for August 1.",
            ]
            await artifact_writer.update_daily_updates_file(new_summaries)

        with allure.step("Verify merged content is properly sorted"):
            content = daily_file.read_text(encoding="utf-8")
            dates_in_file = re.findall(r"### (\d{4}-\d{2}-\d{2})", content)
            expected_order = [
                "2025-08-10",  # New
                "2025-08-07",  # Existing
                "2025-08-06",  # New
                "2025-08-05",  # Existing
                "2025-08-04",  # New
                "2025-08-03",  # Existing
                "2025-08-01",  # New
            ]
            check.equal(dates_in_file, expected_order)

        with allure.step("Verify all summaries are present in final content"):
            expected_days = {1, 3, 4, 5, 6, 7, 10}
            for day in range(1, 11):
                if day in expected_days:
                    date_str = f"2025-08-{day:02d}"
                    check.is_in(date_str, content)
                    check.is_in(f"Summary for August {day}", content)

    @allure.title("Preserve existing content when updating with empty list")
    @allure.description(
        "Tests that updating with empty summary list preserves existing file content"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("daily-updates", "empty-update", "content-preservation", "edge-cases")
    @pytest.mark.asyncio
    async def test_empty_new_summaries_preserves_existing(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test that calling with empty list doesn't affect existing file."""
        with allure.step("Create existing daily updates file with content"):
            daily_file = tmp_path / "DAILY_UPDATES.md"
            original_content = """# Daily Updates
### 2025-08-10

Summary for August 10.

### 2025-08-09

Summary for August 9.
"""
            daily_file.write_text(original_content)

        with allure.step("Update file with empty summaries list"):
            await artifact_writer.update_daily_updates_file([])

        with allure.step("Verify existing content is completely preserved"):
            content = daily_file.read_text(encoding="utf-8")
            check.equal(content, original_content)
