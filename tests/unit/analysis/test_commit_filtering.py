# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for commit filtering logic."""

from unittest.mock import MagicMock

import allure
import git
import pytest

from git_ai_reporter.analysis.git_analyzer import GitAnalyzer
from git_ai_reporter.analysis.git_analyzer import GitAnalyzerConfig


@allure.feature("Git Analysis")
@allure.story("Commit Filtering")
class TestCommitFiltering:
    """Test commit filtering logic to ensure important commits aren't filtered."""

    @pytest.fixture
    def analyzer_config(self) -> GitAnalyzerConfig:
        """Create a GitAnalyzerConfig with updated filtering rules."""
        return GitAnalyzerConfig(
            trivial_commit_types=["style", "chore"],  # Reduced list
            trivial_file_patterns=[r"\.gitignore$", r"\.editorconfig$", r"\.prettierrc"],
            git_command_timeout=30,
            debug=False,
        )

    @pytest.fixture
    def git_analyzer(self, analyzer_config: GitAnalyzerConfig) -> GitAnalyzer:
        """Create a GitAnalyzer instance with mock repo."""
        mock_repo = MagicMock(spec=git.Repo)
        return GitAnalyzer(mock_repo, analyzer_config)

    @allure.title("Test commits are not filtered as trivial")
    @allure.description("Verify that test commits are processed as important work")
    def test_test_commits_not_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that commits with 'test:' prefix are not marked as trivial."""
        mock_commit = MagicMock(spec=git.Commit)
        mock_commit.message = "test: Add comprehensive unit tests for authentication"

        result = git_analyzer._is_trivial_by_message(mock_commit)
        assert not result, "Test commits should not be marked as trivial"

    @allure.title("Refactor commits are not filtered as trivial")
    @allure.description("Verify that refactoring commits are processed as important work")
    def test_refactor_commits_not_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that commits with 'refactor:' prefix are not marked as trivial."""
        mock_commit = MagicMock(spec=git.Commit)
        mock_commit.message = "refactor: Improve database query performance"

        result = git_analyzer._is_trivial_by_message(mock_commit)
        assert not result, "Refactor commits should not be marked as trivial"

    @allure.title("CI commits are not filtered as trivial")
    @allure.description("Verify that CI/CD commits are processed as important infrastructure work")
    def test_ci_commits_not_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that commits with 'ci:' prefix are not marked as trivial."""
        mock_commit = MagicMock(spec=git.Commit)
        mock_commit.message = "ci: Add GitHub Actions workflow for automated testing"

        result = git_analyzer._is_trivial_by_message(mock_commit)
        assert not result, "CI commits should not be marked as trivial"

    @allure.title("Documentation commits are not filtered as trivial")
    @allure.description("Verify that documentation commits are processed as important work")
    def test_docs_commits_not_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that commits with 'docs:' prefix are not marked as trivial."""
        mock_commit = MagicMock(spec=git.Commit)
        mock_commit.message = "docs: Update API documentation with new endpoints"

        result = git_analyzer._is_trivial_by_message(mock_commit)
        assert not result, "Documentation commits should not be marked as trivial"

    @allure.title("Style commits are still filtered as trivial")
    @allure.description("Verify that pure formatting commits are still filtered")
    def test_style_commits_are_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that commits with 'style:' prefix are still marked as trivial."""
        mock_commit = MagicMock(spec=git.Commit)
        mock_commit.message = "style: Format code with prettier"

        result = git_analyzer._is_trivial_by_message(mock_commit)
        assert result, "Style-only commits should be marked as trivial"

    @allure.title("Chore commits are still filtered as trivial")
    @allure.description("Verify that routine chore commits are still filtered")
    def test_chore_commits_are_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that commits with 'chore:' prefix are marked as trivial."""
        mock_commit = MagicMock(spec=git.Commit)
        mock_commit.message = "chore: Update .gitignore"

        result = git_analyzer._is_trivial_by_message(mock_commit)
        assert result, "Chore commits should be marked as trivial"

    @allure.title("Feature commits are not filtered")
    @allure.description("Verify that feature commits are always processed")
    def test_feat_commits_not_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that commits with 'feat:' prefix are not marked as trivial."""
        mock_commit = MagicMock(spec=git.Commit)
        mock_commit.message = "feat: Add user authentication system"

        result = git_analyzer._is_trivial_by_message(mock_commit)
        assert not result, "Feature commits should never be marked as trivial"

    @allure.title("Bug fix commits are not filtered")
    @allure.description("Verify that bug fix commits are always processed")
    def test_fix_commits_not_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that commits with 'fix:' prefix are not marked as trivial."""
        mock_commit = MagicMock(spec=git.Commit)
        mock_commit.message = "fix: Resolve memory leak in image processing"

        result = git_analyzer._is_trivial_by_message(mock_commit)
        assert not result, "Bug fix commits should never be marked as trivial"

    @allure.title("Markdown files are not filtered as trivial")
    @allure.description("Verify that markdown documentation is not filtered out")
    def test_markdown_files_not_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that .md files are not marked as trivial."""
        mock_diff = MagicMock()
        mock_diff.a_path = "README.md"
        mock_diff.b_path = "README.md"

        diffs = [mock_diff]
        result = git_analyzer._is_trivial_by_file_paths(diffs)
        assert not result, "Markdown files should not be marked as trivial"

    @allure.title("Configuration files are not filtered as trivial")
    @allure.description("Verify that config files are not filtered out")
    def test_config_files_not_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that .toml and .cfg files are not marked as trivial."""
        mock_diff1 = MagicMock()
        mock_diff1.a_path = "pyproject.toml"
        mock_diff1.b_path = "pyproject.toml"

        mock_diff2 = MagicMock()
        mock_diff2.a_path = "setup.cfg"
        mock_diff2.b_path = "setup.cfg"

        result1 = git_analyzer._is_trivial_by_file_paths([mock_diff1])
        result2 = git_analyzer._is_trivial_by_file_paths([mock_diff2])

        assert not result1, "TOML config files should not be marked as trivial"
        assert not result2, "CFG config files should not be marked as trivial"

    @allure.title("Gitignore files are still filtered as trivial")
    @allure.description("Verify that .gitignore changes are still filtered")
    def test_gitignore_files_are_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that .gitignore files are marked as trivial."""
        mock_diff = MagicMock()
        mock_diff.a_path = ".gitignore"
        mock_diff.b_path = ".gitignore"

        diffs = [mock_diff]
        result = git_analyzer._is_trivial_by_file_paths(diffs)
        assert result, ".gitignore files should be marked as trivial"

    @allure.title("Mixed file changes with non-trivial files are not filtered")
    @allure.description("Verify that commits with at least one important file are processed")
    def test_mixed_files_not_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that commits with mixed files are not trivial if any file is important."""
        mock_diff1 = MagicMock()
        mock_diff1.a_path = ".gitignore"
        mock_diff1.b_path = ".gitignore"

        mock_diff2 = MagicMock()
        mock_diff2.a_path = "src/main.py"
        mock_diff2.b_path = "src/main.py"

        diffs = [mock_diff1, mock_diff2]
        result = git_analyzer._is_trivial_by_file_paths(diffs)
        assert (
            not result
        ), "Commits with at least one non-trivial file should not be marked as trivial"

    @allure.title("Performance commits are not filtered")
    @allure.description("Verify that performance optimization commits are processed")
    def test_perf_commits_not_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that commits with 'perf:' prefix are not marked as trivial."""
        mock_commit = MagicMock(spec=git.Commit)
        mock_commit.message = "perf: Optimize database query performance"

        result = git_analyzer._is_trivial_by_message(mock_commit)
        assert not result, "Performance commits should not be marked as trivial"

    @allure.title("Build commits are not filtered")
    @allure.description("Verify that build system commits are processed")
    def test_build_commits_not_trivial(self, git_analyzer: GitAnalyzer) -> None:
        """Test that commits with 'build:' prefix are not marked as trivial."""
        mock_commit = MagicMock(spec=git.Commit)
        mock_commit.message = "build: Update dependencies to latest versions"

        result = git_analyzer._is_trivial_by_message(mock_commit)
        assert not result, "Build commits should not be marked as trivial"
