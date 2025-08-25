# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for date range bug in get_commits_in_range."""

from datetime import datetime
from unittest.mock import MagicMock

import git
import pytest

from git_ai_reporter.analysis.git_analyzer import GitAnalyzer
from git_ai_reporter.analysis.git_analyzer import GitAnalyzerConfig

# Test constants
EXPECTED_COMMIT_COUNT_WITH_END_DATE = 4
EXPECTED_SINGLE_DAY_COUNT = 3
EXPECTED_ACTUAL_SCENARIO_COUNT = 2
LATE_EVENING_COMMIT = "feat: Important feature on Aug 23 late evening"
DOCS_COMMIT_AUG_25 = "docs: Documentation on Aug 25"
EXPECTED_COMMIT_HASH = "7702d0b"


class TestDateRangeBug:
    """Test that commits on the end_date are included in the range."""

    @pytest.fixture
    def analyzer_config(self) -> GitAnalyzerConfig:
        """Create a GitAnalyzerConfig for testing."""
        return GitAnalyzerConfig(
            trivial_commit_types=["style", "chore"],
            trivial_file_patterns=[],
            git_command_timeout=30,
            debug=False,
        )

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        """Create a mock repository with commits on specific dates."""
        repo = MagicMock(spec=git.Repo)

        # Create mock commits with specific timestamps
        commit1 = MagicMock(spec=git.Commit)
        commit1.hexsha = "abc123"
        commit1.message = "feat: First feature on Aug 23 morning"
        # August 23, 2025 at 10:00 AM
        commit1.committed_datetime = datetime(2025, 8, 23, 10, 0, 0)

        commit2 = MagicMock(spec=git.Commit)
        commit2.hexsha = "def456"
        commit2.message = "fix: Bug fix on Aug 23 afternoon"
        # August 23, 2025 at 3:00 PM
        commit2.committed_datetime = datetime(2025, 8, 23, 15, 0, 0)

        commit3 = MagicMock(spec=git.Commit)
        commit3.hexsha = "ghi789"
        commit3.message = "feat: Important feature on Aug 23 late evening"
        # August 23, 2025 at 10:48 PM (like the Allure commit)
        commit3.committed_datetime = datetime(2025, 8, 23, 22, 48, 0)

        commit4 = MagicMock(spec=git.Commit)
        commit4.hexsha = "jkl012"
        commit4.message = "test: Test added on Aug 24 morning"
        # August 24, 2025 at 9:00 AM
        commit4.committed_datetime = datetime(2025, 8, 24, 9, 0, 0)

        commit5 = MagicMock(spec=git.Commit)
        commit5.hexsha = "mno345"
        commit5.message = "docs: Documentation on Aug 25"
        # August 25, 2025 at 11:00 AM (should not be included)
        commit5.committed_datetime = datetime(2025, 8, 25, 11, 0, 0)

        return repo, [commit1, commit2, commit3, commit4, commit5]

    def test_end_date_commits_are_included(
        self, analyzer_config: GitAnalyzerConfig, mock_repo: tuple
    ) -> None:
        """Test that commits made on the end_date are included in the range.

        This test demonstrates the bug where commits on the end date (especially
        those late in the day) are excluded from analysis.
        """
        repo, all_commits = mock_repo

        # Set up the mock to return commits based on the date range
        def iter_commits_side_effect(*_args, **kwargs):
            """Mock iter_commits to filter by date."""
            after_str = kwargs.get("after", "")
            before_str = kwargs.get("before", "")

            # Parse the dates from ISO format
            after_date = datetime.fromisoformat(after_str) if after_str else datetime.min
            before_date = datetime.fromisoformat(before_str) if before_str else datetime.max

            # Git's 'before' is exclusive, 'after' is inclusive
            filtered = [
                c
                for c in all_commits
                if c.committed_datetime > after_date and c.committed_datetime < before_date
            ]
            return filtered

        repo.iter_commits.side_effect = iter_commits_side_effect

        # Create analyzer
        analyzer = GitAnalyzer(repo, analyzer_config)

        # Test case: Get commits from Aug 23 to Aug 24 (inclusive)
        start_date = datetime(2025, 8, 23, 0, 0, 0)
        end_date = datetime(2025, 8, 24, 0, 0, 0)

        commits = analyzer.get_commits_in_range(start_date, end_date)

        # Extract commit messages for easier assertion
        commit_messages = [c.message for c in commits]

        # EXPECTED: All commits from Aug 23 and Aug 24 should be included
        # That's commits 1, 2, 3 (Aug 23) and 4 (Aug 24)
        expected_messages = [
            "feat: First feature on Aug 23 morning",
            "fix: Bug fix on Aug 23 afternoon",
            "feat: Important feature on Aug 23 late evening",
            "test: Test added on Aug 24 morning",
        ]

        # This assertion will FAIL with the current implementation
        # because commits on Aug 24 (and possibly late Aug 23) are excluded
        assert (
            len(commits) == EXPECTED_COMMIT_COUNT_WITH_END_DATE
        ), f"Expected {EXPECTED_COMMIT_COUNT_WITH_END_DATE} commits, got {len(commits)}: {commit_messages}"
        assert all(
            msg in commit_messages for msg in expected_messages
        ), f"Missing commits. Expected: {expected_messages}, Got: {commit_messages}"

        # Specifically check for the late evening commit (like the Allure one)
        assert (
            LATE_EVENING_COMMIT in commit_messages
        ), "Late evening commit on end_date should be included"

        # Check that Aug 25 commit is NOT included
        assert (
            DOCS_COMMIT_AUG_25 not in commit_messages
        ), "Commits after end_date should not be included"

    def test_single_day_range_includes_all_commits(
        self, analyzer_config: GitAnalyzerConfig, mock_repo: tuple
    ) -> None:
        """Test that a single day range includes all commits from that day.

        When analyzing just August 23, all three commits from that day should be included.
        """
        repo, all_commits = mock_repo

        # Set up the mock
        def iter_commits_side_effect(*_args, **kwargs):
            """Mock iter_commits to filter by date."""
            after_str = kwargs.get("after", "")
            before_str = kwargs.get("before", "")

            after_date = datetime.fromisoformat(after_str) if after_str else datetime.min
            before_date = datetime.fromisoformat(before_str) if before_str else datetime.max

            filtered = [
                c
                for c in all_commits
                if c.committed_datetime > after_date and c.committed_datetime < before_date
            ]
            return filtered

        repo.iter_commits.side_effect = iter_commits_side_effect

        analyzer = GitAnalyzer(repo, analyzer_config)

        # Test: Get commits for just Aug 23
        start_date = datetime(2025, 8, 23, 0, 0, 0)
        end_date = datetime(2025, 8, 23, 0, 0, 0)  # Same day

        commits = analyzer.get_commits_in_range(start_date, end_date)
        commit_messages = [c.message for c in commits]

        # Should include ALL three Aug 23 commits, including the late evening one
        expected_messages = [
            "feat: First feature on Aug 23 morning",
            "fix: Bug fix on Aug 23 afternoon",
            "feat: Important feature on Aug 23 late evening",
        ]

        assert (
            len(commits) == EXPECTED_SINGLE_DAY_COUNT
        ), f"Expected {EXPECTED_SINGLE_DAY_COUNT} commits from Aug 23, got {len(commits)}: {commit_messages}"
        assert all(
            msg in commit_messages for msg in expected_messages
        ), f"Missing Aug 23 commits. Expected: {expected_messages}, Got: {commit_messages}"

    def test_actual_repository_scenario(self, analyzer_config: GitAnalyzerConfig) -> None:
        """Test the actual scenario from the repository where the Allure commit was missing.

        The commit "feat: add comprehensive Allure test reporting infrastructure"
        was made on 2025-08-23 22:48:47 but was not being processed.
        """
        repo = MagicMock(spec=git.Repo)

        # Create the actual Allure commit
        allure_commit = MagicMock(spec=git.Commit)
        allure_commit.hexsha = "7702d0b"
        allure_commit.message = "feat: add comprehensive Allure test reporting infrastructure"
        # Exact timestamp from the real commit
        allure_commit.committed_datetime = datetime(2025, 8, 23, 22, 48, 47)

        # Create another commit from earlier that day
        earlier_commit = MagicMock(spec=git.Commit)
        earlier_commit.hexsha = "9b0b8f7"
        earlier_commit.message = "fix: modernize build commands and resolve CodeQL issues"
        earlier_commit.committed_datetime = datetime(2025, 8, 23, 14, 30, 0)

        all_commits = [earlier_commit, allure_commit]

        def iter_commits_side_effect(*_args, **kwargs):
            """Mock iter_commits with actual git behavior."""
            after_str = kwargs.get("after", "")
            before_str = kwargs.get("before", "")

            after_date = datetime.fromisoformat(after_str) if after_str else datetime.min
            before_date = datetime.fromisoformat(before_str) if before_str else datetime.max

            # Git's behavior: after is inclusive, before is exclusive
            filtered = [
                c
                for c in all_commits
                if c.committed_datetime > after_date and c.committed_datetime < before_date
            ]
            return filtered

        repo.iter_commits.side_effect = iter_commits_side_effect

        analyzer = GitAnalyzer(repo, analyzer_config)

        # The command that was run: --start-date 2025-08-23 --end-date 2025-08-24
        # This creates datetime objects at midnight
        start_date = datetime(2025, 8, 23, 0, 0, 0)
        end_date = datetime(2025, 8, 24, 0, 0, 0)

        commits = analyzer.get_commits_in_range(start_date, end_date)
        commit_hexshas = [c.hexsha for c in commits]

        # The Allure commit MUST be included
        assert (
            EXPECTED_COMMIT_HASH in commit_hexshas
        ), f"Allure commit ({EXPECTED_COMMIT_HASH}) made at 22:48 on Aug 23 should be included. Got: {commit_hexshas}"

        # Both commits from Aug 23 should be there
        assert (
            len(commits) == EXPECTED_ACTUAL_SCENARIO_COUNT
        ), f"Expected {EXPECTED_ACTUAL_SCENARIO_COUNT} commits from Aug 23, got {len(commits)}: {[c.message for c in commits]}"
