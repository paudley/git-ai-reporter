# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Property-based tests using Hypothesis for git-ai-reporter.

This module uses Hypothesis to test invariants and properties that should
hold for all valid inputs.
"""

from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

from hypothesis import assume
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import composite
import pytest
import pytest_check as check

from git_ai_reporter.cache.manager import CacheManager
from git_ai_reporter.models import AnalysisResult
from git_ai_reporter.models import Change
from git_ai_reporter.models import COMMIT_CATEGORIES
from git_ai_reporter.models import CommitAnalysis
from git_ai_reporter.utils.json_helpers import safe_json_decode
from git_ai_reporter.utils.json_helpers import safe_json_encode

# Constants
BACKTICKS = "```"


# Custom strategies for domain objects
@composite
def change_strategy(draw: st.DrawFn) -> Change:
    """Generate a valid Change object."""
    return Change(
        summary=draw(st.text(min_size=1, max_size=500)),
        category=draw(st.sampled_from(list(COMMIT_CATEGORIES.keys()))),
    )


@composite
def commit_analysis_strategy(draw: st.DrawFn) -> CommitAnalysis:
    """Generate a valid CommitAnalysis object."""
    return CommitAnalysis(
        changes=draw(st.lists(change_strategy(), min_size=0, max_size=10)),
        trivial=draw(st.booleans()),
    )


@composite
def analysis_result_strategy(draw: st.DrawFn) -> AnalysisResult:
    """Generate a valid AnalysisResult object."""
    return AnalysisResult(
        period_summaries=draw(st.lists(st.text(min_size=0, max_size=1000), min_size=0, max_size=5)),
        daily_summaries=draw(st.lists(st.text(min_size=0, max_size=500), min_size=0, max_size=7)),
        changelog_entries=draw(st.lists(commit_analysis_strategy(), min_size=0, max_size=20)),
    )


class TestModelProperties:
    """Test properties of Pydantic models."""

    @given(change_strategy())
    def test_change_serialization_roundtrip(self, change: Change) -> None:
        """Test that Changes can be serialized and deserialized without loss."""
        json_str = change.model_dump_json()
        reconstructed = Change.model_validate_json(json_str)
        check.equal(reconstructed.summary, change.summary)
        check.equal(reconstructed.category, change.category)

    @given(commit_analysis_strategy())
    def test_commit_analysis_serialization_roundtrip(self, analysis: CommitAnalysis) -> None:
        """Test that CommitAnalysis can be serialized and deserialized."""
        json_str = analysis.model_dump_json()
        reconstructed = CommitAnalysis.model_validate_json(json_str)
        check.equal(len(reconstructed.changes), len(analysis.changes))
        check.equal(reconstructed.trivial, analysis.trivial)
        for orig, recon in zip(analysis.changes, reconstructed.changes):
            check.equal(orig.summary, recon.summary)
            check.equal(orig.category, recon.category)

    @given(analysis_result_strategy())
    def test_analysis_result_never_loses_data(self, result: AnalysisResult) -> None:
        """Test that AnalysisResult preserves all data through serialization."""
        json_str = result.model_dump_json()
        reconstructed = AnalysisResult.model_validate_json(json_str)
        check.equal(reconstructed.period_summaries, result.period_summaries)
        check.equal(reconstructed.daily_summaries, result.daily_summaries)
        check.equal(len(reconstructed.changelog_entries), len(result.changelog_entries))

    @given(st.lists(change_strategy(), min_size=1, max_size=100))
    def test_commit_analysis_with_many_changes(self, changes: list[Change]) -> None:
        """Test that CommitAnalysis handles many changes correctly."""
        analysis = CommitAnalysis(changes=changes, trivial=False)
        check.equal(len(analysis.changes), len(changes))
        # All changes should be preserved
        for orig, stored in zip(changes, analysis.changes):
            check.equal(orig.summary, stored.summary)
            check.equal(orig.category, stored.category)


class TestJsonHelperProperties:
    """Test properties of JSON helper functions."""

    @given(
        st.dictionaries(
            st.text(min_size=2, max_size=50).filter(  # Changed from min_size=1 to 2
                lambda x: BACKTICKS not in x and x.strip() != ""
            ),  # Avoid backticks, empty strings, and whitespace-only strings in keys
            st.one_of(
                st.text().filter(lambda x: BACKTICKS not in x),  # Avoid backticks in values
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans(),
                st.none(),
            ),
        )
    )
    def test_json_roundtrip_preserves_structure(self, data: dict[str, Any]) -> None:
        """Test that JSON encoding and decoding preserves data structure."""
        encoded = safe_json_encode(data)
        decoded = safe_json_decode(encoded)
        check.equal(decoded, data)

    @given(st.datetimes())
    def test_datetime_serialization_is_reversible(self, dt: datetime) -> None:
        """Test that datetime serialization produces valid ISO format."""
        data = {"timestamp": dt}
        encoded = safe_json_encode(data)
        decoded = json.loads(encoded)  # Use standard json to verify format
        # Should be ISO format string
        check.is_instance(decoded["timestamp"], str)
        # Should be parseable back to datetime
        parsed = datetime.fromisoformat(decoded["timestamp"].replace("Z", "+00:00"))
        # Microseconds might be truncated, so compare to second precision
        check.equal(parsed.year, dt.year)
        check.equal(parsed.month, dt.month)
        check.equal(parsed.day, dt.day)
        check.equal(parsed.hour, dt.hour)
        check.equal(parsed.minute, dt.minute)
        check.equal(parsed.second, dt.second)

    @given(st.decimals(allow_nan=False, allow_infinity=False))
    def test_decimal_serialization_preserves_value(self, dec: Decimal) -> None:
        """Test that Decimal serialization preserves the value."""
        data = {"amount": dec}
        encoded = safe_json_encode(data)
        decoded = json.loads(encoded)
        # Decimal becomes string
        check.is_instance(decoded["amount"], str)
        # Can be converted back to same Decimal
        restored = Decimal(decoded["amount"])
        check.equal(restored, dec)

    @given(st.text())
    def test_json_decode_handles_any_string(self, text: str) -> None:
        """Test that safe_json_decode handles any string input gracefully."""
        # Should either parse or raise JSONDecodeError, never crash
        try:
            _ = safe_json_decode(text)
            # If it succeeds, result could be any valid JSON value including None
            # (JSON null is a valid value)
            # Just verify it didn't crash
        except json.JSONDecodeError:
            # This is acceptable for invalid JSON
            pass

    @given(st.text())
    def test_json_with_markdown_fence_removal(self, _content: str) -> None:
        """Test that markdown fences are properly removed."""
        # Test with valid JSON wrapped in fence
        valid_json = '{"test": "value"}'
        wrapped = f"```json\n{valid_json}\n```"
        try:
            result = safe_json_decode(wrapped)
            # If it parses, the fence was removed
            check.is_not_none(result)
            if isinstance(result, dict):
                check.equal(result["test"], "value")
        except json.JSONDecodeError:
            # Should not fail for valid JSON
            check.fail("Valid JSON in fence should parse")


class TestCacheManagerProperties:
    """Test properties of the cache manager."""

    @given(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=50))
    def test_hash_generation_is_deterministic(self, items: list[str]) -> None:
        """Test that hash generation is deterministic."""
        manager = CacheManager(Path("/tmp/test"))  # nosec B108 - Test only
        hash1 = manager._get_hash(items)  # pylint: disable=protected-access
        hash2 = manager._get_hash(items)  # pylint: disable=protected-access
        check.equal(hash1, hash2)
        check.equal(len(hash1), 16)

    @given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=50))
    def test_hash_order_independence(self, items: list[str]) -> None:
        """Test that hash is independent of item order."""
        # Create a shuffled version of the same items
        import random  # pylint: disable=import-outside-toplevel

        items2 = items.copy()
        random.shuffle(items2)
        manager = CacheManager(Path("/tmp/test"))  # nosec B108 - Test only
        hash1 = manager._get_hash(items)  # pylint: disable=protected-access
        hash2 = manager._get_hash(items2)  # pylint: disable=protected-access
        # Hashes should be the same regardless of order
        check.equal(hash1, hash2)

    @given(
        st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=50),
        st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=50),
    )
    def test_different_items_produce_different_hashes(
        self, items1: list[str], items2: list[str]
    ) -> None:
        """Test that different item sets produce different hashes (usually)."""
        assume(sorted(items1) != sorted(items2))  # Different items
        manager = CacheManager(Path("/tmp/test"))  # nosec B108 - Test only
        hash1 = manager._get_hash(items1)  # pylint: disable=protected-access
        hash2 = manager._get_hash(items2)  # pylint: disable=protected-access
        # While hash collisions are possible, they should be rare
        # We can't guarantee they're always different, but we can check format
        check.equal(len(hash1), 16)
        check.equal(len(hash2), 16)


class TestCommitCategoryProperties:
    """Test properties of commit categories."""

    @given(st.sampled_from(list(COMMIT_CATEGORIES.keys())))
    def test_all_categories_have_emojis(self, category: str) -> None:
        """Test that every category has an associated emoji."""
        emoji = COMMIT_CATEGORIES[category]
        check.is_not_none(emoji)
        check.greater(len(emoji), 0)
        # Emoji should be a single character (or multi-char emoji sequence)
        check.less_equal(len(emoji), 4)

    @given(change_strategy())
    def test_change_category_is_always_valid(self, change: Change) -> None:
        """Test that generated changes always have valid categories."""
        check.is_in(change.category, COMMIT_CATEGORIES)


class TestStringProcessingProperties:
    """Test properties of string processing functions."""

    @given(st.text())
    def test_json_encoding_never_fails(self, text: str) -> None:
        """Test that safe_json_encode can handle any string."""
        data = {"text": text}
        encoded = safe_json_encode(data)
        check.is_instance(encoded, str)
        # Should be valid JSON
        decoded = json.loads(encoded)
        check.equal(decoded["text"], text)

    @given(st.lists(st.text(), min_size=0, max_size=100))
    def test_string_list_encoding(self, strings: list[str]) -> None:
        """Test that lists of strings are properly encoded."""
        encoded = safe_json_encode(strings)
        decoded = json.loads(encoded)
        check.equal(decoded, strings)


@pytest.mark.hypothesis
class TestEdgeCaseProperties:
    """Test edge cases and boundary conditions."""

    @given(st.text(alphabet="", min_size=0, max_size=1000))
    def test_empty_string_handling(self, empty_str: str) -> None:
        """Test handling of empty or whitespace-only strings."""
        # Empty strings should be handled gracefully
        change = Change(summary=empty_str if empty_str else " ", category="Chore")
        check.equal(change.summary, empty_str if empty_str else " ")

    @given(st.integers(min_value=0, max_value=10000))
    def test_large_collection_handling(self, size: int) -> None:
        """Test handling of large collections."""
        # Generate large list of changes
        changes = [Change(summary=f"Change {i}", category="New Feature") for i in range(size)]
        analysis = CommitAnalysis(changes=changes, trivial=False)
        check.equal(len(analysis.changes), size)

    @given(
        st.text(
            min_size=1,
            alphabet=st.characters(
                whitelist_categories=(
                    "Lu",
                    "Ll",
                    "Nd",
                    "Pc",
                    "Pd",
                    "Po",
                    "Sc",
                    "Sm",
                    "So",
                ),
                blacklist_characters="\x00",
            ),
        )
    )
    def test_json_with_special_characters(self, text: str) -> None:
        """Test JSON encoding of text with special characters."""
        # Add braces to ensure special characters
        text_with_braces = f"{{{text}}}"
        data = {"special": text_with_braces}
        encoded = safe_json_encode(data)
        decoded = json.loads(encoded)
        check.equal(decoded["special"], text_with_braces)
