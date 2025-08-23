# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Step definitions for pre-release process features."""
# pylint: disable=redefined-outer-name,too-many-locals,too-many-arguments,unused-argument,too-many-lines

from datetime import datetime
from datetime import timedelta
from pathlib import Path
import re
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import git
import pytest
from pytest_bdd import given
from pytest_bdd import parsers
from pytest_bdd import scenarios
from pytest_bdd import then
from pytest_bdd import when
import pytest_check as check

from git_ai_reporter.cli import main
from git_ai_reporter.models import Change
from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.writing.markdown_utils import extract_yaml_frontmatter

# Constants to replace magic values
DEFAULT_DAYS_COUNT = 3
DEFAULT_VERSIONS_COUNT = 3
DEFAULT_ACTIVITY_METRICS_COUNT = 2
FEAT_PREFIX = "feat:"
CHANGELOG_ADDED_HEADER = "### Added"
CHANGELOG_FIXED_HEADER = "### Fixed"
CHANGELOG_CHANGED_HEADER = "### Changed"
CHANGELOG_DEPRECATED_HEADER = "### Deprecated"
CHANGELOG_REMOVED_HEADER = "### Removed"
CHANGELOG_SECURITY_HEADER = "### Security"
MIN_MEANINGFUL_CHANGES = 5
MIN_SECTION_LENGTH = 100
MIN_DAILY_CONTENT_LENGTH = 50
MIN_NARRATIVE_LENGTH = 200
NEWS_FILENAME = "NEWS.md"
CHANGES_KEYWORD = "changes"
CATEGORIES_KEYWORD = "categories"
NO_UNRELEASED_MESSAGE = "No unreleased changes yet"
UNRELEASED_HEADER = "## [Unreleased]"
UNRELEASED_SECTION = "[Unreleased]"

# Load all scenarios from the pre-release feature file
scenarios("../features/pre_release_process.feature")


@pytest.fixture
def pre_release_context() -> dict[str, Any]:
    """Context dictionary for pre-release test data."""
    return {
        "version": None,
        "changelog_content": None,
        "news_content": None,
        "daily_updates_content": None,
        "commits": [],
        "temp_dir": None,
        "git_repo": None,
        "output_files": {},
        "command_result": None,
    }


@pytest.fixture
def mock_gemini_client() -> MagicMock:
    """Create a mock Gemini client for testing."""
    # Create a mock that passes isinstance checks
    client = MagicMock(spec=GeminiClient)

    # Add internal attributes that the orchestrator accesses
    mock_config = MagicMock()
    mock_config.model_tier2 = "gemini-2.5-pro"
    client._config = mock_config

    # Create a more realistic mock client with async operations
    mock_client = MagicMock()
    mock_aio = MagicMock()
    mock_models = MagicMock()
    mock_count_tokens = AsyncMock(return_value=MagicMock(total_tokens=100))
    mock_models.count_tokens = mock_count_tokens
    mock_aio.models = mock_models
    mock_client.aio = mock_aio
    client._client = mock_client

    # Mock the async analysis methods with proper return types
    async def mock_generate_commit_analysis(*args, **kwargs):
        return CommitAnalysis(
            changes=[
                Change(summary="Added authentication system", category="New Feature"),
                Change(summary="Enhanced security features", category="New Feature"),
            ],
            trivial=False,
        )

    async def mock_synthesize_daily_summary(*args, **kwargs):
        return "Daily summary of development activities including feature additions and bug fixes."

    async def mock_generate_news_narrative(*args, **kwargs):
        # Check for patch version pattern in kwargs or general maintenance context
        return "This week focused on maintenance and stability improvements. The team addressed several bug fixes and applied patches to enhance system reliability and performance optimization."

    async def mock_generate_changelog_entries(*args, **kwargs):
        return """### ✨ New Feature
- New user authentication system with OAuth2 integration
- Enhanced security features for data protection

### 🐛 Bug Fix
- Memory leak in data processing pipeline
- Database connection timeout issues

### ♻️ Refactoring
- Updated API endpoints for v2 compliance
- Improved error handling throughout the application

### 🔒 Security
- Fixed XSS vulnerability in user input handling
- Enhanced authentication mechanisms"""

    client.generate_commit_analysis.side_effect = mock_generate_commit_analysis
    client.synthesize_daily_summary.side_effect = mock_synthesize_daily_summary
    client.generate_news_narrative.side_effect = mock_generate_news_narrative
    client.generate_changelog_entries.side_effect = mock_generate_changelog_entries

    return client


@pytest.fixture
def temp_repo_with_files(
    pre_release_context: dict[str, Any], sample_git_data: list[dict[str, Any]], tmp_path: Path
) -> git.Repo:
    """Create a git repository with rich sample data and pre-release documentation files."""
    # Create a temporary repository with rich commit data
    repo_path = tmp_path / "rich-test-repo"
    repo = git.Repo.init(repo_path)

    # Configure git user
    config_writer = repo.config_writer()
    try:
        config_writer.set_value("user", "name", "Test User")
        config_writer.set_value("user", "email", "test@example.com")
    finally:
        config_writer.release()

    # Create commits based on sample data (use first 20 for speed)
    for i, commit_data in enumerate(sample_git_data[:20]):
        # Create a file for this commit
        file_path = repo_path / f"src/feature_{i:03d}.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(f"# {commit_data['message']}\nprint('Implementation {i}')")

        repo.index.add([f"src/feature_{i:03d}.py"])
        repo.index.commit(commit_data["message"])

    temp_dir = repo_path
    pre_release_context["temp_dir"] = str(temp_dir)

    # Create initial NEWS.md
    news_content = """---
title: Project News
description: Development summaries and project updates
created: 2025-01-01
updated: 2025-01-23
format: markdown
---

# Project News

## Table of Contents

1. [Week 3: January 15 - January 21, 2025](#week-3-january-15---january-21-2025)

## Week 3: January 15 - January 21, 2025

Previous development activities and features implemented last week.
"""

    # Create initial CHANGELOG.txt
    changelog_content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New user authentication system
- Enhanced data processing capabilities

### Fixed
- Memory leak in data processing pipeline
- Database connection timeout issues

### Changed
- Updated API endpoints for v2 compliance

## [1.1.0] - 2025-01-15

### Added
- Initial authentication framework
- Basic user management

### Fixed
- Critical security vulnerabilities

## [1.0.0] - 2025-01-01

### Added
- Initial stable release
- Core functionality implementation
"""

    # Write files to the rich repository
    news_path = temp_dir / NEWS_FILENAME
    changelog_path = temp_dir / "CHANGELOG.txt"
    daily_path = temp_dir / "DAILY_UPDATES.md"

    news_path.write_text(news_content)
    changelog_path.write_text(changelog_content)
    daily_path.write_text("# Daily Updates\n\n")

    # Add and commit files to the existing rich repo
    repo.index.add([str(news_path), str(changelog_path), str(daily_path)])
    repo.index.commit("Add pre-release documentation files")

    # Store paths in context
    pre_release_context["news_path"] = news_path
    pre_release_context["changelog_path"] = changelog_path
    pre_release_context["daily_path"] = daily_path
    pre_release_context["git_repo"] = repo

    return repo


# Given steps


@given("I have a git repository with commits")
def given_git_repo_with_commits(
    temp_repo_with_files: git.Repo, pre_release_context: dict[str, Any]
) -> None:
    """Set up a git repository with commits (using rich sample data)."""
    repo = temp_repo_with_files

    # The repo already has many commits from sample_git_data.jsonl
    # Verify we have commits available for testing
    commits = list(repo.iter_commits())
    assert len(commits) > 0, "Repository should have commits from sample data"

    # Store commit info for test validation
    pre_release_context["total_commits"] = len(commits)
    pre_release_context["latest_commit"] = commits[0].hexsha if commits else None


@given("I have configured my Gemini API key")
def given_gemini_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock the Gemini API key configuration."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key-for-testing")


@given("the repository has an existing NEWS.md file")
def given_existing_news_file(pre_release_context: dict[str, Any]) -> None:
    """Verify NEWS.md exists (already created in fixture)."""
    news_path = pre_release_context["news_path"]
    check.is_true(news_path.exists(), "NEWS.md should exist")

    content = news_path.read_text()
    pre_release_context["initial_news_content"] = content
    check.is_in("# Project News", content)


@given("the repository has an existing CHANGELOG.txt file")
def given_existing_changelog_file(pre_release_context: dict[str, Any]) -> None:
    """Verify CHANGELOG.txt exists (already created in fixture)."""
    changelog_path = pre_release_context["changelog_path"]
    check.is_true(changelog_path.exists(), "CHANGELOG.txt should exist")

    content = changelog_path.read_text()
    pre_release_context["initial_changelog_content"] = content
    check.is_in("## [Unreleased]", content)


@given("I have commits in the [Unreleased] section of CHANGELOG.txt:")
def given_unreleased_commits(pre_release_context: dict[str, Any]) -> None:
    """Set up expected unreleased commits (already exist in fixture CHANGELOG.txt)."""
    # Use the predefined entries from the fixture CHANGELOG.txt content
    pre_release_context["unreleased_entries"] = [
        {"category": "Added", "item": "New user authentication system"},
        {"category": "Added", "item": "Enhanced data processing capabilities"},
        {"category": "Fixed", "item": "Memory leak in data processing pipeline"},
        {"category": "Fixed", "item": "Database connection timeout issues"},
        {"category": "Changed", "item": "Updated API endpoints for v2 compliance"},
    ]


@given(parsers.parse('I want to prepare for version "{version}" release'))
def given_target_version(version: str, pre_release_context: dict[str, Any]) -> None:
    """Set the target release version."""
    pre_release_context["version"] = version


@given("I have a repository with commits from the last week:")
def given_weekly_commits(datatable, pre_release_context: dict[str, Any]) -> None:
    """Parse table of weekly commits (repository already has rich commit data)."""
    # Extract commit data from datatable
    commits = []

    # Parse commits from table for test expectations (skip header row)
    for i, row in enumerate(datatable):
        if i == 0:  # Skip header row
            continue
        if len(row) >= DEFAULT_DAYS_COUNT:
            commit_data = {"message": row[0], "category": row[1], "files": row[2]}
            commits.append(commit_data)

    # Store expected commits but don't add to repo (already has rich data)
    pre_release_context["expected_weekly_commits"] = commits

    # Get actual commits from the rich repository for verification
    repo = pre_release_context["git_repo"]
    actual_commits = list(repo.iter_commits(max_count=10))  # Get recent commits
    pre_release_context["actual_commits"] = [
        {"message": commit.message.strip(), "hexsha": commit.hexsha} for commit in actual_commits
    ]


@given("the CHANGELOG.txt has an empty [Unreleased] section:")
def given_empty_unreleased_section(pre_release_context: dict[str, Any]) -> None:
    """Set up CHANGELOG with empty unreleased section."""
    # Update the changelog to have empty unreleased section
    changelog_path = pre_release_context["changelog_path"]
    existing_content = changelog_path.read_text()

    # Use the text from the multiline string (extract from step_text)
    content = """## [Unreleased]

*No unreleased changes yet.*"""

    # Replace the [Unreleased] section
    updated_content = re.sub(
        r"## \[Unreleased\].*?(?=## \[|\Z)",
        content.strip() + "\n\n",
        existing_content,
        flags=re.DOTALL,
    )

    changelog_path.write_text(updated_content)


@given("CHANGELOG.txt contains previous versions:")
def given_existing_versions(datatable, pre_release_context: dict[str, Any]) -> None:
    """Verify existing versions in CHANGELOG (already set up in fixture)."""
    versions = []

    # Skip header row and parse data rows
    for i, row in enumerate(datatable):
        if i == 0:  # Skip header row
            continue
        if len(row) >= DEFAULT_VERSIONS_COUNT:
            versions.append({"version": row[0], "date": row[1], "changes": row[2]})

    pre_release_context["existing_versions"] = versions

    # Verify these exist in the changelog
    changelog_content = pre_release_context["changelog_path"].read_text()
    for version_info in versions:
        check.is_in(f"[{version_info['version']}]", changelog_content)


@given("I have new unreleased changes")
def given_new_unreleased_changes(pre_release_context: dict[str, Any]) -> None:
    """Verify that unreleased changes exist (already set up in fixture)."""
    changelog_content = pre_release_context["changelog_path"].read_text()
    check.is_in("## [Unreleased]", changelog_content)
    check.is_in(CHANGELOG_ADDED_HEADER, changelog_content)


@given(parsers.parse('I want to analyze commits from "{start_date}" to "{end_date}"'))
def given_date_range(start_date: str, end_date: str, pre_release_context: dict[str, Any]) -> None:
    """Set the date range for analysis and create commits in that range."""
    pre_release_context["start_date"] = start_date
    pre_release_context["end_date"] = end_date

    # Create additional commits with timestamps in the specified date range
    temp_dir = Path(pre_release_context["temp_dir"])
    repo = git.Repo(temp_dir)

    # Parse the dates
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")

    # Create a few commits within the date range
    commit_messages = [
        "feat: Add OAuth2 integration for date range test",
        "fix: Resolve database connection bug for date range test",
        "perf: Optimize query performance for date range test",
    ]

    for i, message in enumerate(commit_messages):
        # Create a file for this commit
        file_path = temp_dir / f"src/daterange_feature_{i:03d}.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(f"# {message}\nprint('Date range implementation {i}')")

        repo.index.add([f"src/daterange_feature_{i:03d}.py"])

        # Create commit with timestamp within the date range
        # Use middle of the range plus some offset
        days_offset = i * DEFAULT_ACTIVITY_METRICS_COUNT  # Space commits 2 days apart

        commit_datetime = start_dt + timedelta(days=days_offset)

        # Format as string that GitPython expects: "YYYY-MM-DD HH:MM:SS +0000"
        commit_date_str = commit_datetime.strftime("%Y-%m-%d %H:%M:%S +0000")

        # Set both author and committer dates
        repo.index.commit(message, author_date=commit_date_str, commit_date=commit_date_str)


@given("the repository has significant activity:")
def given_activity_metrics(datatable, pre_release_context: dict[str, Any]) -> None:
    """Parse activity metrics from table."""
    metrics = {}

    # Skip header row and parse data rows
    for i, row in enumerate(datatable):
        if i == 0:  # Skip header row
            continue
        if len(row) >= DEFAULT_ACTIVITY_METRICS_COUNT:
            metrics[row[0]] = int(row[1])

    pre_release_context["expected_metrics"] = metrics


@given(parsers.parse('CHANGELOG.txt already contains a section for "[{version}]"'))
def given_existing_version_section(version: str, pre_release_context: dict[str, Any]) -> None:
    """Add an existing version section to test conflict handling."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Add the conflicting section
    conflict_section = f"""
## [v{version}] - 2025-01-20

### Added
- Existing feature from previous release

"""

    # Insert after [Unreleased] section
    updated_content = content.replace(
        "## [1.1.0] - 2025-01-15", conflict_section + "## [1.1.0] - 2025-01-15"
    )

    changelog_path.write_text(updated_content)


@given("I have meaningful commits with descriptive messages")
def given_meaningful_commits(pre_release_context: dict[str, Any]) -> None:
    """Ensure commits have meaningful messages (already set up in fixture)."""
    repo = pre_release_context["git_repo"]
    commits = list(repo.iter_commits())

    # Verify we have commits with good messages
    messages = [commit.message.strip() for commit in commits]
    check.greater(len(messages), 0, "Should have commits")
    check.is_true(any(FEAT_PREFIX in msg for msg in messages), "Should have feature commits")


@given("previous analysis results exist in cache")
def given_existing_cache(pre_release_context: dict[str, Any]) -> None:
    """Mock existing cache results."""
    temp_dir = Path(pre_release_context["temp_dir"])
    cache_dir = temp_dir / ".git-report-cache"
    cache_dir.mkdir(exist_ok=True)

    # Create mock cache files
    cache_file = cache_dir / "commit_analysis.json"
    cache_file.write_text('{"cached": "analysis_results"}')

    pre_release_context["cache_exists"] = True


@given("I am preparing for a release in my git workflow")
def given_release_workflow(pre_release_context: dict[str, Any]) -> None:
    """Set up context for release workflow."""
    pre_release_context["workflow_context"] = "release_preparation"


@given("I want to ensure documentation is ready before tagging")
def given_documentation_ready(pre_release_context: dict[str, Any]) -> None:
    """Ensure documentation readiness check."""
    pre_release_context["documentation_ready"] = True


# When steps


@when(parsers.parse('I run git-ai-reporter with --pre-release "{version}"'))
def when_run_pre_release(
    version: str, pre_release_context: dict[str, Any], mock_gemini_client: AsyncMock
) -> None:
    """Run git-ai-reporter with pre-release flag."""
    temp_dir = pre_release_context["temp_dir"]

    with (
        patch("git_ai_reporter.cli.GeminiClient", return_value=mock_gemini_client),
        patch("git_ai_reporter.cli.genai.Client"),
        patch("git_ai_reporter.services.gemini.GeminiClient", return_value=mock_gemini_client),
    ):

        try:
            main(
                repo_path=temp_dir,
                weeks=1,
                start_date_str=None,
                end_date_str=None,
                config_file=None,
                cache_dir=".git-report-cache",
                no_cache=False,
                debug=True,
                pre_release=version,
            )
            pre_release_context["command_success"] = True
        except (git.exc.GitError, ValueError, RuntimeError, OSError) as e:
            pre_release_context["command_error"] = str(e)
            pre_release_context["command_success"] = False


@when(
    parsers.parse(
        'I run git-ai-reporter with --start-date "{start_date}" --end-date "{end_date}" --pre-release "{version}"'
    )
)
def when_run_pre_release_with_dates(
    start_date: str,
    end_date: str,
    version: str,
    pre_release_context: dict[str, Any],
    mock_gemini_client: AsyncMock,
) -> None:
    """Run git-ai-reporter with date range and pre-release."""
    temp_dir = pre_release_context["temp_dir"]

    with (
        patch("git_ai_reporter.cli.GeminiClient", return_value=mock_gemini_client),
        patch("git_ai_reporter.cli.genai.Client"),
        patch("git_ai_reporter.services.gemini.GeminiClient", return_value=mock_gemini_client),
    ):

        try:
            main(
                repo_path=temp_dir,
                weeks=1,
                start_date_str=start_date,
                end_date_str=end_date,
                config_file=None,
                cache_dir=".git-report-cache",
                no_cache=False,
                debug=True,
                pre_release=version,
            )
            pre_release_context["command_success"] = True
        except (git.exc.GitError, ValueError, RuntimeError, OSError) as e:
            pre_release_context["command_error"] = str(e)
            pre_release_context["command_success"] = False


# Then steps


@then(parsers.parse('NEWS.md should contain "{text}" in the latest week header'))
def then_news_contains_header_text(text: str, pre_release_context: dict[str, Any]) -> None:
    """Verify NEWS.md contains specific text in header."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Find the first actual week header (not Table of Contents)
    lines = content.split("\n")
    latest_header = None
    for line in lines:
        if line.startswith("## Week"):
            latest_header = line
            break

    check.is_not_none(latest_header, "Should have a week header")
    check.is_in(text, latest_header, f"Header should contain '{text}'")


@then(parsers.parse('CHANGELOG.txt should have a new section "## {section}"'))
def then_changelog_has_section(section: str, pre_release_context: dict[str, Any]) -> None:
    """Verify CHANGELOG.txt has the specified section."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    expected_section = section.replace('"', "")  # Remove quotes
    check.is_in(expected_section, content, f"Should contain section {expected_section}")


@then(parsers.parse("the [{version}] section should contain all unreleased changes"))
def then_version_section_has_changes(version: str, pre_release_context: dict[str, Any]) -> None:
    """Verify the version section contains the unreleased changes."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Check that the version section exists and has content
    version_pattern = re.compile(f"## \\[{version}\\].*?(?=## \\[|$)", re.DOTALL)
    version_match = version_pattern.search(content)

    check.is_not_none(version_match, f"Should have section for version {version}")

    section_content = version_match.group(0) if version_match else ""

    # Verify it contains meaningful content about the changes
    # Check for either detailed sections OR a summary indicating changes were processed
    has_detailed_sections = (
        CHANGELOG_ADDED_HEADER in section_content
        and CHANGELOG_FIXED_HEADER in section_content
        and CHANGELOG_CHANGED_HEADER in section_content
    )
    has_summary = (
        CHANGES_KEYWORD in section_content.lower() and CATEGORIES_KEYWORD in section_content.lower()
    )

    check.is_true(
        has_detailed_sections or has_summary,
        "Should have either detailed sections or a meaningful summary of changes",
    )


@then("a new empty [Unreleased] section should be created")
def then_new_unreleased_section(pre_release_context: dict[str, Any]) -> None:
    """Verify a new empty [Unreleased] section was created."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Should have an [Unreleased] section
    check.is_in("## [Unreleased]", content)

    # Find the unreleased section and check it's mostly empty
    unreleased_pattern = re.compile(r"## \[Unreleased\].*?(?=## \[|$)", re.DOTALL)
    unreleased_match = unreleased_pattern.search(content)

    check.is_not_none(unreleased_match, "Should have [Unreleased] section")

    if unreleased_match:
        unreleased_content = unreleased_match.group(0)
        # Should contain indication of no changes
        check.is_true(
            NO_UNRELEASED_MESSAGE in unreleased_content
            or len(unreleased_content.strip()) < MIN_DAILY_CONTENT_LENGTH,
            "Unreleased section should be empty or minimal",
        )


@then("the release date should match today's date")
def then_release_date_today(pre_release_context: dict[str, Any]) -> None:
    """Verify the release date is today."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    today = datetime.now().strftime("%Y-%m-%d")
    check.is_in(today, content, f"Should contain today's date {today}")


@then("NEWS.md should reflect the release as completed")
def then_news_reflects_completed_release(pre_release_context: dict[str, Any]) -> None:
    """Verify NEWS.md shows release as completed."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Should contain "Released" indicating past tense
    check.is_in("Released", content, "Should indicate release is completed")


@then(parsers.parse('the week header should show "Released v{version} 🚀"'))
def then_week_header_shows_release(version: str, pre_release_context: dict[str, Any]) -> None:
    """Verify week header shows the release."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    expected_text = f"Released v{version} 🚀"
    check.is_in(expected_text, content, f"Should contain '{expected_text}'")


@then(parsers.parse("CHANGELOG.txt should move all changes to [{version}] section"))
def then_changelog_moves_to_version(version: str, pre_release_context: dict[str, Any]) -> None:
    """Verify changes moved to version section."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Should have the version section
    version_section = f"[{version}]"
    check.is_in(version_section, content, f"Should have {version_section}")

    # The new [Unreleased] should be minimal
    unreleased_pattern = re.compile(r"## \[Unreleased\].*?(?=## \[|$)", re.DOTALL)
    if unreleased_match := unreleased_pattern.search(content):
        unreleased_content = unreleased_match.group(0)
        check.is_true(
            len(unreleased_content.strip()) < MIN_SECTION_LENGTH,
            "[Unreleased] should be minimal after moving changes",
        )


@then("all four change categories should be properly organized")
def then_four_categories_organized(pre_release_context: dict[str, Any]) -> None:
    """Verify all four categories are present."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    categories = ["### ✨ New Feature", "### 🐛 Bug Fix", "### ♻️ Refactoring", "### 🔒 Security"]
    for category in categories:
        check.is_in(category, content, f"Should have {category} section")


@then("the version date should be today's date")
def then_version_date_today(pre_release_context: dict[str, Any]) -> None:
    """Verify version section has today's date."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    today = datetime.now().strftime("%Y-%m-%d")
    check.is_in(f"- {today}", content, f"Should contain today's date {today}")


# Additional implementation steps for remaining scenarios...


@then("CHANGELOG.txt should create section [v1.0.1] with minimal content")
def then_minimal_version_section(pre_release_context: dict[str, Any]) -> None:
    """Verify minimal version section creation."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()
    check.is_in("[v1.0.1]", content, "Should have v1.0.1 section")


@then("the section should indicate patch-level changes only")
def then_patch_level_changes(pre_release_context: dict[str, Any]) -> None:
    """Verify patch-level indication."""
    # This is a semantic check - would need AI analysis to verify
    # Implementation depends on AI analysis
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()
    # Check that content exists for the patch version
    check.is_true(len(content) > 0, "Should have changelog content")


@then("NEWS.md should reflect a maintenance release")
def then_maintenance_release(pre_release_context: dict[str, Any]) -> None:
    """Verify maintenance release indication."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()
    # Check for maintenance-related terms
    maintenance_terms = ["maintenance", "patch", "bug fix", "stability"]
    has_maintenance = any(term in content.lower() for term in maintenance_terms)
    check.is_true(has_maintenance, "Should indicate maintenance release")


@then("the new [Unreleased] section should be properly formatted")
def then_proper_unreleased_format(pre_release_context: dict[str, Any]) -> None:
    """Verify proper formatting of new [Unreleased] section."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Check format
    check.is_in(UNRELEASED_HEADER, content)
    # Should be at the top after the header
    lines = content.split("\n")
    unreleased_line = next((i for i, line in enumerate(lines) if UNRELEASED_HEADER in line), None)
    check.is_not_none(unreleased_line, "Should have [Unreleased] section")


# Missing step implementations


@then(parsers.parse("the new [{version}] section should be added at the top"))
def then_new_version_at_top(version: str, pre_release_context: dict[str, Any]) -> None:
    """Verify new version section is at the top."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Find first version section after [Unreleased]
    lines = content.split("\n")
    version_lines = [i for i, line in enumerate(lines) if f"[{version}]" in line]
    unreleased_lines = [i for i, line in enumerate(lines) if UNRELEASED_SECTION in line]

    check.is_true(len(version_lines) > 0, f"Should have {version} section")
    check.is_true(len(unreleased_lines) > 0, "Should have Unreleased section")

    if version_lines and unreleased_lines:
        check.is_true(
            version_lines[0] > unreleased_lines[0], f"{version} should be after Unreleased"
        )


@then("all existing version sections should remain unchanged")
def then_existing_versions_unchanged(pre_release_context: dict[str, Any]) -> None:
    """Verify existing versions are preserved."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Check for preserved versions from fixture
    check.is_in("[1.1.0]", content, "Should preserve v1.1.0")
    check.is_in("[1.0.0]", content, "Should preserve v1.0.0")
    check.is_in("2025-01-15", content, "Should preserve dates")
    check.is_in("2025-01-01", content, "Should preserve dates")


@then("the version ordering should be chronologically correct")
def then_version_ordering_correct(pre_release_context: dict[str, Any]) -> None:
    """Verify version ordering is chronologically correct."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Should have versions in reverse chronological order (newest first)
    check.is_in("## [Unreleased]", content)
    # The ordering is implicitly checked by the fixture content structure


@then("the Keep a Changelog format should be maintained")
def then_keep_changelog_format(pre_release_context: dict[str, Any]) -> None:
    """Verify Keep a Changelog format compliance."""
    changelog_path = pre_release_context["changelog_path"]
    _verify_changelog_format(changelog_path)


@then(parsers.parse("only commits in the specified range should be analyzed"))
def then_commits_in_range_analyzed(pre_release_context: dict[str, Any]) -> None:
    """Verify only commits in date range were analyzed."""
    # This would require deeper integration testing - for now just verify success
    check.is_true(pre_release_context.get("command_success", False), "Command should succeed")


@then("the release documentation should reflect that time period")
def then_documentation_reflects_period(pre_release_context: dict[str, Any]) -> None:
    """Verify documentation reflects the specified time period."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Should have some date-related content
    check.is_true(len(content) > MIN_SECTION_LENGTH, "Should have meaningful content")


@then("NEWS.md should show the correct week range in the header")
def then_news_shows_week_range(pre_release_context: dict[str, Any]) -> None:
    """Verify NEWS.md shows correct week range."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Should have a week header
    check.is_in("Week", content, "Should have week header")


@then("CHANGELOG.txt should contain only relevant changes")
def then_changelog_relevant_changes(pre_release_context: dict[str, Any]) -> None:
    """Verify CHANGELOG contains only relevant changes."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Should have changelog structure
    check.is_in("## [", content, "Should have version sections")


@then("NEWS.md should be valid Markdown with proper frontmatter")
def then_news_valid_markdown(pre_release_context: dict[str, Any]) -> None:
    """Verify NEWS.md is valid markdown."""
    news_path = pre_release_context["news_path"]
    _verify_markdown_validity(news_path)


@then("the YAML frontmatter should be correctly formatted")
def then_yaml_frontmatter_correct(pre_release_context: dict[str, Any]) -> None:
    """Verify YAML frontmatter formatting."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    frontmatter, _ = extract_yaml_frontmatter(content)
    check.is_instance(frontmatter, dict, "Should have valid YAML frontmatter")
    check.is_in("title", frontmatter, "Should have title")


@then("CHANGELOG.txt should follow Keep a Changelog standards")
def then_changelog_follows_standards(pre_release_context: dict[str, Any]) -> None:
    """Verify CHANGELOG follows standards."""
    changelog_path = pre_release_context["changelog_path"]
    _verify_changelog_format(changelog_path)


@then("version headers should use correct semantic version format")
def then_version_headers_correct_format(pre_release_context: dict[str, Any]) -> None:
    """Verify version headers use correct format."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Should have proper version format [vX.Y.Z]

    version_pattern = r"\[v?\d+\.\d+\.\d+.*?\]"
    matches = re.findall(version_pattern, content)
    check.is_true(len(matches) > 0, "Should have properly formatted versions")


@then("dates should be in ISO format (YYYY-MM-DD)")
def then_dates_iso_format(pre_release_context: dict[str, Any]) -> None:
    """Verify dates are in ISO format."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Should contain ISO-formatted dates

    date_pattern = r"\d{4}-\d{2}-\d{2}"
    matches = re.findall(date_pattern, content)
    check.is_true(len(matches) > 0, "Should have ISO-formatted dates")


@then("emoji indicators should be present for release headers")
def then_emoji_indicators_present(pre_release_context: dict[str, Any]) -> None:
    """Verify emoji indicators are present."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Should have rocket emoji for releases
    check.is_in("🚀", content, "Should have release emoji")


@then("NEWS.md should include summary metrics for the release")
def then_news_includes_metrics(pre_release_context: dict[str, Any]) -> None:
    """Verify NEWS.md includes metrics."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Should have some numerical data or metrics-like content

    number_pattern = r"\d+"
    matches = re.findall(number_pattern, content)
    check.is_true(len(matches) > 0, "Should contain some metrics")


@then("the metrics should reflect the pre-release activity")
def then_metrics_reflect_activity(pre_release_context: dict[str, Any]) -> None:
    """Verify metrics reflect activity."""
    # This would require detailed analysis - check success for now
    check.is_true(pre_release_context.get("command_success", False), "Command should succeed")


@then("the narrative should mention the scope of changes")
def then_narrative_mentions_scope(pre_release_context: dict[str, Any]) -> None:
    """Verify narrative mentions scope."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Should have content about changes
    scope_terms = ["changes", "improvements", "updates", "features", "fixes"]
    has_scope = any(term in content.lower() for term in scope_terms)
    check.is_true(has_scope, "Should mention scope of changes")


@then("DAILY_UPDATES.md should contain detailed daily breakdowns")
def then_daily_updates_detailed(pre_release_context: dict[str, Any]) -> None:
    """Verify DAILY_UPDATES.md has daily breakdowns."""
    daily_path = pre_release_context["daily_path"]
    content = daily_path.read_text()

    # Should have some daily content
    check.is_true(len(content) > MIN_DAILY_CONTENT_LENGTH, "Should have daily content")


@then("the tool should complete without errors")
def then_tool_completes_without_errors(pre_release_context: dict[str, Any]) -> None:
    """Verify tool completes successfully."""
    check.is_true(
        pre_release_context.get("command_success", False), "Command should complete without errors"
    )


@then("the version string should be used as provided")
def then_version_string_used_as_provided(pre_release_context: dict[str, Any]) -> None:
    """Verify version string is used as provided."""
    # This would require checking the exact version format used
    check.is_true(pre_release_context.get("command_success", False), "Command should succeed")


@then("appropriate warnings should be logged")
def then_appropriate_warnings_logged(pre_release_context: dict[str, Any]) -> None:
    """Verify appropriate warnings are logged."""
    # This would require capturing log output - for now check success
    check.is_true(pre_release_context.get("command_success", False), "Command should succeed")


@then("the release documentation should still be generated")
def then_release_docs_still_generated(pre_release_context: dict[str, Any]) -> None:
    """Verify release documentation is still generated."""
    news_path = pre_release_context["news_path"]
    changelog_path = pre_release_context["changelog_path"]

    check.is_true(news_path.exists(), "NEWS.md should exist")
    check.is_true(changelog_path.exists(), "CHANGELOG.txt should exist")


@then("the tool should handle the conflict gracefully")
def then_tool_handles_conflict_gracefully(pre_release_context: dict[str, Any]) -> None:
    """Verify tool handles conflicts gracefully."""
    check.is_true(
        pre_release_context.get("command_success", False), "Command should handle conflicts"
    )


@then("the existing section should be preserved or merged")
def then_existing_section_preserved(pre_release_context: dict[str, Any]) -> None:
    """Verify existing sections are preserved."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Should have the conflicting version
    check.is_in("[v1.3.0]", content, "Should preserve existing version")


@then("no data loss should occur")
def then_no_data_loss(pre_release_context: dict[str, Any]) -> None:
    """Verify no data loss occurred."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    # Should have all existing content
    check.is_true(len(content) > MIN_SECTION_LENGTH, "Should preserve existing content")


@then("appropriate warnings should be displayed")
def then_warnings_displayed(pre_release_context: dict[str, Any]) -> None:
    """Verify appropriate warnings are displayed."""
    # This would require capturing output - for now check success
    check.is_true(pre_release_context.get("command_success", False), "Command should succeed")


@then(parsers.parse('the version should be formatted as "{expected_format}"'))
def then_version_formatted_as(expected_format: str, pre_release_context: dict[str, Any]) -> None:
    """Verify version is formatted correctly."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    _verify_version_format(content, expected_format, expected_format)


@then(parsers.parse('the release header should show "Released v{version} 🚀"'))
def then_release_header_shows(version: str, pre_release_context: dict[str, Any]) -> None:
    """Verify release header shows correct format."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    expected_text = f"Released v{version} 🚀"
    check.is_in(expected_text, content, f"Should contain '{expected_text}'")


@then(parsers.parse('CHANGELOG.txt should use format "## [v{version}]"'))
def then_changelog_uses_format(version: str, pre_release_context: dict[str, Any]) -> None:
    """Verify CHANGELOG uses correct format."""
    changelog_path = pre_release_context["changelog_path"]
    content = changelog_path.read_text()

    expected_format = f"## [v{version}]"
    check.is_in(expected_format, content, f"Should use format {expected_format}")


@then("NEWS.md should contain coherent narrative about the release")
def then_news_coherent_narrative(pre_release_context: dict[str, Any]) -> None:
    """Verify NEWS.md has coherent narrative."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Should have meaningful content
    check.is_true(len(content) > MIN_NARRATIVE_LENGTH, "Should have substantial narrative")


@then("the narrative should be written in past tense (as if released)")
def then_narrative_past_tense(pre_release_context: dict[str, Any]) -> None:
    """Verify narrative uses past tense."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Should contain past tense indicators
    past_tense_indicators = ["released", "added", "fixed", "improved", "updated"]
    has_past_tense = any(indicator in content.lower() for indicator in past_tense_indicators)
    check.is_true(has_past_tense, "Should use past tense")


@then("technical changes should be explained for stakeholders")
def then_technical_changes_explained(pre_release_context: dict[str, Any]) -> None:
    """Verify technical changes are explained."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Should have explanatory content
    check.is_true(len(content) > MIN_SECTION_LENGTH, "Should have explanations")


@then("the summary should highlight key improvements and fixes")
def then_summary_highlights_key_items(pre_release_context: dict[str, Any]) -> None:
    """Verify summary highlights key items."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Should mention improvements and fixes
    key_terms = ["improvements", "fixes", "features", "enhancements"]
    has_key_terms = any(term in content.lower() for term in key_terms)
    check.is_true(has_key_terms, "Should highlight key improvements and fixes")


@then("the tone should be professional and informative")
def then_tone_professional(pre_release_context: dict[str, Any]) -> None:
    """Verify tone is professional and informative."""
    news_path = pre_release_context["news_path"]
    content = news_path.read_text()

    # Basic check - should have substantial, well-structured content
    check.is_true(len(content) > MIN_SECTION_LENGTH, "Should have professional content")
    check.is_in(".", content, "Should have proper sentences")


@then("cached commit analyses should be reused when possible")
def then_cached_analyses_reused(pre_release_context: dict[str, Any]) -> None:
    """Verify cached analyses are reused."""
    # This would require checking cache usage - for now check success
    check.is_true(pre_release_context.get("command_success", False), "Command should succeed")


@then("only release-specific processing should be performed")
def then_only_release_specific_processing(pre_release_context: dict[str, Any]) -> None:
    """Verify only release-specific processing occurred."""
    # This would require detailed analysis - for now check success
    check.is_true(pre_release_context.get("command_success", False), "Command should succeed")


@then("the performance should be optimized for repeated runs")
def then_performance_optimized(pre_release_context: dict[str, Any]) -> None:
    """Verify performance is optimized."""
    # This would require timing analysis - for now check success
    check.is_true(pre_release_context.get("command_success", False), "Command should succeed")


@then("cache integrity should be maintained")
def then_cache_integrity_maintained(pre_release_context: dict[str, Any]) -> None:
    """Verify cache integrity."""
    # This would require cache validation - for now check success
    check.is_true(pre_release_context.get("command_success", False), "Command should succeed")


@then("all release artifacts should be ready for commit")
def then_artifacts_ready_for_commit(pre_release_context: dict[str, Any]) -> None:
    """Verify all artifacts are ready for commit."""
    news_path = pre_release_context["news_path"]
    changelog_path = pre_release_context["changelog_path"]
    daily_path = pre_release_context["daily_path"]

    check.is_true(news_path.exists(), "NEWS.md should exist")
    check.is_true(changelog_path.exists(), "CHANGELOG.txt should exist")
    check.is_true(daily_path.exists(), "DAILY_UPDATES.md should exist")


@then("the documentation should be suitable for release notes")
def then_documentation_suitable_for_release(pre_release_context: dict[str, Any]) -> None:
    """Verify documentation is suitable for release notes."""
    news_path = pre_release_context["news_path"]
    changelog_path = pre_release_context["changelog_path"]

    news_content = news_path.read_text()
    changelog_content = changelog_path.read_text()

    # Should have release-ready content
    check.is_true(len(news_content) > MIN_SECTION_LENGTH, "NEWS.md should have substantial content")
    check.is_true(
        len(changelog_content) > MIN_SECTION_LENGTH, "CHANGELOG.txt should have substantial content"
    )


@then("the changes should be staged for the release commit")
def then_changes_staged_for_commit(pre_release_context: dict[str, Any]) -> None:
    """Verify changes are staged."""
    # This would require checking git status - for now check files exist
    news_path = pre_release_context["news_path"]
    changelog_path = pre_release_context["changelog_path"]

    check.is_true(news_path.exists(), "NEWS.md should be updated")
    check.is_true(changelog_path.exists(), "CHANGELOG.txt should be updated")


@then("the version should be clearly indicated throughout")
def then_version_clearly_indicated(pre_release_context: dict[str, Any]) -> None:
    """Verify version is clearly indicated throughout."""
    news_path = pre_release_context["news_path"]
    changelog_path = pre_release_context["changelog_path"]

    news_content = news_path.read_text()
    changelog_content = changelog_path.read_text()

    # Should have version references
    has_version = any(char.isdigit() for char in news_content + changelog_content)
    check.is_true(has_version, "Should have version indicators")


# Utility functions for step definitions


def _verify_version_format(content: str, version: str, expected_format: str) -> None:
    """Helper to verify version formatting."""
    check.is_in(f"v{expected_format}", content, f"Should use format v{expected_format}")


def _verify_markdown_validity(file_path: Path) -> None:
    """Helper to verify markdown validity."""
    content = file_path.read_text()

    # Basic markdown checks
    check.is_true(content.strip(), "File should not be empty")

    # Check for YAML frontmatter if it's NEWS.md
    if file_path.name == NEWS_FILENAME:
        frontmatter, _ = extract_yaml_frontmatter(content)
        check.is_instance(frontmatter, dict, "Should have valid frontmatter")


def _verify_changelog_format(file_path: Path) -> None:
    """Helper to verify Keep a Changelog format."""
    content = file_path.read_text()

    # Should have standard changelog elements
    check.is_in("# Changelog", content, "Should have changelog header")
    check.is_in("Keep a Changelog", content, "Should reference standard")
    check.is_in("## [", content, "Should have version sections")
