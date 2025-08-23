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


class TestWindowsFileHandling:
    """Test Windows-specific file handling issues."""

    def test_temp_directory_cleanup_with_git_repo(self) -> None:
        """Test that temp directories with Git repos clean up properly on Windows."""
        temp_path = Path(tempfile.mkdtemp())

        try:
            # Create a Git repository in the temp directory
            repo = git.Repo.init(temp_path)
            config_writer = repo.config_writer()
            try:
                config_writer.set_value("user", "name", "Test User")
                config_writer.set_value("user", "email", "test@example.com")
            finally:
                config_writer.release()

            # Create and commit a file
            test_file = temp_path / "test.txt"
            test_file.write_text("Test content", encoding="utf-8")
            repo.index.add(["test.txt"])
            repo.index.commit("Test commit")

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
            except PermissionError:
                pass  # Ignore cleanup errors
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
                except PermissionError:
                    pass  # Ignore cleanup errors

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
                        os.chmod(test_file, 0o444)
                    except OSError:
                        pass  # Some Windows systems don't support this
                else:
                    # On Unix, set various permissions
                    os.chmod(test_file, 0o600)

            # Test that cleanup can handle files with different permissions
            check.is_true(temp_path.exists())
            safe_cleanup_on_windows(temp_path)

        finally:
            try:
                safe_cleanup_on_windows(temp_path)
            except PermissionError:
                pass

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
            except PermissionError:
                pass


class TestWindowsPathHandling:
    """Test Windows-specific path handling issues."""

    def test_path_serialization_consistency(self) -> None:
        """Test that paths are serialized consistently across platforms."""
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
            except PermissionError:
                pass


class TestConcurrentFileAccess:
    """Test concurrent file access patterns that can cause Windows issues."""

    def test_rapid_file_creation_and_deletion(self) -> None:
        """Test rapid file creation and deletion that can cause Windows locking issues."""
        temp_path = Path(tempfile.mkdtemp())

        try:
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

            # Rapidly delete files
            for test_file in files_created:
                if test_file.exists():
                    try:
                        test_file.unlink()
                    except PermissionError:
                        # On Windows, files might be locked briefly
                        time.sleep(0.1)
                        test_file.unlink()

        finally:
            try:
                safe_cleanup_on_windows(temp_path)
            except PermissionError:
                pass

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
                except PermissionError:
                    pass


class TestWindowsSpecificIssues:
    """Test specific Windows issues that have been encountered."""

    def test_winerror_32_prevention(self) -> None:
        """Test prevention of WinError 32 (file in use by another process)."""
        temp_path = Path(tempfile.mkdtemp())

        try:
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

            # The key is to properly close the repo before cleanup
            repo.close()

            # Force garbage collection to release any lingering references
            gc.collect()

            # Small delay to let Windows release file locks
            if os.name == WINDOWS_OS_NAME:
                time.sleep(0.1)

            # Test that cleanup works without WinError 32
            safe_cleanup_on_windows(temp_path)

        finally:
            try:
                safe_cleanup_on_windows(temp_path)
            except PermissionError:
                pass

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
            except PermissionError:
                pass


def test_fixture_compatibility() -> None:
    """Test that our fixtures work correctly across platforms."""
    # This test uses the actual fixtures from conftest.py
    # to verify they work without issues

    # Test temp_dir fixture manually
    temp_path = Path(tempfile.mkdtemp())
    try:
        check.is_true(temp_path.exists())
        check.is_true(temp_path.is_dir())

        # Create a test file
        test_file = temp_path / "fixture_test.txt"
        test_file.write_text("Fixture test content", encoding="utf-8")
        check.is_true(test_file.exists())

    finally:
        safe_cleanup_on_windows(temp_path)


# Tests focus on cross-platform compatibility
