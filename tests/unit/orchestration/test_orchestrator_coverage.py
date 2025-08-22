# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=too-many-arguments,too-many-positional-arguments
# pylint: disable=redefined-outer-name,unused-argument,duplicate-code
# pylint: disable=protected-access

"""Additional unit tests for orchestrator to achieve comprehensive coverage."""

from datetime import datetime
from datetime import timezone
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
import pytest_check as check
from rich.console import Console
from rich.progress import Progress

from git_ai_reporter.cache.manager import CacheManager
from git_ai_reporter.models import AnalysisResult
from git_ai_reporter.models import Change
from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.orchestration.orchestrator import AnalysisOrchestrator
from git_ai_reporter.orchestration.orchestrator import ArtifactGenerationParams
from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.services.gemini import GeminiClientError
from git_ai_reporter.writing.artifact_writer import ArtifactWriter


@pytest.fixture
def mock_git_analyzer() -> MagicMock:
    """Create a mock GitAnalyzer."""
    analyzer = MagicMock()
    analyzer.repo = MagicMock()
    analyzer.repo.working_dir = "/test/repo"
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
    cache.get_final_narrative = AsyncMock(return_value=None)
    cache.set_final_narrative = AsyncMock()
    cache.get_changelog_entries = AsyncMock(return_value=None)
    cache.set_changelog_entries = AsyncMock()
    return cache


@pytest.fixture
def mock_artifact_writer() -> MagicMock:
    """Create a mock ArtifactWriter."""
    writer = MagicMock(spec=ArtifactWriter)
    writer.update_news_file = AsyncMock()
    writer.update_changelog_file = AsyncMock()
    writer.update_daily_updates_file = AsyncMock()
    writer._read_historical_summaries = AsyncMock(
        return_value="Historical summaries"
    )  # pylint: disable=protected-access
    writer.news_path = MagicMock(name="NEWS.md")
    writer.daily_updates_path = MagicMock(name="DAILY_UPDATES.md")
    writer.changelog_path = MagicMock(name="CHANGELOG.txt")
    return writer


@pytest.fixture
def mock_console() -> MagicMock:
    """Create a mock Console."""
    console = MagicMock(spec=Console)
    console.print = MagicMock()
    return console


@pytest.fixture
def orchestrator(
    mock_git_analyzer: MagicMock,
    mock_gemini_client: MagicMock,
    mock_cache_manager: MagicMock,
    mock_artifact_writer: MagicMock,
    mock_console: MagicMock,
) -> AnalysisOrchestrator:
    """Create an AnalysisOrchestrator instance for testing."""
    return AnalysisOrchestrator(
        git_analyzer=mock_git_analyzer,
        gemini_client=mock_gemini_client,
        cache_manager=mock_cache_manager,
        artifact_writer=mock_artifact_writer,
        console=mock_console,
        no_cache=False,
        max_concurrent_tasks=10,
        debug=False,
    )


class TestOrchestratorCoverage:
    """Test suite for achieving comprehensive coverage in orchestrator."""

    @pytest.mark.asyncio
    async def test_summarize_one_day_no_full_log(
        self,
        orchestrator: AnalysisOrchestrator,  # pylint: disable=redefined-outer-name
        mock_git_analyzer: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _summarize_one_day when there's no full log (line 229)."""
        commit = MagicMock()
        commit.hexsha = "abc123"
        commit.committed_datetime = datetime(2025, 1, 1, tzinfo=timezone.utc)

        # Empty analysis results in no log entries
        analysis = CommitAnalysis(changes=[], trivial=False)
        day_commits_and_analyses = [(commit, analysis)]

        result = await orchestrator._summarize_one_day(
            commit.committed_datetime.date(), day_commits_and_analyses
        )

        check.is_none(result)

    @pytest.mark.asyncio
    async def test_summarize_one_day_no_daily_diff(
        self,
        orchestrator: AnalysisOrchestrator,  # pylint: disable=redefined-outer-name
        mock_git_analyzer: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _summarize_one_day when there's no daily diff (line 232)."""
        commit = MagicMock()
        commit.hexsha = "abc123"
        commit.committed_datetime = datetime(2025, 1, 1, tzinfo=timezone.utc)

        analysis = CommitAnalysis(
            changes=[Change(summary="Test change", category="New Feature")],
            trivial=False,
        )
        day_commits_and_analyses = [(commit, analysis)]

        # Mock get_weekly_diff to return None
        mock_git_analyzer.get_weekly_diff.return_value = None

        result = await orchestrator._summarize_one_day(
            commit.committed_datetime.date(), day_commits_and_analyses
        )

        check.is_none(result)

    @pytest.mark.asyncio
    async def test_summarize_one_day_gemini_error_debug_mode(
        self,
        mock_git_analyzer: MagicMock,  # pylint: disable=redefined-outer-name
        mock_gemini_client: MagicMock,  # pylint: disable=redefined-outer-name
        mock_cache_manager: MagicMock,  # pylint: disable=redefined-outer-name
        mock_artifact_writer: MagicMock,  # pylint: disable=redefined-outer-name
        mock_console: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _summarize_one_day with GeminiClientError in debug mode (lines 238-242)."""
        orchestrator_debug = AnalysisOrchestrator(
            git_analyzer=mock_git_analyzer,
            gemini_client=mock_gemini_client,
            cache_manager=mock_cache_manager,
            artifact_writer=mock_artifact_writer,
            console=mock_console,
            no_cache=False,
            max_concurrent_tasks=10,
            debug=True,  # Enable debug mode
        )

        commit = MagicMock()
        commit.hexsha = "abc123"
        commit.committed_datetime = datetime(2025, 1, 1, tzinfo=timezone.utc)

        analysis = CommitAnalysis(
            changes=[Change(summary="Test", category="New Feature")], trivial=False
        )
        day_commits_and_analyses = [(commit, analysis)]

        mock_git_analyzer.get_weekly_diff.return_value = "diff content"
        mock_gemini_client.synthesize_daily_summary.side_effect = GeminiClientError("API error")

        with pytest.raises(GeminiClientError):
            await orchestrator_debug._summarize_one_day(
                commit.committed_datetime.date(), day_commits_and_analyses
            )

    @pytest.mark.asyncio
    async def test_summarize_one_day_gemini_error_non_debug(
        self,
        orchestrator: AnalysisOrchestrator,  # pylint: disable=redefined-outer-name
        mock_git_analyzer: MagicMock,  # pylint: disable=redefined-outer-name
        mock_gemini_client: MagicMock,  # pylint: disable=redefined-outer-name
        mock_console: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _summarize_one_day with GeminiClientError in non-debug mode (lines 241-242)."""
        commit = MagicMock()
        commit.hexsha = "abc123"
        commit.committed_datetime = datetime(2025, 1, 1, tzinfo=timezone.utc)

        analysis = CommitAnalysis(
            changes=[Change(summary="Test", category="New Feature")], trivial=False
        )
        day_commits_and_analyses = [(commit, analysis)]

        mock_git_analyzer.get_weekly_diff.return_value = "diff content"
        mock_gemini_client.synthesize_daily_summary.side_effect = GeminiClientError("API error")

        result = await orchestrator._summarize_one_day(
            commit.committed_datetime.date(), day_commits_and_analyses
        )

        check.is_none(result)
        mock_console.print.assert_called_with(
            f"Skipping daily summary for {commit.committed_datetime.date()}: API error",
            style="yellow",
        )

    @pytest.mark.asyncio
    async def test_get_or_generate_weekly_summary_cached(
        self,
        orchestrator: AnalysisOrchestrator,  # pylint: disable=redefined-outer-name
        mock_cache_manager: MagicMock,  # pylint: disable=redefined-outer-name
        mock_console: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _get_or_generate_weekly_summary with cache hit (lines 310-311)."""
        commits = [MagicMock(hexsha=f"commit{i}") for i in range(3)]
        week_num = (2025, 1)

        mock_cache_manager.get_weekly_summary.return_value = "Cached weekly summary"

        result = await orchestrator._get_or_generate_weekly_summary(week_num, commits, commits)

        check.equal(result, "Cached weekly summary")
        mock_console.print.assert_called_with("Loaded weekly summary for NEWS.md from cache.")

    @pytest.mark.asyncio
    async def test_get_or_generate_weekly_summary_no_diff_no_summary(
        self,
        orchestrator: AnalysisOrchestrator,  # pylint: disable=redefined-outer-name
        mock_git_analyzer: MagicMock,  # pylint: disable=redefined-outer-name
        mock_gemini_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _get_or_generate_weekly_summary when no diff or summary is generated (line 324)."""
        commits = [MagicMock(hexsha=f"commit{i}") for i in range(3)]
        week_num = (2025, 1)

        # No diff available
        mock_git_analyzer.get_weekly_diff.return_value = None

        result = await orchestrator._get_or_generate_weekly_summary(week_num, commits, commits)

        check.is_none(result)

    @pytest.mark.asyncio
    async def test_get_or_generate_narrative_no_diff(
        self,
        orchestrator: AnalysisOrchestrator,  # pylint: disable=redefined-outer-name
        mock_git_analyzer: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _get_or_generate_narrative when no period diff available (line 422)."""
        result = AnalysisResult(
            period_summaries=["Summary"],
            daily_summaries=["Daily"],
            changelog_entries=[],
        )
        commits = [MagicMock()]

        mock_git_analyzer.get_weekly_diff.return_value = None

        narrative = await orchestrator._get_or_generate_narrative(result, commits, None)

        check.is_none(narrative)

    @pytest.mark.asyncio
    async def test_get_or_generate_narrative_no_narrative_generated(
        self,
        orchestrator: AnalysisOrchestrator,  # pylint: disable=redefined-outer-name
        mock_git_analyzer: MagicMock,  # pylint: disable=redefined-outer-name
        mock_gemini_client: MagicMock,  # pylint: disable=redefined-outer-name
        mock_artifact_writer: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _get_or_generate_narrative when Gemini returns None (line 443)."""
        result = AnalysisResult(
            period_summaries=["Summary"],
            daily_summaries=["Daily"],
            changelog_entries=[
                CommitAnalysis(
                    changes=[Change(summary="Test", category="New Feature")],
                    trivial=False,
                )
            ],
        )
        commits = [MagicMock()]

        mock_git_analyzer.get_weekly_diff.return_value = "diff"
        mock_gemini_client.generate_news_narrative.return_value = None

        narrative = await orchestrator._get_or_generate_narrative(result, commits, None)

        check.is_none(narrative)

    @pytest.mark.asyncio
    async def test_get_or_generate_changelog_no_summaries(
        self,
        orchestrator: AnalysisOrchestrator,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _get_or_generate_changelog with no summaries (line 458)."""
        entries: list[CommitAnalysis] = []

        changelog = await orchestrator._get_or_generate_changelog(entries, None)

        check.is_none(changelog)

    @pytest.mark.asyncio
    async def test_get_or_generate_changelog_no_changelog_generated(
        self,
        orchestrator: AnalysisOrchestrator,  # pylint: disable=redefined-outer-name
        mock_gemini_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _get_or_generate_changelog when Gemini returns None (line 463)."""
        entries = [
            CommitAnalysis(changes=[Change(summary="Test", category="New Feature")], trivial=False)
        ]

        mock_gemini_client.generate_changelog_entries.return_value = None

        changelog = await orchestrator._get_or_generate_changelog(entries, None)

        check.is_none(changelog)

    @pytest.mark.asyncio
    async def test_generate_and_write_artifacts_no_tasks(
        self,
        orchestrator: AnalysisOrchestrator,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _generate_and_write_artifacts with no generation tasks (lines 583-585)."""
        # Create params with empty result
        params = ArtifactGenerationParams.model_construct(
            result=AnalysisResult(period_summaries=[], daily_summaries=[], changelog_entries=[]),
            start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 1, 7, tzinfo=timezone.utc),
            all_commits=[],
        )

        # Create a mock progress
        mock_progress = MagicMock(spec=Progress)
        mock_progress.add_task = MagicMock(return_value=1)
        mock_progress.remove_task = MagicMock()

        result = await orchestrator._generate_and_write_artifacts(params, mock_progress)

        check.is_none(result)
        mock_progress.remove_task.assert_called_once_with(1)
