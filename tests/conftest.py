# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Global pytest configuration and fixtures for git-ai-reporter test suite.

This file contains fixtures and configuration that are available to all tests.
"""

from collections.abc import Iterator
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Final
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock

import git
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import test utilities (needs to be after path modification)
from tests.utils.windows_cleanup import \
    safe_cleanup_on_windows  # pylint: disable=wrong-import-position  # noqa: E402

# Register our custom Allure plugin - must load first to prevent conflicts
pytest_plugins = ["tests.allure_unified_plugin"]

# Constants
WINDOWS_OS_NAME: Final[str] = "nt"


# pylint: disable=wrong-import-position
from git_ai_reporter.models import AnalysisResult  # noqa: E402
from git_ai_reporter.models import Change  # noqa: E402
from git_ai_reporter.models import CommitAnalysis  # noqa: E402


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for test files.

    Uses Windows-safe cleanup to handle Git file locking issues.

    Yields:
        Path: Path to the temporary directory.
    """
    # Create temp directory manually to control cleanup
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        # Use our Windows-safe cleanup
        safe_cleanup_on_windows(temp_path)


@pytest.fixture
def temp_git_repo(temp_dir: Path) -> Iterator[git.Repo]:  # pylint: disable=redefined-outer-name
    """Create a temporary git repository for testing.

    Args:
        temp_dir: Temporary directory to create repo in.

    Yields:
        git.Repo: Initialized git repository.
    """
    # Resolve to absolute path to avoid path issues in CI
    # Use expanduser and resolve to get consistent path format across platforms
    absolute_temp_dir = temp_dir.expanduser().resolve()

    # On Windows, ensure consistent path format
    if os.name == WINDOWS_OS_NAME:  # Windows
        # Convert to string and back to normalize path separators and case
        normalized_path = os.path.normpath(os.path.abspath(str(absolute_temp_dir)))
        absolute_temp_dir = Path(normalized_path)

    repo = git.Repo.init(absolute_temp_dir)

    # Configure git with Windows-compatible settings
    config_writer = repo.config_writer()
    try:
        config_writer.set_value("user", "name", "Test User")
        config_writer.set_value("user", "email", "test@example.com")
        # On Windows, set core.longpaths to handle long path issues
        if os.name == WINDOWS_OS_NAME:
            config_writer.set_value("core", "longpaths", "true")
    finally:
        config_writer.release()

    # Create initial commit with proper path handling
    readme = absolute_temp_dir / "README.md"
    readme.write_text("# Test Repository\n", encoding="utf-8")

    # Use relative path for git index to avoid absolute path issues
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    try:
        yield repo
    finally:
        # Explicitly close the repo to release file locks on Windows
        try:
            repo.close()
        except (OSError, AttributeError):
            pass  # Ignore cleanup errors - repo may not support close() or file locks


@pytest.fixture
def sample_commit_analysis() -> CommitAnalysis:
    """Create a sample CommitAnalysis for testing.

    Returns:
        CommitAnalysis: Sample commit analysis data.
    """
    return CommitAnalysis(
        changes=[
            Change(
                summary="Added OAuth2 integration module",
                category="New Feature",
            ),
            Change(
                summary="Implemented user session management",
                category="New Feature",
            ),
        ],
        trivial=False,
    )


@pytest.fixture
def sample_change() -> Change:
    """Create a sample Change for testing.

    Returns:
        Change: Sample change data.
    """
    return Change(
        summary="OAuth2 authentication with Google and GitHub",
        category="New Feature",
    )


@pytest.fixture
def sample_analysis_result() -> AnalysisResult:
    """Create a sample AnalysisResult for testing.

    Returns:
        AnalysisResult: Sample analysis result data.
    """
    return AnalysisResult(
        period_summaries=["Week saw major progress on authentication"],
        daily_summaries=["Monday: OAuth2 setup", "Tuesday: Testing"],
        changelog_entries=[
            CommitAnalysis(
                changes=[
                    Change(
                        summary="OAuth2 authentication support",
                        category="New Feature",
                    )
                ],
                trivial=False,
            ),
            CommitAnalysis(
                changes=[
                    Change(
                        summary="Fixed memory leak",
                        category="Bug Fix",
                    )
                ],
                trivial=False,
            ),
        ],
    )


@pytest.fixture
def mock_gemini_client() -> Mock:
    """Create a mocked GeminiClient for testing.

    Returns:
        Mock: Mocked GeminiClient instance.
    """
    client = MagicMock()
    client.analyze_commit = AsyncMock(
        return_value=CommitAnalysis(
            changes=[Change(summary="Test change", category="New Feature")],
            trivial=False,
        )
    )
    client.generate_weekly_narrative = AsyncMock(return_value="Weekly narrative...")
    client.generate_changelog = AsyncMock(return_value=[Change(summary="Test", category="Bug Fix")])
    return client


@pytest.fixture
def mock_genai_model() -> Mock:
    """Create a mocked Gemini AI model for testing.

    Returns:
        Mock: Mocked GenerativeModel instance.
    """
    model = MagicMock()
    response = MagicMock()
    response.text = json.dumps(
        {
            "title": "Test commit",
            "category": "New Feature",
            "impact": "high",
            "summary": "Test summary",
            "key_changes": ["Change 1", "Change 2"],
        }
    )
    model.generate_content = MagicMock(return_value=response)
    return model


@pytest.fixture
def sample_git_data() -> list[dict[str, Any]]:
    """Load sample git data from extracts.

    Returns:
        list[dict[str, Any]]: List of commit data from sample_git_data.jsonl.
    """
    data_file = Path(__file__).parent / "extracts" / "sample_git_data.jsonl"
    if not data_file.exists():
        # Return synthetic data if file doesn't exist yet
        return [
            {
                "hash": "abc123",
                "message": "feat: Add new feature",
                "author": "Test User",
                "date": "2025-01-07T10:00:00Z",
                "files": ["src/feature.py"],
                "diff": "+ def new_feature():\n+     pass",
            }
        ]

    commits = []
    with open(data_file, encoding="utf-8") as f:
        for line in f:
            commits.append(json.loads(line))
    return commits


@pytest.fixture
def malformed_json_samples() -> dict[str, str]:
    """Provide various malformed JSON samples for testing.

    Returns:
        dict[str, str]: Dictionary of malformed JSON strings.
    """
    return {
        "extra_comma": '{"key": "value",}',
        "missing_quote": '{"key: "value"}',
        "single_quotes": "{'key': 'value'}",
        "trailing_comma_array": '["item1", "item2",]',
        "mixed_quotes": "{\"key\": 'value'}",
        "markdown_wrapped": '```json\n{"key": "value"}\n```',
        "nested_error": '{"outer": {"inner": "value",},}',
    }


@pytest.fixture
def vcr_config() -> dict[str, Any]:
    """VCR configuration for recording API calls.

    Returns:
        dict[str, Any]: VCR configuration dictionary.
    """
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "record_mode": "once",
        "match_on": ["uri", "method", "body"],
        "cassette_library_dir": "tests/cassettes",
    }


@pytest.fixture(scope="session")
def vcr_config_session() -> dict[str, Any]:
    """Session-scoped VCR configuration.

    Returns:
        dict[str, Any]: VCR configuration dictionary.
    """
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "record_mode": "once",
        "match_on": ["uri", "method", "body"],
        "cassette_library_dir": "tests/cassettes",
    }


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers.

    Args:
        config: Pytest configuration object.
    """
    # Register custom markers to avoid warnings and enable selective runs
    config.addinivalue_line(
        "markers", "smoke: marks tests as critical smoke tests for linting integration"
    )
    config.addinivalue_line(
        "markers", "vcr: marks tests that use pytest-recording for network mocking"
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers", "bdd: marks tests that use pytest-bdd for behavior-driven development"
    )
    config.addinivalue_line(
        "markers", "hypothesis: marks tests that use hypothesis for property-based testing"
    )
    config.addinivalue_line("markers", "asyncio: marks tests as async tests")
    config.addinivalue_line("markers", "requires_api_key: marks tests that need API key")


# BDD Fixtures for pytest-bdd tests
@pytest.fixture
def mock_commit() -> MagicMock:
    """Create a mock commit object for BDD testing."""
    commit = MagicMock(spec=git.Commit)
    commit.hexsha = "abc123"
    commit.authored_datetime = datetime(2025, 1, 7, 10, 0, 0)
    commit.author.name = "Test Author"
    commit.author.email = "test@example.com"
    commit.stats.files = {}
    return commit


@pytest.fixture
def git_analyzer(temp_git_repo: git.Repo) -> MagicMock:  # pylint: disable=redefined-outer-name
    """Create a mock GitAnalyzer instance for BDD testing."""
    analyzer = MagicMock()
    analyzer.repo_path = Path(temp_git_repo.working_dir) if temp_git_repo.working_dir else None
    analyzer.since_date = datetime(2025, 1, 1)
    analyzer.until_date = datetime(2025, 1, 8)
    return analyzer


@pytest.fixture
def analysis_context() -> dict[str, Any]:
    """Context dictionary for sharing state between BDD steps."""
    return {}


@pytest.fixture
def summary_context() -> dict[str, Any]:
    """Context dictionary for summary BDD steps."""
    context = {}
    return context


@pytest.fixture
def pre_release_context() -> dict[str, Any]:
    """Context dictionary for pre-release BDD steps."""
    return {
        "version": None,
        "changelog_content": None,
        "news_content": None,
        "daily_updates_content": None,
        "commits": [],
        "temp_dir": None,
        "git_repo": None,
        "output_files": {},
        "command_result": None,
    }


@pytest.fixture
def mock_genai_client() -> MagicMock:
    """Create a mock google.genai.Client for advanced testing."""
    try:
        from google import genai  # pylint: disable=import-outside-toplevel

        client = MagicMock(spec=genai.Client)
    except ImportError:
        # Fallback if genai not available
        client = MagicMock()

    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock()

    # Setup count_tokens to return a proper response
    token_response = MagicMock()
    token_response.total_tokens = 100  # Default small token count
    client.aio.models.count_tokens = AsyncMock(return_value=token_response)

    return client


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset environment variables for each test.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    # Clear any existing API keys
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
