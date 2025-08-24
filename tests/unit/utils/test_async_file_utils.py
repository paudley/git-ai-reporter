# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for async_file_utils module to improve coverage."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import patch

import allure
import pytest
import pytest_check as check

from git_ai_reporter.utils.async_file_utils import async_file_exists_with_content
from git_ai_reporter.utils.async_file_utils import async_write_file_atomic


@allure.feature("Async File Utilities")
class TestAsyncWriteFileAtomic:
    """Test suite for async_write_file_atomic function."""

    @allure.story("Successful File Operations")
    @allure.title("Write file atomically with successful completion")
    @allure.description(
        "Tests that atomic file write completes successfully and creates file with expected content"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("async-file", "atomic-write", "success-case", "file-io")
    @pytest.mark.asyncio
    async def test_successful_atomic_write(self, tmp_path: Path) -> None:
        """Test successful atomic write."""
        with allure.step("Set up test file path and content"):
            target_file = tmp_path / "test.txt"
            content = "Hello, world!"
            allure.attach(str(target_file), "Target File Path", allure.attachment_type.TEXT)
            allure.attach(content, "File Content", allure.attachment_type.TEXT)

        with allure.step("Execute atomic write operation"):
            result = await async_write_file_atomic(target_file, content)
            allure.attach(str(result), "Operation Result", allure.attachment_type.TEXT)

        with allure.step("Verify file was created successfully"):
            check.is_true(result)
            check.is_true(target_file.exists())
            actual_content = target_file.read_text(encoding="utf-8")
            check.equal(actual_content, content)
            allure.attach(actual_content, "Actual File Content", allure.attachment_type.TEXT)

    @allure.story("File Overwrite Operations")
    @allure.title("Overwrite existing file with atomic write")
    @allure.description("Tests that atomic write correctly overwrites existing file content")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("async-file", "atomic-write", "overwrite", "file-io")
    @pytest.mark.asyncio
    async def test_atomic_write_overwrites_existing(self, tmp_path: Path) -> None:
        """Test atomic write overwrites existing file."""
        with allure.step("Create existing file with original content"):
            target_file = tmp_path / "test.txt"
            original_content = "Original content"
            target_file.write_text(original_content)
            allure.attach(str(target_file), "Target File Path", allure.attachment_type.TEXT)
            allure.attach(original_content, "Original Content", allure.attachment_type.TEXT)

        with allure.step("Execute atomic write with new content"):
            new_content = "New content"
            allure.attach(new_content, "New Content", allure.attachment_type.TEXT)
            result = await async_write_file_atomic(target_file, new_content)
            allure.attach(str(result), "Operation Result", allure.attachment_type.TEXT)

        with allure.step("Verify file was overwritten successfully"):
            check.is_true(result)
            actual_content = target_file.read_text(encoding="utf-8")
            check.equal(actual_content, new_content)
            allure.attach(actual_content, "Final File Content", allure.attachment_type.TEXT)

    @allure.story("Unicode Content Handling")
    @allure.title("Write Unicode content atomically")
    @allure.description(
        "Tests that atomic write correctly handles Unicode characters and international text"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "atomic-write", "unicode", "encoding", "international")
    @pytest.mark.asyncio
    async def test_atomic_write_with_unicode(self, tmp_path: Path) -> None:
        """Test atomic write with Unicode content."""
        with allure.step("Set up Unicode content for writing"):
            target_file = tmp_path / "unicode.txt"
            content = "Hello 🌍 你好 مرحبا"
            allure.attach(str(target_file), "Target File Path", allure.attachment_type.TEXT)
            allure.attach(content, "Unicode Content", allure.attachment_type.TEXT)

        with allure.step("Execute atomic write with Unicode content"):
            result = await async_write_file_atomic(target_file, content)
            allure.attach(str(result), "Operation Result", allure.attachment_type.TEXT)

        with allure.step("Verify Unicode content was written correctly"):
            check.is_true(result)
            actual_content = target_file.read_text(encoding="utf-8")
            check.equal(actual_content, content)
            allure.attach(actual_content, "Actual Unicode Content", allure.attachment_type.TEXT)

    @allure.story("Directory Creation")
    @allure.title("Create parent directories during atomic write")
    @allure.description(
        "Tests that atomic write automatically creates missing parent directories when writing files"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "atomic-write", "directory-creation", "nested-paths")
    @pytest.mark.asyncio
    async def test_atomic_write_with_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test atomic write creates parent directories."""
        with allure.step("Set up nested file path in non-existent directories"):
            target_file = tmp_path / "nested" / "deep" / "test.txt"
            content = "Nested content"
            allure.attach(str(target_file), "Nested File Path", allure.attachment_type.TEXT)
            allure.attach(content, "File Content", allure.attachment_type.TEXT)
            allure.attach(
                str(target_file.parent.exists()),
                "Parent Directory Exists (Before)",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute atomic write to nested path"):
            result = await async_write_file_atomic(target_file, content)
            allure.attach(str(result), "Operation Result", allure.attachment_type.TEXT)

        with allure.step("Verify directory creation and file writing"):
            check.is_true(result)
            check.is_true(target_file.exists())
            actual_content = target_file.read_text(encoding="utf-8")
            check.equal(actual_content, content)
            allure.attach(
                str(target_file.parent.exists()),
                "Parent Directory Exists (After)",
                allure.attachment_type.TEXT,
            )
            allure.attach(actual_content, "Final File Content", allure.attachment_type.TEXT)

    @allure.story("Error Handling")
    @allure.title("Handle permission errors during atomic write")
    @allure.description(
        "Tests that atomic write gracefully handles permission errors and returns False"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "atomic-write", "error-handling", "permissions")
    @pytest.mark.asyncio
    async def test_atomic_write_permission_error(self, tmp_path: Path) -> None:
        """Test atomic write handles permission errors."""
        with allure.step("Set up test file path and content"):
            target_file = tmp_path / "readonly.txt"
            content = "Test content"
            allure.attach(str(target_file), "Target File Path", allure.attachment_type.TEXT)
            allure.attach(content, "File Content", allure.attachment_type.TEXT)

        with allure.step("Mock tempfile creation to simulate permission error"):
            # Mock to simulate permission error during tempfile creation
            with patch(
                "tempfile.NamedTemporaryFile", side_effect=PermissionError("Permission denied")
            ):
                with allure.step("Execute atomic write operation"):
                    result = await async_write_file_atomic(target_file, content)
                    allure.attach(str(result), "Operation Result", allure.attachment_type.TEXT)

                with allure.step("Verify permission error was handled gracefully"):
                    check.is_false(result)

    @allure.story("Error Recovery")
    @allure.title("Clean up temporary files on atomic write failure")
    @allure.description(
        "Tests that atomic write properly cleans up temporary files when the operation fails"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "atomic-write", "error-recovery", "cleanup")
    @pytest.mark.asyncio
    async def test_atomic_write_cleanup_on_error(self, tmp_path: Path) -> None:
        """Test temp file cleanup when atomic write fails."""
        with allure.step("Set up test file path and content"):
            target_file = tmp_path / "test.txt"
            content = "Test content"
            allure.attach(str(target_file), "Target File Path", allure.attachment_type.TEXT)
            allure.attach(content, "File Content", allure.attachment_type.TEXT)

        with allure.step("Mock replace operation to fail and monitor cleanup"):
            # Mock the replace operation to fail
            with patch("asyncio.to_thread", side_effect=OSError("Replace failed")):
                with patch("aiofiles.os.remove", new_callable=AsyncMock) as mock_remove:
                    with allure.step("Execute atomic write operation"):
                        result = await async_write_file_atomic(target_file, content)
                        allure.attach(str(result), "Operation Result", allure.attachment_type.TEXT)

                    with allure.step("Verify operation failed and cleanup was attempted"):
                        check.is_false(result)
                        # Should have attempted to clean up temp file
                        mock_remove.assert_called_once()
                        allure.attach(
                            str(mock_remove.call_count),
                            "Cleanup Attempts",
                            allure.attachment_type.TEXT,
                        )

    @allure.story("Path Type Support")
    @allure.title("Write file using pathlib.Path objects")
    @allure.description(
        "Tests that atomic write correctly handles pathlib.Path objects as file paths"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "atomic-write", "pathlib", "path-types")
    @pytest.mark.asyncio
    async def test_atomic_write_with_pathlib_path(self, tmp_path: Path) -> None:
        """Test atomic write works with pathlib.Path objects."""
        with allure.step("Set up pathlib.Path and content"):
            target_file = tmp_path / "pathlib.txt"
            content = "Pathlib content"
            allure.attach(str(target_file), "Pathlib File Path", allure.attachment_type.TEXT)
            allure.attach(str(type(target_file)), "Path Type", allure.attachment_type.TEXT)
            allure.attach(content, "File Content", allure.attachment_type.TEXT)

        with allure.step("Execute atomic write with pathlib.Path object"):
            result = await async_write_file_atomic(target_file, content)  # Path object
            allure.attach(str(result), "Operation Result", allure.attachment_type.TEXT)

        with allure.step("Verify pathlib.Path was handled correctly"):
            check.is_true(result)
            actual_content = target_file.read_text(encoding="utf-8")
            check.equal(actual_content, content)
            allure.attach(actual_content, "Final File Content", allure.attachment_type.TEXT)

    @allure.story("Path Type Support")
    @allure.title("Write file using string path")
    @allure.description("Tests that atomic write correctly handles string paths as file paths")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "atomic-write", "string-path", "path-types")
    @pytest.mark.asyncio
    async def test_atomic_write_with_string_path(self, tmp_path: Path) -> None:
        """Test atomic write works with string paths."""
        with allure.step("Set up string path and content"):
            target_file = tmp_path / "string.txt"
            content = "String path content"
            string_path = str(target_file)
            allure.attach(string_path, "String File Path", allure.attachment_type.TEXT)
            allure.attach(str(type(string_path)), "Path Type", allure.attachment_type.TEXT)
            allure.attach(content, "File Content", allure.attachment_type.TEXT)

        with allure.step("Execute atomic write with string path"):
            result = await async_write_file_atomic(str(target_file), content)  # String path
            allure.attach(str(result), "Operation Result", allure.attachment_type.TEXT)

        with allure.step("Verify string path was handled correctly"):
            check.is_true(result)
            actual_content = target_file.read_text(encoding="utf-8")
            check.equal(actual_content, content)
            allure.attach(actual_content, "Final File Content", allure.attachment_type.TEXT)


@allure.feature("Async File Existence Checking")
class TestAsyncFileExistsWithContent:
    """Test suite for async_file_exists_with_content function."""

    @allure.story("File Existence with Content")
    @allure.title("Detect existing file with content")
    @allure.description(
        "Tests that function correctly identifies files that exist and contain content"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("async-file", "file-exists", "content-check", "success-case")
    @pytest.mark.asyncio
    async def test_file_exists_with_content(self, tmp_path: Path) -> None:
        """Test file that exists and has content."""
        with allure.step("Create test file with content"):
            test_file = tmp_path / "content.txt"
            content = "Some content"
            test_file.write_text(content)
            allure.attach(str(test_file), "Test File Path", allure.attachment_type.TEXT)
            allure.attach(content, "File Content", allure.attachment_type.TEXT)
            allure.attach(str(test_file.exists()), "File Exists", allure.attachment_type.TEXT)

        with allure.step("Check if file exists with content"):
            result = await async_file_exists_with_content(test_file)
            allure.attach(str(result), "Function Result", allure.attachment_type.TEXT)

        with allure.step("Verify file was detected as having content"):
            check.is_true(result)

    @allure.story("Empty File Detection")
    @allure.title("Detect existing but empty file")
    @allure.description(
        "Tests that function correctly identifies files that exist but have no content"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("async-file", "file-exists", "empty-file", "edge-case")
    @pytest.mark.asyncio
    async def test_file_exists_but_empty(self, tmp_path: Path) -> None:
        """Test file that exists but is empty."""
        with allure.step("Create empty test file"):
            test_file = tmp_path / "empty.txt"
            test_file.touch()  # Create empty file
            allure.attach(str(test_file), "Test File Path", allure.attachment_type.TEXT)
            allure.attach(str(test_file.exists()), "File Exists", allure.attachment_type.TEXT)
            allure.attach(str(test_file.stat().st_size), "File Size", allure.attachment_type.TEXT)

        with allure.step("Check if empty file is detected as having content"):
            result = await async_file_exists_with_content(test_file)
            allure.attach(str(result), "Function Result", allure.attachment_type.TEXT)

        with allure.step("Verify empty file was correctly identified"):
            check.is_false(result)

    @allure.story("Nonexistent File Detection")
    @allure.title("Handle nonexistent file")
    @allure.description("Tests that function correctly handles files that do not exist")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("async-file", "file-exists", "nonexistent", "edge-case")
    @pytest.mark.asyncio
    async def test_file_does_not_exist(self, tmp_path: Path) -> None:
        """Test file that doesn't exist."""
        with allure.step("Set up path to nonexistent file"):
            test_file = tmp_path / "nonexistent.txt"
            allure.attach(str(test_file), "Test File Path", allure.attachment_type.TEXT)
            allure.attach(str(test_file.exists()), "File Exists", allure.attachment_type.TEXT)

        with allure.step("Check if nonexistent file is detected as having content"):
            result = await async_file_exists_with_content(test_file)
            allure.attach(str(result), "Function Result", allure.attachment_type.TEXT)

        with allure.step("Verify nonexistent file was correctly identified"):
            check.is_false(result)

    @allure.story("Whitespace Content Handling")
    @allure.title("Handle file with only whitespace content")
    @allure.description(
        "Tests that function correctly handles files containing only whitespace characters"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "file-exists", "whitespace", "edge-case")
    @pytest.mark.asyncio
    async def test_file_with_whitespace_only(self, tmp_path: Path) -> None:
        """Test file with only whitespace content."""
        with allure.step("Create file with whitespace-only content"):
            test_file = tmp_path / "whitespace.txt"
            whitespace_content = "   \n\t  \n  "
            test_file.write_text(whitespace_content)
            allure.attach(str(test_file), "Test File Path", allure.attachment_type.TEXT)
            allure.attach(
                repr(whitespace_content), "Whitespace Content (repr)", allure.attachment_type.TEXT
            )
            allure.attach(str(test_file.stat().st_size), "File Size", allure.attachment_type.TEXT)

        with allure.step("Check if whitespace-only file is detected as having content"):
            result = await async_file_exists_with_content(test_file)
            allure.attach(str(result), "Function Result", allure.attachment_type.TEXT)

        with allure.step("Verify whitespace content was detected"):
            check.is_true(result)  # Function only checks file size > 0, doesn't strip whitespace

    @allure.story("Mixed Content Handling")
    @allure.title("Handle file with content and whitespace")
    @allure.description(
        "Tests that function correctly handles files with actual content surrounded by whitespace"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "file-exists", "mixed-content", "whitespace")
    @pytest.mark.asyncio
    async def test_file_with_actual_content_and_whitespace(self, tmp_path: Path) -> None:
        """Test file with actual content surrounded by whitespace."""
        with allure.step("Create file with content padded by whitespace"):
            test_file = tmp_path / "padded.txt"
            padded_content = "   \n  Hello World  \n\t  "
            test_file.write_text(padded_content)
            allure.attach(str(test_file), "Test File Path", allure.attachment_type.TEXT)
            allure.attach(
                repr(padded_content), "Padded Content (repr)", allure.attachment_type.TEXT
            )
            allure.attach(str(test_file.stat().st_size), "File Size", allure.attachment_type.TEXT)

        with allure.step("Check if padded content file is detected as having content"):
            result = await async_file_exists_with_content(test_file)
            allure.attach(str(result), "Function Result", allure.attachment_type.TEXT)

        with allure.step("Verify padded content was detected"):
            check.is_true(result)  # Has content (file size > 0)

    @allure.story("Path Type Support")
    @allure.title("Handle string path input")
    @allure.description("Tests that function correctly handles string path inputs")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "file-exists", "string-path", "path-types")
    @pytest.mark.asyncio
    async def test_string_path_input(self, tmp_path: Path) -> None:
        """Test function works with string path input."""
        with allure.step("Create test file and prepare string path"):
            test_file = tmp_path / "string_path.txt"
            content = "Content via string path"
            test_file.write_text(content)
            string_path = str(test_file)
            allure.attach(string_path, "String Path", allure.attachment_type.TEXT)
            allure.attach(str(type(string_path)), "Path Type", allure.attachment_type.TEXT)
            allure.attach(content, "File Content", allure.attachment_type.TEXT)

        with allure.step("Check file existence using string path"):
            result = await async_file_exists_with_content(str(test_file))
            allure.attach(str(result), "Function Result", allure.attachment_type.TEXT)

        with allure.step("Verify string path was handled correctly"):
            check.is_true(result)

    @allure.story("Path Type Support")
    @allure.title("Handle pathlib.Path input")
    @allure.description("Tests that function correctly handles pathlib.Path object inputs")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "file-exists", "pathlib", "path-types")
    @pytest.mark.asyncio
    async def test_pathlib_path_input(self, tmp_path: Path) -> None:
        """Test function works with pathlib.Path input."""
        with allure.step("Create test file using pathlib.Path"):
            test_file = tmp_path / "pathlib_path.txt"
            content = "Content via pathlib"
            test_file.write_text(content)
            allure.attach(str(test_file), "Pathlib Path", allure.attachment_type.TEXT)
            allure.attach(str(type(test_file)), "Path Type", allure.attachment_type.TEXT)
            allure.attach(content, "File Content", allure.attachment_type.TEXT)

        with allure.step("Check file existence using pathlib.Path"):
            result = await async_file_exists_with_content(test_file)
            allure.attach(str(result), "Function Result", allure.attachment_type.TEXT)

        with allure.step("Verify pathlib.Path was handled correctly"):
            check.is_true(result)

    @allure.story("Error Handling")
    @allure.title("Handle permission errors gracefully")
    @allure.description("Tests that function correctly handles permission errors and returns False")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "file-exists", "error-handling", "permissions")
    @pytest.mark.asyncio
    async def test_permission_error_handling(self, tmp_path: Path) -> None:
        """Test handling of permission errors."""
        with allure.step("Set up test file path"):
            test_file = tmp_path / "permission_test.txt"
            allure.attach(str(test_file), "Test File Path", allure.attachment_type.TEXT)

        with allure.step("Mock aiofiles.open to simulate permission error"):
            # Mock to simulate permission error
            with patch("aiofiles.open", side_effect=PermissionError("No permission")):
                with allure.step("Execute file existence check"):
                    result = await async_file_exists_with_content(test_file)
                    allure.attach(str(result), "Function Result", allure.attachment_type.TEXT)

                with allure.step("Verify permission error was handled gracefully"):
                    check.is_false(result)

    @allure.story("Error Handling")
    @allure.title("Handle OS errors gracefully")
    @allure.description("Tests that function correctly handles OS errors and returns False")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "file-exists", "error-handling", "os-errors")
    @pytest.mark.asyncio
    async def test_os_error_handling(self, tmp_path: Path) -> None:
        """Test handling of OS errors."""
        with allure.step("Set up test file path"):
            test_file = tmp_path / "os_error_test.txt"
            allure.attach(str(test_file), "Test File Path", allure.attachment_type.TEXT)

        with allure.step("Mock aiofiles.open to simulate OS error"):
            # Mock to simulate OS error
            with patch("aiofiles.open", side_effect=OSError("OS error")):
                with allure.step("Execute file existence check"):
                    result = await async_file_exists_with_content(test_file)
                    allure.attach(str(result), "Function Result", allure.attachment_type.TEXT)

                with allure.step("Verify OS error was handled gracefully"):
                    check.is_false(result)

    @allure.story("Binary File Handling")
    @allure.title("Handle binary files correctly")
    @allure.description(
        "Tests that function correctly handles binary files and detects them as having content"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "file-exists", "binary-files", "edge-case")
    @pytest.mark.asyncio
    async def test_binary_file_handling(self, tmp_path: Path) -> None:
        """Test handling of binary files."""
        with allure.step("Create binary file with binary data"):
            test_file = tmp_path / "binary.bin"
            # Write some binary data
            binary_data = b"\x00\x01\x02\x03\xff"
            test_file.write_bytes(binary_data)
            allure.attach(str(test_file), "Binary File Path", allure.attachment_type.TEXT)
            allure.attach(str(binary_data), "Binary Data (str)", allure.attachment_type.TEXT)
            allure.attach(str(test_file.stat().st_size), "File Size", allure.attachment_type.TEXT)

        with allure.step("Check if binary file is detected as having content"):
            result = await async_file_exists_with_content(test_file)
            allure.attach(str(result), "Function Result", allure.attachment_type.TEXT)

        with allure.step("Verify binary file was detected as having content"):
            # Function only checks file size, so binary files with size > 0 return True
            check.is_true(result)

    @allure.story("Performance Testing")
    @allure.title("Handle large files efficiently")
    @allure.description(
        "Tests that function processes large files efficiently without hanging or excessive delays"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("async-file", "file-exists", "performance", "large-files")
    @pytest.mark.asyncio
    async def test_very_large_file_timeout(self, tmp_path: Path) -> None:
        """Test function doesn't hang on very large files."""
        with allure.step("Create large file with significant content"):
            test_file = tmp_path / "large.txt"
            # Create a file with significant content
            content = "A" * 10000  # 10KB of content
            test_file.write_text(content)
            allure.attach(str(test_file), "Large File Path", allure.attachment_type.TEXT)
            allure.attach(str(len(content)), "Content Length", allure.attachment_type.TEXT)
            allure.attach(
                str(test_file.stat().st_size), "File Size (bytes)", allure.attachment_type.TEXT
            )

        with allure.step("Execute file existence check with timing"):
            # Should complete quickly even for larger files
            start_time = asyncio.get_event_loop().time()
            result = await async_file_exists_with_content(test_file)
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time

            allure.attach(str(result), "Function Result", allure.attachment_type.TEXT)
            allure.attach(
                f"{execution_time:.4f} seconds", "Execution Time", allure.attachment_type.TEXT
            )

        with allure.step("Verify large file processing performance"):
            check.is_true(result)
            check.less(execution_time, 1.0)  # Should complete within 1 second
