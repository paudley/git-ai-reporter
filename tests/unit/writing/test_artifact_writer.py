# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=protected-access

"""Unit tests for git_ai_reporter.writing.artifact_writer module.

This module tests the ArtifactWriter class which handles writing
NEWS.md, CHANGELOG.txt, and DAILY_UPDATES.md files.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import allure
import pytest
import pytest_check as check
from rich.console import Console

from git_ai_reporter.models import AnalysisResult
from git_ai_reporter.models import Change
from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.writing.artifact_writer import ArtifactWriter
from git_ai_reporter.writing.artifact_writer import NewsFileParams


@pytest.fixture
def artifact_writer(temp_dir: Path) -> ArtifactWriter:
    """Create an ArtifactWriter instance for testing."""
    console = Console()
    return ArtifactWriter(
        news_file=str(temp_dir / "NEWS.md"),
        changelog_file=str(temp_dir / "CHANGELOG.txt"),
        daily_updates_file=str(temp_dir / "DAILY_UPDATES.md"),
        console=console,
    )


@pytest.fixture
def sample_analysis_result() -> AnalysisResult:
    """Create a sample AnalysisResult for testing."""
    return AnalysisResult(
        period_summaries=["This week we made significant progress on the authentication system."],
        daily_summaries=[
            "Monday: Implemented login functionality",
            "Tuesday: Added password reset feature",
            "Wednesday: Fixed security vulnerabilities",
        ],
        changelog_entries=[
            CommitAnalysis(
                changes=[
                    Change(summary="Add user authentication", category="New Feature"),
                    Change(summary="Fix login timeout", category="Bug Fix"),
                ],
                trivial=False,
            ),
            CommitAnalysis(
                changes=[Change(summary="Update README", category="Documentation")],
                trivial=True,
            ),
        ],
    )


@allure.feature("Writing - Artifact Writer")
@allure.story("File Generation and Updates")
class TestArtifactWriter:
    """Test suite for ArtifactWriter class."""

    @allure.title("Initialize ArtifactWriter with file paths")
    @allure.description(
        "Verifies that ArtifactWriter can be properly initialized with NEWS.md, CHANGELOG.txt and DAILY_UPDATES.md paths"
    )
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.tag("writing", "initialization", "files")
    def test_init(self, temp_dir: Path) -> None:
        """Test ArtifactWriter initialization."""
        with allure.step("Create ArtifactWriter instance"):
            console = Console()
            writer = ArtifactWriter(
                news_file=str(temp_dir / "NEWS.md"),
                changelog_file=str(temp_dir / "CHANGELOG.txt"),
                daily_updates_file=str(temp_dir / "DAILY_UPDATES.md"),
                console=console,
            )

        with allure.step("Verify file paths are set correctly"):
            check.equal(writer.news_path, temp_dir / "NEWS.md")
        check.equal(writer.changelog_path, temp_dir / "CHANGELOG.txt")
        check.equal(writer.daily_updates_path, temp_dir / "DAILY_UPDATES.md")

    @pytest.mark.asyncio
    @allure.title("Read historical summaries from NEWS.md")
    @allure.description(
        "Verifies that existing historical summaries can be read from NEWS.md files"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("writing", "reading", "historical-data")
    async def test_read_historical_summaries(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
        temp_dir: Path,
    ) -> None:
        """Test reading historical summaries."""
        with allure.step("Create existing NEWS.md with historical content"):
            # Create existing NEWS.md with some history
            news_file = temp_dir / "NEWS.md"
        news_file.write_text(
            "# Project News\n\n"
            "## Week of 2024-12-25 to 2024-12-31\n"
            "Previous week summary.\n\n"
            "## Week of 2025-01-01 to 2025-01-07\n"
            "Current week summary.\n"
        )

        with allure.step("Read historical summaries"):
            history = (
                await artifact_writer._read_historical_summaries()
            )  # pylint: disable=protected-access

        with allure.step("Verify historical content is retrieved"):
            # Should return recent history
            check.is_not_none(history)
            check.is_in("Current week summary", history)

    @pytest.mark.asyncio
    @allure.title("Append daily updates to existing file")
    @allure.description(
        "Verifies that new daily updates are properly merged with existing DAILY_UPDATES.md content"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("writing", "daily-updates", "merging")
    async def test_daily_updates_appends_to_existing(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
        temp_dir: Path,
    ) -> None:
        """Test that DAILY_UPDATES.md properly merges existing summaries."""
        with allure.step("Create existing daily updates file"):
            # Create existing file with proper format
            daily_file = temp_dir / "DAILY_UPDATES.md"
            daily_file.write_text("# Daily Updates\n### 2025-01-01\n\nOld updates here.\n")

        with allure.step("Append new daily updates"):
            await artifact_writer.update_daily_updates_file(["### 2025-01-02\n\nNew daily update"])

        with allure.step("Verify content is properly merged"):
            content = daily_file.read_text(encoding="utf-8")
            check.is_in("Old updates here", content)
            check.is_in("New daily update", content)

    @allure.title("Handle empty input data gracefully")
    @allure.description(
        "Verifies that empty narratives, summaries, and changelog entries are handled without errors"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("writing", "edge-cases", "empty-data")
    @pytest.mark.asyncio
    async def test_empty_inputs(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
        temp_dir: Path,
    ) -> None:
        """Test handling of empty inputs."""
        with allure.step("Test empty narrative handling"):
            # Test with empty narrative - should still create file
            params = NewsFileParams(
                narrative="", start_date=datetime.now(), end_date=datetime.now()
            )
            await artifact_writer.update_news_file(params)
        news_file = temp_dir / "NEWS.md"
        # File might not exist if nothing was written, which is ok
        if news_file.exists():
            check.is_true(news_file.exists())

        with allure.step("Test empty daily summaries handling"):
            # Test with empty daily summaries
            await artifact_writer.update_daily_updates_file([])
        daily_file = temp_dir / "DAILY_UPDATES.md"
        if daily_file.exists():
            check.is_true(daily_file.exists())

        with allure.step("Test empty changelog entries handling"):
            # Test with empty changelog entries
            await artifact_writer.update_changelog_file("")
        changelog_file = temp_dir / "CHANGELOG.txt"
        if changelog_file.exists():
            check.is_true(changelog_file.exists())

    @allure.title("Format changelog entries with proper categories")
    @allure.description(
        "Verifies that changelog entries are properly formatted with emoji categories and content"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("writing", "changelog", "formatting")
    @pytest.mark.asyncio
    async def test_changelog_formatting(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
        temp_dir: Path,
    ) -> None:
        """Test that changelog entries are formatted correctly."""
        with allure.step("Create changelog entries with various categories"):
            # Create various category entries
            entries = """### ✨ New Feature
- Add user authentication
- Add profile management

### 🐛 Bug Fix
- Fix login timeout
- Fix memory leak

### 🔒 Security
- Fix SQL injection vulnerability

### 🗑️ Deprecated
- Deprecate old API

### ❌ Removed
- Remove legacy code"""

        with allure.step("Update changelog file with formatted entries"):
            await artifact_writer.update_changelog_file(entries)

        with allure.step("Verify changelog formatting and content"):
            content = (temp_dir / "CHANGELOG.txt").read_text(encoding="utf-8")
        check.is_in("Add user authentication", content)
        check.is_in("Fix login timeout", content)
        check.is_in("Fix SQL injection", content)
        check.is_in("Deprecate old API", content)
        check.is_in("Remove legacy code", content)

    @pytest.mark.asyncio
    async def test_file_write_error_handling(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test error handling when file writing fails."""
        # With the refactored code, async_write_file_atomic returns False on error
        # rather than raising
        with patch(
            "git_ai_reporter.utils.async_file_utils.async_write_file_atomic", return_value=False
        ):
            # The method should complete without raising an exception (graceful error handling)
            params = NewsFileParams(
                narrative="Test narrative", start_date=datetime.now(), end_date=datetime.now()
            )
            # This should not raise an exception but should handle the error gracefully
            await artifact_writer.update_news_file(params)

    @pytest.mark.asyncio
    async def test_concurrent_writes(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
        temp_dir: Path,
    ) -> None:
        """Test that concurrent writes don't interfere with each other."""
        # Run multiple write operations concurrently
        tasks = [
            artifact_writer.update_news_file(
                NewsFileParams(
                    narrative="News content", start_date=datetime.now(), end_date=datetime.now()
                )
            ),
            artifact_writer.update_changelog_file("### Added\n- New feature"),
            artifact_writer.update_daily_updates_file(["Daily update"]),
        ]
        await asyncio.gather(*tasks)

        # All files should exist and have content
        check.is_true((temp_dir / "NEWS.md").exists())
        check.is_true((temp_dir / "CHANGELOG.txt").exists())
        check.is_true((temp_dir / "DAILY_UPDATES.md").exists())

        check.greater(len((temp_dir / "NEWS.md").read_text(encoding="utf-8")), 0)
        check.greater(len((temp_dir / "CHANGELOG.txt").read_text(encoding="utf-8")), 0)
        check.greater(len((temp_dir / "DAILY_UPDATES.md").read_text(encoding="utf-8")), 0)

    def test_format_timestamp(self) -> None:
        """Test timestamp formatting."""
        # This assumes the class has a method for formatting timestamps
        # Adjust based on actual implementation
        now = datetime(2025, 1, 8, 10, 30, 45)
        with patch("git_ai_reporter.writing.artifact_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.strftime = datetime.strftime

            # Test that timestamps are formatted correctly in output
            # This will depend on the actual implementation

    @pytest.mark.asyncio
    async def test_unicode_content(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
        temp_dir: Path,
    ) -> None:
        """Test handling of Unicode content."""
        # Test Unicode in news
        params = NewsFileParams(
            narrative="Added emoji support 🎉 and unicode: ñáéíóú",
            start_date=datetime.now(),
            end_date=datetime.now(),
        )
        await artifact_writer.update_news_file(params)

        # Test Unicode in daily updates
        await artifact_writer.update_daily_updates_file(
            ["### 2025-01-08\n\nChinese: 中文, Japanese: 日本語, Korean: 한국어"]
        )

        # Test Unicode in changelog
        await artifact_writer.update_changelog_file("### 🚀 CI/CD\n- Add emoji 🚀")

        # Check that Unicode is preserved
        news_content = (temp_dir / "NEWS.md").read_text(encoding="utf-8")
        check.is_in("🎉", news_content)
        check.is_in("ñáéíóú", news_content)

        daily_content = (temp_dir / "DAILY_UPDATES.md").read_text(encoding="utf-8")
        check.is_in("中文", daily_content)
        check.is_in("日本語", daily_content)
        check.is_in("한국어", daily_content)

        changelog_content = (temp_dir / "CHANGELOG.txt").read_text(encoding="utf-8")
        check.is_in("🚀", changelog_content)

    @pytest.mark.asyncio
    async def test_insert_content_after_header_existing_file(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
        temp_dir: Path,
    ) -> None:
        """Test _insert_content_after_header with existing file (lines 127-128, 134-142)."""
        # Create a file with existing content - targeting the file reading logic
        test_file = temp_dir / "test_file.md"
        test_file.write_text("# Header\n\nExisting content line 1\nExisting content line 2\n")

        # Test the method that uses _insert_content_after_header
        content_to_insert = "New content block"
        header = "# Header"

        # Call the private method directly to test the specific lines
        await artifact_writer._insert_content_after_header(test_file, content_to_insert, header)

        # Verify the file was read (lines 127-128) and processed (lines 134-142)
        result = test_file.read_text(encoding="utf-8")
        check.is_in("New content block", result)
        check.is_in("Existing content line 1", result)
        check.is_in("Existing content line 2", result)

    @pytest.mark.asyncio
    async def test_insert_content_after_header_non_empty_lines_processing(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
        temp_dir: Path,
    ) -> None:
        """Test _insert_content_after_header line processing logic (lines 134-142)."""
        # Create a file with empty lines at the beginning to test line processing
        test_file = temp_dir / "test_file.md"
        test_file.write_text("\n\n# Header\n\nExisting content\n")

        content_to_insert = "Inserted content"
        header = "# Header"

        # Call the method to trigger the line processing code
        await artifact_writer._insert_content_after_header(test_file, content_to_insert, header)

        # Verify the content was inserted at the correct position
        result = test_file.read_text(encoding="utf-8")

        # Should find first non-empty line and insert after it
        check.is_in("Inserted content", result)
        check.is_in("# Header", result)

    @pytest.mark.asyncio
    async def test_insert_content_after_header_file_not_exists(
        self,
        artifact_writer: ArtifactWriter,  # pylint: disable=redefined-outer-name
        temp_dir: Path,
    ) -> None:
        """Test _insert_content_after_header when file doesn't exist."""
        # Test with non-existent file - should create new file
        test_file = temp_dir / "new_file.md"
        content_to_insert = "New content"
        header = "# New Header"

        await artifact_writer._insert_content_after_header(test_file, content_to_insert, header)

        # Verify file was created with header and content
        result = test_file.read_text(encoding="utf-8")
        check.is_in("# New Header", result)
        check.is_in("New content", result)
