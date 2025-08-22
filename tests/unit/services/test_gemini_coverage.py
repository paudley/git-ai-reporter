# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=duplicate-code,too-many-lines

"""Additional unit tests for gemini service to achieve comprehensive coverage."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from google import genai
from httpx import HTTPStatusError
import pytest
import pytest_check as check
from tenacity import RetryError

from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.services.gemini import GeminiClientConfig
from git_ai_reporter.services.gemini import GeminiClientError

# Constants for magic values
EXCEEDS_LIMIT_MSG = "exceeds limit"
SENDING_PROMPT_MSG = "Sending prompt"
RECEIVED_RESPONSE_MSG = "Received response"
EMPTY_RESPONSE_MSG = "empty response"


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


@pytest.fixture
def gemini_config() -> GeminiClientConfig:
    """Create a GeminiClientConfig for testing."""
    return GeminiClientConfig(
        model_tier1="gemini-2.5-flash",
        model_tier2="gemini-2.5-pro",
        model_tier3="gemini-2.5-pro",
        temperature=0.5,
        debug=False,
        api_timeout=1,  # Short timeout for tests
    )


@pytest.fixture
def gemini_config_debug() -> GeminiClientConfig:
    """Create a GeminiClientConfig with debug enabled."""
    return GeminiClientConfig(
        model_tier1="gemini-2.5-flash",
        model_tier2="gemini-2.5-pro",
        model_tier3="gemini-2.5-pro",
        temperature=0.5,
        debug=True,
        api_timeout=1,
    )


@pytest.fixture
def gemini_client(
    mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
) -> GeminiClient:
    """Create a GeminiClient instance for testing."""
    return GeminiClient(client=mock_genai_client, config=gemini_config)


@pytest.fixture
def gemini_client_debug(
    mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    gemini_config_debug: GeminiClientConfig,  # pylint: disable=redefined-outer-name
) -> GeminiClient:
    """Create a GeminiClient instance with debug enabled."""
    return GeminiClient(client=mock_genai_client, config=gemini_config_debug)


class TestGeminiCoverage:  # pylint: disable=too-many-public-methods
    """Test suite for achieving comprehensive coverage in gemini service."""

    # NOTE: Previous _trim_history, _trim_diff tests removed as these methods
    # have been replaced with data-preserving PromptFitter system that never
    # trims or loses data, per CLAUDE.md mandatory complete data integrity requirement.

    @pytest.mark.asyncio
    async def test_construct_weekly_prompt_debug_mode(
        self,
        gemini_client_debug: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test construct weekly prompt with debug output (line 138)."""
        # Setup token count response
        token_response = MagicMock()
        token_response.total_tokens = 500
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        with patch("git_ai_reporter.services.gemini.rprint") as mock_print:
            result = await gemini_client_debug._construct_and_fit_weekly_prompt(  # pylint: disable=protected-access
                "commits", "daily", "diff", "history"
            )

        check.is_not_none(result)
        mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_construct_weekly_prompt_debug_fitting(
        self,
        gemini_client_debug: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly prompt fitting with debug output (line 142)."""
        # First call over limit, second under
        token_response1 = MagicMock()
        token_response1.total_tokens = 2000000
        token_response2 = MagicMock()
        token_response2.total_tokens = 500000

        mock_genai_client.aio.models.count_tokens.side_effect = [
            token_response1,
            token_response2,
        ]

        with patch("git_ai_reporter.services.gemini.rprint") as mock_print:
            result = await gemini_client_debug._construct_and_fit_weekly_prompt(  # pylint: disable=protected-access
                "commits", "daily", "diff", "x" * 1000
            )

        check.is_not_none(result)
        # Should print debug messages about data-preserving fitting
        assert any(EXCEEDS_LIMIT_MSG in str(call) for call in mock_print.call_args_list)

    @pytest.mark.asyncio
    async def test_construct_weekly_prompt_max_iterations_exceeded(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly prompt when max iterations exceeded (line 159)."""
        # Always return over limit
        token_response = MagicMock()
        token_response.total_tokens = 2000000
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client._construct_and_fit_weekly_prompt(  # pylint: disable=protected-access
                "commits", "daily", "diff", "history"
            )

        check.is_in("Failed to fit prompt while preserving data integrity", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_generate_commit_analysis_debug_mode(
        self,
        gemini_client_debug: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis with debug output (lines 186-187, 208-209)."""
        response = MagicMock()
        response.text = '{"changes": [], "trivial": true}'
        mock_genai_client.aio.models.generate_content.return_value = response

        with patch("git_ai_reporter.services.gemini.rprint") as mock_print:
            result = await gemini_client_debug.generate_commit_analysis("test diff")

        check.is_instance(result, CommitAnalysis)
        # Should print prompt and response
        assert any(SENDING_PROMPT_MSG in str(call) for call in mock_print.call_args_list)
        assert any(RECEIVED_RESPONSE_MSG in str(call) for call in mock_print.call_args_list)

    @pytest.mark.asyncio
    async def test_generate_commit_analysis_empty_response_debug(
        self,
        gemini_client_debug: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test empty response handling with debug (lines 203-205)."""
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
            result = await gemini_client_debug.generate_commit_analysis("test diff")

        check.is_instance(result, CommitAnalysis)
        # Should print empty response warning
        assert any(EMPTY_RESPONSE_MSG in str(call) for call in mock_print.call_args_list)

    @pytest.mark.asyncio
    async def test_generate_commit_analysis_http_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test HTTP error handling (line 219)."""
        # Create mock request and response objects for HTTPStatusError
        mock_request = Mock()
        mock_response = Mock()
        mock_genai_client.aio.models.generate_content.side_effect = HTTPStatusError(
            "Bad request", request=mock_request, response=mock_response
        )

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_commit_analysis("test diff")

        check.is_in("HTTPStatusError", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_generate_commit_analysis_validation_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test validation error during commit analysis (line 268)."""
        response = MagicMock()
        response.text = '{"invalid": "json structure"}'

        # Fail 4 times with invalid structure
        mock_genai_client.aio.models.generate_content.side_effect = [
            response,
            response,
            response,
            response,
        ]

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_commit_analysis("test diff")

        check.is_in("Commit analysis failed after", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_generate_with_retry_empty_response(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _generate_with_retry with empty response (line 312)."""
        # First empty, then success
        response1 = MagicMock()
        response1.text = ""
        response2 = MagicMock()
        response2.text = "Valid response"

        mock_genai_client.aio.models.generate_content.side_effect = [
            response1,
            response2,
        ]

        result = await gemini_client._generate_with_retry(  # pylint: disable=protected-access
            "model", "prompt", 100
        )

        check.equal(result, "Valid response")

    @pytest.mark.asyncio
    async def test_generate_with_retry_client_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _generate_with_retry with client error (lines 314-315)."""
        # Create a generic exception that will be caught as an unexpected error
        error = RuntimeError("API Error")

        mock_genai_client.aio.models.generate_content.side_effect = error

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client._generate_with_retry(  # pylint: disable=protected-access
                "model", "prompt", 100
            )

        check.is_in("Unexpected error: RuntimeError", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_synthesize_daily_summary_token_limit_exceeded(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily summary with token limit exceeded (line 326)."""
        token_response = MagicMock()
        token_response.total_tokens = 2000000
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.synthesize_daily_summary("log", "diff")

        check.is_in("Failed to process any chunk pairs for daily summary", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_synthesize_daily_summary_retry_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily summary retry error (lines 332-342)."""
        # All attempts fail
        mock_genai_client.aio.models.generate_content.side_effect = [
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
        ]

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.synthesize_daily_summary("log", "diff")

        check.is_in("Daily summary failed after", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_generate_news_narrative_empty_response_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test news narrative with empty response error (line 353)."""
        # Setup token count OK
        token_response = MagicMock()
        token_response.total_tokens = 500
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # Generate fails with empty response
        response = MagicMock()
        response.text = ""
        mock_genai_client.aio.models.generate_content.side_effect = [
            response,
            response,
            response,
        ]  # All empty

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_news_narrative("c", "d", "w", "h")

        check.is_in("News narrative generation failed after", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_generate_news_narrative_retry_error_details(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test news narrative retry error with details (lines 355-363)."""
        # Setup token count OK
        token_response = MagicMock()
        token_response.total_tokens = 500
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # All attempts timeout
        mock_genai_client.aio.models.generate_content.side_effect = [
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
        ]

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_news_narrative("c", "d", "w", "h")

        error_msg = str(exc_info.value)
        check.is_in("News narrative generation failed after", error_msg)

    @pytest.mark.asyncio
    async def test_generate_changelog_entries_timeout_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test changelog entries with timeout error (lines 370-380)."""
        # All attempts timeout
        mock_genai_client.aio.models.generate_content.side_effect = [
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
        ]

        test_entries = [{"summary": "test", "category": "Bug Fix"}]
        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_changelog_entries(test_entries)

        check.is_in("Changelog generation failed after", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_generate_changelog_entries_retry_error_details(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test changelog retry error with prompt details (lines 370-380)."""
        # Create a RetryError by patching the retry decorator
        with patch("git_ai_reporter.services.gemini.retry") as mock_retry:
            # Make the retry raise RetryError immediately
            async def raise_retry_error(*_args: Any, **_kwargs: Any) -> Any:
                # Create a proper RetryError with last_attempt
                last_attempt = MagicMock()
                last_attempt.attempt_number = 3
                last_attempt.exception = lambda: Exception("Test error")
                error = RetryError(last_attempt)
                error.last_attempt = last_attempt
                raise error

            mock_retry.return_value = lambda f: raise_retry_error

            # Reinitialize client to pick up the patched retry
            # pylint: disable=protected-access
            client = GeminiClient(client=mock_genai_client, config=gemini_client._config)

            with pytest.raises(GeminiClientError) as exc_info:
                await client.generate_changelog_entries(
                    [{"summary": "test", "category": "Bug Fix"}]
                )

            error_msg = str(exc_info.value)
            check.is_in("failed after", error_msg)
            check.is_in("PROMPT SENT TO MODEL", error_msg)
