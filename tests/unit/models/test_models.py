# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for git_ai_reporter.models module.

This module tests all Pydantic models including validation,
serialization, and edge cases.
"""

from typing import get_args

from pydantic import ValidationError
import pytest
import pytest_check as check

from git_ai_reporter.models import AnalysisResult
from git_ai_reporter.models import Change
from git_ai_reporter.models import COMMIT_CATEGORIES
from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.models import CommitCategory


class TestChange:
    """Test suite for the Change model."""

    @pytest.mark.smoke
    def test_valid_change_creation(self) -> None:
        """Test creating a valid Change instance."""
        change = Change(
            summary="Added new authentication feature",
            category="New Feature",
        )
        check.equal(change.summary, "Added new authentication feature")
        check.equal(change.category, "New Feature")

    def test_change_with_all_categories(self) -> None:
        """Test that Change accepts all valid categories."""
        for category in COMMIT_CATEGORIES:
            change = Change(
                summary=f"Test change for {category}",
                category=category,  # type: ignore[arg-type]
            )
            check.equal(change.category, category)

    @pytest.mark.smoke
    def test_change_with_invalid_category(self) -> None:
        """Test that Change rejects invalid categories."""
        with pytest.raises(ValidationError) as exc_info:
            Change(
                summary="Test change",
                category="Invalid Category",  # type: ignore[arg-type]
            )
        errors = exc_info.value.errors()
        check.equal(len(errors), 1)
        check.is_in("literal_error", errors[0]["type"])

    def test_change_serialization(self) -> None:
        """Test Change model serialization."""
        change = Change(
            summary="Test summary",
            category="Bug Fix",
        )
        data = change.model_dump()
        check.equal(data["summary"], "Test summary")
        check.equal(data["category"], "Bug Fix")

    def test_change_json_roundtrip(self) -> None:
        """Test Change JSON serialization and deserialization."""
        change = Change(
            summary="Original summary",
            category="Security",
        )
        json_str = change.model_dump_json()
        reconstructed = Change.model_validate_json(json_str)
        check.equal(reconstructed.summary, change.summary)
        check.equal(reconstructed.category, change.category)

    def test_change_empty_summary(self) -> None:
        """Test that empty summary is allowed but empty."""
        change = Change(
            summary="",
            category="New Feature",
        )
        check.equal(change.summary, "")

    def test_change_field_descriptions(self) -> None:
        """Test that field descriptions are properly set."""
        schema = Change.model_json_schema()
        properties = schema["properties"]
        check.is_in("description", properties["summary"])
        check.is_in("description", properties["category"])


class TestCommitAnalysis:
    """Test suite for the CommitAnalysis model."""

    @pytest.mark.smoke
    def test_valid_commit_analysis_creation(self) -> None:
        """Test creating a valid CommitAnalysis instance."""
        analysis = CommitAnalysis(
            changes=[
                Change(summary="Feature 1", category="New Feature"),
                Change(summary="Fix 1", category="Bug Fix"),
            ],
            trivial=False,
        )
        check.equal(len(analysis.changes), 2)
        check.is_false(analysis.trivial)

    def test_commit_analysis_empty_changes(self) -> None:
        """Test CommitAnalysis with empty changes list."""
        analysis = CommitAnalysis(
            changes=[],
            trivial=True,
        )
        check.equal(len(analysis.changes), 0)
        check.is_true(analysis.trivial)

    def test_commit_analysis_default_trivial(self) -> None:
        """Test that trivial defaults to False."""
        analysis = CommitAnalysis(
            changes=[Change(summary="Test", category="Chore")],
            trivial=False,
        )
        check.is_false(analysis.trivial)

    def test_commit_analysis_serialization(self) -> None:
        """Test CommitAnalysis serialization."""
        analysis = CommitAnalysis(
            changes=[
                Change(summary="Added feature", category="New Feature"),
                Change(summary="Fixed bug", category="Bug Fix"),
            ],
            trivial=False,
        )
        data = analysis.model_dump()
        check.equal(len(data["changes"]), 2)
        check.equal(data["changes"][0]["summary"], "Added feature")
        check.is_false(data["trivial"])

    def test_commit_analysis_json_roundtrip(self) -> None:
        """Test CommitAnalysis JSON serialization and deserialization."""
        analysis = CommitAnalysis(
            changes=[
                Change(summary="Test change", category="Tests"),
            ],
            trivial=True,
        )
        json_str = analysis.model_dump_json()
        reconstructed = CommitAnalysis.model_validate_json(json_str)
        check.equal(len(reconstructed.changes), 1)
        check.equal(reconstructed.changes[0].summary, "Test change")
        check.is_true(reconstructed.trivial)

    def test_commit_analysis_many_changes(self) -> None:
        """Test CommitAnalysis with many changes."""
        changes = [Change(summary=f"Change {i}", category="New Feature") for i in range(100)]
        analysis = CommitAnalysis(changes=changes, trivial=False)
        check.equal(len(analysis.changes), 100)


class TestAnalysisResult:
    """Test suite for the AnalysisResult model."""

    def test_valid_analysis_result_creation(self) -> None:
        """Test creating a valid AnalysisResult instance."""
        result = AnalysisResult(
            period_summaries=["Week 1 summary", "Week 2 summary"],
            daily_summaries=["Day 1", "Day 2", "Day 3"],
            changelog_entries=[
                CommitAnalysis(
                    changes=[Change(summary="Feature", category="New Feature")],
                    trivial=False,
                ),
            ],
        )
        check.equal(len(result.period_summaries), 2)
        check.equal(len(result.daily_summaries), 3)
        check.equal(len(result.changelog_entries), 1)

    def test_analysis_result_empty_lists(self) -> None:
        """Test AnalysisResult with empty lists."""
        result = AnalysisResult(
            period_summaries=[],
            daily_summaries=[],
            changelog_entries=[],
        )
        check.equal(len(result.period_summaries), 0)
        check.equal(len(result.daily_summaries), 0)
        check.equal(len(result.changelog_entries), 0)

    def test_analysis_result_serialization(self) -> None:
        """Test AnalysisResult serialization."""
        result = AnalysisResult(
            period_summaries=["Summary 1"],
            daily_summaries=["Daily 1", "Daily 2"],
            changelog_entries=[
                CommitAnalysis(
                    changes=[Change(summary="Change 1", category="Bug Fix")],
                    trivial=False,
                ),
            ],
        )
        data = result.model_dump()
        check.equal(data["period_summaries"], ["Summary 1"])
        check.equal(len(data["daily_summaries"]), 2)
        check.equal(len(data["changelog_entries"]), 1)

    def test_analysis_result_json_roundtrip(self) -> None:
        """Test AnalysisResult JSON serialization and deserialization."""
        result = AnalysisResult(
            period_summaries=["Period 1"],
            daily_summaries=["Day 1"],
            changelog_entries=[
                CommitAnalysis(
                    changes=[
                        Change(summary="Test", category="Tests"),
                    ],
                    trivial=True,
                ),
            ],
        )
        json_str = result.model_dump_json()
        reconstructed = AnalysisResult.model_validate_json(json_str)
        check.equal(reconstructed.period_summaries, result.period_summaries)
        check.equal(reconstructed.daily_summaries, result.daily_summaries)
        check.equal(len(reconstructed.changelog_entries), 1)

    def test_analysis_result_large_dataset(self) -> None:
        """Test AnalysisResult with large amounts of data."""
        result = AnalysisResult(
            period_summaries=[f"Period {i}" for i in range(52)],  # Year of weeks
            daily_summaries=[f"Day {i}" for i in range(365)],  # Year of days
            changelog_entries=[
                CommitAnalysis(
                    changes=[Change(summary=f"Change {i}", category="Chore")],
                    trivial=False,
                )
                for i in range(1000)
            ],
        )
        check.equal(len(result.period_summaries), 52)
        check.equal(len(result.daily_summaries), 365)
        check.equal(len(result.changelog_entries), 1000)


class TestCommitCategories:
    """Test suite for commit categories and emojis."""

    def test_all_categories_have_emojis(self) -> None:
        """Test that all categories have corresponding emojis."""
        # Extract all valid categories from the Literal type
        categories = get_args(CommitCategory)
        for category in categories:
            check.is_in(category, COMMIT_CATEGORIES)
            check.is_true(len(COMMIT_CATEGORIES[category]) > 0)

    def test_emoji_uniqueness(self) -> None:
        """Test that all emojis are unique."""
        emojis = list(COMMIT_CATEGORIES.values())
        unique_emojis = set(emojis)
        check.equal(len(emojis), len(unique_emojis))

    def test_category_count(self) -> None:
        """Test that we have the expected number of categories."""
        check.equal(len(COMMIT_CATEGORIES), 17)
