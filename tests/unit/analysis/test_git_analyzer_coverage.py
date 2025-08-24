# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Additional tests for git_analyzer to improve coverage."""

from unittest.mock import MagicMock

import allure
from git import GitCommandError
import pytest_check as check

from git_ai_reporter.analysis.git_analyzer import GitAnalyzer
from git_ai_reporter.analysis.git_analyzer import GitAnalyzerConfig


@allure.feature("Analysis - Git Analyzer Coverage")
class TestGitAnalyzerCoverage:
    """Tests to cover specific uncovered lines in git_analyzer."""

    @allure.story("Analysis Logic")
    @allure.title("Git analyzer handles repository with no commits")
    @allure.description(
        "Validates that get_first_commit_date returns None when repository has no commits"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("analysis", "git", "edge-case")
    def test_get_first_commit_date_no_commits(self) -> None:
        """Test get_first_commit_date when no commits exist - covers line 182."""
        with allure.step("Setup mock repository with no commits"):
            mock_repo = MagicMock()
            mock_repo.iter_commits.return_value = []  # No commits

        with allure.step("Create GitAnalyzer configuration"):
            config = GitAnalyzerConfig(
                trivial_commit_types=["chore", "docs", "style"],
                trivial_file_patterns=[r"\.md$", r"docs/", r"\.txt$"],
                git_command_timeout=300,
                debug=False,
            )

        with allure.step("Initialize analyzer and get first commit date"):
            analyzer = GitAnalyzer(repo=mock_repo, config=config)
            result = analyzer.get_first_commit_date()

        with allure.step("Verify None is returned for empty repository"):
            check.is_none(result)
            allure.attach(
                "No commits found, returned None as expected",
                "Empty Repo Test",
                allure.attachment_type.TEXT,
            )

    @allure.story("Analysis Logic")
    @allure.title("Git analyzer handles git command errors gracefully")
    @allure.description(
        "Validates that get_first_commit_date returns None when GitCommandError occurs"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("analysis", "git", "error-handling")
    def test_get_first_commit_date_git_command_error(self) -> None:
        """Test get_first_commit_date when GitCommandError occurs - covers lines 184-185."""
        with allure.step("Setup mock repository to raise GitCommandError"):
            mock_repo = MagicMock()
            mock_repo.iter_commits.side_effect = GitCommandError("command failed")

        with allure.step("Create GitAnalyzer configuration"):
            config = GitAnalyzerConfig(
                trivial_commit_types=["chore", "docs", "style"],
                trivial_file_patterns=[r"\.md$", r"docs/", r"\.txt$"],
                git_command_timeout=300,
                debug=False,
            )

        with allure.step("Initialize analyzer and handle git command error"):
            analyzer = GitAnalyzer(repo=mock_repo, config=config)
            result = analyzer.get_first_commit_date()

        with allure.step("Verify None is returned on git command error"):
            check.is_none(result)
            allure.attach(
                "GitCommandError handled gracefully, returned None",
                "Error Handling Test",
                allure.attachment_type.TEXT,
            )
