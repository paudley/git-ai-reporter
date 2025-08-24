# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=too-many-lines

"""Final coverage tests to reach comprehensive coverage."""

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import allure
from git import GitCommandError
from git import NoSuchPathError
from google import genai
from httpx import HTTPStatusError
import pytest
import typer

from git_ai_reporter import models
from git_ai_reporter.cli import _setup  # pylint: disable=protected-access,import-private-name
from git_ai_reporter.config import Settings
from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.services.gemini import GeminiClientConfig
from git_ai_reporter.utils import json_helpers

# Constants for magic values
ERROR_CALLING_GEMINI_MSG = "Error calling Gemini API"
INVALID_JSON_MSG = "Invalid JSON"


@allure.feature("Coverage - Final Tests")
class TestCoverage100:
    """Tests to achieve comprehensive coverage."""

    @allure.story("Data Models")
    @allure.title("Core modules can be imported successfully")
    @allure.description("Smoke test to verify all core modules and classes are importable")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("smoke", "imports", "core")
    @pytest.mark.smoke
    def test_core_imports(self) -> None:
        """Smoke test: Verify core modules can be imported."""
        with allure.step("Verify models module attributes exist"):
            assert hasattr(models, "Change")
            assert hasattr(models, "CommitAnalysis")
        with allure.step("Verify other core modules are callable"):
            assert callable(Settings)
            assert hasattr(json_helpers, "safe_json_decode")
            assert hasattr(json_helpers, "safe_json_encode")
            allure.attach(
                "All core modules imported successfully", "Import Test", allure.attachment_type.TEXT
            )

    @allure.story("CLI Operations")
    @allure.title("CLI handles GitCommandError appropriately")
    @allure.description("Validates that CLI setup handles GitCommandError by exiting gracefully")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("cli", "error-handling", "git")
    def test_cli_git_command_error(self) -> None:
        """Test CLI handling of GitCommandError (lines 84-85)."""
        with allure.step("Setup test settings"):
            settings = Settings(GEMINI_API_KEY="test-key")

        with allure.step("Mock Repo to raise GitCommandError"):
            with patch("git_ai_reporter.cli.Repo") as mock_repo:
                mock_repo.side_effect = GitCommandError("git error")

                with allure.step("Verify typer.Exit is raised"):
                    with pytest.raises(typer.Exit):
                        _setup(".", settings, ".cache", False, False)
                    allure.attach(
                        "GitCommandError handled with typer.Exit",
                        "CLI Error Handling",
                        allure.attachment_type.TEXT,
                    )

    @allure.story("CLI Operations")
    @allure.title("CLI handles NoSuchPathError appropriately")
    @allure.description("Validates that CLI setup handles NoSuchPathError by exiting gracefully")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("cli", "error-handling", "path")
    def test_cli_no_such_path_error(self) -> None:
        """Test CLI handling of NoSuchPathError (lines 84-85)."""
        with allure.step("Setup test settings"):
            settings = Settings(GEMINI_API_KEY="test-key")

        with allure.step("Mock Repo to raise NoSuchPathError"):
            with patch("git_ai_reporter.cli.Repo") as mock_repo:
                mock_repo.side_effect = NoSuchPathError("path error")

                with allure.step("Verify typer.Exit is raised"):
                    with pytest.raises(typer.Exit):
                        _setup(".", settings, ".cache", False, False)
                    allure.attach(
                        "NoSuchPathError handled with typer.Exit",
                        "CLI Error Handling",
                        allure.attachment_type.TEXT,
                    )

    @allure.story("Service Integration")
    @allure.title("Gemini client handles HTTP status errors appropriately")
    @allure.description("Validates that GeminiClient raises appropriate exceptions on HTTP errors")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("gemini", "http-error", "service")
    @pytest.mark.asyncio
    async def test_gemini_client_error_line_349(self) -> None:
        """Test GeminiClientError on line 349."""
        with allure.step("Create mock Gemini client"):
            mock_client = MagicMock(spec=genai.Client)
            mock_client.aio = MagicMock()
            mock_client.aio.models = MagicMock()

        with allure.step("Setup HTTPStatusError simulation"):
            mock_request = Mock()
            mock_response = Mock()
            mock_client.aio.models.generate_content = MagicMock(
                side_effect=HTTPStatusError(
                    "Bad request", request=mock_request, response=mock_response
                )
            )

        with allure.step("Initialize GeminiClient and test error handling"):
            config = GeminiClientConfig()
            client = GeminiClient(mock_client, config)

            with pytest.raises(Exception) as exc_info:
                await client._generate_with_retry(  # pylint: disable=protected-access
                    "model", "prompt", 100
                )

        with allure.step("Verify error message contains expected text"):
            assert ERROR_CALLING_GEMINI_MSG in str(exc_info.value)
            allure.attach(
                f"Error message: {exc_info.value}", "Gemini Error", allure.attachment_type.TEXT
            )

    @allure.story("File Operations")
    @allure.title("JSON helpers handle parsing errors appropriately")
    @allure.description(
        "Validates that json_helpers raises appropriate exceptions on parsing errors"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "parsing", "error-handling")
    def test_json_helpers_error_lines_53_55(self) -> None:
        """Test json_helpers error handling (lines 53-55)."""
        with allure.step("Mock tolerantjson to raise ValueError"):
            with patch("tolerantjson.tolerate") as mock_tolerate:
                mock_tolerate.side_effect = ValueError("Invalid")

                with allure.step("Test JSON parsing error handling"):
                    with pytest.raises(Exception) as exc_info:
                        json_helpers.safe_json_decode('{"test": true}')

                with allure.step("Verify error message contains expected text"):
                    assert INVALID_JSON_MSG in str(exc_info.value)
                    allure.attach(
                        f"JSON error: {exc_info.value}",
                        "JSON Error Handling",
                        allure.attachment_type.TEXT,
                    )
