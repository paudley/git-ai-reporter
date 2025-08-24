# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
# pylint: disable=protected-access

"""Unit tests for git_ai_reporter.cache.manager module.

This module tests the cache manager for storing and retrieving analysis results.
"""

import asyncio
from datetime import date
import json
from pathlib import Path

import allure
import pytest
import pytest_check as check

from git_ai_reporter.cache.manager import CacheManager
from git_ai_reporter.models import AnalysisResult
from git_ai_reporter.models import Change
from git_ai_reporter.models import CommitAnalysis


@allure.feature("Cache Management")
@pytest.mark.asyncio
class TestCacheManager:
    """Test suite for CacheManager class."""

    @pytest.fixture
    def cache_manager(self, temp_dir: Path) -> CacheManager:
        """Create a CacheManager instance with temp directory."""
        return CacheManager(temp_dir / "cache")

    @allure.title("Initialize cache with required subdirectories")
    @allure.description(
        "Tests that cache manager creates all required subdirectories on initialization"
    )
    @allure.tag("cache", "initialization", "filesystem")
    async def test_init_creates_subdirectories(self, temp_dir: Path) -> None:
        """Test that initialization creates all required subdirectories."""
        with allure.step("Initialize cache manager"):
            cache_path = temp_dir / "cache"
            CacheManager(cache_path)

            subdirs = ["commits", "daily_summaries", "weekly_summaries", "narratives", "changelogs"]

            allure.attach(
                json.dumps(
                    {"cache_path": str(cache_path), "expected_subdirectories": subdirs}, indent=2
                ),
                "Cache Initialization Config",
                allure.attachment_type.JSON,
            )

        with allure.step("Verify subdirectory creation"):
            check.is_true((cache_path / "commits").exists())
            check.is_true((cache_path / "daily_summaries").exists())
            check.is_true((cache_path / "weekly_summaries").exists())
            check.is_true((cache_path / "narratives").exists())
            check.is_true((cache_path / "changelogs").exists())

            allure.attach(
                "All required cache subdirectories created successfully",
                "Directory Creation Result",
                allure.attachment_type.TEXT,
            )

    @allure.title("Handle cache miss for non-existent commit")
    @allure.description("Tests graceful handling when retrieving non-existent commit analysis")
    @allure.tag("cache", "cache-miss", "error-handling")
    async def test_get_commit_analysis_not_found(self, cache_manager: CacheManager) -> None:
        """Test retrieving non-existent commit analysis returns None."""
        with allure.step("Attempt to retrieve non-existent commit analysis"):
            commit_hash = "nonexistent"
            result = await cache_manager.get_commit_analysis(commit_hash)

            allure.attach(
                json.dumps(
                    {"commit_hash": commit_hash, "result": result, "cache_miss": True}, indent=2
                ),
                "Cache Miss Test Result",
                allure.attachment_type.JSON,
            )

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

    @allure.story("Daily Summary Cache")
    @allure.title("Save and retrieve daily summary successfully")
    @allure.description("Tests complete roundtrip caching of daily summary data")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("cache", "daily-summary", "roundtrip", "date-based")
    async def test_set_and_get_daily_summary(self, cache_manager: CacheManager) -> None:
        """Test saving and retrieving daily summary."""
        with allure.step("Set up daily summary test data"):
            test_date = date(2025, 1, 7)
            hexshas = ["commit1", "commit2"]
            summary = "Today we made great progress on features X and Y."

            allure.attach(str(test_date), "Test Date", allure.attachment_type.TEXT)
            allure.attach(str(hexshas), "Commit Hashes", allure.attachment_type.TEXT)
            allure.attach(summary, "Daily Summary", allure.attachment_type.TEXT)

        with allure.step("Store daily summary in cache"):
            await cache_manager.set_daily_summary(test_date, hexshas, summary)
            allure.attach(
                "Daily summary cached successfully", "Storage Status", allure.attachment_type.TEXT
            )

        with allure.step("Retrieve daily summary from cache"):
            retrieved = await cache_manager.get_daily_summary(test_date, hexshas)
            allure.attach(str(retrieved), "Retrieved Summary", allure.attachment_type.TEXT)

        with allure.step("Verify retrieved summary matches original"):
            check.equal(retrieved, summary)

    @allure.story("Daily Summary Cache")
    @allure.title("Return None for non-existent daily summary")
    @allure.description("Tests that cache miss returns None when daily summary doesn't exist")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("cache", "daily-summary", "cache-miss", "not-found")
    async def test_get_daily_summary_not_found(self, cache_manager: CacheManager) -> None:
        """Test retrieving non-existent daily summary returns None."""
        with allure.step("Set up non-existent daily summary parameters"):
            test_date = date(2025, 1, 7)
            hexshas = ["nonexistent"]
            allure.attach(str(test_date), "Test Date", allure.attachment_type.TEXT)
            allure.attach(str(hexshas), "Non-existent Commits", allure.attachment_type.TEXT)

        with allure.step("Attempt to retrieve non-existent daily summary"):
            result = await cache_manager.get_daily_summary(test_date, hexshas)
            allure.attach(str(result), "Cache Result", allure.attachment_type.TEXT)

        with allure.step("Verify cache miss returns None"):
            check.is_none(result)

    @allure.story("Cache Key Generation")
    @allure.title("Generate different cache keys for different commit sets")
    @allure.description(
        "Tests that daily summary cache keys differentiate between different sets of commits"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("cache", "daily-summary", "cache-keys", "isolation")
    async def test_daily_summary_cache_key_depends_on_commits(
        self, cache_manager: CacheManager
    ) -> None:
        """Test that daily summary cache key changes with different commits."""
        with allure.step("Set up different commit sets for same date"):
            test_date = date(2025, 1, 7)
            hexshas1 = ["commit1", "commit2"]
            hexshas2 = ["commit3", "commit4"]
            summary1 = "Summary for commits 1 and 2"
            summary2 = "Summary for commits 3 and 4"

            allure.attach(str(test_date), "Test Date", allure.attachment_type.TEXT)
            allure.attach(str(hexshas1), "Commit Set 1", allure.attachment_type.TEXT)
            allure.attach(str(hexshas2), "Commit Set 2", allure.attachment_type.TEXT)
            allure.attach(summary1, "Summary 1", allure.attachment_type.TEXT)
            allure.attach(summary2, "Summary 2", allure.attachment_type.TEXT)

        with allure.step("Store both summaries in cache"):
            await cache_manager.set_daily_summary(test_date, hexshas1, summary1)
            await cache_manager.set_daily_summary(test_date, hexshas2, summary2)
            allure.attach("Both summaries cached", "Storage Status", allure.attachment_type.TEXT)

        with allure.step("Retrieve both summaries from cache"):
            retrieved1 = await cache_manager.get_daily_summary(test_date, hexshas1)
            retrieved2 = await cache_manager.get_daily_summary(test_date, hexshas2)
            allure.attach(str(retrieved1), "Retrieved Summary 1", allure.attachment_type.TEXT)
            allure.attach(str(retrieved2), "Retrieved Summary 2", allure.attachment_type.TEXT)

        with allure.step("Verify cache isolation between different commit sets"):
            check.equal(retrieved1, summary1)
            check.equal(retrieved2, summary2)

    @allure.story("Weekly Summary Cache")
    @allure.title("Save and retrieve weekly summary successfully")
    @allure.description("Tests complete roundtrip caching of weekly summary data")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("cache", "weekly-summary", "roundtrip", "period-based")
    async def test_set_and_get_weekly_summary(self, cache_manager: CacheManager) -> None:
        """Test saving and retrieving weekly summary."""
        with allure.step("Set up weekly summary test data"):
            week_str = "2025-02"
            hexshas = ["commit1", "commit2", "commit3"]
            summary = "This week we completed the authentication system."

            allure.attach(week_str, "Week String", allure.attachment_type.TEXT)
            allure.attach(str(hexshas), "Commit Hashes", allure.attachment_type.TEXT)
            allure.attach(summary, "Weekly Summary", allure.attachment_type.TEXT)

        with allure.step("Store weekly summary in cache"):
            await cache_manager.set_weekly_summary(week_str, hexshas, summary)
            allure.attach(
                "Weekly summary cached successfully", "Storage Status", allure.attachment_type.TEXT
            )

        with allure.step("Retrieve weekly summary from cache"):
            retrieved = await cache_manager.get_weekly_summary(week_str, hexshas)
            allure.attach(str(retrieved), "Retrieved Summary", allure.attachment_type.TEXT)

        with allure.step("Verify retrieved summary matches original"):
            check.equal(retrieved, summary)

    @allure.story("Weekly Summary Cache")
    @allure.title("Return None for non-existent weekly summary")
    @allure.description("Tests that cache miss returns None when weekly summary doesn't exist")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("cache", "weekly-summary", "cache-miss", "not-found")
    async def test_get_weekly_summary_not_found(self, cache_manager: CacheManager) -> None:
        """Test retrieving non-existent weekly summary returns None."""
        with allure.step("Set up non-existent weekly summary parameters"):
            week_str = "2025-02"
            hexshas = ["nonexistent"]
            allure.attach(week_str, "Week String", allure.attachment_type.TEXT)
            allure.attach(str(hexshas), "Non-existent Commits", allure.attachment_type.TEXT)

        with allure.step("Attempt to retrieve non-existent weekly summary"):
            result = await cache_manager.get_weekly_summary(week_str, hexshas)
            allure.attach(str(result), "Cache Result", allure.attachment_type.TEXT)

        with allure.step("Verify cache miss returns None"):
            check.is_none(result)

    @allure.story("Narrative Cache")
    @allure.title("Save and retrieve final narrative successfully")
    @allure.description(
        "Tests complete roundtrip caching of final narrative based on analysis results"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("cache", "narrative", "analysis-result", "roundtrip")
    async def test_set_and_get_final_narrative(self, cache_manager: CacheManager) -> None:
        """Test saving and retrieving final narrative."""
        with allure.step("Set up analysis result and narrative"):
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

            allure.attach(
                str(len(result.period_summaries)),
                "Period Summaries Count",
                allure.attachment_type.TEXT,
            )
            allure.attach(
                str(len(result.daily_summaries)),
                "Daily Summaries Count",
                allure.attachment_type.TEXT,
            )
            allure.attach(
                str(len(result.changelog_entries)),
                "Changelog Entries Count",
                allure.attachment_type.TEXT,
            )
            allure.attach(narrative, "Final Narrative", allure.attachment_type.TEXT)

        with allure.step("Store final narrative in cache"):
            await cache_manager.set_final_narrative(result, narrative)
            allure.attach(
                "Final narrative cached successfully", "Storage Status", allure.attachment_type.TEXT
            )

        with allure.step("Retrieve final narrative from cache"):
            retrieved = await cache_manager.get_final_narrative(result)
            allure.attach(str(retrieved), "Retrieved Narrative", allure.attachment_type.TEXT)

        with allure.step("Verify retrieved narrative matches original"):
            check.equal(retrieved, narrative)

    @allure.story("Narrative Cache")
    @allure.title("Return None for non-existent final narrative")
    @allure.description("Tests that cache miss returns None when final narrative doesn't exist")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("cache", "narrative", "cache-miss", "not-found")
    async def test_get_final_narrative_not_found(self, cache_manager: CacheManager) -> None:
        """Test retrieving non-existent final narrative returns None."""
        with allure.step("Set up non-existent analysis result"):
            result = AnalysisResult(
                period_summaries=["Nonexistent"],
                daily_summaries=[],
                changelog_entries=[],
            )
            allure.attach(
                str(result.period_summaries), "Period Summaries", allure.attachment_type.TEXT
            )
            allure.attach(
                str(len(result.daily_summaries)),
                "Daily Summaries Count",
                allure.attachment_type.TEXT,
            )
            allure.attach(
                str(len(result.changelog_entries)),
                "Changelog Entries Count",
                allure.attachment_type.TEXT,
            )

        with allure.step("Attempt to retrieve non-existent narrative"):
            retrieved = await cache_manager.get_final_narrative(result)
            allure.attach(str(retrieved), "Cache Result", allure.attachment_type.TEXT)

        with allure.step("Verify cache miss returns None"):
            check.is_none(retrieved)

    @allure.story("Changelog Cache")
    @allure.title("Save and retrieve changelog entries successfully")
    @allure.description("Tests complete roundtrip caching of changelog entries")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("cache", "changelog", "commit-analysis", "roundtrip")
    async def test_set_and_get_changelog_entries(self, cache_manager: CacheManager) -> None:
        """Test saving and retrieving changelog entries."""
        with allure.step("Set up changelog entries and formatted changelog"):
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

            allure.attach(str(len(entries)), "Number of Entries", allure.attachment_type.TEXT)
            allure.attach(
                str(len(entries[0].changes)), "Changes in Entry 1", allure.attachment_type.TEXT
            )
            allure.attach(
                str(len(entries[1].changes)), "Changes in Entry 2", allure.attachment_type.TEXT
            )
            allure.attach(changelog, "Formatted Changelog", allure.attachment_type.TEXT)

        with allure.step("Store changelog entries in cache"):
            await cache_manager.set_changelog_entries(entries, changelog)
            allure.attach(
                "Changelog entries cached successfully",
                "Storage Status",
                allure.attachment_type.TEXT,
            )

        with allure.step("Retrieve changelog entries from cache"):
            retrieved = await cache_manager.get_changelog_entries(entries)
            allure.attach(str(retrieved), "Retrieved Changelog", allure.attachment_type.TEXT)

        with allure.step("Verify retrieved changelog matches original"):
            check.equal(retrieved, changelog)

    @allure.story("Changelog Cache")
    @allure.title("Return None for non-existent changelog entries")
    @allure.description("Tests that cache miss returns None when changelog entries don't exist")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("cache", "changelog", "cache-miss", "not-found")
    async def test_get_changelog_entries_not_found(self, cache_manager: CacheManager) -> None:
        """Test retrieving non-existent changelog entries returns None."""
        with allure.step("Set up non-existent changelog entries"):
            entries = [
                CommitAnalysis(
                    changes=[Change(summary="Nonexistent", category="Chore")],
                    trivial=True,
                )
            ]
            allure.attach(str(len(entries)), "Number of Entries", allure.attachment_type.TEXT)
            allure.attach(
                entries[0].changes[0].summary, "Entry Summary", allure.attachment_type.TEXT
            )
            allure.attach(str(entries[0].trivial), "Entry Is Trivial", allure.attachment_type.TEXT)

        with allure.step("Attempt to retrieve non-existent changelog entries"):
            result = await cache_manager.get_changelog_entries(entries)
            allure.attach(str(result), "Cache Result", allure.attachment_type.TEXT)

        with allure.step("Verify cache miss returns None"):
            check.is_none(result)

    @allure.story("File System Operations")
    @allure.title("Use correct file extensions for different cache types")
    @allure.description(
        "Tests that cache files are created with appropriate file extensions for each cache type"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("cache", "file-extensions", "file-system", "organization")
    async def test_cache_files_use_correct_extensions(self, cache_manager: CacheManager) -> None:
        """Test that cache files use appropriate extensions."""
        with allure.step("Create various cache entries"):
            # Set various cache entries
            analysis = CommitAnalysis(
                changes=[Change(summary="Test", category="Tests")],
                trivial=False,
            )
            await cache_manager.set_commit_analysis("test123", analysis)

            test_date = date(2025, 1, 7)
            await cache_manager.set_daily_summary(test_date, ["c1"], "daily")
            await cache_manager.set_weekly_summary("2025-02", ["c2"], "weekly")

            allure.attach(
                "Created commit analysis, daily summary, and weekly summary",
                "Cache Entries Created",
                allure.attachment_type.TEXT,
            )

        with allure.step("Check file extensions for each cache type"):
            # Check file extensions
            commit_files = list(cache_manager._commits_path.glob("*.json"))
            daily_files = list(cache_manager._daily_summaries_path.glob("*.txt"))
            weekly_files = list(cache_manager._weekly_summaries_path.glob("*.txt"))

            allure.attach(
                str([f.name for f in commit_files]),
                "Commit Files (.json)",
                allure.attachment_type.TEXT,
            )
            allure.attach(
                str([f.name for f in daily_files]),
                "Daily Files (.txt)",
                allure.attachment_type.TEXT,
            )
            allure.attach(
                str([f.name for f in weekly_files]),
                "Weekly Files (.txt)",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify correct number of files with correct extensions"):
            check.equal(len(commit_files), 1)
            check.equal(len(daily_files), 1)
            check.equal(len(weekly_files), 1)

            allure.attach(str(len(commit_files)), "Commit Files Count", allure.attachment_type.TEXT)
            allure.attach(str(len(daily_files)), "Daily Files Count", allure.attachment_type.TEXT)
            allure.attach(str(len(weekly_files)), "Weekly Files Count", allure.attachment_type.TEXT)

    @allure.story("Concurrency Support")
    @allure.title("Handle concurrent cache operations correctly")
    @allure.description(
        "Tests that multiple concurrent read and write operations work without data corruption"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("cache", "concurrency", "async", "threading")
    async def test_concurrent_cache_operations(self, cache_manager: CacheManager) -> None:
        """Test that concurrent cache operations work correctly."""
        with allure.step("Set up test data for concurrent operations"):
            analyses = [
                CommitAnalysis(
                    changes=[Change(summary=f"Change {i}", category="New Feature")],
                    trivial=False,
                )
                for i in range(10)
            ]
            allure.attach(
                str(len(analyses)), "Number of Analysis Objects", allure.attachment_type.TEXT
            )

        with allure.step("Execute concurrent write operations"):
            tasks = [
                cache_manager.set_commit_analysis(f"hash{i}", analysis)
                for i, analysis in enumerate(analyses)
            ]
            await asyncio.gather(*tasks)
            allure.attach(str(len(tasks)), "Concurrent Write Tasks", allure.attachment_type.TEXT)

        with allure.step("Execute concurrent read operations"):
            read_tasks = [cache_manager.get_commit_analysis(f"hash{i}") for i in range(10)]
            results = await asyncio.gather(*read_tasks)
            allure.attach(
                str(len(read_tasks)), "Concurrent Read Tasks", allure.attachment_type.TEXT
            )
            allure.attach(str(len(results)), "Retrieved Results Count", allure.attachment_type.TEXT)

        with allure.step("Verify all concurrent operations completed successfully"):
            for i, result in enumerate(results):
                check.is_not_none(result)
                if result is not None:
                    check.equal(result.changes[0].summary, f"Change {i}")

            successful_reads = sum(1 for r in results if r is not None)
            allure.attach(str(successful_reads), "Successful Reads", allure.attachment_type.TEXT)

    @allure.story("Unicode Support")
    @allure.title("Cache and retrieve Unicode content correctly")
    @allure.description(
        "Tests that cache handles Unicode characters, emojis, and international text correctly"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("cache", "unicode", "internationalization", "encoding")
    async def test_cache_with_unicode_content(self, cache_manager: CacheManager) -> None:
        """Test caching content with unicode characters."""
        with allure.step("Set up analysis with Unicode content"):
            analysis = CommitAnalysis(
                changes=[
                    Change(summary="Added 日本語 support", category="New Feature"),
                    Change(summary="Fixed émoji 🚀 rendering", category="Bug Fix"),
                ],
                trivial=False,
            )
            unicode_hash = "unicode123"

            allure.attach(unicode_hash, "Unicode Commit Hash", allure.attachment_type.TEXT)
            allure.attach(
                analysis.changes[0].summary, "Japanese Text Summary", allure.attachment_type.TEXT
            )
            allure.attach(
                analysis.changes[1].summary, "Emoji Text Summary", allure.attachment_type.TEXT
            )

        with allure.step("Store Unicode analysis in cache"):
            await cache_manager.set_commit_analysis(unicode_hash, analysis)
            allure.attach(
                "Unicode analysis cached successfully",
                "Storage Status",
                allure.attachment_type.TEXT,
            )

        with allure.step("Retrieve Unicode analysis from cache"):
            retrieved = await cache_manager.get_commit_analysis(unicode_hash)
            allure.attach(str(type(retrieved)), "Retrieved Type", allure.attachment_type.TEXT)

        with allure.step("Verify Unicode content was preserved"):
            check.is_not_none(retrieved)
            check.equal(retrieved.changes[0].summary, "Added 日本語 support")  # type: ignore[union-attr]
            check.equal(
                retrieved.changes[1].summary,  # type: ignore[union-attr]
                "Fixed émoji 🚀 rendering",
            )

            if retrieved is not None:
                allure.attach(
                    retrieved.changes[0].summary,
                    "Retrieved Japanese Text",
                    allure.attachment_type.TEXT,
                )
                allure.attach(
                    retrieved.changes[1].summary,
                    "Retrieved Emoji Text",
                    allure.attachment_type.TEXT,
                )

    @allure.story("Hash Generation Edge Cases")
    @allure.title("Generate consistent hash for empty commit list")
    @allure.description("Tests that empty commit lists produce consistent and valid hashes")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("cache", "hashing", "edge-case", "empty-list")
    async def test_empty_commit_list_hash(self, cache_manager: CacheManager) -> None:
        """Test hash generation with empty commit list."""
        with allure.step("Generate hash for empty commit list"):
            empty_hash = cache_manager._get_hash([])
            allure.attach(empty_hash, "Empty List Hash 1", allure.attachment_type.TEXT)
            allure.attach(str(len(empty_hash)), "Hash Length", allure.attachment_type.TEXT)

        with allure.step("Generate second hash for empty list to test consistency"):
            empty_hash2 = cache_manager._get_hash([])
            allure.attach(empty_hash2, "Empty List Hash 2", allure.attachment_type.TEXT)

        with allure.step("Verify empty list hash properties"):
            check.equal(len(empty_hash), 16)
            # Empty list should produce consistent hash
            check.equal(empty_hash, empty_hash2)

            allure.attach(
                str(empty_hash == empty_hash2), "Hashes Are Identical", allure.attachment_type.TEXT
            )
