# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Handles the AI-powered generation of the weekly news narrative."""

from typing import Final

PROMPT_TEMPLATE: Final[str] = (
    "You are a product manager writing a detailed weekly development update for project\n"
    "stakeholders.\n"
    "Your summary should be approximately 500 words.\n\n"
    "First, review the historical context to understand the project's trajectory.\n"
    ""
    "Do not repeat information from the history section in your new summary.\n"
    "Then, based on the new information for the current period, write a compelling,\n"
    "high-level narrative.\n\n"
    "**Formatting Rules:**\n"
    "- Do NOT include any salutations or metadata like 'To:', 'From:', 'Date:', or 'Subject:'.\n"
    "- Do NOT start with conversational text like 'Of course, here is the summary...'.\n"
    "- Begin the response *directly* with the main narrative content.\n\n"
    "**Content Requirements:**\n"
    "1.  A breakdown of the major additions or changes to the codebase.\n"
    "2.  An analysis of any new external dependencies added. Look for changes in files\n"
    "like `pyproject.toml`.\n"
    "Do not include testing or development dependencies.\n"
    "3.  The overall themes of the week's work.\n\n"
    'After the main narrative, provide a bulleted list of "Notable Changes" which should include '
    "major new features, security fixes, or other significant individual changes.\n\n"
    "---\n"
    "## HISTORICAL CONTEXT (Recent Past)\n"
    "{history}\n\n"
    "---\n"
    "## CURRENT PERIOD ANALYSIS (Your Task)\n"
    "### 1. All Individual Commit Summaries (Micro-Level)\n"
    'Use these to find specific, impactful examples or details for the "Notable Changes" list.\n'
    "{commit_summaries}\n\n"
    "### 2. Synthesized Daily Summaries (Mezzo-Level)\n"
    "Use these to understand the day-to-day progression and rhythm of the work.\n"
    "{daily_summaries}\n\n"
    "### 3. Full Period Diff (Macro-Level)\\n"
    "Use this for the main themes and structure of your narrative. This includes code and "
    "dependency file changes.\\n"
    "```diff\\n"
    "{weekly_diff}\n"
    "```"
)
