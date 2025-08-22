# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""This module orchestrates the entire analysis and report generation process."""

import asyncio
from collections import defaultdict
from collections.abc import Coroutine
from datetime import date
from datetime import datetime
from typing import Any

from git import Commit
from pydantic import BaseModel
from pydantic import ConfigDict
from rich.console import Console
from rich.progress import BarColumn
from rich.progress import MofNCompleteColumn
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TaskID
from rich.progress import TextColumn
from rich.progress import TimeRemainingColumn
import typer

from ..analysis.git_analyzer import GitAnalyzer
from ..cache.manager import CacheManager
from ..models import AnalysisResult
from ..models import CommitAnalysis
from ..prompt_fitting.prompt_fitting import fit_git_diff
from ..services.gemini import _GeminiTokenCounter
from ..services.gemini import GeminiClient
from ..services.gemini import GeminiClientError
from ..writing.artifact_writer import ArtifactWriter
from ..writing.artifact_writer import NewsFileParams


class OrchestratorServices(BaseModel):
    """Service dependencies for the AnalysisOrchestrator."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    git_analyzer: GitAnalyzer
    gemini_client: GeminiClient
    cache_manager: CacheManager
    artifact_writer: ArtifactWriter
    console: Console


class OrchestratorConfig(BaseModel):
    """Configuration parameters for the AnalysisOrchestrator."""

    no_cache: bool
    max_concurrent_tasks: int
    debug: bool = False


class WeeklyAnalysis(BaseModel):
    """A data contract for the results of analyzing a single week."""

    weekly_summary: str | None
    daily_summaries: list[str]
    changelog_entries: list[CommitAnalysis]


class WritingTaskParams(BaseModel):
    """Parameters for preparing writing tasks."""

    final_narrative: str | None
    final_changelog: str | None
    result: AnalysisResult
    start_date: datetime
    end_date: datetime


class DailySummaryTaskParams(BaseModel):
    """Parameters for daily summary task creation."""

    model_config = {"arbitrary_types_allowed": True}

    commit_date: date
    day_data: list[tuple[Commit, CommitAnalysis]]
    existing_summaries: dict[str, str]
    progress: Progress | None
    daily_task: TaskID | None


class ArtifactGenerationParams(BaseModel):
    """Parameters for artifact generation."""

    model_config = {"arbitrary_types_allowed": True}

    result: AnalysisResult
    start_date: datetime
    end_date: datetime
    all_commits: list[Commit]


class AnalysisOrchestrator:
    """Orchestrates the git analysis, AI summarization, and artifact writing."""

    def __init__(
        self,
        *,
        services: OrchestratorServices,
        config: OrchestratorConfig,
    ):
        """Initializes the AnalysisOrchestrator.

        Args:
            services: Service dependencies for the orchestrator.
            config: Configuration parameters for the orchestrator.
        """
        self.services = services
        self.config = config

    async def run(self, start_date: datetime, end_date: datetime) -> None:
        """Executes the full analysis and report generation workflow.

        Args:
            start_date: The start date for the analysis range.
            end_date: The end date for the analysis range.

        Raises:
            typer.Exit: If no commits are found in the specified range.
        """
        self.services.console.print(
            f"Analyzing repository from {start_date.date()} to {end_date.date()}..."
        )

        if not (
            all_commits := await asyncio.to_thread(
                self.services.git_analyzer.get_commits_in_range, start_date, end_date
            )
        ):
            self.services.console.print("No commits found in the specified timeframe.")
            raise typer.Exit()

        if self.config.debug:
            self.services.console.print("[bold yellow]DEBUG MODE ENABLED[/bold yellow]")
            analysis_result = await self._analyze_commits_by_week(all_commits, None)

            if not analysis_result.changelog_entries and not analysis_result.daily_summaries:
                self.services.console.print("No non-trivial commits found to analyze.")
                return

            params = ArtifactGenerationParams.model_construct(
                result=analysis_result,
                start_date=start_date,
                end_date=end_date,
                all_commits=all_commits,
            )
            stats = await self._generate_and_write_artifacts(params, None)
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=self.services.console,
            ) as progress:
                analysis_result = await self._analyze_commits_by_week(all_commits, progress)

                if not analysis_result.changelog_entries and not analysis_result.daily_summaries:
                    self.services.console.print("No non-trivial commits found to analyze.")
                    return

                params = ArtifactGenerationParams.model_construct(
                    result=analysis_result,
                    start_date=start_date,
                    end_date=end_date,
                    all_commits=all_commits,
                )
                stats = await self._generate_and_write_artifacts(params, progress)

        self.services.console.print("\nAnalysis complete.", style="bold green")
        if stats:
            self.services.console.print(stats)

    async def _analyze_one_commit(self, commit: Commit) -> tuple[Commit, CommitAnalysis]:
        """Analyzes a single commit, running blocking I/O in a separate thread.

        Args:
            commit: The commit to analyze.

        Returns:
            A tuple of the commit and its analysis.

        Raises:
            GeminiClientError: If the analysis fails after all retries.
        """
        if not self.config.no_cache and (
            cached_analysis := await self.services.cache_manager.get_commit_analysis(commit.hexsha)
        ):
            return commit, cached_analysis

        try:
            diff = await asyncio.to_thread(self.services.git_analyzer.get_commit_diff, commit)

            analysis = await self.services.gemini_client.generate_commit_analysis(diff)
            await self.services.cache_manager.set_commit_analysis(commit.hexsha, analysis)
            return commit, analysis
        except Exception as e:
            # Enhanced error message with commit details for better debugging
            raise GeminiClientError(
                f"Failed to analyze commit {commit.hexsha[:7]} "
                f"({commit.summary[:60]!r}...): {e}"
            ) from e

    async def _get_commit_analyses(
        self, commits: list[Commit], progress: Progress | None
    ) -> list[tuple[Commit, CommitAnalysis]]:
        """Analyzes a list of commits concurrently and returns pairs of (commit, analysis).

        Args:
            commits: A list of Commit objects to analyze.
            progress: The rich Progress object to update, or None in debug mode.

        Returns:
            A list of tuples, where each tuple contains the original Commit object
            and its corresponding CommitAnalysis result from the AI.
        """
        commit_task = (
            progress.add_task("Analyzing commits", total=len(commits)) if progress else None
        )

        async def _analyze_and_update(commit: Commit) -> tuple[Commit, CommitAnalysis]:
            if self.config.debug:
                self.services.console.print(f"  Analyzing commit: {commit.hexsha[:7]}")
            result = await self._analyze_one_commit(commit)
            if progress and commit_task is not None:
                progress.update(commit_task, advance=1)
            return result

        tasks = [_analyze_and_update(commit) for commit in commits]
        if self.config.debug:
            results = []
            for task in tasks:
                results.append(await task)
        else:
            results = await asyncio.gather(*tasks)
        if progress and commit_task is not None:
            progress.remove_task(commit_task)

        # No longer need to filter Nones, as failures will raise exceptions
        return results

    async def _summarize_one_day(
        self,
        commit_date: date,
        day_commits_and_analyses: list[tuple[Commit, CommitAnalysis]],
    ) -> str | None:
        """Generates a summary for a single day's commits.

        Args:
            commit_date: The date of the commits.
            day_commits_and_analyses: A list of Commit and CommitAnalysis tuples for the given day.

        Returns:
            A formatted summary string or None if generation fails.
        """
        day_commits = [commit for commit, _ in day_commits_and_analyses]
        day_hexshas = [c.hexsha for c in day_commits]
        if not self.config.no_cache and (
            cached_summary := await self.services.cache_manager.get_daily_summary(
                commit_date, day_hexshas
            )
        ):
            return f"### {commit_date.strftime('%Y-%m-%d')}\n\n{cached_summary}"

        log_entries = []
        for _, analysis in day_commits_and_analyses:
            for change in analysis.changes:
                log_entries.append(f"- {change.summary} ({change.category})")
        if not (full_log := "\n".join(log_entries)):
            return None

        if not (
            daily_diff := await asyncio.to_thread(
                self.services.git_analyzer.get_weekly_diff, day_commits
            )
        ):
            return None

        try:
            if daily_summary := await self.services.gemini_client.synthesize_daily_summary(
                full_log, daily_diff
            ):
                await self.services.cache_manager.set_daily_summary(
                    commit_date, day_hexshas, daily_summary
                )
                return f"### {commit_date.strftime('%Y-%m-%d')}\n\n{daily_summary}"
        except GeminiClientError as e:
            if self.config.debug:
                raise e
            self.services.console.print(
                f"Skipping daily summary for {commit_date}: {e}", style="yellow"
            )
        return None

    def _group_commits_by_date(
        self, commit_and_analysis: list[tuple[Commit, CommitAnalysis]]
    ) -> dict[date, list[tuple[Commit, CommitAnalysis]]]:
        """Groups commit analysis pairs by their commit dates.

        Args:
            commit_and_analysis: A list of (Commit, CommitAnalysis) tuples.

        Returns:
            A dictionary mapping dates to lists of commit analysis pairs.
        """
        daily_commits: dict[date, list[tuple[Commit, CommitAnalysis]]] = defaultdict(list)
        for commit, analysis in commit_and_analysis:
            commit_date = commit.committed_datetime.date()
            daily_commits[commit_date].append((commit, analysis))
        return daily_commits

    async def _create_daily_summary_task(self, params: DailySummaryTaskParams) -> str | None:
        """Creates a summary task for a single day, reusing existing summaries when possible.

        Args:
            params: Parameters for creating the daily summary task.

        Returns:
            A summary string or None if generation fails.
        """
        # Check if we already have a summary for this date
        if (date_str := params.commit_date.strftime("%Y-%m-%d")) in params.existing_summaries:
            if self.config.debug:
                self.services.console.print(f"  Using existing summary for: {params.commit_date}")
            if params.progress and params.daily_task is not None:
                params.progress.update(params.daily_task, advance=1)
            # Return the existing summary
            return params.existing_summaries[date_str]

        # Generate new summary only if it doesn't exist
        if self.config.debug:
            self.services.console.print(f"  Generating daily summary for: {params.commit_date}")
        summary = await self._summarize_one_day(params.commit_date, params.day_data)
        if params.progress and params.daily_task is not None:
            params.progress.update(params.daily_task, advance=1)
        return summary

    async def _execute_daily_summary_tasks(
        self,
        sorted_days: list[tuple[date, list[tuple[Commit, CommitAnalysis]]]],
        existing_summaries: dict[str, str],
        progress: Progress | None,
        daily_task: TaskID | None,
    ) -> list[str | None]:
        """Executes daily summary tasks either sequentially or concurrently.

        Args:
            sorted_days: List of date and commit analysis pairs, sorted by date.
            existing_summaries: Dictionary of existing daily summaries.
            progress: The rich Progress object to update, or None in debug mode.
            daily_task: The task ID for progress tracking.

        Returns:
            A list of summary strings, with None for failed generations.
        """
        tasks = [
            self._create_daily_summary_task(
                DailySummaryTaskParams.model_construct(
                    commit_date=commit_date,
                    day_data=day_commits,
                    existing_summaries=existing_summaries,
                    progress=progress,
                    daily_task=daily_task,
                )
            )
            for commit_date, day_commits in sorted_days
        ]

        if self.config.debug:
            daily_summaries = []
            for task in tasks:
                daily_summaries.append(await task)
        else:
            daily_summaries = await asyncio.gather(*tasks)

        return daily_summaries

    async def _generate_daily_summaries(
        self,
        commit_and_analysis: list[tuple[Commit, CommitAnalysis]],
        progress: Progress | None,
    ) -> list[str]:
        """Groups analyses by day and generates a summary for each day.

        Checks for existing daily summaries in DAILY_UPDATES.md and reuses them
        instead of regenerating, saving API calls and ensuring consistency.

        Args:
            commit_and_analysis: A list of (Commit, CommitAnalysis) tuples.
            progress: The rich Progress object to update, or None in debug mode.

        Returns:
            A list of strings, where each string is an AI-generated summary for one
            day of development activity.
        """
        # Read existing daily summaries to avoid regenerating them
        existing_summaries = await self.services.artifact_writer.read_existing_daily_summaries()

        if not (daily_commits := self._group_commits_by_date(commit_and_analysis)):
            return []

        sorted_days = sorted(daily_commits.items())
        daily_task = (
            progress.add_task("Generating daily summaries", total=len(sorted_days))
            if progress
            else None
        )

        daily_summaries = await self._execute_daily_summary_tasks(
            sorted_days, existing_summaries, progress, daily_task
        )

        if progress and daily_task is not None:
            progress.remove_task(daily_task)

        return [summary for summary in daily_summaries if summary is not None]

    def _extract_commit_messages(self, commits: list[Commit]) -> list[str]:
        """Extract commit messages from a list of commits."""
        return [
            c.message.decode("utf-8", "ignore") if isinstance(c.message, bytes) else str(c.message)
            for c in commits
        ]

    async def _get_or_generate_weekly_summary(
        self,
        week_num: tuple[int, int],
        commits_in_week: list[Commit],
        non_trivial_commits: list[Commit],
    ) -> str | None:
        """Gets a weekly summary from cache or generates it if not present.

        Args:
            week_num: The week number tuple (year, week).
            commits_in_week: All commits in the week.
            non_trivial_commits: Filtered list of non-trivial commits.

        Returns:
            The weekly summary string, or None.
        """
        week_num_str = f"{week_num[0]}-{week_num[1]}"
        week_hexshas = [c.hexsha for c in commits_in_week]

        if not self.config.no_cache and (
            cached_summary := await self.services.cache_manager.get_weekly_summary(
                week_num_str, week_hexshas
            )
        ):
            self.services.console.print("Loaded weekly summary for NEWS.md from cache.")
            return cached_summary

        # Generate weekly summary for all commits (complete coverage required)
        if not (
            weekly_diff := await asyncio.to_thread(
                self.services.git_analyzer.get_weekly_diff, commits_in_week
            )
        ):
            return None

        self.services.console.print(
            f"Generating weekly summary for {len(commits_in_week)} commits..."
        )
        messages = self._extract_commit_messages(non_trivial_commits)
        weekly_log = "\n".join(messages)

        # 🚨 CLAUDE.md COMPLIANCE: Complete Data Integrity Enforcement 🚨
        # This replaces the previous MAX_DIFF_LINES truncation (FORBIDDEN)
        # Uses data-preserving prompt fitting with overlapping chunks
        # CRITICAL: NO truncation or data loss allowed per CLAUDE.md requirements

        # Create token counter using same model as Gemini service
        token_counter = _GeminiTokenCounter(
            self.services.gemini_client._client, self.services.gemini_client._config.model_tier2
        )

        # This will preserve ALL data through overlapping chunks if needed
        weekly_diff = await fit_git_diff(
            weekly_diff,
            token_counter,
            max_tokens=800000,  # Conservative target to ensure processing succeeds
        )

        # Log successful data preservation
        self.services.console.print("[green]✓ Diff fitted with 100% data preservation[/green]")

        if summary := await self.services.gemini_client.synthesize_daily_summary(
            weekly_log, weekly_diff
        ):
            await self.services.cache_manager.set_weekly_summary(
                week_num_str, week_hexshas, summary
            )
            self.services.console.print(
                "Generated weekly summary for NEWS.md with 100% data preservation."
            )
        return summary

    async def _generate_standard_summary(
        self,
        all_commits: list[Commit],
        non_trivial_commits: list[Commit],
        week_num_str: str,
        week_hexshas: list[str],
    ) -> str | None:
        """Generate a standard weekly summary without caching logic.

        This is a helper method for testing that always generates a fresh summary
        without checking the cache first.

        Args:
            all_commits: All commits for the week.
            non_trivial_commits: Filtered list of non-trivial commits.
            week_num_str: Week identifier string.
            week_hexshas: List of commit hexshas for the week.

        Returns:
            The generated summary string, or None if no diff available.
        """
        # Generate weekly diff for all commits (complete coverage required)
        if not (
            weekly_diff := await asyncio.to_thread(
                self.services.git_analyzer.get_weekly_diff, all_commits
            )
        ):
            return None

        self.services.console.print(
            f"Generating standard summary for {len(all_commits)} commits..."
        )
        messages = self._extract_commit_messages(non_trivial_commits)
        weekly_log = "\n".join(messages)

        # 🚨 CLAUDE.md COMPLIANCE: Complete Data Integrity Enforcement 🚨
        # Uses data-preserving prompt fitting with overlapping chunks
        # CRITICAL: NO truncation or data loss allowed per CLAUDE.md requirements

        # Create token counter using same model as Gemini service
        token_counter = _GeminiTokenCounter(
            self.services.gemini_client._client, self.services.gemini_client._config.model_tier2
        )

        # This will preserve ALL data through overlapping chunks if needed
        weekly_diff = await fit_git_diff(
            weekly_diff,
            token_counter,
            max_tokens=800000,  # Conservative target to ensure processing succeeds
        )

        # Log successful data preservation
        self.services.console.print("[green]✓ Diff fitted with 100% data preservation[/green]")

        if summary := await self.services.gemini_client.synthesize_daily_summary(
            weekly_log, weekly_diff
        ):
            await self.services.cache_manager.set_weekly_summary(
                week_num_str, week_hexshas, summary
            )
            self.services.console.print("Generated standard summary with 100% data preservation.")
        return summary

    async def _analyze_one_week(
        self,
        week_num: tuple[int, int],
        commits_in_week: list[Commit],
        progress: Progress | None,
    ) -> WeeklyAnalysis:
        """Analyzes a single week of commits.

        This function orchestrates the three levels of analysis for a given week:
        1. Individual commit analysis (Tier 1).
        2. Daily summary synthesis (Tier 2).
        3. Weekly consolidated diff summary (Tier 2).

        Args:
            week_num: A tuple representing the (year, week_number).
            commits_in_week: A list of commits for the given week.
            progress: The rich Progress object to update, or None in debug mode.

        Returns:
            A data class containing the high-level weekly summary, a list of
            daily summaries, and a list of all individual commit analyses.
        """
        # Analyze all commits once. The analysis now includes triviality.
        commit_and_analysis = await self._get_commit_analyses(commits_in_week, progress)

        # Filter for non-trivial commits for use in weekly summary and changelog.
        non_trivial_results = [
            (commit, analysis) for commit, analysis in commit_and_analysis if not analysis.trivial
        ]
        non_trivial_commits = [commit for commit, _ in non_trivial_results]
        non_trivial_changelog_entries = [analysis for _, analysis in non_trivial_results]

        daily_summaries = await self._generate_daily_summaries(non_trivial_results, progress)

        weekly_summary = await self._get_or_generate_weekly_summary(
            week_num, commits_in_week, non_trivial_commits
        )

        return WeeklyAnalysis(
            weekly_summary=weekly_summary,
            daily_summaries=daily_summaries,
            changelog_entries=non_trivial_changelog_entries,
        )

    async def _analyze_commits_by_week(
        self, all_commits: list[Commit], progress: Progress | None
    ) -> AnalysisResult:
        """Groups all commits by week and analyzes each week.

        Args:
            all_commits: A list of all commits in the specified date range.
            progress: The rich Progress object to update, or None in debug mode.

        Returns:
            A single AnalysisResult object containing the aggregated results from all weeks.
        """
        weekly_commits: dict[tuple[int, int], list[Commit]] = defaultdict(list)
        for commit in all_commits:
            week_number = commit.committed_datetime.isocalendar()[:2]
            weekly_commits[week_number].append(commit)

        all_period_summaries: list[str] = []
        all_daily_summaries: list[str] = []
        all_changelog_entries: list[CommitAnalysis] = []

        sorted_weeks = sorted(weekly_commits.items())
        week_task = (
            progress.add_task("Processing by week", total=len(sorted_weeks)) if progress else None
        )

        for week_num, commits_in_week in sorted_weeks:
            if self.config.debug:
                self.services.console.print(f"Processing week: {week_num[0]}-W{week_num[1]}")
            weekly_result = await self._analyze_one_week(week_num, commits_in_week, progress)
            all_daily_summaries.extend(weekly_result.daily_summaries)
            if weekly_result.weekly_summary:
                all_period_summaries.append(weekly_result.weekly_summary)
            all_changelog_entries.extend(weekly_result.changelog_entries)
            if progress and week_task is not None:
                progress.update(week_task, advance=1)

        if progress and week_task is not None:
            progress.remove_task(week_task)

        return AnalysisResult(
            period_summaries=all_period_summaries,
            daily_summaries=all_daily_summaries,
            changelog_entries=all_changelog_entries,
        )

    async def _get_or_generate_narrative(
        self,
        result: AnalysisResult,
        all_commits: list[Commit],
        progress: Progress | None,
    ) -> str | None:
        """Gets the final narrative from cache or generates it if not present."""
        del progress  # Unused but kept for API consistency
        if not self.config.no_cache and (
            cached_narrative := await self.services.cache_manager.get_final_narrative(result)
        ):
            self.services.console.print("Loaded final narrative from cache.")
            return cached_narrative

        if not (
            period_diff := await asyncio.to_thread(
                self.services.git_analyzer.get_weekly_diff, all_commits
            )
        ):
            return None

        history = (
            await self.services.artifact_writer._read_historical_summaries()
        )  # pylint: disable=protected-access

        daily_summaries_text = "\n\n".join(result.daily_summaries)

        summaries_list = []
        for entry in result.changelog_entries:
            for change in entry.changes:
                summaries_list.append(f"- {change.summary} ({change.category})")
        detailed_commits_text = "\n".join(summaries_list)

        narrative = await self.services.gemini_client.generate_news_narrative(
            commit_summaries=detailed_commits_text,
            daily_summaries=daily_summaries_text,
            weekly_diff=period_diff,
            history=history,
        )
        if narrative:
            await self.services.cache_manager.set_final_narrative(result, narrative)
            return narrative
        return None

    async def _get_or_generate_changelog(
        self, entries: list[CommitAnalysis], progress: Progress | None
    ) -> str | None:
        """Gets the final changelog from cache or generates it if not present."""
        del progress  # Unused but kept for API consistency
        if not self.config.no_cache and (
            cached_changelog := await self.services.cache_manager.get_changelog_entries(entries)
        ):
            self.services.console.print("Loaded final changelog from cache.")
            return cached_changelog

        categorized_summaries = []
        for entry in entries:
            for change in entry.changes:
                categorized_summaries.append(
                    {"summary": change.summary, "category": change.category}
                )

        if not categorized_summaries:
            return None

        if changelog := await self.services.gemini_client.generate_changelog_entries(
            categorized_summaries
        ):
            await self.services.cache_manager.set_changelog_entries(entries, changelog)
            return changelog
        return None

    def _prepare_generation_tasks(
        self,
        result: AnalysisResult,
        all_commits: list[Commit],
        progress: Progress | None,
    ) -> tuple[
        list[Coroutine[Any, Any, str | None]],
        Coroutine[Any, Any, str | None] | None,
        Coroutine[Any, Any, str | None] | None,
    ]:
        """Prepare content generation tasks."""
        generation_tasks = []
        narrative_task, changelog_task = None, None

        if result.changelog_entries or result.daily_summaries:
            if self.config.debug:
                self.services.console.print("Generating narrative...")
            narrative_task = self._get_or_generate_narrative(result, all_commits, progress)
            generation_tasks.append(narrative_task)
        if result.changelog_entries:
            if self.config.debug:
                self.services.console.print("Generating changelog...")
            changelog_task = self._get_or_generate_changelog(result.changelog_entries, progress)
            generation_tasks.append(changelog_task)

        return generation_tasks, narrative_task, changelog_task

    def _prepare_writing_tasks(self, params: WritingTaskParams) -> list[Coroutine[Any, Any, None]]:
        """Prepare file writing tasks."""
        writing_tasks = []
        if params.final_narrative:
            if self.config.debug:
                self.services.console.print(
                    f"  Writing file: {self.services.artifact_writer.news_path.name}"
                )
            news_params = NewsFileParams(
                narrative=params.final_narrative,
                start_date=params.start_date,
                end_date=params.end_date,
                gemini_client=self.services.gemini_client,
            )
            writing_tasks.append(self.services.artifact_writer.update_news_file(news_params))
        if params.result.daily_summaries:
            if self.config.debug:
                self.services.console.print(
                    f"  Writing file: {self.services.artifact_writer.daily_updates_path.name}"
                )
            writing_tasks.append(
                self.services.artifact_writer.update_daily_updates_file(
                    params.result.daily_summaries
                )
            )
        if params.final_changelog:
            if self.config.debug:
                self.services.console.print(
                    f"  Writing file: {self.services.artifact_writer.changelog_path.name}"
                )
            writing_tasks.append(
                self.services.artifact_writer.update_changelog_file(params.final_changelog)
            )
        return writing_tasks

    def _build_stats_message(
        self,
        final_narrative: str | None,
        final_changelog: str | None,
        result: AnalysisResult,
    ) -> str | None:
        """Build statistics message for completed tasks."""
        stats = []
        if final_narrative:
            stats.append(
                f"Wrote narrative to [bold magenta]{self.services.artifact_writer.news_path.name}[/]."
            )
        if final_changelog:
            stats.append(
                f"Updated [bold magenta]{self.services.artifact_writer.changelog_path.name}[/]."
            )
        if result.daily_summaries:
            stats.append(
                f"Updated [bold magenta]{self.services.artifact_writer.daily_updates_path.name}[/]."
            )
        return " ".join(stats) if stats else None

    async def _execute_generation_tasks(
        self,
        generation_tasks: list[Coroutine[Any, Any, str | None]],
        progress: Progress | None,
        generation_task: TaskID | None,
    ) -> list[str | None]:
        """Execute generation tasks and update progress."""
        if self.config.debug:
            generated_content = []
            for task in generation_tasks:
                generated_content.append(await task)
        else:
            generated_content = await asyncio.gather(*generation_tasks)

        if progress and generation_task is not None:
            progress.update(generation_task, completed=1)
            progress.remove_task(generation_task)
        return generated_content

    async def _execute_writing_tasks(
        self,
        writing_tasks: list[Coroutine[Any, Any, None]],
        progress: Progress | None,
        writing_task_id: TaskID | None,
    ) -> None:
        """Execute writing tasks and update progress."""
        if self.config.debug:
            for task in writing_tasks:
                await task
        else:
            await asyncio.gather(*writing_tasks)

        if progress and writing_task_id is not None:
            progress.update(writing_task_id, completed=1)
            progress.remove_task(writing_task_id)

    async def _generate_and_write_artifacts(
        self, params: ArtifactGenerationParams, progress: Progress | None = None
    ) -> str | None:
        """Generates the final content from summaries and writes to files concurrently.

        Args:
            params: The artifact generation parameters.
            progress: The rich Progress object to update, or None in debug mode.

        Returns:
            A statistics string summarizing the actions taken.
        """
        # --- Concurrent Content Generation ---
        generation_task = (
            progress.add_task("Generating final reports", total=1, completed=0)
            if progress
            else None
        )
        generation_tasks, narrative_task, changelog_task = self._prepare_generation_tasks(
            params.result, params.all_commits, progress
        )

        if not generation_tasks:
            if progress and generation_task is not None:
                progress.remove_task(generation_task)
            return None

        generated_content = await self._execute_generation_tasks(
            generation_tasks, progress, generation_task
        )

        # Extract results
        final_narrative = generated_content[0] if narrative_task else None
        final_changelog = (
            generated_content[1]
            if (narrative_task and changelog_task)
            else (generated_content[0] if changelog_task else None)
        )

        # --- Concurrent File Writing ---
        writing_task_id = (
            progress.add_task("Writing artifacts", total=1, completed=0) if progress else None
        )
        writing_params = WritingTaskParams.model_construct(
            final_narrative=final_narrative,
            final_changelog=final_changelog,
            result=params.result,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        if writing_tasks := self._prepare_writing_tasks(writing_params):
            await self._execute_writing_tasks(writing_tasks, progress, writing_task_id)

        return self._build_stats_message(final_narrative, final_changelog, params.result)
