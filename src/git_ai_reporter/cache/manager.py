# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""This module handles caching of analysis results to the filesystem."""

from datetime import date
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import aiofiles.os
from pydantic import ValidationError

from ..models import CommitAnalysis
from ..utils import json_helpers

if TYPE_CHECKING:
    from ..models import AnalysisResult


class CacheManager:
    """Manages reading from and writing to the file-based cache."""

    def __init__(self, cache_path: Path):
        """Initializes the CacheManager.

        Args:
            cache_path: The root path for the cache directory.
        """
        self.cache_path = cache_path
        self._commits_path = self.cache_path / "commits"
        self._daily_summaries_path = self.cache_path / "daily_summaries"
        self._weekly_summaries_path = self.cache_path / "weekly_summaries"
        self._narratives_path = self.cache_path / "narratives"
        self._changelogs_path = self.cache_path / "changelogs"

        for path in (
            self._commits_path,
            self._daily_summaries_path,
            self._weekly_summaries_path,
            self._narratives_path,
            self._changelogs_path,
        ):
            path.mkdir(parents=True, exist_ok=True)

    async def get_commit_analysis(self, hexsha: str) -> CommitAnalysis | None:
        """Retrieves a cached commit analysis.

        Args:
            hexsha: The commit hash.

        Returns:
            A CommitAnalysis object or None if not found in cache.
        """
        cache_file = self._commits_path / f"{hexsha}.json"
        if await aiofiles.os.path.exists(cache_file):
            try:
                async with aiofiles.open(cache_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                data = json_helpers.safe_json_decode(content)
                return CommitAnalysis.model_validate(data)
            except (json.JSONDecodeError, ValidationError):
                # If the file is corrupted or the schema is wrong, treat as a cache miss.
                return None
        return None

    async def set_commit_analysis(self, hexsha: str, analysis: CommitAnalysis) -> None:
        """Saves a commit analysis to the cache.

        Args:
            hexsha: The commit hash.
            analysis: The CommitAnalysis object to save.
        """
        cache_file = self._commits_path / f"{hexsha}.json"
        async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
            await f.write(analysis.model_dump_json(indent=2))

    def _get_hash(self, items: list[str]) -> str:
        """Creates a stable hash from a list of strings."""
        return hashlib.sha256("".join(sorted(items)).encode()).hexdigest()[:16]

    async def get_daily_summary(self, commit_date: date, commit_hexshas: list[str]) -> str | None:
        """Retrieves a cached daily summary.

        Args:
            commit_date: The date of the summary.
            commit_hexshas: The list of commit hashes for that day.

        Returns:
            The summary string or None if not found in cache.
        """
        content_hash = self._get_hash(commit_hexshas)
        cache_file = self._daily_summaries_path / f"{commit_date.isoformat()}-{content_hash}.txt"
        if await aiofiles.os.path.exists(cache_file):
            async with aiofiles.open(cache_file, "r", encoding="utf-8") as f:
                return await f.read()
        return None

    async def set_daily_summary(
        self, commit_date: date, commit_hexshas: list[str], summary: str
    ) -> None:
        """Saves a daily summary to the cache.

        Args:
            commit_date: The date of the summary.
            commit_hexshas: The list of commit hashes for that day.
            summary: The summary string to save.
        """
        content_hash = self._get_hash(commit_hexshas)
        cache_file = self._daily_summaries_path / f"{commit_date.isoformat()}-{content_hash}.txt"
        async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
            await f.write(summary)

    async def get_weekly_summary(self, week_num_str: str, commit_hexshas: list[str]) -> str | None:
        """Retrieves a cached weekly summary.

        Args:
            week_num_str: A string representing the week (e.g., "2023-42").
            commit_hexshas: The list of commit hashes for that week.

        Returns:
            The summary string or None if not found in cache.
        """
        content_hash = self._get_hash(commit_hexshas)
        cache_file = self._weekly_summaries_path / f"{week_num_str}-{content_hash}.txt"
        if await aiofiles.os.path.exists(cache_file):
            async with aiofiles.open(cache_file, "r", encoding="utf-8") as f:
                return await f.read()
        return None

    async def set_weekly_summary(
        self, week_num_str: str, commit_hexshas: list[str], summary: str
    ) -> None:
        """Saves a weekly summary to the cache.

        Args:
            week_num_str: A string representing the week (e.g., "2023-42").
            commit_hexshas: The list of commit hashes for that week.
            summary: The summary string to save.
        """
        content_hash = self._get_hash(commit_hexshas)
        cache_file = self._weekly_summaries_path / f"{week_num_str}-{content_hash}.txt"
        async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
            await f.write(summary)

    async def get_final_narrative(self, result: "AnalysisResult") -> str | None:
        """Retrieves a cached final narrative.

        Args:
            result: The full analysis result object.

        Returns:
            The narrative string or None if not found in cache.
        """
        hashes = [
            *result.period_summaries,
            *result.daily_summaries,
            *[
                f"{change.summary}-{change.category}"
                for entry in result.changelog_entries
                for change in entry.changes
            ],
        ]
        content_hash = self._get_hash(hashes)
        cache_file = self._narratives_path / f"{content_hash}.txt"
        if await aiofiles.os.path.exists(cache_file):
            async with aiofiles.open(cache_file, "r", encoding="utf-8") as f:
                return await f.read()
        return None

    async def set_final_narrative(self, result: "AnalysisResult", narrative: str) -> None:
        """Saves a final narrative to the cache.

        Args:
            result: The full analysis result object.
            narrative: The narrative string to save.
        """
        hashes = [
            *result.period_summaries,
            *result.daily_summaries,
            *[
                f"{change.summary}-{change.category}"
                for entry in result.changelog_entries
                for change in entry.changes
            ],
        ]
        content_hash = self._get_hash(hashes)
        cache_file = self._narratives_path / f"{content_hash}.txt"
        async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
            await f.write(narrative)

    async def get_changelog_entries(self, entries: list[CommitAnalysis]) -> str | None:
        """Retrieves cached changelog entries.

        Args:
            entries: The list of commit analysis objects.

        Returns:
            The changelog markdown string or None if not found in cache.
        """
        hashes = [
            f"{change.summary}-{change.category}" for entry in entries for change in entry.changes
        ]
        content_hash = self._get_hash(hashes)
        cache_file = self._changelogs_path / f"{content_hash}.txt"
        if await aiofiles.os.path.exists(cache_file):
            async with aiofiles.open(cache_file, "r", encoding="utf-8") as f:
                return await f.read()
        return None

    async def set_changelog_entries(self, entries: list[CommitAnalysis], changelog: str) -> None:
        """Saves changelog entries to the cache.

        Args:
            entries: The list of commit analysis objects.
            changelog: The changelog markdown string to save.
        """
        hashes = [
            f"{change.summary}-{change.category}" for entry in entries for change in entry.changes
        ]
        content_hash = self._get_hash(hashes)
        cache_file = self._changelogs_path / f"{content_hash}.txt"
        async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
            await f.write(changelog)
