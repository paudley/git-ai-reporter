# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=duplicate-code

"""Unit tests for git_ai_reporter.services.gemini module.

This module tests the GeminiClient class which handles three-tier AI processing
for commit analysis, daily synthesis, and weekly narrative generation.
"""

import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from google import genai
from httpx import ConnectError
from pydantic import ValidationError
import pytest
import pytest_check as check

from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.services.gemini import GeminiClient
from git_ai_reporter.services.gemini import GeminiClientConfig
from git_ai_reporter.services.gemini import GeminiClientError


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
    """Create a mock GenerateContentResponse."""
    response = MagicMock()
    response.text = (
        '{"changes": [{"summary": "Add feature", "category": "New Feature"}], "trivial": false}'
    )
    return response


class TestGeminiClient:
    """Test suite for GeminiClient class."""

    def test_init(
        self,
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        gemini_config: GeminiClientConfig,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test GeminiClient initialization."""
        client = GeminiClient(client=mock_genai_client, config=gemini_config)
        check.equal(client._client, mock_genai_client)  # pylint: disable=protected-access
        check.equal(client._config, gemini_config)  # pylint: disable=protected-access
        check.is_false(client._debug)  # pylint: disable=protected-access
        check.equal(client._api_timeout, 600)  # pylint: disable=protected-access

    @pytest.mark.asyncio
    async def test_analyze_commit(
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

    @pytest.mark.asyncio
    async def test_analyze_commit_malformed_json(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of malformed JSON response."""
        # Setup mock with malformed JSON - will fail 4 times
        response = MagicMock()
        response.text = "```json\n{invalid json}\n```"
        mock_genai_client.aio.models.generate_content.side_effect = [
            response,
            response,
            response,
            response,  # All fail
        ]

        # Should raise after retries with malformed JSON
        with pytest.raises(GeminiClientError):
            await gemini_client.generate_commit_analysis("Test diff")

    @pytest.mark.asyncio
    async def test_synthesize_daily_activity(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily activity synthesis."""
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

    @pytest.mark.asyncio
    async def test_narrate_weekly_summary(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly narrative generation."""
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

    @pytest.mark.asyncio
    async def test_generate_changelog_entries(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test changelog entry generation."""
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

    @pytest.mark.asyncio
    async def test_exception_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of various exceptions."""
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

    @pytest.mark.asyncio
    async def test_retry_on_failure(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        mock_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test retry mechanism on API failures."""
        # Setup mock to fail then succeed
        mock_genai_client.aio.models.generate_content.side_effect = [
            ConnectError("Connection failed"),
            ConnectError("Connection failed"),
            mock_response,
        ]

        # Should eventually succeed
        result = await gemini_client.generate_commit_analysis("Test diff")

        # Verify successful result after retries
        check.is_instance(result, CommitAnalysis)
        check.equal(len(result.changes), 1)
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_prompt_truncation(
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

    @pytest.mark.asyncio
    async def test_empty_input_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of empty inputs."""
        # Setup mock
        response = MagicMock()
        response.text = '{"changes": [], "trivial": true}'
        mock_genai_client.aio.models.generate_content.return_value = response

        # Test empty commit diff
        result = await gemini_client.generate_commit_analysis("")
        check.is_instance(result, CommitAnalysis)

        # Setup for text response
        response.text = "No activity"
        mock_genai_client.aio.models.generate_content.return_value = response

        # Test empty daily summaries
        daily_result = await gemini_client.synthesize_daily_summary("", "")
        check.is_instance(daily_result, str)

        # Setup token count for weekly
        token_response = MagicMock()
        token_response.total_tokens = 100
        mock_genai_client.aio.models.count_tokens.return_value = token_response

        # Test empty weekly summary
        weekly_result = await gemini_client.generate_news_narrative("", "", "", "")
        check.is_instance(weekly_result, str)

        # Test empty changelog
        changelog_result = await gemini_client.generate_changelog_entries([])
        check.is_instance(changelog_result, str)

    @pytest.mark.asyncio
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

    def test_config_defaults(self) -> None:
        """Test GeminiClientConfig default values."""
        config = GeminiClientConfig()
        check.equal(config.model_tier1, "gemini-2.5-flash")
        check.equal(config.model_tier2, "gemini-2.5-pro")
        check.equal(config.model_tier3, "gemini-2.5-pro")
        check.equal(config.temperature, 0.5)
        check.equal(config.api_timeout, 600)
        check.is_false(config.debug)

    @pytest.mark.asyncio
    async def test_weekly_prompt_trimming(
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

    @pytest.mark.asyncio
    async def test_validation_error_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        mock_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of Pydantic validation errors."""
        # First call: raises ValidationError
        # Second call: succeeds
        mock_genai_client.aio.models.generate_content.side_effect = [
            ValidationError.from_exception_data("test", []),
            mock_response,
        ]

        # Should retry and succeed
        result = await gemini_client.generate_commit_analysis("Test diff")

        check.is_instance(result, CommitAnalysis)
        check.equal(len(result.changes), 1)
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 2)
