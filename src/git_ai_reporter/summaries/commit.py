# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Handles the AI-powered analysis of a single git commit."""

from typing import Final

from git_ai_reporter.models import COMMIT_CATEGORIES

# Used by gemini.py for commit analysis
# Build the prompt template with dynamic category list
PROMPT_TEMPLATE: Final[
    str
] = f"""You are an expert senior software engineer tasked with analyzing a git diff to produce a
structured summary. Your goal is to identify all distinct logical changes within the commit
and format them as a JSON object.
This output will be used to automatically generate changelogs and project reports.

**Instructions:**

1.  **Analyze the Diff:** Carefully examine the provided `git diff`.
2.  **Identify Logical Changes:** A single commit can contain multiple distinct changes. A logical
    change is a self-contained modification that achieves a single purpose (e.g., adding a feature,
    fixing a bug, refactoring a function, updating documentation). Identify every logical change in
    the diff.
3.  **Summarize Each Change:** For each change, write a concise, one-sentence summary in the
    imperative mood (e.g., "Add new user authentication endpoint.").
4.  **Categorize Each Change:** Assign one of the following categories to each change:
    {", ".join(f"'{cat}'" for cat in COMMIT_CATEGORIES)}.
5.  **Assess Triviality:** Determine if the *entire* commit is trivial. A commit is trivial only if
    ALL its changes are categorized as `Documentation`, `Styling`, `Tests`, or `Chore`. If any
    change
    is a `New Feature`, `Bug Fix`, `Refactoring`, etc., the commit is NOT trivial.
6.  **Format as JSON:** Your entire response **MUST** be a single, valid JSON object. Do not include
    any explanatory text, markdown formatting, or code fences. The JSON object must have two keys:
    `changes` (a list of change objects) and `trivial` (a boolean).

---

**Example 1: Simple Feature Commit**

**Diff:**
```diff
diff --git a/src/api/users.py b/src/api/users.py
--- a/src/api/users.py
+++ b/src/api/users.py
@@ -10,3 +10,6 @@
 class User(BaseModel):
     id: int
     name: str
+
+def get_user_by_id(user_id: int) -> User:
+    return USERS.get(user_id)
```

**JSON Response:**
```json
{{{{
  "changes": [
    {{{{
      "summary": "Add new `get_user_by_id` function to retrieve users.",
      "category": "New Feature"
    }}}}
  ],
  "trivial": false
}}}}
```

---

**Example 2: Commit with Multiple Changes**

**Diff:**
```diff
diff --git a/src/utils/calculator.py b/src/utils/calculator.py
--- a/src/utils/calculator.py
+++ b/src/utils/calculator.py
@@ -1,8 +1,8 @@
 def add(x, y):
-    # A simple addition function
+    # A simple, well-documented addition function for two numbers.
     return x + y

 def subtract(a, b):
-    return b - a # This is wrong!
+    # Corrected subtraction logic
+    return a - b
```

**JSON Response:**
```json
{{{{
  "changes": [
    {{{{
      "summary": "Fix incorrect logic in the `subtract` function.",
      "category": "Bug Fix"
    }}}},
    {{{{
      "summary": "Improve code comment for the `add` function.",
      "category": "Documentation"
    }}}}
  ],
  "trivial": false
}}}}
```

---

**Example 3: Trivial Documentation Commit**

**Diff:**
```diff
diff --git a/docs/USAGE.md b/docs/USAGE.md
--- a/docs/USAGE.md
+++ b/docs/USAGE.md
@@ -1 +1,2 @@
 # Usage
-This document explains how to use the tool.
+This document explains how to use the calculator tool.
```

**JSON Response:**
```json
{{{{
  "changes": [
    {{{{
      "summary": "Clarify usage instructions in the documentation.",
      "category": "Documentation"
    }}}}
  ],
  "trivial": true
}}}}
```

---

**Your Task**

Now, analyze the following diff and provide the JSON response.

**Diff:**
```diff
{{diff}}
```
"""
