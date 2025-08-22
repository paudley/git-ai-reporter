# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for git_ai_reporter.summaries modules.

This module tests the prompt templates and constants in the summary modules.
"""

import pytest_check as check

from git_ai_reporter.models import COMMIT_CATEGORIES
from git_ai_reporter.summaries import commit
from git_ai_reporter.summaries import daily
from git_ai_reporter.summaries import weekly


class TestCommitSummaryPrompts:
    """Test suite for commit summary prompts."""

    def test_prompt_template_includes_all_categories(self) -> None:
        """Test that the prompt template includes all commit categories."""
        for category in COMMIT_CATEGORIES:
            check.is_in(f"'{category}'", commit.PROMPT_TEMPLATE)

    def test_prompt_template_has_placeholders(self) -> None:
        """Test that the prompt template has required placeholders."""
        check.is_in("{diff}", commit.PROMPT_TEMPLATE)
        # Check for example JSON structure
        check.is_in('"changes"', commit.PROMPT_TEMPLATE)
        check.is_in('"trivial"', commit.PROMPT_TEMPLATE)
        check.is_in('"summary"', commit.PROMPT_TEMPLATE)
        check.is_in('"category"', commit.PROMPT_TEMPLATE)

    def test_prompt_template_includes_examples(self) -> None:
        """Test that the prompt includes example diffs and responses."""
        # Check for example markers
        check.is_in("Example 1:", commit.PROMPT_TEMPLATE)
        check.is_in("Example 2:", commit.PROMPT_TEMPLATE)
        check.is_in("Example 3:", commit.PROMPT_TEMPLATE)
        # Check for diff examples
        check.is_in("diff --git", commit.PROMPT_TEMPLATE)
        check.is_in("@@", commit.PROMPT_TEMPLATE)
        check.is_in("+", commit.PROMPT_TEMPLATE)
        check.is_in("-", commit.PROMPT_TEMPLATE)

    def test_triviality_prompt_exists(self) -> None:
        """Test that the triviality prompt is defined."""
        check.is_in("trivial", commit.TRIVIALITY_PROMPT.lower())
        check.is_in("{diff}", commit.TRIVIALITY_PROMPT)
        check.is_in("true", commit.TRIVIALITY_PROMPT)
        check.is_in("false", commit.TRIVIALITY_PROMPT)

    def test_triviality_prompt_has_examples(self) -> None:
        """Test that triviality prompt includes examples."""
        check.is_in("TRIVIAL changes", commit.TRIVIALITY_PROMPT)
        check.is_in("NON-TRIVIAL changes", commit.TRIVIALITY_PROMPT)
        check.is_in("typos", commit.TRIVIALITY_PROMPT.lower())
        check.is_in("bug", commit.TRIVIALITY_PROMPT.lower())

    def test_category_list_for_prompt_format(self) -> None:
        """Test that the category list is properly formatted."""
        # The _CATEGORY_LIST_FOR_PROMPT should be accessible via the template
        check.is_true(all(f"'{cat}'" in commit.PROMPT_TEMPLATE for cat in COMMIT_CATEGORIES))

    def test_prompt_json_structure_is_valid(self) -> None:
        """Test that example JSON in prompts has valid structure."""
        # Check for proper JSON object markers (template uses {{ for examples)
        check.is_in("{{", commit.PROMPT_TEMPLATE)
        check.is_in("}}", commit.PROMPT_TEMPLATE)
        # Check for required JSON fields
        check.is_in('"changes":', commit.PROMPT_TEMPLATE)
        check.is_in('"trivial":', commit.PROMPT_TEMPLATE)

    def test_prompt_instructions_are_clear(self) -> None:
        """Test that prompt includes clear instructions."""
        check.is_in("Instructions:", commit.PROMPT_TEMPLATE)
        check.is_in("Analyze the Diff", commit.PROMPT_TEMPLATE)
        check.is_in("Identify Logical Changes", commit.PROMPT_TEMPLATE)
        check.is_in("Categorize Each Change", commit.PROMPT_TEMPLATE)
        check.is_in("Format as JSON", commit.PROMPT_TEMPLATE)


class TestDailySummaryPrompts:
    """Test suite for daily summary prompts."""

    def test_prompt_template_exists(self) -> None:
        """Test that daily prompt template is defined."""
        check.is_not_none(daily.PROMPT_TEMPLATE)
        check.greater(len(daily.PROMPT_TEMPLATE), 100)

    def test_prompt_template_has_placeholders(self) -> None:
        """Test that the prompt has required placeholders."""
        check.is_in("{full_log}", daily.PROMPT_TEMPLATE)
        check.is_in("{daily_diff}", daily.PROMPT_TEMPLATE)

    def test_prompt_formatting_rules(self) -> None:
        """Test that prompt includes formatting rules."""
        check.is_in("Formatting Rules:", daily.PROMPT_TEMPLATE)
        check.is_in("Do NOT include", daily.PROMPT_TEMPLATE)
        check.is_in("Structure your response", daily.PROMPT_TEMPLATE)

    def test_prompt_requests_structure(self) -> None:
        """Test that prompt requests specific structure."""
        check.is_in("one-sentence title", daily.PROMPT_TEMPLATE)
        check.is_in("paragraph", daily.PROMPT_TEMPLATE)
        check.is_in("bulleted list", daily.PROMPT_TEMPLATE)

    def test_prompt_role_definition(self) -> None:
        """Test that prompt defines the AI role."""
        check.is_in("technical project manager", daily.PROMPT_TEMPLATE)
        check.is_in("summarizing", daily.PROMPT_TEMPLATE)

    def test_prompt_input_sections(self) -> None:
        """Test that prompt has clear input sections."""
        check.is_in("Full Daily Git Log:", daily.PROMPT_TEMPLATE)
        check.is_in("Consolidated Daily Diff:", daily.PROMPT_TEMPLATE)
        check.is_in("Summary:", daily.PROMPT_TEMPLATE)


class TestWeeklySummaryPrompts:
    """Test suite for weekly summary prompts."""

    def test_prompt_template_exists(self) -> None:
        """Test that weekly prompt template is defined."""
        check.is_not_none(weekly.PROMPT_TEMPLATE)
        check.greater(len(weekly.PROMPT_TEMPLATE), 200)

    def test_prompt_template_has_placeholders(self) -> None:
        """Test that the prompt has all required placeholders."""
        check.is_in("{history}", weekly.PROMPT_TEMPLATE)
        check.is_in("{commit_summaries}", weekly.PROMPT_TEMPLATE)
        check.is_in("{daily_summaries}", weekly.PROMPT_TEMPLATE)
        check.is_in("{weekly_diff}", weekly.PROMPT_TEMPLATE)

    def test_prompt_role_and_length(self) -> None:
        """Test that prompt defines role and length requirements."""
        check.is_in("product manager", weekly.PROMPT_TEMPLATE)
        check.is_in("500 words", weekly.PROMPT_TEMPLATE)

    def test_prompt_formatting_rules(self) -> None:
        """Test that prompt includes formatting rules."""
        check.is_in("Formatting Rules:", weekly.PROMPT_TEMPLATE)
        check.is_in("Do NOT include", weekly.PROMPT_TEMPLATE)
        check.is_in("Begin the response", weekly.PROMPT_TEMPLATE)

    def test_prompt_content_requirements(self) -> None:
        """Test that prompt specifies content requirements."""
        check.is_in("Content Requirements:", weekly.PROMPT_TEMPLATE)
        check.is_in("major additions", weekly.PROMPT_TEMPLATE)
        check.is_in("external dependencies", weekly.PROMPT_TEMPLATE)
        check.is_in("overall themes", weekly.PROMPT_TEMPLATE)

    def test_prompt_sections(self) -> None:
        """Test that prompt has clear sections."""
        check.is_in("HISTORICAL CONTEXT", weekly.PROMPT_TEMPLATE)
        check.is_in("CURRENT PERIOD ANALYSIS", weekly.PROMPT_TEMPLATE)
        check.is_in("Micro-Level", weekly.PROMPT_TEMPLATE)
        check.is_in("Mezzo-Level", weekly.PROMPT_TEMPLATE)
        check.is_in("Macro-Level", weekly.PROMPT_TEMPLATE)

    def test_prompt_notable_changes_section(self) -> None:
        """Test that prompt requests Notable Changes section."""
        check.is_in("Notable Changes", weekly.PROMPT_TEMPLATE)
        check.is_in("major new features", weekly.PROMPT_TEMPLATE)
        check.is_in("security fixes", weekly.PROMPT_TEMPLATE)

    def test_prompt_dependency_analysis(self) -> None:
        """Test that prompt mentions dependency analysis."""
        check.is_in("pyproject.toml", weekly.PROMPT_TEMPLATE)
        check.is_in("Do not include testing or development dependencies", weekly.PROMPT_TEMPLATE)


class TestSummaryModuleIntegration:
    """Test integration between summary modules."""

    def test_all_modules_use_final_typing(self) -> None:
        """Test that all prompt templates use Final typing."""
        # This is checked at import time, but verify the attributes exist
        check.is_true(hasattr(commit, "PROMPT_TEMPLATE"))
        check.is_true(hasattr(commit, "TRIVIALITY_PROMPT"))
        check.is_true(hasattr(daily, "PROMPT_TEMPLATE"))
        check.is_true(hasattr(weekly, "PROMPT_TEMPLATE"))

    def test_prompts_are_strings(self) -> None:
        """Test that all prompts are string types."""
        check.is_instance(commit.PROMPT_TEMPLATE, str)
        check.is_instance(commit.TRIVIALITY_PROMPT, str)
        check.is_instance(daily.PROMPT_TEMPLATE, str)
        check.is_instance(weekly.PROMPT_TEMPLATE, str)

    def test_prompts_are_non_empty(self) -> None:
        """Test that all prompts have substantial content."""
        check.greater(len(commit.PROMPT_TEMPLATE), 1000)
        check.greater(len(commit.TRIVIALITY_PROMPT), 100)
        check.greater(len(daily.PROMPT_TEMPLATE), 200)
        check.greater(len(weekly.PROMPT_TEMPLATE), 500)

    def test_commit_categories_consistency(self) -> None:
        """Test that commit categories are consistently used."""
        # Count categories in the prompt
        category_count = sum(1 for cat in COMMIT_CATEGORIES if f"'{cat}'" in commit.PROMPT_TEMPLATE)
        check.equal(category_count, len(COMMIT_CATEGORIES))

    def test_placeholder_format_consistency(self) -> None:
        """Test that all placeholders use consistent format."""
        # All should use single braces for format strings
        placeholders = [
            ("{diff}", commit.PROMPT_TEMPLATE),
            ("{diff}", commit.TRIVIALITY_PROMPT),
            ("{full_log}", daily.PROMPT_TEMPLATE),
            ("{daily_diff}", daily.PROMPT_TEMPLATE),
            ("{history}", weekly.PROMPT_TEMPLATE),
            ("{commit_summaries}", weekly.PROMPT_TEMPLATE),
            ("{daily_summaries}", weekly.PROMPT_TEMPLATE),
            ("{weekly_diff}", weekly.PROMPT_TEMPLATE),
        ]
        for placeholder, template in placeholders:
            check.is_in(placeholder, template)
