# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Tests for daily updates deduplication and sorting functionality."""
# pylint: disable=redefined-outer-name,too-many-locals,duplicate-code

from pathlib import Path
import re

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


class TestDailyUpdatesDeduplication:
    """Test cases for daily updates deduplication and sorting."""

    @pytest.mark.asyncio
    async def test_read_existing_daily_summaries_empty_file(
        self, artifact_writer: ArtifactWriter
    ) -> None:
        """Test reading from non-existent file returns empty dict."""
        summaries = await artifact_writer.read_existing_daily_summaries()
        check.equal(summaries, {})

    @pytest.mark.asyncio
    async def test_read_existing_daily_summaries_with_content(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test reading existing summaries from file."""
        # Create a file with existing summaries
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

        summaries = await artifact_writer.read_existing_daily_summaries()

        check.equal(len(summaries), 3)
        check.is_in("2025-08-10", summaries)
        check.is_in("2025-08-09", summaries)
        check.is_in("2025-08-08", summaries)

        # Check that full content is preserved
        check.is_in("Summary for August 10", summaries["2025-08-10"])
        check.is_in("Summary for August 9", summaries["2025-08-09"])
        check.is_in("Summary for August 8", summaries["2025-08-08"])

    @pytest.mark.asyncio
    async def test_update_daily_updates_no_duplicates(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test that duplicate dates are not added."""
        # Create existing file
        daily_file = tmp_path / "DAILY_UPDATES.md"
        existing_content = """# Daily Updates
### 2025-08-10

Existing summary for August 10.

### 2025-08-09

Existing summary for August 9.
"""
        daily_file.write_text(existing_content)

        # Try to add summaries including a duplicate date
        new_summaries = [
            "### 2025-08-11\n\nNew summary for August 11.",
            "### 2025-08-10\n\nDifferent summary for August 10 (should be ignored).",
            "### 2025-08-08\n\nNew summary for August 8.",
        ]

        await artifact_writer.update_daily_updates_file(new_summaries)

        content = daily_file.read_text()

        # Check that the file has proper structure
        check.is_in("# Daily Updates", content)

        # Check that new dates were added
        check.is_in("2025-08-11", content)
        check.is_in("New summary for August 11", content)
        check.is_in("2025-08-08", content)
        check.is_in("New summary for August 8", content)

        # Check that existing summary for 2025-08-10 was preserved
        check.is_in("Existing summary for August 10", content)
        different_summary_text = "Different summary for August 10"
        check.is_false(different_summary_text in content)

        # Count occurrences of 2025-08-10 (should be exactly 1)
        count_08_10 = content.count("### 2025-08-10")
        check.equal(count_08_10, 1)

    @pytest.mark.asyncio
    async def test_update_daily_updates_sorted_newest_first(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test that daily updates are sorted with newest dates first."""
        # Add summaries in random order
        summaries = [
            "### 2025-08-05\n\nSummary for August 5.",
            "### 2025-08-10\n\nSummary for August 10.",
            "### 2025-08-07\n\nSummary for August 7.",
            "### 2025-08-12\n\nSummary for August 12.",
            "### 2025-08-03\n\nSummary for August 3.",
        ]

        await artifact_writer.update_daily_updates_file(summaries)

        daily_file = tmp_path / "DAILY_UPDATES.md"
        content = daily_file.read_text()

        # Extract dates in order from the file

        dates_in_file = re.findall(r"### (\d{4}-\d{2}-\d{2})", content)

        # Check that dates are sorted newest first
        expected_order = [
            "2025-08-12",
            "2025-08-10",
            "2025-08-07",
            "2025-08-05",
            "2025-08-03",
        ]
        check.equal(dates_in_file, expected_order)

    @pytest.mark.asyncio
    async def test_update_daily_updates_preserves_multiline_summaries(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test that multiline summaries are preserved correctly."""
        # Add a complex multiline summary
        summary = """### 2025-08-10

Major refactoring completed today.

The following changes were made:
- Updated the core module
- Fixed critical bugs
- Improved performance by 50%

This was a very productive day with multiple team members contributing."""

        await artifact_writer.update_daily_updates_file([summary])

        daily_file = tmp_path / "DAILY_UPDATES.md"
        content = daily_file.read_text()

        # Check that the entire multiline summary is preserved
        check.is_in("Major refactoring completed today", content)
        check.is_in("Updated the core module", content)
        check.is_in("Fixed critical bugs", content)
        check.is_in("Improved performance by 50%", content)
        check.is_in("This was a very productive day", content)

    @pytest.mark.asyncio
    async def test_update_daily_updates_merge_and_sort(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test merging new summaries with existing ones and sorting."""
        # Create existing file with some dates
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

        # Add new summaries (some before, some after existing dates)
        new_summaries = [
            "### 2025-08-10\n\nSummary for August 10.",
            "### 2025-08-06\n\nSummary for August 6.",
            "### 2025-08-04\n\nSummary for August 4.",
            "### 2025-08-01\n\nSummary for August 1.",
        ]

        await artifact_writer.update_daily_updates_file(new_summaries)

        content = daily_file.read_text()

        # Extract dates in order

        dates_in_file = re.findall(r"### (\d{4}-\d{2}-\d{2})", content)

        # Check that all dates are present and sorted
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

        # Verify all summaries are present
        expected_days = {1, 3, 4, 5, 6, 7, 10}
        for day in range(1, 11):
            if day in expected_days:
                date_str = f"2025-08-{day:02d}"
                check.is_in(date_str, content)
                check.is_in(f"Summary for August {day}", content)

    @pytest.mark.asyncio
    async def test_empty_new_summaries_preserves_existing(
        self, artifact_writer: ArtifactWriter, tmp_path: Path
    ) -> None:
        """Test that calling with empty list doesn't affect existing file."""
        # Create existing file
        daily_file = tmp_path / "DAILY_UPDATES.md"
        original_content = """# Daily Updates
### 2025-08-10

Summary for August 10.

### 2025-08-09

Summary for August 9.
"""
        daily_file.write_text(original_content)

        # Update with empty list
        await artifact_writer.update_daily_updates_file([])

        # File should not be modified
        content = daily_file.read_text()
        check.equal(content, original_content)
