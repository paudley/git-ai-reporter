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

import allure
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


@allure.feature("Gemini AI Service - Commit Analysis")
class TestCommitAnalysis:
    """Tests for generate_commit_analysis method."""

    @allure.story("Successful Analysis")
    @allure.title("Generate successful commit analysis with valid response")
    @allure.description(
        "Tests that commit analysis generates correct results when provided with valid diff and API response"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("commit-analysis", "success-case", "gemini")
    async def test_successful_analysis(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        valid_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful commit analysis."""
        with allure.step("Set up mock for successful response"):
            # Setup mock
            mock_genai_client.aio.models.generate_content.return_value = valid_response
            allure.attach(valid_response.text, "Mock Response Content", allure.attachment_type.JSON)

        with allure.step("Execute commit analysis"):
            # Call method
            result = await gemini_client.generate_commit_analysis("Test commit diff")
            allure.attach(
                f"Result type: {type(result).__name__}\nChanges count: {len(result.changes)}\nTrivial: {result.trivial}",
                "Analysis Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify analysis results"):
            # Verify
            check.is_instance(result, CommitAnalysis)
            check.equal(len(result.changes), 1)
            check.equal(result.changes[0].summary, "Add feature")
            check.equal(result.changes[0].category, "New Feature")
            check.is_false(result.trivial)
            mock_genai_client.aio.models.generate_content.assert_called_once()

    @allure.story("Empty Diff Handling")
    @allure.title("Handle empty diff input without API calls")
    @allure.description(
        "Tests that empty diffs are handled efficiently without making unnecessary API calls"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("commit-analysis", "empty-diff", "optimization")
    async def test_empty_diff_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of empty commit diffs."""
        with allure.step("Set up mock for empty response"):
            # Setup mock for empty response
            response = MagicMock()
            response.text = '{"changes": [], "trivial": true}'
            mock_genai_client.aio.models.generate_content.return_value = response
            allure.attach(response.text, "Mock Empty Response", allure.attachment_type.JSON)

        with allure.step("Execute commit analysis with empty diff"):
            # Test empty commit diff
            result = await gemini_client.generate_commit_analysis("")
            allure.attach(
                f"Result type: {type(result).__name__}\nChanges: {len(result.changes)}\nTrivial: {result.trivial}",
                "Empty Diff Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify empty diff produces trivial analysis"):
            check.is_instance(result, CommitAnalysis)
            check.equal(len(result.changes), 0)
            check.is_true(result.trivial)

    @allure.story("JSON Parsing Error Handling")
    @allure.title("Handle various JSON parsing errors in API responses")
    @allure.description(
        "Tests that different types of malformed JSON responses are handled gracefully with appropriate fallbacks"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("commit-analysis", "error-handling", "json-parsing")
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
        with allure.step(f"Set up mock with invalid JSON: {json_text[:50]}..."):
            # Setup mock with invalid JSON - will fail 4 times
            response = MagicMock()
            response.text = json_text
            allure.attach(json_text, "Invalid JSON Response", allure.attachment_type.TEXT)
            mock_genai_client.aio.models.generate_content.side_effect = [
                response,
                response,
                response,
                response,  # All fail
            ]

        with allure.step("Execute commit analysis with JSON parsing failures"):
            # Should raise after retries
            with pytest.raises(GeminiClientError) as exc_info:
                await gemini_client.generate_commit_analysis("Test diff")

            allure.attach(
                str(exc_info.value), "JSON Parsing Error Result", allure.attachment_type.TEXT
            )

        with allure.step("Verify appropriate error message after retries"):
            check.is_in("Commit analysis failed after", str(exc_info.value))

    @allure.story("Validation Error Handling")
    @allure.title("Handle Pydantic validation errors with retry")
    @allure.description(
        "Tests that Pydantic validation errors trigger appropriate retry logic and eventual success"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("commit-analysis", "validation-errors", "retry-logic")
    async def test_validation_error_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        valid_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of Pydantic validation errors."""
        with allure.step("Set up validation error followed by success"):
            # First call: raises ValidationError, second call: succeeds
            mock_genai_client.aio.models.generate_content.side_effect = [
                ValidationError.from_exception_data("test", []),
                valid_response,
            ]
            allure.attach(
                "First call: ValidationError\nSecond call: Success",
                "Validation Error Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute commit analysis with retry after validation error"):
            # Should retry and succeed
            result = await gemini_client.generate_commit_analysis("Test diff")
            allure.attach(
                f"Result type: {type(result).__name__}\nChanges: {len(result.changes)}\nCall count: {mock_genai_client.aio.models.generate_content.call_count}",
                "Validation Error Recovery Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify successful recovery after validation error"):
            check.is_instance(result, CommitAnalysis)
            check.equal(len(result.changes), 1)
            check.equal(mock_genai_client.aio.models.generate_content.call_count, 2)

    @allure.story("Connection Retry Logic")
    @allure.title("Handle connection failures with retry mechanism")
    @allure.description(
        "Tests that connection failures trigger appropriate retry logic and eventual success"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("commit-analysis", "connection-errors", "retry-logic")
    async def test_retry_logic_connection(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        valid_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test retry mechanism on connection failures."""
        with allure.step("Set up connection failures followed by success"):
            # Setup mock to fail then succeed
            side_effect = [ConnectError("Connection failed"), ConnectError("Connection failed")]
            mock_genai_client.aio.models.generate_content.side_effect = side_effect + [
                valid_response
            ]
            allure.attach(
                "2 connection failures + 1 success configured",
                "Connection Retry Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute commit analysis with connection retries"):
            # Should eventually succeed
            result = await gemini_client.generate_commit_analysis("Test diff")
            allure.attach(
                f"Result type: {type(result).__name__}\nChanges: {len(result.changes)}\nTotal calls: {mock_genai_client.aio.models.generate_content.call_count}",
                "Connection Retry Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify successful result after connection retries"):
            # Verify successful result after retries
            check.is_instance(result, CommitAnalysis)
            check.equal(len(result.changes), 1)
            check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)

    @allure.story("Timeout Retry Logic")
    @allure.title("Handle timeout failures with retry mechanism")
    @allure.description(
        "Tests that timeout failures trigger appropriate retry logic and eventual success"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("commit-analysis", "timeout-errors", "retry-logic")
    async def test_retry_logic_timeout(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        valid_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test retry mechanism on timeout failures."""
        with allure.step("Set up timeout failures followed by success"):
            # Setup mock to fail then succeed
            side_effect = [asyncio.TimeoutError(), asyncio.TimeoutError()]
            mock_genai_client.aio.models.generate_content.side_effect = side_effect + [
                valid_response
            ]
            allure.attach(
                "2 timeout errors + 1 success configured",
                "Timeout Retry Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute commit analysis with timeout retries"):
            # Should eventually succeed
            result = await gemini_client.generate_commit_analysis("Test diff")
            allure.attach(
                f"Result type: {type(result).__name__}\nChanges: {len(result.changes)}\nTotal calls: {mock_genai_client.aio.models.generate_content.call_count}",
                "Timeout Retry Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify successful result after timeout retries"):
            # Verify successful result after retries
            check.is_instance(result, CommitAnalysis)
            check.equal(len(result.changes), 1)
            check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)

    @allure.story("Retry Exhaustion")
    @allure.title("Handle retry exhaustion when max retries exceeded")
    @allure.description(
        "Tests behavior when maximum number of retries is exceeded and final error is raised"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("commit-analysis", "retry-exhaustion", "error-handling")
    async def test_retry_exhaustion(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test behavior when max retries are exceeded."""
        with allure.step("Set up persistent connection errors exceeding retry limit"):
            # Setup mock to always fail with retryable error (4 times)
            mock_genai_client.aio.models.generate_content.side_effect = [
                ConnectError("Persistent connection error"),
                ConnectError("Persistent connection error"),
                ConnectError("Persistent connection error"),
                ConnectError("Persistent connection error"),
            ]
            allure.attach(
                "4 persistent connection errors configured to exceed retry limit",
                "Retry Exhaustion Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute commit analysis and expect retry exhaustion"):
            # Should raise after exhausting retries
            with pytest.raises(GeminiClientError) as exc_info:
                await gemini_client.generate_commit_analysis("Test diff")

            allure.attach(
                str(exc_info.value), "Retry Exhaustion Error", allure.attachment_type.TEXT
            )

        with allure.step("Verify all retry attempts were made"):
            # Should have tried 4 times (initial + 3 retries)
            check.equal(mock_genai_client.aio.models.generate_content.call_count, 4)

    @allure.story("Prompt Fitting")
    @allure.title("Handle prompt fitting overflow scenarios")
    @allure.description(
        "Tests behavior when prompt content exceeds token limits and requires fitting"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("commit-analysis", "prompt-fitting", "token-limits")
    async def test_prompt_fitting_overflow(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis when prompt fitting fails due to size."""
        with allure.step("Set up token response exceeding limits"):
            # Always return over limit tokens
            token_response = MagicMock()
            token_response.total_tokens = 2000000
            mock_genai_client.aio.models.count_tokens.return_value = token_response
            allure.attach(
                f"Token count set to {token_response.total_tokens} (exceeds limit)",
                "Token Limit Overflow Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute commit analysis with oversized prompt"):
            with pytest.raises(GeminiClientError) as exc_info:
                await gemini_client.generate_commit_analysis("x" * 100000)

            allure.attach(str(exc_info.value), "Prompt Fitting Error", allure.attachment_type.TEXT)

        with allure.step("Verify prompt fitting error message"):
            # With prompt fitting, error message includes fitting details
            error_msg = str(exc_info.value)
            check.is_true(
                FITTING_FAILED_MSG in error_msg or EXCEEDS_TARGET_MSG in error_msg,
                f"Expected fitting error message, got: {error_msg}",
            )

    @allure.story("Debug Mode")
    @allure.title("Test debug mode output during commit analysis")
    @allure.description(
        "Tests that debug mode produces appropriate diagnostic output during commit analysis"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("commit-analysis", "debug-mode", "diagnostics")
    async def test_debug_mode_output(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
        valid_response: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis with debug output when debug mode is enabled."""
        with allure.step("Check if test applies to debug mode"):
            # Skip test if not in debug mode
            if not gemini_client._config.debug:  # pylint: disable=protected-access
                pytest.skip("Test only applies to debug mode")

            allure.attach(
                f"Debug mode enabled: {gemini_client._config.debug}",
                "Debug Mode Configuration",
                allure.attachment_type.TEXT,
            )

        mock_genai_client.aio.models.generate_content.return_value = valid_response

        with patch("git_ai_reporter.services.gemini.rprint") as mock_print:
            result = await gemini_client.generate_commit_analysis("test diff")

        check.is_instance(result, CommitAnalysis)
        # Should print prompt and response in debug mode
        assert any(SENDING_PROMPT_MSG in str(call) for call in mock_print.call_args_list)
        assert any(RECEIVED_RESPONSE_MSG in str(call) for call in mock_print.call_args_list)

    @allure.story("JSON Parsing")
    @allure.title("Parse JSON wrapped in markdown fence")
    @allure.description(
        "Tests that JSON responses wrapped in markdown code fences are parsed correctly"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("commit-analysis", "json-parsing", "markdown-fence")
    async def test_json_with_markdown_fence(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test handling of JSON wrapped in markdown fence."""
        with allure.step("Set up mock response with JSON in markdown fence"):
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
            allure.attach(response.text, "Mock Fenced JSON Response", allure.attachment_type.TEXT)

        with allure.step("Execute commit analysis with fenced JSON"):
            # Should parse successfully
            result = await gemini_client.generate_commit_analysis("Test diff")
            allure.attach(
                f"Result type: {type(result).__name__}\nChanges: {len(result.changes)}\nFirst change: {result.changes[0].summary}",
                "Fenced JSON Parse Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify successful parsing of fenced JSON"):
            check.is_instance(result, CommitAnalysis)
            check.equal(len(result.changes), 1)
            check.equal(result.changes[0].summary, "Add feature")


@allure.feature("Gemini AI Service - Daily Summary")
class TestDailySummary:
    """Tests for generate_daily_summary method."""

    @allure.story("Successful Summary Generation")
    @allure.title("Generate successful daily summary")
    @allure.description(
        "Tests that daily summaries are generated successfully with valid input and responses"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("daily-summary", "success-case", "gemini")
    async def test_successful_daily_summary(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful daily summary generation."""
        with allure.step("Set up mock response for daily summary"):
            # Setup mock with summary response
            response = MagicMock()
            response.text = "Daily development summary: Added new features and fixed bugs."
            mock_genai_client.aio.models.generate_content.return_value = response
            allure.attach(response.text, "Mock Daily Summary Response", allure.attachment_type.TEXT)

        with allure.step("Execute daily summary synthesis"):
            # Call method
            result = await gemini_client.synthesize_daily_summary(
                "Test diff content", "Test diff content"
            )
            allure.attach(result, "Generated Daily Summary", allure.attachment_type.TEXT)

        with allure.step("Verify daily summary content and API call"):
            # Verify
            check.is_instance(result, str)
            check.is_in("Daily development summary", result)
            mock_genai_client.aio.models.generate_content.assert_called_once()

    @allure.story("Empty Content Handling")
    @allure.title("Handle empty daily summary content")
    @allure.description(
        "Tests that empty content in daily summary generation is handled with appropriate error messages"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("daily-summary", "empty-content", "error-handling")
    async def test_empty_daily_content(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test daily summary with empty content."""
        with allure.step("Set up mock for empty response"):
            # Setup mock for empty response
            response = MagicMock()
            response.text = ""
            mock_genai_client.aio.models.generate_content.return_value = response
            allure.attach(
                "Empty response configured",
                "Mock Empty Response Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute daily summary with empty content and expect error"):
            # Should raise error
            with pytest.raises(GeminiClientError, match=EMPTY_RESPONSE_MSG) as exc_info:
                await gemini_client.synthesize_daily_summary("", "")

            allure.attach(str(exc_info.value), "Empty Content Error", allure.attachment_type.TEXT)

    @allure.story("Retry Logic")
    @allure.title("Handle retry scenarios in daily summary generation")
    @allure.description(
        "Tests that various error scenarios trigger appropriate retry logic and eventual success"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("daily-summary", "retry-logic", "error-recovery")
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
        with allure.step(f"Set up retry scenario: {error_scenario}"):
            success_response = MagicMock()
            success_response.text = "Successfully generated summary after retries"

            if error_scenario == TIMEOUT_ERRORS_MSG:
                # Test timeout error scenario
                mock_genai_client.aio.models.generate_content.side_effect = [
                    asyncio.TimeoutError(),
                    asyncio.TimeoutError(),
                    success_response,
                ]
                allure.attach(
                    "2 timeout errors + 1 success configured",
                    "Timeout Retry Setup",
                    allure.attachment_type.TEXT,
                )
            else:  # EMPTY_RESPONSES_MSG
                # Test empty response scenario
                empty_response = MagicMock()
                empty_response.text = ""
                mock_genai_client.aio.models.generate_content.side_effect = [
                    empty_response,
                    empty_response,
                    success_response,
                ]
                allure.attach(
                    "2 empty responses + 1 success configured",
                    "Empty Response Retry Setup",
                    allure.attachment_type.TEXT,
                )

        with allure.step("Execute daily summary with retry logic"):
            # Should eventually succeed
            result = await gemini_client.synthesize_daily_summary("Test content", "Test content")
            allure.attach(
                f"Result: {result}\nTotal calls: {mock_genai_client.aio.models.generate_content.call_count}",
                "Daily Summary Retry Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify successful recovery after retries"):
            check.equal(result, "Successfully generated summary after retries")
            check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)


@allure.feature("Gemini AI Service - Weekly Narrative")
class TestWeeklyNarrative:
    """Tests for generate_weekly_narrative method."""

    @allure.story("Successful Narrative Generation")
    @allure.title("Generate successful weekly narrative")
    @allure.description(
        "Tests that weekly narratives are generated successfully with valid input and responses"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("weekly-narrative", "success-case", "gemini")
    async def test_successful_weekly_narrative(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful weekly narrative generation."""
        with allure.step("Set up mock response for narrative generation"):
            # Setup mock with narrative response
            response = MagicMock()
            response.text = "This week focused on major feature development and bug fixes."
            mock_genai_client.aio.models.generate_content.return_value = response
            allure.attach(
                response.text, "Mock Weekly Narrative Response", allure.attachment_type.TEXT
            )

        with allure.step("Execute weekly narrative generation"):
            # Call method
            result = await gemini_client.generate_news_narrative(
                "commit_summaries", "daily_summaries", "Weekly diff content", "history"
            )
            allure.attach(result, "Generated Weekly Narrative", allure.attachment_type.TEXT)

        # Verify
        check.is_instance(result, str)
        check.is_in("This week focused on", result)
        mock_genai_client.aio.models.generate_content.assert_called_once()

    @allure.story("Empty Content Handling")
    @allure.title("Handle empty weekly narrative content")
    @allure.description(
        "Tests that empty content in weekly narrative generation is handled with appropriate error messages"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("weekly-narrative", "empty-content", "error-handling")
    async def test_empty_weekly_content(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test weekly narrative with empty content."""
        with allure.step("Set up mock for empty response"):
            # Setup mock for empty response
            response = MagicMock()
            response.text = ""
            mock_genai_client.aio.models.generate_content.return_value = response
            allure.attach(
                "Empty response configured",
                "Mock Empty Response Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute weekly narrative with empty content and expect error"):
            # Should raise error
            with pytest.raises(GeminiClientError, match=EMPTY_RESPONSE_MSG) as exc_info:
                await gemini_client.generate_news_narrative(
                    "commit_summaries", "daily_summaries", "", "history"
                )

            allure.attach(str(exc_info.value), "Empty Content Error", allure.attachment_type.TEXT)

    @allure.story("Retry Logic")
    @allure.title("Handle retry scenarios in weekly narrative generation")
    @allure.description(
        "Tests that various error scenarios trigger appropriate retry logic and eventual success"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("weekly-narrative", "retry-logic", "error-recovery")
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
        with allure.step(f"Set up retry scenario: {error_scenario}"):
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
                allure.attach(
                    "2 empty responses + 1 success configured",
                    "Empty Response Retry Setup",
                    allure.attachment_type.TEXT,
                )
            else:  # TIMEOUT_ERROR_MSG
                # Test timeout error scenario
                mock_genai_client.aio.models.generate_content.side_effect = [
                    asyncio.TimeoutError(),
                    asyncio.TimeoutError(),
                    success_response,
                ]
                allure.attach(
                    "2 timeout errors + 1 success configured",
                    "Timeout Retry Setup",
                    allure.attachment_type.TEXT,
                )

        with allure.step("Execute weekly narrative with retry logic"):
            # Should eventually succeed
            result = await gemini_client.generate_news_narrative(
                "commit_summaries", "daily_summaries", "Test content", "history"
            )
            allure.attach(
                f"Result: {result}\nTotal calls: {mock_genai_client.aio.models.generate_content.call_count}",
                "Weekly Narrative Retry Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify successful recovery after retries"):
            check.equal(result, "Successfully generated narrative after retries")
            check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)


@allure.feature("Gemini AI Service - Changelog Generation")
class TestChangelogGeneration:
    """Tests for generate_changelog_entry method."""

    @allure.story("Successful Changelog Generation")
    @allure.title("Generate successful changelog entries")
    @allure.description(
        "Tests that changelog entries are generated successfully with valid input and responses"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("changelog-generation", "success-case", "gemini")
    async def test_successful_changelog_generation(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test successful changelog entry generation."""
        with allure.step("Set up mock response for changelog generation"):
            # Setup mock with changelog response
            response = MagicMock()
            response.text = """## [Unreleased]

### Added
- New feature implementation

### Fixed
- Bug fix for critical issue"""
            mock_genai_client.aio.models.generate_content.return_value = response
            allure.attach(response.text, "Mock Changelog Response", allure.attachment_type.TEXT)

        with allure.step("Execute changelog entry generation"):
            # Call method
            result = await gemini_client.generate_changelog_entries(
                [{"category": "Added", "summary": "Weekly analysis content"}]
            )
            allure.attach(result, "Generated Changelog", allure.attachment_type.TEXT)

        with allure.step("Verify changelog content and structure"):
            # Verify
            check.is_instance(result, str)
            check.is_in("## [Unreleased]", result)
            check.is_in("### Added", result)
            check.is_in("### Fixed", result)
            mock_genai_client.aio.models.generate_content.assert_called_once()

    @allure.story("Empty Content Handling")
    @allure.title("Handle empty changelog content gracefully")
    @allure.description(
        "Tests that empty changelog content is handled appropriately without errors"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("changelog-generation", "empty-content", "edge-cases")
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

    @allure.story("Retry Logic")
    @allure.title("Handle retry scenarios in changelog generation")
    @allure.description(
        "Tests that various error scenarios trigger appropriate retry logic and eventual success"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("changelog-generation", "retry-logic", "error-recovery")
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
        with allure.step(f"Set up retry scenario: {error_scenario}"):
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
                allure.attach(
                    "2 timeout errors + 1 success configured",
                    "Timeout Retry Setup",
                    allure.attachment_type.TEXT,
                )
            else:  # EMPTY_RESPONSE_MSG
                # Test empty response scenario
                empty_response = MagicMock()
                empty_response.text = ""
                mock_genai_client.aio.models.generate_content.side_effect = [
                    empty_response,
                    empty_response,
                    success_response,
                ]
                allure.attach(
                    "2 empty responses + 1 success configured",
                    "Empty Response Retry Setup",
                    allure.attachment_type.TEXT,
                )

        with allure.step("Execute changelog generation with retry logic"):
            # Should eventually succeed
            result = await gemini_client.generate_changelog_entries(
                [{"category": "Fixed", "summary": "Test analysis content"}]
            )
            allure.attach(
                f"Result: {result}\nTotal calls: {mock_genai_client.aio.models.generate_content.call_count}",
                "Changelog Generation Retry Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify successful recovery after retries"):
            check.is_in("Successfully generated after retries", result)
            check.equal(mock_genai_client.aio.models.generate_content.call_count, 3)
