# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=duplicate-code

"""Consolidated unit tests for git_ai_reporter.services.gemini module.

This module tests the GeminiClient class which handles three-tier AI processing
for commit analysis, daily synthesis, and weekly narrative generation.

Consolidates tests from:
- test_gemini_client.py (basic functionality)
- test_gemini_coverage.py (coverage-focused tests)
- test_gemini_comprehensive_coverage.py (final coverage gaps)
- test_gemini_final_coverage.py (comprehensive coverage)
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from google import genai
from google.genai import errors
from httpx import ConnectError
from httpx import HTTPStatusError
from httpx import Request
from httpx import Response
from pydantic import ValidationError
import pytest
import pytest_check as check
from tenacity import AttemptManager
from tenacity import RetryError

from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.services.gemini import GeminiClientConfig
from git_ai_reporter.services.gemini import GeminiClientError

# Constants for magic values used in tests
EXCEEDS_LIMIT_MSG = "exceeds limit"
SENDING_PROMPT_MSG = "Sending prompt"
RECEIVED_RESPONSE_MSG = "Received response"
EMPTY_RESPONSE_MSG = "empty response"
# =============================================================================
# MODULE-LEVEL PATCHES (apply to all tests)
# =============================================================================

# Apply asyncio marker to all tests in this module
pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
def patch_wait_exponential_and_sleep():
    """Patch wait_exponential and asyncio.sleep globally to eliminate retry delays in all tests."""
    with patch("git_ai_reporter.services.gemini.wait_exponential", return_value=lambda retry_state: 0), \
         patch("asyncio.sleep", new_callable=AsyncMock):
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
def mock_response() -> MagicMock:
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
        check.equal(client._api_timeout, gemini_config.api_timeout)  # pylint: disable=protected-access

    def test_config_defaults(self) -> None:
        """Test GeminiClientConfig default values."""
        config = GeminiClientConfig()
        check.equal(config.model_tier1, "gemini-2.5-flash")
        check.equal(config.model_tier2, "gemini-2.5-pro")
        check.equal(config.model_tier3, "gemini-2.5-pro")
        check.equal(config.temperature, 0.5)
        check.equal(config.api_timeout, 600)
        check.is_false(config.debug)
class TestCommitAnalysis:
    """Tests for generate_commit_analysis method."""
    async def test_successful_analysis(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        mock_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful commit analysis."""
        # Setup mock
        mock_genai_client.aio.models.generate_content.return_value = mock_response

        # Call method
        result = await gemini_client.generate_commit_analysis("Test commit diff")

        # Verify
        check.is_instance(result, CommitAnalysis)
        check.equal(len(result.changes), 1)
        check.equal(result.changes[0].summary, "Add feature")
        check.equal(result.changes[0].category, "New Feature")
        check.is_false(result.trivial)
        mock_genai_client.aio.models.generate_content.assert_called_once()
    async def test_empty_diff_handling(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of empty commit diffs."""
        # Setup mock for empty response
        response = MagicMock()
        response.text = '{"changes": [], "trivial": true}'
        mock_genai_client.aio.models.generate_content.return_value = response

        # Test empty commit diff
        result = await gemini_client.generate_commit_analysis("")
        check.is_instance(result, CommitAnalysis)
        check.equal(len(result.changes), 0)
        check.is_true(result.trivial)
    @pytest.mark.parametrize("json_text,error_type", [
        ("```json\n{invalid json}\n```", "malformed JSON"),
        ("not valid json at all {", "invalid JSON"),
        ('{"invalid": "json structure"}', "validation error"),
    ])
    async def test_json_parsing_errors(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        json_text: str,
        error_type: str,  # pylint: disable=unused-argument
    ) -> None:
        """Test handling of various JSON parsing errors."""
        # Setup mock with invalid JSON - will fail 4 times
        response = MagicMock()
        response.text = json_text
        mock_genai_client.aio.models.generate_content.side_effect = [
            response, response, response, response,  # All fail
        ]

        # Should raise after retries
        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_commit_analysis("Test diff")

        check.is_in("Commit analysis failed after", str(exc_info.value))
    async def test_validation_error_handling(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        mock_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of Pydantic validation errors."""
        # First call: raises ValidationError, second call: succeeds
        mock_genai_client.aio.models.generate_content.side_effect = [
            ValidationError.from_exception_data("test", []),
            mock_response,
        ]

        # Should retry and succeed
        result = await gemini_client.generate_commit_analysis("Test diff")

        check.is_instance(result, CommitAnalysis)
        check.equal(len(result.changes), 1)
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 2)
    @pytest.mark.parametrize("error_type,side_effect", [
        ("connection", [ConnectError("Connection failed"), ConnectError("Connection failed")]),
        ("timeout", [asyncio.TimeoutError(), asyncio.TimeoutError()]),
    ])
    async def test_retry_logic(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        mock_response: MagicMock,  # pylint: disable=redefined-outer-name
        error_type: str,  # pylint: disable=unused-argument
        side_effect: list,
    ) -> None:
        """Test retry mechanism on various failures."""
        # Setup mock to fail then succeed
        mock_genai_client.aio.models.generate_content.side_effect = side_effect + [mock_response]

        # Should eventually succeed
        result = await gemini_client.generate_commit_analysis("Test diff")

        # Verify successful result after retries
        check.is_instance(result, CommitAnalysis)
        check.equal(len(result.changes), 1)
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)
    async def test_retry_exhaustion(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test behavior when max retries are exceeded."""
        # Setup mock to always fail with retryable error (4 times)
        mock_genai_client.aio.models.generate_content.side_effect = [
            ConnectError("Persistent connection error"),
            ConnectError("Persistent connection error"),
            ConnectError("Persistent connection error"),
            ConnectError("Persistent connection error"),
        ]

        # Should raise after exhausting retries
        with pytest.raises(GeminiClientError):
            await gemini_client.generate_commit_analysis("Test diff")

        # Should have tried 4 times (initial + 3 retries)
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 4)
    async def test_prompt_fitting_overflow(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis when prompt fitting fails due to size."""
        # Always return over limit tokens
        token_response = MagicMock()
        token_response.total_tokens = 2000000
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_commit_analysis("x" * 100000)

        # With prompt fitting, error message includes fitting details
        error_msg = str(exc_info.value)
        check.is_true(
            "Fitting failed" in error_msg or "exceeds target" in error_msg,
            f"Expected fitting error message, got: {error_msg}"
        )
    async def test_debug_mode_output(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        mock_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis with debug output when debug mode is enabled."""
        # Skip test if not in debug mode
        if not gemini_client._config.debug:  # pylint: disable=protected-access
            pytest.skip("Test only applies to debug mode")

        mock_genai_client.aio.models.generate_content.return_value = mock_response

        with patch("git_ai_reporter.services.gemini.rprint") as mock_print:
            result = await gemini_client.generate_commit_analysis("test diff")

        check.is_instance(result, CommitAnalysis)
        # Should print prompt and response in debug mode
        assert any(SENDING_PROMPT_MSG in str(call) for call in mock_print.call_args_list)
        assert any(RECEIVED_RESPONSE_MSG in str(call) for call in mock_print.call_args_list)
    async def test_json_with_markdown_fence(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of JSON wrapped in markdown fence."""
        # Setup mock with fenced JSON
        response = MagicMock()
        response.text = """```json
{
    "changes": [
        {"summary": "Add feature", "category": "New Feature"}
    ],
    "trivial": false
}
```"""
        mock_genai_client.aio.models.generate_content.return_value = response

        # Should parse correctly
        result = await gemini_client.generate_commit_analysis("Test diff")

        check.is_instance(result, CommitAnalysis)
        check.equal(len(result.changes), 1)
        check.equal(result.changes[0].summary, "Add feature")
class TestDailySummary:
    """Tests for synthesize_daily_summary method."""
    async def test_successful_synthesis(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful daily activity synthesis."""
        # Setup mock
        response = MagicMock()
        response.text = "### 2025-01-07 - Major Progress\\n\\nSignificant development today..."
        mock_genai_client.aio.models.generate_content.return_value = response

        # Call method
        result = await gemini_client.synthesize_daily_summary(
            "Full log content", "Daily diff content"
        )

        # Verify
        check.is_instance(result, str)
        check.is_in("Major Progress", result)
        mock_genai_client.aio.models.generate_content.assert_called_once()
    async def test_empty_input_handling(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of empty inputs for daily summary."""
        # Setup for text response
        response = MagicMock()
        response.text = "No activity"
        mock_genai_client.aio.models.generate_content.return_value = response

        # Test empty daily summaries
        daily_result = await gemini_client.synthesize_daily_summary("", "")
        check.is_instance(daily_result, str)
    async def test_token_limit_exceeded(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily summary with token limit exceeded."""
        token_response = MagicMock()
        token_response.total_tokens = 2000000
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.synthesize_daily_summary("log", "diff")

        check.is_in("Failed to process any chunk pairs for daily summary", str(exc_info.value))
    async def test_chunked_processing(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful chunked processing for daily summary."""
        # Setup token count that requires chunking
        token_response = MagicMock()
        token_response.total_tokens = 150000  # Over single chunk limit but processable
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # Setup successful response
        response = MagicMock()
        response.text = "Chunked daily summary"
        mock_genai_client.aio.models.generate_content.return_value = response

        result = await gemini_client.synthesize_daily_summary("long log content", "long diff")

        check.is_instance(result, str)
        check.is_in("Chunked daily summary", result)
    @pytest.mark.parametrize("error_scenario", [
        "timeout_errors",
        "empty_responses",
    ])
    async def test_retry_logic(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        error_scenario: str,
    ) -> None:
        """Test daily summary retry logic for various error scenarios."""
        if error_scenario == "timeout_errors":
            # All attempts timeout
            mock_genai_client.aio.models.generate_content.side_effect = [
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
            ]
        elif error_scenario == "empty_responses":
            # All attempts return empty
            response = MagicMock()
            response.text = ""
            mock_genai_client.aio.models.generate_content.side_effect = [
                response, response, response,
            ]

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.synthesize_daily_summary("log", "diff")

        check.is_in("Daily summary failed after", str(exc_info.value))
    async def test_timeout_then_success(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily summary with timeout then success."""
        # Need 2 timeouts then success (retry decorator has 3 attempts total)
        response = MagicMock()
        response.text = "Daily summary"

        mock_genai_client.aio.models.generate_content.side_effect = [
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            response,
        ]

        result = await gemini_client.synthesize_daily_summary("log", "diff")

        check.equal(result, "Daily summary")
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)
    async def test_debug_mode_output(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily summary with debug output when token limit exceeded."""
        # Skip test if not in debug mode
        if not gemini_client._config.debug:  # pylint: disable=protected-access
            pytest.skip("Test only applies to debug mode")

        token_response = MagicMock()
        token_response.total_tokens = 2000000
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        with patch("git_ai_reporter.services.gemini.rprint") as mock_print:
            with pytest.raises(GeminiClientError):
                await gemini_client.synthesize_daily_summary("log", "diff")

        # Should print debug messages
        mock_print.assert_called()
class TestWeeklyNarrative:
    """Tests for generate_news_narrative method."""
    async def test_successful_generation(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful weekly narrative generation."""
        # Setup mock for both count_tokens and generate_content
        token_response = MagicMock()
        token_response.total_tokens = 1000
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        response = MagicMock()
        response.text = "This week marked significant progress in authentication..."
        mock_genai_client.aio.models.generate_content.return_value = response

        # Call method
        result = await gemini_client.generate_news_narrative(
            commit_summaries="Commit summaries",
            daily_summaries="Day 1 summary\n\nDay 2 summary",
            weekly_diff="Weekly diff content",
            history="Previous week context",
        )

        # Verify
        check.is_instance(result, str)
        check.is_in("significant progress", result)
        check.is_in("authentication", result)
        mock_genai_client.aio.models.generate_content.assert_called_once()
    async def test_empty_input_handling(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of empty inputs for weekly narrative."""
        # Setup token count for weekly
        token_response = MagicMock()
        token_response.total_tokens = 100
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        response = MagicMock()
        response.text = "Empty week summary"
        mock_genai_client.aio.models.generate_content.return_value = response

        # Test empty weekly summary
        weekly_result = await gemini_client.generate_news_narrative("", "", "", "")
        check.is_instance(weekly_result, str)
    async def test_prompt_trimming_strategies(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly prompt trimming strategies."""
        # First call: over limit
        token_response1 = MagicMock()
        token_response1.total_tokens = 1100000  # Over limit

        # Second call: under limit after trimming
        token_response2 = MagicMock()
        token_response2.total_tokens = 900000  # Under limit

        mock_genai_client.aio.models.count_tokens.side_effect = [
            token_response1,
            token_response2,
        ]

        # Generate response
        response = MagicMock()
        response.text = "Trimmed narrative"
        mock_genai_client.aio.models.generate_content.return_value = response

        # Call with long inputs
        result = await gemini_client.generate_news_narrative(
            commit_summaries="Commits",
            daily_summaries="Day 1\n\nDay 2\n\nDay 3",
            weekly_diff="Long diff content with context",
            history="#### Old History\nOld content\n#### Recent History\nRecent content",
        )

        # Should succeed after trimming
        check.is_instance(result, str)
        check.equal(mock_genai_client.aio.models.count_tokens.call_count, 2)
    async def test_token_limit_handling(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test that prompts are truncated when too long."""
        # Setup mock for token counting
        token_response = MagicMock()
        token_response.total_tokens = 2000000  # Over limit
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # Should raise error when unable to trim
        with pytest.raises(GeminiClientError):
            await gemini_client.generate_news_narrative(
                commit_summaries="x" * 1000000,
                daily_summaries="x" * 1000000,
                weekly_diff="x" * 1000000,
                history="x" * 1000000,
            )
    @pytest.mark.parametrize("error_scenario", [
        "empty_response",
        "timeout_error",
    ])
    async def test_retry_logic(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        error_scenario: str,
    ) -> None:
        """Test weekly narrative retry logic for various error scenarios."""
        # Setup token count OK
        token_response = MagicMock()
        token_response.total_tokens = 500
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        if error_scenario == "empty_response":
            # Generate fails with empty response
            response = MagicMock()
            response.text = ""
            mock_genai_client.aio.models.generate_content.side_effect = [
                response, response, response,  # All empty
            ]
        elif error_scenario == "timeout_error":
            # All attempts timeout
            mock_genai_client.aio.models.generate_content.side_effect = [
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
            ]

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_news_narrative("c", "d", "w", "h")

        check.is_in("News narrative generation failed after", str(exc_info.value))
    async def test_timeout_then_success(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test news narrative with timeout then success."""
        # Setup token count OK
        token_response = MagicMock()
        token_response.total_tokens = 500
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # First timeout, second succeeds
        response = MagicMock()
        response.text = "News narrative"

        mock_genai_client.aio.models.generate_content.side_effect = [
            asyncio.TimeoutError(),
            response,
        ]

        result = await gemini_client.generate_news_narrative("c", "d", "w", "h")

        check.equal(result, "News narrative")
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 2)
class TestChangelogGeneration:
    """Tests for generate_changelog_entries method."""
    async def test_successful_generation(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful changelog entry generation."""
        # Setup mock
        response = MagicMock()
        response.text = (
            "### 🚀 New Feature\\n- Add authentication system\\n\\n"
            "### 🐛 Bug Fix\\n- Fix login timeout"
        )
        mock_genai_client.aio.models.generate_content.return_value = response

        # Call method
        categorized = [
            {"summary": "Add authentication", "category": "New Feature"},
            {"summary": "Fix login timeout", "category": "Bug Fix"},
        ]
        result = await gemini_client.generate_changelog_entries(categorized)

        # Verify
        check.is_instance(result, str)
        check.is_in("New Feature", result)
        check.is_in("Bug Fix", result)
        check.is_in("authentication", result)
        mock_genai_client.aio.models.generate_content.assert_called_once()
    async def test_empty_entries(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of empty changelog entries."""
        response = MagicMock()
        response.text = "No changes"
        mock_genai_client.aio.models.generate_content.return_value = response

        # Test empty changelog
        changelog_result = await gemini_client.generate_changelog_entries([])
        check.is_instance(changelog_result, str)
    @pytest.mark.parametrize("error_scenario", [
        "timeout_error",
        "empty_response",
    ])
    async def test_retry_logic(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        error_scenario: str,
    ) -> None:
        """Test changelog generation retry logic."""
        if error_scenario == "timeout_error":
            # All attempts timeout
            mock_genai_client.aio.models.generate_content.side_effect = [
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
            ]
        elif error_scenario == "empty_response":
            # All attempts return empty
            response = MagicMock()
            response.text = ""
            mock_genai_client.aio.models.generate_content.side_effect = [
                response, response, response,
            ]

        test_entries = [{"summary": "test", "category": "Bug Fix"}]
        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_changelog_entries(test_entries)

        check.is_in("Changelog generation failed after", str(exc_info.value))
    async def test_timeout_then_success(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test changelog generation with timeout then success."""
        # First timeout, then success
        response = MagicMock()
        response.text = "### 🐛 Bug Fix\\n- Fixed issue"

        mock_genai_client.aio.models.generate_content.side_effect = [
            asyncio.TimeoutError(),
            response,
        ]

        result = await gemini_client.generate_changelog_entries([
            {"summary": "test", "category": "Bug Fix"}
        ])

        check.is_instance(result, str)
        check.is_in("Bug Fix", result)
class TestInternalHelpers:
    """Tests for internal helper methods (for coverage completion)."""
    async def test_generate_with_retry_empty_response(
        self,
        
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _generate_with_retry with empty response."""
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
    async def test_construct_weekly_prompt_debug_fitting(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly prompt fitting with debug output."""
        # Skip test if not in debug mode
        if not gemini_client._config.debug:  # pylint: disable=protected-access
            pytest.skip("Test only applies to debug mode")

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
            result = await gemini_client._construct_and_fit_weekly_prompt(  # pylint: disable=protected-access
                "commits", "daily", "diff", "x" * 1000
            )

        check.is_not_none(result)
        # Should print debug messages about data-preserving fitting
        assert any(EXCEEDS_LIMIT_MSG in str(call) for call in mock_print.call_args_list)
    async def test_construct_weekly_prompt_max_iterations_exceeded(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly prompt when max iterations exceeded."""
        # Always return over limit
        token_response = MagicMock()
        token_response.total_tokens = 2000000
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client._construct_and_fit_weekly_prompt(  # pylint: disable=protected-access
                "commits", "daily", "diff", "history"
            )

        check.is_in("Failed to fit prompt while preserving data integrity", str(exc_info.value))
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
        mock_response = Mock()
        mock_genai_client.aio.models.generate_content.side_effect = HTTPStatusError(
            "Bad request", request=mock_request, response=mock_response
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
        mock_response = Response(400)
        http_error = HTTPStatusError("Bad request", request=mock_request, response=mock_response)

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
            response1, response2, response3, response4,
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

        check.is_in("Commit analysis failed after", str(exc_info.value))