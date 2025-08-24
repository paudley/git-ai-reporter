# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Additional tests for CLI to improve coverage."""

from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock

import allure
import pytest_check as check

from git_ai_reporter.analysis.git_analyzer import GitAnalyzer
from git_ai_reporter.cli import _get_full_repo_date_range  # pylint: disable=import-private-name


@allure.feature("CLI Operations - Coverage")
class TestCLICoverage:
    """Tests to cover specific uncovered lines in CLI."""

    @allure.story("CLI Operations")
    @allure.title("CLI handles repository with no first commit gracefully")
    @allure.description(
        "Validates that _get_full_repo_date_range falls back to 1 year when first commit date is None"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("cli", "date-range", "fallback")
    def test_get_full_repo_date_range_no_first_commit(self) -> None:
        """Test _get_full_repo_date_range when first commit date is None - covers line 213."""
        with allure.step("Setup mock GitAnalyzer with no first commit date"):
            mock_git_analyzer = MagicMock(spec=GitAnalyzer)
            mock_git_analyzer.get_first_commit_date.return_value = None

        with allure.step("Get full repository date range"):
            start_date, end_date = _get_full_repo_date_range(mock_git_analyzer)

        with allure.step("Verify fallback to 1 year ago"):
            expected_start = end_date - timedelta(weeks=52)
            # Allow some tolerance for timing differences in test execution
            check.less_equal(abs((start_date - expected_start).total_seconds()), 5)
            check.is_instance(end_date, datetime)
            allure.attach(
                f"Date range: {start_date} to {end_date}",
                "Date Range Fallback",
                allure.attachment_type.TEXT,
            )
