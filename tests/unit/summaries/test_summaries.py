# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for git_ai_reporter.summaries modules.

This module tests the prompt templates and constants in the summary modules.
"""

import allure
import pytest_check as check

from git_ai_reporter.models import COMMIT_CATEGORIES
from git_ai_reporter.summaries import commit
from git_ai_reporter.summaries import daily
from git_ai_reporter.summaries import weekly


@allure.feature("Summary Module - Commit Prompts")
class TestCommitSummaryPrompts:
    """Test suite for commit summary prompts."""

    @allure.story("Content Generation")
    @allure.title("Prompt template includes all commit categories")
    @allure.description(
        "Validates that the commit prompt template includes all defined commit categories"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("prompts", "templates", "categories")
    def test_prompt_template_includes_all_categories(self) -> None:
        """Test that the prompt template includes all commit categories."""
        with allure.step("Verify all categories are included in prompt template"):
            for category in COMMIT_CATEGORIES:
                check.is_in(f"'{category}'", commit.PROMPT_TEMPLATE)
            allure.attach(
                f"Categories verified: {len(COMMIT_CATEGORIES)}",
                "Categories Count",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Prompt template contains required placeholders")
    @allure.description(
        "Validates that the commit prompt template has all necessary placeholders and JSON structure"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("prompts", "templates", "placeholders")
    def test_prompt_template_has_placeholders(self) -> None:
        """Test that the prompt template has required placeholders."""
        with allure.step("Verify diff placeholder exists"):
            check.is_in("{diff}", commit.PROMPT_TEMPLATE)
        with allure.step("Verify JSON structure placeholders exist"):
            check.is_in('"changes"', commit.PROMPT_TEMPLATE)
            check.is_in('"trivial"', commit.PROMPT_TEMPLATE)
            check.is_in('"summary"', commit.PROMPT_TEMPLATE)
            check.is_in('"category"', commit.PROMPT_TEMPLATE)
            allure.attach(
                "Placeholders verified: {diff}, JSON fields",
                "Placeholders",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Prompt template includes example diffs and responses")
    @allure.description(
        "Validates that the commit prompt contains sufficient examples for AI training"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "templates", "examples")
    def test_prompt_template_includes_examples(self) -> None:
        """Test that the prompt includes example diffs and responses."""
        with allure.step("Verify example markers exist"):
            check.is_in("Example 1:", commit.PROMPT_TEMPLATE)
            check.is_in("Example 2:", commit.PROMPT_TEMPLATE)
            check.is_in("Example 3:", commit.PROMPT_TEMPLATE)
        with allure.step("Verify diff format examples exist"):
            check.is_in("diff --git", commit.PROMPT_TEMPLATE)
            check.is_in("@@", commit.PROMPT_TEMPLATE)
            check.is_in("+", commit.PROMPT_TEMPLATE)
            check.is_in("-", commit.PROMPT_TEMPLATE)
            allure.attach(
                "Examples verified: 3 examples with diff formats",
                "Examples",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Category list is properly formatted in prompt")
    @allure.description(
        "Validates that all commit categories are properly formatted within the prompt template"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "categories", "formatting")
    def test_category_list_for_prompt_format(self) -> None:
        """Test that the category list is properly formatted."""
        with allure.step("Verify all categories are properly formatted in prompt"):
            # The _CATEGORY_LIST_FOR_PROMPT should be accessible via the template
            check.is_true(all(f"'{cat}'" in commit.PROMPT_TEMPLATE for cat in COMMIT_CATEGORIES))
            allure.attach(
                f"All {len(COMMIT_CATEGORIES)} categories properly formatted",
                "Formatting",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Prompt contains valid JSON structure examples")
    @allure.description(
        "Validates that the prompt template includes properly formatted JSON examples"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "json", "structure")
    def test_prompt_json_structure_is_valid(self) -> None:
        """Test that example JSON in prompts has valid structure."""
        with allure.step("Verify JSON object markers exist"):
            check.is_in("{{", commit.PROMPT_TEMPLATE)
            check.is_in("}}", commit.PROMPT_TEMPLATE)
        with allure.step("Verify required JSON fields exist"):
            check.is_in('"changes":', commit.PROMPT_TEMPLATE)
            check.is_in('"trivial":', commit.PROMPT_TEMPLATE)
            allure.attach(
                "JSON structure validated with required fields",
                "JSON Structure",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Prompt contains clear instructions for AI")
    @allure.description(
        "Validates that the prompt provides comprehensive instructions for commit analysis"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("prompts", "instructions", "clarity")
    def test_prompt_instructions_are_clear(self) -> None:
        """Test that prompt includes clear instructions."""
        with allure.step("Verify instruction header exists"):
            check.is_in("Instructions:", commit.PROMPT_TEMPLATE)
        with allure.step("Verify specific instruction steps exist"):
            check.is_in("Analyze the Diff", commit.PROMPT_TEMPLATE)
            check.is_in("Identify Logical Changes", commit.PROMPT_TEMPLATE)
            check.is_in("Categorize Each Change", commit.PROMPT_TEMPLATE)
            check.is_in("Format as JSON", commit.PROMPT_TEMPLATE)
            allure.attach(
                "All instruction steps verified", "Instructions", allure.attachment_type.TEXT
            )


@allure.feature("Summary Module - Daily Prompts")
class TestDailySummaryPrompts:
    """Test suite for daily summary prompts."""

    @allure.story("Content Generation")
    @allure.title("Daily prompt template is properly defined")
    @allure.description(
        "Validates that the daily summary prompt template exists and has sufficient content"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("prompts", "daily", "templates")
    def test_prompt_template_exists(self) -> None:
        """Test that daily prompt template is defined."""
        with allure.step("Verify template exists and is not None"):
            check.is_not_none(daily.PROMPT_TEMPLATE)
        with allure.step("Verify template has sufficient content"):
            check.greater(len(daily.PROMPT_TEMPLATE), 100)
            allure.attach(
                f"Template length: {len(daily.PROMPT_TEMPLATE)}",
                "Template Info",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Daily prompt template contains required placeholders")
    @allure.description(
        "Validates that the daily prompt has all necessary placeholders for data injection"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("prompts", "daily", "placeholders")
    def test_prompt_template_has_placeholders(self) -> None:
        """Test that the prompt has required placeholders."""
        with allure.step("Verify full_log placeholder exists"):
            check.is_in("{full_log}", daily.PROMPT_TEMPLATE)
        with allure.step("Verify daily_diff placeholder exists"):
            check.is_in("{daily_diff}", daily.PROMPT_TEMPLATE)
            allure.attach(
                "Required placeholders: {full_log}, {daily_diff}",
                "Placeholders",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Daily prompt includes formatting rules")
    @allure.description("Validates that the daily prompt provides clear formatting guidelines")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "daily", "formatting")
    def test_prompt_formatting_rules(self) -> None:
        """Test that prompt includes formatting rules."""
        with allure.step("Verify formatting rules section exists"):
            check.is_in("Formatting Rules:", daily.PROMPT_TEMPLATE)
        with allure.step("Verify specific formatting instructions exist"):
            check.is_in("Do NOT include", daily.PROMPT_TEMPLATE)
            check.is_in("Structure your response", daily.PROMPT_TEMPLATE)
            allure.attach("Formatting rules verified", "Formatting", allure.attachment_type.TEXT)

    @allure.story("Content Generation")
    @allure.title("Daily prompt requests specific output structure")
    @allure.description("Validates that the daily prompt specifies the required output format")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "daily", "structure")
    def test_prompt_requests_structure(self) -> None:
        """Test that prompt requests specific structure."""
        with allure.step("Verify structure requirements are specified"):
            check.is_in("one-sentence title", daily.PROMPT_TEMPLATE)
            check.is_in("paragraph", daily.PROMPT_TEMPLATE)
            check.is_in("bulleted list", daily.PROMPT_TEMPLATE)
            allure.attach(
                "Structure requirements: title, paragraph, list",
                "Structure",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Daily prompt defines AI role and purpose")
    @allure.description(
        "Validates that the daily prompt establishes clear role definition for the AI"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "daily", "role")
    def test_prompt_role_definition(self) -> None:
        """Test that prompt defines the AI role."""
        with allure.step("Verify role definition exists"):
            check.is_in("technical project manager", daily.PROMPT_TEMPLATE)
        with allure.step("Verify purpose is stated"):
            check.is_in("summarizing", daily.PROMPT_TEMPLATE)
            allure.attach(
                "Role: technical project manager, Purpose: summarizing",
                "Role Definition",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Daily prompt has clear input sections")
    @allure.description("Validates that the daily prompt defines clear input data sections")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "daily", "sections")
    def test_prompt_input_sections(self) -> None:
        """Test that prompt has clear input sections."""
        with allure.step("Verify input sections are clearly defined"):
            check.is_in("Full Daily Git Log:", daily.PROMPT_TEMPLATE)
            check.is_in("Consolidated Daily Diff:", daily.PROMPT_TEMPLATE)
            check.is_in("Summary:", daily.PROMPT_TEMPLATE)
            allure.attach(
                "Input sections: Git Log, Daily Diff, Summary",
                "Sections",
                allure.attachment_type.TEXT,
            )


@allure.feature("Summary Module - Weekly Prompts")
class TestWeeklySummaryPrompts:
    """Test suite for weekly summary prompts."""

    @allure.story("Content Generation")
    @allure.title("Weekly prompt template is properly defined")
    @allure.description(
        "Validates that the weekly summary prompt template exists and has comprehensive content"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("prompts", "weekly", "templates")
    def test_prompt_template_exists(self) -> None:
        """Test that weekly prompt template is defined."""
        with allure.step("Verify template exists and is not None"):
            check.is_not_none(weekly.PROMPT_TEMPLATE)
        with allure.step("Verify template has comprehensive content"):
            check.greater(len(weekly.PROMPT_TEMPLATE), 200)
            allure.attach(
                f"Template length: {len(weekly.PROMPT_TEMPLATE)}",
                "Template Info",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Weekly prompt template contains all required placeholders")
    @allure.description(
        "Validates that the weekly prompt has all necessary placeholders for comprehensive data injection"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("prompts", "weekly", "placeholders")
    def test_prompt_template_has_placeholders(self) -> None:
        """Test that the prompt has all required placeholders."""
        with allure.step("Verify all required placeholders exist"):
            check.is_in("{history}", weekly.PROMPT_TEMPLATE)
            check.is_in("{commit_summaries}", weekly.PROMPT_TEMPLATE)
            check.is_in("{daily_summaries}", weekly.PROMPT_TEMPLATE)
            check.is_in("{weekly_diff}", weekly.PROMPT_TEMPLATE)
            allure.attach(
                "Placeholders: {history}, {commit_summaries}, {daily_summaries}, {weekly_diff}",
                "Placeholders",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Weekly prompt defines role and length requirements")
    @allure.description(
        "Validates that the weekly prompt establishes clear role and output length specifications"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "weekly", "requirements")
    def test_prompt_role_and_length(self) -> None:
        """Test that prompt defines role and length requirements."""
        with allure.step("Verify role definition exists"):
            check.is_in("product manager", weekly.PROMPT_TEMPLATE)
        with allure.step("Verify length requirement is specified"):
            check.is_in("500 words", weekly.PROMPT_TEMPLATE)
            allure.attach(
                "Role: product manager, Length: 500 words",
                "Requirements",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Weekly prompt includes comprehensive formatting rules")
    @allure.description("Validates that the weekly prompt provides detailed formatting guidelines")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "weekly", "formatting")
    def test_prompt_formatting_rules(self) -> None:
        """Test that prompt includes formatting rules."""
        with allure.step("Verify formatting rules section exists"):
            check.is_in("Formatting Rules:", weekly.PROMPT_TEMPLATE)
        with allure.step("Verify specific formatting instructions exist"):
            check.is_in("Do NOT include", weekly.PROMPT_TEMPLATE)
            check.is_in("Begin the response", weekly.PROMPT_TEMPLATE)
            allure.attach(
                "Formatting rules verified with specific instructions",
                "Formatting",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Weekly prompt specifies content requirements")
    @allure.description("Validates that the weekly prompt defines what content should be included")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "weekly", "content")
    def test_prompt_content_requirements(self) -> None:
        """Test that prompt specifies content requirements."""
        with allure.step("Verify content requirements section exists"):
            check.is_in("Content Requirements:", weekly.PROMPT_TEMPLATE)
        with allure.step("Verify specific content types are mentioned"):
            check.is_in("major additions", weekly.PROMPT_TEMPLATE)
            check.is_in("external dependencies", weekly.PROMPT_TEMPLATE)
            check.is_in("overall themes", weekly.PROMPT_TEMPLATE)
            allure.attach(
                "Content types: major additions, dependencies, themes",
                "Content Types",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Weekly prompt has clear analytical sections")
    @allure.description("Validates that the weekly prompt defines structured analysis sections")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "weekly", "structure")
    def test_prompt_sections(self) -> None:
        """Test that prompt has clear sections."""
        with allure.step("Verify main analysis sections exist"):
            check.is_in("HISTORICAL CONTEXT", weekly.PROMPT_TEMPLATE)
            check.is_in("CURRENT PERIOD ANALYSIS", weekly.PROMPT_TEMPLATE)
        with allure.step("Verify analysis level sections exist"):
            check.is_in("Micro-Level", weekly.PROMPT_TEMPLATE)
            check.is_in("Mezzo-Level", weekly.PROMPT_TEMPLATE)
            check.is_in("Macro-Level", weekly.PROMPT_TEMPLATE)
            allure.attach(
                "Sections: Historical Context, Current Analysis, Multi-level Analysis",
                "Sections",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Weekly prompt requests Notable Changes section")
    @allure.description(
        "Validates that the weekly prompt specifically requests notable changes highlighting"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "weekly", "notable-changes")
    def test_prompt_notable_changes_section(self) -> None:
        """Test that prompt requests Notable Changes section."""
        with allure.step("Verify Notable Changes section exists"):
            check.is_in("Notable Changes", weekly.PROMPT_TEMPLATE)
        with allure.step("Verify specific change types are mentioned"):
            check.is_in("major new features", weekly.PROMPT_TEMPLATE)
            check.is_in("security fixes", weekly.PROMPT_TEMPLATE)
            allure.attach(
                "Notable change types: features, security fixes",
                "Change Types",
                allure.attachment_type.TEXT,
            )

    @allure.story("Content Generation")
    @allure.title("Weekly prompt includes dependency analysis")
    @allure.description("Validates that the weekly prompt requests analysis of dependency changes")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("prompts", "weekly", "dependencies")
    def test_prompt_dependency_analysis(self) -> None:
        """Test that prompt mentions dependency analysis."""
        with allure.step("Verify dependency file is mentioned"):
            check.is_in("pyproject.toml", weekly.PROMPT_TEMPLATE)
        with allure.step("Verify dependency filtering instructions exist"):
            check.is_in(
                "Do not include testing or development dependencies", weekly.PROMPT_TEMPLATE
            )
            allure.attach(
                "Dependency analysis: pyproject.toml, exclude dev dependencies",
                "Dependencies",
                allure.attachment_type.TEXT,
            )


@allure.feature("Summary Module - Integration")
class TestSummaryModuleIntegration:
    """Test integration between summary modules."""

    @allure.story("Data Models")
    @allure.title("All summary modules have required template attributes")
    @allure.description("Validates that all summary modules properly export their prompt templates")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("modules", "templates", "attributes")
    def test_all_modules_use_final_typing(self) -> None:
        """Test that all prompt templates use Final typing."""
        with allure.step("Verify commit module attributes exist"):
            check.is_true(hasattr(commit, "PROMPT_TEMPLATE"))
        with allure.step("Verify daily and weekly module attributes exist"):
            check.is_true(hasattr(daily, "PROMPT_TEMPLATE"))
            check.is_true(hasattr(weekly, "PROMPT_TEMPLATE"))
            allure.attach(
                "All modules have required template attributes",
                "Attributes",
                allure.attachment_type.TEXT,
            )

    @allure.story("Data Models")
    @allure.title("All prompt templates are string types")
    @allure.description("Validates that all prompt templates are properly typed as strings")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("modules", "types", "validation")
    def test_prompts_are_strings(self) -> None:
        """Test that all prompts are string types."""
        with allure.step("Verify commit module prompts are strings"):
            check.is_instance(commit.PROMPT_TEMPLATE, str)
        with allure.step("Verify daily and weekly prompts are strings"):
            check.is_instance(daily.PROMPT_TEMPLATE, str)
            check.is_instance(weekly.PROMPT_TEMPLATE, str)
            allure.attach(
                "All prompt templates are string type",
                "Type Validation",
                allure.attachment_type.TEXT,
            )

    @allure.story("Data Models")
    @allure.title("All prompt templates have substantial content")
    @allure.description(
        "Validates that all prompt templates meet minimum content length requirements"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("modules", "content", "length")
    def test_prompts_are_non_empty(self) -> None:
        """Test that all prompts have substantial content."""
        with allure.step("Verify commit prompt lengths meet requirements"):
            check.greater(len(commit.PROMPT_TEMPLATE), 1000)
        with allure.step("Verify daily and weekly prompt lengths meet requirements"):
            check.greater(len(daily.PROMPT_TEMPLATE), 200)
            check.greater(len(weekly.PROMPT_TEMPLATE), 500)
            allure.attach(
                f"Lengths - Commit: {len(commit.PROMPT_TEMPLATE)}, Daily: {len(daily.PROMPT_TEMPLATE)}, Weekly: {len(weekly.PROMPT_TEMPLATE)}",
                "Content Lengths",
                allure.attachment_type.TEXT,
            )

    @allure.story("Data Models")
    @allure.title("Commit categories are consistently used across prompts")
    @allure.description(
        "Validates that all defined commit categories are properly integrated into prompts"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("modules", "categories", "consistency")
    def test_commit_categories_consistency(self) -> None:
        """Test that commit categories are consistently used."""
        with allure.step("Count categories present in commit prompt"):
            category_count = sum(
                1 for cat in COMMIT_CATEGORIES if f"'{cat}'" in commit.PROMPT_TEMPLATE
            )
        with allure.step("Verify all categories are included"):
            check.equal(category_count, len(COMMIT_CATEGORIES))
            allure.attach(
                f"Categories found: {category_count}/{len(COMMIT_CATEGORIES)}",
                "Category Consistency",
                allure.attachment_type.TEXT,
            )

    @allure.story("Data Models")
    @allure.title("All placeholders use consistent format across templates")
    @allure.description(
        "Validates that placeholder formatting is consistent across all prompt templates"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("modules", "placeholders", "consistency")
    def test_placeholder_format_consistency(self) -> None:
        """Test that all placeholders use consistent format."""
        with allure.step("Define expected placeholders for each template"):
            placeholders = [
                ("{diff}", commit.PROMPT_TEMPLATE),
                ("{full_log}", daily.PROMPT_TEMPLATE),
                ("{daily_diff}", daily.PROMPT_TEMPLATE),
                ("{history}", weekly.PROMPT_TEMPLATE),
                ("{commit_summaries}", weekly.PROMPT_TEMPLATE),
                ("{daily_summaries}", weekly.PROMPT_TEMPLATE),
                ("{weekly_diff}", weekly.PROMPT_TEMPLATE),
            ]
        with allure.step("Verify all placeholders exist in their respective templates"):
            for placeholder, template in placeholders:
                check.is_in(placeholder, template)
            allure.attach(
                f"Verified {len(placeholders)} placeholders for consistency",
                "Placeholder Validation",
                allure.attachment_type.TEXT,
            )
