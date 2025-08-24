# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Additional unit tests for git_command_runner module to improve coverage."""

from pathlib import Path
import subprocess
from unittest.mock import Mock
from unittest.mock import patch

import allure
import pytest
import pytest_check as check

from git_ai_reporter.utils.git_command_runner import GitCommandError
from git_ai_reporter.utils.git_command_runner import run_git_command


@allure.feature("Utils - Git Command Runner")
class TestRunGitCommand:
    """Test suite for run_git_command function."""

    @allure.story("Git Operations")
    @allure.title("Git command execution succeeds with valid output")
    @allure.description(
        "Validates that run_git_command executes successfully and returns expected output"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("git", "command", "success")
    @patch("subprocess.run")
    def test_run_git_command_success(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test successful run_git_command."""
        with allure.step("Setup mock subprocess to return success"):
            mock_run.return_value = Mock(returncode=0, stdout="branch main", stderr="")

        with allure.step("Execute git command"):
            result = run_git_command(str(tmp_path), "branch", timeout=30)

        with allure.step("Verify command output"):
            check.equal(result, "branch main")
            allure.attach(f"Command output: {result}", "Git Output", allure.attachment_type.TEXT)

    @allure.story("Git Operations")
    @allure.title("Git command execution fails with appropriate error")
    @allure.description("Validates that run_git_command raises GitCommandError on command failure")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("git", "command", "error")
    @patch("subprocess.run")
    def test_run_git_command_failure(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command failure."""
        with allure.step("Setup mock subprocess to return failure"):
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="error: pathspec 'nonexistent' did not match any files",
            )

        with allure.step("Execute git command expecting failure"):
            with pytest.raises(GitCommandError):
                run_git_command(str(tmp_path), "add", "nonexistent", timeout=30)
            allure.attach(
                "GitCommandError raised as expected", "Error Handling", allure.attachment_type.TEXT
            )

    @allure.story("Git Operations")
    @allure.title("Git command execution with debug mode enabled")
    @allure.description("Validates that run_git_command works correctly with debug mode")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git", "debug", "logging")
    @patch("subprocess.run")
    def test_run_git_command_with_debug(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command with debug mode."""
        with allure.step("Setup mock subprocess for debug test"):
            mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")

        with allure.step("Execute git command with debug enabled"):
            result = run_git_command(str(tmp_path), "status", timeout=30, debug=True)

        with allure.step("Verify debug mode output"):
            check.equal(result, "output")
            allure.attach(
                "Debug mode enabled and working", "Debug Test", allure.attachment_type.TEXT
            )

    @allure.story("Git Operations")
    @allure.title("Git command timeout handling works correctly")
    @allure.description("Validates that run_git_command handles command timeouts appropriately")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("git", "timeout", "error-handling")
    @patch("subprocess.run")
    def test_run_git_command_timeout_handling(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command timeout handling."""
        with allure.step("Setup mock subprocess to simulate timeout"):
            mock_run.side_effect = subprocess.TimeoutExpired(["git"], 30)

        with allure.step("Execute git command expecting timeout"):
            with pytest.raises(GitCommandError) as exc_info:
                run_git_command(str(tmp_path), "log", "--all", timeout=30)

        with allure.step("Verify timeout error message"):
            check.is_in("timed out", str(exc_info.value))
            allure.attach(
                f"Timeout error: {exc_info.value}", "Timeout Handling", allure.attachment_type.TEXT
            )

    @allure.story("Git Operations")
    @allure.title("Git command OS error handling works correctly")
    @allure.description("Validates that run_git_command handles OS errors appropriately")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("git", "os-error", "error-handling")
    @patch("subprocess.run")
    def test_run_git_command_os_error(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command OS error handling."""
        with allure.step("Setup mock subprocess to simulate OS error"):
            mock_run.side_effect = OSError("Command not found")

        with allure.step("Execute git command expecting OS error"):
            with pytest.raises(GitCommandError) as exc_info:
                run_git_command(str(tmp_path), "status", timeout=30)

        with allure.step("Verify OS error message"):
            check.is_in("Failed to execute", str(exc_info.value))
            allure.attach(
                f"OS error: {exc_info.value}", "OS Error Handling", allure.attachment_type.TEXT
            )

    @allure.story("Git Operations")
    @allure.title("Git command debug mode handles empty output")
    @allure.description("Validates that run_git_command debug mode works with empty command output")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git", "debug", "edge-case")
    @patch("subprocess.run")
    def test_run_git_command_debug_empty_output(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command debug mode with empty output."""
        with allure.step("Setup mock subprocess with empty output"):
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with allure.step("Execute git command with debug mode and empty output"):
            result = run_git_command(str(tmp_path), "status", timeout=30, debug=True)

        with allure.step("Verify empty output handling"):
            check.equal(result, "")
            allure.attach(
                "Empty output handled correctly in debug mode",
                "Empty Output Test",
                allure.attachment_type.TEXT,
            )

    @allure.story("Git Operations")
    @allure.title("Git command debug mode handles long output")
    @allure.description(
        "Validates that run_git_command debug mode works with extensive command output"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git", "debug", "long-output")
    @patch("subprocess.run")
    def test_run_git_command_debug_long_output(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test run_git_command debug mode with long output."""
        with allure.step("Setup mock subprocess with long output"):
            long_output = "\n".join([f"line {i}" for i in range(150)])
            mock_run.return_value = Mock(returncode=0, stdout=long_output, stderr="")

        with allure.step("Execute git command with debug mode and long output"):
            result = run_git_command(str(tmp_path), "log", timeout=30, debug=True)

        with allure.step("Verify long output handling"):
            check.equal(result, long_output)
            allure.attach(
                f"Long output length: {len(long_output)} chars, lines: 150",
                "Long Output Test",
                allure.attachment_type.TEXT,
            )


@allure.feature("Utils - Git Command Error")
class TestGitCommandError:
    """Test suite for GitCommandError exception."""

    @allure.story("Git Operations")
    @allure.title("GitCommandError creates with message")
    @allure.description("Validates that GitCommandError can be created with a custom message")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git", "error", "creation")
    def test_git_command_error_creation(self) -> None:
        """Test GitCommandError creation."""
        with allure.step("Create GitCommandError with test message"):
            error = GitCommandError("Test error message")

        with allure.step("Verify error message"):
            check.equal(str(error), "Test error message")
            allure.attach(f"Error message: {error}", "Error Creation", allure.attachment_type.TEXT)

    @allure.story("Git Operations")
    @allure.title("GitCommandError includes detailed command information")
    @allure.description(
        "Validates that GitCommandError can include detailed command and error information"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git", "error", "details")
    def test_git_command_error_with_details(self) -> None:
        """Test GitCommandError with detailed message."""
        with allure.step("Setup command details and error message"):
            cmd = ["git", "log", "--oneline"]
            stderr = "fatal: not a git repository"

        with allure.step("Create detailed GitCommandError"):
            error = GitCommandError(f"Command {cmd} failed: {stderr}")

        with allure.step("Verify detailed error content"):
            check.is_in("git", str(error))
            check.is_in("failed", str(error))
            check.is_in("fatal", str(error))
            allure.attach(f"Detailed error: {error}", "Detailed Error", allure.attachment_type.TEXT)

    @allure.story("Git Operations")
    @allure.title("GitCommandError inherits from Exception")
    @allure.description("Validates that GitCommandError is a proper Exception subclass")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git", "error", "inheritance")
    def test_git_command_error_inheritance(self) -> None:
        """Test GitCommandError inheritance."""
        with allure.step("Create GitCommandError instance"):
            error = GitCommandError("Test")

        with allure.step("Verify Exception inheritance"):
            check.is_instance(error, Exception)
            allure.attach(
                "GitCommandError correctly inherits from Exception",
                "Inheritance Test",
                allure.attachment_type.TEXT,
            )
