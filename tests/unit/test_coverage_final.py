# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=too-many-lines

"""Final coverage tests to reach comprehensive coverage."""

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from git import GitCommandError
from git import NoSuchPathError
from google import genai
from httpx import HTTPStatusError
import pytest
import typer

from git_ai_reporter.cli import _setup  # pylint: disable=protected-access,import-private-name
from git_ai_reporter.config import Settings
from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.services.gemini import GeminiClientConfig
from git_ai_reporter.utils import json_helpers

# Constants for magic values
ERROR_CALLING_GEMINI_MSG = "Error calling Gemini API"
INVALID_JSON_MSG = "Invalid JSON"


class TestCoverage100:
    """Tests to achieve comprehensive coverage."""

    def test_cli_git_command_error(self) -> None:
        """Test CLI handling of GitCommandError (lines 84-85)."""
        settings = Settings(GEMINI_API_KEY="test-key")

        with patch("git_ai_reporter.cli.Repo") as mock_repo:
            mock_repo.side_effect = GitCommandError("git error")

            with pytest.raises(typer.Exit):
                _setup(".", settings, ".cache", False, False)

    def test_cli_no_such_path_error(self) -> None:
        """Test CLI handling of NoSuchPathError (lines 84-85)."""
        settings = Settings(GEMINI_API_KEY="test-key")

        with patch("git_ai_reporter.cli.Repo") as mock_repo:
            mock_repo.side_effect = NoSuchPathError("path error")

            with pytest.raises(typer.Exit):
                _setup(".", settings, ".cache", False, False)

    @pytest.mark.asyncio
    async def test_gemini_client_error_line_349(self) -> None:
        """Test GeminiClientError on line 349."""
        # Create a mock client
        mock_client = MagicMock(spec=genai.Client)
        mock_client.aio = MagicMock()
        mock_client.aio.models = MagicMock()

        # Mock HTTPStatusError
        mock_request = Mock()
        mock_response = Mock()
        mock_client.aio.models.generate_content = MagicMock(
            side_effect=HTTPStatusError("Bad request", request=mock_request, response=mock_response)
        )

        config = GeminiClientConfig()
        client = GeminiClient(mock_client, config)

        with pytest.raises(Exception) as exc_info:
            await client._generate_with_retry(  # pylint: disable=protected-access
                "model", "prompt", 100
            )

        assert ERROR_CALLING_GEMINI_MSG in str(exc_info.value)

    def test_json_helpers_error_lines_53_55(self) -> None:
        """Test json_helpers error handling (lines 53-55)."""
        with patch("tolerantjson.tolerate") as mock_tolerate:
            mock_tolerate.side_effect = ValueError("Invalid")

            with pytest.raises(Exception) as exc_info:
                json_helpers.safe_json_decode('{"test": true}')

            assert INVALID_JSON_MSG in str(exc_info.value)
