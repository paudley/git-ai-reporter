# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""This module contains the Pydantic data models for the application.

These models serve as the data contracts, ensuring that data structures
are explicit and validated.
"""

from typing import Final, Literal, TypeAlias

from pydantic import BaseModel
from pydantic import Field

# A dictionary mapping commit category names to their representative emoji.
COMMIT_CATEGORIES: Final[dict[str, str]] = {
    "New Feature": "✨",
    "Bug Fix": "🐛",
    "Documentation": "📝",
    "Refactoring": "♻️",
    "Performance": "🏎️",
    "Styling": "🎨",
    "Tests": "✅",
    "Build": "📦",
    "CI/CD": "🚀",
    "Chore": "🧹",
    "Security": "🔒",
    "Deprecated": "🗑️",
    "Removed": "❌",
    "Infrastructure": "🧱",
    "Developer Experience": "🧑‍💻",
    "Breaking Change": "💥",
    "Revert": "⏪",
}

# A list of valid categories for a commit, as expected by the LLM prompts.
# Using Literal enforces this contract.
CommitCategory: TypeAlias = Literal[
    "New Feature",
    "Bug Fix",
    "Documentation",
    "Refactoring",
    "Performance",
    "Styling",
    "Tests",
    "Build",
    "CI/CD",
    "Chore",
    "Security",
    "Deprecated",
    "Removed",
    "Infrastructure",
    "Developer Experience",
    "Breaking Change",
    "Revert",
]


class Change(BaseModel):
    """Represents a single distinct change within a commit."""

    summary: str = Field(..., description="A concise, one-sentence summary of the change.")
    category: CommitCategory = Field(
        ..., description="The most appropriate category for the change."
    )


class CommitAnalysis(BaseModel):
    """Represents the AI's analysis of a single commit."""

    changes: list[Change] = Field(
        ...,
        description="A list of distinct changes within the commit, each with "
        "a summary and category.",
    )
    trivial: bool = Field(
        False,
        description="Indicates if the commit is considered trivial (e.g., docs, tests, chores).",
    )


class AnalysisResult(BaseModel):
    """Holds the collected results from analyzing a period of commits."""

    period_summaries: list[str]
    daily_summaries: list[str]
    changelog_entries: list[CommitAnalysis]
