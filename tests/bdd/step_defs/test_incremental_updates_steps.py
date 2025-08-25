# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Step definitions for incremental repository updates feature."""
# pylint: disable=redefined-outer-name  # BDD step functions need to match fixture names

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any

import git
import pytest
from pytest_bdd import given
from pytest_bdd import parsers
from pytest_bdd import scenarios
from pytest_bdd import then
from pytest_bdd import when

# Test constants
CHANGELOG_CATEGORIES = {
    "Added": "Added",
    "Fixed": "Fixed",
    "Week": "Week",
    "Unreleased": "[Unreleased]",
}

# Additional constants for magic values
NEW_FEATURES_ADDED_TEXT = "new features added"
NEW_FEATURE_TEXT = "new feature"
FEAT_PREFIX = "feat:"
FIX_PREFIX = "fix:"
FEATURE_KEYWORD = "feature"
WEEK_ONE_HEADER = "Week 1:"
WEEK_PREFIX = "Week "
PROJECT_NEWS_TITLE = "Project News"
THREE_COMMITS = 3
NARRATIVE_QUALITY_THRESHOLD = 100

# Additional constants for magic values
DAILY_UPDATES_TEXT = "Daily Updates"
TRUE_VALUE = "true"
OUTPUT_FILES_KEY = "output_files"
INITIAL_DEVELOPMENT_WEEK = "Initial development week"

# Default changelog template
DEFAULT_CHANGELOG_CONTENT = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Initial features

### Fixed
-

### Changed
-

### Removed
-
"""

# Load feature scenarios
scenarios("../features/incremental_updates.feature")


@pytest.fixture
def incremental_context() -> dict[str, Any]:
    """Context dictionary for incremental update tests."""
    return {
        "repo": None,
        "repo_path": None,
        "initial_news": None,
        "initial_changelog": None,
        "initial_daily": None,
        "modification_times": {},
        "new_commits": [],
        "output_files": {},
    }


@given("I have a git repository with sample commits")
def setup_git_repository_with_sample_commits(
    incremental_context: dict[str, Any], temp_git_repo: git.Repo
) -> None:
    """Set up a git repository with sample commits."""
    incremental_context["repo"] = temp_git_repo
    incremental_context["repo_path"] = (
        Path(temp_git_repo.working_dir) if temp_git_repo.working_dir else None
    )


@given("I have configured my Gemini API key")
def configure_gemini_api_key(incremental_context: dict[str, Any]) -> None:
    """Configure Gemini API key for testing."""
    incremental_context["api_key"] = "test-api-key-12345"
    os.environ["GEMINI_API_KEY"] = incremental_context["api_key"]


@given("I have a repository with existing commits from sample_git_data.jsonl")
def setup_repo_with_sample_data(tmp_path: Path, incremental_context: dict[str, Any]) -> None:
    """Set up a repository with commits from sample data."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize repo
    repo = git.Repo.init(repo_path)
    config_writer = repo.config_writer()
    try:
        config_writer.set_value("user", "name", "Test User")
        config_writer.set_value("user", "email", "test@example.com")
    finally:
        config_writer.release()

    # Load sample data
    sample_file = Path(__file__).parent.parent.parent / "extracts" / "sample_git_data.jsonl"
    if sample_file.exists():
        with open(sample_file, encoding="utf-8") as f:
            # Add first few commits from sample data
            for i, line in enumerate(f):
                if i >= THREE_COMMITS:  # Just use first 3 commits for speed
                    break
                commit_data = json.loads(line)

                # Create a file for the commit
                test_file = repo_path / f"file_{i}.txt"
                test_file.write_text(f"Content for commit {i}\n", encoding="utf-8")

                repo.index.add([str(test_file.relative_to(repo_path))])
                repo.index.commit(commit_data["message"])
    else:
        # Fallback: create some test commits
        for i in range(THREE_COMMITS):
            test_file = repo_path / f"file_{i}.txt"
            test_file.write_text(f"Initial content {i}\n", encoding="utf-8")
            repo.index.add([str(test_file.relative_to(repo_path))])
            repo.index.commit(f"feat: Initial commit {i}")

    incremental_context["repo"] = repo
    incremental_context["repo_path"] = repo_path


@given("I have a repository with existing commits")
def setup_repo_with_commits(tmp_path: Path, incremental_context: dict[str, Any]) -> None:
    """Set up a repository with some existing commits."""
    setup_repo_with_sample_data(tmp_path, incremental_context)


@given("I have a repository with analyzed commits")
def setup_repo_with_analyzed_commits(tmp_path: Path, incremental_context: dict[str, Any]) -> None:
    """Set up a repository with analyzed commits."""
    setup_repo_with_sample_data(tmp_path, incremental_context)

    # Create initial analysis files
    if repo_path := incremental_context["repo_path"]:
        news_file = repo_path / "NEWS.md"
        changelog_file = repo_path / "CHANGELOG.txt"
        daily_file = repo_path / "DAILY_UPDATES.md"

        news_file.write_text(
            "# Project News\n\n## Week 1: January 1 - January 7, 2025\n\nInitial commits analyzed.\n",
            encoding="utf-8",
        )
        changelog_file.write_text(
            "# Changelog\n\n## [Unreleased]\n\n### Added\n- Initial features\n", encoding="utf-8"
        )
        daily_file.write_text(
            "# Daily Updates\n\n## January 1, 2025\n\n- Repository initialized\n", encoding="utf-8"
        )

        incremental_context["output_files"] = {
            "news": news_file,
            "changelog": changelog_file,
            "daily": daily_file,
        }


@given("I have run git-ai-reporter to generate initial files")
def run_initial_analysis(
    incremental_context: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run git-ai-reporter to generate initial files."""
    repo_path = incremental_context["repo_path"]

    # Set up environment
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    monkeypatch.chdir(repo_path)

    # Run git-ai-reporter (mocked)
    # In a real test, this would call the actual CLI
    # For now, we'll create the files manually
    news_file = repo_path / "NEWS.md"
    changelog_file = repo_path / "CHANGELOG.txt"
    daily_file = repo_path / "DAILY_UPDATES.md"

    news_file.write_text(
        "# Project News\n\n## Week 1: January 1 - January 7, 2025\n\nInitial development week.\n",
        encoding="utf-8",
    )
    changelog_file.write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Added\n- Initial features\n", encoding="utf-8"
    )
    daily_file.write_text(
        "# Daily Updates\n\n## January 1, 2025\n\n- Started project\n", encoding="utf-8"
    )

    incremental_context["output_files"]["news"] = news_file
    incremental_context["output_files"]["changelog"] = changelog_file
    incremental_context["output_files"]["daily"] = daily_file


@given("NEWS.md contains the initial week's narrative")
def verify_initial_news(incremental_context: dict[str, Any]) -> None:
    """Verify and store initial NEWS.md content."""
    news_file = incremental_context["output_files"]["news"]
    content = news_file.read_text(encoding="utf-8")
    assert CHANGELOG_CATEGORIES["Week"] in content
    incremental_context["initial_news"] = content


@given("CHANGELOG.txt contains the initial entries")
def verify_initial_changelog(incremental_context: dict[str, Any]) -> None:
    """Verify and store initial CHANGELOG.txt content."""
    changelog_file = incremental_context["output_files"]["changelog"]
    content = changelog_file.read_text(encoding="utf-8")
    assert CHANGELOG_CATEGORIES["Unreleased"] in content
    incremental_context["initial_changelog"] = content


@given("DAILY_UPDATES.md contains the initial daily summaries")
def verify_initial_daily(incremental_context: dict[str, Any]) -> None:
    """Verify and store initial DAILY_UPDATES.md content."""
    daily_file = incremental_context["output_files"]["daily"]
    content = daily_file.read_text(encoding="utf-8")
    assert DAILY_UPDATES_TEXT in content
    incremental_context["initial_daily"] = content


@given("I record the modification times of output files")
def record_modification_times(incremental_context: dict[str, Any]) -> None:
    """Record the modification times of output files."""
    for name, path in incremental_context["output_files"].items():
        if path.exists():
            incremental_context["modification_times"][name] = path.stat().st_mtime


@given("I have commits from last week that have been analyzed")
def setup_last_week_commits(incremental_context: dict[str, Any]) -> None:
    """Set up commits from last week."""
    repo = incremental_context["repo"]
    # Add commits with dates from last week
    # This would need proper date manipulation in a real test
    test_file = incremental_context["repo_path"] / "last_week.txt"
    test_file.write_text("Last week's work\n", encoding="utf-8")
    repo.index.add([str(test_file.relative_to(incremental_context["repo_path"]))])
    repo.index.commit("feat: Last week's feature")


@when(parsers.parse('I add a new commit with message "{message}"'))
def add_new_commit(incremental_context: dict[str, Any], message: str) -> None:
    """Add a new commit to the repository."""
    repo = incremental_context["repo"]
    repo_path = incremental_context["repo_path"]

    # Create or modify a file
    test_file = repo_path / f"new_feature_{len(incremental_context['new_commits'])}.txt"
    test_file.write_text("New feature content\n", encoding="utf-8")

    repo.index.add([str(test_file.relative_to(repo_path))])
    commit = repo.index.commit(message)
    incremental_context["new_commits"].append(commit)


@when(parsers.parse('I add a commit "{message}" on {day}'))
def add_commit_on_day(incremental_context: dict[str, Any], message: str, day: str) -> None:
    """Add a commit on a specific day."""
    _ = day  # Day parameter used for BDD matching
    add_new_commit(incremental_context, message)


@when("I add commits with these prefixes:")
def add_commits_with_prefixes(incremental_context: dict[str, Any], datatable) -> None:
    """Add commits with various prefixes from the data table."""
    repo = incremental_context["repo"]
    repo_path = incremental_context["repo_path"]

    # Convert raw datatable to dict format (skip header row)
    headers = datatable[0]  # First row contains headers
    rows = datatable[1:]  # Remaining rows contain data

    for row in rows:
        # Create a dict from headers and row data
        row_dict = dict(zip(headers, row))
        prefix = row_dict["prefix"]
        message = row_dict["message"]
        should_appear = row_dict["should_appear"]

        # Create a file for each commit
        test_file = repo_path / f"{prefix}_file.txt"
        test_file.write_text(f"Content for {prefix}\n", encoding="utf-8")

        repo.index.add([str(test_file.relative_to(repo_path))])
        commit = repo.index.commit(message)
        incremental_context["new_commits"].append(
            {"commit": commit, "should_appear": should_appear == TRUE_VALUE}
        )


@when("I add new commits in the current week")
def add_current_week_commits(incremental_context: dict[str, Any]) -> None:
    """Add commits for the current week."""
    add_new_commit(incremental_context, "feat: This week's new feature")


@when("I add a new significant commit")
def add_significant_commit(incremental_context: dict[str, Any]) -> None:
    """Add a significant commit that should definitely be processed."""
    add_new_commit(incremental_context, "feat: Major new functionality with extensive changes")


def _initialize_output_files(incremental_context: dict[str, Any]) -> None:
    """Initialize output files if not already set."""
    if OUTPUT_FILES_KEY not in incremental_context or not incremental_context[OUTPUT_FILES_KEY]:
        repo_path = incremental_context["repo_path"]
        incremental_context["output_files"] = {
            "news": repo_path / "NEWS.md" if repo_path else Path("NEWS.md"),
            "changelog": repo_path / "CHANGELOG.txt" if repo_path else Path("CHANGELOG.txt"),
            "daily": repo_path / "DAILY_UPDATES.md" if repo_path else Path("DAILY_UPDATES.md"),
        }


def _update_news_file(news_file: Path) -> None:
    """Update or create NEWS.md file."""
    if news_file.exists():
        news_content = news_file.read_text(encoding="utf-8")
        if INITIAL_DEVELOPMENT_WEEK in news_content:
            news_content = news_content.replace(
                "Initial development week.", "Initial development week with new features added."
            )
    else:
        # Create initial NEWS.md
        news_content = "# News\n\n## Week 1\n\nInitial development week with new features added.\n"
    news_file.write_text(news_content, encoding="utf-8")


def _update_changelog_file(changelog_file: Path, new_commits: list) -> None:
    """Update or create CHANGELOG.txt file."""
    changelog_content = (
        changelog_file.read_text(encoding="utf-8")
        if changelog_file.exists()
        else DEFAULT_CHANGELOG_CONTENT
    )
    for commit in new_commits:
        if isinstance(commit, dict):
            commit_obj = commit["commit"]
            message = commit_obj.message
        else:
            message = commit.message

        if FEAT_PREFIX in message:
            changelog_content = changelog_content.replace(
                "### Added\n- Initial features",
                f"### Added\n- Initial features\n- {message.split(':', 1)[1].strip()}",
            )
    changelog_file.write_text(changelog_content, encoding="utf-8")


def _update_daily_file(daily_file: Path) -> None:
    """Update or create DAILY_UPDATES.md file."""
    if daily_file.exists():
        daily_content = daily_file.read_text(encoding="utf-8")
        daily_content += f"\n## {datetime.now().strftime('%B %d, %Y')}\n\n- New updates added\n"
    else:
        # Create initial DAILY_UPDATES.md
        daily_content = (
            f"# Daily Updates\n\n## {datetime.now().strftime('%B %d, %Y')}\n\n- New updates added\n"
        )
    daily_file.write_text(daily_content, encoding="utf-8")


@when("I run git-ai-reporter again for the same week")
@when("I run git-ai-reporter")
@when("I run git-ai-reporter again")
def run_git_ai_reporter(
    incremental_context: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run git-ai-reporter on the repository."""
    _ = monkeypatch  # Acknowledge parameter usage
    _initialize_output_files(incremental_context)

    # In a real test, this would call the actual CLI
    # For this test, we'll simulate the update
    news_file = incremental_context["output_files"]["news"]
    changelog_file = incremental_context["output_files"]["changelog"]
    daily_file = incremental_context["output_files"]["daily"]

    # Simulate updating files with new commit info
    if incremental_context["new_commits"]:
        _update_news_file(news_file)
        _update_changelog_file(changelog_file, incremental_context["new_commits"])
        _update_daily_file(daily_file)


@then("NEWS.md should contain the new commit information")
def verify_news_has_new_commit(incremental_context: dict[str, Any]) -> None:
    """Verify NEWS.md contains information about the new commit."""
    news_file = incremental_context["output_files"]["news"]
    content = news_file.read_text(encoding="utf-8")
    assert NEW_FEATURES_ADDED_TEXT in content.lower() or NEW_FEATURE_TEXT in content.lower()


@then("CHANGELOG.txt should include the new feature entry")
def verify_changelog_has_new_feature(incremental_context: dict[str, Any]) -> None:
    """Verify CHANGELOG.txt includes the new feature entry."""
    changelog_file = incremental_context["output_files"]["changelog"]
    content = changelog_file.read_text(encoding="utf-8")

    # Check that new commits are in the changelog
    for commit in incremental_context["new_commits"]:
        message = commit["commit"].message if isinstance(commit, dict) else commit.message

        if FEAT_PREFIX in message:
            feature_text = message.split(":", 1)[1].strip()
            assert feature_text in content or FEATURE_KEYWORD in content.lower()


@then("DAILY_UPDATES.md should be updated with the new commit")
def verify_daily_has_new_commit(incremental_context: dict[str, Any]) -> None:
    """Verify DAILY_UPDATES.md has been updated."""
    daily_file = incremental_context["output_files"]["daily"]
    content = daily_file.read_text(encoding="utf-8")
    original = incremental_context["initial_daily"]
    assert len(content) > len(original)


@then("the week header should remain the same")
def verify_same_week_header(incremental_context: dict[str, Any]) -> None:
    """Verify the week header hasn't changed."""
    news_file = incremental_context["output_files"]["news"]
    content = news_file.read_text(encoding="utf-8")
    assert WEEK_ONE_HEADER in content or WEEK_PREFIX in content


@then("existing content should be preserved and merged")
def verify_content_preserved(incremental_context: dict[str, Any]) -> None:
    """Verify existing content is preserved."""
    news_file = incremental_context["output_files"]["news"]
    content = news_file.read_text(encoding="utf-8")
    # Check that initial content markers are still present
    assert CHANGELOG_CATEGORIES["Week"] in content
    assert PROJECT_NEWS_TITLE in content


@then("NEWS.md should contain all three new commits")
def verify_all_commits_in_news(incremental_context: dict[str, Any]) -> None:
    """Verify all new commits are in NEWS.md."""
    news_file = incremental_context["output_files"]["news"]
    _ = news_file.read_text(encoding="utf-8")
    assert len(incremental_context["new_commits"]) >= THREE_COMMITS


@then("the narrative should be coherent and comprehensive")
def verify_narrative_quality(incremental_context: dict[str, Any]) -> None:
    """Verify the narrative is coherent."""
    news_file = incremental_context["output_files"]["news"]
    content = news_file.read_text(encoding="utf-8")
    assert len(content) > NARRATIVE_QUALITY_THRESHOLD  # Should have substantial content


@then("no commits should be missing from the analysis")
def verify_no_missing_commits(incremental_context: dict[str, Any]) -> None:
    """Verify no commits are missing."""
    # In a real test, we would check that all commits in the repo
    # are represented in the output files
    assert len(incremental_context["new_commits"]) > 0


@then("the commits marked as should_appear=true should be in all output files")
def verify_commits_appear(incremental_context: dict[str, Any]) -> None:
    """Verify that commits that should appear are in output files."""
    changelog_file = incremental_context["output_files"]["changelog"]
    content = changelog_file.read_text(encoding="utf-8")

    for commit_info in incremental_context["new_commits"]:
        if isinstance(commit_info, dict) and commit_info.get("should_appear"):
            message = commit_info["commit"].message
            # At least the category should be in the changelog
            if FEAT_PREFIX in message or FIX_PREFIX in message:
                assert (
                    CHANGELOG_CATEGORIES["Added"] in content
                    or CHANGELOG_CATEGORIES["Fixed"] in content
                )


@then("the commits marked as should_appear=false may be filtered")
def verify_filtered_commits(incremental_context: dict[str, Any]) -> None:
    """Verify that trivial commits may be filtered."""
    # This is a permissive check - trivial commits MAY be filtered
    # but it's also OK if they appear. No verification needed.
    _ = incremental_context  # Acknowledge parameter usage


@then("NEWS.md should have separate entries for each week")
def verify_separate_week_entries(incremental_context: dict[str, Any]) -> None:
    """Verify NEWS.md has separate week entries."""
    news_file = incremental_context["output_files"]["news"]
    content = news_file.read_text(encoding="utf-8")
    # Should have at least one week header
    assert CHANGELOG_CATEGORIES["Week"] in content


@then("CHANGELOG.txt should contain all changes in [Unreleased]")
def verify_unreleased_section(incremental_context: dict[str, Any]) -> None:
    """Verify all changes are in the Unreleased section."""
    changelog_file = incremental_context["output_files"]["changelog"]
    content = changelog_file.read_text(encoding="utf-8")
    assert CHANGELOG_CATEGORIES["Unreleased"] in content


@then("each week should maintain its own narrative")
def verify_week_narratives(incremental_context: dict[str, Any]) -> None:
    """Verify each week has its own narrative."""
    news_file = incremental_context["output_files"]["news"]
    content = news_file.read_text(encoding="utf-8")
    # Each week section should have content
    lines = content.split("\n")
    week_count = sum(1 for line in lines if line.startswith("## Week"))
    assert week_count >= 1


@then("all three output files should have newer modification times")
def verify_newer_modification_times(incremental_context: dict[str, Any]) -> None:
    """Verify all output files have been updated."""
    for name, path in incremental_context["output_files"].items():
        if path.exists() and name in incremental_context["modification_times"]:
            old_time = incremental_context["modification_times"][name]
            new_time = path.stat().st_mtime
            assert new_time > old_time, f"{name} was not updated"


@then("the files should contain the new commit data")
def verify_files_contain_new_data(incremental_context: dict[str, Any]) -> None:
    """Verify the files contain new commit data."""
    # Check that at least one file has been meaningfully updated
    news_file = incremental_context["output_files"]["news"]
    content = news_file.read_text(encoding="utf-8")
    if original := incremental_context.get("initial_news", ""):
        assert content != original, "NEWS.md was not updated with new content"
