# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=duplicate-code,protected-access

"""Additional unit tests for artifact_writer to achieve comprehensive coverage."""

from datetime import datetime
from pathlib import Path

import aiofiles
import aiofiles.os
import pytest
import pytest_check as check
from rich.console import Console

from git_ai_reporter.writing.artifact_writer import ArtifactWriter
from git_ai_reporter.writing.artifact_writer import NewsFileParams


@pytest.fixture
def artifact_writer(tmp_path: Path) -> ArtifactWriter:
    """Create an ArtifactWriter instance for testing."""
    console = Console()
    return ArtifactWriter(
        news_file=str(tmp_path / "NEWS.md"),
        changelog_file=str(tmp_path / "CHANGELOG.txt"),
        daily_updates_file=str(tmp_path / "DAILY_UPDATES.md"),
        console=console,
    )


class TestHistoricalSummariesCoverage:
    """Tests for historical summaries reading to achieve full coverage."""

    @pytest.mark.asyncio
    async def test_read_historical_summaries_with_daily_updates(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test reading historical summaries with daily updates in the previous week."""
        # Create NEWS.md
        news_content = """# Development News

## Week of 2024-12-23 to 2024-12-29

First week summary.

## Week of 2024-12-30 to 2025-01-05

Second week summary.
"""
        async with aiofiles.open(artifact_writer.news_path, "w") as f:
            await f.write(news_content)

        # Create DAILY_UPDATES.md with daily summaries
        daily_content = """# Daily Development Updates

### 2024-12-25

Christmas day work.

### 2024-12-26

Boxing day development.

### 2024-12-30

New year prep work.

### 2025-01-01

New year's day coding.
"""
        async with aiofiles.open(artifact_writer.daily_updates_path, "w") as f:
            await f.write(daily_content)

        history = (
            await artifact_writer._read_historical_summaries()
        )  # pylint: disable=protected-access

        # Should include both NEWS summaries and relevant daily summaries
        check.is_in("## Recent Weekly Summaries", history)
        check.is_in("First week summary", history)
        check.is_in("Second week summary", history)

        # Should include daily summaries
        check.is_in("## Recent Daily Updates", history)
        check.is_in("Boxing day development", history)
        check.is_in("New year prep work", history)
        check.is_in("New year's day coding", history)

        # Current implementation includes all daily updates (first 1000 chars)
        check.is_in("Christmas day work", history)

    @pytest.mark.asyncio
    async def test_update_changelog_file_error_handling(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test error handling when updating changelog file."""
        # Create existing CHANGELOG.txt
        changelog_content = """# Changelog

## [Unreleased]

### ✨ New Feature
- Existing feature

## [1.0.0] - 2024-01-01
### ✨ New Feature
- Initial release
"""
        async with aiofiles.open(artifact_writer.changelog_path, "w") as f:
            await f.write(changelog_content)

        # Update with new changelog that has an New Feature section
        new_changelog = """### ✨ New Feature
- New feature 1
- New feature 2

### 🐛 Bug Fix
- Bug fix 1
"""

        await artifact_writer.update_changelog_file(new_changelog)

        # Read the updated file
        async with aiofiles.open(artifact_writer.changelog_path, "r") as f:
            updated_content = await f.read()

        # Should merge the Added sections
        check.is_in("- Existing feature", updated_content)
        check.is_in("- New feature 1", updated_content)
        check.is_in("- New feature 2", updated_content)
        check.is_in("- Bug fix 1", updated_content)

    @pytest.mark.asyncio
    async def test_update_changelog_no_existing_unreleased(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test updating changelog when there's no [Unreleased] section."""
        # Create CHANGELOG.txt without [Unreleased]
        changelog_content = """# Changelog

## [1.0.0] - 2024-01-01
### Added
- Initial release
"""
        async with aiofiles.open(artifact_writer.changelog_path, "w") as f:
            await f.write(changelog_content)

        new_changelog = """### Added
- New feature
"""

        await artifact_writer.update_changelog_file(new_changelog)

        # Read the updated file
        async with aiofiles.open(artifact_writer.changelog_path, "r") as f:
            updated_content = await f.read()

        # When there's no [Unreleased] section, it should remain unchanged
        # because the function prints an error and returns early
        check.is_in("## [1.0.0]", updated_content)
        check.is_in("- Initial release", updated_content)
        check.is_not_in("- New feature", updated_content)

    @pytest.mark.asyncio
    async def test_update_news_file_first_time(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test creating NEWS.md for the first time."""
        narrative = "This week we made great progress on the project."
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 7)

        params = NewsFileParams(narrative=narrative, start_date=start_date, end_date=end_date)
        await artifact_writer.update_news_file(params)

        # Check the file was created
        async with aiofiles.open(artifact_writer.news_path, "r") as f:
            content = await f.read()

        check.is_in("# Project News", content)
        check.is_in("## Week 1: January 01 - January 07, 2025", content)
        check.is_in("This week we made great progress", content)
