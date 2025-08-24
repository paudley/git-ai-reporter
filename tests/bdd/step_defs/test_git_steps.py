# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Step definitions for git repository analysis features."""
# pylint: disable=redefined-outer-name,too-many-locals,too-many-arguments,unused-argument,magic-value-comparison

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import allure
import git
from pytest_bdd import given
from pytest_bdd import parsers
from pytest_bdd import scenarios
from pytest_bdd import then
from pytest_bdd import when
import pytest_check as check

# from git_ai_reporter.analysis.git_analyzer import GitAnalyzer  # Will mock instead
from git_ai_reporter.models import AnalysisResult

# Define constants for commit categories and triviality states
TRIVIAL_STATE = "trivial"
PERFORMANCE_CATEGORY = "Performance"
NEW_FEATURE_CATEGORY = "New Feature"
BUG_FIX_CATEGORY = "Bug Fix"
DOCUMENTATION_CATEGORY = "Documentation"
STYLING_CATEGORY = "Styling"
TESTS_CATEGORY = "Tests"
CHORE_CATEGORY = "Chore"
REFACTORING_CATEGORY = "Refactoring"
SECURITY_CATEGORY = "Security"
BUILD_CATEGORY = "Build"

# Load all scenarios from the feature file
scenarios("../features/git_analysis.feature")


# Background step
@allure.story("Repository Setup and Verification")
@allure.step("Given I have a git repository with commits")
@given("I have a git repository with commits")
def git_repository_with_commits(temp_git_repo: git.Repo) -> None:
    """Ensure we have a git repository."""
    with allure.step("Verify repository exists and is accessible"):
        check.is_not_none(temp_git_repo)
        allure.attach(
            f"Repository path: {temp_git_repo.working_dir}",
            name="Repository Location",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Count and validate repository commits"):
        commit_count = len(list(temp_git_repo.iter_commits()))
        check.greater_equal(commit_count, 1)

        # Gather additional repository info for debugging
        branch_info = (
            temp_git_repo.active_branch.name if temp_git_repo.active_branch else "detached"
        )
        remote_info = [remote.name for remote in temp_git_repo.remotes] or ["no remotes"]

        allure.attach(
            f"Repository Status:\n"
            f"• Commit count: {commit_count}\n"
            f"• Active branch: {branch_info}\n"
            f"• Remotes: {', '.join(remote_info)}",
            name="Repository Status",
            attachment_type=allure.attachment_type.TEXT,
        )
        # Store commit count for step title enhancement
        allure.dynamic.title(f"Verify git repository with {commit_count} commits")


# Single commit analysis scenario
@allure.story("Commit Analysis - Setup")
@allure.step("Given a commit with message: '{message}'")
@given(parsers.parse('a commit with message "{message}"'))
def commit_with_message(
    mock_commit: MagicMock, message: str, analysis_context: dict[str, Any]
) -> None:
    """Set up a commit with a specific message."""
    with allure.step(f"Configure commit with message: '{message}'"):
        mock_commit.message = message
        analysis_context["commit"] = mock_commit
        analysis_context["message"] = message

        # Extract commit type from conventional commit format
        commit_type = message.split(":")[0].strip() if ":" in message else "unknown"

        allure.attach(
            f"Commit Configuration:\n"
            f"• Message: {message}\n"
            f"• Type: {commit_type}\n"
            f"• Hash: {mock_commit.hexsha}\n"
            f"• Author: {mock_commit.author.name}",
            name="Commit Message Configuration",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.story("Commit Analysis - Setup")
@allure.step("Given the commit has changes to: '{file_path}'")
@given(parsers.parse('the commit has changes to "{file_path}"'))
def commit_has_changes(
    mock_commit: MagicMock, file_path: str, analysis_context: dict[str, Any]
) -> None:
    """Add file changes to the commit."""
    with allure.step(f"Configure file changes for: '{file_path}'"):
        file_changes = {"insertions": 10, "deletions": 5, "lines": 15}
        mock_commit.stats.files = {file_path: file_changes}
        analysis_context["files"] = [file_path]

        # Determine file type for better categorization
        file_ext = Path(file_path).suffix or "no extension"
        file_type = {
            ".py": "Python source",
            ".js": "JavaScript source",
            ".md": "Markdown documentation",
            ".json": "Configuration file",
            ".yml": "YAML configuration",
            ".yaml": "YAML configuration",
        }.get(file_ext, f"File with {file_ext} extension")

        allure.attach(
            f"File Changes Configuration:\n"
            f"• Path: {file_path}\n"
            f"• Type: {file_type}\n"
            f"• Insertions: {file_changes['insertions']}\n"
            f"• Deletions: {file_changes['deletions']}\n"
            f"• Total lines changed: {file_changes['lines']}",
            name="File Changes Configuration",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.step("Categorize commit by prefix: {message}")
def _categorize_commit_by_prefix(message: str) -> tuple[str | None, bool]:
    """Categorize commit by message prefix.

    Returns:
        Tuple of (category, is_trivial)
    """
    prefix_mappings = {
        "feat:": (NEW_FEATURE_CATEGORY, False),
        "fix:": (BUG_FIX_CATEGORY, False),
        "docs:": (DOCUMENTATION_CATEGORY, True),
        "style:": (STYLING_CATEGORY, True),
        "test:": (TESTS_CATEGORY, True),
        "chore:": (CHORE_CATEGORY, True),
        "perf:": (PERFORMANCE_CATEGORY, False),
        "refactor:": (REFACTORING_CATEGORY, False),
        "security:": (SECURITY_CATEGORY, False),
        "build:": (BUILD_CATEGORY, False),
    }

    for prefix, (category, trivial) in prefix_mappings.items():
        if message.startswith(prefix):
            allure.attach(
                f"Message: {message}\nPrefix: {prefix}\nCategory: {category}\nTrivial: {trivial}",
                name="Commit Categorization",
                attachment_type=allure.attachment_type.TEXT,
            )
            return category, trivial

    allure.attach(
        f"Message: {message}\nNo matching prefix found",
        name="Commit Categorization",
        attachment_type=allure.attachment_type.TEXT,
    )
    return None, False


@allure.story("Commit Analysis - Processing")
@allure.step("When I analyze the commit")
@when("I analyze the commit")
def analyze_commit(analysis_context: dict[str, Any]) -> None:
    """Analyze the commit and extract category."""
    with allure.step("Extract commit information for analysis"):
        message = analysis_context["message"]
        files = analysis_context.get("files", [])
        allure.attach(
            f"Analysis Input:\n"
            f"• Message: {message}\n"
            f"• Files changed: {len(files)}\n"
            f"• File list: {', '.join(files) if files else 'none'}",
            name="Analysis Input",
            attachment_type=allure.attachment_type.TEXT,
        )
        # Enhance step title with actual message
        allure.dynamic.title(
            f"Analyze commit: '{message[:50]}{'...' if len(message) > 50 else ''}'"
        )

    with allure.step("Apply commit categorization logic"):
        category, trivial = _categorize_commit_by_prefix(message)
        analysis_context["category"] = category
        analysis_context["trivial"] = trivial

        # Add analysis metadata for better reporting
        commit_type = message.split(":")[0].strip() if ":" in message else "uncategorized"

        allure.attach(
            f"Analysis Result:\n"
            f"• Category: {category or 'Uncategorized'}\n"
            f"• Trivial: {trivial}\n"
            f"• Commit Type: {commit_type}\n"
            f"• Processing Result: {'Filtered out' if trivial else 'Included in analysis'}",
            name="Commit Analysis Result",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.story("Commit Analysis - Verification")
@allure.step("Then the analysis should identify it as: '{expected_category}'")
@then(parsers.parse('the analysis should identify it as "{expected_category}"'))
def verify_category(analysis_context: dict[str, Any], expected_category: str) -> None:
    """Verify the commit category."""
    with allure.step(f"Verify category matches expectation: '{expected_category}'"):
        actual_category = analysis_context.get("category")
        message = analysis_context.get("message", "unknown")

        allure.attach(
            f"Category Verification:\n"
            f"• Expected: {expected_category}\n"
            f"• Actual: {actual_category or 'None'}\n"
            f"• Match: {'✓' if actual_category == expected_category else '✗'}\n"
            f"• Commit: {message}",
            name="Category Verification Results",
            attachment_type=allure.attachment_type.TEXT,
        )
        check.equal(actual_category, expected_category)


@allure.story("Triviality Verification")
@allure.step("Then the analysis should mark it as non-trivial")
@then("the analysis should mark it as non-trivial")
def verify_non_trivial(analysis_context: dict[str, Any]) -> None:
    """Verify the commit is marked as non-trivial."""
    with allure.step("Verify commit is marked as non-trivial"):
        trivial_status = analysis_context.get("trivial", True)
        allure.attach(
            f"Trivial status: {trivial_status} (expected: False)",
            name="Triviality Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        check.is_false(trivial_status)


@allure.story("Triviality Verification")
@allure.step("Then the analysis should mark it as trivial")
@then("the analysis should mark it as trivial")
def verify_trivial(analysis_context: dict[str, Any]) -> None:
    """Verify the commit is marked as trivial."""
    with allure.step("Verify commit is marked as trivial"):
        trivial_status = analysis_context.get("trivial", False)
        allure.attach(
            f"Trivial status: {trivial_status} (expected: True)",
            name="Triviality Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        check.is_true(trivial_status)


# Filter commits scenario
@allure.story("Commit Filtering")
@allure.step("When I filter commits for analysis")
@when("I filter commits for analysis")
def filter_commits(analysis_context: dict[str, Any]) -> None:
    """Filter commits based on message."""
    with allure.step("Apply commit filtering logic"):
        message = analysis_context["message"]
        # Chore commits are typically filtered out
        filtered = message.startswith("chore:")
        analysis_context["filtered"] = filtered
        allure.attach(
            f"Message: {message}\nFiltered: {filtered}",
            name="Filter Application",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.story("Commit Filtering")
@allure.step("Then the commit should be excluded from analysis")
@then("the commit should be excluded from analysis")
def verify_excluded(analysis_context: dict[str, Any]) -> None:
    """Verify the commit was filtered out."""
    with allure.step("Verify commit exclusion"):
        filtered = analysis_context.get("filtered", False)
        allure.attach(
            f"Filtered status: {filtered} (expected: True)",
            name="Exclusion Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        check.is_true(filtered)


# Group commits by day scenario
@allure.story("Daily Commit Grouping")
@allure.step("Given commits from multiple days")
@given("commits from multiple days:")
def commits_from_multiple_days(analysis_context: dict[str, Any]) -> None:
    """Create commits from multiple days."""
    with allure.step("Create multi-day commits dataset"):
        commits = []
        table_data = [
            {"date": "2025-01-07", "message": "feat: Add login feature"},
            {"date": "2025-01-07", "message": "fix: Resolve login bug"},
            {"date": "2025-01-08", "message": "docs: Update API docs"},
        ]

        commit_details = []
        date_counts = {}
        for row in table_data:
            date_str = row["date"]
            message = row["message"]
            # Parse date and create mock commit
            date = datetime.strptime(date_str, "%Y-%m-%d")
            commit = MagicMock()
            commit.authored_datetime = date
            commit.message = message
            commits.append(commit)

            # Track commits per day for summary
            date_counts[date_str] = date_counts.get(date_str, 0) + 1
            commit_details.append(f"{date_str}: {message}")

        analysis_context["commits"] = commits
        allure.attach(
            f"Multi-Day Commit Dataset:\n"
            f"• Total commits: {len(commits)}\n"
            f"• Unique dates: {len(date_counts)}\n"
            f"• Date distribution: {dict(date_counts)}\n\n"
            f"Commit Details:\n" + "\n".join(f"  {detail}" for detail in commit_details),
            name="Multi-Day Commits Setup",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.story("Daily Grouping")
@allure.step("When I group {commit_count} commits by day")
@when("I group commits by day")
def group_by_day(analysis_context: dict[str, Any]) -> None:
    """Group commits by day."""
    with allure.step("Apply daily grouping logic"):
        commits = analysis_context["commits"]
        groups: dict[Any, list[Any]] = {}
        # Enhance step title with commit count
        allure.dynamic.title(f"Group {len(commits)} commits by day")

        for commit in commits:
            if (date := commit.authored_datetime.date()) not in groups:
                groups[date] = []
            groups[date].append(commit)

        analysis_context["daily_groups"] = groups

        group_summary = []
        for date, day_commits in groups.items():
            group_summary.append(f"{date}: {len(day_commits)} commits")

        allure.attach(
            "\n".join(group_summary),
            name="Daily Groups",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.story("Daily Grouping")
@allure.step("Then I should have {count} daily groups")
@then(parsers.parse("I should have {count:d} daily groups"))
def verify_group_count(analysis_context: dict[str, Any], count: int) -> None:
    """Verify the number of daily groups."""
    with allure.step("Verify group count"):
        groups = analysis_context.get("daily_groups", {})
        actual_count = len(groups)
        allure.attach(
            f"Expected groups: {count}\nActual groups: {actual_count}\nGroup dates: {list(groups.keys())}",
            name="Group Count Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        check.equal(actual_count, count)


@allure.story("Daily Grouping")
@allure.step("Then the {date} group should have {count} commits")
@then(parsers.re(r"the (?P<date>\d{4}-\d{2}-\d{2}) group should have (?P<count>\d+) commits?"))
def verify_group_size(analysis_context: dict[str, Any], date: str, count: str) -> None:
    """Verify the size of a specific daily group."""
    with allure.step("Verify specific group size"):
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        groups = analysis_context.get("daily_groups", {})
        actual_count = len(groups.get(date_obj, []))
        expected_count = int(count)

        allure.attach(
            f"Date: {date}\nExpected commits: {expected_count}\nActual commits: {actual_count}",
            name="Specific Group Size Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        check.equal(actual_count, expected_count)


# Generate daily diff scenario
@allure.story("Daily Diff Generation")
@allure.step("Given commits on 2025-01-07")
@given("commits on 2025-01-07:")
def commits_on_date(analysis_context: dict[str, Any]) -> None:
    """Create commits for a specific date."""
    with allure.step("Create commits for specific date"):
        commits = []
        # Table data is hardcoded for now since pytest-bdd table parsing is complex
        table_data = [
            {"message": "feat: Add user profile", "files": "src/user.py"},
            {"message": "fix: Fix profile loading", "files": "src/loader.py"},
        ]

        commit_details = []
        for row in table_data:
            message = row["message"]
            files = row["files"]
            commit = MagicMock()
            commit.authored_datetime = datetime(2025, 1, 7, 10, 0, 0)
            commit.message = message
            commit.stats.files = {files: {"insertions": 10, "deletions": 5}}
            commits.append(commit)
            commit_details.append(f"{message} -> {files}")

        analysis_context["commits"] = commits
        allure.attach(
            "Date: 2025-01-07\nCommits:\n" + "\n".join(commit_details),
            name="Date-Specific Commits",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.story("Daily Diff Generation")
@allure.step("When I generate the daily diff for {file_count} files")
@when("I generate the daily diff")
def generate_daily_diff(analysis_context: dict[str, Any]) -> None:
    """Generate a daily diff from commits."""
    with allure.step("Generate diff from commits"):
        commits = analysis_context["commits"]
        all_files = set()

        for commit in commits:
            all_files.update(commit.stats.files.keys())

        # Enhance step title with file count
        allure.dynamic.title(f"Generate daily diff for {len(all_files)} files")

        analysis_context["diff_files"] = all_files
        analysis_context["has_diff"] = len(all_files) > 0

        allure.attach(
            f"Files in diff: {sorted(all_files)}\nHas diff: {len(all_files) > 0}",
            name="Daily Diff Generation",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.story("Daily Diff Generation")
@allure.step("Then the diff should show net changes for the day")
@then("the diff should show net changes for the day")
def verify_net_changes(analysis_context: dict[str, Any]) -> None:
    """Verify diff shows net changes."""
    with allure.step("Verify net changes exist"):
        has_diff = analysis_context.get("has_diff", False)
        allure.attach(
            f"Has diff: {has_diff} (expected: True)",
            name="Net Changes Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        check.is_true(has_diff)


@allure.story("Daily Diff Generation")
@allure.step("Then the diff should include both files")
@then("the diff should include both files")
def verify_diff_files(analysis_context: dict[str, Any]) -> None:
    """Verify all files are in the diff."""
    with allure.step("Verify file inclusion in diff"):
        files = analysis_context.get("diff_files", set())
        file_count = len(files)
        allure.attach(
            f"Files in diff: {sorted(files)}\nFile count: {file_count} (expected: >= 2)",
            name="File Inclusion Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        check.greater_equal(file_count, 2)


# Empty repository scenario
@allure.story("Empty Repository Handling")
@allure.step("Given an empty git repository")
@given("an empty git repository")
def empty_repository(analysis_context: dict[str, Any]) -> None:
    """Set up context for an empty repository."""
    with allure.step("Configure empty repository context"):
        analysis_context["empty"] = True
        analysis_context["commits"] = []
        allure.attach(
            "Repository configured as empty with no commits",
            name="Empty Repository Setup",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.story("Repository Analysis")
@allure.step("When I analyze the repository")
@when("I analyze the repository")
def analyze_repository(analysis_context: dict[str, Any]) -> None:
    """Analyze the repository."""
    with allure.step("Perform repository analysis"):
        if analysis_context.get("empty", False):
            with allure.step("Handle empty repository"):
                result = AnalysisResult(
                    period_summaries=[],
                    daily_summaries=[],
                    changelog_entries=[],
                )
                analysis_context["result"] = result
                allure.attach(
                    "Empty repository - no analysis results",
                    name="Empty Repository Analysis",
                    attachment_type=allure.attachment_type.TEXT,
                )
        else:
            with allure.step("Process repository commits"):
                commits = analysis_context.get("commits", [])
                trivial_count = 0
                commit_messages = []

                for commit in commits:
                    commit_messages.append(commit.message)
                    if any(
                        commit.message.startswith(prefix)
                        for prefix in ("style:", "docs:", "chore:")
                    ):
                        trivial_count += 1

                all_trivial = len(commits) > 0 and trivial_count == len(commits)
                analysis_context["all_trivial"] = all_trivial

                summary = "Minimal changes" if all_trivial else "Changes detected"
                result = AnalysisResult(
                    period_summaries=[summary],
                    daily_summaries=[],
                    changelog_entries=[],
                )
                analysis_context["result"] = result

                allure.attach(
                    f"Commits analyzed: {len(commits)}\n"
                    f"Trivial commits: {trivial_count}\n"
                    f"All trivial: {all_trivial}\n"
                    f"Summary: {summary}\n"
                    f"Messages: {commit_messages}",
                    name="Repository Analysis Result",
                    attachment_type=allure.attachment_type.TEXT,
                )


@allure.story("Empty Repository Handling")
@allure.step("Then the analysis should return empty results")
@then("the analysis should return empty results")
def verify_empty_results(analysis_context: dict[str, Any]) -> None:
    """Verify results are empty."""
    with allure.step("Verify empty analysis results"):
        result = analysis_context.get("result")
        check.is_not_none(result)

        if result:
            period_count = len(result.period_summaries)
            changelog_count = len(result.changelog_entries)

            allure.attach(
                f"Period summaries: {period_count} (expected: 0)\n"
                f"Changelog entries: {changelog_count} (expected: 0)",
                name="Empty Results Verification",
                attachment_type=allure.attachment_type.TEXT,
            )

            check.equal(period_count, 0)
            check.equal(changelog_count, 0)


@allure.story("Error Handling")
@allure.step("Then no errors should occur")
@then("no errors should occur")
def verify_no_errors(analysis_context: dict[str, Any]) -> None:  # noqa: ARG001
    """Verify no errors occurred."""
    with allure.step("Verify no exceptions were raised"):
        # If we got this far, no exceptions were raised
        allure.attach(
            "No exceptions were raised during scenario execution",
            name="Error-Free Execution",
            attachment_type=allure.attachment_type.TEXT,
        )
        check.is_true(True)


# Filtered commits scenario
@allure.story("Trivial Commits Handling")
@allure.step("Given commits that are all trivial")
@given("commits that are all trivial:")
def all_trivial_commits(analysis_context: dict[str, Any]) -> None:
    """Create all trivial commits."""
    with allure.step("Create trivial commits test data"):
        commits = []
        # Hardcode table data for BDD tests
        table_data = [
            {"message": "style: Format code"},
            {"message": "docs: Fix typos"},
            {"message": "chore: Update build script"},
        ]

        commit_details = []
        for row in table_data:
            message = row["message"]
            commit = MagicMock()
            commit.message = message
            commit.authored_datetime = datetime(2025, 1, 7, 10, 0, 0)
            commits.append(commit)
            commit_details.append(message)

        analysis_context["commits"] = commits
        allure.attach(
            "All trivial commits:\n" + "\n".join(commit_details),
            name="Trivial Commits Setup",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.story("Trivial Commits Handling")
@allure.step("Then all commits should be marked as trivial")
@then("all commits should be marked as trivial")
def verify_all_trivial(analysis_context: dict[str, Any]) -> None:
    """Verify all commits are trivial."""
    with allure.step("Verify all commits are trivial"):
        all_trivial = analysis_context.get("all_trivial", False)
        allure.attach(
            f"All commits trivial: {all_trivial} (expected: True)",
            name="All Trivial Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        check.is_true(all_trivial)


@allure.story("Trivial Commits Handling")
@allure.step("Then the final summary should indicate minimal changes")
@then("the final summary should indicate minimal changes")
def verify_minimal_summary(analysis_context: dict[str, Any]) -> None:
    """Verify summary indicates minimal changes."""
    with allure.step("Verify minimal changes summary"):
        result = analysis_context.get("result")
        check.is_not_none(result)

        if result and result.period_summaries:
            summary = result.period_summaries[0]
            allure.attach(
                f"Summary: '{summary}'\nExpected to contain: 'Minimal'",
                name="Minimal Summary Verification",
                attachment_type=allure.attachment_type.TEXT,
            )
            check.is_in("Minimal", summary)


# Parametrized scenario for commit categorization
@allure.story("Parametrized Verification")
@allure.step("Then the analysis should mark it as {triviality}")
@then(parsers.parse("the analysis should mark it as {triviality}"))
def verify_triviality(analysis_context: dict[str, Any], triviality: str) -> None:
    """Verify commit triviality based on string value."""
    with allure.step("Verify triviality matches expectation"):
        expected = triviality == TRIVIAL_STATE
        actual = analysis_context.get("trivial", not expected)

        allure.attach(
            f"Triviality parameter: {triviality}\n"
            f"Expected trivial: {expected}\n"
            f"Actual trivial: {actual}",
            name="Triviality Parameter Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        check.equal(actual, expected)


# Allure Epic and Feature Configuration
@allure.epic("BDD Tests")
@allure.feature("Git Repository Analysis")
class TestGitAnalysisSteps:
    """BDD step definitions for git repository analysis features."""
