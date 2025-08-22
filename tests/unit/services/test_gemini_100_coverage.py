# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=duplicate-code

"""Tests to achieve comprehensive coverage for the remaining lines in gemini.py."""

import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
import pytest_check as check

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
    token_response.total_tokens = 100
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


class TestGemini100Coverage:
    """Tests for comprehensive coverage of gemini.py."""

    @pytest.mark.asyncio
    async def test_generate_commit_analysis_async_timeout_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis with asyncio.TimeoutError triggering line 268."""
        # All 4 attempts timeout
        mock_genai_client.aio.models.generate_content.side_effect = [
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
        ]

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_commit_analysis("test diff")

        check.is_in("Commit analysis failed after", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_synthesize_daily_summary_empty_response_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily summary with empty response error triggering line 333."""
        # All attempts return empty
        response = MagicMock()
        response.text = ""

        mock_genai_client.aio.models.generate_content.side_effect = [
            response,
            response,
            response,
        ]

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.synthesize_daily_summary("log", "diff")

        check.is_in("Daily summary failed after", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_generate_news_narrative_async_timeout_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test news narrative with async timeout error triggering line 353."""
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

        check.is_in("News narrative generation failed after", str(exc_info.value))

    @pytest.mark.asyncio
    async def test_generate_changelog_entries_empty_response_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test changelog entries with empty response error triggering line 371."""
        # All attempts return empty
        response = MagicMock()
        response.text = ""

        mock_genai_client.aio.models.generate_content.side_effect = [
            response,
            response,
            response,
        ]

        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_changelog_entries(
                [{"summary": "test", "category": "Bug Fix"}]
            )

        check.is_in("Changelog generation failed after", str(exc_info.value))
