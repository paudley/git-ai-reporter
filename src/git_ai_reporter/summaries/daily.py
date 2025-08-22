# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Handles the AI-powered synthesis of daily commit summaries."""

from typing import Final

PROMPT_TEMPLATE: Final[
    str
] = """You are a technical project manager summarizing a day's work.
Your task is to synthesize the provided git log and diff into a coherent, high-level summary.

**Formatting Rules:**
- Do NOT include any salutations, metadata, or headers like 'Date:' or 'Summary:'.
- Do NOT start with conversational text like 'Of course, here is the summary...'.
- Do NOT include horizontal rules (---).
- **Structure your response as follows:**
  1. A one-sentence title that captures the main theme of the day's work.
  2. A short paragraph (2-3 sentences) elaborating on the day's key activities and goals.
  3. A bulleted list of the most notable individual changes or accomplishments.
- Begin the response *directly* with the title.

**Full Daily Git Log:**
```
{full_log}
```

**Consolidated Daily Diff:**
```diff
{daily_diff}
```

**Summary:**
"""
