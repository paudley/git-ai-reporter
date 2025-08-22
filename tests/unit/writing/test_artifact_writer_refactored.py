# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Basic tests for refactored artifact writer to ensure core functionality works."""

from datetime import datetime
from pathlib import Path

import pytest
from rich.console import Console

from git_ai_reporter.writing.artifact_writer import ArtifactWriter
from git_ai_reporter.writing.artifact_writer import NewsFileParams

# Test constants
EXPECTED_DAILY_COUNT = 2
TEST_DATE_2025_01_01 = "2025-01-01"
TEST_DATE_2025_01_02 = "2025-01-02"
TEST_SUMMARY_JAN_1ST = "Test summary for January 1st"
TEST_SUMMARY_JAN_2ND = "Test summary for January 2nd"
FIRST_DAY_SUMMARY = "First day summary"
SECOND_DAY_SUMMARY = "Second day summary"
TEST_NARRATIVE = "Test narrative for the week"


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


class TestRefactoredArtifactWriter:
    """Test the refactored ArtifactWriter functionality."""

    @pytest.mark.asyncio
    async def test_update_news_file_with_params(self, tmp_path: Path) -> None:
        """Test that update_news_file works with NewsFileParams."""
        # Create an ArtifactWriter instance for testing
        console = Console()
        writer = ArtifactWriter(
            news_file=str(tmp_path / "NEWS.md"),
            changelog_file=str(tmp_path / "CHANGELOG.txt"),
            daily_updates_file=str(tmp_path / "DAILY_UPDATES.md"),
            console=console,
        )

        params = NewsFileParams(
            narrative=TEST_NARRATIVE,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 7),
        )

        await writer.update_news_file(params)

        news_file = tmp_path / "NEWS.md"
        assert news_file.exists()
        content = news_file.read_text()
        assert TEST_NARRATIVE in content

    @pytest.mark.asyncio
    async def test_read_existing_daily_summaries(self, tmp_path: Path) -> None:
        """Test that read_existing_daily_summaries works."""
        # Create an ArtifactWriter instance for testing
        console = Console()
        writer = ArtifactWriter(
            news_file=str(tmp_path / "NEWS.md"),
            changelog_file=str(tmp_path / "CHANGELOG.txt"),
            daily_updates_file=str(tmp_path / "DAILY_UPDATES.md"),
            console=console,
        )

        # Create a test daily updates file
        daily_file = tmp_path / "DAILY_UPDATES.md"
        daily_file.write_text(
            f"""# Daily Updates

### {TEST_DATE_2025_01_01}

{TEST_SUMMARY_JAN_1ST}.

### {TEST_DATE_2025_01_02}

{TEST_SUMMARY_JAN_2ND}.
"""
        )

        summaries = await writer.read_existing_daily_summaries()

        assert len(summaries) == EXPECTED_DAILY_COUNT
        assert TEST_DATE_2025_01_01 in summaries
        assert TEST_DATE_2025_01_02 in summaries
        assert TEST_SUMMARY_JAN_1ST in summaries[TEST_DATE_2025_01_01]
        assert TEST_SUMMARY_JAN_2ND in summaries[TEST_DATE_2025_01_02]

    @pytest.mark.asyncio
    async def test_update_daily_updates_file(self, tmp_path: Path) -> None:
        """Test that update_daily_updates_file works."""
        # Create an ArtifactWriter instance for testing
        console = Console()
        writer = ArtifactWriter(
            news_file=str(tmp_path / "NEWS.md"),
            changelog_file=str(tmp_path / "CHANGELOG.txt"),
            daily_updates_file=str(tmp_path / "DAILY_UPDATES.md"),
            console=console,
        )

        summaries = [
            f"### {TEST_DATE_2025_01_01}\n\n{FIRST_DAY_SUMMARY}.",
            f"### {TEST_DATE_2025_01_02}\n\n{SECOND_DAY_SUMMARY}.",
        ]

        await writer.update_daily_updates_file(summaries)

        daily_file = tmp_path / "DAILY_UPDATES.md"
        assert daily_file.exists()
        content = daily_file.read_text()
        assert FIRST_DAY_SUMMARY in content
        assert SECOND_DAY_SUMMARY in content
