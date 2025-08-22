# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=protected-access

"""Unit tests for git_ai_reporter.cache.manager module.

This module tests the cache manager for storing and retrieving analysis results.
"""

import asyncio
from datetime import date
from pathlib import Path

import pytest
import pytest_check as check

from git_ai_reporter.cache.manager import CacheManager
from git_ai_reporter.models import AnalysisResult
from git_ai_reporter.models import Change
from git_ai_reporter.models import CommitAnalysis


@pytest.mark.asyncio
class TestCacheManager:
    """Test suite for CacheManager class."""

    @pytest.fixture
    def cache_manager(self, temp_dir: Path) -> CacheManager:
        """Create a CacheManager instance with temp directory."""
        return CacheManager(temp_dir / "cache")

    async def test_init_creates_subdirectories(self, temp_dir: Path) -> None:
        """Test that initialization creates all required subdirectories."""
        cache_path = temp_dir / "cache"
        CacheManager(cache_path)

        check.is_true((cache_path / "commits").exists())
        check.is_true((cache_path / "daily_summaries").exists())
        check.is_true((cache_path / "weekly_summaries").exists())
        check.is_true((cache_path / "narratives").exists())
        check.is_true((cache_path / "changelogs").exists())

    async def test_get_commit_analysis_not_found(self, cache_manager: CacheManager) -> None:
        """Test retrieving non-existent commit analysis returns None."""
        result = await cache_manager.get_commit_analysis("nonexistent")
        check.is_none(result)

    async def test_set_and_get_commit_analysis(self, cache_manager: CacheManager) -> None:
        """Test saving and retrieving commit analysis."""
        analysis = CommitAnalysis(
            changes=[
                Change(summary="Added feature X", category="New Feature"),
                Change(summary="Fixed bug Y", category="Bug Fix"),
            ],
            trivial=False,
        )
        hexsha = "abc123def456"

        await cache_manager.set_commit_analysis(hexsha, analysis)
        retrieved = await cache_manager.get_commit_analysis(hexsha)

        check.is_not_none(retrieved)
        check.equal(len(retrieved.changes), 2)  # type: ignore[union-attr]
        check.equal(retrieved.changes[0].summary, "Added feature X")  # type: ignore[union-attr]
        check.equal(retrieved.changes[1].category, "Bug Fix")  # type: ignore[union-attr]
        check.is_false(retrieved.trivial)  # type: ignore[union-attr]

    async def test_get_commit_analysis_corrupted_json(self, cache_manager: CacheManager) -> None:
        """Test that corrupted JSON cache returns None."""
        hexsha = "corrupted123"
        cache_file = cache_manager._commits_path / f"{hexsha}.json"

        # Write corrupted JSON
        cache_file.write_text("{'not': 'valid json'", encoding="utf-8")

        result = await cache_manager.get_commit_analysis(hexsha)
        check.is_none(result)

    async def test_get_commit_analysis_invalid_schema(self, cache_manager: CacheManager) -> None:
        """Test that invalid schema cache returns None."""
        hexsha = "invalid123"
        cache_file = cache_manager._commits_path / f"{hexsha}.json"

        # Write valid JSON but invalid schema
        cache_file.write_text('{"wrong_field": "value"}', encoding="utf-8")

        result = await cache_manager.get_commit_analysis(hexsha)
        check.is_none(result)

    async def test_hash_generation(self, cache_manager: CacheManager) -> None:
        """Test that hash generation is stable and unique."""
        items1 = ["commit1", "commit2", "commit3"]
        items2 = ["commit3", "commit1", "commit2"]  # Same items, different order
        items3 = ["commit1", "commit2", "commit4"]  # Different items

        hash1 = cache_manager._get_hash(items1)
        hash2 = cache_manager._get_hash(items2)
        hash3 = cache_manager._get_hash(items3)

        # Same items should produce same hash regardless of order
        check.equal(hash1, hash2)
        # Different items should produce different hash
        check.not_equal(hash1, hash3)
        # Hash should be 16 characters
        check.equal(len(hash1), 16)

    async def test_set_and_get_daily_summary(self, cache_manager: CacheManager) -> None:
        """Test saving and retrieving daily summary."""
        test_date = date(2025, 1, 7)
        hexshas = ["commit1", "commit2"]
        summary = "Today we made great progress on features X and Y."

        await cache_manager.set_daily_summary(test_date, hexshas, summary)
        retrieved = await cache_manager.get_daily_summary(test_date, hexshas)

        check.equal(retrieved, summary)

    async def test_get_daily_summary_not_found(self, cache_manager: CacheManager) -> None:
        """Test retrieving non-existent daily summary returns None."""
        test_date = date(2025, 1, 7)
        hexshas = ["nonexistent"]

        result = await cache_manager.get_daily_summary(test_date, hexshas)
        check.is_none(result)

    async def test_daily_summary_cache_key_depends_on_commits(
        self, cache_manager: CacheManager
    ) -> None:
        """Test that daily summary cache key changes with different commits."""
        test_date = date(2025, 1, 7)
        hexshas1 = ["commit1", "commit2"]
        hexshas2 = ["commit3", "commit4"]
        summary1 = "Summary for commits 1 and 2"
        summary2 = "Summary for commits 3 and 4"

        await cache_manager.set_daily_summary(test_date, hexshas1, summary1)
        await cache_manager.set_daily_summary(test_date, hexshas2, summary2)

        retrieved1 = await cache_manager.get_daily_summary(test_date, hexshas1)
        retrieved2 = await cache_manager.get_daily_summary(test_date, hexshas2)

        check.equal(retrieved1, summary1)
        check.equal(retrieved2, summary2)

    async def test_set_and_get_weekly_summary(self, cache_manager: CacheManager) -> None:
        """Test saving and retrieving weekly summary."""
        week_str = "2025-02"
        hexshas = ["commit1", "commit2", "commit3"]
        summary = "This week we completed the authentication system."

        await cache_manager.set_weekly_summary(week_str, hexshas, summary)
        retrieved = await cache_manager.get_weekly_summary(week_str, hexshas)

        check.equal(retrieved, summary)

    async def test_get_weekly_summary_not_found(self, cache_manager: CacheManager) -> None:
        """Test retrieving non-existent weekly summary returns None."""
        week_str = "2025-02"
        hexshas = ["nonexistent"]

        result = await cache_manager.get_weekly_summary(week_str, hexshas)
        check.is_none(result)

    async def test_set_and_get_final_narrative(self, cache_manager: CacheManager) -> None:
        """Test saving and retrieving final narrative."""
        result = AnalysisResult(
            period_summaries=["Week 1 summary"],
            daily_summaries=["Day 1", "Day 2"],
            changelog_entries=[
                CommitAnalysis(
                    changes=[Change(summary="Feature", category="New Feature")],
                    trivial=False,
                )
            ],
        )
        narrative = "This period saw significant development..."

        await cache_manager.set_final_narrative(result, narrative)
        retrieved = await cache_manager.get_final_narrative(result)

        check.equal(retrieved, narrative)

    async def test_get_final_narrative_not_found(self, cache_manager: CacheManager) -> None:
        """Test retrieving non-existent final narrative returns None."""
        result = AnalysisResult(
            period_summaries=["Nonexistent"],
            daily_summaries=[],
            changelog_entries=[],
        )

        retrieved = await cache_manager.get_final_narrative(result)
        check.is_none(retrieved)

    async def test_set_and_get_changelog_entries(self, cache_manager: CacheManager) -> None:
        """Test saving and retrieving changelog entries."""
        entries = [
            CommitAnalysis(
                changes=[
                    Change(summary="Added OAuth", category="New Feature"),
                    Change(summary="Fixed login bug", category="Bug Fix"),
                ],
                trivial=False,
            ),
            CommitAnalysis(
                changes=[Change(summary="Updated docs", category="Documentation")],
                trivial=False,
            ),
        ]
        changelog = "## [Unreleased]\n### Added\n- OAuth support\n### Fixed\n- Login bug"

        await cache_manager.set_changelog_entries(entries, changelog)
        retrieved = await cache_manager.get_changelog_entries(entries)

        check.equal(retrieved, changelog)

    async def test_get_changelog_entries_not_found(self, cache_manager: CacheManager) -> None:
        """Test retrieving non-existent changelog entries returns None."""
        entries = [
            CommitAnalysis(
                changes=[Change(summary="Nonexistent", category="Chore")],
                trivial=True,
            )
        ]

        result = await cache_manager.get_changelog_entries(entries)
        check.is_none(result)

    async def test_cache_files_use_correct_extensions(self, cache_manager: CacheManager) -> None:
        """Test that cache files use appropriate extensions."""
        # Set various cache entries
        analysis = CommitAnalysis(
            changes=[Change(summary="Test", category="Tests")],
            trivial=False,
        )
        await cache_manager.set_commit_analysis("test123", analysis)

        test_date = date(2025, 1, 7)
        await cache_manager.set_daily_summary(test_date, ["c1"], "daily")
        await cache_manager.set_weekly_summary("2025-02", ["c2"], "weekly")

        # Check file extensions
        commit_files = list(cache_manager._commits_path.glob("*.json"))
        daily_files = list(cache_manager._daily_summaries_path.glob("*.txt"))
        weekly_files = list(cache_manager._weekly_summaries_path.glob("*.txt"))

        check.equal(len(commit_files), 1)
        check.equal(len(daily_files), 1)
        check.equal(len(weekly_files), 1)

    async def test_concurrent_cache_operations(self, cache_manager: CacheManager) -> None:
        """Test that concurrent cache operations work correctly."""
        analyses = [
            CommitAnalysis(
                changes=[Change(summary=f"Change {i}", category="New Feature")],
                trivial=False,
            )
            for i in range(10)
        ]

        # Concurrent writes
        tasks = [
            cache_manager.set_commit_analysis(f"hash{i}", analysis)
            for i, analysis in enumerate(analyses)
        ]
        await asyncio.gather(*tasks)

        # Concurrent reads
        read_tasks = [cache_manager.get_commit_analysis(f"hash{i}") for i in range(10)]
        results = await asyncio.gather(*read_tasks)

        for i, result in enumerate(results):
            check.is_not_none(result)
            if result is not None:
                check.equal(result.changes[0].summary, f"Change {i}")

    async def test_cache_with_unicode_content(self, cache_manager: CacheManager) -> None:
        """Test caching content with unicode characters."""
        analysis = CommitAnalysis(
            changes=[
                Change(summary="Added 日本語 support", category="New Feature"),
                Change(summary="Fixed émoji 🚀 rendering", category="Bug Fix"),
            ],
            trivial=False,
        )

        await cache_manager.set_commit_analysis("unicode123", analysis)
        retrieved = await cache_manager.get_commit_analysis("unicode123")

        check.is_not_none(retrieved)
        check.equal(retrieved.changes[0].summary, "Added 日本語 support")  # type: ignore[union-attr]
        check.equal(
            retrieved.changes[1].summary,  # type: ignore[union-attr]
            "Fixed émoji 🚀 rendering",
        )

    async def test_empty_commit_list_hash(self, cache_manager: CacheManager) -> None:
        """Test hash generation with empty commit list."""
        empty_hash = cache_manager._get_hash([])
        check.equal(len(empty_hash), 16)

        # Empty list should produce consistent hash
        empty_hash2 = cache_manager._get_hash([])
        check.equal(empty_hash, empty_hash2)
