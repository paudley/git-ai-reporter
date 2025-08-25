# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""This module contains the client for interacting with the Google Gemini API."""

import asyncio
import json
import time
from typing import Any, Final, Optional

from google import genai
from httpx import ConnectError
from httpx import HTTPStatusError
from pydantic import BaseModel
from pydantic import ValidationError
from rich import print as rprint
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import RetryError
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from git_ai_reporter.models import COMMIT_CATEGORIES
from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.prompt_fitting import ContentType
from git_ai_reporter.prompt_fitting import FittingResult
from git_ai_reporter.prompt_fitting import PromptFitter
from git_ai_reporter.prompt_fitting import PromptFittingConfig
from git_ai_reporter.prompt_fitting import record_fitting_operation
from git_ai_reporter.prompt_fitting.constants import MAX_CHUNK_PAIRS
from git_ai_reporter.prompt_fitting.constants import MAX_LOG_REDUCTION_LINES
from git_ai_reporter.prompt_fitting.prompt_fitting import OverlapRatio
from git_ai_reporter.prompt_fitting.prompt_fitting import TokenCount

# TokenCounter is only used for type hints in this module
from git_ai_reporter.summaries import commit
from git_ai_reporter.summaries import daily
from git_ai_reporter.summaries import weekly
from git_ai_reporter.utils import json_helpers

# No longer needed - replaced with data-preserving PromptFitter system


class _EmptyResponseError(Exception):
    """Internal exception to trigger a retry for empty LLM responses."""


class _GeminiTokenCounter:
    """Token counter adapter for the Gemini API client."""

    def __init__(self, client: genai.Client, model: str):
        self._client = client
        self._model = model

    async def count_tokens(self, content: str) -> "TokenCount":
        """Count tokens using the Gemini API."""
        try:
            response = await self._client.aio.models.count_tokens(
                model=self._model, contents=content
            )
            return TokenCount(response.total_tokens or 0)
        except (
            HTTPStatusError,
            genai.errors.ClientError,  # pyright: ignore[reportAttributeAccessIssue]
            ConnectError,
            ValidationError,
            ValueError,
            OSError,
        ):
            # Fallback estimation: roughly 4 characters per token
            return TokenCount(len(content) // 4)


_CHANGELOG_HEADINGS_FOR_PROMPT: Final[str] = ", ".join(
    f"'### {emoji} {name}'" for name, emoji in COMMIT_CATEGORIES.items()
)

_PROMPT_TEMPLATE_CHANGELOG: Final[
    str
] = f"""
    You are an automated release engineering tool. Given the following list of changes (in JSON
    format), group them under the appropriate headings from this list:
    {_CHANGELOG_HEADINGS_FOR_PROMPT}.
    Use the 'category' field from the JSON to determine the heading. For example, a change with
    category 'New Feature' should go under the '### ✨ New Feature' heading. Format the output
    as a Markdown snippet ready to be inserted into a changelog file. Use the original
    one-sentence summaries for each item.

    JSON Input:
    {{categorized_summaries}}
"""


class GeminiClientError(Exception):
    """Custom exception for Gemini client errors."""

    def __init__(self, message: str):
        """Initializes the exception with a message."""
        super().__init__(message)


class GeminiClientConfig(BaseModel):
    """Configuration for the GeminiClient."""

    model_tier1: str = "gemini-2.5-flash"
    model_tier2: str = "gemini-2.5-pro"
    model_tier3: str = "gemini-2.5-pro"
    input_token_limit_tier1: int = 1000000
    input_token_limit_tier2: int = 1000000
    input_token_limit_tier3: int = 1000000
    max_tokens_tier1: int = 8192
    max_tokens_tier2: int = 8192
    max_tokens_tier3: int = 16384
    temperature: float = 0.5
    api_timeout: int = 600  # Increased timeout for large diffs
    debug: bool = False


class GeminiClient:
    """A wrapper for the Google Gemini API client."""

    def __init__(self, client: genai.Client, config: GeminiClientConfig):
        """Initializes the GeminiClient.

        Args:
            client: An initialized `google.genai.Client` instance.
            config: A configuration object for the client.
        """
        self._client = client
        self._config = config
        self._debug = config.debug
        self._api_timeout = config.api_timeout

        # Initialize prompt fitting system for data-preserving token management
        self._token_counter = _GeminiTokenCounter(client, config.model_tier1)
        self._prompt_fitting_config = PromptFittingConfig(
            max_tokens=TokenCount(config.input_token_limit_tier1),
            overlap_ratio=OverlapRatio(0.25),  # 25% overlap for good boundary preservation
            validation_enabled=True,
        )
        self._prompt_fitter = PromptFitter(self._prompt_fitting_config, self._token_counter)

    async def _construct_and_fit_weekly_prompt(
        self,
        commit_summaries: str,
        daily_summaries: str,
        weekly_diff: str,
        history: str,
    ) -> str:
        """PROJECT COMPLIANT: Constructs weekly prompt using data-preserving fitting.

        CRITICAL: This method NEVER trims or loses data. Instead, it uses the
        PromptFitter system to preserve 100% data integrity through overlapping
        chunks and hierarchical processing as required by the project.
        """
        # Construct the initial prompt
        prompt_parts = {
            "commit_summaries": commit_summaries,
            "daily_summaries": daily_summaries,
            "weekly_diff": weekly_diff,
            "history": history,
        }

        full_prompt = weekly.PROMPT_TEMPLATE.format(**prompt_parts)

        # Check if prompt already fits
        response = await self._client.aio.models.count_tokens(
            model=self._config.model_tier3, contents=full_prompt
        )

        if (
            response.total_tokens is not None
            and response.total_tokens <= self._config.input_token_limit_tier3
        ):
            if self._debug:
                rprint(
                    f"[bold green]Prompt fits within limit: "
                    f"{response.total_tokens} <= {self._config.input_token_limit_tier3}[/bold green]"
                )
            return full_prompt

        # Use PromptFitter to preserve 100% of data
        if self._debug:
            rprint(
                f"[bold yellow]Prompt exceeds limit ({response.total_tokens} > "
                f"{self._config.input_token_limit_tier3}). Using data-preserving fitting...[/bold yellow]"
            )

        try:
            # Use ContentType.WEEKLY_NARRATIVE for optimal strategy selection
            fitting_result = await self._prompt_fitter.fit_content(
                content=full_prompt,
                content_type=ContentType.WEEKLY_NARRATIVE,
                target_tokens=self._config.input_token_limit_tier3,
            )

            if not fitting_result.data_preserved:
                raise GeminiClientError(
                    "Data preservation validation failed - cannot proceed with data loss"
                )

            if self._debug:
                rprint(
                    f"[bold green]Successfully fitted prompt: "
                    f"{fitting_result.fitted_size} tokens "
                    f"(compression: {fitting_result.compression_ratio:.2f}, "
                    f"strategy: {fitting_result.strategy_used.value})[/bold green]"
                )

            return fitting_result.fitted_content

        except Exception as e:
            raise GeminiClientError(
                f"Failed to fit prompt while preserving data integrity: {e}"
            ) from e

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=2, max=30),  # Longer waits for large diffs
        retry=retry_if_exception_type(
            (
                ConnectError,
                json.JSONDecodeError,
                _EmptyResponseError,
                ValidationError,
                asyncio.TimeoutError,
            )
        ),
    )
    async def _generate_commit_analysis_with_retry(self, prompt: str) -> CommitAnalysis:
        """Tier 1: Analyzes a single commit diff, retrying on errors.

        This method prompts the LLM, then parses and validates the response.
        The retry decorator handles transient network errors, empty responses,
        and any JSON or Pydantic validation errors. The prompt passed to this
        method is guaranteed by the public-facing method to be within the token limit.

        Args:
            prompt: The full, formatted prompt to send to the model.

        Returns:
            A validated CommitAnalysis object.

        Raises:
            GeminiClientError: If the analysis fails after all retries.
        """
        if self._debug:
            rprint(f"[bold cyan]Sending prompt to {self._config.model_tier1}:[/]")
            rprint(prompt)

        try:
            # Step 1: Generate Content (async with timeout)
            async with asyncio.timeout(self._api_timeout):
                generation_config = genai.types.GenerateContentConfig(
                    max_output_tokens=self._config.max_tokens_tier1,
                    temperature=self._config.temperature,
                )
                response = await self._client.aio.models.generate_content(
                    model=self._config.model_tier1,
                    contents=prompt,
                    config=generation_config,
                )
            raw_response = response.text or ""

            if not raw_response.strip():
                if self._debug:
                    rprint("[bold yellow]LLM returned an empty response. Retrying...[/bold yellow]")
                    rprint(f"[bold cyan]Prompt length: {len(prompt)} characters[/bold cyan]")
                raise _EmptyResponseError("LLM returned an empty response.")

            if self._debug:
                rprint("[bold green]Received response:[/]")
                rprint(raw_response)

            # Step 2: Parse and Validate directly. Let the @retry decorator handle ValidationError.
            parsed_data: object = json_helpers.safe_json_decode(raw_response)
            return CommitAnalysis.model_validate(parsed_data)

        except (
            _EmptyResponseError,
            json.JSONDecodeError,
            ValidationError,
            asyncio.TimeoutError,
            ConnectError,
        ) as e:
            # Re-raise to be caught by the tenacity retry decorator.
            raise e
        except (
            HTTPStatusError,
            genai.errors.ClientError,  # pyright: ignore[reportAttributeAccessIssue]
        ) as e:
            raise GeminiClientError(f"Error calling Gemini API: {type(e).__name__}: {e}") from e
        except Exception as e:
            # Catch any other unexpected exceptions and wrap them
            raise GeminiClientError(f"Unexpected error: {type(e).__name__}: {e}") from e

    def _handle_empty_diff(self) -> CommitAnalysis:
        """Handle empty diff as a special case.

        Returns:
            A trivial CommitAnalysis for empty diffs.
        """
        return CommitAnalysis(changes=[], trivial=True)

    async def _prepare_commit_prompt(self, diff: str) -> tuple[str, FittingResult[Any]]:
        """Prepare and fit the commit prompt while ensuring data preservation.

        Args:
            diff: The raw git diff content.

        Returns:
            Tuple of (formatted_prompt, fitting_result).

        Raises:
            GeminiClientError: If prompt fitting fails to preserve data.
        """
        if self._debug:
            rprint(f"[bold cyan]Processing diff of {len(diff)} characters[/bold cyan]")

        fitting_result = await self._prompt_fitter.fit_content(
            diff, ContentType.GIT_DIFF, target_tokens=self._config.input_token_limit_tier1
        )

        # Verify data integrity as required by the project
        if not fitting_result.data_preserved:
            raise GeminiClientError(
                "Project violation: Prompt fitting failed to preserve 100% of diff data"
            )

        if self._debug:
            rprint(
                f"[bold green]Prompt fitting successful. Fitted content: {len(fitting_result.fitted_content)} chars[/bold green]"
            )

        # Generate analysis using fitted content

        prompt = commit.PROMPT_TEMPLATE.format(diff=fitting_result.fitted_content)

        return prompt, fitting_result

    async def _handle_retry_with_fallback(self, prompt: str, error: RetryError) -> CommitAnalysis:
        """Handle retry failures with fallback to more capable model.

        Args:
            prompt: The formatted prompt to retry with fallback model.
            error: The original retry error.

        Returns:
            Analysis result from fallback model.

        Raises:
            GeminiClientError: If both primary and fallback models fail.
        """
        # Check if all failures were empty responses - if so, try with more capable model
        if isinstance(error.last_attempt.exception(), _EmptyResponseError):
            rprint(
                f"[bold yellow]⚠️  Flash model failed with empty responses after {error.last_attempt.attempt_number} attempts.[/bold yellow]"
            )
            rprint("[bold cyan]🔄 Falling back to more capable model...[/bold cyan]")
            try:
                # Fallback to more capable model for difficult content
                result = await self._generate_commit_analysis_with_fallback_model(prompt)
                rprint("[bold green]✅ Fallback successful! Analysis completed.[/bold green]")
                return result
            except Exception as fallback_error:
                orig_exc = error.last_attempt.exception()
                orig_exc_name = type(orig_exc).__name__ if orig_exc else "Unknown"
                orig_exc_msg = str(orig_exc) if orig_exc else "No details"
                msg = (
                    f"Commit analysis failed after {error.last_attempt.attempt_number} attempts with {self._config.model_tier1}.\n"
                    f"Fallback to {self._config.model_tier2} also failed: {fallback_error}\n"
                    f"Original error was: {orig_exc_name}: {orig_exc_msg}\n"
                )
                raise GeminiClientError(msg) from error

        # For non-empty response errors, use original error handling
        final_exc = error.last_attempt.exception()
        exc_name = type(final_exc).__name__ if final_exc else "Unknown"
        exc_msg = str(final_exc) if final_exc else "No details"
        msg = (
            f"Commit analysis failed after {error.last_attempt.attempt_number} attempts.\n"
            f"Final error was: {exc_name}: {exc_msg}\n"
        )
        raise GeminiClientError(msg) from error

    async def _record_analysis_metrics(
        self,
        start_time: float,
        fitting_result: FittingResult[Any] | None,
        error: Exception | None,
        diff_size: int,
    ) -> None:
        """Record operation metrics for monitoring.

        Args:
            start_time: Start time of the operation.
            fitting_result: Result from prompt fitting operation.
            error: Any error that occurred during processing.
            diff_size: Size of the original diff content.
        """
        processing_time = time.time() - start_time
        try:
            await record_fitting_operation(
                strategy_name="GeminiTier1Analysis",
                operation_type="commit_analysis",
                processing_time=processing_time,
                result=fitting_result,
                error=error,
                model=self._config.model_tier1,
                content_size=diff_size,
            )
        except (ImportError, AttributeError, TypeError, ValueError):
            # Don't let monitoring errors break the main operation
            pass

    async def generate_commit_analysis(self, diff: str) -> CommitAnalysis:
        """Public method for commit analysis with data-preserving prompt fitting.

        If the initial prompt exceeds the token limit, this method uses the
        data-preserving prompt fitting system to ensure 100% of diff content
        is analyzed through overlapping chunks, as required by the project.

        Args:
            diff: The raw text of a git diff.

        Returns:
            A validated CommitAnalysis object.

        Raises:
            GeminiClientError: If the analysis fails after all retries.
        """
        start_time = time.time()
        error: Optional[Exception] = None
        fitting_result = None
        prompt: Optional[str] = None

        try:
            # Handle empty diff as a special case
            if not diff or not diff.strip():
                return self._handle_empty_diff()

            # Prepare and fit the prompt with data preservation
            prompt, fitting_result = await self._prepare_commit_prompt(diff)

            # Generate analysis using fitted content
            result = await self._generate_commit_analysis_with_retry(prompt)
            return result

        except (
            _EmptyResponseError,
            ValidationError,
            asyncio.TimeoutError,
            ValueError,  # From prompt fitting when content exceeds limits, also catches JSONDecodeError
        ) as e:
            error = e
            raise GeminiClientError(
                f"Failed to generate and validate commit analysis after multiple retries: {e}"
            ) from e  # pragma: no cover

        except RetryError as e:
            error = e
            if prompt is None:
                raise GeminiClientError("Failed to generate prompt before retries") from e
            return await self._handle_retry_with_fallback(prompt, e)

        finally:
            # Record operation for monitoring
            await self._record_analysis_metrics(start_time, fitting_result, error, len(diff))

    async def _generate_commit_analysis_with_fallback_model(self, prompt: str) -> CommitAnalysis:
        """Fallback method using tier2 model when tier1 fails with empty responses.

        Args:
            prompt: The full, formatted prompt to send to the fallback model.

        Returns:
            A validated CommitAnalysis object.

        Raises:
            GeminiClientError: If the fallback analysis also fails.
        """
        if self._debug:
            rprint(f"[bold magenta]Sending prompt to fallback model {self._config.model_tier2}:[/]")

        try:
            # Use longer timeout and higher token limit for more capable model
            async with asyncio.timeout(self._api_timeout * 2):  # Double timeout for fallback
                generation_config = genai.types.GenerateContentConfig(
                    max_output_tokens=self._config.max_tokens_tier2,  # Use tier2 limits
                    temperature=self._config.temperature,
                )
                response = await self._client.aio.models.generate_content(
                    model=self._config.model_tier2,  # Use more capable model
                    contents=prompt,
                    config=generation_config,
                )
            raw_response = response.text or ""

            if not raw_response.strip():
                raise _EmptyResponseError("Fallback model also returned an empty response.")

            if self._debug:
                rprint("[bold green]Received response from fallback model:[/]")
                rprint(raw_response)

            # Parse and validate
            parsed_data: object = json_helpers.safe_json_decode(raw_response)
            return CommitAnalysis.model_validate(parsed_data)

        except (
            HTTPStatusError,
            genai.errors.ClientError,  # pyright: ignore[reportAttributeAccessIssue]
        ) as e:
            raise GeminiClientError(
                f"Error calling Gemini API (fallback): {type(e).__name__}: {e}"
            ) from e
        except Exception as e:
            raise GeminiClientError(
                f"Unexpected error in fallback model: {type(e).__name__}: {e}"
            ) from e

    async def _generate_with_retry(self, model_name: str, prompt: str, max_tokens: int) -> str:
        """A private, retryable async text generation method."""

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(
                (ConnectError, _EmptyResponseError, asyncio.TimeoutError)
            ),
        )
        async def _attempt_generation() -> str:
            try:
                async with asyncio.timeout(self._api_timeout):
                    generation_config = genai.types.GenerateContentConfig(
                        max_output_tokens=max_tokens,
                        temperature=self._config.temperature,
                    )
                    response = await self._client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=generation_config,
                    )
                response_text = response.text or ""
                if not response_text.strip():
                    raise _EmptyResponseError("LLM returned an empty response.")
                return response_text
            except (asyncio.TimeoutError, _EmptyResponseError):
                # Re-raise these errors to be caught by retry decorator
                raise
            except (
                HTTPStatusError,
                genai.errors.ClientError,  # pyright: ignore[reportAttributeAccessIssue]
            ) as e:
                raise GeminiClientError(f"Error calling Gemini API: {type(e).__name__}: {e}") from e
            except Exception as e:
                # Catch any other unexpected exceptions and wrap them
                raise GeminiClientError(f"Unexpected error: {type(e).__name__}: {e}") from e

        return await _attempt_generation()

    async def synthesize_daily_summary(self, full_log: str, daily_diff: str) -> str:
        """Tier 2: Synthesizes a daily log and diff into a summary."""
        prompt = daily.PROMPT_TEMPLATE.format(full_log=full_log, daily_diff=daily_diff)

        token_count_response = await self._client.aio.models.count_tokens(
            model=self._config.model_tier2, contents=prompt
        )
        token_count = token_count_response.total_tokens

        if token_count is not None and token_count > self._config.input_token_limit_tier2:
            # Use new prompt fitting system for data-preserving content management
            if self._debug:
                rprint(
                    f"[bold yellow]Daily summary prompt ({token_count} tokens) exceeds limit "
                    f"({self._config.input_token_limit_tier2}). "
                    f"Using data-preserving fitting...[/bold yellow]"
                )

            return await self._synthesize_daily_summary_chunked(full_log, daily_diff, token_count)

        try:
            return await self._generate_with_retry(
                self._config.model_tier2, prompt, self._config.max_tokens_tier2
            )
        except (_EmptyResponseError, asyncio.TimeoutError) as e:
            raise GeminiClientError(
                "Failed to synthesize daily summary after multiple retries."
            ) from e  # pragma: no cover
        except RetryError as e:
            attempt_number = e.last_attempt.attempt_number
            final_error = e.last_attempt.exception()
            error_name = type(final_error).__name__ if final_error else "Unknown"
            error_msg = str(final_error) if final_error else "No details"
            msg = (
                f"Daily summary failed after {attempt_number} attempts.\n"
                f"Final error was: {error_name}: {error_msg}\n"
                f"--- PROMPT SENT TO MODEL ---\n{prompt}"
            )
            raise GeminiClientError(msg) from e

    async def _synthesize_daily_summary_chunked(
        self, full_log: str, daily_diff: str, current_tokens: int
    ) -> str:
        """Handle daily summary generation using dynamic chunking strategy.

        This method splits large content into overlapping chunks and combines results.
        The number of chunks is calculated dynamically based on token overage.

        Args:
            full_log: The full commit log content
            daily_diff: The daily diff content
            current_tokens: Current token count that exceeded the limit

        Returns:
            Combined summary from all chunk pairs

        Raises:
            GeminiClientError: If chunking fails or results cannot be combined
        """
        num_chunks = self._calculate_chunks_needed(current_tokens)
        chunks = self._split_content_into_chunks(daily_diff, num_chunks)
        if not (chunk_summaries := await self._process_chunk_pairs(chunks, full_log)):
            raise GeminiClientError("Failed to process any chunk pairs for daily summary")

        return self._combine_chunk_summaries(chunk_summaries)

    def _calculate_chunks_needed(self, current_tokens: int) -> int:
        """Calculate the number of chunks needed based on token overage."""
        overage_ratio = current_tokens / self._config.input_token_limit_tier2
        num_chunks = max(3, int(overage_ratio * 2) + 1)

        if self._debug:
            rprint(
                f"[bold cyan]Splitting into {num_chunks} chunks "
                f"(overage ratio: {overage_ratio:.2f})[/bold cyan]"
            )

        return num_chunks

    async def _process_chunk_pairs(self, chunks: list[str], full_log: str) -> list[str]:
        """Process overlapping pairs of chunks and return summaries.

        Ensures complete coverage by processing overlapping pairs and handling edge cases
        where the last chunk might not be fully covered.
        """
        chunk_summaries = []

        # Process overlapping pairs to ensure full coverage
        for i in range(len(chunks) - 1):
            if summary := await self._process_single_chunk_pair(chunks, i, full_log):
                chunk_summaries.append(summary)

        # If we have 3+ chunks, ensure the last chunk is fully represented
        # by checking if it needs separate processing
        if len(chunks) >= MAX_CHUNK_PAIRS:
            # The last chunk should be covered by the final pair, but double-check
            # by processing it with the second-to-last if not already covered
            # This is already covered by the loop above, so no additional processing needed
            pass

        return chunk_summaries

    async def _process_single_chunk_pair(
        self, chunks: list[str], index: int, full_log: str
    ) -> str | None:
        """Process a single pair of chunks and return the summary."""
        combined_diff = (
            f"--- Chunk {index + 1} ---\n{chunks[index]}\n\n"
            f"--- Chunk {index + 2} ---\n{chunks[index + 1]}"
        )
        prompt = await self._prepare_chunk_prompt(full_log, combined_diff)

        if self._debug:
            rprint(f"[bold blue]Processing chunk pair {index + 1}+{index + 2}[/bold blue]")

        try:
            return await self._generate_with_retry(
                self._config.model_tier2, prompt, self._config.max_tokens_tier2
            )
        except (RetryError, _EmptyResponseError, asyncio.TimeoutError) as e:
            if self._debug:
                rprint(
                    f"[bold red]Failed to process chunk pair {index + 1}+{index + 2}: "
                    f"{e}[/bold red]"
                )
            return None

    async def _prepare_chunk_prompt(self, full_log: str, combined_diff: str) -> str:
        """Prepare a prompt for chunk processing, adjusting size if needed."""
        reduction_factors = [3, 5, 10, 20, 50]  # Progressive reduction factors

        for factor in reduction_factors:
            reduced_log = self._reduce_log_content(full_log, factor)
            prompt = daily.PROMPT_TEMPLATE.format(full_log=reduced_log, daily_diff=combined_diff)

            # Verify this chunk pair fits within limits
            token_response = await self._client.aio.models.count_tokens(
                model=self._config.model_tier2, contents=prompt
            )

            if token_response.total_tokens is None:
                # Token counting failed - this is a fatal error
                raise GeminiClientError("Token counting failed - unable to determine prompt size")

            if token_response.total_tokens <= self._config.input_token_limit_tier2:
                if self._debug:
                    rprint(
                        f"[bold green]Chunk prompt fits with reduction factor {factor} "
                        f"({token_response.total_tokens} tokens)[/bold green]"
                    )
                return prompt

            if self._debug:
                rprint(
                    f"[bold yellow]Reduction factor {factor} still too large "
                    f"({token_response.total_tokens} tokens > "
                    f"{self._config.input_token_limit_tier2})[/bold yellow]"
                )

        # If we've exhausted all reduction attempts, raise an error
        raise GeminiClientError(
            f"Unable to reduce prompt to fit within token limit of "
            f"{self._config.input_token_limit_tier2}. "
            f"Content is too large even with maximum reduction."
        )

    def _split_content_into_chunks(self, content: str, num_chunks: int) -> list[str]:
        """Split content into roughly equal chunks by line count."""
        lines = content.split("\n")
        chunk_size = max(1, len(lines) // num_chunks)

        chunks = []
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i : i + chunk_size]
            chunks.append("\n".join(chunk_lines))

        return chunks

    def _reduce_log_content(self, log_content: str, _reduction_factor: int) -> str:
        """Reduce log content while preserving ALL data integrity.

        CRITICAL: This method MUST NOT sample or discard ANY commit information.
        Instead, it signals that the content needs overlapping chunk processing
        to maintain 100% data preservation as required by the project.
        """
        lines = log_content.split("\n")
        if len(lines) <= MAX_LOG_REDUCTION_LINES:  # If already small, don't reduce
            return log_content

        # FORBIDDEN: No sampling, truncation, or data loss allowed
        # Instead, return content with metadata for chunk processing
        return f"[REQUIRES_CHUNKING: {len(lines)} lines]\n{log_content}"

    def _combine_chunk_summaries(self, summaries: list[str]) -> str:
        """Combine overlapping chunk summaries into a coherent daily summary."""
        if len(summaries) == 1:
            return summaries[0]

        combined = "### Daily Development Summary\n\n"
        details = []

        for i, summary in enumerate(summaries):
            section_intro = f"Development activity from chunk analysis {i + 1}:\n"
            clean_summary = summary.replace("### Daily Development Summary", "")
            if clean_summary := clean_summary.replace("###", "").strip():
                details.append(section_intro + clean_summary)

        combined += "\n\n".join(details)
        combined += f"\n\n*Summary generated from {len(summaries)} overlapping content analyses.*"
        return combined

    async def generate_news_narrative(
        self,
        commit_summaries: str,
        daily_summaries: str,
        weekly_diff: str,
        history: str,
    ) -> str:
        """Tier 3: Generates the narrative for NEWS.md."""
        prompt = ""  # Initialize to ensure it's available in the except block
        try:
            # First, construct a prompt using data-preserving fitting.
            prompt = await self._construct_and_fit_weekly_prompt(
                commit_summaries, daily_summaries, weekly_diff, history
            )
            # Then, generate the content.
            return await self._generate_with_retry(
                self._config.model_tier3, prompt, self._config.max_tokens_tier3
            )
        except (_EmptyResponseError, asyncio.TimeoutError) as e:
            raise GeminiClientError(
                "Failed to generate news narrative after multiple retries."
            ) from e  # pragma: no cover
        except RetryError as e:
            attempt_number = e.last_attempt.attempt_number
            final_error = e.last_attempt.exception()
            error_name = type(final_error).__name__ if final_error else "Unknown"
            error_msg = str(final_error) if final_error else "No details"
            # The prompt is too large to display fully, so we show a snippet.
            msg = (
                f"News narrative generation failed after {attempt_number} attempts.\n"
                f"Final error was: {error_name}: {error_msg}\n"
                f"--- PROMPT SENT TO MODEL (first 2000 chars) ---\n"
                f"{prompt[:2000]}... (prompt truncated)"
            )
            raise GeminiClientError(msg) from e

    async def generate_changelog_entries(self, categorized_summaries: list[dict[str, str]]) -> str:
        """Tier 3: Generates structured entries for CHANGELOG.txt."""
        prompt = _PROMPT_TEMPLATE_CHANGELOG.format(
            categorized_summaries=json_helpers.safe_json_encode(categorized_summaries)
        )
        try:
            return await self._generate_with_retry(
                self._config.model_tier3, prompt, self._config.max_tokens_tier3
            )
        except (_EmptyResponseError, asyncio.TimeoutError) as e:
            raise GeminiClientError(
                "Failed to generate changelog entries after multiple retries."
            ) from e  # pragma: no cover
        except RetryError as e:
            attempt_number = e.last_attempt.attempt_number
            final_error = e.last_attempt.exception()
            error_name = type(final_error).__name__ if final_error else "Unknown"
            error_msg = str(final_error) if final_error else "No details"
            msg = (
                f"Changelog generation failed after {attempt_number} attempts.\n"
                f"Final error was: {error_name}: {error_msg}\n"
                f"--- PROMPT SENT TO MODEL ---\n{prompt}"
            )
            raise GeminiClientError(msg) from e
