# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for async_file_utils module to improve coverage."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
import pytest_check as check

from git_ai_reporter.utils.async_file_utils import async_file_exists_with_content
from git_ai_reporter.utils.async_file_utils import async_write_file_atomic


class TestAsyncWriteFileAtomic:
    """Test suite for async_write_file_atomic function."""

    @pytest.mark.asyncio
    async def test_successful_atomic_write(self, tmp_path: Path) -> None:
        """Test successful atomic write."""
        target_file = tmp_path / "test.txt"
        content = "Hello, world!"

        result = await async_write_file_atomic(target_file, content)

        check.is_true(result)
        check.is_true(target_file.exists())
        check.equal(target_file.read_text(), content)

    @pytest.mark.asyncio
    async def test_atomic_write_overwrites_existing(self, tmp_path: Path) -> None:
        """Test atomic write overwrites existing file."""
        target_file = tmp_path / "test.txt"
        target_file.write_text("Original content")

        new_content = "New content"
        result = await async_write_file_atomic(target_file, new_content)

        check.is_true(result)
        check.equal(target_file.read_text(), new_content)

    @pytest.mark.asyncio
    async def test_atomic_write_with_unicode(self, tmp_path: Path) -> None:
        """Test atomic write with Unicode content."""
        target_file = tmp_path / "unicode.txt"
        content = "Hello 🌍 你好 مرحبا"

        result = await async_write_file_atomic(target_file, content)

        check.is_true(result)
        check.equal(target_file.read_text(encoding="utf-8"), content)

    @pytest.mark.asyncio
    async def test_atomic_write_with_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test atomic write creates parent directories."""
        target_file = tmp_path / "nested" / "deep" / "test.txt"
        content = "Nested content"

        result = await async_write_file_atomic(target_file, content)

        check.is_true(result)
        check.is_true(target_file.exists())
        check.equal(target_file.read_text(), content)

    @pytest.mark.asyncio
    async def test_atomic_write_permission_error(self, tmp_path: Path) -> None:
        """Test atomic write handles permission errors."""
        target_file = tmp_path / "readonly.txt"
        content = "Test content"

        # Mock to simulate permission error during tempfile creation
        with patch("tempfile.NamedTemporaryFile", side_effect=PermissionError("Permission denied")):
            result = await async_write_file_atomic(target_file, content)
            check.is_false(result)

    @pytest.mark.asyncio
    async def test_atomic_write_cleanup_on_error(self, tmp_path: Path) -> None:
        """Test temp file cleanup when atomic write fails."""
        target_file = tmp_path / "test.txt"
        content = "Test content"

        # Mock the replace operation to fail
        with patch("asyncio.to_thread", side_effect=OSError("Replace failed")):
            with patch("aiofiles.os.remove", new_callable=AsyncMock) as mock_remove:
                result = await async_write_file_atomic(target_file, content)

                check.is_false(result)
                # Should have attempted to clean up temp file
                mock_remove.assert_called_once()

    @pytest.mark.asyncio
    async def test_atomic_write_with_pathlib_path(self, tmp_path: Path) -> None:
        """Test atomic write works with pathlib.Path objects."""
        target_file = tmp_path / "pathlib.txt"
        content = "Pathlib content"

        result = await async_write_file_atomic(target_file, content)  # Path object

        check.is_true(result)
        check.equal(target_file.read_text(), content)

    @pytest.mark.asyncio
    async def test_atomic_write_with_string_path(self, tmp_path: Path) -> None:
        """Test atomic write works with string paths."""
        target_file = tmp_path / "string.txt"
        content = "String path content"

        result = await async_write_file_atomic(str(target_file), content)  # String path

        check.is_true(result)
        check.equal(target_file.read_text(), content)


class TestAsyncFileExistsWithContent:
    """Test suite for async_file_exists_with_content function."""

    @pytest.mark.asyncio
    async def test_file_exists_with_content(self, tmp_path: Path) -> None:
        """Test file that exists and has content."""
        test_file = tmp_path / "content.txt"
        test_file.write_text("Some content")

        result = await async_file_exists_with_content(test_file)
        check.is_true(result)

    @pytest.mark.asyncio
    async def test_file_exists_but_empty(self, tmp_path: Path) -> None:
        """Test file that exists but is empty."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()  # Create empty file

        result = await async_file_exists_with_content(test_file)
        check.is_false(result)

    @pytest.mark.asyncio
    async def test_file_does_not_exist(self, tmp_path: Path) -> None:
        """Test file that doesn't exist."""
        test_file = tmp_path / "nonexistent.txt"

        result = await async_file_exists_with_content(test_file)
        check.is_false(result)

    @pytest.mark.asyncio
    async def test_file_with_whitespace_only(self, tmp_path: Path) -> None:
        """Test file with only whitespace content."""
        test_file = tmp_path / "whitespace.txt"
        test_file.write_text("   \n\t  \n  ")

        result = await async_file_exists_with_content(test_file)
        check.is_true(result)  # Function only checks file size > 0, doesn't strip whitespace

    @pytest.mark.asyncio
    async def test_file_with_actual_content_and_whitespace(self, tmp_path: Path) -> None:
        """Test file with actual content surrounded by whitespace."""
        test_file = tmp_path / "padded.txt"
        test_file.write_text("   \n  Hello World  \n\t  ")

        result = await async_file_exists_with_content(test_file)
        check.is_true(result)  # Has content (file size > 0)

    @pytest.mark.asyncio
    async def test_string_path_input(self, tmp_path: Path) -> None:
        """Test function works with string path input."""
        test_file = tmp_path / "string_path.txt"
        test_file.write_text("Content via string path")

        result = await async_file_exists_with_content(str(test_file))
        check.is_true(result)

    @pytest.mark.asyncio
    async def test_pathlib_path_input(self, tmp_path: Path) -> None:
        """Test function works with pathlib.Path input."""
        test_file = tmp_path / "pathlib_path.txt"
        test_file.write_text("Content via pathlib")

        result = await async_file_exists_with_content(test_file)
        check.is_true(result)

    @pytest.mark.asyncio
    async def test_permission_error_handling(self, tmp_path: Path) -> None:
        """Test handling of permission errors."""
        test_file = tmp_path / "permission_test.txt"

        # Mock to simulate permission error
        with patch("aiofiles.open", side_effect=PermissionError("No permission")):
            result = await async_file_exists_with_content(test_file)
            check.is_false(result)

    @pytest.mark.asyncio
    async def test_os_error_handling(self, tmp_path: Path) -> None:
        """Test handling of OS errors."""
        test_file = tmp_path / "os_error_test.txt"

        # Mock to simulate OS error
        with patch("aiofiles.open", side_effect=OSError("OS error")):
            result = await async_file_exists_with_content(test_file)
            check.is_false(result)

    @pytest.mark.asyncio
    async def test_binary_file_handling(self, tmp_path: Path) -> None:
        """Test handling of binary files."""
        test_file = tmp_path / "binary.bin"
        # Write some binary data
        test_file.write_bytes(b"\x00\x01\x02\x03\xff")

        # Function only checks file size, so binary files with size > 0 return True
        result = await async_file_exists_with_content(test_file)
        check.is_true(result)

    @pytest.mark.asyncio
    async def test_very_large_file_timeout(self, tmp_path: Path) -> None:
        """Test function doesn't hang on very large files."""
        test_file = tmp_path / "large.txt"

        # Create a file with significant content
        content = "A" * 10000  # 10KB of content
        test_file.write_text(content)

        # Should complete quickly even for larger files
        start_time = asyncio.get_event_loop().time()
        result = await async_file_exists_with_content(test_file)
        end_time = asyncio.get_event_loop().time()

        check.is_true(result)
        check.less(end_time - start_time, 1.0)  # Should complete within 1 second
