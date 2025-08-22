# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Shared utilities for async file operations.

This module provides common async file I/O operations with robust error handling,
atomic writing, and safety checks used across the git-ai-reporter application.
"""

import asyncio
import os
from pathlib import Path
import tempfile
from typing import Final

import aiofiles
import aiofiles.os

# Constants for file operations
DEFAULT_ENCODING: Final[str] = "utf-8"
TEMP_PREFIX: Final[str] = "git_ai_reporter_"


async def async_read_file_safe(file_path: Path | str) -> str | None:
    """Safely read a file's content with error handling.

    Args:
        file_path: Path to the file to read.

    Returns:
        File content as string, or None if file doesn't exist or can't be read.
    """
    try:
        async with aiofiles.open(file_path, "r", encoding=DEFAULT_ENCODING) as f:
            return await f.read()
    except OSError:
        return None


async def async_write_file_atomic(file_path: Path | str, content: str) -> bool:
    """Write content to a file atomically using a temporary file.

    This ensures that the target file is never in a partially written state,
    even if the process is interrupted during writing.

    Args:
        file_path: Path to the target file.
        content: Content to write.

    Returns:
        True if write was successful, False otherwise.
    """
    file_path = Path(file_path)

    try:
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=DEFAULT_ENCODING,
            prefix=TEMP_PREFIX,
            dir=file_path.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(content)
            temp_file.flush()
            await asyncio.to_thread(
                os.fsync, temp_file.file.fileno()
            )  # Ensure data is written to disk

        # Atomic move - replace target file with temp file
        await asyncio.to_thread(temp_path.replace, file_path)
        return True

    except OSError:
        # Clean up temp file if it exists
        try:
            if (temp_path_var := locals().get("temp_path")) is not None:
                await aiofiles.os.remove(temp_path_var)
        except OSError:
            pass  # Temp file already cleaned up or inaccessible
        return False


async def async_file_exists_with_content(file_path: Path | str) -> bool:
    """Check if a file exists and has non-empty content.

    Args:
        file_path: Path to the file to check.

    Returns:
        True if file exists and has content, False otherwise.
    """
    try:
        stat_result = await aiofiles.os.stat(file_path)
        return stat_result.st_size > 0
    except OSError:
        return False


async def async_ensure_file_exists(file_path: Path | str, default_content: str = "") -> bool:
    """Ensure a file exists, creating it with default content if it doesn't.

    Args:
        file_path: Path to the file.
        default_content: Content to write if file doesn't exist.

    Returns:
        True if file exists or was created successfully, False otherwise.
    """
    file_path = Path(file_path)

    if await aiofiles.os.path.exists(file_path):
        return True

    try:
        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, "w", encoding=DEFAULT_ENCODING) as f:
            await f.write(default_content)
        return True

    except OSError:
        return False


async def async_read_or_create_file(file_path: Path | str, default_content: str = "") -> str:
    """Read file content, creating it with default content if it doesn't exist.

    Args:
        file_path: Path to the file.
        default_content: Content to use if file doesn't exist.

    Returns:
        File content or default content if file was created.

    Raises:
        OSError: If file operations fail.
    """
    if (content := await async_read_file_safe(file_path)) is not None:
        return content

    # File doesn't exist, create it
    if await async_ensure_file_exists(file_path, default_content):
        return default_content

    # If we couldn't create the file, raise an error
    raise OSError(f"Could not read or create file: {file_path}")


async def async_backup_file(file_path: Path | str, backup_suffix: str = ".bak") -> bool:
    """Create a backup copy of a file.

    Args:
        file_path: Path to the file to backup.
        backup_suffix: Suffix to append to the backup filename.

    Returns:
        True if backup was created successfully, False otherwise.
    """
    file_path = Path(file_path)
    backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)

    try:
        if (content := await async_read_file_safe(file_path)) is None:
            return False  # Source file doesn't exist

        return await async_write_file_atomic(backup_path, content)

    except OSError:
        return False


async def async_safe_write_with_backup(
    file_path: Path | str, content: str, backup_suffix: str = ".bak"
) -> bool:
    """Write content to a file with automatic backup of the original.

    Args:
        file_path: Path to the target file.
        content: Content to write.
        backup_suffix: Suffix for the backup file.

    Returns:
        True if write was successful, False otherwise.
    """
    file_path = Path(file_path)

    # Create backup if file exists
    if await aiofiles.os.path.exists(file_path):
        if not await async_backup_file(file_path, backup_suffix):
            return False  # Backup failed

    # Write new content
    return await async_write_file_atomic(file_path, content)
