# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Tests for orchestrator daily summary reuse functionality."""
# pylint: disable=redefined-outer-name,too-many-locals,protected-access

from datetime import datetime
from datetime import timezone
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
import pytest_check as check
from rich.console import Console

from git_ai_reporter.analysis.git_analyzer import GitAnalyzer
from git_ai_reporter.cache.manager import CacheManager
from git_ai_reporter.models import Change
from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.orchestration.orchestrator import AnalysisOrchestrator
from git_ai_reporter.orchestration.orchestrator import OrchestratorConfig
from git_ai_reporter.orchestration.orchestrator import OrchestratorServices
from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.writing.artifact_writer import ArtifactWriter


@pytest.fixture
def mock_git_analyzer() -> MagicMock:
    """Create a mock GitAnalyzer."""
    analyzer = MagicMock(spec=GitAnalyzer)
    analyzer.get_commits_in_range = MagicMock()
    analyzer.get_commit_diff = MagicMock(return_value="diff content")
    analyzer.get_weekly_diff = MagicMock(return_value="weekly diff")
    return analyzer


@pytest.fixture
def mock_gemini_client() -> MagicMock:
    """Create a mock GeminiClient."""
    client = MagicMock(spec=GeminiClient)
    client.generate_commit_analysis = AsyncMock()
    client.synthesize_daily_summary = AsyncMock()
    client.generate_news_narrative = AsyncMock()
    client.generate_changelog_entries = AsyncMock()
    return client


@pytest.fixture
def mock_cache_manager() -> MagicMock:
    """Create a mock CacheManager."""
    cache = MagicMock(spec=CacheManager)
    cache.get_commit_analysis = AsyncMock(return_value=None)
    cache.set_commit_analysis = AsyncMock()
    cache.get_daily_summary = AsyncMock(return_value=None)
    cache.set_daily_summary = AsyncMock()
    cache.get_weekly_summary = AsyncMock(return_value=None)
    cache.set_weekly_summary = AsyncMock()
    return cache


@pytest.fixture
def mock_artifact_writer(tmp_path: Path) -> MagicMock:
    """Create a mock ArtifactWriter."""
    writer = MagicMock(spec=ArtifactWriter)
    writer.update_news_file = AsyncMock()
    writer.update_changelog_file = AsyncMock()
    writer.update_daily_updates_file = AsyncMock()
    writer.read_existing_daily_summaries = AsyncMock(return_value={})
    writer._read_historical_summaries = AsyncMock(return_value="")
    writer.news_path = tmp_path / "NEWS.md"
    writer.daily_updates_path = tmp_path / "DAILY_UPDATES.md"
    writer.changelog_path = tmp_path / "CHANGELOG.txt"
    return writer


@pytest.fixture
def orchestrator_fixture(
    mock_git_analyzer: MagicMock,
    mock_gemini_client: MagicMock,
    mock_cache_manager: MagicMock,
    mock_artifact_writer: MagicMock,
) -> AnalysisOrchestrator:
    """Create an AnalysisOrchestrator instance for testing."""
    console = MagicMock(spec=Console)
    services = OrchestratorServices(
        git_analyzer=mock_git_analyzer,
        gemini_client=mock_gemini_client,
        cache_manager=mock_cache_manager,
        artifact_writer=mock_artifact_writer,
        console=console,
    )
    config = OrchestratorConfig(
        no_cache=False,
        max_concurrent_tasks=10,
        debug=False,
    )
    return AnalysisOrchestrator(services=services, config=config)


class TestDailySummaryReuse:
    """Test cases for daily summary reuse functionality."""

    @pytest.mark.asyncio
    async def test_generate_daily_summaries_uses_existing(
        self,
        orchestrator_fixture: AnalysisOrchestrator,
        mock_artifact_writer: MagicMock,
        mock_gemini_client: MagicMock,
    ) -> None:
        """Test that existing daily summaries are reused instead of regenerated."""
        # Setup existing summaries
        existing_summaries = {
            "2025-08-10": "### 2025-08-10\n\nExisting summary for August 10.",
            "2025-08-09": "### 2025-08-09\n\nExisting summary for August 9.",
        }
        mock_artifact_writer.read_existing_daily_summaries.return_value = existing_summaries

        # Create mock commits for dates that have existing summaries
        commit1 = MagicMock()
        commit1.hexsha = "abc123"
        commit1.committed_datetime = datetime(2025, 8, 10, 12, 0, tzinfo=timezone.utc)

        commit2 = MagicMock()
        commit2.hexsha = "def456"
        commit2.committed_datetime = datetime(2025, 8, 9, 12, 0, tzinfo=timezone.utc)

        # Create a commit for a new date (no existing summary)
        commit3 = MagicMock()
        commit3.hexsha = "ghi789"
        commit3.committed_datetime = datetime(2025, 8, 11, 12, 0, tzinfo=timezone.utc)

        # Create analyses
        analysis1 = CommitAnalysis(
            changes=[Change(summary="Change 1", category="Bug Fix")],
            trivial=False,
        )
        analysis2 = CommitAnalysis(
            changes=[Change(summary="Change 2", category="New Feature")],
            trivial=False,
        )
        analysis3 = CommitAnalysis(
            changes=[Change(summary="Change 3", category="Refactoring")],
            trivial=False,
        )

        commit_and_analysis = [
            (commit1, analysis1),
            (commit2, analysis2),
            (commit3, analysis3),
        ]

        # Mock the synthesize_daily_summary to return a new summary for the new date
        mock_gemini_client.synthesize_daily_summary.return_value = "New summary for August 11"

        # Call the method
        summaries = await orchestrator_fixture._generate_daily_summaries(commit_and_analysis, None)

        # Verify that existing summaries were used
        check.equal(len(summaries), 3)

        # Check that existing summaries are in the result
        check.is_in("### 2025-08-10", "\n".join(summaries))
        check.is_in("Existing summary for August 10", "\n".join(summaries))
        check.is_in("### 2025-08-09", "\n".join(summaries))
        check.is_in("Existing summary for August 9", "\n".join(summaries))

        # Check that new summary was generated for August 11
        check.is_in("### 2025-08-11", "\n".join(summaries))
        check.is_in("New summary for August 11", "\n".join(summaries))

        # Verify that synthesize_daily_summary was called only once (for the new date)
        check.equal(mock_gemini_client.synthesize_daily_summary.call_count, 1)

    @pytest.mark.asyncio
    async def test_generate_daily_summaries_all_existing(
        self,
        orchestrator_fixture: AnalysisOrchestrator,
        mock_artifact_writer: MagicMock,
        mock_gemini_client: MagicMock,
    ) -> None:
        """Test that no API calls are made when all summaries already exist."""
        # Setup existing summaries for all dates
        existing_summaries = {
            "2025-08-10": "### 2025-08-10\n\nExisting summary for August 10.",
            "2025-08-09": "### 2025-08-09\n\nExisting summary for August 9.",
        }
        mock_artifact_writer.read_existing_daily_summaries.return_value = existing_summaries

        # Create mock commits for dates that all have existing summaries
        commit1 = MagicMock()
        commit1.hexsha = "abc123"
        commit1.committed_datetime = datetime(2025, 8, 10, 12, 0, tzinfo=timezone.utc)

        commit2 = MagicMock()
        commit2.hexsha = "def456"
        commit2.committed_datetime = datetime(2025, 8, 9, 12, 0, tzinfo=timezone.utc)

        analysis1 = CommitAnalysis(
            changes=[Change(summary="Change 1", category="Bug Fix")],
            trivial=False,
        )
        analysis2 = CommitAnalysis(
            changes=[Change(summary="Change 2", category="New Feature")],
            trivial=False,
        )

        commit_and_analysis = [
            (commit1, analysis1),
            (commit2, analysis2),
        ]

        # Call the method
        summaries = await orchestrator_fixture._generate_daily_summaries(commit_and_analysis, None)

        # Verify that existing summaries were used
        check.equal(len(summaries), 2)
        check.is_in("Existing summary for August 10", "\n".join(summaries))
        check.is_in("Existing summary for August 9", "\n".join(summaries))

        # Verify that synthesize_daily_summary was never called
        mock_gemini_client.synthesize_daily_summary.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_daily_summaries_debug_mode(
        self,
        mock_git_analyzer: MagicMock,
        mock_gemini_client: MagicMock,
        mock_cache_manager: MagicMock,
        mock_artifact_writer: MagicMock,
    ) -> None:
        """Test that debug mode prints appropriate messages for existing summaries."""
        # Create orchestrator with debug mode enabled
        console = MagicMock(spec=Console)
        services = OrchestratorServices(
            git_analyzer=mock_git_analyzer,
            gemini_client=mock_gemini_client,
            cache_manager=mock_cache_manager,
            artifact_writer=mock_artifact_writer,
            console=console,
        )
        config = OrchestratorConfig(
            no_cache=False,
            max_concurrent_tasks=10,
            debug=True,  # Enable debug mode
        )
        debug_orchestrator = AnalysisOrchestrator(services=services, config=config)

        # Setup existing summary
        existing_summaries = {
            "2025-08-10": "### 2025-08-10\n\nExisting summary.",
        }
        mock_artifact_writer.read_existing_daily_summaries.return_value = existing_summaries

        # Create mock commit for existing date
        commit = MagicMock()
        commit.hexsha = "abc123"
        commit.committed_datetime = datetime(2025, 8, 10, 12, 0, tzinfo=timezone.utc)

        analysis = CommitAnalysis(
            changes=[Change(summary="Change", category="Bug Fix")],
            trivial=False,
        )

        # Call the method
        await debug_orchestrator._generate_daily_summaries([(commit, analysis)], None)

        # Verify debug message was printed
        console.print.assert_any_call("  Using existing summary for: 2025-08-10")

    @pytest.mark.asyncio
    async def test_generate_daily_summaries_no_existing(
        self,
        orchestrator_fixture: AnalysisOrchestrator,
        mock_artifact_writer: MagicMock,
        mock_gemini_client: MagicMock,
    ) -> None:
        """Test normal generation when no existing summaries are found."""
        # No existing summaries
        mock_artifact_writer.read_existing_daily_summaries.return_value = {}

        # Create mock commits
        commit = MagicMock()
        commit.hexsha = "abc123"
        commit.committed_datetime = datetime(2025, 8, 10, 12, 0, tzinfo=timezone.utc)

        analysis = CommitAnalysis(
            changes=[Change(summary="New change", category="New Feature")],
            trivial=False,
        )

        # Mock the synthesize_daily_summary
        mock_gemini_client.synthesize_daily_summary.return_value = "Generated summary"

        # Call the method
        summaries = await orchestrator_fixture._generate_daily_summaries([(commit, analysis)], None)

        # Verify that new summary was generated
        check.equal(len(summaries), 1)
        check.is_in("### 2025-08-10", summaries[0])
        check.is_in("Generated summary", summaries[0])

        # Verify that synthesize_daily_summary was called
        mock_gemini_client.synthesize_daily_summary.assert_called_once()
