# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=duplicate-code

"""Analysis unit tests for git_ai_reporter.services.gemini module.

This module tests the core analysis functions: commit analysis, daily summaries,
weekly narratives, and changelog generation.
Part of the split from the original large test_gemini.py file.
"""

import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from google import genai
from httpx import ConnectError
from pydantic import ValidationError
import pytest
import pytest_check as check
# Import constants from basic test file
from test_gemini_basic import EMPTY_RESPONSE_MSG
from test_gemini_basic import EMPTY_RESPONSES_MSG
from test_gemini_basic import EXCEEDS_TARGET_MSG
from test_gemini_basic import FITTING_FAILED_MSG
from test_gemini_basic import RECEIVED_RESPONSE_MSG
from test_gemini_basic import SENDING_PROMPT_MSG
from test_gemini_basic import TIMEOUT_ERROR_MSG
from test_gemini_basic import TIMEOUT_ERRORS_MSG

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
# SHARED FIXTURES (imported from basic tests)
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


# =============================================================================
# TEST CLASSES
# =============================================================================


class TestCommitAnalysis:
    """Tests for generate_commit_analysis method."""

    async def test_successful_analysis(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        valid_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful commit analysis."""
        # Setup mock
        mock_genai_client.aio.models.generate_content.return_value = valid_response

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

    @pytest.mark.parametrize(
        "json_text,_",
        [
            ("```json\n{invalid json}\n```", "malformed JSON"),
            ("not valid json at all {", "invalid JSON"),
            ('{"invalid": "json structure"}', "validation error"),
        ],
    )
    async def test_json_parsing_errors(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        json_text: str,
        _: str,  # error_type unused in test body
    ) -> None:
        """Test handling of various JSON parsing errors."""
        # Setup mock with invalid JSON - will fail 4 times
        response = MagicMock()
        response.text = json_text
        mock_genai_client.aio.models.generate_content.side_effect = [
            response,
            response,
            response,
            response,  # All fail
        ]

        # Should raise after retries
        with pytest.raises(GeminiClientError) as exc_info:
            await gemini_client.generate_commit_analysis("Test diff")

        check.is_in("Commit analysis failed after", str(exc_info.value))

    async def test_validation_error_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        valid_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of Pydantic validation errors."""
        # First call: raises ValidationError, second call: succeeds
        mock_genai_client.aio.models.generate_content.side_effect = [
            ValidationError.from_exception_data("test", []),
            valid_response,
        ]

        # Should retry and succeed
        result = await gemini_client.generate_commit_analysis("Test diff")

        check.is_instance(result, CommitAnalysis)
        check.equal(len(result.changes), 1)
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 2)

    async def test_retry_logic_connection(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        valid_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test retry mechanism on connection failures."""
        # Setup mock to fail then succeed
        side_effect = [ConnectError("Connection failed"), ConnectError("Connection failed")]
        mock_genai_client.aio.models.generate_content.side_effect = side_effect + [valid_response]

        # Should eventually succeed
        result = await gemini_client.generate_commit_analysis("Test diff")

        # Verify successful result after retries
        check.is_instance(result, CommitAnalysis)
        check.equal(len(result.changes), 1)
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)

    async def test_retry_logic_timeout(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        valid_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test retry mechanism on timeout failures."""
        # Setup mock to fail then succeed
        side_effect = [asyncio.TimeoutError(), asyncio.TimeoutError()]
        mock_genai_client.aio.models.generate_content.side_effect = side_effect + [valid_response]

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
            FITTING_FAILED_MSG in error_msg or EXCEEDS_TARGET_MSG in error_msg,
            f"Expected fitting error message, got: {error_msg}",
        )

    async def test_debug_mode_output(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        valid_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis with debug output when debug mode is enabled."""
        # Skip test if not in debug mode
        if not gemini_client._config.debug:  # pylint: disable=protected-access
            pytest.skip("Test only applies to debug mode")

        mock_genai_client.aio.models.generate_content.return_value = valid_response

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

        # Should parse successfully
        result = await gemini_client.generate_commit_analysis("Test diff")

        check.is_instance(result, CommitAnalysis)
        check.equal(len(result.changes), 1)
        check.equal(result.changes[0].summary, "Add feature")


class TestDailySummary:
    """Tests for generate_daily_summary method."""

    async def test_successful_daily_summary(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful daily summary generation."""
        # Setup mock with summary response
        response = MagicMock()
        response.text = "Daily development summary: Added new features and fixed bugs."
        mock_genai_client.aio.models.generate_content.return_value = response

        # Call method
        result = await gemini_client.synthesize_daily_summary(
            "Test diff content", "Test diff content"
        )

        # Verify
        check.is_instance(result, str)
        check.is_in("Daily development summary", result)
        mock_genai_client.aio.models.generate_content.assert_called_once()

    async def test_empty_daily_content(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily summary with empty content."""
        # Setup mock for empty response
        response = MagicMock()
        response.text = ""
        mock_genai_client.aio.models.generate_content.return_value = response

        # Should raise error
        with pytest.raises(GeminiClientError, match=EMPTY_RESPONSE_MSG):
            await gemini_client.synthesize_daily_summary("", "")

    @pytest.mark.parametrize(
        "error_scenario",
        [TIMEOUT_ERRORS_MSG, EMPTY_RESPONSES_MSG],
    )
    async def test_retry_logic(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        error_scenario: str,
    ) -> None:
        """Test retry logic for daily summary with different error scenarios."""
        success_response = MagicMock()
        success_response.text = "Successfully generated summary after retries"

        if error_scenario == TIMEOUT_ERRORS_MSG:
            # Test timeout error scenario
            mock_genai_client.aio.models.generate_content.side_effect = [
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
                success_response,
            ]
        else:  # EMPTY_RESPONSES_MSG
            # Test empty response scenario
            empty_response = MagicMock()
            empty_response.text = ""
            mock_genai_client.aio.models.generate_content.side_effect = [
                empty_response,
                empty_response,
                success_response,
            ]

        # Should eventually succeed
        result = await gemini_client.synthesize_daily_summary("Test content", "Test content")
        check.equal(result, "Successfully generated summary after retries")
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)


class TestWeeklyNarrative:
    """Tests for generate_weekly_narrative method."""

    async def test_successful_weekly_narrative(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful weekly narrative generation."""
        # Setup mock with narrative response
        response = MagicMock()
        response.text = "This week focused on major feature development and bug fixes."
        mock_genai_client.aio.models.generate_content.return_value = response

        # Call method
        result = await gemini_client.generate_news_narrative(
            "commit_summaries", "daily_summaries", "Weekly diff content", "history"
        )

        # Verify
        check.is_instance(result, str)
        check.is_in("This week focused on", result)
        mock_genai_client.aio.models.generate_content.assert_called_once()

    async def test_empty_weekly_content(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly narrative with empty content."""
        # Setup mock for empty response
        response = MagicMock()
        response.text = ""
        mock_genai_client.aio.models.generate_content.return_value = response

        # Should raise error
        with pytest.raises(GeminiClientError, match=EMPTY_RESPONSE_MSG):
            await gemini_client.generate_news_narrative(
                "commit_summaries", "daily_summaries", "", "history"
            )

    @pytest.mark.parametrize(
        "error_scenario",
        [EMPTY_RESPONSE_MSG, TIMEOUT_ERROR_MSG],
    )
    async def test_retry_logic(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        error_scenario: str,
    ) -> None:
        """Test retry logic for weekly narrative with different error scenarios."""
        success_response = MagicMock()
        success_response.text = "Successfully generated narrative after retries"

        if error_scenario == EMPTY_RESPONSE_MSG:
            # Test empty response scenario
            empty_response = MagicMock()
            empty_response.text = ""
            mock_genai_client.aio.models.generate_content.side_effect = [
                empty_response,
                empty_response,
                success_response,
            ]
        else:  # TIMEOUT_ERROR_MSG
            # Test timeout error scenario
            mock_genai_client.aio.models.generate_content.side_effect = [
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
                success_response,
            ]

        # Should eventually succeed
        result = await gemini_client.generate_news_narrative(
            "commit_summaries", "daily_summaries", "Test content", "history"
        )
        check.equal(result, "Successfully generated narrative after retries")
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)


class TestChangelogGeneration:
    """Tests for generate_changelog_entry method."""

    async def test_successful_changelog_generation(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful changelog entry generation."""
        # Setup mock with changelog response
        response = MagicMock()
        response.text = """## [Unreleased]

### Added
- New feature implementation

### Fixed
- Bug fix for critical issue"""
        mock_genai_client.aio.models.generate_content.return_value = response

        # Call method
        result = await gemini_client.generate_changelog_entries(
            [{"category": "Added", "summary": "Weekly analysis content"}]
        )

        # Verify
        check.is_instance(result, str)
        check.is_in("## [Unreleased]", result)
        check.is_in("### Added", result)
        check.is_in("### Fixed", result)
        mock_genai_client.aio.models.generate_content.assert_called_once()

    async def test_empty_changelog_content(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test changelog generation with empty content."""
        # Setup mock for empty response
        response = MagicMock()
        response.text = ""
        mock_genai_client.aio.models.generate_content.return_value = response

        # Should raise error
        with pytest.raises(GeminiClientError, match=EMPTY_RESPONSE_MSG):
            await gemini_client.generate_changelog_entries([])

    @pytest.mark.parametrize(
        "error_scenario",
        [TIMEOUT_ERROR_MSG, EMPTY_RESPONSE_MSG],
    )
    async def test_retry_logic(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        error_scenario: str,
    ) -> None:
        """Test retry logic for changelog generation with different error scenarios."""
        success_response = MagicMock()
        success_response.text = (
            "## [Unreleased]\n\n### Fixed\n- Successfully generated after retries"
        )

        if error_scenario == TIMEOUT_ERROR_MSG:
            # Test timeout error scenario
            mock_genai_client.aio.models.generate_content.side_effect = [
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
                success_response,
            ]
        else:  # EMPTY_RESPONSE_MSG
            # Test empty response scenario
            empty_response = MagicMock()
            empty_response.text = ""
            mock_genai_client.aio.models.generate_content.side_effect = [
                empty_response,
                empty_response,
                success_response,
            ]

        # Should eventually succeed
        result = await gemini_client.generate_changelog_entries(
            [{"category": "Fixed", "summary": "Test analysis content"}]
        )
        check.is_in("Successfully generated after retries", result)
        check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)
