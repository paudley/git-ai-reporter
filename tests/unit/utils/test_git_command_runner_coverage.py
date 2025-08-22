# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Additional unit tests for git_command_runner module to improve coverage."""

from pathlib import Path
import subprocess
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import pytest_check as check

from git_ai_reporter.utils.git_command_runner import GitCommandError
from git_ai_reporter.utils.git_command_runner import run_git_command


class TestRunGitCommand:
    """Test suite for run_git_command function."""

    @patch("subprocess.run")
    def test_run_git_command_success(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test successful run_git_command."""
        mock_run.return_value = Mock(returncode=0, stdout="branch main", stderr="")

        result = run_git_command(str(tmp_path), "branch", timeout=30)
        check.equal(result, "branch main")

    @patch("subprocess.run")
    def test_run_git_command_failure(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command failure."""
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr="error: pathspec 'nonexistent' did not match any files"
        )

        with pytest.raises(GitCommandError):
            run_git_command(str(tmp_path), "add", "nonexistent", timeout=30)

    @patch("subprocess.run")
    def test_run_git_command_with_debug(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command with debug mode."""
        mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")

        result = run_git_command(str(tmp_path), "status", timeout=30, debug=True)
        check.equal(result, "output")

    @patch("subprocess.run")
    def test_run_git_command_timeout_handling(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired(["git"], 30)

        with pytest.raises(GitCommandError) as exc_info:
            run_git_command(str(tmp_path), "log", "--all", timeout=30)

        check.is_in("timed out", str(exc_info.value))

    @patch("subprocess.run")
    def test_run_git_command_os_error(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command OS error handling."""
        mock_run.side_effect = OSError("Command not found")

        with pytest.raises(GitCommandError) as exc_info:
            run_git_command(str(tmp_path), "status", timeout=30)

        check.is_in("Failed to execute", str(exc_info.value))

    @patch("subprocess.run")
    def test_run_git_command_debug_empty_output(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command debug mode with empty output."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = run_git_command(str(tmp_path), "status", timeout=30, debug=True)
        check.equal(result, "")

    @patch("subprocess.run")
    def test_run_git_command_debug_long_output(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command debug mode with long output."""
        long_output = "\n".join([f"line {i}" for i in range(150)])
        mock_run.return_value = Mock(returncode=0, stdout=long_output, stderr="")

        result = run_git_command(str(tmp_path), "log", timeout=30, debug=True)
        check.equal(result, long_output)


class TestGitCommandError:
    """Test suite for GitCommandError exception."""

    def test_git_command_error_creation(self) -> None:
        """Test GitCommandError creation."""
        error = GitCommandError("Test error message")
        check.equal(str(error), "Test error message")

    def test_git_command_error_with_details(self) -> None:
        """Test GitCommandError with detailed message."""
        cmd = ["git", "log", "--oneline"]
        stderr = "fatal: not a git repository"

        error = GitCommandError(f"Command {cmd} failed: {stderr}")

        check.is_in("git", str(error))
        check.is_in("failed", str(error))
        check.is_in("fatal", str(error))

    def test_git_command_error_inheritance(self) -> None:
        """Test GitCommandError inheritance."""
        error = GitCommandError("Test")
        check.is_instance(error, Exception)
