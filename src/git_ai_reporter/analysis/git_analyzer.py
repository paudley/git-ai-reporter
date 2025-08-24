# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""This module handles all interactions with the Git repository."""

from datetime import datetime
from datetime import timedelta
import re
from typing import Final, TYPE_CHECKING

from git import Commit
from git import Repo
from git.diff import Diff
from git.diff import DiffIndex
from git.exc import GitCommandError
from pydantic import BaseModel

from ..utils import git_command_runner

if TYPE_CHECKING:
    pass


_MIN_COMMITS_FOR_WEEKLY_DIFF: Final[int] = 2


class GitAnalyzerConfig(BaseModel):
    """Configuration for the GitAnalyzer."""

    trivial_commit_types: list[str]
    trivial_file_patterns: list[str]
    git_command_timeout: int
    debug: bool = False


class GitAnalyzer:
    """Handles all interactions with the Git repository."""

    def __init__(self, repo: Repo, config: GitAnalyzerConfig):
        """Initializes the GitAnalyzer.

        Args:
            repo: An initialized GitPython Repo object.
            config: A configuration object with heuristic settings.
        """
        self.repo = repo
        self._trivial_commit_types = config.trivial_commit_types
        self._trivial_file_patterns = config.trivial_file_patterns
        self._git_command_timeout = config.git_command_timeout
        self._debug = config.debug

    def get_commits_in_range(self, start_date: datetime, end_date: datetime) -> list[Commit]:
        """Fetches commits within a specific datetime range.

        Args:
            start_date: The start of the date range (inclusive).
            end_date: The end of the date range (inclusive through end of day).

        Returns:
            A list of Commit objects, sorted by commit date.
        """
        try:
            # Add 1 day to end_date to make it inclusive through the end of that day
            # Git's 'before' parameter is exclusive, so we need the next day at midnight
            end_date_inclusive = end_date + timedelta(days=1)
            commits = list(
                self.repo.iter_commits(
                    "--all", after=start_date.isoformat(), before=end_date_inclusive.isoformat()
                )
            )
            return sorted(commits, key=lambda c: c.committed_datetime)
        except GitCommandError:
            return []

    def _is_trivial_by_message(self, commit: Commit) -> bool:
        """Checks if a commit is trivial based on its message prefix.

        Args:
            commit: The Commit object to analyze.

        Returns:
            True if the commit message starts with a defined triviality prefix.
        """
        message = commit.message
        if isinstance(message, bytes):
            message = message.decode("utf-8", "ignore")
        msg_lower = message.lower()
        return any(
            msg_lower.startswith(f"{trivial_type}:") or msg_lower.startswith(f"{trivial_type}(")
            for trivial_type in self._trivial_commit_types
        )

    def _is_trivial_by_file_paths(self, diffs: DiffIndex[Diff]) -> bool:
        """Checks if all files in a diff match trivial patterns.

        Args:
            diffs: The DiffIndex object containing all file changes.

        Returns:
            True if all changed file paths match a trivial pattern.
        """
        for diff_item in diffs:
            if not (path := diff_item.a_path or diff_item.b_path):
                return False  # Should not happen, but not trivial

            if not any(re.search(pattern, path) for pattern in self._trivial_file_patterns):
                return False  # Found one non-trivial file
        return True  # All files were trivial

    def get_commit_diff(self, commit: Commit) -> str:
        """Gets the diff string for a single commit against its first parent.

        Args:
            commit: The commit to generate a diff for.

        Returns:
            The raw diff text as a string.
        """
        command_args = (
            ["show", commit.hexsha]
            if not commit.parents
            else ["diff", commit.parents[0].hexsha, commit.hexsha]
        )

        try:
            return git_command_runner.run_git_command(
                str(self.repo.working_dir),
                *command_args,
                timeout=self._git_command_timeout,
                debug=self._debug,
            )
        except git_command_runner.GitCommandError as e:
            if self._debug:
                raise e
            return ""

    def get_weekly_diff(self, week_commits: list[Commit]) -> str:
        """Gets a consolidated diff for a list of commits (e.g., a week).

        Args:
            week_commits: A list of commits representing one week of work.

        Returns:
            A single, consolidated diff string representing the net changes
            over the week.
        """
        if len(week_commits) < _MIN_COMMITS_FOR_WEEKLY_DIFF:
            return self.get_commit_diff(week_commits[0]) if week_commits else ""

        first_commit = week_commits[0]
        last_commit = week_commits[-1]

        # Determine the parent of the first commit in a thread-safe way.
        if (
            start_commit_parent_sha := (
                first_commit.parents[0].hexsha if first_commit.parents else None
            )
        ) is None:
            # Handle root commit case
            return self.get_commit_diff(last_commit)

        try:
            return git_command_runner.run_git_command(
                str(self.repo.working_dir),
                "diff",
                start_commit_parent_sha,
                last_commit.hexsha,
                timeout=self._git_command_timeout,
                debug=self._debug,
            )
        except git_command_runner.GitCommandError as e:
            if self._debug:
                raise e
            return ""

    def get_first_commit_date(self) -> datetime | None:
        """Gets the date of the first commit in the repository.

        Returns:
            The commit date of the first (oldest) commit, or None if no commits exist.
        """
        try:
            # Get the first commit by getting all commits and taking the last one
            # (since iter_commits returns newest first)
            if not (commits := list(self.repo.iter_commits("--all"))):
                return None
            return commits[-1].committed_datetime
        except GitCommandError:
            return None
