# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=duplicate-code

"""Basic unit tests for git_ai_reporter.services.gemini module.

This module tests GeminiClient initialization, configuration, and basic functionality.
Part of the split from the original large test_gemini.py file.
"""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from google import genai
import pytest
import pytest_check as check

from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.services.gemini import GeminiClientConfig

# Constants for magic values used in tests
EXCEEDS_LIMIT_MSG = "exceeds limit"
SENDING_PROMPT_MSG = "Sending prompt"
RECEIVED_RESPONSE_MSG = "Received response"
EMPTY_RESPONSE_MSG = "empty response"
TIMEOUT_ERROR_MSG = "timeout_error"
TIMEOUT_ERRORS_MSG = "timeout_errors"
EMPTY_RESPONSES_MSG = "empty_responses"
FITTING_FAILED_MSG = "Fitting failed"
EXCEEDS_TARGET_MSG = "exceeds target"

# =============================================================================
# MODULE-LEVEL PATCHES (apply to all tests)
# =============================================================================

# No async tests in this module - asyncio marker not needed


@pytest.fixture(autouse=True)
def patch_wait_exponential_and_sleep():
    """Patch wait_exponential and asyncio.sleep globally to eliminate retry delays in all tests."""
    with (
        patch(
            "git_ai_reporter.services.gemini.wait_exponential", return_value=lambda _retry_state: 0
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        yield


# =============================================================================
# SHARED FIXTURES
# =============================================================================


@pytest.fixture
def mock_genai_client() -> MagicMock:
    """Create a mock google.genai.Client."""
    client = MagicMock(spec=genai.Client)
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock()

    # Setup count_tokens to return a proper response
    token_response = MagicMock()
    token_response.total_tokens = 100  # Default small token count
    client.aio.models.count_tokens = AsyncMock(return_value=token_response)

    return client


@pytest.fixture(params=[False, True], ids=["normal", "debug"])
def gemini_config(request) -> GeminiClientConfig:
    """Create a GeminiClientConfig for testing, parametrized for debug mode."""
    return GeminiClientConfig(
        model_tier1="gemini-2.5-flash",
        model_tier2="gemini-2.5-pro",
        model_tier3="gemini-2.5-pro",
        temperature=0.5,
        debug=request.param,
        api_timeout=1,  # Short timeout for tests
    )


@pytest.fixture
def gemini_client(
    mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
) -> GeminiClient:
    """Create a GeminiClient instance for testing."""
    return GeminiClient(client=mock_genai_client, config=gemini_config)


@pytest.fixture
def valid_response() -> MagicMock:
    """Create a mock GenerateContentResponse with valid JSON."""
    response = MagicMock()
    response.text = (
        '{"changes": [{"summary": "Add feature", "category": "New Feature"}], "trivial": false}'
    )
    return response


@pytest.fixture
def mock_empty_response() -> MagicMock:
    """Create a mock response with empty text."""
    response = MagicMock()
    response.text = ""
    return response


@pytest.fixture
def mock_malformed_json_response() -> MagicMock:
    """Create a mock response with malformed JSON."""
    response = MagicMock()
    response.text = "```json\n{invalid json}\n```"
    return response


# =============================================================================
# TEST CLASSES
# =============================================================================


class TestGeminiClientInitialization:
    """Tests for client setup and configuration."""

    @pytest.mark.smoke
    def test_init(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test GeminiClient initialization."""
        client = GeminiClient(client=mock_genai_client, config=gemini_config)
        check.equal(client._client, mock_genai_client)  # pylint: disable=protected-access
        check.equal(client._config, gemini_config)  # pylint: disable=protected-access
        check.equal(client._debug, gemini_config.debug)  # pylint: disable=protected-access
        check.equal(
            client._api_timeout, gemini_config.api_timeout
        )  # pylint: disable=protected-access

    @pytest.mark.smoke
    def test_config_defaults(self) -> None:
        """Test GeminiClientConfig default values."""
        config = GeminiClientConfig()
        check.equal(config.model_tier1, "gemini-2.5-flash")
        check.equal(config.model_tier2, "gemini-2.5-pro")
        check.equal(config.model_tier3, "gemini-2.5-pro")
        check.equal(config.temperature, 0.5)
        check.equal(config.api_timeout, 600)
        check.is_false(config.debug)
