# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Centralized configuration for the DevSummary AI application.

This module uses pydantic-settings to load configuration from environment
variables or a .env file, providing type-safe access to settings.
"""

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Defines the application's configuration settings."""

    # Gemini API Configuration
    GEMINI_API_KEY: str | None = None

    # Model Configuration
    MODEL_TIER_1: str = "gemini-2.5-flash"
    MODEL_TIER_2: str = "gemini-2.5-pro"
    MODEL_TIER_3: str = "gemini-2.5-pro"

    # Artifact file paths
    NEWS_FILE: str = "NEWS.md"
    CHANGELOG_FILE: str = "CHANGELOG.txt"
    DAILY_UPDATES_FILE: str = "DAILY_UPDATES.md"

    # Commit Triviality Heuristics
    TRIVIAL_COMMIT_TYPES: list[str] = [
        "chore",
        "docs",
        "style",
        "refactor",
        "test",
        "ci",
    ]
    TRIVIAL_FILE_PATTERNS: list[str] = [
        r"\.md$",
        r"docs/",
        r"\.gitignore",
        r"\.cfg$",
        r"\.toml$",
    ]

    # LLM Generation Parameters
    GEMINI_INPUT_TOKEN_LIMIT_TIER1: int = 1000000
    GEMINI_INPUT_TOKEN_LIMIT_TIER2: int = 1000000
    GEMINI_INPUT_TOKEN_LIMIT_TIER3: int = 1000000
    MAX_TOKENS_TIER_1: int = 8192
    MAX_TOKENS_TIER_2: int = 8192
    MAX_TOKENS_TIER_3: int = 16384
    TEMPERATURE: float = 0.5

    # Concurrency and Timeout Settings
    GEMINI_API_TIMEOUT: int = 300  # Timeout in seconds for Gemini API calls
    GIT_COMMAND_TIMEOUT: int = 30  # Timeout in seconds for individual git commands
    MAX_CONCURRENT_GIT_COMMANDS: int = 5  # Max concurrent asyncio tasks

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
