# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for git_ai_reporter.utils.git_command_runner module.

This module tests the git command execution utility.
"""

import subprocess
from unittest.mock import MagicMock
from unittest.mock import patch

import allure
import pytest
import pytest_check as check

from git_ai_reporter.utils.git_command_runner import GitCommandError
from git_ai_reporter.utils.git_command_runner import run_git_command


@allure.feature("Git Command Execution Utilities")
class TestRunGitCommand:
    """Test suite for run_git_command function."""

    @allure.story("Successful Command Execution")
    @allure.title("Execute git command successfully and return output")
    @allure.description(
        "Tests that git commands execute successfully and return the expected output with proper parameters"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("git-command", "success-case", "subprocess")
    def test_successful_command_execution(self) -> None:
        """Test successful git command execution."""
        with allure.step("Set up mock subprocess result"):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "commit abc123\nAuthor: Test User"
            mock_result.stderr = ""
            allure.attach(
                f"Return code: {mock_result.returncode}\nStdout: {mock_result.stdout}",
                "Mock Subprocess Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute git command via run_git_command"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = run_git_command("/repo", "log", "--oneline", timeout=30)
                allure.attach(result, "Git Command Output", allure.attachment_type.TEXT)

        with allure.step("Verify command result and subprocess call"):
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
            allure.attach(
                str(mock_run.call_args), "Subprocess Call Arguments", allure.attachment_type.TEXT
            )

    @allure.story("Debug Mode")
    @allure.title("Execute git command with debug output enabled")
    @allure.description(
        "Tests that debug mode produces appropriate diagnostic output for git commands"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git-command", "debug-mode", "diagnostics")
    def test_command_with_debug_output(self) -> None:
        """Test git command execution with debug output."""
        with allure.step("Set up mock subprocess result for debug test"):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "debug output"
            mock_result.stderr = ""
            allure.attach(
                "Debug mode enabled with mock output",
                "Debug Test Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute git command with debug=True"):
            with patch("subprocess.run", return_value=mock_result):
                with patch("git_ai_reporter.utils.git_command_runner.rprint") as mock_print:
                    result = run_git_command("/repo", "status", timeout=10, debug=True)
                    allure.attach(result, "Debug Command Output", allure.attachment_type.TEXT)

        with allure.step("Verify debug output and print calls"):
            check.equal(result, "debug output")
            # Should print the command and output
            check.equal(mock_print.call_count, 3)
            mock_print.assert_any_call("[bold cyan]Running Git Command:[/] git -C /repo status")
            mock_print.assert_any_call("[bold green]Git Command Output:[/]")
            mock_print.assert_any_call("debug output")
            allure.attach(
                f"Print call count: {mock_print.call_count}",
                "Debug Print Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("Debug Mode")
    @allure.title("Handle empty output in debug mode")
    @allure.description(
        "Tests that debug mode properly handles and reports empty/whitespace-only output"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git-command", "debug-mode", "empty-output")
    def test_command_with_empty_output_debug(self) -> None:
        """Test git command with empty output in debug mode."""
        with allure.step("Set up mock result with whitespace-only output"):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "   "  # Whitespace only
            mock_result.stderr = ""
            allure.attach(
                "Whitespace-only stdout configured",
                "Empty Output Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute git command with debug mode and empty output"):
            with patch("subprocess.run", return_value=mock_result):
                with patch("git_ai_reporter.utils.git_command_runner.rprint") as mock_print:
                    result = run_git_command("/repo", "status", timeout=10, debug=True)
                    allure.attach(
                        f"Result: '{result}'", "Empty Output Result", allure.attachment_type.TEXT
                    )

        with allure.step("Verify empty output handling in debug mode"):
            check.equal(result, "   ")
            # Should show [EMPTY STDOUT] when output is whitespace only
            mock_print.assert_any_call("[EMPTY STDOUT]")

    @allure.story("Error Handling")
    @allure.title("Handle git command failure with non-zero exit code")
    @allure.description(
        "Tests that git commands with non-zero exit codes raise appropriate GitCommandError exceptions"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("git-command", "error-handling", "exit-codes")
    def test_command_failure_with_non_zero_exit(self) -> None:
        """Test git command failure with non-zero exit code."""
        with allure.step("Set up mock result with non-zero exit code"):
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "fatal: not a git repository"
            allure.attach(
                f"Exit code: {mock_result.returncode}\nStderr: {mock_result.stderr}",
                "Error Result Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute failing git command and expect GitCommandError"):
            with patch("subprocess.run", return_value=mock_result):
                with pytest.raises(GitCommandError) as exc_info:
                    run_git_command("/not-a-repo", "status", timeout=30)

                allure.attach(
                    str(exc_info.value), "GitCommandError Details", allure.attachment_type.TEXT
                )

        with allure.step("Verify error message contains exit code and stderr"):
            check.is_in("Git command failed with exit code 1", str(exc_info.value))
            check.is_in("fatal: not a git repository", str(exc_info.value))

    @allure.story("Error Handling")
    @allure.title("Handle git command timeout scenarios")
    @allure.description(
        "Tests that git commands that exceed timeout limits raise appropriate GitCommandError exceptions"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("git-command", "timeout", "error-handling")
    def test_command_timeout(self) -> None:
        """Test git command timeout handling."""
        with allure.step("Set up subprocess timeout scenario"):
            timeout_exception = subprocess.TimeoutExpired(
                cmd=["git", "-C", "/repo", "log"],
                timeout=5,
            )
            allure.attach(
                f"Timeout: 5 seconds\nCommand: {timeout_exception.cmd}",
                "Timeout Scenario Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute git command with timeout and expect GitCommandError"):
            with patch("subprocess.run", side_effect=timeout_exception):
                with pytest.raises(GitCommandError) as exc_info:
                    run_git_command("/repo", "log", timeout=5)

                allure.attach(
                    str(exc_info.value), "Timeout Error Details", allure.attachment_type.TEXT
                )

        with allure.step("Verify timeout error message contains timeout duration and command"):
            check.is_in("Git command timed out after 5 seconds", str(exc_info.value))
            check.is_in("git -C /repo log", str(exc_info.value))

    @allure.story("Error Handling")
    @allure.title("Handle OS errors during git command execution")
    @allure.description(
        "Tests that OS errors (like command not found) are properly caught and wrapped in GitCommandError"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("git-command", "os-errors", "error-handling")
    def test_command_os_error(self) -> None:
        """Test handling of OS errors during command execution."""
        with allure.step("Set up OS error scenario"):
            os_error = OSError("Command not found")
            allure.attach(str(os_error), "OS Error Setup", allure.attachment_type.TEXT)

        with allure.step("Execute git command with OS error and expect GitCommandError"):
            with patch("subprocess.run", side_effect=os_error):
                with pytest.raises(GitCommandError) as exc_info:
                    run_git_command("/repo", "status", timeout=30)

                allure.attach(str(exc_info.value), "OS Error Details", allure.attachment_type.TEXT)

        with allure.step("Verify OS error message is properly wrapped"):
            check.is_in("Failed to execute git command", str(exc_info.value))
            check.is_in("Command not found", str(exc_info.value))

    @allure.story("Command Arguments")
    @allure.title("Execute git command with multiple arguments")
    @allure.description(
        "Tests that git commands with multiple arguments are properly assembled and executed"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git-command", "arguments", "multiple-args")
    def test_command_with_multiple_arguments(self) -> None:
        """Test git command with multiple arguments."""
        with allure.step("Set up mock result for multi-argument command"):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = ""
            allure.attach(
                "Multi-argument git log command configured",
                "Multi-Arg Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute git command with multiple arguments"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = run_git_command(
                    "/repo",
                    "log",
                    "--since=2025-01-01",
                    "--until=2025-01-07",
                    "--format=%H",
                    timeout=60,
                )
                allure.attach(result, "Multi-Arg Command Output", allure.attachment_type.TEXT)

        with allure.step("Verify multi-argument command assembly and execution"):
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
            allure.attach(
                str(mock_run.call_args[0][0]),
                "Command Array Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("Unicode Support")
    @allure.title("Handle unicode characters in git command output")
    @allure.description(
        "Tests that git commands properly handle unicode characters in output including emojis and international text"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git-command", "unicode", "encoding")
    def test_command_with_unicode_output(self) -> None:
        """Test handling of unicode output from git command."""
        with allure.step("Set up mock result with unicode output"):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "commit by 用户 with émoji 🚀"
            mock_result.stderr = ""
            allure.attach(mock_result.stdout, "Unicode Output Setup", allure.attachment_type.TEXT)

        with allure.step("Execute git command with unicode output"):
            with patch("subprocess.run", return_value=mock_result):
                result = run_git_command("/repo", "log", timeout=30)
                allure.attach(result, "Unicode Command Result", allure.attachment_type.TEXT)

        with allure.step("Verify unicode characters are preserved"):
            check.equal(result, "commit by 用户 with émoji 🚀")

    @allure.story("Output Handling")
    @allure.title("Ignore stderr on successful git commands")
    @allure.description(
        "Tests that stderr is ignored when git commands succeed (exit code 0) and only stdout is returned"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git-command", "stderr", "success-case")
    def test_command_with_stderr_on_success(self) -> None:
        """Test that stderr is ignored on successful commands."""
        with allure.step("Set up successful command with stderr output"):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success output"
            mock_result.stderr = "warning: something"
            allure.attach(
                f"Exit code: {mock_result.returncode}\nStdout: {mock_result.stdout}\nStderr: {mock_result.stderr}",
                "Success with Stderr Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute successful git command with stderr"):
            with patch("subprocess.run", return_value=mock_result):
                result = run_git_command("/repo", "status", timeout=30)
                allure.attach(
                    result, "Command Result (Stderr Ignored)", allure.attachment_type.TEXT
                )

        with allure.step("Verify only stdout is returned, stderr is ignored"):
            # Should return stdout and ignore stderr when successful
            check.equal(result, "success output")

    @allure.story("Path Handling")
    @allure.title("Handle empty repository path")
    @allure.description(
        "Tests that git commands work with empty repository paths (current directory)"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git-command", "path-handling", "empty-path")
    def test_command_with_empty_repo_path(self) -> None:
        """Test git command with empty repository path."""
        with allure.step("Set up mock result for empty path command"):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = ""
            allure.attach(
                "Empty repository path configured", "Empty Path Setup", allure.attachment_type.TEXT
            )

        with allure.step("Execute git command with empty repository path"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = run_git_command("", "status", timeout=30)
                allure.attach(result, "Empty Path Command Result", allure.attachment_type.TEXT)

        with allure.step("Verify empty path is handled correctly"):
            check.equal(result, "output")
            # Should still include -C flag even with empty path
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            check.equal(args[0], "git")
            check.equal(args[1], "-C")
            check.equal(args[2], "")
            allure.attach(str(args[:3]), "Command Args Verification", allure.attachment_type.TEXT)

    @allure.story("Path Handling")
    @allure.title("Handle special characters in repository path")
    @allure.description(
        "Tests that git commands work correctly with paths containing spaces and special characters"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git-command", "path-handling", "special-characters")
    def test_command_with_special_characters_in_path(self) -> None:
        """Test git command with special characters in repository path."""
        with allure.step("Set up mock result for special character path"):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = ""
            special_path = "/path with spaces/repo"
            allure.attach(
                f"Special path: {special_path}",
                "Special Character Path Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute git command with special character path"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = run_git_command(special_path, "status", timeout=30)
                allure.attach(result, "Special Path Command Result", allure.attachment_type.TEXT)

        with allure.step("Verify special characters in path are preserved"):
            check.equal(result, "output")
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            check.equal(args[2], "/path with spaces/repo")
            allure.attach(
                f"Path argument: {args[2]}",
                "Path Preservation Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("Exception Handling")
    @allure.title("Verify GitCommandError exception properties")
    @allure.description(
        "Tests that GitCommandError is properly defined as an Exception subclass with correct behavior"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git-command", "exceptions", "error-types")
    def test_command_error_types(self) -> None:
        """Test that GitCommandError is properly raised."""
        with allure.step("Verify GitCommandError is Exception subclass"):
            # Test that GitCommandError is an Exception subclass
            check.is_true(issubclass(GitCommandError, Exception))
            allure.attach(
                f"GitCommandError inheritance: {GitCommandError.__mro__}",
                "Exception Inheritance Verification",
                allure.attachment_type.TEXT,
            )

        with allure.step("Test GitCommandError message handling"):
            # Test creating GitCommandError with message
            error = GitCommandError("Test error message")
            check.equal(str(error), "Test error message")
            allure.attach(str(error), "GitCommandError Message Test", allure.attachment_type.TEXT)

    @allure.story("Timeout Handling")
    @allure.title("Handle zero timeout configuration")
    @allure.description("Tests that git commands work with zero timeout (no timeout) configuration")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("git-command", "timeout", "zero-timeout")
    def test_command_with_zero_timeout(self) -> None:
        """Test git command with zero timeout (should work but risky)."""
        with allure.step("Set up mock result for zero timeout command"):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = ""
            allure.attach(
                "Zero timeout configured (no timeout limit)",
                "Zero Timeout Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute git command with zero timeout"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = run_git_command("/repo", "status", timeout=0)
                allure.attach(result, "Zero Timeout Command Result", allure.attachment_type.TEXT)

        with allure.step("Verify zero timeout is passed through correctly"):
            check.equal(result, "output")
            # Verify timeout=0 is passed through
            check.equal(mock_run.call_args[1]["timeout"], 0)
            allure.attach(
                str(mock_run.call_args[1]["timeout"]),
                "Timeout Parameter Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("Error Handling")
    @allure.title("Handle negative exit codes from git commands")
    @allure.description(
        "Tests that git commands with negative exit codes (signal termination) raise appropriate errors"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("git-command", "negative-exit-code", "signal-termination")
    def test_command_with_negative_exit_code(self) -> None:
        """Test git command with negative exit code."""
        with allure.step("Set up mock result with negative exit code"):
            mock_result = MagicMock()
            mock_result.returncode = -1
            mock_result.stdout = ""
            mock_result.stderr = "terminated"
            allure.attach(
                f"Exit code: {mock_result.returncode} (signal termination)\nStderr: {mock_result.stderr}",
                "Negative Exit Code Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute git command with negative exit code and expect GitCommandError"):
            with patch("subprocess.run", return_value=mock_result):
                with pytest.raises(GitCommandError) as exc_info:
                    run_git_command("/repo", "status", timeout=30)

                allure.attach(
                    str(exc_info.value), "Negative Exit Code Error", allure.attachment_type.TEXT
                )

        with allure.step("Verify negative exit code error message"):
            check.is_in("Git command failed with exit code -1", str(exc_info.value))

    @allure.story("Output Handling")
    @allure.title("Preserve newlines in git command output")
    @allure.description(
        "Tests that newlines and blank lines in git command output are correctly preserved"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("git-command", "newlines", "output-formatting")
    def test_command_preserves_newlines(self) -> None:
        """Test that output newlines are preserved."""
        with allure.step("Set up mock result with multiple newlines"):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "line1\nline2\n\nline4\n"
            mock_result.stderr = ""
            allure.attach(
                repr(mock_result.stdout), "Newline Output Setup", allure.attachment_type.TEXT
            )

        with allure.step("Execute git command with newline output"):
            with patch("subprocess.run", return_value=mock_result):
                result = run_git_command("/repo", "log", timeout=30)
                allure.attach(
                    repr(result), "Newline Preservation Result", allure.attachment_type.TEXT
                )

        with allure.step("Verify all newlines are preserved"):
            check.equal(result, "line1\nline2\n\nline4\n")
            check.equal(result.count("\n"), 4)
            allure.attach(
                f"Newline count: {result.count('\n')}",
                "Newline Count Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("Debug Mode")
    @allure.title("Handle debug output truncation for long output")
    @allure.description("Tests that debug mode truncates very long output to prevent console spam")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("git-command", "debug-mode", "truncation")
    def test_command_with_debug_output_truncation(self) -> None:
        """Test git command execution with debug output truncation (lines 52-53)."""
        with allure.step("Generate long output exceeding debug line limit"):
            # Create output that exceeds default max_debug_lines (100 in the code)
            output_lines = [f"line {i}" for i in range(150)]  # More than max_debug_lines
            long_output = "\n".join(output_lines)

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = long_output
            mock_result.stderr = ""

            allure.attach(
                f"Output lines: {len(output_lines)}\nFirst 5 lines: {output_lines[:5]}",
                "Long Output Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute git command with long output in debug mode"):
            with patch("subprocess.run", return_value=mock_result):
                with patch("git_ai_reporter.utils.git_command_runner.rprint") as mock_print:
                    result = run_git_command("/repo", "status", timeout=10, debug=True)
                    allure.attach(
                        f"Result length: {len(result)} chars",
                        "Long Output Result",
                        allure.attachment_type.TEXT,
                    )

        with allure.step("Verify output is returned full but debug is truncated"):
            check.equal(result, long_output)
            # Should print truncated output with truncation message
            truncation_indicator = "truncated"
            truncation_call_found = False
            for call in mock_print.call_args_list:
                if truncation_indicator in str(call).lower():
                    truncation_call_found = True
                    break

            check.is_true(truncation_call_found, "Expected truncation message in debug output")
            allure.attach(
                f"Truncation message found: {truncation_call_found}",
                "Debug Truncation Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("Debug Mode")
    @allure.title("Handle debug output without truncation for short output")
    @allure.description(
        "Tests that debug mode prints full output when it's shorter than the truncation limit"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("git-command", "debug-mode", "no-truncation")
    def test_command_with_debug_output_no_truncation_needed(self) -> None:
        """Test git command execution with debug output that doesn't need truncation."""
        with allure.step("Generate short output below debug line limit"):
            # Create output that's less than max_debug_lines
            output_lines = [f"line {i}" for i in range(5)]  # Less than max_debug_lines
            short_output = "\n".join(output_lines)

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = short_output
            mock_result.stderr = ""

            allure.attach(
                f"Output lines: {len(output_lines)}\nFull output: {short_output}",
                "Short Output Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute git command with short output in debug mode"):
            with patch("subprocess.run", return_value=mock_result):
                with patch("git_ai_reporter.utils.git_command_runner.rprint") as mock_print:
                    result = run_git_command("/repo", "status", timeout=10, debug=True)
                    allure.attach(result, "Short Output Result", allure.attachment_type.TEXT)

        with allure.step("Verify full output is printed without truncation"):
            check.equal(result, short_output)
            # Should print full output without truncation
            mock_print.assert_any_call(short_output)
            allure.attach(
                "Full output printed in debug mode without truncation",
                "No Truncation Verification",
                allure.attachment_type.TEXT,
            )
