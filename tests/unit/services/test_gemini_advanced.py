# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=duplicate-code

"""Advanced unit tests for git_ai_reporter.services.gemini module.

This module tests error handling, concurrency, and edge cases.
Part of the split from the original large test_gemini.py file.
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from google import genai
from httpx import ConnectError
from httpx import HTTPStatusError
from httpx import Request
from httpx import Response
from pydantic import ValidationError
import pytest
import pytest_check as check
from tenacity import AttemptManager
from tenacity import RetryError
# Import constants from basic test file
from test_gemini_basic import EMPTY_RESPONSE_MSG

from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.services.gemini import GeminiClientConfig
from git_ai_reporter.services.gemini import GeminiClientError

# =============================================================================
# MODULE-LEVEL PATCHES (apply to all tests)
# =============================================================================

# Apply asyncio marker to all tests in this module
pytestmark = pytest.mark.asyncio


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


# =============================================================================
# TEST CLASSES
# =============================================================================


class TestErrorHandling:
    """Consolidated error handling tests."""

    async def test_http_errors(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test HTTP error handling."""
        # Create mock request and response objects for HTTPStatusError
        mock_request = Mock()
        test_response = Mock()
        mock_genai_client.aio.models.generate_content.side_effect = HTTPStatusError(
            "Bad request", request=mock_request, response=test_response
        )

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_commit_analysis("test diff")

        check.is_in("HTTPStatusError", str(exc_info.value))

    async def test_generate_with_retry_http_status_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _generate_with_retry with HTTP status error."""
        # Create mock HTTP error with proper request/response
        mock_request = Request("GET", "http://example.com")
        test_response = Response(400)
        http_error = HTTPStatusError("Bad request", request=mock_request, response=test_response)

        mock_genai_client.aio.models.generate_content.side_effect = http_error

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client._generate_with_retry(  # pylint: disable=protected-access
                "model", "prompt", 100
            )

        check.is_in("HTTPStatusError", str(exc_info.value))

    async def test_generate_with_retry_generic_exception(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _generate_with_retry with generic exception."""
        # Create a generic exception that will be caught as an unexpected error
        error = RuntimeError("API Error")

        mock_genai_client.aio.models.generate_content.side_effect = error

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client._generate_with_retry(  # pylint: disable=protected-access
                "model", "prompt", 100
            )

        check.is_in("Unexpected error: RuntimeError", str(exc_info.value))

    async def test_commit_analysis_generic_exception(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis with generic exception."""
        # Setup mock to raise exception 4 times (initial + 3 retries)
        mock_genai_client.aio.models.generate_content.side_effect = [
            Exception("API error"),
            Exception("API error"),
            Exception("API error"),
            Exception("API error"),
        ]

        # Should raise GeminiClientError after retries
        with pytest.raises(GeminiClientError):
            await gemini_client.generate_commit_analysis("Test diff")

    async def test_empty_response_with_debug(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test empty response handling with debug output."""
        # Skip test if not in debug mode
        if not gemini_client._config.debug:  # pylint: disable=protected-access
            pytest.skip("Test only applies to debug mode")

        # Need 4 attempts (3 empty for retries, 1 success)
        response1 = MagicMock()
        response1.text = ""
        response2 = MagicMock()
        response2.text = ""
        response3 = MagicMock()
        response3.text = ""
        response4 = MagicMock()
        response4.text = '{"changes": [], "trivial": true}'

        mock_genai_client.aio.models.generate_content.side_effect = [
            response1,
            response2,
            response3,
            response4,
        ]

        with patch("git_ai_reporter.services.gemini.rprint") as mock_print:
            result = await gemini_client.generate_commit_analysis("test diff")

        check.is_instance(result, CommitAnalysis)
        # Should print empty response warning
        assert any(EMPTY_RESPONSE_MSG in str(call) for call in mock_print.call_args_list)

    async def test_retry_error_with_details(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test retry error handling with prompt details."""
        # Make generate_content always timeout
        mock_genai_client.aio.models.generate_content.side_effect = asyncio.TimeoutError()

        # Patch the retry decorator to capture the actual RetryError
        async def mock_generate_with_retry(*_args: Any, **_kwargs: Any) -> str:
            # Create a proper RetryError
            last_attempt = MagicMock(spec=AttemptManager)
            last_attempt.attempt_number = 3
            last_attempt.exception = lambda: asyncio.TimeoutError("Timed out")

            error = RetryError(last_attempt)
            error.last_attempt = last_attempt
            raise error

        with patch.object(gemini_client, "_generate_with_retry", mock_generate_with_retry):
            with pytest.raises(GeminiClientError) as exc_info:
                await gemini_client.synthesize_daily_summary("log", "diff")

        error_msg = str(exc_info.value)
        check.is_in("Daily summary failed after 3 attempts", error_msg)
        check.is_in("PROMPT SENT TO MODEL", error_msg)


class TestConcurrency:
    """Concurrency and performance tests."""

    async def test_concurrent_analyses(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test concurrent commit analyses."""
        # Setup mock
        response = MagicMock()
        response.text = '{"changes": [], "trivial": true}'
        mock_genai_client.aio.models.generate_content.return_value = response

        # Run multiple analyses concurrently
        tasks = [gemini_client.generate_commit_analysis(f"Diff {i}") for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        check.equal(len(results), 5)
        for result in results:
            check.is_instance(result, CommitAnalysis)

    async def test_async_timeout_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test proper async timeout handling with nested retry logic."""
        # All 4 attempts timeout (tests the double retry decorator scenario)
        mock_genai_client.aio.models.generate_content.side_effect = [
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
        ]

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_commit_analysis("test diff")

        # Should mention timeout in error
        check.is_in("TimeoutError", str(exc_info.value))

    async def test_token_counting_error_fallback(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name,unused-argument
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test token counting fallback when count_tokens fails."""
        # Import here to avoid issues with private class access  # pylint: disable=import-outside-toplevel
        from git_ai_reporter.services.gemini import \
            _GeminiTokenCounter  # pylint: disable=import-private-name

        # Mock count_tokens to raise various errors
        mock_genai_client.aio.models.count_tokens.side_effect = [
            HTTPStatusError("API error", request=Mock(), response=Mock()),
            ConnectError("Connection error"),
            ValidationError.from_exception_data("test", []),
            ValueError("Value error"),
            OSError("OS error"),
        ]

        # Test that it falls back to character-based estimation
        counter = _GeminiTokenCounter(mock_genai_client, "gemini-2.5-flash")

        # Each call should fallback to len(content) // 4
        test_content = "This is test content"  # 20 chars = 5 tokens
        for _ in range(5):
            result = await counter.count_tokens(test_content)
            check.equal(
                result, 5
            )  # TokenCount is a NewType based on int, so 20 chars / 4 = 5 tokens

    async def test_empty_diff_special_case(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test empty diff handling without going through API."""
        result = await gemini_client.generate_commit_analysis("")

        check.is_instance(result, CommitAnalysis)
        check.equal(len(result.changes), 0)
        check.is_true(result.trivial)

        # Should not have called the API for empty diff
        mock_genai_client.aio.models.generate_content.assert_not_called()

    async def test_weekly_summary_error_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name,unused-argument
    ) -> None:
        """Test weekly summary generation error handling."""
        # Create RetryError for weekly summary failure

        last_attempt = MagicMock(spec=AttemptManager)
        last_attempt.attempt_number = 3
        last_attempt.exception = lambda: HTTPStatusError(
            "API error", request=Mock(), response=Mock()
        )

        error = RetryError(last_attempt)
        error.last_attempt = last_attempt

        # Mock the internal method to raise RetryError
        with patch.object(gemini_client, "_generate_with_retry", side_effect=error):
            with pytest.raises(GeminiClientError) as exc_info:
                await gemini_client.generate_news_narrative("commits", "daily", "diff", "history")

            error_msg = str(exc_info.value)
            check.is_in("News narrative generation failed after 3 attempts", error_msg)
            check.is_in("HTTPStatusError", error_msg)

    async def test_changelog_generation_error_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name,unused-argument
    ) -> None:
        """Test changelog generation error handling."""
        # Create RetryError for changelog generation failure

        last_attempt = MagicMock(spec=AttemptManager)
        last_attempt.attempt_number = 3
        last_attempt.exception = lambda: ConnectError("Connection failed")

        error = RetryError(last_attempt)
        error.last_attempt = last_attempt

        # Mock the internal method to raise RetryError
        with patch.object(gemini_client, "_generate_with_retry", side_effect=error):
            with pytest.raises(GeminiClientError) as exc_info:
                await gemini_client.generate_changelog_entries(
                    [{"category": "Added", "summary": "New feature"}]
                )

            error_msg = str(exc_info.value)
            check.is_in("Changelog generation failed after 3 attempts", error_msg)
            check.is_in("ConnectError", error_msg)
