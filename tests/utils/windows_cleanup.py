# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Windows-compatible cleanup utilities for cross-platform CI/CD stability.

This module provides shared utilities for safely cleaning up temporary directories
and Git repositories on Windows systems, handling file locking issues gracefully.
"""

import logging
import os
from pathlib import Path
import shutil
import time
from typing import Final

import git

# Constants for magic values
WINDOWS_OS_NAME: Final[str] = "nt"


def _make_writable(path: Path) -> None:
    """Make path writable, ignoring errors."""
    try:
        os.chmod(path, 0o777)
    except OSError:
        pass  # Ignore all OS-related errors


def _prepare_windows_cleanup(temp_path: Path) -> None:
    """Prepare directory for cleanup on Windows."""
    if os.name != WINDOWS_OS_NAME:
        return

    time.sleep(0.1)  # Brief pause to let processes release locks

    # Make all files and directories writable
    for root, dirs, files in os.walk(temp_path):
        for d in dirs:
            _make_writable(Path(root) / d)
        for f in files:
            _make_writable(Path(root) / f)


def _handle_cleanup_failure(temp_path: Path, error: OSError, is_final_attempt: bool) -> None:
    """Handle cleanup failure based on platform and attempt."""
    if not is_final_attempt:
        return  # Will retry

    if os.name == WINDOWS_OS_NAME:
        # On Windows, log warning but don't raise - CI constraint
        logging.warning("Could not clean up %s: %s", temp_path, error)
        return

    # On Unix systems, re-raise the error
    raise error


def safe_cleanup_on_windows(temp_path: Path, max_retries: int = 3) -> None:
    """Safely clean up temporary directory on Windows with retry logic.

    Windows can hold locks on Git files longer than Unix systems,
    preventing immediate cleanup. This function implements retry logic
    to handle these cases gracefully.

    Args:
        temp_path: Path to temporary directory to clean up
        max_retries: Maximum number of cleanup attempts
    """
    if not temp_path.exists():
        return

    # Force close any Git repositories that might be holding locks
    if hasattr(git.Repo, "_clear_caches"):
        git.Repo._clear_caches()  # type: ignore[attr-defined]

    for attempt in range(max_retries):
        try:
            _prepare_windows_cleanup(temp_path)

            # Try to remove the directory
            shutil.rmtree(temp_path, ignore_errors=attempt < max_retries - 1)
            return  # Success!

        except OSError as error:
            is_final_attempt = attempt == max_retries - 1
            _handle_cleanup_failure(temp_path, error, is_final_attempt)

            if not is_final_attempt:
                # Wait longer between retries
                time.sleep(0.2 * (attempt + 1))