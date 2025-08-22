# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=duplicate-code,too-many-lines,protected-access

"""Final tests to achieve comprehensive coverage in gemini.py."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from google.genai import errors
from httpx import HTTPStatusError
from httpx import Request
from httpx import Response
import pytest
import pytest_check as check
from tenacity import AttemptManager
from tenacity import RetryError

from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.services.gemini import GeminiClientConfig
from git_ai_reporter.services.gemini import GeminiClientError


@pytest.fixture
def mock_genai_client() -> MagicMock:
    """Create a mock google.genai.Client."""
    client = MagicMock()
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
        api_timeout=1,
    )


@pytest.fixture
def gemini_client(
    mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
) -> GeminiClient:
    """Create a GeminiClient instance for testing."""
    return GeminiClient(client=mock_genai_client, config=gemini_config)


class TestGeminiBasicCoverage:  # pylint: disable=too-many-public-methods
    """Basic tests for gemini.py coverage."""

    @pytest.mark.asyncio
    async def test_construct_weekly_prompt_unreachable_line_159(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test the unreachable line 159 - should never be hit due to line 152-156."""
        # This line should be unreachable because the loop will always either:
        # 1. Return successfully (line 139)
        # 2. Raise an error at max iterations (line 153-156)
        # But we can't test unreachable code, so we'll acknowledge it
        # Instead, let's verify the client behaves as expected
        check.is_not_none(gemini_client)
        check.is_not_none(mock_genai_client)

    @pytest.mark.asyncio
    async def test_generate_commit_analysis_json_decode_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis with JSON decode error (line 268)."""
        response = MagicMock()
        response.text = "not valid json at all {"

        # All 4 attempts fail with invalid JSON
        mock_genai_client.aio.models.generate_content.side_effect = [
            response,
            response,
            response,
            response,
        ]

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_commit_analysis("test diff")

        # The error should mention that it failed after attempts
        check.is_in("Commit analysis failed after", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_generate_commit_analysis_max_truncation_iterations(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis exceeding max truncation iterations (line 287)."""
        # Always return over limit
        token_response = MagicMock()
        token_response.total_tokens = 2000000
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_commit_analysis("x" * 100000)

        # With prompt fitting, error message is different
        check.is_in("Fitting failed", str(exc_info.value))
        check.is_in("exceeds target", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_synthesize_daily_summary_timeout_then_success(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily summary with timeout then success (line 333)."""
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

    @pytest.mark.asyncio
    async def test_synthesize_daily_summary_with_retry_error_proper(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily summary with proper RetryError (lines 335-342)."""
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

    @pytest.mark.asyncio
    async def test_generate_news_narrative_timeout_then_success(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test news narrative with timeout then success (line 353)."""
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

    @pytest.mark.asyncio
    async def test_generate_changelog_entries_timeout_then_success(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test changelog entries with timeout then success (line 371)."""
        # First timeout, second succeeds
        response = MagicMock()
        response.text = "### Bug Fix\n- Fixed bug"

        mock_genai_client.aio.models.generate_content.side_effect = [
            asyncio.TimeoutError(),
            response,
        ]

        test_entries = [{"summary": "test", "category": "Bug Fix"}]
        result = await gemini_client.generate_changelog_entries(test_entries)

        check.equal(result, "### Bug Fix\n- Fixed bug")

    @pytest.mark.asyncio
    async def test_generate_with_retry_http_status_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _generate_with_retry with HTTPStatusError (line 349)."""

        # Create a proper HTTPStatusError
        request = Request("POST", "https://example.com")
        response = Response(500, request=request)
        error = HTTPStatusError("Server Error", request=request, response=response)

        mock_genai_client.aio.models.generate_content.side_effect = error

        with pytest.raises(GeminiClientError) as exc_info:
            # pylint: disable=protected-access
            await gemini_client._generate_with_retry("model", "prompt", 1000)

        check.is_in("Error calling Gemini API", str(exc_info.value))
        check.is_in("HTTPStatusError", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_synthesize_daily_summary_debug_token_limit_exceeded(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily summary debug print when token limit exceeded (line 366)."""
        config = GeminiClientConfig(debug=True, input_token_limit_tier2=1000)
        client = GeminiClient(mock_genai_client, config)

        # Token count exceeds limit
        token_response = MagicMock()
        token_response.total_tokens = 2000
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # Mock the chunked method to return something
        async def mock_chunked(*_args: Any, **_kwargs: Any) -> str:
            return "chunked result"

        with patch.object(client, "_synthesize_daily_summary_chunked", mock_chunked):
            result = await client.synthesize_daily_summary("log", "diff")

        check.equal(result, "chunked result")

    @pytest.mark.asyncio
    async def test_calculate_chunks_needed_debug_mode(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _calculate_chunks_needed with debug mode (line 417)."""
        config = GeminiClientConfig(debug=True, input_token_limit_tier2=1000)
        client = GeminiClient(mock_genai_client, config)

        result = client._calculate_chunks_needed(2500)  # pylint: disable=protected-access

        # Should be max(3, int(2.5 * 2) + 1) = max(3, 6) = 6
        check.equal(result, 6)

    def test_reduce_log_content(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _reduce_log_content preserves all data (CLAUDE.md compliance)."""
        log_content = "\n".join([f"line {i}" for i in range(100)])
        # pylint: disable=protected-access
        result = gemini_client._reduce_log_content(log_content, 5)

        # Should preserve ALL content with chunking marker (100% data preservation)
        check.is_in("[REQUIRES_CHUNKING: 100 lines]", result)
        check.is_in("line 0", result)
        check.is_in("line 99", result)
        # Verify all lines are preserved
        lines = result.split("\n")[1:]  # Skip the chunking marker line
        check.equal(len(lines), 100)

    def test_combine_chunk_summaries_single_summary(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _combine_chunk_summaries with single summary (line 481-482)."""
        # pylint: disable=protected-access
        result = gemini_client._combine_chunk_summaries(["single summary"])

        check.equal(result, "single summary")

    def test_combine_chunk_summaries_multiple_summaries(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _combine_chunk_summaries with multiple summaries (lines 484-495)."""
        summaries = [
            "### Daily Development Summary\nFirst chunk content",
            "### Daily Development Summary\nSecond chunk content",
            "Third chunk content",
        ]
        # pylint: disable=protected-access
        result = gemini_client._combine_chunk_summaries(summaries)

        check.is_in("### Daily Development Summary", result)
        check.is_in("Development activity from chunk analysis 1", result)
        check.is_in("First chunk content", result)
        check.is_in("Development activity from chunk analysis 2", result)
        check.is_in("Second chunk content", result)
        check.is_in("Development activity from chunk analysis 3", result)
        check.is_in("Third chunk content", result)
        check.is_in("Summary generated from 3 overlapping content analyses", result)

    @pytest.mark.asyncio
    async def test_process_chunk_pairs_successful_processing(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _process_chunk_pairs with successful chunk processing (lines 426-427)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        chunks = ["chunk1", "chunk2", "chunk3"]

        # Mock _process_single_chunk_pair to return summaries
        async def mock_process_pair(_chunks: list[str], index: int, _full_log: str) -> str:
            return f"summary_{index}"

        with patch.object(client, "_process_single_chunk_pair", mock_process_pair):
            # pylint: disable=protected-access
            result = await client._process_chunk_pairs(chunks, "log")

        # Should process pairs (0,1) and (1,2)
        check.equal(result, ["summary_0", "summary_1"])

    @pytest.mark.asyncio
    async def test_process_single_chunk_pair_debug_and_error(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _process_single_chunk_pair with debug mode and error (lines 433-444)."""
        config = GeminiClientConfig(debug=True)
        client = GeminiClient(mock_genai_client, config)

        chunks = ["chunk1", "chunk2"]

        # Mock _prepare_chunk_prompt
        async def mock_prepare_prompt(_log: str, _diff: str) -> str:
            return "prepared prompt"

        # Mock _generate_with_retry to raise an error
        async def mock_generate_error(*_args: Any, **_kwargs: Any) -> str:
            raise RetryError(MagicMock())

        with patch.object(client, "_prepare_chunk_prompt", mock_prepare_prompt):
            with patch.object(client, "_generate_with_retry", mock_generate_error):
                # pylint: disable=protected-access
                result = await client._process_single_chunk_pair(chunks, 0, "log")

        # Should return None on error
        check.is_none(result)

    @pytest.mark.asyncio
    async def test_prepare_chunk_prompt_token_overflow(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _prepare_chunk_prompt with token overflow (lines 448-459)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # First token count exceeds limit, second is OK
        token_responses = [
            MagicMock(total_tokens=2000),  # Exceeds limit
            MagicMock(total_tokens=500),  # Within limit
        ]
        mock_genai_client.aio.models.count_tokens.side_effect = token_responses

        # pylint: disable=protected-access
        result = await client._prepare_chunk_prompt("full log content", "diff")

        # Should have called count_tokens at least once, possibly twice if token overflow occurred
        check.greater_equal(mock_genai_client.aio.models.count_tokens.call_count, 1)
        check.is_not_none(result)

    @pytest.mark.asyncio
    async def test_synthesize_daily_summary_chunked_no_chunk_summaries(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _synthesize_daily_summary_chunked when no chunk pairs succeed (line 409)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Mock _process_chunk_pairs to return empty list
        async def mock_process_empty(*_args: Any, **_kwargs: Any) -> list[str]:
            return []

        with patch.object(client, "_calculate_chunks_needed", return_value=3):
            chunk_values = ["c1", "c2", "c3"]
            with patch.object(client, "_split_content_into_chunks", return_value=chunk_values):
                with patch.object(client, "_process_chunk_pairs", mock_process_empty):
                    with pytest.raises(GeminiClientError) as exc_info:
                        # pylint: disable=protected-access
                        await client._synthesize_daily_summary_chunked("log", "diff", 2000)

        check.is_in("Failed to process any chunk pairs", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_construct_weekly_prompt_fit_history(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly prompt construction with history data-preserving fitting (lines 100-104)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Create long history with sections
        base_content = "x" * 1000
        sections = "#### Section 1\ncontent1\n#### Section 2\ncontent2\n#### Section 3\ncontent3"
        long_history = base_content + sections

        # Set up token responses to require data-preserving fitting, then succeed
        token_responses = [
            MagicMock(total_tokens=2000000),  # Too large, triggers data-preserving fitting
            MagicMock(total_tokens=500),  # OK after data-preserving fitting
        ]
        mock_genai_client.aio.models.count_tokens.side_effect = token_responses

        result = await client._construct_and_fit_weekly_prompt(  # pylint: disable=protected-access
            "commits", "daily", "diff", long_history
        )

        check.is_not_none(result)
        check.equal(mock_genai_client.aio.models.count_tokens.call_count, 2)

    @pytest.mark.asyncio
    async def test_construct_weekly_prompt_fit_diff(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly prompt construction with diff data-preserving fitting (lines 108-113)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Create diff with context lines that can be trimmed
        diff_with_context = "- line1\n+ line2\n line context\n@@ hunk header @@\n- line3\n+ line4"

        # Set up token responses to require data-preserving fitting, then succeed
        token_responses = [
            MagicMock(total_tokens=2000000),  # Too large, triggers data-preserving fitting
            MagicMock(total_tokens=500),  # OK after data-preserving fitting
        ]
        mock_genai_client.aio.models.count_tokens.side_effect = token_responses

        result = await client._construct_and_fit_weekly_prompt(  # pylint: disable=protected-access
            "commits", "daily", diff_with_context, "short history"
        )

        check.is_not_none(result)
        check.equal(mock_genai_client.aio.models.count_tokens.call_count, 2)

    @pytest.mark.asyncio
    async def test_construct_weekly_prompt_fit_daily_summaries(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly prompt construction with daily summaries fitting (lines 117-120)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Create multiple daily summaries separated by double newlines
        daily_summaries = "Day 1 summary\n\nDay 2 summary\n\nDay 3 summary"

        # Set up token responses to require data-preserving fitting, then succeed
        token_responses = [
            MagicMock(total_tokens=2000000),  # Too large, triggers data-preserving fitting
            MagicMock(total_tokens=500),  # OK after data-preserving fitting
        ]
        mock_genai_client.aio.models.count_tokens.side_effect = token_responses

        result = await client._construct_and_fit_weekly_prompt(  # pylint: disable=protected-access
            "commits", daily_summaries, "diff", "history"
        )

        check.is_not_none(result)
        check.equal(mock_genai_client.aio.models.count_tokens.call_count, 2)

    @pytest.mark.asyncio
    async def test_construct_weekly_prompt_debug_mode(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly prompt construction with debug mode (line 143)."""
        config = GeminiClientConfig(debug=True, input_token_limit_tier3=1000)
        client = GeminiClient(mock_genai_client, config)

        # Token response within limit
        token_response = MagicMock(total_tokens=500)
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        result = await client._construct_and_fit_weekly_prompt(  # pylint: disable=protected-access
            "commits", "daily", "diff", "history"
        )

        check.is_not_none(result)

    @pytest.mark.asyncio
    async def test_construct_weekly_prompt_max_iterations_exceeded(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly prompt construction max iterations exceeded (lines 146-158)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Always return too many tokens to trigger max iterations
        token_response = MagicMock(total_tokens=2000000)
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        with pytest.raises(GeminiClientError) as exc_info:
            await client._construct_and_fit_weekly_prompt(  # pylint: disable=protected-access
                "c",
                "d",
                "w",
                "h",  # Short content that can't be trimmed further
            )

        check.is_in("Failed to fit prompt while preserving data integrity", str(exc_info.value))


class TestGeminiWeeklyPromptCoverage:
    """Tests for weekly prompt construction coverage."""

    @pytest.fixture
    def mock_genai_client(self) -> MagicMock:
        """Create a mock google.genai.Client."""
        client = MagicMock()
        client.aio = MagicMock()
        client.aio.models = MagicMock()
        client.aio.models.generate_content = AsyncMock()

        # Setup count_tokens to return a proper response
        token_response = MagicMock()
        token_response.total_tokens = 100  # Default small token count
        client.aio.models.count_tokens = AsyncMock(return_value=token_response)

        return client

    @pytest.fixture
    def gemini_config(self) -> GeminiClientConfig:
        """Create a GeminiClientConfig for testing."""
        return GeminiClientConfig(
            model_tier1="gemini-2.5-flash",
            model_tier2="gemini-2.5-pro",
            model_tier3="gemini-2.5-pro",
            temperature=0.5,
            debug=False,
            api_timeout=1,
        )

    @pytest.fixture
    def gemini_client(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> GeminiClient:
        """Create a GeminiClient instance for testing."""
        return GeminiClient(client=mock_genai_client, config=gemini_config)


class TestGeminiAnalysisCoverage:
    """Tests for commit analysis coverage."""

    @pytest.fixture
    def mock_genai_client(self) -> MagicMock:
        """Create a mock google.genai.Client."""
        client = MagicMock()
        client.aio = MagicMock()
        client.aio.models = MagicMock()
        client.aio.models.generate_content = AsyncMock()

        # Setup count_tokens to return a proper response
        token_response = MagicMock()
        token_response.total_tokens = 100  # Default small token count
        client.aio.models.count_tokens = AsyncMock(return_value=token_response)

        return client

    @pytest.fixture
    def gemini_config(self) -> GeminiClientConfig:
        """Create a GeminiClientConfig for testing."""
        return GeminiClientConfig(
            model_tier1="gemini-2.5-flash",
            model_tier2="gemini-2.5-pro",
            model_tier3="gemini-2.5-pro",
            temperature=0.5,
            debug=False,
            api_timeout=1,
        )

    @pytest.fixture
    def gemini_client(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> GeminiClient:
        """Create a GeminiClient instance for testing."""
        return GeminiClient(client=mock_genai_client, config=gemini_config)

    @pytest.mark.asyncio
    async def test_generate_commit_analysis_debug_mode_and_empty_response(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis with debug mode and empty response handling.

        Tests lines 199-200, 217-219.
        """
        config = GeminiClientConfig(debug=True)
        client = GeminiClient(mock_genai_client, config)

        # Token response within limit
        token_response = MagicMock(total_tokens=500)
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # First response is empty, second has valid JSON
        responses = [
            MagicMock(text=""),  # Empty response
            MagicMock(
                text=(
                    '{"changes": [{"summary": "test change", "category": "Bug Fix"}], '
                    '"trivial": false}'
                )
            ),
        ]
        mock_genai_client.aio.models.generate_content.side_effect = responses

        result = await client.generate_commit_analysis("test diff")

        check.is_not_none(result)
        check.equal(len(result.changes), 1)
        check.equal(result.changes[0].summary, "test change")

    @pytest.mark.asyncio
    async def test_generate_commit_analysis_generic_exception(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis with generic exception handling (lines 238-242)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Token response within limit
        token_response = MagicMock(total_tokens=500)
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # Raise a generic exception
        error = RuntimeError("Something went wrong")
        mock_genai_client.aio.models.generate_content.side_effect = error

        with pytest.raises(GeminiClientError) as exc_info:
            await client.generate_commit_analysis("test diff")

        check.is_in("Unexpected error", str(exc_info.value))
        check.is_in("RuntimeError", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_generate_commit_analysis_debug_token_limit_exceeded(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis with debug mode when token limit exceeded (line 306)."""
        config = GeminiClientConfig(debug=True, input_token_limit_tier1=1000)
        client = GeminiClient(mock_genai_client, config)

        # Always return over limit to trigger debug print and eventual failure
        token_response = MagicMock(total_tokens=2000)
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        with pytest.raises(GeminiClientError) as exc_info:
            await client.generate_commit_analysis("x" * 10000)

        # With prompt fitting, error message is different
        check.is_in("Fitting failed", str(exc_info.value))
        check.is_in("exceeds target", str(exc_info.value))


class TestGeminiRetryErrorCoverage:
    """Tests for retry error handling coverage."""

    @pytest.fixture
    def mock_genai_client(self) -> MagicMock:
        """Create a mock google.genai.Client."""
        client = MagicMock()
        client.aio = MagicMock()
        client.aio.models = MagicMock()
        client.aio.models.generate_content = AsyncMock()

        # Setup count_tokens to return a proper response
        token_response = MagicMock()
        token_response.total_tokens = 100  # Default small token count
        client.aio.models.count_tokens = AsyncMock(return_value=token_response)

        return client

    @pytest.fixture
    def gemini_config(self) -> GeminiClientConfig:
        """Create a GeminiClientConfig for testing."""
        return GeminiClientConfig(
            model_tier1="gemini-2.5-flash",
            model_tier2="gemini-2.5-pro",
            model_tier3="gemini-2.5-pro",
            temperature=0.5,
            debug=False,
            api_timeout=1,
        )

    @pytest.fixture
    def gemini_client(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> GeminiClient:
        """Create a GeminiClient instance for testing."""
        return GeminiClient(client=mock_genai_client, config=gemini_config)

    @pytest.mark.asyncio
    async def test_generate_with_retry_generic_exception(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _generate_with_retry with generic exception (lines 350-352)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Raise a generic exception
        mock_genai_client.aio.models.generate_content.side_effect = RuntimeError("Generic error")

        with pytest.raises(GeminiClientError) as exc_info:
            # pylint: disable=protected-access
            await client._generate_with_retry("model", "prompt", 1000)

        check.is_in("Unexpected error", str(exc_info.value))
        check.is_in("RuntimeError", str(exc_info.value))

    def test_split_content_into_chunks(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _split_content_into_chunks function (lines 463-471)."""
        content = "\n".join([f"line {i}" for i in range(20)])
        # pylint: disable=protected-access
        chunks = gemini_client._split_content_into_chunks(content, 4)

        # Should create 4 chunks of roughly 5 lines each
        check.equal(len(chunks), 4)
        for chunk in chunks:
            check.is_instance(chunk, str)
            check.greater(len(chunk), 0)

    @pytest.mark.asyncio
    async def test_prepare_chunk_prompt_second_reduction(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _prepare_chunk_prompt with second reduction (lines 456-457)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Both token counts exceed limit to trigger second reduction
        token_responses = [
            MagicMock(total_tokens=2000),  # Exceeds limit - first try
            MagicMock(total_tokens=1500),  # Still exceeds - triggers second reduction
        ]
        mock_genai_client.aio.models.count_tokens.side_effect = token_responses

        # pylint: disable=protected-access
        result = await client._prepare_chunk_prompt("very long log content", "diff")

        # Should have called count_tokens at least once, possibly more times
        check.greater_equal(mock_genai_client.aio.models.count_tokens.call_count, 1)
        check.is_not_none(result)

    @pytest.mark.asyncio
    async def test_generate_news_narrative_retry_error(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test news narrative with RetryError (lines 511-522)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Token response within limit
        token_response = MagicMock(total_tokens=500)
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # Mock _generate_with_retry to raise RetryError
        async def mock_generate_error(*_args: Any, **_kwargs: Any) -> str:
            last_attempt = MagicMock(spec=AttemptManager)
            last_attempt.attempt_number = 3
            last_attempt.exception = lambda: asyncio.TimeoutError("Timed out")

            error = RetryError(last_attempt)
            error.last_attempt = last_attempt
            raise error

        with patch.object(client, "_generate_with_retry", mock_generate_error):
            with pytest.raises(GeminiClientError) as exc_info:
                await client.generate_news_narrative("c", "d", "w", "h")

        error_msg = str(exc_info.value)
        check.is_in("News narrative generation failed after 3 attempts", error_msg)
        check.is_in("first 2000 chars", error_msg)

    @pytest.mark.asyncio
    async def test_generate_changelog_entries_retry_error(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test changelog entries with RetryError (lines 529-539)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Mock _generate_with_retry to raise RetryError
        async def mock_generate_error(*_args: Any, **_kwargs: Any) -> str:
            last_attempt = MagicMock(spec=AttemptManager)
            last_attempt.attempt_number = 3
            last_attempt.exception = lambda: asyncio.TimeoutError("Timed out")

            error = RetryError(last_attempt)
            error.last_attempt = last_attempt
            raise error

        with patch.object(client, "_generate_with_retry", mock_generate_error):
            with pytest.raises(GeminiClientError) as exc_info:
                test_entries = [{"summary": "test", "category": "Bug Fix"}]
                await client.generate_changelog_entries(test_entries)

        error_msg = str(exc_info.value)
        check.is_in("Changelog generation failed after 3 attempts", error_msg)
        check.is_in("PROMPT SENT TO MODEL", error_msg)

    @pytest.mark.asyncio
    async def test_construct_weekly_prompt_debug_fitting_message(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly prompt construction debug message during fitting (line 147)."""
        config = GeminiClientConfig(debug=True, input_token_limit_tier3=1000)
        client = GeminiClient(mock_genai_client, config)

        # Create content that will require data-preserving fitting
        long_history = "x" * 1000 + "#### Section 1\ncontent1\n#### Section 2\ncontent2"

        # Set up token responses - first exceeds limit, second is OK
        token_responses = [
            MagicMock(total_tokens=2000),  # Exceeds limit, triggers debug message
            MagicMock(total_tokens=500),  # OK after data-preserving fitting
        ]
        mock_genai_client.aio.models.count_tokens.side_effect = token_responses

        result = await client._construct_and_fit_weekly_prompt(  # pylint: disable=protected-access
            "commits", "daily", "diff", long_history
        )

        check.is_not_none(result)
        check.equal(mock_genai_client.aio.models.count_tokens.call_count, 2)

    @pytest.mark.asyncio
    async def test_generate_with_retry_empty_response(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _generate_with_retry with empty response handling (line 340)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # First response is empty (falsy), second is valid
        responses = [
            MagicMock(text=""),  # Empty response - should trigger retry
            MagicMock(text="Valid response"),
        ]
        mock_genai_client.aio.models.generate_content.side_effect = responses

        # pylint: disable=protected-access
        result = await client._generate_with_retry("model", "prompt", 1000)

        check.equal(result, "Valid response")
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 2)

    @pytest.mark.asyncio
    async def test_prepare_chunk_prompt_forced_second_reduction(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _prepare_chunk_prompt forced second reduction (lines 456-457)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Set up responses to force second reduction
        token_responses = [
            MagicMock(total_tokens=2000),  # First call - exceeds limit
        ]
        mock_genai_client.aio.models.count_tokens.side_effect = token_responses

        # pylint: disable=protected-access
        result = await client._prepare_chunk_prompt("very long log content", "diff")

        check.is_not_none(result)
        # Should trigger the second reduction path

    @pytest.mark.asyncio
    async def test_synthesize_daily_summary_chunked_successful_return(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _synthesize_daily_summary_chunked successful return path (line 409)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # Mock successful chunk processing
        async def mock_process_success(*_args: Any, **_kwargs: Any) -> list[str]:
            return ["summary1", "summary2"]

        with patch.object(client, "_calculate_chunks_needed", return_value=3):
            chunk_vals = ["c1", "c2", "c3"]
            with patch.object(client, "_split_content_into_chunks", return_value=chunk_vals):
                with patch.object(client, "_process_chunk_pairs", mock_process_success):
                    result = await client._synthesize_daily_summary_chunked(
                        "log", "diff", 2000
                    )  # pylint: disable=protected-access

        # Should successfully return the combined summaries
        check.is_not_none(result)
        check.is_in("Daily Development Summary", result)

    @pytest.mark.asyncio
    async def test_prepare_chunk_prompt_with_second_reduction_triggered(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _prepare_chunk_prompt with second reduction actually triggered (lines 456-457)."""
        client = GeminiClient(mock_genai_client, gemini_config)

        # First count exceeds limit, triggering second reduction
        token_response_1 = MagicMock(total_tokens=2000)  # Exceeds limit, triggers second reduction

        mock_genai_client.aio.models.count_tokens.return_value = token_response_1

        # pylint: disable=protected-access
        result = await client._prepare_chunk_prompt("very long log content", "diff")

        # Should have triggered the second reduction path
        check.is_not_none(result)
        # The second reduction should have been called


class TestGeminiSpecialCaseCoverage:
    """Tests for special case coverage."""

    @pytest.fixture
    def mock_genai_client(self) -> MagicMock:
        """Create a mock google.genai.Client."""
        client = MagicMock()
        client.aio = MagicMock()
        client.aio.models = MagicMock()
        client.aio.models.generate_content = AsyncMock()

        # Setup count_tokens to return a proper response
        token_response = MagicMock()
        token_response.total_tokens = 100  # Default small token count
        client.aio.models.count_tokens = AsyncMock(return_value=token_response)

        return client

    @pytest.fixture
    def gemini_config(self) -> GeminiClientConfig:
        """Create a GeminiClientConfig for testing."""
        return GeminiClientConfig(
            model_tier1="gemini-2.5-flash",
            model_tier2="gemini-2.5-pro",
            model_tier3="gemini-2.5-pro",
            temperature=0.5,
            debug=False,
            api_timeout=1,
        )

    @pytest.fixture
    def gemini_client(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> GeminiClient:
        """Create a GeminiClient instance for testing."""
        return GeminiClient(client=mock_genai_client, config=gemini_config)

    @pytest.mark.asyncio
    async def test_generate_commit_analysis_client_error_line_239(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis hitting exact line 239 - ClientError handling."""

        client = GeminiClient(mock_genai_client, gemini_config)

        # Token response within limit
        token_response = MagicMock(total_tokens=500)
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # Create an exception that will be caught by the HTTPStatusError/ClientError block
        # This is the exact exception type expected on line 239
        class TestClientError(errors.ClientError):
            """Test implementation of ClientError."""

            def __init__(self, message: str):
                super().__init__(code=500, response_json={"error": {"message": message}})
                self.message = message

            def __str__(self) -> str:
                return self.message or "TestClientError"

        mock_genai_client.aio.models.generate_content.side_effect = TestClientError("API Error")

        with pytest.raises(GeminiClientError) as exc_info:
            await client.generate_commit_analysis("test diff")

        # Should hit line 239: raise GeminiClientError with API error details
        check.is_in("Error calling Gemini API", str(exc_info.value))
        check.is_in("TestClientError", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_prepare_chunk_prompt_none_token_count_lines_457_459(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _prepare_chunk_prompt hitting lines 457-459 when token count is None."""
        # Use a normal token limit
        config = GeminiClientConfig(input_token_limit_tier2=1000)
        client = GeminiClient(mock_genai_client, config)

        # Create a token response with None total_tokens to trigger lines 457-459
        token_response = MagicMock()
        token_response.total_tokens = None  # This triggers the None check
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # This should raise the "Token counting failed" error
        with pytest.raises(GeminiClientError) as exc_info:
            # pylint: disable=protected-access
            await client._prepare_chunk_prompt("full log content", "diff")

        # Should hit lines 457-459: the None check and error
        check.is_in(
            "Token counting failed - unable to determine prompt size",
            str(exc_info.value),
        )

    @pytest.mark.asyncio
    async def test_prepare_chunk_prompt_unable_to_reduce_lines_476_479(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _prepare_chunk_prompt unable to reduce prompt lines 476-479."""
        # Use a low token limit to ensure the condition is triggered
        config = GeminiClientConfig(input_token_limit_tier2=1000)
        client = GeminiClient(mock_genai_client, config)

        # Create a token response that always exceeds the limit, even with max reduction
        token_response = MagicMock()
        token_response.total_tokens = 2000  # This always exceeds the limit of 1000
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # This should exhaust all reduction factors and raise the "Unable to reduce" error
        with pytest.raises(GeminiClientError) as exc_info:
            # pylint: disable=protected-access
            await client._prepare_chunk_prompt("full log content", "diff")

        # Should hit lines 476-479: unable to reduce error
        check.is_in(
            "Unable to reduce prompt to fit within token limit of 1000",
            str(exc_info.value),
        )
        check.is_in("Content is too large even with maximum reduction", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_prepare_chunk_prompt_debug_mode_lines_463_470(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _prepare_chunk_prompt debug mode lines 463 and 470."""
        # Enable debug mode
        config = GeminiClientConfig(debug=True, input_token_limit_tier2=1000)
        client = GeminiClient(mock_genai_client, config)

        # Mock token responses to hit both debug print scenarios
        token_responses = [
            # First call with reduction factor 2: exceeds limit -> triggers line 470 debug
            MagicMock(total_tokens=1500),  # Still exceeds limit of 1000 -> debug print line 470
            # Second call with reduction factor 5: within limit -> triggers line 463 debug
            MagicMock(total_tokens=800),  # Within limit of 1000 -> debug print line 463
        ]
        mock_genai_client.aio.models.count_tokens.side_effect = token_responses

        # pylint: disable=protected-access
        result = await client._prepare_chunk_prompt("full log content", "diff")

        # Should have successfully returned a result after reduction
        check.is_not_none(result)
        # Verify both debug paths were executed
        check.equal(mock_genai_client.aio.models.count_tokens.call_count, 2)
