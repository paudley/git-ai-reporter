# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Additional tests for git_analyzer to improve coverage."""

from unittest.mock import MagicMock

from git import GitCommandError
import pytest_check as check

from git_ai_reporter.analysis.git_analyzer import GitAnalyzer
from git_ai_reporter.analysis.git_analyzer import GitAnalyzerConfig


class TestGitAnalyzerCoverage:
    """Tests to cover specific uncovered lines in git_analyzer."""

    def test_get_first_commit_date_no_commits(self) -> None:
        """Test get_first_commit_date when no commits exist - covers line 182."""
        # Mock a repo with no commits
        mock_repo = MagicMock()
        mock_repo.iter_commits.return_value = []  # No commits

        config = GitAnalyzerConfig(
            trivial_commit_types=["chore", "docs", "style"],
            trivial_file_patterns=[r"\.md$", r"docs/", r"\.txt$"],
            git_command_timeout=300,
            debug=False,
        )

        analyzer = GitAnalyzer(repo=mock_repo, config=config)
        result = analyzer.get_first_commit_date()

        check.is_none(result)

    def test_get_first_commit_date_git_command_error(self) -> None:
        """Test get_first_commit_date when GitCommandError occurs - covers lines 184-185."""
        # Mock a repo that raises GitCommandError
        mock_repo = MagicMock()
        mock_repo.iter_commits.side_effect = GitCommandError("command failed")

        config = GitAnalyzerConfig(
            trivial_commit_types=["chore", "docs", "style"],
            trivial_file_patterns=[r"\.md$", r"docs/", r"\.txt$"],
            git_command_timeout=300,
            debug=False,
        )

        analyzer = GitAnalyzer(repo=mock_repo, config=config)
        result = analyzer.get_first_commit_date()

        check.is_none(result)
