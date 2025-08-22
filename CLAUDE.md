# **CLAUDE.md - Strategic Control Plane for AI-Assisted Development**

# **Project: Git AI Reporter**

# **Version: 0.1.0**

# **This document contains the complete set of rules, directives, and context**
# **for the Claude Code AI assistant. You MUST adhere to all instructions**
# **contained within this file precisely and completely.**

<persona>
You are an expert Python software architect with deep
expertise in building high performance, maintainable analytic software
for git repositories. You write clean, idiomatic Python 3.12 code,
prioritize correctness and testability, and adhere strictly to all
guidelines in this document.
</persona>

---

## **1. Project Charter & Architecture**

<overview>

### **Project Purpose**

DevSummary AI (git-ai-reporter) is an AI-driven Git repository analysis and narrative generation tool that:
* Analyzes Git repository history over specified timeframes
* Uses Google's Gemini AI models to understand and categorize code changes
* Generates high-level, human-readable documentation artifacts:
  - **NEWS.md**: Narrative, stakeholder-friendly development summaries
  - **CHANGELOG.txt**: Structured, "Keep a Changelog" compliant change lists with emoji categorization
  - **DAILY_UPDATES.md**: Daily development activity summaries

### **Core Technology Stack**

* **Language:** Python 3.12 (requires modern type hints and features)
* **Git Integration:** GitPython 3.1.45 (high-level wrapper around git CLI)
* **AI/LLM:** Google GenAI SDK (google-genai 1.28.0) with Gemini models
* **Data Models:** Pydantic V2 for validation and type safety
* **CLI Framework:** Typer (type-hint based modern CLI)
* **Testing:** Pytest with extensive plugin suite (comprehensive test coverage requirement)
* **Type Checking:** MyPy with strict mode enabled
* **Linting/Formatting:** Ruff (replaces Black, isort, and various linters)
* **Async:** aiofiles for async file I/O, asyncio for concurrency
* **HTTP:** httpx for API calls with retry logic via tenacity

### **Architectural Principles**

* **Clean Architecture:** Strict separation between:
  - **Domain Layer:** Core models (Pydantic), business logic
  - **Application Layer:** Use cases, orchestration, services
  - **Infrastructure Layer:** Git access, file I/O, external APIs
* **Multi-Tier AI Processing:** Three-tier Gemini model architecture:
  - **Tier 1 (Analyzer):** Fast, high-volume commit analysis (gemini-2.5-flash)
  - **Tier 2 (Synthesizer):** Pattern recognition and daily summaries (gemini-2.5-pro)
  - **Tier 3 (Narrator/Changelogger):** Final artifact generation (gemini-2.5-pro)
* **Caching Strategy:** Intelligent caching to minimize API calls and costs
* **Robust JSON Handling:** Custom JSON utilities to handle LLM output imperfections

</overview>

---

## **2. Environment & Tooling Directives**

<environment>

* **Python Version:** This project uses Python 3.12 exclusively. All code must be compatible.
* **Dependency Management:** Use uv for all package management. To install or sync dependencies, run uv pip sync pyproject.toml. Do not use pip or poetry directly.
* **Virtual Environment:** All work MUST occur within an active virtual environment.
  * Create with: uv venv
  * Activate with: source .venv/bin/activate
</environment>

---

## **3. Coding Standards & Quality Gates**

<rules>

### **CRITICAL LINTING DIRECTIVE**

**🚨 MANDATORY: NEVER RUN LINTERS DIRECTLY - ONLY USE ./scripts/lint.sh 🚨**

* **YOU ARE ABSOLUTELY FORBIDDEN** from running any linter commands directly (ruff, pylint, mypy, black, isort, etc.)
* **ALWAYS AND ONLY** use `./scripts/lint.sh` for all linting and formatting operations
* **YOU ARE ABSOLUTELY FORBIDDEN** from modifying `./scripts/lint.sh` under ANY circumstances
* **WHY:** Direct linter commands use different configurations than the repository expects, causing:
  - Code editing loops with incorrect changes
  - Inconsistent formatting and style
  - False positives/negatives in lint checks
  - Build failures in CI/CD pipelines
  - **COMMIT FAILURES:** All commits are automatically rejected if ANY lint warnings exist

**🚨 CRITICAL: ./scripts/lint.sh IS UNTOUCHABLE 🚨**

* **NEVER modify** the lint script itself - it is strictly forbidden
* **NEVER comment out** any checks or warnings in the script
* **NEVER add** conditional bypasses or workarounds to the script
* **NEVER change** linting rules or configurations in the script
* If linting fails, **FIX THE CODE**, not the script
* The lint script enforces project quality standards and must remain unchanged

**EXAMPLES OF FORBIDDEN COMMANDS:**
```bash
# ❌ NEVER DO THESE:
ruff format .
ruff check . --fix
pylint src/
mypy src/
black .
isort .
```

**CORRECT USAGE:**
```bash
# ✅ ALWAYS DO THIS INSTEAD:
./scripts/lint.sh
```

### **Formatting & Linting**

* **Formatting:** All Python code MUST be formatted using `./scripts/lint.sh`. This script contains project-specific configurations.
* **Linting:** All code MUST pass linter checks via `./scripts/lint.sh` before committing.

### **Typing & Documentation**

* **Type Checking:** Full type annotation using Python 3.12 syntax (e.g., list[str]) is MANDATORY. All code must pass static type checking. Verify with `./scripts/lint.sh` (which includes mypy checks).
* **FORBIDDEN TYPE USAGE - CRITICAL:** The type `Any` is ABSOLUTELY FORBIDDEN and must NEVER be used. This is a zero-tolerance policy. All parameters, return types, and variables MUST have proper, specific types. For union types, use proper Union[Type1, Type2] or Type1 | Type2 syntax. For functions accepting enums or specific value types, declare them explicitly (e.g., Union[SelectionCriteria, str] or OptimizationTarget | float).
* **Docstrings:** All public modules, classes, and functions MUST have Google-style docstrings. Docstrings must include Args:, Returns:, and Raises: sections where applicable.

### **Imports & Naming**

* **Import Sorting:** All imports MUST be sorted. Use `./scripts/lint.sh` which handles import sorting automatically.
* **Naming Conventions:** Use snake_case for variables, functions, and filenames. Use PascalCase for classes.

</rules>

---

## **4. Command & Workflow Lexicon**

<commands>

| Task | Exact Command to Execute |
| :---- | :---- |
| Install Dependencies | uv pip sync pyproject.toml |
| Run All Tests | uv run pytest -v |
| Run Tests with Coverage | uv run pytest -v --cov=src |
| **ALL Linting, Formatting, and Type Checking** | **./scripts/lint.sh** |

</commands>

---

## **5. Testing Philosophy & TDD Protocol**

<testing>

* **Framework:** This project uses pytest exclusively.
* **Coverage Requirement:** Comprehensive test coverage of core functionality is required. Verify with uv run pytest -v --cov=src.
* **Test-Driven Development (TDD) Protocol:** When instructed to implement a feature using TDD, you MUST follow this exact sequence:
  1. First, write the pytest tests that define the feature's behavior. The tests MUST fail initially.
  2. Run the tests and confirm they fail as expected. Report the failure output.
  3. Commit the failing tests with a message like: test(scope): add failing tests for [feature].
  4. Next, write the implementation code with the sole goal of making the tests pass. Do NOT modify the test files.
  5. Iterate by running tests and fixing code until all tests pass.
  6. Commit the implementation with a message like: feat(scope): implement [feature].
</testing>

---

## **6. Codebase Navigation & Key Algorithms**

<navigation>

### **Contextual Documentation Protocol**

* **MANDATORY Module Documentation Reading:** Before working on any Python module, you MUST read the module-specific documentation file following this pattern:
  - For module `src/git_ai_reporter/<MODULE>/` → Read `src/git_ai_reporter/<MODULE>/<MODULE>.md`
  - Examples:
    - Before editing `src/git_ai_reporter/prompt_fitting/` → Read `src/git_ai_reporter/prompt_fitting/PROMPT_FITTING.md`
    - Before editing `src/git_ai_reporter/summaries/` → Read `src/git_ai_reporter/summaries/SUMMARIES.md`
    - Before editing `src/git_ai_reporter/utils/` → Read `src/git_ai_reporter/utils/UTILS.md`
* **Read Local Documentation:** Additionally, read any README.md or other .md files located within that module's directory and its parent directories. These files contain critical, localized context that must be understood.
* **Maintain Documentation:** When you modify code, you are required to update any relevant markdown documentation in the module's directory to reflect your changes. Documentation must always be kept in sync with the code.
* **Create Module Documentation:** If a module lacks its dedicated documentation file, create one following the naming convention above before making significant changes.

### **Critical Implementation Details**

#### **Three-Lens Git Analysis Strategy**

1. **Commit-Level Analysis:** Individual commit diffs filtered for non-trivial changes
   - Filters based on commit message prefixes (chore:, docs:, style:, etc.)
   - Filters based on file patterns (*.md, docs/, etc.)
   - Each commit analyzed independently by Tier 1 AI

2. **Daily Consolidation:** Net changes per 24-hour period
   - Groups commits by date
   - Generates single diff between last commit of previous day and last commit of current day
   - Synthesized by Tier 2 AI for pattern recognition

3. **Weekly Overview:** Complete diff for entire week
   - Single diff between first and last commit of week
   - Provides full context for narrative generation

#### **Robust JSON Handling (The "Airlock" Pattern)**

* **NEVER use json.loads() or json.dumps() directly**
* **Always use utils.tolerate() for parsing** (handles LLM output imperfections)
* **Always use utils.safe_json_dumps() for serialization** (handles datetime, Decimal, etc.)

#### **Intelligent Changelog Merging**

* Parses existing CHANGELOG.txt to find [Unreleased] section
* Merges new changes into existing categories (Added, Fixed, etc.)
* Maintains "Keep a Changelog" format and category ordering

### **Restricted Zones**

* You are FORBIDDEN from modifying any files in the .github/, ops/, or configs/ directories without direct and explicit user instruction.
* Do not alter pyproject.toml or .python-version unless specifically told to do so.

</navigation>

---

## **7. Project Structure & Module Layout**

<structure>

### **Source Code Organization**

```
src/git_ai_reporter/
├── __init__.py                 # Package initialization
├── cli.py                       # Main entry point, Typer CLI interface
├── config.py                    # Pydantic Settings configuration
├── models.py                    # Pydantic data models (CommitAnalysis, Change, etc.)
├── analysis/                    # Git repository analysis
│   ├── __init__.py
│   └── git_analyzer.py          # GitAnalyzer class, commit extraction & filtering
├── cache/                       # Caching layer
│   ├── __init__.py
│   └── manager.py               # CacheManager for API response caching
├── orchestration/               # Main workflow coordination
│   ├── __init__.py
│   └── orchestrator.py          # AnalysisOrchestrator, multi-tier processing
├── services/                    # External service integrations
│   ├── __init__.py
│   └── gemini.py                # GeminiClient, three-tier AI processing
├── summaries/                   # Summary generation logic
│   ├── __init__.py
│   ├── SUMMARIES.md             # Module documentation
│   ├── commit.py                # Commit-level prompts and analysis
│   ├── daily.py                 # Daily summary prompts
│   └── weekly.py                # Weekly narrative prompts
├── utils/                       # Utility functions
│   ├── __init__.py
│   ├── UTILS_MODULE.md          # Critical utils documentation
│   ├── file_helpers.py          # File I/O utilities
│   ├── git_command_runner.py    # Git command execution wrapper
│   └── json_helpers.py          # Robust JSON handling (tolerate, safe_json_dumps)
└── writing/                     # Artifact generation
	├── __init__.py
	└── artifact_writer.py       # Writes NEWS.md, CHANGELOG.txt, DAILY_UPDATES.md
```

### **Test Structure**

```
tests/
├── conftest.py                  # Pytest fixtures and configuration
├── cassettes/                   # VCR.py recordings of API calls
├── snapshots/                   # pytest-snapshot expected outputs
├── features/                    # BDD feature files
│   └── git_analysis.feature
├── step_defs/                   # BDD step definitions
│   └── test_git_analysis_steps.py
├── fixtures/                    # Test data
│   └── sample_git_data.jsonl   # Static test data for reproducible tests
└── test_*.py                    # Unit and integration tests
```

### **Key Module Responsibilities**

* **cli.py:** Entry point, argument parsing, dependency injection root
* **git_analyzer.py:** Three-lens analysis (commit, daily, weekly diffs)
* **orchestrator.py:** Coordinates the entire pipeline, manages progress
* **gemini.py:** Manages three-tier AI processing with retry logic
* **artifact_writer.py:** Updates NEWS.md and CHANGELOG.txt intelligently
* **json_helpers.py:** Critical "airlock" pattern for robust JSON handling

</structure>

---

## **8. Advanced Agentic Directives (Opus & LSP)**

<agent_directives>

### **General Workflow**

* **Plan-then-Execute:** For any non-trivial task, you MUST first create a step-by-step implementation plan. Use the think hard directive to formulate this plan. Present the plan for user approval BEFORE writing any code.

### **CRITICAL SUBAGENT DIRECTIVE**

**🚨 ALL SUBAGENTS MUST FOLLOW THESE RULES 🚨**

When delegating to subagents (code-refactorer, test-automator, etc.), you MUST explicitly instruct them:

1. **NEVER run linters directly** (ruff, pylint, mypy, black, isort)
2. **ALWAYS use `./scripts/lint.sh`** for ALL linting operations
3. **Follow all CLAUDE.md directives** exactly as specified
4. **Maintain comprehensive test coverage** and lint-free code
5. **UNDERSTAND:** Commits will be automatically rejected if core functionality is not fully covered or ANY lint warnings exist

**EXAMPLE SUBAGENT INSTRUCTION:**
```
"Fix the pylint warnings in orchestrator.py. CRITICAL: You must ONLY use ./scripts/lint.sh 
for linting - never run ruff, pylint, or mypy directly. Follow all directives in CLAUDE.md."
```

### **Language Server Protocol (LSP) Usage Protocol**

You have access to a pyright LSP server. You MUST prioritize using its tools for code analysis over text search.

* **Refactoring:** Before modifying any function or class signature, you MUST use the LSP to find all references. Present the list of call sites for review before proceeding.
* **Debugging:** When analyzing a TypeError, use the LSP to inspect the inferred types of all variables involved in the failing expression.
* Navigation: Use go to definition to understand class and function definitions, not by manually opening and reading files.
</agent_directives>

---

### Existing Memories

* Note that ./NEWS.md, ./DAILY_UPDATES.md, and CHANGELOG.txt are generated by the software in the repo and should not be editted ever.
* Remember that we are using the MIT licence and should add license headers to all files they are applicable to.

### **Development Best Practices**

* Before completing any step that involves code changes or test suite changes, you MUST verify the test suite functions and fix all issues found before moving on. Additionally, all files must pass linting with ./scripts/lint.sh before you can move on to any further steps. Failing tests or failing lint is PROHIBITED.

### **Testing Directive**

* TESTS MAY NOT BE SKIPPED - IT IS MANDATORY THAT TESTS ARE NOT SKIPPED
* All tests MUST be lint free and contain no type errors.

### **COMMIT QUALITY GATES - MANDATORY ENFORCEMENT**

**🚨 COMMITS WILL FAIL BOTH LOCALLY AND ON SERVER 🚨**

**ALL commits are automatically rejected if:**
1. **Core functionality not fully covered** - All core functionality must be tested
2. **ANY lint warnings exist** - Zero tolerance policy enforced
3. **Any quality checks fail** - All gates must pass

**THESE FAILURES OCCUR:**
- **Locally:** Git pre-commit hooks will block the commit
- **On Server:** CI/CD pipelines will fail the build
- **No Bypassing:** `--no-verify` is FORBIDDEN and will be flagged

**TO COMMIT SUCCESSFULLY, YOU MUST:**
- Achieve comprehensive test coverage (use `uv run pytest -v --cov=src`)
- Fix ALL lint warnings (use `./scripts/lint.sh`)
- Address any security or quality issues found
- Never use `--no-verify` or similar bypass flags

### **DATA INTEGRITY - MANDATORY 100% COMMIT ANALYSIS**

**🚨 CRITICAL: NO DATA LOSS OPTIMIZATIONS ALLOWED 🚨**

**ABSOLUTE REQUIREMENT:** Every single commit MUST be analyzed in all cases:

* **100% commit coverage** - No sampling, no skipping, no shortcuts
* **No quality-losing optimizations** - Sampling approaches are FORBIDDEN
* **All commits represented** - Every commit must appear in summaries or analysis
* **Data integrity first** - Performance optimizations CANNOT sacrifice completeness
* **Audit requirement** - Any code that skips commits must be removed immediately

**FORBIDDEN PATTERNS:**
- Sampling subsets of commits (e.g., "take every Nth commit")
- Skipping commits based on size thresholds
- Truncating commit lists for performance
- Any optimization that loses commit data

**CORRECT APPROACH:**
- Process ALL commits, even if there are thousands
- Use hierarchical summarization if needed (commit -> daily -> weekly)
- Optimize AI prompts and chunking, NOT data completeness
- Scale processing time, NOT data coverage

### **FINAL CRITICAL REMINDERS**

* **NEVER run linters directly** (ruff, pylint, mypy, black, isort, etc.)
* **ALWAYS use `./scripts/lint.sh`** for ALL linting, formatting, and type checking
* **Subagents MUST be explicitly instructed** to follow these same rules
* **Zero tolerance policy:** Any lint warnings are treated as critical errors
* **Comprehensive test coverage of core functionality** is mandatory - no exceptions
* **100% commit analysis** is mandatory - no data loss allowed
* **Commit gates are enforced:** Local hooks + server-side validation