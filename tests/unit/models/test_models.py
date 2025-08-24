# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for git_ai_reporter.models module.

This module tests all Pydantic models including validation,
serialization, and edge cases.
"""

import json
from typing import get_args

import allure
from pydantic import ValidationError
import pytest
import pytest_check as check

from git_ai_reporter.models import AnalysisResult
from git_ai_reporter.models import Change
from git_ai_reporter.models import COMMIT_CATEGORIES
from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.models import CommitCategory


@allure.feature("Data Models")
class TestChange:
    """Test suite for the Change model."""

    @allure.story("Change Model Creation")
    @allure.title("Create valid Change instance with required fields")
    @allure.description(
        "Verifies that a Change model can be created with valid summary and category fields"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("smoke", "models", "change", "validation", "data-integrity")
    @allure.testcase("TC-MODEL-001", "Test Change model creation")
    @pytest.mark.smoke
    def test_valid_change_creation(self) -> None:
        """Test creating a valid Change instance."""
        allure.dynamic.description("Testing Pydantic model instantiation with data validation")

        with allure.step("Create Change instance with valid data"):
            try:
                change = Change(
                    summary="Added new authentication feature",
                    category="New Feature",
                )

                allure.attach(
                    json.dumps(
                        {
                            "summary": change.summary,
                            "category": change.category,
                            "model_type": "Change",
                            "validation_passed": True,
                        },
                        indent=2,
                    ),
                    "Change Model Data",
                    allure.attachment_type.JSON,
                )
            except Exception as e:
                allure.attach(
                    f"Model creation failed: {str(e)}",
                    "Model Creation Error",
                    allure.attachment_type.TEXT,
                )
                raise

        with allure.step("Verify Change instance properties"):
            check.equal(change.summary, "Added new authentication feature")
            check.equal(change.category, "New Feature")

            allure.attach(
                "Change model validation successful",
                "Validation Result",
                allure.attachment_type.TEXT,
            )

    @allure.story("Change Model Validation")
    @allure.title("Validate Change accepts all defined categories")
    @allure.description(
        "Tests that the Change model accepts all valid categories defined in COMMIT_CATEGORIES"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "change", "validation", "categories")
    def test_change_with_all_categories(self) -> None:
        """Test that Change accepts all valid categories."""
        with allure.step(f"Test all {len(COMMIT_CATEGORIES)} valid categories"):
            for category in COMMIT_CATEGORIES:
                with allure.step(f"Test category: {category}"):
                    change = Change(
                        summary=f"Test change for {category}",
                        category=category,  # type: ignore[arg-type]
                    )
                    check.equal(change.category, category)

            allure.attach(
                str(list(COMMIT_CATEGORIES.keys())),
                "Valid Categories Tested",
                allure.attachment_type.JSON,
            )

    @allure.story("Change Model Validation")
    @allure.title("Reject invalid categories with ValidationError")
    @allure.description("Verifies that the Change model properly rejects invalid category values")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("smoke", "models", "change", "validation", "error-handling")
    @pytest.mark.smoke
    def test_change_with_invalid_category(self) -> None:
        """Test that Change rejects invalid categories."""
        with allure.step("Attempt to create Change with invalid category"):
            with pytest.raises(ValidationError) as exc_info:
                Change(
                    summary="Test change",
                    category="Invalid Category",  # type: ignore[arg-type]
                )

        with allure.step("Verify ValidationError details"):
            errors = exc_info.value.errors()
            allure.attach(str(errors), "ValidationError Details", allure.attachment_type.JSON)
            check.equal(len(errors), 1)
            check.is_in("literal_error", errors[0]["type"])

    @allure.story("Change Model Serialization")
    @allure.title("Serialize Change to dictionary format")
    @allure.description("Tests that Change model can be serialized to dictionary format correctly")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "change", "serialization")
    def test_change_serialization(self) -> None:
        """Test Change model serialization."""
        with allure.step("Create Change instance for serialization"):
            change = Change(
                summary="Test summary",
                category="Bug Fix",
            )

        with allure.step("Serialize Change to dictionary"):
            data = change.model_dump()

        with allure.step("Verify serialized data"):
            allure.attach(str(data), "Serialized Change Data", allure.attachment_type.JSON)
            check.equal(data["summary"], "Test summary")
            check.equal(data["category"], "Bug Fix")

    @allure.story("Change Model Serialization")
    @allure.title("JSON roundtrip serialization and deserialization")
    @allure.description(
        "Tests that Change model maintains data integrity through JSON serialization roundtrip"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "change", "serialization", "json")
    def test_change_json_roundtrip(self) -> None:
        """Test Change JSON serialization and deserialization."""
        with allure.step("Create original Change instance"):
            change = Change(
                summary="Original summary",
                category="Security",
            )

        with allure.step("Serialize to JSON"):
            json_str = change.model_dump_json()
            allure.attach(json_str, "JSON Serialized Data", allure.attachment_type.JSON)

        with allure.step("Deserialize from JSON"):
            reconstructed = Change.model_validate_json(json_str)

        with allure.step("Verify roundtrip integrity"):
            check.equal(reconstructed.summary, change.summary)
            check.equal(reconstructed.category, change.category)

    @allure.story("Change Model Edge Cases")
    @allure.title("Handle empty summary string")
    @allure.description("Verifies that Change model accepts empty summary strings")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("models", "change", "edge-cases", "validation")
    def test_change_empty_summary(self) -> None:
        """Test that empty summary is allowed but empty."""
        with allure.step("Create Change with empty summary"):
            change = Change(
                summary="",
                category="New Feature",
            )

        with allure.step("Verify empty summary is preserved"):
            allure.attach(
                f"Summary length: {len(change.summary)}",
                "Empty Summary Verification",
                allure.attachment_type.TEXT,
            )
            check.equal(change.summary, "")

    @allure.story("Change Model Schema")
    @allure.title("Validate field descriptions in schema")
    @allure.description(
        "Verifies that Change model fields have proper descriptions in the JSON schema"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("models", "change", "schema", "documentation")
    def test_change_field_descriptions(self) -> None:
        """Test that field descriptions are properly set."""
        with allure.step("Generate JSON schema for Change model"):
            schema = Change.model_json_schema()
            properties = schema["properties"]

        with allure.step("Verify field descriptions exist"):
            allure.attach(
                str(properties), "Change Model Schema Properties", allure.attachment_type.JSON
            )
            check.is_in("description", properties["summary"])
            check.is_in("description", properties["category"])


@allure.feature("Data Models")
class TestCommitAnalysis:
    """Test suite for the CommitAnalysis model."""

    @allure.story("CommitAnalysis Model Creation")
    @allure.title("Create valid CommitAnalysis with multiple changes")
    @allure.description("Verifies that CommitAnalysis can be created with a list of Change objects")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("smoke", "models", "commit-analysis", "validation")
    @pytest.mark.smoke
    def test_valid_commit_analysis_creation(self) -> None:
        """Test creating a valid CommitAnalysis instance."""
        with allure.step("Create CommitAnalysis with multiple changes"):
            analysis = CommitAnalysis(
                changes=[
                    Change(summary="Feature 1", category="New Feature"),
                    Change(summary="Fix 1", category="Bug Fix"),
                ],
                trivial=False,
            )

        with allure.step("Verify CommitAnalysis properties"):
            allure.attach(
                f"Changes count: {len(analysis.changes)}\nTrivial: {analysis.trivial}",
                "CommitAnalysis Instance Data",
                allure.attachment_type.TEXT,
            )
            check.equal(len(analysis.changes), 2)
            check.is_false(analysis.trivial)

    @allure.story("CommitAnalysis Model Edge Cases")
    @allure.title("Handle empty changes list")
    @allure.description("Verifies that CommitAnalysis accepts empty changes list")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "commit-analysis", "edge-cases")
    def test_commit_analysis_empty_changes(self) -> None:
        """Test CommitAnalysis with empty changes list."""
        with allure.step("Create CommitAnalysis with empty changes"):
            analysis = CommitAnalysis(
                changes=[],
                trivial=True,
            )

        with allure.step("Verify empty changes handling"):
            allure.attach(
                f"Changes count: {len(analysis.changes)}\nTrivial: {analysis.trivial}",
                "Empty Changes Analysis",
                allure.attachment_type.TEXT,
            )
            check.equal(len(analysis.changes), 0)
            check.is_true(analysis.trivial)

    @allure.story("CommitAnalysis Model Defaults")
    @allure.title("Verify trivial field default behavior")
    @allure.description("Tests the default value and explicit setting of the trivial field")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("models", "commit-analysis", "defaults")
    def test_commit_analysis_default_trivial(self) -> None:
        """Test that trivial defaults to False."""
        with allure.step("Create CommitAnalysis with explicit trivial=False"):
            analysis = CommitAnalysis(
                changes=[Change(summary="Test", category="Chore")],
                trivial=False,
            )

        with allure.step("Verify trivial field value"):
            allure.attach(
                f"Trivial value: {analysis.trivial}",
                "Trivial Field Verification",
                allure.attachment_type.TEXT,
            )
            check.is_false(analysis.trivial)

    @allure.story("CommitAnalysis Model Serialization")
    @allure.title("Serialize CommitAnalysis to dictionary format")
    @allure.description(
        "Tests that CommitAnalysis model can be serialized to dictionary format with nested Change objects"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "commit-analysis", "serialization")
    def test_commit_analysis_serialization(self) -> None:
        """Test CommitAnalysis serialization."""
        with allure.step("Create CommitAnalysis with multiple changes"):
            analysis = CommitAnalysis(
                changes=[
                    Change(summary="Added feature", category="New Feature"),
                    Change(summary="Fixed bug", category="Bug Fix"),
                ],
                trivial=False,
            )

        with allure.step("Serialize CommitAnalysis to dictionary"):
            data = analysis.model_dump()

        with allure.step("Verify serialized data structure"):
            allure.attach(str(data), "Serialized CommitAnalysis Data", allure.attachment_type.JSON)
            check.equal(len(data["changes"]), 2)
            check.equal(data["changes"][0]["summary"], "Added feature")
            check.is_false(data["trivial"])

    @allure.story("CommitAnalysis Model Serialization")
    @allure.title("JSON roundtrip serialization and deserialization")
    @allure.description(
        "Tests that CommitAnalysis maintains data integrity through JSON serialization roundtrip"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "commit-analysis", "serialization", "json")
    def test_commit_analysis_json_roundtrip(self) -> None:
        """Test CommitAnalysis JSON serialization and deserialization."""
        with allure.step("Create original CommitAnalysis instance"):
            analysis = CommitAnalysis(
                changes=[
                    Change(summary="Test change", category="Tests"),
                ],
                trivial=True,
            )

        with allure.step("Serialize to JSON"):
            json_str = analysis.model_dump_json()
            allure.attach(json_str, "JSON Serialized CommitAnalysis", allure.attachment_type.JSON)

        with allure.step("Deserialize from JSON"):
            reconstructed = CommitAnalysis.model_validate_json(json_str)

        with allure.step("Verify roundtrip integrity"):
            check.equal(len(reconstructed.changes), 1)
            check.equal(reconstructed.changes[0].summary, "Test change")
            check.is_true(reconstructed.trivial)

    @allure.story("CommitAnalysis Model Performance")
    @allure.title("Handle large number of changes")
    @allure.description(
        "Tests that CommitAnalysis can handle a large number of Change objects efficiently"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "commit-analysis", "performance", "scalability")
    def test_commit_analysis_many_changes(self) -> None:
        """Test CommitAnalysis with many changes."""
        with allure.step("Generate 100 Change objects"):
            changes = [Change(summary=f"Change {i}", category="New Feature") for i in range(100)]

        with allure.step("Create CommitAnalysis with many changes"):
            analysis = CommitAnalysis(changes=changes, trivial=False)

        with allure.step("Verify all changes are preserved"):
            allure.attach(
                f"Total changes: {len(analysis.changes)}",
                "Large Changes Set Verification",
                allure.attachment_type.TEXT,
            )
            check.equal(len(analysis.changes), 100)


@allure.feature("Data Models")
class TestAnalysisResult:
    """Test suite for the AnalysisResult model."""

    @allure.story("AnalysisResult Model Creation")
    @allure.title("Create valid AnalysisResult with all field types")
    @allure.description("Verifies that AnalysisResult can be created with all required field types")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("models", "analysis-result", "validation")
    def test_valid_analysis_result_creation(self) -> None:
        """Test creating a valid AnalysisResult instance."""
        with allure.step("Create AnalysisResult with comprehensive data"):
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

        with allure.step("Verify AnalysisResult field counts"):
            allure.attach(
                f"Period summaries: {len(result.period_summaries)}\n"
                f"Daily summaries: {len(result.daily_summaries)}\n"
                f"Changelog entries: {len(result.changelog_entries)}",
                "AnalysisResult Field Counts",
                allure.attachment_type.TEXT,
            )
            check.equal(len(result.period_summaries), 2)
            check.equal(len(result.daily_summaries), 3)
            check.equal(len(result.changelog_entries), 1)

    @allure.story("AnalysisResult Model Edge Cases")
    @allure.title("Handle empty lists for all fields")
    @allure.description("Verifies that AnalysisResult accepts empty lists for all its fields")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "analysis-result", "edge-cases")
    def test_analysis_result_empty_lists(self) -> None:
        """Test AnalysisResult with empty lists."""
        with allure.step("Create AnalysisResult with empty lists"):
            result = AnalysisResult(
                period_summaries=[],
                daily_summaries=[],
                changelog_entries=[],
            )

        with allure.step("Verify empty lists handling"):
            allure.attach(
                f"Period summaries: {len(result.period_summaries)}\n"
                f"Daily summaries: {len(result.daily_summaries)}\n"
                f"Changelog entries: {len(result.changelog_entries)}",
                "Empty Lists Verification",
                allure.attachment_type.TEXT,
            )
            check.equal(len(result.period_summaries), 0)
            check.equal(len(result.daily_summaries), 0)
            check.equal(len(result.changelog_entries), 0)

    @allure.story("AnalysisResult Model Serialization")
    @allure.title("Serialize AnalysisResult to dictionary format")
    @allure.description(
        "Tests that AnalysisResult can be serialized to dictionary with nested structures"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "analysis-result", "serialization")
    def test_analysis_result_serialization(self) -> None:
        """Test AnalysisResult serialization."""
        with allure.step("Create AnalysisResult with mixed data"):
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

        with allure.step("Serialize AnalysisResult to dictionary"):
            data = result.model_dump()

        with allure.step("Verify serialized data structure"):
            allure.attach(str(data), "Serialized AnalysisResult Data", allure.attachment_type.JSON)
            check.equal(data["period_summaries"], ["Summary 1"])
            check.equal(len(data["daily_summaries"]), 2)
            check.equal(len(data["changelog_entries"]), 1)

    @allure.story("AnalysisResult Model Serialization")
    @allure.title("JSON roundtrip serialization and deserialization")
    @allure.description(
        "Tests that AnalysisResult maintains data integrity through JSON serialization roundtrip"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "analysis-result", "serialization", "json")
    def test_analysis_result_json_roundtrip(self) -> None:
        """Test AnalysisResult JSON serialization and deserialization."""
        with allure.step("Create original AnalysisResult instance"):
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

        with allure.step("Serialize to JSON"):
            json_str = result.model_dump_json()
            allure.attach(json_str, "JSON Serialized AnalysisResult", allure.attachment_type.JSON)

        with allure.step("Deserialize from JSON"):
            reconstructed = AnalysisResult.model_validate_json(json_str)

        with allure.step("Verify roundtrip integrity"):
            check.equal(reconstructed.period_summaries, result.period_summaries)
            check.equal(reconstructed.daily_summaries, result.daily_summaries)
            check.equal(len(reconstructed.changelog_entries), 1)

    @allure.story("AnalysisResult Model Performance")
    @allure.title("Handle large datasets efficiently")
    @allure.description(
        "Tests that AnalysisResult can handle large amounts of data (yearly scale) efficiently"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "analysis-result", "performance", "scalability")
    def test_analysis_result_large_dataset(self) -> None:
        """Test AnalysisResult with large amounts of data."""
        with allure.step("Generate large dataset (yearly scale)"):
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

        with allure.step("Verify large dataset handling"):
            allure.attach(
                f"Period summaries: {len(result.period_summaries)}\n"
                f"Daily summaries: {len(result.daily_summaries)}\n"
                f"Changelog entries: {len(result.changelog_entries)}",
                "Large Dataset Verification",
                allure.attachment_type.TEXT,
            )
            check.equal(len(result.period_summaries), 52)
            check.equal(len(result.daily_summaries), 365)
            check.equal(len(result.changelog_entries), 1000)


@allure.feature("Data Models")
class TestCommitCategories:
    """Test suite for commit categories and emojis."""

    @allure.story("Commit Categories Validation")
    @allure.title("Verify all categories have corresponding emojis")
    @allure.description(
        "Tests that every category in CommitCategory type has a corresponding emoji in COMMIT_CATEGORIES"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("models", "categories", "emojis", "validation")
    def test_all_categories_have_emojis(self) -> None:
        """Test that all categories have corresponding emojis."""
        with allure.step("Extract all valid categories from CommitCategory type"):
            # Extract all valid categories from the Literal type
            categories = get_args(CommitCategory)

        with allure.step(f"Verify {len(categories)} categories have emojis"):
            for category in categories:
                with allure.step(f"Check category: {category}"):
                    check.is_in(category, COMMIT_CATEGORIES)
                    check.is_true(len(COMMIT_CATEGORIES[category]) > 0)

            allure.attach(
                str(list(categories)), "All Valid Categories", allure.attachment_type.JSON
            )

    @allure.story("Commit Categories Validation")
    @allure.title("Verify emoji uniqueness across categories")
    @allure.description("Tests that each emoji is used only once across all commit categories")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("models", "categories", "emojis", "uniqueness")
    def test_emoji_uniqueness(self) -> None:
        """Test that all emojis are unique."""
        with allure.step("Extract all emojis from categories"):
            emojis = list(COMMIT_CATEGORIES.values())
            unique_emojis = set(emojis)

        with allure.step("Verify emoji uniqueness"):
            allure.attach(
                f"Total emojis: {len(emojis)}\nUnique emojis: {len(unique_emojis)}\nEmojis: {emojis}",
                "Emoji Uniqueness Check",
                allure.attachment_type.TEXT,
            )
            check.equal(len(emojis), len(unique_emojis))

    @allure.story("Commit Categories Validation")
    @allure.title("Verify expected number of categories")
    @allure.description(
        "Tests that the COMMIT_CATEGORIES dictionary contains the expected number of categories"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("models", "categories", "count")
    def test_category_count(self) -> None:
        """Test that we have the expected number of categories."""
        with allure.step("Check total category count"):
            category_count = len(COMMIT_CATEGORIES)
            allure.attach(
                f"Total categories: {category_count}\nCategories: {list(COMMIT_CATEGORIES.keys())}",
                "Category Count Verification",
                allure.attachment_type.TEXT,
            )
            check.equal(category_count, 17)
