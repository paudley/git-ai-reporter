# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for git_ai_reporter.utils.git_command_runner module.

This module tests the git command execution utility.
"""

import subprocess
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import pytest_check as check

from git_ai_reporter.utils.git_command_runner import GitCommandError
from git_ai_reporter.utils.git_command_runner import run_git_command


class TestRunGitCommand:
    """Test suite for run_git_command function."""

    def test_successful_command_execution(self) -> None:
        """Test successful git command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "commit abc123\nAuthor: Test User"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = run_git_command("/repo", "log", "--oneline", timeout=30)

            check.equal(result, "commit abc123\nAuthor: Test User")
            mock_run.assert_called_once_with(
                ["git", "-C", "/repo", "log", "--oneline"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
                encoding="utf-8",
                errors="ignore",
            )

    def test_command_with_debug_output(self) -> None:
        """Test git command execution with debug output."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "debug output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            with patch("git_ai_reporter.utils.git_command_runner.rprint") as mock_print:
                result = run_git_command("/repo", "status", timeout=10, debug=True)

                check.equal(result, "debug output")
                # Should print the command and output
                check.equal(mock_print.call_count, 3)
                mock_print.assert_any_call("[bold cyan]Running Git Command:[/] git -C /repo status")
                mock_print.assert_any_call("[bold green]Git Command Output:[/]")
                mock_print.assert_any_call("debug output")

    def test_command_with_empty_output_debug(self) -> None:
        """Test git command with empty output in debug mode."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "   "  # Whitespace only
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            with patch("git_ai_reporter.utils.git_command_runner.rprint") as mock_print:
                result = run_git_command("/repo", "status", timeout=10, debug=True)

                check.equal(result, "   ")
                # Should show [EMPTY STDOUT] when output is whitespace only
                mock_print.assert_any_call("[EMPTY STDOUT]")

    def test_command_failure_with_non_zero_exit(self) -> None:
        """Test git command failure with non-zero exit code."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "fatal: not a git repository"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(GitCommandError) as exc_info:
                run_git_command("/not-a-repo", "status", timeout=30)

            check.is_in("Git command failed with exit code 1", str(exc_info.value))
            check.is_in("fatal: not a git repository", str(exc_info.value))

    def test_command_timeout(self) -> None:
        """Test git command timeout handling."""
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(
                cmd=["git", "-C", "/repo", "log"],
                timeout=5,
            ),
        ):
            with pytest.raises(GitCommandError) as exc_info:
                run_git_command("/repo", "log", timeout=5)

            check.is_in("Git command timed out after 5 seconds", str(exc_info.value))
            check.is_in("git -C /repo log", str(exc_info.value))

    def test_command_os_error(self) -> None:
        """Test handling of OS errors during command execution."""
        with patch("subprocess.run", side_effect=OSError("Command not found")):
            with pytest.raises(GitCommandError) as exc_info:
                run_git_command("/repo", "status", timeout=30)

            check.is_in("Failed to execute git command", str(exc_info.value))
            check.is_in("Command not found", str(exc_info.value))

    def test_command_with_multiple_arguments(self) -> None:
        """Test git command with multiple arguments."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = run_git_command(
                "/repo",
                "log",
                "--since=2025-01-01",
                "--until=2025-01-07",
                "--format=%H",
                timeout=60,
            )

            check.equal(result, "output")
            mock_run.assert_called_once_with(
                [
                    "git",
                    "-C",
                    "/repo",
                    "log",
                    "--since=2025-01-01",
                    "--until=2025-01-07",
                    "--format=%H",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
                encoding="utf-8",
                errors="ignore",
            )

    def test_command_with_unicode_output(self) -> None:
        """Test handling of unicode output from git command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "commit by 用户 with émoji 🚀"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = run_git_command("/repo", "log", timeout=30)

            check.equal(result, "commit by 用户 with émoji 🚀")

    def test_command_with_stderr_on_success(self) -> None:
        """Test that stderr is ignored on successful commands."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = "warning: something"

        with patch("subprocess.run", return_value=mock_result):
            result = run_git_command("/repo", "status", timeout=30)

            # Should return stdout and ignore stderr when successful
            check.equal(result, "success output")

    def test_command_with_empty_repo_path(self) -> None:
        """Test git command with empty repository path."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = run_git_command("", "status", timeout=30)

            check.equal(result, "output")
            # Should still include -C flag even with empty path
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            check.equal(args[0], "git")
            check.equal(args[1], "-C")
            check.equal(args[2], "")

    def test_command_with_special_characters_in_path(self) -> None:
        """Test git command with special characters in repository path."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = run_git_command("/path with spaces/repo", "status", timeout=30)

            check.equal(result, "output")
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            check.equal(args[2], "/path with spaces/repo")

    def test_command_error_types(self) -> None:
        """Test that GitCommandError is properly raised."""
        # Test that GitCommandError is an Exception subclass
        check.is_true(issubclass(GitCommandError, Exception))

        # Test creating GitCommandError with message
        error = GitCommandError("Test error message")
        check.equal(str(error), "Test error message")

    def test_command_with_zero_timeout(self) -> None:
        """Test git command with zero timeout (should work but risky)."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = run_git_command("/repo", "status", timeout=0)

            check.equal(result, "output")
            # Verify timeout=0 is passed through
            check.equal(mock_run.call_args[1]["timeout"], 0)

    def test_command_with_negative_exit_code(self) -> None:
        """Test git command with negative exit code."""
        mock_result = MagicMock()
        mock_result.returncode = -1
        mock_result.stdout = ""
        mock_result.stderr = "terminated"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(GitCommandError) as exc_info:
                run_git_command("/repo", "status", timeout=30)

            check.is_in("Git command failed with exit code -1", str(exc_info.value))

    def test_command_preserves_newlines(self) -> None:
        """Test that output newlines are preserved."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "line1\nline2\n\nline4\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = run_git_command("/repo", "log", timeout=30)

            check.equal(result, "line1\nline2\n\nline4\n")
            check.equal(result.count("\n"), 4)

    def test_command_with_debug_output_truncation(self) -> None:
        """Test git command execution with debug output truncation (lines 52-53)."""
        # Create output that exceeds default max_debug_lines (100 in the code)
        output_lines = [f"line {i}" for i in range(150)]  # More than max_debug_lines
        long_output = "\n".join(output_lines)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = long_output
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            with patch("git_ai_reporter.utils.git_command_runner.rprint") as mock_print:
                result = run_git_command("/repo", "status", timeout=10, debug=True)

                check.equal(result, long_output)
                # Should print truncated output with truncation message
                truncation_indicator = "truncated"
                truncation_call_found = False
                for call in mock_print.call_args_list:
                    if truncation_indicator in str(call).lower():
                        truncation_call_found = True
                        break

                check.is_true(truncation_call_found, "Expected truncation message in debug output")

    def test_command_with_debug_output_no_truncation_needed(self) -> None:
        """Test git command execution with debug output that doesn't need truncation."""
        # Create output that's less than max_debug_lines
        output_lines = [f"line {i}" for i in range(5)]  # Less than max_debug_lines
        short_output = "\n".join(output_lines)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = short_output
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            with patch("git_ai_reporter.utils.git_command_runner.rprint") as mock_print:
                result = run_git_command("/repo", "status", timeout=10, debug=True)

                check.equal(result, short_output)
                # Should print full output without truncation
                mock_print.assert_any_call(short_output)
