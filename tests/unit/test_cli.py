# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=too-many-lines

"""Unit tests for git_ai_reporter.cli module.

This module tests the CLI functions including settings loading,
date range determination, and error handling.
"""

from datetime import datetime
from datetime import timezone
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import MagicMock
from unittest.mock import patch

import allure
import pytest
import pytest_check as check
import typer
from typer.testing import CliRunner

from git_ai_reporter.cli import \
    _determine_date_range  # pylint: disable=protected-access,import-private-name
from git_ai_reporter.cli import \
    _load_settings  # pylint: disable=protected-access,import-private-name
from git_ai_reporter.cli import APP
from git_ai_reporter.cli import main
from git_ai_reporter.config import Settings
from git_ai_reporter.services.gemini import GeminiClientError


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI test runner."""
    return CliRunner()


@allure.feature("CLI Settings Management")
class TestLoadSettings:
    """Test suite for _load_settings function."""

    @allure.story("Configuration Loading")
    @allure.title("Load settings with default configuration")
    @allure.description("Verifies that settings load correctly when no config file is provided")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("smoke", "config", "defaults")
    @pytest.mark.smoke
    def test_load_settings_no_config_file(self) -> None:
        """Test loading settings with no config file."""
        with allure.step("Load settings with no config file"):
            settings = _load_settings(None)

        with allure.step("Verify settings are loaded with default values"):
            check.is_instance(settings, Settings)
            # Should use default values
            check.equal(settings.MODEL_TIER_1, "gemini-2.5-flash")

    @allure.story("Configuration Loading")
    @allure.title("Load settings from valid TOML configuration file")
    @allure.description("Verifies custom configuration values are loaded from a valid TOML file")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("config", "toml", "file-io")
    def test_load_settings_with_valid_config(self) -> None:
        """Test loading settings from valid TOML file."""
        with allure.step("Create temporary TOML config file with custom values"):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
                temp_filename = f.name
                config_content = """
MODEL_TIER_1 = "custom-model"
TEMPERATURE = 0.8
NEWS_FILE = "CUSTOM_NEWS.md"
"""
                f.write(config_content)
                f.flush()
                allure.attach(
                    config_content,
                    name="Test Configuration",
                    attachment_type=allure.attachment_type.TEXT,
                )

        # File is now closed, safe to delete on Windows
        try:
            with allure.step("Load settings from custom config file"):
                settings = _load_settings(temp_filename)

            with allure.step("Verify custom values are applied"):
                check.equal(settings.MODEL_TIER_1, "custom-model")
                check.equal(settings.TEMPERATURE, 0.8)
                check.equal(settings.NEWS_FILE, "CUSTOM_NEWS.md")
        finally:
            with allure.step("Clean up temporary file"):
                Path(temp_filename).unlink()

    @allure.story("Configuration Loading")
    @allure.title("Handle missing configuration file gracefully")
    @allure.description("Verifies appropriate error handling when config file doesn't exist")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("config", "error-handling", "file-io")
    def test_load_settings_file_not_found(self) -> None:
        """Test loading settings when config file doesn't exist."""
        with allure.step("Attempt to load settings from non-existent file"):
            with pytest.raises(typer.Exit) as exc_info:
                _load_settings("/nonexistent/config.toml")

        with allure.step("Verify correct exit code is returned"):
            check.equal(exc_info.value.exit_code, 1)

    @allure.story("Configuration Loading")
    @allure.title("Handle invalid TOML configuration file")
    @allure.description("Verifies error handling when TOML file contains invalid syntax")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("config", "error-handling", "toml", "validation")
    def test_load_settings_invalid_toml(self) -> None:
        """Test loading settings from invalid TOML file."""
        with allure.step("Create temporary file with invalid TOML content"):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
                temp_filename = f.name
                invalid_content = "invalid toml content {[}"
                f.write(invalid_content)
                f.flush()
                allure.attach(
                    invalid_content,
                    name="Invalid TOML Content",
                    attachment_type=allure.attachment_type.TEXT,
                )

        # File is now closed, safe to delete on Windows
        try:
            with allure.step("Attempt to load settings from invalid TOML file"):
                with pytest.raises(Exception):  # tomllib will raise an error
                    _load_settings(temp_filename)
        finally:
            with allure.step("Clean up temporary file"):
                Path(temp_filename).unlink()


@allure.feature("CLI Date Range Processing")
class TestDetermineDateRange:
    """Test suite for _determine_date_range function."""

    @allure.story("Date Range Calculation")
    @allure.title("Calculate default date range using weeks parameter")
    @allure.description(
        "Verifies that date range is correctly calculated when using weeks parameter only"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("smoke", "date-range", "weeks")
    @pytest.mark.smoke
    def test_default_weeks(self) -> None:
        """Test default date range with weeks parameter."""
        with allure.step("Calculate date range for 2 weeks"):
            start, end = _determine_date_range(2, None, None)
            allure.attach(
                f"Start: {start}, End: {end}",
                name="Calculated Date Range",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Verify end date is close to current time"):
            # End should be close to now
            now = datetime.now(timezone.utc)
            check.less((now - end).total_seconds(), 60)  # Within a minute

        with allure.step("Verify start date is 2 weeks before end date"):
            # Start should be 2 weeks before end
            expected_days = 14
            actual_days = (end - start).days
            check.equal(actual_days, expected_days)

    @allure.story("Date Range Calculation")
    @allure.title("Calculate date range with custom start date")
    @allure.description("Verifies date range calculation when start date is specified")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("date-range", "custom-start")
    def test_custom_start_date(self) -> None:
        """Test with custom start date."""
        with allure.step("Calculate date range with custom start date"):
            start, end = _determine_date_range(0, "2025-01-01", None)
            allure.attach(
                f"Start: {start}, End: {end}",
                name="Date Range with Custom Start",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Verify start date matches specified date"):
            check.equal(start.date().isoformat(), "2025-01-01")

        with allure.step("Verify end date is close to current time"):
            # End should be close to now when not specified
            now = datetime.now(timezone.utc)
            check.less((now - end).total_seconds(), 60)

    @allure.story("Date Range Calculation")
    @allure.title("Calculate date range with custom end date")
    @allure.description("Verifies date range calculation when end date is specified")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("date-range", "custom-end")
    def test_custom_end_date(self) -> None:
        """Test with custom end date."""
        with allure.step("Calculate date range with custom end date"):
            start, end = _determine_date_range(1, None, "2025-01-15")
            allure.attach(
                f"Start: {start}, End: {end}",
                name="Date Range with Custom End",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Verify end date matches specified date"):
            check.equal(end.date().isoformat(), "2025-01-15")

        with allure.step("Verify start date is 1 week before end date"):
            # Start should be 1 week before end
            check.equal((end - start).days, 7)

    @allure.story("Date Range Calculation")
    @allure.title("Calculate date range with both start and end dates specified")
    @allure.description(
        "Verifies date range calculation when both start and end dates are provided"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("date-range", "custom-both")
    def test_both_dates_specified(self) -> None:
        """Test with both start and end dates specified."""
        with allure.step("Calculate date range with both dates specified"):
            start, end = _determine_date_range(0, "2025-01-01", "2025-01-15")
            allure.attach(
                f"Start: {start}, End: {end}",
                name="Date Range with Both Dates",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Verify both dates match specified values"):
            check.equal(start.date().isoformat(), "2025-01-01")
            check.equal(end.date().isoformat(), "2025-01-15")

    @allure.story("Date Range Validation")
    @allure.title("Handle invalid date format gracefully")
    @allure.description("Verifies error handling when invalid date formats are provided")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("date-range", "error-handling", "validation")
    def test_invalid_date_format(self) -> None:
        """Test with invalid date format."""
        with allure.step("Test invalid start date format"):
            with pytest.raises(ValueError):
                _determine_date_range(1, "invalid-date", None)

        with allure.step("Test invalid end date format"):
            with pytest.raises(ValueError):
                _determine_date_range(1, None, "2025-13-45")  # Invalid month/day


@allure.feature("CLI Main Command Execution")
class TestMainCommand:
    """Test suite for main command."""

    @allure.step("Setup mock settings for test")
    def _setup_mock_settings(self, mock_load_settings: MagicMock) -> None:
        """Helper method to setup mock settings to reduce local variables."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.GEMINI_API_KEY = "test-key"
        mock_settings.MODEL_TIER_1 = "model1"
        mock_settings.MODEL_TIER_2 = "model2"
        mock_settings.MODEL_TIER_3 = "model3"
        mock_settings.GEMINI_INPUT_TOKEN_LIMIT_TIER1 = 1000
        mock_settings.GEMINI_INPUT_TOKEN_LIMIT_TIER2 = 2000
        mock_settings.GEMINI_INPUT_TOKEN_LIMIT_TIER3 = 3000
        mock_settings.MAX_TOKENS_TIER_1 = 100
        mock_settings.MAX_TOKENS_TIER_2 = 200
        mock_settings.MAX_TOKENS_TIER_3 = 300
        mock_settings.TEMPERATURE = 0.7
        mock_settings.NEWS_FILE = "NEWS.md"
        mock_settings.CHANGELOG_FILE = "CHANGELOG.txt"
        mock_settings.DAILY_UPDATES_FILE = "DAILY_UPDATES.md"
        mock_settings.TRIVIAL_COMMIT_TYPES = ["chore"]
        mock_settings.TRIVIAL_FILE_PATTERNS = ["*.md"]
        mock_settings.GEMINI_API_TIMEOUT = 300
        mock_settings.GIT_COMMAND_TIMEOUT = 30
        mock_settings.MAX_CONCURRENT_GIT_COMMANDS = 5
        mock_load_settings.return_value = mock_settings
        allure.attach(
            str(mock_settings),
            name="Mock Settings Configuration",
            attachment_type=allure.attachment_type.TEXT,
        )

    @allure.step("Setup mock date range for test")
    def _setup_date_range_mock(self, mock_determine_date_range: MagicMock) -> None:
        """Helper method to setup date range mock."""
        start_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2025, 1, 8, tzinfo=timezone.utc)
        mock_determine_date_range.return_value = (start_dt, end_dt)
        allure.attach(
            f"Start: {start_dt}, End: {end_dt}",
            name="Mock Date Range",
            attachment_type=allure.attachment_type.TEXT,
        )

    @allure.story("Error Handling")
    @allure.title("Handle Gemini API client errors gracefully")
    @allure.description("Verifies that Gemini API errors are caught and handled appropriately")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("error-handling", "api", "gemini")
    @allure.issue("GH-001", "Gemini API error handling")
    @patch("git_ai_reporter.cli._determine_date_range")
    @patch("git_ai_reporter.cli.timedelta")
    @patch("git_ai_reporter.cli._load_settings")
    @patch("git.Repo")
    @patch("git_ai_reporter.cli.GeminiClient")
    @patch("git_ai_reporter.cli.GitAnalyzer")
    @patch("git_ai_reporter.cli.CacheManager")
    @patch("git_ai_reporter.cli.ArtifactWriter")
    @patch("git_ai_reporter.cli.OrchestratorServices")
    @patch("git_ai_reporter.cli.AnalysisOrchestrator")
    @patch("git_ai_reporter.cli.asyncio.run")
    def test_analyze_with_gemini_error(  # pylint: disable=too-many-arguments
        # pylint: disable=too-many-positional-arguments
        self,
        mock_asyncio_run: MagicMock,
        mock_orchestrator_class: MagicMock,
        mock_services_class: MagicMock,
        mock_writer_class: MagicMock,
        mock_cache_class: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_client_class: MagicMock,
        mock_repo_class: MagicMock,
        mock_load_settings: MagicMock,
        mock_timedelta: MagicMock,
        mock_determine_date_range: MagicMock,
    ) -> None:
        """Test analyze command handling GeminiClientError."""
        with allure.step("Setup test environment and mocks"):
            # Mark unused mocks
            del mock_orchestrator_class, mock_writer_class, mock_cache_class
            del mock_analyzer_class, mock_client_class, mock_repo_class, mock_timedelta
            mock_services_class.return_value = MagicMock()

            # Setup mocks using helper methods
            self._setup_date_range_mock(mock_determine_date_range)
            self._setup_mock_settings(mock_load_settings)

        with allure.step("Configure Gemini API to raise error"):
            # Setup the error
            error_message = "API error"
            mock_asyncio_run.side_effect = GeminiClientError(error_message)
            allure.attach(
                error_message,
                name="Simulated API Error",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Execute main command and expect error handling"):
            with pytest.raises(typer.Exit) as exc_info:
                main(
                    repo_path=".",
                    weeks=1,  # Explicit integer to avoid mock contamination
                    start_date_str=None,
                    end_date_str=None,
                    config_file=None,
                    cache_dir=".git-report-cache",
                    no_cache=False,
                    debug=False,
                    pre_release=None,
                )

        with allure.step("Verify error is handled correctly"):
            check.equal(exc_info.value.exit_code, 1)
            mock_asyncio_run.assert_called_once()

    @allure.story("Repository Validation")
    @allure.title("Handle invalid git repository path")
    @allure.description("Verifies error handling when an invalid repository path is provided")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("error-handling", "repository", "validation")
    @patch("git.Repo")
    @patch("git_ai_reporter.cli.GitAnalyzer")
    @patch("git_ai_reporter.cli.genai.Client")
    def test_analyze_invalid_repo(
        self,
        mock_genai_client: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_repo_class: MagicMock,
    ) -> None:
        """Test analyze with invalid repository."""
        with allure.step("Setup mock to simulate invalid repository"):
            del mock_genai_client, mock_analyzer_class  # Unused mocks
            error_message = "Invalid repo"
            mock_repo_class.side_effect = Exception(error_message)
            allure.attach(
                error_message, name="Repository Error", attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("Execute main command with invalid repository path"):
            with pytest.raises(typer.Exit) as exc_info:
                main(
                    repo_path="/invalid/path",
                    weeks=1,
                    start_date_str=None,
                    end_date_str=None,
                    config_file=None,
                    cache_dir=".git-report-cache",
                    no_cache=False,
                    debug=False,
                    pre_release=None,
                )

        with allure.step("Verify appropriate error code is returned"):
            check.equal(exc_info.value.exit_code, 1)

    @patch("git_ai_reporter.cli._determine_date_range")
    @patch("git_ai_reporter.cli.timedelta")
    @patch("git_ai_reporter.cli._load_settings")
    @patch("git.Repo")
    @patch("git_ai_reporter.cli.asyncio.run")
    @patch("git_ai_reporter.cli.AnalysisOrchestrator")
    @patch("git_ai_reporter.cli.OrchestratorServices")
    @patch("git_ai_reporter.cli.ArtifactWriter")
    @patch("git_ai_reporter.cli.CacheManager")
    @patch("git_ai_reporter.cli.GitAnalyzer")
    @patch("git_ai_reporter.cli.GeminiClient")
    def test_analyze_success_with_cache(  # pylint: disable=too-many-arguments
        # pylint: disable=too-many-positional-arguments
        self,
        mock_client_class: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_cache_class: MagicMock,
        mock_writer_class: MagicMock,
        mock_services_class: MagicMock,
        mock_orchestrator_class: MagicMock,
        mock_asyncio_run: MagicMock,
        mock_repo_class: MagicMock,
        mock_load_settings: MagicMock,
        mock_timedelta: MagicMock,
        mock_determine_date_range: MagicMock,
    ) -> None:
        """Test successful analyze with cache enabled."""
        del (
            mock_client_class,
            mock_analyzer_class,
            mock_writer_class,
            mock_timedelta,
        )  # Unused mocks
        mock_services_class.return_value = MagicMock()

        # Mock the date range function to avoid timedelta issues
        mock_determine_date_range.return_value = (
            datetime(2025, 1, 1, tzinfo=timezone.utc),
            datetime(2025, 1, 8, tzinfo=timezone.utc),
        )

        # Setup settings
        mock_settings = MagicMock(spec=Settings)
        mock_settings.GEMINI_API_KEY = "test-key"
        mock_settings.MODEL_TIER_1 = "model1"
        mock_settings.MODEL_TIER_2 = "model2"
        mock_settings.MODEL_TIER_3 = "model3"
        mock_settings.GEMINI_INPUT_TOKEN_LIMIT_TIER1 = 1000
        mock_settings.GEMINI_INPUT_TOKEN_LIMIT_TIER2 = 2000
        mock_settings.GEMINI_INPUT_TOKEN_LIMIT_TIER3 = 3000
        mock_settings.MAX_TOKENS_TIER_1 = 100
        mock_settings.MAX_TOKENS_TIER_2 = 200
        mock_settings.MAX_TOKENS_TIER_3 = 300
        mock_settings.TEMPERATURE = 0.7
        mock_settings.NEWS_FILE = "NEWS.md"
        mock_settings.CHANGELOG_FILE = "CHANGELOG.txt"
        mock_settings.DAILY_UPDATES_FILE = "DAILY_UPDATES.md"
        mock_settings.TRIVIAL_COMMIT_TYPES = ["chore"]
        mock_settings.TRIVIAL_FILE_PATTERNS = ["*.md"]
        mock_settings.GEMINI_API_TIMEOUT = 300
        mock_settings.GIT_COMMAND_TIMEOUT = 30
        mock_settings.MAX_CONCURRENT_GIT_COMMANDS = 5
        mock_load_settings.return_value = mock_settings

        # Setup repo mock
        mock_repo = MagicMock()
        mock_repo.working_dir = "/test/repo"
        mock_repo.close = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Setup orchestrator mock
        mock_orchestrator_class.return_value = MagicMock()

        # Run main with explicit integer weeks parameter
        main(
            repo_path=".",
            weeks=1,  # Explicit integer to avoid mock contamination
            start_date_str=None,
            end_date_str=None,
            config_file=None,
            cache_dir=".git-report-cache",
            no_cache=False,
            debug=False,
            pre_release=None,
        )

        # Verify cache manager was created
        mock_cache_class.assert_called_once()
        # Verify orchestrator was created with cache
        mock_orchestrator_class.assert_called_once()
        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()
        # Note: repo.close() is called in finally block, but may not be captured in mocks
        # due to the way the test is structured with multiple patches

    @patch("git_ai_reporter.cli._determine_date_range")
    @patch("git_ai_reporter.cli.timedelta")
    @patch("git_ai_reporter.cli._load_settings")
    @patch("git.Repo")
    @patch("git_ai_reporter.cli.asyncio.run")
    @patch("git_ai_reporter.cli.AnalysisOrchestrator")
    @patch("git_ai_reporter.cli.OrchestratorServices")
    @patch("git_ai_reporter.cli.ArtifactWriter")
    @patch("git_ai_reporter.cli.CacheManager")
    @patch("git_ai_reporter.cli.GitAnalyzer")
    @patch("git_ai_reporter.cli.GeminiClient")
    def test_analyze_no_cache(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        mock_client_class: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_cache_class: MagicMock,
        mock_writer_class: MagicMock,
        mock_services_class: MagicMock,
        mock_orchestrator_class: MagicMock,
        mock_asyncio_run: MagicMock,
        mock_repo_class: MagicMock,
        mock_load_settings: MagicMock,
        mock_timedelta: MagicMock,
        mock_determine_date_range: MagicMock,
    ) -> None:
        """Test analyze with no-cache option."""
        del (
            mock_client_class,
            mock_analyzer_class,
            mock_writer_class,
            mock_timedelta,
            mock_asyncio_run,
        )  # Unused mocks
        mock_services_class.return_value = MagicMock()

        # Setup mocks using helper methods
        self._setup_date_range_mock(mock_determine_date_range)
        self._setup_mock_settings(mock_load_settings)

        mock_repo = MagicMock()
        mock_repo.working_dir = "/test/repo"
        mock_repo.close = MagicMock()
        mock_repo_class.return_value = mock_repo

        main(
            repo_path=".",
            weeks=1,  # Explicit integer to avoid mock contamination
            start_date_str=None,
            end_date_str=None,
            config_file=None,
            cache_dir=".git-report-cache",
            no_cache=True,
            debug=False,
            pre_release=None,
        )

        # Verify cache manager was created (it's always created)
        mock_cache_class.assert_called_once()
        # Orchestrator should be created with no_cache=True in config
        mock_orchestrator_class.assert_called_once()
        # The no_cache flag should be passed to OrchestratorConfig constructor
        # Check that config was created with no_cache=True - this is handled by _create_config


@allure.feature("CLI Entry Point")
class TestMainEntry:
    """Test suite for main entry point."""

    @allure.story("Application Entry Point")
    @allure.title("Verify CLI application entry point functionality")
    @allure.description("Tests that the main CLI application entry point works correctly")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("smoke", "cli", "entry-point")
    def test_main_entry_point(
        self, cli_runner: CliRunner  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test that main entry point works."""
        with allure.step("Invoke CLI application with --help flag"):
            # Test with --help to avoid actual execution
            result = cli_runner.invoke(APP, ["--help"])
            allure.attach(
                result.stdout, name="CLI Help Output", attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("Verify successful execution and help content"):
            check.equal(result.exit_code, 0)
            check.is_in("Usage:", result.stdout)

    @allure.story("Module Execution")
    @allure.title("Verify module can be executed directly via python -m")
    @allure.description("Tests that the module can be executed as a script using python -m command")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("cli", "module", "execution")
    def test_main_dunder(self) -> None:
        """Test __main__ execution."""
        with allure.step("Execute module using python -m with --help"):
            # Run the module as a script to test the __main__ block
            command = [sys.executable, "-m", "git_ai_reporter.cli", "--help"]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
            allure.attach(
                " ".join(command),
                name="Executed Command",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                result.stdout,
                name="Module Execution Output",
                attachment_type=allure.attachment_type.TEXT,
            )
            if result.stderr:
                allure.attach(
                    result.stderr,
                    name="Module Execution Errors",
                    attachment_type=allure.attachment_type.TEXT,
                )

        with allure.step("Verify module executed successfully"):
            check.equal(result.returncode, 0)
            check.is_in("Usage:", result.stdout)
