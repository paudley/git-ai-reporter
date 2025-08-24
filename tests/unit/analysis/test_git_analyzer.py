# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=protected-access

"""Unit tests for git_ai_reporter.analysis.git_analyzer module.

This module tests the GitAnalyzer class which handles all interactions
with Git repositories including commit filtering, diff generation, and
analysis of changes.
"""

from datetime import datetime
from datetime import timedelta
import json
import time
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import allure
import git
from git.exc import GitCommandError
import pytest
import pytest_check as check

from git_ai_reporter.analysis.git_analyzer import GitAnalyzer
from git_ai_reporter.analysis.git_analyzer import GitAnalyzerConfig
from git_ai_reporter.utils.git_command_runner import GitCommandError as CommandRunnerError


@pytest.fixture
@allure.title("Mock Git repository fixture")
def mock_repo() -> MagicMock:
    """Create a mock Git repository."""
    with allure.step("Create mock Git repository for testing"):
        repo = MagicMock(spec=git.Repo)
        repo.working_dir = "/mock/repo"
        repo.iter_commits = MagicMock()

        allure.attach(
            json.dumps(
                {
                    "working_directory": "/mock/repo",
                    "mock_type": "git.Repo",
                    "iter_commits_available": True,
                },
                indent=2,
            ),
            name="Mock Repository Configuration",
            attachment_type=allure.attachment_type.JSON,
        )
        return repo


@pytest.fixture
@allure.title("Git analyzer configuration fixture")
def analyzer_config() -> GitAnalyzerConfig:
    """Create a GitAnalyzerConfig for testing."""
    with allure.step("Create git analyzer configuration"):
        config = GitAnalyzerConfig(
            trivial_commit_types=["chore", "docs", "style"],
            trivial_file_patterns=[r"\.md$", r"docs/", r"\.txt$"],
            git_command_timeout=300,
            debug=False,
        )

        allure.attach(
            json.dumps(
                {
                    "trivial_commit_types": config.trivial_commit_types,
                    "trivial_file_patterns": config.trivial_file_patterns,
                    "git_command_timeout": config.git_command_timeout,
                    "debug_enabled": config.debug,
                },
                indent=2,
            ),
            name="Analyzer Configuration",
            attachment_type=allure.attachment_type.JSON,
        )
        return config


@pytest.fixture
def git_analyzer(
    mock_repo: MagicMock,  # pylint: disable=redefined-outer-name
    analyzer_config: GitAnalyzerConfig,  # pylint: disable=redefined-outer-name
) -> GitAnalyzer:
    """Create a GitAnalyzer instance for testing."""
    return GitAnalyzer(repo=mock_repo, config=analyzer_config)


@pytest.fixture
def mock_commit() -> MagicMock:
    """Create a mock commit object."""
    commit = MagicMock(spec=git.Commit)
    commit.hexsha = "abc123def456"
    commit.message = "feat: Add new feature"
    commit.committed_datetime = datetime(2025, 1, 7, 10, 0, 0)
    commit.parents = []
    return commit


@allure.feature("Analysis - Git Analyzer")
@allure.story("Core Git Analysis Operations")
class TestGitAnalyzer:
    """Test suite for GitAnalyzer class."""

    @pytest.mark.smoke
    @allure.title("Initialize GitAnalyzer with configuration")
    @allure.description(
        "Verifies that GitAnalyzer can be properly initialized with a Git repository and configuration"
    )
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.tag("git", "initialization", "smoke", "critical-path")
    @allure.link(
        "https://github.com/example/git-reporter/docs/git-analyzer",
        name="GitAnalyzer Documentation",
    )
    @allure.testcase("TC-GIT-001", "Test GitAnalyzer initialization")
    def test_init(
        self,
        mock_repo: MagicMock,  # pylint: disable=redefined-outer-name
        analyzer_config: GitAnalyzerConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test GitAnalyzer initialization."""
        allure.dynamic.description(
            "Testing GitAnalyzer instantiation with dependency injection and configuration validation"
        )
        allure.dynamic.tag("dependency-injection")

        start_time = time.time()

        with allure.step("Create GitAnalyzer instance"):
            try:
                analyzer = GitAnalyzer(repo=mock_repo, config=analyzer_config)
                init_time = time.time() - start_time

                allure.attach(
                    json.dumps(
                        {
                            "initialization_time_ms": init_time * 1000,
                            "repo_working_dir": analyzer.repo.working_dir,
                            "config_applied": True,
                        },
                        indent=2,
                    ),
                    name="Initialization Performance",
                    attachment_type=allure.attachment_type.JSON,
                )
            except Exception as e:
                allure.attach(
                    f"Initialization failed: {str(e)}",
                    name="Initialization Error",
                    attachment_type=allure.attachment_type.TEXT,
                )
                raise

        with allure.step("Verify analyzer initialization and configuration"):
            check.equal(analyzer.repo, mock_repo)
            check.equal(
                analyzer._trivial_commit_types, ["chore", "docs", "style"]
            )  # pylint: disable=protected-access
            check.equal(len(analyzer._trivial_file_patterns), 3)  # pylint: disable=protected-access
            check.equal(analyzer._git_command_timeout, 300)  # pylint: disable=protected-access
            check.is_false(analyzer._debug)  # pylint: disable=protected-access

            allure.attach(
                json.dumps(
                    {
                        "repo_match": analyzer.repo == mock_repo,
                        "trivial_types_count": len(analyzer._trivial_commit_types),
                        "pattern_count": len(analyzer._trivial_file_patterns),
                        "timeout_seconds": analyzer._git_command_timeout,
                        "debug_disabled": not analyzer._debug,
                    },
                    indent=2,
                ),
                name="Configuration Verification",
                attachment_type=allure.attachment_type.JSON,
            )

    @pytest.mark.smoke
    @allure.title("Fetch commits within date range")
    @allure.description(
        "Verifies that commits can be retrieved and properly sorted within a specified date range"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("git", "commits", "date-range", "smoke")
    def test_get_commits_in_range(
        self,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
        mock_repo: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test fetching commits within a date range."""
        with allure.step("Setup mock commits with different dates"):
            # Setup mock commits
            commit1 = MagicMock()
        commit1.committed_datetime = datetime(2025, 1, 5, 10, 0, 0)
        commit2 = MagicMock()
        commit2.committed_datetime = datetime(2025, 1, 7, 10, 0, 0)
        commit3 = MagicMock()
        commit3.committed_datetime = datetime(2025, 1, 6, 10, 0, 0)

        mock_repo.iter_commits.return_value = [commit1, commit2, commit3]

        with allure.step("Execute commit range query"):
            # Call method
            start_date = datetime(2025, 1, 1)
            end_date = datetime(2025, 1, 8)
            commits = git_analyzer.get_commits_in_range(start_date, end_date)

        with allure.step("Verify commit retrieval and sorting"):
            # Verify
            check.equal(len(commits), 3)
        # Should be sorted by date
        check.equal(commits[0].committed_datetime, datetime(2025, 1, 5, 10, 0, 0))
        check.equal(commits[1].committed_datetime, datetime(2025, 1, 6, 10, 0, 0))
        check.equal(commits[2].committed_datetime, datetime(2025, 1, 7, 10, 0, 0))
        # Verify that end_date is made inclusive by adding 1 day
        mock_repo.iter_commits.assert_called_once_with(
            "--all",
            after=start_date.isoformat(),
            before=(end_date + timedelta(days=1)).isoformat(),
        )

    @allure.title("Handle Git command errors when fetching commits")
    @allure.description("Verifies graceful handling of Git command errors and returns empty list")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git", "error-handling", "commits")
    def test_get_commits_in_range_git_error(
        self,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
        mock_repo: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of GitCommandError when fetching commits."""
        with allure.step("Setup Git command error"):
            mock_repo.iter_commits.side_effect = GitCommandError("git", "error")

        with allure.step("Execute commit range query with error"):
            commits = git_analyzer.get_commits_in_range(
                datetime(2025, 1, 1),
                datetime(2025, 1, 8),
            )

        with allure.step("Verify error handled gracefully"):
            check.equal(commits, [])

    @allure.title("Detect commit triviality by message prefix")
    @allure.description(
        "Verifies that commits are correctly classified as trivial based on message prefixes"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git", "triviality", "commit-messages")
    def test_is_trivial_by_message(
        self,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit triviality detection by message."""
        with allure.step("Test trivial commit detection"):
            # Trivial commits
            trivial_commit = MagicMock()
        trivial_commit.message = "chore: Update dependencies"
        check.is_true(
            git_analyzer._is_trivial_by_message(trivial_commit)
        )  # pylint: disable=protected-access

        trivial_commit.message = "docs: Fix typo"
        check.is_true(
            git_analyzer._is_trivial_by_message(trivial_commit)
        )  # pylint: disable=protected-access

        trivial_commit.message = "style(frontend): Format code"
        check.is_true(
            git_analyzer._is_trivial_by_message(trivial_commit)
        )  # pylint: disable=protected-access

        with allure.step("Test non-trivial commit detection"):
            # Non-trivial commits
            non_trivial = MagicMock()
        non_trivial.message = "feat: Add new feature"
        check.is_false(
            git_analyzer._is_trivial_by_message(non_trivial)
        )  # pylint: disable=protected-access

        non_trivial.message = "fix: Resolve bug"
        check.is_false(
            git_analyzer._is_trivial_by_message(non_trivial)
        )  # pylint: disable=protected-access

    @allure.title("Handle byte string commit messages")
    @allure.description(
        "Verifies that byte string commit messages are properly decoded and classified"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("git", "encoding", "bytes")
    def test_is_trivial_by_message_bytes(
        self,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of byte string commit messages."""
        with allure.step("Test byte string commit message decoding"):
            commit = MagicMock()
            commit.message = b"chore: Update dependencies"

        with allure.step("Verify byte string message classified correctly"):
            check.is_true(
                git_analyzer._is_trivial_by_message(commit)
            )  # pylint: disable=protected-access

    @allure.title("Detect commit triviality by file paths")
    @allure.description(
        "Verifies that commits are classified as trivial based on modified file patterns"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git", "triviality", "file-patterns")
    def test_is_trivial_by_file_paths(
        self,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test file path triviality detection."""
        with allure.step("Test all trivial files detection"):
            # All trivial files
            diff1 = MagicMock()
        diff1.a_path = "README.md"
        diff1.b_path = None

        diff2 = MagicMock()
        diff2.a_path = None
        diff2.b_path = "docs/guide.md"

        diffs = MagicMock()
        diffs.__iter__ = Mock(return_value=iter([diff1, diff2]))

        check.is_true(
            git_analyzer._is_trivial_by_file_paths(diffs)
        )  # pylint: disable=protected-access

        with allure.step("Test mixed trivial and non-trivial files"):
            # Mix of trivial and non-trivial
            diff3 = MagicMock()
        diff3.a_path = "src/main.py"
        diff3.b_path = None

        diffs.__iter__ = Mock(return_value=iter([diff1, diff3]))
        check.is_false(
            git_analyzer._is_trivial_by_file_paths(diffs)
        )  # pylint: disable=protected-access

        with allure.step("Test edge case with no paths"):
            # No path (edge case)
            diff4 = MagicMock()
        diff4.a_path = None
        diff4.b_path = None

        diffs.__iter__ = Mock(return_value=iter([diff4]))
        check.is_false(
            git_analyzer._is_trivial_by_file_paths(diffs)
        )  # pylint: disable=protected-access

    @allure.title("Generate commit diff output")
    @allure.description(
        "Verifies that commit diffs are properly generated for commits with and without parents"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("git", "diff", "commits")
    @patch("git_ai_reporter.analysis.git_analyzer.git_command_runner")
    def test_get_commit_diff(
        self,
        mock_runner: MagicMock,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
        mock_commit: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test getting diff for a single commit."""
        with allure.step("Test initial commit diff (no parents)"):
            # Test with no parents (initial commit)
            mock_runner.run_git_command.return_value = "diff content"

            diff = git_analyzer.get_commit_diff(mock_commit)

        check.equal(diff, "diff content")
        mock_runner.run_git_command.assert_called_once_with(
            "/mock/repo",
            "show",
            "abc123def456",
            timeout=300,
            debug=False,
        )

        with allure.step("Test commit diff with parent"):
            # Test with parent
            mock_runner.reset_mock()
            parent = MagicMock()
            parent.hexsha = "parent123"
            mock_commit.parents = [parent]

            diff = git_analyzer.get_commit_diff(mock_commit)

        check.equal(diff, "diff content")
        mock_runner.run_git_command.assert_called_once_with(
            "/mock/repo",
            "diff",
            "parent123",
            "abc123def456",
            timeout=300,
            debug=False,
        )

    @allure.title("Handle errors in commit diff generation")
    @allure.description(
        "Verifies graceful error handling when Git command fails during diff generation"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git", "error-handling", "diff")
    @patch("git_ai_reporter.analysis.git_analyzer.git_command_runner")
    def test_get_commit_diff_error(
        self,
        mock_runner: MagicMock,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
        mock_commit: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test error handling in get_commit_diff."""
        with allure.step("Setup Git command error"):
            mock_runner.run_git_command.side_effect = CommandRunnerError("Error")
            mock_runner.GitCommandError = CommandRunnerError

        with allure.step("Execute diff generation with error"):
            diff = git_analyzer.get_commit_diff(mock_commit)

        with allure.step("Verify error handled gracefully"):
            check.equal(diff, "")

    @patch("git_ai_reporter.analysis.git_analyzer.git_command_runner")
    def test_get_weekly_diff_error_debug_mode(
        self,
        mock_runner: MagicMock,
        mock_repo: MagicMock,  # pylint: disable=redefined-outer-name
        mock_commit: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test error handling in get_weekly_diff with debug mode."""
        config = GitAnalyzerConfig(
            trivial_commit_types=["chore", "docs"],
            trivial_file_patterns=[r".*\.md$"],
            git_command_timeout=300,
            debug=True,  # Enable debug mode
        )
        analyzer = GitAnalyzer(mock_repo, config)

        # Setup commits with parent
        parent = MagicMock()
        parent.hexsha = "parent123"
        mock_commit.parents = [parent]
        second_commit = MagicMock()
        second_commit.hexsha = "def456ghi789"

        mock_runner.run_git_command.side_effect = CommandRunnerError("Git error")
        mock_runner.GitCommandError = CommandRunnerError

        # Should raise the error in debug mode
        with pytest.raises(CommandRunnerError):
            analyzer.get_weekly_diff([mock_commit, second_commit])

        # Test with debug mode
        analyzer._debug = True  # pylint: disable=protected-access
        with pytest.raises(CommandRunnerError):
            analyzer.get_commit_diff(mock_commit)

    @patch("git_ai_reporter.analysis.git_analyzer.git_command_runner")
    def test_get_weekly_diff(
        self,
        mock_runner: MagicMock,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test getting consolidated weekly diff."""
        # Create mock commits
        commit1 = MagicMock()
        commit1.hexsha = "commit1"
        parent1 = MagicMock()
        parent1.hexsha = "parent1"
        commit1.parents = [parent1]

        commit2 = MagicMock()
        commit2.hexsha = "commit2"
        commit2.parents = [commit1]

        commit3 = MagicMock()
        commit3.hexsha = "commit3"
        commit3.parents = [commit2]

        mock_runner.run_git_command.return_value = "weekly diff"

        # Test with multiple commits
        diff = git_analyzer.get_weekly_diff([commit1, commit2, commit3])

        check.equal(diff, "weekly diff")
        mock_runner.run_git_command.assert_called_once_with(
            "/mock/repo",
            "diff",
            "parent1",
            "commit3",
            timeout=300,
            debug=False,
        )

    @patch("git_ai_reporter.analysis.git_analyzer.git_command_runner")
    def test_get_weekly_diff_single_commit(
        self,
        mock_runner: MagicMock,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
        mock_commit: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly diff with single commit."""
        mock_runner.run_git_command.return_value = "single diff"

        # Test with single commit
        diff = git_analyzer.get_weekly_diff([mock_commit])

        check.equal(diff, "single diff")
        mock_runner.run_git_command.assert_called_once_with(
            "/mock/repo",
            "show",
            "abc123def456",
            timeout=300,
            debug=False,
        )

    @patch("git_ai_reporter.analysis.git_analyzer.git_command_runner")
    def test_get_weekly_diff_empty(
        self,
        mock_runner: MagicMock,  # pylint: disable=unused-argument
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly diff with no commits."""
        diff = git_analyzer.get_weekly_diff([])
        check.equal(diff, "")

    @patch("git_ai_reporter.analysis.git_analyzer.git_command_runner")
    def test_get_weekly_diff_root_commit(
        self,
        mock_runner: MagicMock,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly diff when first commit is root."""
        # Root commit (no parents)
        root_commit = MagicMock()
        root_commit.hexsha = "root"
        root_commit.parents = []

        last_commit = MagicMock()
        last_commit.hexsha = "last"
        last_commit.parents = [root_commit]

        mock_runner.run_git_command.return_value = "root diff"

        diff = git_analyzer.get_weekly_diff([root_commit, last_commit])

        check.equal(diff, "root diff")
        # Should use diff between root and last
        mock_runner.run_git_command.assert_called_with(
            "/mock/repo",
            "diff",
            "root",
            "last",
            timeout=300,
            debug=False,
        )

    @patch("git_ai_reporter.analysis.git_analyzer.git_command_runner")
    def test_get_weekly_diff_error_handling_debug_mode(
        self,
        mock_runner: MagicMock,
        mock_repo: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test error handling in get_weekly_diff with debug mode."""
        # Create analyzer with debug=True
        config = GitAnalyzerConfig(
            trivial_commit_types=["chore", "docs"],
            trivial_file_patterns=[r"\.md$"],
            git_command_timeout=300,
            debug=True,
        )
        analyzer = GitAnalyzer(mock_repo, config)

        commit1 = MagicMock()
        commit1.hexsha = "commit1"
        parent1 = MagicMock()
        parent1.hexsha = "parent1"
        commit1.parents = [parent1]

        # Set up the error
        mock_runner.run_git_command.side_effect = CommandRunnerError("Error")
        mock_runner.GitCommandError = CommandRunnerError

        # Should re-raise in debug mode
        with pytest.raises(CommandRunnerError):
            analyzer.get_weekly_diff([commit1])

    @patch("git_ai_reporter.analysis.git_analyzer.git_command_runner")
    def test_get_weekly_diff_error_handling(
        self,
        mock_runner: MagicMock,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test error handling in get_weekly_diff."""
        commit1 = MagicMock()
        commit1.hexsha = "commit1"
        parent1 = MagicMock()
        parent1.hexsha = "parent1"
        commit1.parents = [parent1]

        commit2 = MagicMock()
        commit2.hexsha = "commit2"

        mock_runner.run_git_command.side_effect = CommandRunnerError("Error")
        mock_runner.GitCommandError = CommandRunnerError

        diff = git_analyzer.get_weekly_diff([commit1, commit2])
        check.equal(diff, "")

    def test_config_validation(self) -> None:
        """Test GitAnalyzerConfig validation."""
        # Valid config
        config = GitAnalyzerConfig(
            trivial_commit_types=["chore", "docs"],
            trivial_file_patterns=[r"\.md$"],
            git_command_timeout=300,
            debug=True,
        )
        check.equal(config.trivial_commit_types, ["chore", "docs"])
        check.equal(config.trivial_file_patterns, [r"\.md$"])
        check.equal(config.git_command_timeout, 300)
        check.is_true(config.debug)

        # Default debug value
        config = GitAnalyzerConfig(
            trivial_commit_types=[],
            trivial_file_patterns=[],
            git_command_timeout=60,
        )
        check.is_false(config.debug)

    def test_empty_trivial_patterns(
        self,
        mock_repo: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test analyzer with empty triviality patterns."""
        config = GitAnalyzerConfig(
            trivial_commit_types=[],
            trivial_file_patterns=[],
            git_command_timeout=300,
        )
        analyzer = GitAnalyzer(repo=mock_repo, config=config)

        # Nothing should be trivial
        commit = MagicMock()
        commit.message = "chore: Update"
        check.is_false(analyzer._is_trivial_by_message(commit))  # pylint: disable=protected-access

        diff = MagicMock()
        diff.a_path = "README.md"
        diffs = MagicMock()
        diffs.__iter__ = Mock(return_value=iter([diff]))
        check.is_false(
            analyzer._is_trivial_by_file_paths(diffs)
        )  # pylint: disable=protected-access

    def test_complex_file_patterns(
        self,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test complex regex patterns for file triviality."""
        # Test various file paths against patterns
        test_cases = [
            ("README.md", True),
            ("docs/guide.md", True),
            ("src/README.md", True),
            ("test.txt", True),
            ("src/main.py", False),
            ("tests/test_foo.py", False),
            ("docs/api.py", True),  # Matches docs/ pattern
        ]

        for filepath, expected_trivial in test_cases:
            diff = MagicMock()
            diff.a_path = filepath
            diff.b_path = None
            diffs = MagicMock()
            diffs.__iter__ = Mock(return_value=iter([diff]))

            result = git_analyzer._is_trivial_by_file_paths(
                diffs
            )  # pylint: disable=protected-access
            check.equal(
                result,
                expected_trivial,
                f"Path {filepath} should be {'trivial' if expected_trivial else 'non-trivial'}",
            )

    def test_date_range_boundary(
        self,
        git_analyzer: GitAnalyzer,  # pylint: disable=redefined-outer-name
        mock_repo: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test date range boundary conditions."""
        # Create commits at exact boundaries
        commit_before = MagicMock()
        commit_before.committed_datetime = datetime(2025, 1, 1, 0, 0, 0) - timedelta(seconds=1)

        commit_start = MagicMock()
        commit_start.committed_datetime = datetime(2025, 1, 1, 0, 0, 0)

        commit_middle = MagicMock()
        commit_middle.committed_datetime = datetime(2025, 1, 4, 12, 0, 0)

        commit_end = MagicMock()
        commit_end.committed_datetime = datetime(2025, 1, 8, 0, 0, 0)

        commit_after = MagicMock()
        commit_after.committed_datetime = datetime(2025, 1, 8, 0, 0, 1)

        # GitPython's iter_commits uses after/before which are inclusive/exclusive
        mock_repo.iter_commits.return_value = [
            commit_start,
            commit_middle,
        ]

        commits = git_analyzer.get_commits_in_range(
            datetime(2025, 1, 1, 0, 0, 0),
            datetime(2025, 1, 8, 0, 0, 0),
        )

        check.equal(len(commits), 2)
