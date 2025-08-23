# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Refactored artifact writer with extracted utility modules."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import TYPE_CHECKING

import aiofiles
import aiofiles.os
from rich.console import Console

from git_ai_reporter.utils.async_file_utils import async_read_file_safe
from git_ai_reporter.utils.async_file_utils import async_write_file_atomic
from git_ai_reporter.writing.changelog_utils import create_changelog_template
from git_ai_reporter.writing.changelog_utils import find_unreleased_section
from git_ai_reporter.writing.changelog_utils import merge_changelog_changes
from git_ai_reporter.writing.changelog_utils import rebuild_unreleased_section
from git_ai_reporter.writing.changelog_utils import reconstruct_changelog
from git_ai_reporter.writing.content_formatting import insert_content_after_header
from git_ai_reporter.writing.content_formatting import wrap_text_lines
from git_ai_reporter.writing.markdown_utils import format_week_header
from git_ai_reporter.writing.markdown_utils import generate_yaml_frontmatter
from git_ai_reporter.writing.markdown_utils import parse_changelog_section
from git_ai_reporter.writing.news_utils import find_duplicate_week_groups
from git_ai_reporter.writing.news_utils import generate_summary_metrics_from_dict
from git_ai_reporter.writing.news_utils import generate_table_of_contents
from git_ai_reporter.writing.news_utils import normalize_entry_dates
from git_ai_reporter.writing.news_utils import parse_weekly_entries

if TYPE_CHECKING:
    from git_ai_reporter.services.gemini import GeminiClient

# File headers
NEWS_HEADER = "# Project News"
DAILY_UPDATES_HEADER = "# Daily Updates"

# Constants for date validation
DATE_STRING_LENGTH = 10
DATE_SEPARATOR_COUNT = 2

# Constants for changelog formatting
UNRELEASED_HEADER_SEPARATOR = "\n\n"


@dataclass
class NewsFileParams:
    """Parameters for updating news file."""

    narrative: str
    start_date: datetime
    end_date: datetime
    gemini_client: "GeminiClient | None" = None
    metrics: dict[str, int] | None = None
    pre_release_version: str | None = None


@dataclass
class NewsEntryParams:
    """Parameters for creating a new news entry."""

    narrative: str
    week_header: str
    start_date: datetime
    metrics: dict[str, int] | None = None
    pre_release_version: str | None = None


@dataclass
class ChangelogUpdateParams:
    """Parameters for updating changelog file."""

    new_entries_md: str
    pre_release_version: str | None = None


class ArtifactWriter:
    """Handles reading from and writing to the NEWS and CHANGELOG files."""

    def __init__(
        self,
        news_file: str,
        changelog_file: str,
        daily_updates_file: str,
        console: Console,
    ):
        """Initialize the ArtifactWriter.

        Args:
            news_file: The file path for the NEWS.md file.
            changelog_file: The file path for the CHANGELOG.txt file.
            daily_updates_file: The file path for the DAILY_UPDATES.md file.
            console: An instance of rich.console.Console for printing output.
        """
        self.news_path = Path(news_file)
        self.changelog_path = Path(changelog_file)
        self.daily_updates_path = Path(daily_updates_file)
        self._console = console
        self._week_counter = 0

    async def _read_historical_summaries(self) -> str:
        """Parse existing artifacts to provide historical context for generation.

        Returns:
            A formatted string containing the last 4 weekly summaries and the
            recent daily summaries.
        """
        history_parts = []

        # Get last 4 weekly summaries from NEWS.md
        if await aiofiles.os.path.exists(self.news_path):
            if content := await async_read_file_safe(self.news_path):
                weekly_entries = parse_weekly_entries(content)
                if recent_entries := weekly_entries[:4]:
                    history_parts.append("## Recent Weekly Summaries")
                    for entry in recent_entries:
                        history_parts.append(f"### {entry['header']}")
                        history_parts.append(str(entry["content"]))

        # Get previous week's daily updates
        if await aiofiles.os.path.exists(self.daily_updates_path):
            if content := await async_read_file_safe(self.daily_updates_path):
                # Simple extraction - could be enhanced with proper parsing
                history_parts.append("## Recent Daily Updates")
                history_parts.append(content[:1000])  # Limit to first 1000 chars

        return "\n\n".join(history_parts) if history_parts else ""

    async def read_existing_daily_summaries(self) -> dict[str, str]:
        """Read existing daily summaries from DAILY_UPDATES.md file.

        Returns:
            Dictionary mapping date strings (YYYY-MM-DD) to summary content.
        """
        if not await aiofiles.os.path.exists(self.daily_updates_path):
            return {}

        if not (content := await async_read_file_safe(self.daily_updates_path)):
            return {}

        summaries = {}
        lines = content.split("\n")
        current_date = None
        current_content: list[str] = []

        for line in lines:
            # Look for date headers like "### 2025-08-10" or "## 2025-08-10"
            if line.startswith("### ") or line.startswith("## "):
                # Save previous summary if we have one
                if current_date and current_content:
                    summaries[current_date] = "\n".join(current_content).strip()

                # Extract new date
                date_part = line.lstrip("# ").strip()
                if (
                    len(date_part) == DATE_STRING_LENGTH
                    and date_part.count("-") == DATE_SEPARATOR_COUNT
                ):  # YYYY-MM-DD format
                    current_date = date_part
                    current_content = []
                else:
                    current_date = None
                    current_content = []
            elif current_date:
                # Accumulate content for current date
                current_content.append(line)

        # Don't forget the last summary
        if current_date and current_content:
            summaries[current_date] = "\n".join(current_content).strip()

        return summaries

    async def _insert_content_after_header(
        self, file_path: Path, content: str, header: str
    ) -> None:
        """Insert content after a header in a file.

        Args:
            file_path: Path to the file.
            content: Content to insert.
            header: Header to insert content after.
        """
        existing_content = await async_read_file_safe(file_path) or ""
        updated_content = insert_content_after_header(existing_content, content, header)
        await async_write_file_atomic(file_path, updated_content)

    async def _read_or_create_news_file(self) -> str:
        """Read existing news file content or return empty string if not found."""
        return await async_read_file_safe(self.news_path) or ""

    async def _create_new_news_entry(self, params: NewsEntryParams) -> str:
        """Create a new news entry with proper formatting.

        Args:
            params: Parameters for creating the news entry.

        Returns:
            Formatted news entry string.
        """
        # pre_release_version is used indirectly via week_header formatting
        _ = params.pre_release_version  # Acknowledge unused parameter

        yaml_front = generate_yaml_frontmatter(
            "Project News",
            "Development summaries and project updates",
            params.start_date,
            datetime.now(),
        )

        wrapped_narrative = wrap_text_lines(params.narrative)

        metrics_section = ""
        if params.metrics and params.metrics.get("commits_analyzed", 0) > 0:
            metrics_section = f"\n{generate_summary_metrics_from_dict(params.metrics)}\n"

        return f"{yaml_front}\n{params.week_header}\n\n{wrapped_narrative}{metrics_section}\n"

    async def _merge_news_entries(
        self,
        existing_entry: dict[str, str | datetime],
        new_narrative: str,
        gemini_client: "GeminiClient | None",
    ) -> str:
        """Merge existing and new narrative content."""
        if gemini_client:
            self._console.print("Found existing entry for week, merging content...", style="yellow")

            existing_content = str(existing_entry["content"])
            merged_summaries = (
                f"Previous summary:\n{existing_content}\n\nNew summary:\n{new_narrative}"
            )

            new_narrative = await gemini_client.generate_news_narrative(
                commit_summaries=merged_summaries,
                daily_summaries="",
                weekly_diff="",
                history="",
            )

            self._console.print("Successfully merged and re-summarized week entry", style="green")
            return new_narrative
        else:
            self._console.print(
                "Found existing entry for week, replacing content...", style="yellow"
            )
            return new_narrative

    async def _save_weekly_entries(self, entries: list[dict[str, str | datetime]]) -> None:
        """Sort and save weekly entries to the news file."""
        entries = normalize_entry_dates(entries)
        entries.sort(key=lambda x: x["start_date"], reverse=True)
        await self._write_news_file_with_entries(entries)

    async def update_news_file(self, params: NewsFileParams) -> None:
        """Update the weekly narrative in NEWS.md file."""
        week_header = format_week_header(
            params.start_date, params.end_date, params.pre_release_version
        )
        existing_content = await self._read_or_create_news_file()

        if not existing_content.strip():
            entry_params = NewsEntryParams(
                narrative=params.narrative,
                week_header=week_header,
                start_date=params.start_date,
                metrics=params.metrics,
                pre_release_version=params.pre_release_version,
            )
            content_block = await self._create_new_news_entry(entry_params)
            await self._insert_content_after_header(self.news_path, content_block, NEWS_HEADER)
            self._console.print(f"Successfully updated {self.news_path}", style="green")
            return

        weekly_entries = parse_weekly_entries(existing_content)
        weekly_entries = await self._auto_consolidate_duplicates(
            weekly_entries, params.gemini_client
        )

        existing_entry = None
        for entry in weekly_entries:
            if entry["header"] == week_header:
                existing_entry = entry
                break

        if existing_entry:
            merged_narrative = await self._merge_news_entries(
                existing_entry, params.narrative, params.gemini_client
            )
            existing_entry["content"] = merged_narrative
        else:
            weekly_entries.append(
                {
                    "header": week_header,
                    "content": params.narrative,
                    "start_date": params.start_date,
                    "end_date": params.end_date,
                }
            )

        await self._save_weekly_entries(weekly_entries)
        self._console.print(f"Successfully updated {self.news_path}", style="green")

    async def _write_news_file_with_entries(
        self, weekly_entries: list[dict[str, str | datetime]]
    ) -> None:
        """Write the NEWS.md file with the given weekly entries."""
        if not weekly_entries:
            return

        # Generate YAML frontmatter and table of contents
        first_entry_start_date = weekly_entries[0]["start_date"]
        # Ensure it's a datetime object
        first_entry_date = (
            datetime.fromisoformat(first_entry_start_date)
            if isinstance(first_entry_start_date, str)
            else first_entry_start_date
        )
        yaml_front = generate_yaml_frontmatter(
            "Project News",
            "Development summaries and project updates",
            first_entry_date,
            datetime.now(),
        )

        toc = generate_table_of_contents(weekly_entries)

        # Build the content
        content_lines = [yaml_front, NEWS_HEADER, "", toc]

        for entry in weekly_entries:
            content_lines.append(str(entry["header"]))
            content_lines.append("")
            content_lines.append(str(entry["content"]))
            content_lines.append("")

        final_content = "\n".join(content_lines)
        await async_write_file_atomic(self.news_path, final_content)

    async def _validate_news_file_exists(self) -> tuple[bool, str]:
        """Check if news file exists and has content."""
        if not await aiofiles.os.path.exists(self.news_path):
            return False, "NEWS.md file does not exist, nothing to consolidate"

        content = await async_read_file_safe(self.news_path)
        if not content or not content.strip():
            return False, "NEWS.md file is empty, nothing to consolidate"

        return True, content

    async def _consolidate_week_groups(
        self,
        week_groups: dict[str, list[dict[str, str | datetime]]],
        gemini_client: "GeminiClient | None",
    ) -> tuple[list[dict[str, str | datetime]], bool]:
        """Process week groups and merge duplicates."""
        consolidated_entries = []
        duplicates_found = False

        for header, entries in week_groups.items():
            if len(entries) == 1:
                consolidated_entries.append(entries[0])
            else:
                duplicates_found = True
                self._console.print(
                    f"Found {len(entries)} duplicate entries for {header}", style="yellow"
                )
                merged_entry = await self._merge_duplicate_entries(entries, gemini_client)
                consolidated_entries.append(merged_entry)

        return consolidated_entries, duplicates_found

    async def consolidate_duplicate_weeks(
        self, gemini_client: "GeminiClient | None" = None
    ) -> None:
        """Clean up existing duplicate week entries in NEWS.md."""
        file_valid, content = await self._validate_news_file_exists()
        if not file_valid:
            self._console.print(content, style="yellow")
            return

        weekly_entries = parse_weekly_entries(content)

        if len(weekly_entries) <= 1:
            self._console.print("No duplicate weeks found", style="green")
            return

        week_groups = find_duplicate_week_groups(weekly_entries)
        consolidated_entries, duplicates_found = await self._consolidate_week_groups(
            week_groups, gemini_client
        )

        if not duplicates_found:
            self._console.print("No duplicate weeks found", style="green")
            return

        consolidated_entries = normalize_entry_dates(consolidated_entries)
        consolidated_entries.sort(key=lambda x: x["start_date"], reverse=True)

        await self._write_news_file_with_entries(consolidated_entries)
        self._console.print(
            f"Successfully consolidated duplicate weeks in {self.news_path}", style="green"
        )

    async def _merge_duplicate_entries(
        self, entries: list[dict[str, str | datetime]], gemini_client: "GeminiClient | None"
    ) -> dict[str, str | datetime]:
        """Merge multiple duplicate entries into a single entry."""
        if len(entries) == 1:
            return entries[0]

        base_entry = entries[0].copy()
        all_content = []
        for entry in entries:
            if content := str(entry["content"]).strip():
                all_content.append(content)

        if gemini_client and len(all_content) > 1:
            # Use AI to merge content intelligently
            merged_summaries = "\n\n".join(all_content)
            new_narrative = await gemini_client.generate_news_narrative(
                commit_summaries=merged_summaries,
                daily_summaries="",
                weekly_diff="",
                history="",
            )
            base_entry["content"] = new_narrative
        else:
            # Simple concatenation fallback
            base_entry["content"] = "\n\n".join(all_content)

        return base_entry

    async def _auto_consolidate_duplicates(
        self, weekly_entries: list[dict[str, str | datetime]], gemini_client: "GeminiClient | None"
    ) -> list[dict[str, str | datetime]]:
        """Automatically consolidate any duplicate entries found."""
        week_groups = find_duplicate_week_groups(weekly_entries)

        if not any(len(entries) > 1 for entries in week_groups.values()):
            return weekly_entries

        consolidated_entries, _ = await self._consolidate_week_groups(week_groups, gemini_client)
        return consolidated_entries

    def _parse_daily_entries(self, content: str) -> dict[str, str]:
        """Parse daily entries from content into a date -> content mapping."""

        entries = {}
        # Find all date headers and their content
        pattern = r"### (\d{4}-\d{2}-\d{2})\n\n(.*?)(?=\n### \d{4}-\d{2}-\d{2}|\Z)"
        matches = re.findall(pattern, content, re.DOTALL)

        for date, entry_content in matches:
            entries[date] = entry_content.strip()

        return entries

    def _merge_and_sort_daily_entries(
        self, existing_entries: dict[str, str], new_summaries: list[str]
    ) -> str:
        """Merge new summaries with existing entries and sort by date (newest first)."""

        # Parse new summaries into date -> content mapping
        new_entries = {}
        for summary in new_summaries:
            # Extract date and content from each summary
            if match := re.match(r"### (\d{4}-\d{2}-\d{2})\n\n(.*)", summary, re.DOTALL):
                date, content = match.groups()
                new_entries[date] = content.strip()

        # Merge entries (existing entries take precedence over new ones with same date)
        all_entries = {**new_entries, **existing_entries}

        # Sort dates in descending order (newest first)
        sorted_dates = sorted(all_entries.keys(), reverse=True)

        # Build the content string
        content_parts = []
        for date in sorted_dates:
            content_parts.append(f"### {date}\n\n{all_entries[date]}")

        return "\n\n".join(content_parts)

    async def update_daily_updates_file(self, daily_summaries: list[str]) -> None:
        """Update the DAILY_UPDATES.md file with new entries, merging and sorting by date."""
        if not daily_summaries:
            return

        existing_content = await async_read_file_safe(self.daily_updates_path) or ""

        if DAILY_UPDATES_HEADER not in existing_content:
            # New file - parse and sort the entries before adding them
            merged_content = self._merge_and_sort_daily_entries({}, daily_summaries)
            yaml_front = generate_yaml_frontmatter(
                "Daily Updates",
                "Daily development activity summaries",
                datetime.now(),
                datetime.now(),
            )
            content = f"{yaml_front}\n{DAILY_UPDATES_HEADER}\n\n{merged_content}\n\n"
        else:
            # Parse existing entries
            existing_entries = self._parse_daily_entries(existing_content)

            # Merge and sort all entries
            merged_content = self._merge_and_sort_daily_entries(existing_entries, daily_summaries)

            # Replace content after header
            if (header_pos := existing_content.find(DAILY_UPDATES_HEADER)) != -1:
                header_end = existing_content.find("\n", header_pos + len(DAILY_UPDATES_HEADER))
                if header_end == -1:
                    header_end = len(existing_content)

                # Keep everything up to and including the header line, then add merged content
                content = existing_content[: header_end + 1] + "\n" + merged_content + "\n\n"
            else:
                content = (
                    existing_content
                    + "\n\n"
                    + DAILY_UPDATES_HEADER
                    + "\n\n"
                    + merged_content
                    + "\n\n"
                )

        await async_write_file_atomic(self.daily_updates_path, content)
        self._console.print(f"Successfully updated {self.daily_updates_path}", style="green")

    async def _ensure_changelog_exists(self) -> str:
        """Ensure changelog file exists, creating template if needed."""
        if not await aiofiles.os.path.exists(self.changelog_path):
            template = create_changelog_template()
            await async_write_file_atomic(self.changelog_path, template)
            return template
        else:
            content = await async_read_file_safe(self.changelog_path)
            if not content or not content.strip():
                template = create_changelog_template()
                await async_write_file_atomic(self.changelog_path, template)
                return template
            return content

    def _create_version_section(
        self, pre_release_version: str, merged_changes: dict[str, list[str]]
    ) -> str:
        """Create a version-specific section for the completed release.

        Args:
            pre_release_version: Version string for the release.
            merged_changes: Merged changelog changes.

        Returns:
            Formatted version section string.
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        # Ensure version has 'v' prefix but don't double-prefix
        version = (
            pre_release_version
            if pre_release_version.startswith("v")
            else f"v{pre_release_version}"
        )
        updated_entries_str = f"## [{version}] - {current_date}\n\n"

        # Add the actual changes without the "[Unreleased]" header
        changes_content = rebuild_unreleased_section(merged_changes)
        # Remove the "## [Unreleased]" header and leading newlines
        changes_without_header = (
            changes_content.split(UNRELEASED_HEADER_SEPARATOR, 1)[1]
            if UNRELEASED_HEADER_SEPARATOR in changes_content
            else ""
        )
        updated_entries_str += changes_without_header
        # Add a new empty [Unreleased] section for future changes
        updated_entries_str += "\n\n## [Unreleased]\n\n*No unreleased changes yet.*\n"

        return updated_entries_str

    def _process_changelog_changes(
        self, params: ChangelogUpdateParams, existing_entries: str
    ) -> str:
        """Process and merge changelog changes.

        Args:
            params: Changelog update parameters.
            existing_entries: Existing changelog entries.

        Returns:
            Updated entries string.
        """
        new_changes = parse_changelog_section(params.new_entries_md)
        existing_changes = parse_changelog_section(existing_entries)
        merged_changes = merge_changelog_changes(new_changes, existing_changes)

        if params.pre_release_version:
            return self._create_version_section(params.pre_release_version, merged_changes)
        else:
            return rebuild_unreleased_section(merged_changes)

    async def update_changelog_file(
        self, new_entries_md: str, pre_release_version: str | None = None
    ) -> None:
        """Intelligently merge new entries into the [Unreleased] section of the changelog.

        Args:
            new_entries_md: New changelog entries in markdown format.
            pre_release_version: If provided, formats for upcoming release (e.g., "1.2.3").
        """
        params = ChangelogUpdateParams(new_entries_md, pre_release_version)

        content = await self._ensure_changelog_exists()

        if not (section_parts := find_unreleased_section(content)):
            self._console.print(
                "Could not find '## [Unreleased]' section in CHANGELOG.",
                style="bold red",
            )
            return

        prefix, existing_entries, suffix = section_parts
        updated_entries_str = self._process_changelog_changes(params, existing_entries)

        original_match = f"{prefix}{existing_entries}{suffix}"
        final_content = reconstruct_changelog(
            content, updated_entries_str, prefix, suffix, original_match
        )

        await async_write_file_atomic(self.changelog_path, final_content)
        self._console.print(f"Successfully updated {self.changelog_path}", style="green")
