# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for pre-release functionality."""

from datetime import datetime
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import allure
import git
import pytest
import pytest_check as check

from git_ai_reporter.cli import main
from git_ai_reporter.models import Change
from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.services.gemini import GeminiClient


@allure.feature("Pre-Release Feature")
@allure.story("Version Release Management")
class TestPreReleaseFeature:
    """Test suite for pre-release functionality."""

    @pytest.fixture
    def temp_git_repo_with_files(self) -> tuple[git.Repo, Path]:
        """Create a temporary git repository with initial files."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        # Initialize git repo
        repo = git.Repo.init(temp_dir)

        # Create initial NEWS.md
        news_content = """---
title: Project News
description: Development summaries and project updates
created: 2025-01-01
updated: 2025-01-23
format: markdown
---

# Project News

## Week 3: January 15 - January 21, 2025

Previous development activities.
"""

        # Create initial CHANGELOG.txt
        changelog_content = """# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New user authentication system
- Enhanced data processing capabilities

### Fixed
- Memory leak in data processing pipeline
- Database connection timeout issues

### Changed
- Updated API endpoints for v2 compliance

## [1.0.0] - 2025-01-01

### Added
- Initial stable release
"""

        # Write files
        news_path = temp_path / "NEWS.md"
        changelog_path = temp_path / "CHANGELOG.txt"
        daily_path = temp_path / "DAILY_UPDATES.md"

        news_path.write_text(news_content, encoding="utf-8")
        changelog_path.write_text(changelog_content, encoding="utf-8")
        daily_path.write_text("# Daily Updates\n\n", encoding="utf-8")

        # Add some sample commits
        sample_file = temp_path / "src/test.py"
        sample_file.parent.mkdir(exist_ok=True)
        sample_file.write_text("# hello world", encoding="utf-8")

        repo.index.add([str(news_path), str(changelog_path), str(daily_path), str(sample_file)])
        repo.index.commit("Initial commit")

        # Add another commit
        sample_file.write_text("# hello updated world", encoding="utf-8")
        repo.index.add([str(sample_file)])
        repo.index.commit("feat: Update greeting message")

        return repo, temp_path

    @pytest.fixture
    def mock_gemini_client(self) -> MagicMock:
        """Create a mock Gemini client."""

        # Create a mock that passes isinstance checks
        client = MagicMock(spec=GeminiClient)

        # Mock internal attributes needed by orchestrator
        client._client = MagicMock()
        client._config = MagicMock()
        client._config.model_tier2 = "gemini-2.5-pro"

        # Mock the token counter that's used by PromptFitter
        mock_token_counter = MagicMock()
        mock_token_counter.count_tokens = AsyncMock(
            return_value=1000
        )  # Return reasonable token count
        client._token_counter = mock_token_counter

        # Use AsyncMock for async methods
        client.generate_commit_analysis = AsyncMock(
            return_value=CommitAnalysis(
                changes=[Change(summary="Added feature", category="New Feature")], trivial=False
            )
        )
        client.synthesize_daily_summary = AsyncMock(return_value="Daily summary content.")
        client.generate_news_narrative = AsyncMock(
            return_value="This week brought significant improvements including new authentication features and performance enhancements."
        )
        client.generate_changelog_entries = AsyncMock(
            return_value="""### Added
- New user authentication system

### Fixed
- Memory leak fixes

### Changed
- API endpoint updates"""
        )

        return client

    @allure.title("Create version section in changelog during pre-release")
    @allure.description(
        "Verifies that pre-release flag properly creates versioned sections in CHANGELOG.txt and NEWS.md"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("pre-release", "versioning", "changelog", "news")
    def test_pre_release_creates_version_section(
        self,
        temp_git_repo_with_files: tuple[git.Repo, Path],
        mock_gemini_client: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that pre-release flag creates proper version section."""
        with allure.step("Setup test environment and version"):
            _repo, temp_path = temp_git_repo_with_files
            version = "1.2.3"

            # Set up environment
            monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")

        with (
            patch("git_ai_reporter.cli.GeminiClient", return_value=mock_gemini_client),
            patch("git_ai_reporter.cli.genai.Client"),
            patch("git_ai_reporter.services.gemini.GeminiClient", return_value=mock_gemini_client),
        ):

            # Run with pre-release flag
            main(
                repo_path=str(temp_path),
                weeks=1,
                start_date_str=None,
                end_date_str=None,
                config_file=None,
                cache_dir=".git-report-cache",
                no_cache=False,
                debug=True,
                pre_release=version,
            )

        with allure.step("Verify CHANGELOG.txt version section creation"):
            # Verify CHANGELOG.txt has version section
            changelog_path = temp_path / "CHANGELOG.txt"
            changelog_content = changelog_path.read_text(encoding="utf-8")

            check.is_in(
                f"[v{version}]", changelog_content, f"Should contain version section v{version}"
            )

        # Get today's date dynamically
        today = datetime.now().strftime("%Y-%m-%d")
        check.is_in(today, changelog_content, f"Should contain today's date {today}")
        check.is_in(
            "## [Unreleased]", changelog_content, "Should have new empty unreleased section"
        )

        # Verify NEWS.md has release header
        news_path = temp_path / "NEWS.md"
        news_content = news_path.read_text(encoding="utf-8")

        # The release marker appears in the week header format: "## Week N: ... - Released v1.2.3 🚀"
        # Note: This test currently fails due to an issue in the orchestrator's narrative generation task execution
        check.is_in(f"Released v{version} 🚀", news_content, f"Should show release v{version}")
        check.is_in("##", news_content, "Should have a week header")

    def test_pre_release_preserves_existing_versions(
        self,
        temp_git_repo_with_files: tuple[git.Repo, Path],
        mock_gemini_client: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that pre-release preserves existing version history."""
        _repo, temp_path = temp_git_repo_with_files
        version = "2.0.0"

        # Set up environment
        monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")

        # Get initial changelog content
        changelog_path = temp_path / "CHANGELOG.txt"
        # Get initial changelog content for verification
        changelog_path.read_text(encoding="utf-8")

        with (
            patch("git_ai_reporter.cli.GeminiClient", return_value=mock_gemini_client),
            patch("git_ai_reporter.cli.genai.Client"),
            patch("git_ai_reporter.services.gemini.GeminiClient", return_value=mock_gemini_client),
        ):

            # Run with pre-release flag
            main(
                repo_path=str(temp_path),
                weeks=1,
                start_date_str=None,
                end_date_str=None,
                config_file=None,
                cache_dir=".git-report-cache",
                no_cache=False,
                debug=True,
                pre_release=version,
            )

        # Verify changelog
        updated_content = changelog_path.read_text(encoding="utf-8")

        # Should have new version section at top
        check.is_in(f"[v{version}]", updated_content, f"Should have new version v{version}")

        # Should preserve existing version
        check.is_in("[1.0.0] - 2025-01-01", updated_content, "Should preserve existing version")

        # Version order should be correct (newer first)
        v2_pos = updated_content.find(f"[v{version}]")
        v1_pos = updated_content.find("[1.0.0]")
        check.is_true(v2_pos < v1_pos, "New version should appear before old version")

    def test_pre_release_with_no_version_string(
        self,
        temp_git_repo_with_files: tuple[git.Repo, Path],
        mock_gemini_client: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test pre-release without version (should work normally)."""
        _repo, temp_path = temp_git_repo_with_files

        # Set up environment
        monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")

        with (
            patch("git_ai_reporter.cli.GeminiClient", return_value=mock_gemini_client),
            patch("git_ai_reporter.cli.genai.Client"),
            patch("git_ai_reporter.services.gemini.GeminiClient", return_value=mock_gemini_client),
        ):

            # Run without pre-release flag (normal mode)
            main(
                repo_path=str(temp_path),
                weeks=1,
                start_date_str=None,
                end_date_str=None,
                config_file=None,
                cache_dir=".git-report-cache",
                no_cache=False,
                debug=True,
                pre_release=None,  # No pre-release
            )

        # Verify normal operation
        changelog_path = temp_path / "CHANGELOG.txt"
        changelog_content = changelog_path.read_text(encoding="utf-8")

        # Should still have [Unreleased] section (not converted to version)
        check.is_in("## [Unreleased]", changelog_content, "Should have unreleased section")
        # Should not have version-specific sections from this run
        check.is_not_in("Released v", changelog_content, "Should not show release marker")

        # Verify NEWS.md doesn't have release marker
        news_path = temp_path / "NEWS.md"
        news_content = news_path.read_text(encoding="utf-8")

        # Should not contain "Released" marker in recent content
        lines = news_content.split("\n")
        if recent_header := next((line for line in lines if line.startswith("## Week")), None):
            check.is_not_in("Released v", recent_header, "Should not have release marker in header")
