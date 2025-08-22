# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""A robust, async-native utility for running git commands as subprocesses."""

import subprocess

from rich import print as rprint


class GitCommandError(Exception):
    """Custom exception for errors during git command execution."""


def run_git_command(repo_path: str, *args: str, timeout: int, debug: bool = False) -> str:
    """Run a git command in a subprocess with a timeout.

    Args:
        repo_path: The path to the repository.
        *args: The arguments for the git command (e.g., "log", "--oneline").
        timeout: The timeout in seconds for the command.
        debug: If True, print the command and its output.

    Returns:
        The stdout from the command as a string.

    Raises:
        GitCommandError: If the command fails, times out, or returns a non-zero exit code.
    """
    command = ["git", "-C", repo_path, *args]
    if debug:
        rprint(f"[bold cyan]Running Git Command:[/] {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            encoding="utf-8",
            errors="ignore",
        )
        if result.returncode != 0:
            raise GitCommandError(
                f"Git command failed with exit code {result.returncode}: {result.stderr}"
            )
        if debug:
            rprint("[bold green]Git Command Output:[/]")
            output = result.stdout if result.stdout.strip() else "[EMPTY STDOUT]"
            # Truncate very large outputs in debug mode to prevent console hang
            max_debug_lines = 100
            output_lines = output.split("\n")
            if len(output_lines) > max_debug_lines:
                truncated_output = "\n".join(output_lines[:max_debug_lines])
                rprint(
                    f"{truncated_output}\n[... truncated {len(output_lines) - max_debug_lines} "
                    f"lines of output ...]"
                )
            else:
                rprint(output)
        return result.stdout
    except subprocess.TimeoutExpired as e:
        raise GitCommandError(
            f"Git command timed out after {timeout} seconds: {' '.join(command)}"
        ) from e
    except OSError as e:
        raise GitCommandError(f"Failed to execute git command: {e}") from e
