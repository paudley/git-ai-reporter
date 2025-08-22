# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Global pytest configuration and fixtures for git-ai-reporter test suite.

This file contains fixtures and configuration that are available to all tests.
"""

from collections.abc import Iterator
import json
from pathlib import Path
import sys
import tempfile
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock

import git
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# pylint: disable=wrong-import-position
from git_ai_reporter.models import AnalysisResult  # noqa: E402
from git_ai_reporter.models import Change  # noqa: E402
from git_ai_reporter.models import CommitAnalysis  # noqa: E402


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for test files.

    Yields:
        Path: Path to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_git_repo(temp_dir: Path) -> git.Repo:  # pylint: disable=redefined-outer-name
    """Create a temporary git repository for testing.

    Args:
        temp_dir: Temporary directory to create repo in.

    Returns:
        git.Repo: Initialized git repository.
    """
    repo = git.Repo.init(temp_dir)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Create initial commit
    readme = temp_dir / "README.md"
    readme.write_text("# Test Repository\n")
    repo.index.add([str(readme)])
    repo.index.commit("Initial commit")

    return repo


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
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "requires_api_key: marks tests that need API key")
    config.addinivalue_line("markers", "hypothesis: marks property-based tests")


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset environment variables for each test.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    # Clear any existing API keys
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
