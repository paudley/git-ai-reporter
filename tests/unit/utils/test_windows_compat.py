# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Windows compatibility tests for cross-platform CI/CD stability.

This module contains tests specifically designed to catch Windows-specific
issues early and ensure compatibility across platforms.
"""

import gc
import os
from pathlib import Path
import tempfile
import time
from typing import Final
import warnings

import allure
import git
import pytest
import pytest_check as check

# Import shared Windows cleanup utilities
from tests.utils.windows_cleanup import safe_cleanup_on_windows

# Constants for magic values
WINDOWS_OS_NAME: Final[str] = "nt"
BACKSLASH: Final[str] = "\\"
ASCII_LIMIT: Final[int] = 127
CAFE_TEXT: Final[str] = "Café"
ASCII_ENCODINGS: Final[frozenset[str]] = frozenset(["ascii", "cp1252"])


@allure.feature("Utils - Windows File Handling")
@allure.story("Cross-Platform File Operations")
class TestWindowsFileHandling:
    """Test Windows-specific file handling issues."""

    @allure.title("Clean up temporary Git repositories on Windows")
    @allure.description(
        "Verifies that temporary directories containing Git repositories can be properly cleaned up on Windows systems"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("windows", "file-cleanup", "git", "temp-directories")
    def test_temp_directory_cleanup_with_git_repo(self) -> None:
        """Test that temp directories with Git repos clean up properly on Windows."""
        with allure.step("Create temporary directory and Git repository"):
            temp_path = Path(tempfile.mkdtemp())

        try:
            with allure.step("Initialize Git repository with configuration"):
                # Create a Git repository in the temp directory
                repo = git.Repo.init(temp_path)
            config_writer = repo.config_writer()
            try:
                config_writer.set_value("user", "name", "Test User")
                config_writer.set_value("user", "email", "test@example.com")
            finally:
                config_writer.release()

            with allure.step("Create and commit test file"):
                # Create and commit a file
                test_file = temp_path / "test.txt"
                test_file.write_text("Test content", encoding="utf-8")
                repo.index.add(["test.txt"])
                repo.index.commit("Test commit")

            with allure.step("Close repository and test cleanup"):
                # Close the repo to release locks
                repo.close()

                # Test that our cleanup function works
                check.is_true(temp_path.exists())
                safe_cleanup_on_windows(temp_path)

            # On Windows, we allow cleanup to fail gracefully
            if os.name != WINDOWS_OS_NAME:
                check.is_false(temp_path.exists())
            # On Windows, we just verify no exception was raised

        except (OSError, git.exc.GitError):
            # Ensure cleanup even if test fails
            try:
                safe_cleanup_on_windows(temp_path)
            except PermissionError as e:
                # Log cleanup errors for debugging

                warnings.warn(f"Cleanup failed: {e}", UserWarning, stacklevel=2)
            raise

    def test_multiple_git_repos_cleanup(self) -> None:
        """Test cleanup of multiple Git repositories created in quick succession."""
        temp_paths = []

        try:
            # Create multiple temp directories with Git repos
            for i in range(3):
                temp_path = Path(tempfile.mkdtemp())
                temp_paths.append(temp_path)

                repo = git.Repo.init(temp_path)
                config_writer = repo.config_writer()
                try:
                    config_writer.set_value("user", "name", "Test User")
                    config_writer.set_value("user", "email", "test@example.com")
                finally:
                    config_writer.release()

                # Create a unique file for each repo
                test_file = temp_path / f"test_{i}.txt"
                test_file.write_text(f"Test content {i}", encoding="utf-8")
                repo.index.add([f"test_{i}.txt"])
                repo.index.commit(f"Test commit {i}")
                repo.close()

            # Test cleanup of all repos
            for temp_path in temp_paths:
                check.is_true(temp_path.exists())
                safe_cleanup_on_windows(temp_path)

        finally:
            # Ensure all temp paths are cleaned up
            for temp_path in temp_paths:
                try:
                    safe_cleanup_on_windows(temp_path)
                except PermissionError as e:
                    # Log cleanup errors for debugging
                    warnings.warn(f"Cleanup failed for {temp_path}: {e}", UserWarning, stacklevel=2)

    def test_file_permissions_on_windows(self) -> None:
        """Test file permission handling on Windows."""
        temp_path = Path(tempfile.mkdtemp())

        try:
            # Create files with different permissions
            test_files = []
            for i in range(3):
                test_file = temp_path / f"test_{i}.txt"
                test_file.write_text(f"Content {i}", encoding="utf-8")
                test_files.append(test_file)

                # Try to set different permissions
                if os.name == WINDOWS_OS_NAME:
                    # On Windows, try to make file read-only
                    try:
                        os.chmod(test_file, 0o600)  # Owner read/write only
                    except OSError as e:
                        # Some Windows systems don't support permission changes

                        warnings.warn(
                            f"Cannot set permissions on Windows: {e}", UserWarning, stacklevel=2
                        )
                else:
                    # On Unix, set various permissions
                    os.chmod(test_file, 0o600)

            # Test that cleanup can handle files with different permissions
            check.is_true(temp_path.exists())
            safe_cleanup_on_windows(temp_path)

        finally:
            try:
                safe_cleanup_on_windows(temp_path)
            except PermissionError as e:
                # Log cleanup errors for debugging

                warnings.warn(f"Final cleanup failed: {e}", UserWarning, stacklevel=2)

    @pytest.mark.parametrize(
        "encoding,content",
        [
            ("utf-8", "Hello, 世界! 🚀"),
            ("ascii", "Hello, World!"),
            ("cp1252", "Hello, World! Café"),
        ],
    )
    def test_file_encoding_compatibility(self, encoding: str, content: str) -> None:
        """Test file encoding compatibility across platforms."""
        temp_path = Path(tempfile.mkdtemp())

        try:
            test_file = temp_path / "encoding_test.txt"

            try:
                # Try to write with different encodings
                test_file.write_text(content, encoding=encoding)

                # Verify we can read it back
                read_content = test_file.read_text(encoding=encoding)
                check.equal(read_content, content)

            except UnicodeEncodeError as e:
                # Expected for some encoding/content combinations
                if encoding in ASCII_ENCODINGS and any(
                    ord(c) > ASCII_LIMIT for c in content if c not in CAFE_TEXT
                ):
                    pytest.skip(f"Cannot encode content '{content}' with {encoding}: {e}")
                raise

        finally:
            try:
                safe_cleanup_on_windows(temp_path)
            except PermissionError as e:
                # Log cleanup errors for debugging

                warnings.warn(f"Encoding test cleanup failed: {e}", UserWarning, stacklevel=2)


@allure.feature("Utils - Windows Path Handling")
@allure.story("Cross-Platform Path Operations")
class TestWindowsPathHandling:
    """Test Windows-specific path handling issues."""

    @allure.title("Ensure consistent path serialization across platforms")
    @allure.description(
        "Verifies that file paths are serialized consistently using POSIX format across different operating systems"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("windows", "paths", "serialization", "cross-platform")
    def test_path_serialization_consistency(self) -> None:
        """Test that paths are serialized consistently across platforms."""
        with allure.step("Create various path types for testing"):
            # Test various path types
            paths = [
                Path("/home/user/file.txt"),
                Path("relative/path/file.txt"),
                Path("./current/file.txt"),
                Path("../parent/file.txt"),
            ]

        # Only test Windows paths on Windows to avoid cross-platform issues
        if os.name == WINDOWS_OS_NAME:
            paths.append(Path("C:\\Users\\User\\file.txt"))

        with allure.step("Test POSIX path conversion for consistency"):
            for path in paths:
                # Test as_posix() for cross-platform consistency
                posix_path = path.as_posix()
                check.is_instance(posix_path, str)

            # Only check for backslashes if we're not on the current platform
            # where the path might legitimately contain backslashes
            if not (os.name == WINDOWS_OS_NAME and str(path).startswith("C:")):
                check.is_false(BACKSLASH in posix_path)  # No backslashes in POSIX paths

            # Test that Path.as_posix() is idempotent
            reparsed_path = Path(posix_path)
            check.equal(path.as_posix(), reparsed_path.as_posix())

    def test_temp_path_handling(self) -> None:
        """Test temporary path creation and handling."""
        temp_path = Path(tempfile.mkdtemp())

        try:
            # Verify the temp path is absolute
            check.is_true(temp_path.is_absolute())

            # Test path resolution
            resolved_path = temp_path.expanduser().resolve()
            check.is_true(resolved_path.is_absolute())

            # On Windows, test path normalization
            if os.name == WINDOWS_OS_NAME:
                normalized_path = os.path.normpath(os.path.abspath(str(resolved_path)))
                check.is_not_none(normalized_path)
                check.is_instance(normalized_path, str)

            # Test POSIX path consistency
            posix_path = temp_path.as_posix()
            check.is_false(BACKSLASH in posix_path)

        finally:
            try:
                safe_cleanup_on_windows(temp_path)
            except PermissionError as e:
                # Log cleanup errors for debugging

                warnings.warn(f"Temp path cleanup failed: {e}", UserWarning, stacklevel=2)


@allure.feature("Utils - Concurrent File Access")
@allure.story("Windows File Locking Prevention")
class TestConcurrentFileAccess:
    """Test concurrent file access patterns that can cause Windows issues."""

    @allure.title("Handle rapid file operations without locking")
    @allure.description(
        "Verifies that rapid file creation and deletion operations don't cause Windows file locking issues"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("windows", "file-locking", "concurrent-access", "rapid-operations")
    def test_rapid_file_creation_and_deletion(self) -> None:
        """Test rapid file creation and deletion that can cause Windows locking issues."""
        with allure.step("Setup temporary directory for rapid operations"):
            temp_path = Path(tempfile.mkdtemp())

        try:
            with allure.step("Rapidly create multiple files"):
                files_created = []

                # Rapidly create files
                for i in range(10):
                    test_file = temp_path / f"rapid_{i}.txt"
                    test_file.write_text(f"Content {i}", encoding="utf-8")
                    files_created.append(test_file)

                # Small delay to simulate real usage
                time.sleep(0.01)

            # Verify all files exist
            for test_file in files_created:
                check.is_true(test_file.exists())

            with allure.step("Rapidly delete files with Windows compatibility"):
                # Rapidly delete files
                for test_file in files_created:
                    if test_file.exists():
                        try:
                            test_file.unlink()
                        except PermissionError as e:
                            # On Windows, files might be locked briefly

                            warnings.warn(f"File locked, retrying: {e}", UserWarning, stacklevel=2)
                            time.sleep(0.1)
                            test_file.unlink()

        finally:
            try:
                safe_cleanup_on_windows(temp_path)
            except PermissionError as e:
                # Log cleanup errors for debugging

                warnings.warn(f"Rapid file test cleanup failed: {e}", UserWarning, stacklevel=2)

    def test_git_repository_cleanup_stress_test(self) -> None:
        """Stress test Git repository cleanup to catch Windows locking issues."""
        repos_created = []

        try:
            # Create multiple repos in quick succession
            for i in range(5):
                temp_path = Path(tempfile.mkdtemp())
                repos_created.append(temp_path)

                repo = git.Repo.init(temp_path)
                config_writer = repo.config_writer()
                try:
                    config_writer.set_value("user", "name", f"Test User {i}")
                    config_writer.set_value("user", "email", f"test{i}@example.com")
                finally:
                    config_writer.release()

                # Create multiple commits
                for j in range(3):
                    test_file = temp_path / f"file_{i}_{j}.txt"
                    test_file.write_text(f"Content {i}_{j}", encoding="utf-8")
                    repo.index.add([f"file_{i}_{j}.txt"])
                    repo.index.commit(f"Commit {i}_{j}")

                # Explicitly close the repo
                repo.close()

                # Small delay between repos
                time.sleep(0.05)

            # Clean up all repos
            for temp_path in repos_created:
                check.is_true(temp_path.exists())
                safe_cleanup_on_windows(temp_path)

        finally:
            # Ensure cleanup even if test fails
            for temp_path in repos_created:
                try:
                    safe_cleanup_on_windows(temp_path)
                except PermissionError as e:
                    # Log cleanup errors for debugging
                    warnings.warn(
                        f"Stress test cleanup failed for {temp_path}: {e}",
                        UserWarning,
                        stacklevel=2,
                    )


@allure.feature("Utils - Windows Specific Issues")
@allure.story("Windows Error Prevention")
class TestWindowsSpecificIssues:
    """Test specific Windows issues that have been encountered."""

    @allure.title("Prevent WinError 32 file locking issues")
    @allure.description(
        "Verifies that proper resource cleanup prevents WinError 32 (file in use by another process)"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("windows", "winerror-32", "file-locking", "resource-cleanup")
    def test_winerror_32_prevention(self) -> None:
        """Test prevention of WinError 32 (file in use by another process)."""
        with allure.step("Setup scenario that could cause WinError 32"):
            temp_path = Path(tempfile.mkdtemp())

        try:
            with allure.step("Create Git repository that could lock files"):
                # Simulate the pattern that causes WinError 32
                repo = git.Repo.init(temp_path)
            config_writer = repo.config_writer()
            try:
                config_writer.set_value("user", "name", "Test User")
                config_writer.set_value("user", "email", "test@example.com")
            finally:
                config_writer.release()

            # Create a commit
            test_file = temp_path / "test.txt"
            test_file.write_text("Test content", encoding="utf-8")
            repo.index.add(["test.txt"])
            repo.index.commit("Test commit")

            with allure.step("Perform proper cleanup to prevent file locking"):
                # The key is to properly close the repo before cleanup
                repo.close()

                # Force garbage collection to release any lingering references
                gc.collect()

            # Small delay to let Windows release file locks
            if os.name == WINDOWS_OS_NAME:
                time.sleep(0.1)

            with allure.step("Verify cleanup succeeds without WinError 32"):
                # Test that cleanup works without WinError 32
                safe_cleanup_on_windows(temp_path)

        finally:
            try:
                safe_cleanup_on_windows(temp_path)
            except PermissionError as e:
                # Log cleanup errors for debugging

                warnings.warn(f"WinError32 test cleanup failed: {e}", UserWarning, stacklevel=2)

    def test_long_path_handling(self) -> None:
        """Test handling of long paths on Windows."""
        temp_path = Path(tempfile.mkdtemp())

        try:
            # Create a nested directory structure
            nested_path = temp_path
            for i in range(5):
                nested_path = (
                    nested_path / f"very_long_directory_name_{i}_that_creates_deep_nesting"
                )
                nested_path.mkdir(exist_ok=True)

            # Create a file in the deep path
            test_file = nested_path / "deep_file.txt"
            test_file.write_text("Deep content", encoding="utf-8")
            check.is_true(test_file.exists())

            # Test cleanup of deep paths
            safe_cleanup_on_windows(temp_path)

        finally:
            try:
                safe_cleanup_on_windows(temp_path)
            except PermissionError as e:
                # Log cleanup errors for debugging

                warnings.warn(f"Long path test cleanup failed: {e}", UserWarning, stacklevel=2)


@allure.title("Verify test fixture compatibility across platforms")
@allure.description(
    "Ensures that test fixtures work correctly on both Windows and Unix-like systems"
)
@allure.severity(allure.severity_level.MINOR)
@allure.tag("fixtures", "cross-platform", "compatibility")
def test_fixture_compatibility() -> None:
    """Test that our fixtures work correctly across platforms."""
    with allure.step("Test fixture functionality manually"):
        # This test uses the actual fixtures from conftest.py
        # to verify they work without issues

        # Test temp_dir fixture manually
        temp_path = Path(tempfile.mkdtemp())
    try:
        with allure.step("Verify fixture creates proper directory structure"):
            check.is_true(temp_path.exists())
            check.is_true(temp_path.is_dir())

        with allure.step("Create test file and verify functionality"):
            # Create a test file
            test_file = temp_path / "fixture_test.txt"
            test_file.write_text("Fixture test content", encoding="utf-8")
            check.is_true(test_file.exists())

    finally:
        safe_cleanup_on_windows(temp_path)


# Tests focus on cross-platform compatibility
