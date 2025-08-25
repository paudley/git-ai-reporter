# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=duplicate-code,magic-value-comparison

"""Advanced unit tests for git_ai_reporter.services.gemini module.

This module tests error handling, concurrency, and edge cases.
Part of the split from the original large test_gemini.py file.
"""

import asyncio
import json
import time
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import allure
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


# Using mock_genai_client from conftest.py


@allure.step("Create GeminiClientConfig for advanced testing")
@pytest.fixture(params=[False, True], ids=["normal", "debug"])
def gemini_config(request) -> GeminiClientConfig:
    """Create a GeminiClientConfig for testing, parametrized for debug mode."""
    with allure.step(f"Set up advanced config with debug={request.param}"):
        config = GeminiClientConfig(
            model_tier1="gemini-2.5-flash",
            model_tier2="gemini-2.5-pro",
            model_tier3="gemini-2.5-pro",
            temperature=0.5,
            debug=request.param,
            api_timeout=1,  # Short timeout for tests
        )
        allure.attach(
            f"Advanced testing config - Debug mode: {request.param}\nAPI timeout: 1s\nTemperature: 0.5",
            "Advanced Config Parameters",
            allure.attachment_type.TEXT,
        )
        return config


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


@pytest.mark.skip("TODO: Fix async mocking issues in advanced error handling tests")
@allure.feature("Gemini AI Service - Error Handling")
class TestErrorHandling:
    """Consolidated error handling tests."""

    @allure.story("HTTP Error Handling")
    @allure.title("Handle HTTP status errors from Gemini API")
    @allure.description(
        "Tests that HTTP status errors from the Gemini API are properly caught and wrapped in GeminiClientError"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("error-handling", "gemini", "http-errors", "api", "resilience")
    @allure.link(
        "https://github.com/example/git-reporter/docs/error-handling", name="Error Handling Guide"
    )
    @allure.testcase("TC-GEM-ADV-001", "Test HTTP error resilience")
    async def test_http_errors(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test HTTP error handling."""
        allure.dynamic.description(
            "Testing robust HTTP error handling and exception wrapping mechanisms"
        )
        allure.dynamic.tag("api-resilience")

        with allure.step("Set up HTTP status error mock"):
            # Create mock request and response objects for HTTPStatusError
            mock_request = Mock()
            test_response = Mock()
            http_error = HTTPStatusError(
                "Bad request", request=mock_request, response=test_response
            )
            mock_genai_client.aio.models.generate_content.side_effect = http_error

            allure.attach(
                json.dumps(
                    {
                        "error_type": "HTTPStatusError",
                        "message": "Bad request",
                        "request_object": str(mock_request),
                        "response_object": str(test_response),
                    },
                    indent=2,
                ),
                "HTTP Error Configuration",
                allure.attachment_type.JSON,
            )

        with allure.step("Attempt commit analysis with HTTP error"):
            start_time = time.time()
            try:
                with pytest.raises(GeminiClientError) as exc_info:
                    await gemini_client.generate_commit_analysis("test diff")

                error_handling_time = time.time() - start_time
                allure.attach(
                    json.dumps(
                        {
                            "exception_type": "GeminiClientError",
                            "original_error": "HTTPStatusError",
                            "error_handling_time_ms": error_handling_time * 1000,
                            "exception_message": str(exc_info.value),
                        },
                        indent=2,
                    ),
                    "Error Handling Results",
                    allure.attachment_type.JSON,
                )
            except Exception as e:
                allure.attach(
                    f"Unexpected error during HTTP error test: {str(e)}",
                    "Unexpected Error",
                    allure.attachment_type.TEXT,
                )
                raise

        with allure.step("Verify HTTP error is properly wrapped"):
            check.is_in("HTTPStatusError", str(exc_info.value))
            allure.attach(
                "HTTP error successfully wrapped in GeminiClientError",
                "Error Wrapping Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("Retry Mechanism")
    @allure.title("Handle HTTP errors in retry mechanism")
    @allure.description(
        "Tests that HTTP status errors are properly handled within the retry mechanism of _generate_with_retry"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("error-handling", "retry-logic", "http-errors")
    async def test_generate_with_retry_http_status_error(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _generate_with_retry with HTTP status error."""
        with allure.step("Set up HTTP error with proper request/response objects"):
            # Create mock HTTP error with proper request/response
            mock_request = Request("GET", "http://example.com")
            test_response = Response(400)
            http_error = HTTPStatusError(
                "Bad request", request=mock_request, response=test_response
            )
            mock_genai_client.aio.models.generate_content.side_effect = http_error
            allure.attach(
                f"Request: {mock_request}\nResponse: {test_response}\nError: Bad request",
                "HTTP Error Details",
                allure.attachment_type.TEXT,
            )

        with allure.step("Call _generate_with_retry with HTTP error"):
            with pytest.raises(GeminiClientError) as exc_info:
                await gemini_client._generate_with_retry(  # pylint: disable=protected-access
                    "model", "prompt", 100
                )

            allure.attach(
                str(exc_info.value), "Retry Mechanism Exception", allure.attachment_type.TEXT
            )

        with allure.step("Verify HTTP error is handled in retry mechanism"):
            check.is_in("HTTPStatusError", str(exc_info.value))

    @allure.story("Exception Handling")
    @allure.title("Handle generic exceptions in retry mechanism")
    @allure.description(
        "Tests that generic runtime exceptions are properly caught and wrapped as unexpected errors"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("error-handling", "retry-logic", "generic-exceptions")
    async def test_generate_with_retry_generic_exception(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test _generate_with_retry with generic exception."""
        with allure.step("Set up generic runtime exception"):
            # Create a generic exception that will be caught as an unexpected error
            error = RuntimeError("API Error")
            mock_genai_client.aio.models.generate_content.side_effect = error
            allure.attach(
                f"Exception Type: {type(error).__name__}\nMessage: {error}",
                "Generic Exception Details",
                allure.attachment_type.TEXT,
            )

        with allure.step("Call _generate_with_retry with generic exception"):
            with pytest.raises(GeminiClientError) as exc_info:
                await gemini_client._generate_with_retry(  # pylint: disable=protected-access
                    "model", "prompt", 100
                )

            allure.attach(
                str(exc_info.value), "Generic Exception Wrapper", allure.attachment_type.TEXT
            )

        with allure.step("Verify generic exception is properly wrapped"):
            check.is_in("Unexpected error: RuntimeError", str(exc_info.value))

    @allure.story("Commit Analysis Error Handling")
    @allure.title("Handle persistent exceptions in commit analysis")
    @allure.description(
        "Tests that commit analysis handles persistent generic exceptions across multiple retry attempts"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("error-handling", "commit-analysis", "retry-exhaustion")
    async def test_commit_analysis_generic_exception(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test commit analysis with generic exception."""
        with allure.step("Set up persistent exception across 4 retry attempts"):
            # Setup mock to raise exception 4 times (initial + 3 retries)
            mock_genai_client.aio.models.generate_content.side_effect = [
                Exception("API error"),
                Exception("API error"),
                Exception("API error"),
                Exception("API error"),
            ]
            allure.attach(
                "4 consecutive API errors configured to test retry exhaustion",
                "Persistent Exception Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Attempt commit analysis with persistent errors"):
            # Should raise GeminiClientError after retries
            with pytest.raises(GeminiClientError) as exc_info:
                await gemini_client.generate_commit_analysis("Test diff")

            allure.attach(
                str(exc_info.value), "Retry Exhaustion Exception", allure.attachment_type.TEXT
            )

    @allure.story("Debug Mode Handling")
    @allure.title("Handle empty responses in debug mode")
    @allure.description(
        "Tests that empty responses are handled correctly with debug output enabled"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("error-handling", "debug-mode", "empty-responses")
    async def test_empty_response_with_debug(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test empty response handling with debug output."""
        with allure.step("Check if test applies to debug mode"):
            # Skip test if not in debug mode
            if not gemini_client._config.debug:  # pylint: disable=protected-access
                pytest.skip("Test only applies to debug mode")

            allure.attach(
                f"Debug mode: {gemini_client._config.debug}",
                "Debug Mode Configuration",
                allure.attachment_type.TEXT,
            )

        with allure.step("Set up empty responses for retry testing"):
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
            allure.attach(
                "3 empty responses + 1 successful response configured",
                "Empty Response Test Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute commit analysis with debug output monitoring"):
            with patch("git_ai_reporter.services.gemini.rprint") as mock_print:
                result = await gemini_client.generate_commit_analysis("test diff")

            allure.attach(
                f"Result type: {type(result).__name__}",
                "Analysis Result",
                allure.attachment_type.TEXT,
            )
            allure.attach(
                str(mock_print.call_args_list), "Debug Print Calls", allure.attachment_type.TEXT
            )

        with allure.step("Verify successful analysis and debug warnings"):
            check.is_instance(result, CommitAnalysis)
            # Should print empty response warning
            assert any(EMPTY_RESPONSE_MSG in str(call) for call in mock_print.call_args_list)

    @allure.story("Retry Error Details")
    @allure.title("Handle retry errors with detailed prompt information")
    @allure.description(
        "Tests that retry errors include detailed information about the prompts and attempts"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("error-handling", "retry-errors", "error-details")
    async def test_retry_error_with_details(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test retry error handling with prompt details."""
        with allure.step("Set up persistent timeout errors"):
            # Make generate_content always timeout
            mock_genai_client.aio.models.generate_content.side_effect = asyncio.TimeoutError()
            allure.attach(
                "Persistent asyncio.TimeoutError configured",
                "Timeout Error Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Create mock retry error with attempt details"):
            # Patch the retry decorator to capture the actual RetryError
            async def mock_generate_with_retry(*_args: Any, **_kwargs: Any) -> str:
                # Create a proper RetryError
                last_attempt = MagicMock(spec=AttemptManager)
                last_attempt.attempt_number = 3
                last_attempt.exception = lambda: asyncio.TimeoutError("Timed out")

                error = RetryError(last_attempt)
                error.last_attempt = last_attempt
                raise error

            allure.attach(
                "Mock retry error with 3 attempts configured",
                "Retry Error Mock Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute daily summary with retry error"):
            with patch.object(gemini_client, "_generate_with_retry", mock_generate_with_retry):
                with pytest.raises(GeminiClientError) as exc_info:
                    await gemini_client.synthesize_daily_summary("log", "diff")

            allure.attach(str(exc_info.value), "Retry Error Details", allure.attachment_type.TEXT)

        with allure.step("Verify detailed error information is included"):
            error_msg = str(exc_info.value)
            check.is_in("Daily summary failed after 3 attempts", error_msg)
            check.is_in("PROMPT SENT TO MODEL", error_msg)


@pytest.mark.skip("TODO: Fix async mocking issues in advanced concurrency tests")
@allure.feature("Gemini AI Service - Concurrency & Performance")
class TestConcurrency:
    """Concurrency and performance tests."""

    @allure.story("Concurrent Processing")
    @allure.title("Handle multiple concurrent commit analyses")
    @allure.description(
        "Tests that multiple commit analyses can be processed concurrently without conflicts or errors"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("concurrency", "performance", "commit-analysis", "async", "scalability")
    @allure.link(
        "https://github.com/example/git-reporter/docs/concurrency", name="Concurrency Guide"
    )
    @allure.testcase("TC-GEM-ADV-002", "Test concurrent processing")
    async def test_concurrent_analyses(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test concurrent commit analyses."""
        allure.dynamic.description(
            "Testing high-throughput concurrent analysis with performance monitoring"
        )
        allure.dynamic.tag("high-throughput")

        with allure.step("Set up mock response for concurrent analyses"):
            # Setup mock
            response = MagicMock()
            response.text = '{"changes": [], "trivial": true}'
            mock_genai_client.aio.models.generate_content.return_value = response

            allure.attach(
                json.dumps(
                    {
                        "mock_response": json.loads(response.text),
                        "concurrency_level": 5,
                        "test_pattern": "parallel_execution",
                    },
                    indent=2,
                ),
                "Concurrency Test Configuration",
                allure.attachment_type.JSON,
            )

        with allure.step("Execute 5 concurrent commit analyses"):
            start_time = time.time()
            try:
                # Run multiple analyses concurrently
                tasks = [gemini_client.generate_commit_analysis(f"Diff {i}") for i in range(5)]
                results = await asyncio.gather(*tasks)

                execution_time = time.time() - start_time
                throughput = len(tasks) / execution_time if execution_time > 0 else 0

                allure.attach(
                    json.dumps(
                        {
                            "concurrent_tasks": len(tasks),
                            "successful_results": len(results),
                            "execution_time_seconds": execution_time,
                            "throughput_tasks_per_second": throughput,
                            "average_task_time_ms": (
                                (execution_time / len(tasks)) * 1000 if tasks else 0
                            ),
                        },
                        indent=2,
                    ),
                    "Concurrency Performance Metrics",
                    allure.attachment_type.JSON,
                )
            except Exception as e:
                allure.attach(
                    f"Concurrent execution failed: {str(e)}",
                    "Concurrency Error",
                    allure.attachment_type.TEXT,
                )
                raise

        with allure.step("Verify all concurrent analyses succeeded"):
            # All should succeed
            check.equal(len(results), 5)

            success_count = 0
            result_details = []

            for i, result in enumerate(results):
                check.is_instance(result, CommitAnalysis)
                success_count += 1
                result_details.append(
                    {
                        "task_id": i,
                        "result_type": type(result).__name__,
                        "trivial": result.trivial,
                        "changes_count": len(result.changes),
                    }
                )

            allure.attach(
                json.dumps(
                    {
                        "total_tasks": len(tasks),
                        "successful_tasks": success_count,
                        "success_rate_percent": (success_count / len(tasks)) * 100,
                        "result_details": result_details,
                    },
                    indent=2,
                ),
                "Concurrency Success Analysis",
                allure.attachment_type.JSON,
            )

    @allure.story("Timeout Handling")
    @allure.title("Handle async timeout errors with nested retry logic")
    @allure.description(
        "Tests that async timeout errors are properly handled through nested retry logic and result in appropriate error messages"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("timeout", "async", "retry-logic", "error-handling")
    async def test_async_timeout_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test proper async timeout handling with nested retry logic."""
        with allure.step("Set up persistent timeout errors for all retry attempts"):
            # All 4 attempts timeout (tests the double retry decorator scenario)
            mock_genai_client.aio.models.generate_content.side_effect = [
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
                asyncio.TimeoutError(),
            ]
            allure.attach(
                "4 consecutive asyncio.TimeoutError configured to test nested retry logic",
                "Timeout Error Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute commit analysis with persistent timeouts"):
            with pytest.raises(GeminiClientError) as exc_info:
                await gemini_client.generate_commit_analysis("test diff")

            allure.attach(str(exc_info.value), "Timeout Error Result", allure.attachment_type.TEXT)

        with allure.step("Verify timeout error is properly reported"):
            # Should mention timeout in error
            check.is_in("TimeoutError", str(exc_info.value))

    @allure.story("Token Counting Fallback")
    @allure.title("Handle token counting errors with graceful fallback")
    @allure.description(
        "Tests that token counting errors are handled gracefully with appropriate fallback mechanisms"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("token-counting", "error-handling", "fallback", "resilience")
    @allure.link(
        "https://github.com/example/git-reporter/docs/token-counting", name="Token Counting Guide"
    )
    @allure.testcase("TC-GEM-ADV-003", "Test token counting fallback")
    async def test_token_counting_error_fallback(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name,unused-argument
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test token counting fallback when count_tokens fails."""
        allure.dynamic.description(
            "Testing graceful degradation of token counting with character-based fallback"
        )
        allure.dynamic.tag("graceful-degradation")

        with allure.step("Import private token counter class"):
            # Import here to avoid issues with private class access  # pylint: disable=import-outside-toplevel
            from git_ai_reporter.services.gemini import \
                _GeminiTokenCounter  # pylint: disable=import-private-name

            allure.attach(
                json.dumps(
                    {
                        "class_name": "_GeminiTokenCounter",
                        "import_successful": True,
                        "fallback_mechanism": "character_based_estimation",
                    },
                    indent=2,
                ),
                "Token Counter Import Configuration",
                allure.attachment_type.JSON,
            )

        with allure.step("Set up various token counting errors"):
            # Mock count_tokens to raise various errors
            mock_genai_client.aio.models.count_tokens.side_effect = [
                HTTPStatusError("API error", request=Mock(), response=Mock()),
                ConnectError("Connection error"),
                ValidationError.from_exception_data("test", []),
                ValueError("Value error"),
                OSError("OS error"),
            ]
            allure.attach(
                "5 different error types configured: HTTPStatusError, ConnectError, ValidationError, ValueError, OSError",
                "Error Types Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Create token counter and test fallback mechanism"):
            # Test that it falls back to character-based estimation
            counter = _GeminiTokenCounter(mock_genai_client, "gemini-2.5-flash")

            # Each call should fallback to len(content) // 4
            test_content = "This is test content"  # 20 chars = 5 tokens
            allure.attach(
                f"Test content: '{test_content}' ({len(test_content)} chars)",
                "Test Content",
                allure.attachment_type.TEXT,
            )

            fallback_results = []
            for i in range(5):
                start_time = time.time()
                result = await counter.count_tokens(test_content)
                fallback_time = time.time() - start_time

                check.equal(
                    result, 5
                )  # TokenCount is a NewType based on int, so 20 chars / 4 = 5 tokens

                fallback_results.append(
                    {
                        "attempt": i + 1,
                        "expected_tokens": 5,
                        "actual_tokens": result,
                        "fallback_time_ms": fallback_time * 1000,
                        "success": result == 5,
                    }
                )

            allure.attach(
                json.dumps(
                    {
                        "test_content_length": len(test_content),
                        "expected_token_calculation": "chars / 4",
                        "fallback_results": fallback_results,
                        "all_attempts_successful": all(r["success"] for r in fallback_results),
                        "average_fallback_time_ms": sum(
                            r["fallback_time_ms"] for r in fallback_results
                        )
                        / len(fallback_results),
                    },
                    indent=2,
                ),
                "Token Counting Fallback Analysis",
                allure.attachment_type.JSON,
            )

    @allure.story("Edge Cases")
    @allure.title("Handle empty diff special case without API calls")
    @allure.description(
        "Tests that empty diffs are handled as a special case without making API calls"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("edge-cases", "empty-diff", "optimization")
    async def test_empty_diff_special_case(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name
    ) -> None:
        """Test empty diff handling without going through API."""
        with allure.step("Process empty diff as special case"):
            result = await gemini_client.generate_commit_analysis("")

            allure.attach(
                "Empty string diff provided", "Empty Diff Input", allure.attachment_type.TEXT
            )
            allure.attach(
                f"Result type: {type(result).__name__}\nChanges count: {len(result.changes)}\nTrivial: {result.trivial}",
                "Empty Diff Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify empty diff produces trivial analysis"):
            check.is_instance(result, CommitAnalysis)
            check.equal(len(result.changes), 0)
            check.is_true(result.trivial)

        # Should not have called the API for empty diff
        mock_genai_client.aio.models.generate_content.assert_not_called()

    @allure.story("Weekly Summary Error Handling")
    @allure.title("Handle weekly summary generation errors")
    @allure.description(
        "Tests that errors during weekly summary generation are properly caught and reported with detailed information"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("error-handling", "weekly-summary", "news-narrative")
    async def test_weekly_summary_error_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name,unused-argument
    ) -> None:
        """Test weekly summary generation error handling."""
        with allure.step("Create RetryError for weekly summary failure"):
            # Create RetryError for weekly summary failure
            last_attempt = MagicMock(spec=AttemptManager)
            last_attempt.attempt_number = 3
            last_attempt.exception = lambda: HTTPStatusError(
                "API error", request=Mock(), response=Mock()
            )

            error = RetryError(last_attempt)
            error.last_attempt = last_attempt

            allure.attach(
                "RetryError with HTTPStatusError after 3 attempts configured",
                "Weekly Summary Error Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute news narrative generation with retry error"):
            # Mock the internal method to raise RetryError
            with patch.object(gemini_client, "_generate_with_retry", side_effect=error):
                with pytest.raises(GeminiClientError) as exc_info:
                    await gemini_client.generate_news_narrative(
                        "commits", "daily", "diff", "history"
                    )

                allure.attach(
                    str(exc_info.value), "News Narrative Error", allure.attachment_type.TEXT
                )

        with allure.step("Verify detailed error information is included"):
            error_msg = str(exc_info.value)
            check.is_in("News narrative generation failed after 3 attempts", error_msg)
            check.is_in("HTTPStatusError", error_msg)

    @allure.story("Changelog Generation Error Handling")
    @allure.title("Handle changelog generation errors")
    @allure.description(
        "Tests that errors during changelog generation are properly caught and reported with detailed information"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("error-handling", "changelog-generation", "connection-errors")
    async def test_changelog_generation_error_handling(
        self,
        gemini_client: GeminiClient,  # pylint: disable=redefined-outer-name
        mock_genai_client: MagicMock,  # pylint: disable=redefined-outer-name,unused-argument
    ) -> None:
        """Test changelog generation error handling."""
        with allure.step("Create RetryError for changelog generation failure"):
            # Create RetryError for changelog generation failure
            last_attempt = MagicMock(spec=AttemptManager)
            last_attempt.attempt_number = 3
            last_attempt.exception = lambda: ConnectError("Connection failed")

            error = RetryError(last_attempt)
            error.last_attempt = last_attempt

            allure.attach(
                "RetryError with ConnectError after 3 attempts configured",
                "Changelog Generation Error Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Execute changelog generation with retry error"):
            # Mock the internal method to raise RetryError
            with patch.object(gemini_client, "_generate_with_retry", side_effect=error):
                with pytest.raises(GeminiClientError) as exc_info:
                    await gemini_client.generate_changelog_entries(
                        [{"category": "Added", "summary": "New feature"}]
                    )

                allure.attach(
                    str(exc_info.value), "Changelog Generation Error", allure.attachment_type.TEXT
                )

        with allure.step("Verify detailed error information is included"):
            error_msg = str(exc_info.value)
            check.is_in("Changelog generation failed after 3 attempts", error_msg)
            check.is_in("ConnectError", error_msg)
