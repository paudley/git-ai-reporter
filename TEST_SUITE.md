# Git AI Reporter Test Suite Design

## Executive Summary

This document outlines a comprehensive test strategy for the Git AI Reporter project, designed to achieve comprehensive core functionality coverage while ensuring robustness, maintainability, and best practices compliance. The test suite leverages modern Python testing frameworks and methodologies including BDD, property-based testing, and snapshot testing.

## Core Testing Principles

### 1. Test Organization Structure

```
tests/
├── conftest.py                      # Global fixtures and pytest configuration
├── unit/                            # Unit tests (isolated, fast, mocked)
│   ├── __init__.py
│   ├── conftest.py                  # Unit-specific fixtures
│   ├── analysis/
│   │   └── test_git_analyzer.py     # GitAnalyzer unit tests
│   ├── cache/
│   │   └── test_cache_manager.py    # CacheManager unit tests
│   ├── models/
│   │   └── test_models.py           # Pydantic model validation tests
│   ├── services/
│   │   └── test_gemini_client.py    # GeminiClient unit tests (mocked)
│   ├── summaries/
│   │   ├── test_commit_summary.py   # Commit summary prompt tests
│   │   ├── test_daily_summary.py    # Daily summary prompt tests
│   │   └── test_weekly_summary.py   # Weekly summary prompt tests
│   ├── utils/
│   │   ├── test_file_helpers.py     # File I/O utility tests
│   │   ├── test_git_command.py      # Git command runner tests
│   │   └── test_json_helpers.py     # JSON handling tests
│   └── writing/
│       └── test_artifact_writer.py  # Artifact writer unit tests
├── integration/                      # Integration tests (real subsystems)
│   ├── __init__.py
│   ├── conftest.py                  # Integration-specific fixtures
│   ├── test_cli.py                  # CLI integration tests
│   ├── test_orchestrator.py         # Full pipeline tests (mocked Gemini)
│   ├── test_git_integration.py      # Real git repo operations
│   └── test_cache_persistence.py    # Cache file I/O tests
├── e2e/                             # End-to-end tests (real API calls)
│   ├── __init__.py
│   ├── conftest.py                  # E2E-specific fixtures
│   ├── test_full_pipeline.py        # Complete workflow with real Gemini
│   └── test_real_repository.py      # Tests against actual git repos
├── bdd/                             # Behavior-driven development tests
│   ├── __init__.py
│   ├── features/
│   │   ├── git_analysis.feature     # Git analysis scenarios
│   │   ├── summary_generation.feature # Summary generation scenarios
│   │   └── changelog_merge.feature  # Changelog merging scenarios
│   └── step_defs/
│       ├── test_git_steps.py        # Git-related step definitions
│       ├── test_summary_steps.py    # Summary generation steps
│       └── test_changelog_steps.py  # Changelog-related steps
├── property/                        # Property-based tests with Hypothesis
│   ├── __init__.py
│   ├── test_json_robustness.py     # Fuzz testing JSON handling
│   ├── test_model_invariants.py    # Model validation properties
│   └── test_diff_processing.py     # Diff parsing edge cases
├── performance/                     # Performance and stress tests
│   ├── __init__.py
│   ├── test_large_repos.py         # Tests with large repositories
│   └── test_concurrent_processing.py # Concurrency stress tests
├── fixtures/                        # Shared test data
│   ├── sample_commits.json         # Sample commit data
│   ├── sample_diffs.txt            # Sample git diffs
│   ├── malformed_json/             # Malformed JSON samples
│   │   ├── extra_commas.json
│   │   ├── missing_quotes.json
│   │   └── nested_errors.json
│   └── snapshots/                  # pytest-snapshot reference outputs
│       ├── news_output.md
│       ├── changelog_output.txt
│       └── daily_updates.md
├── cassettes/                       # VCR.py recordings for API calls
│   ├── gemini_analyze_commit.yaml
│   ├── gemini_synthesize_daily.yaml
│   └── gemini_generate_weekly.yaml
└── extracts/
    └── sample_git_data.jsonl       # Real-world repository data

```

## 2. Testing Strategy by Module

### 2.1 Core Models (`models.py`)

**Unit Tests:**
- Pydantic validation for all models (CommitAnalysis, Change, WeeklySummary, etc.)
- Test required vs optional fields
- Test field constraints (min/max length, regex patterns)
- Test serialization/deserialization
- Edge cases: empty strings, None values, extreme lengths

**Property Tests (Hypothesis):**
```python
@given(st.text(min_size=1, max_size=1000))
def test_commit_message_always_strips_whitespace(message):
    # Property: commit messages are always stripped
    pass

@given(st.lists(st.text(), min_size=0, max_size=100))
def test_change_deduplication(changes):
    # Property: duplicate changes are always removed
    pass
```

### 2.2 Git Analysis (`git_analyzer.py`)

**Unit Tests:**
- Mock GitPython objects for controlled testing
- Test commit filtering logic (chore:, docs:, style: exclusions)
- Test file pattern filtering (*.md, docs/, etc.)
- Test three-lens analysis:
  - Commit-level: individual commit processing
  - Daily: grouping and consolidation
  - Weekly: full diff generation
- Edge cases:
  - Empty repository
  - Single commit repository
  - Repository with only filtered commits
  - Commits at exact midnight boundaries
  - Merge commits and branch scenarios

**Integration Tests:**
- Use sample_git_data.jsonl for reproducible scenarios
- Test actual git command execution
- Verify diff generation accuracy

**Property Tests:**
```python
@given(st.lists(commit_strategy(), min_size=0, max_size=1000))
def test_daily_grouping_preserves_all_commits(commits):
    # Property: no commits lost during daily grouping
    pass
```

### 2.3 Gemini Service (`gemini.py`)

**Unit Tests:**
- Mock google.genai API responses
- Test retry logic with tenacity
- Test prompt construction for all three tiers
- Test token counting and truncation
- Test error handling:
  - API rate limits
  - Network failures
  - Invalid API keys
  - Malformed responses

**Integration Tests (with VCR):**
- Record actual Gemini API calls
- Test response parsing
- Verify JSON extraction from markdown

**Property Tests:**
```python
@given(st.text(min_size=10000, max_size=100000))
def test_prompt_truncation_preserves_structure(large_diff):
    # Property: truncated prompts remain valid
    pass
```

### 2.4 JSON Handling (`json_helpers.py`)

**Unit Tests:**
- Test tolerate() with various malformed JSON
- Test safe_json_dumps() with datetime, Decimal, custom objects
- Test error recovery strategies

**Property Tests:**
```python
@given(json_strategy())
def test_tolerate_never_raises(possibly_malformed_json):
    # Property: tolerate() never raises exceptions
    result = tolerate(possibly_malformed_json)
    assert result is not None
```

**Edge Cases:**
- Extra commas
- Missing quotes
- Trailing commas
- Mixed quote styles
- Unicode handling
- Nested errors
- Truncated JSON

### 2.5 Orchestrator (`orchestrator.py`)

**Integration Tests:**
- Test full pipeline with mocked Gemini
- Test progress tracking
- Test cache integration
- Test error recovery
- Test partial failure scenarios

**E2E Tests:**
- Complete workflow with real Gemini API
- Verify artifact generation
- Test idempotency

### 2.6 CLI (`cli.py`)

**Unit Tests:**
- Mock Typer context
- Test argument parsing
- Test validation logic

**Integration Tests:**
- Test CLI invocation with subprocess
- Test all command combinations
- Test error messages
- Test progress display

**BDD Tests:**
```gherkin
Feature: Git Repository Analysis
  Scenario: Analyze repository for past week
    Given a git repository with commits from the past 7 days
    When I run git-ai-reporter with default settings
    Then NEWS.md should be created with weekly summary
    And CHANGELOG.txt should be updated with new entries
    And DAILY_UPDATES.md should contain daily summaries
```

### 2.7 Artifact Writer (`artifact_writer.py`)

**Unit Tests:**
- Test NEWS.md generation
- Test CHANGELOG.txt merging logic
- Test Keep a Changelog format compliance
- Test emoji categorization

**Property Tests:**
```python
@given(changelog_entries())
def test_changelog_merge_preserves_existing(entries):
    # Property: existing entries never lost during merge
    pass
```

## 3. Testing Infrastructure

### 3.1 Fixtures (conftest.py)

```python
# Global fixtures
@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    pass

@pytest.fixture
def sample_commits():
    """Load sample commit data from fixtures."""
    pass

@pytest.fixture
def mock_gemini_client(mocker):
    """Mocked GeminiClient with controlled responses."""
    pass

@pytest.fixture
def vcr_config():
    """VCR configuration for recording API calls."""
    return {
        'filter_headers': ['authorization'],
        'record_mode': 'once',
        'match_on': ['uri', 'method', 'body']
    }
```

### 3.2 pytest-check Usage

```python
import pytest_check as check

def test_multiple_assertions():
    """Use soft assertions for comprehensive validation."""
    result = analyze_commits(commits)
    
    check.equal(len(result), 10, "Should have 10 results")
    check.is_true(result[0].is_valid, "First result should be valid")
    check.is_in("feat", result[0].type, "Should be a feature")
    # All checks run even if one fails
```

### 3.3 Hypothesis Strategies

```python
# Custom strategies for domain objects
@st.composite
def commit_strategy(draw):
    return {
        'hash': draw(st.text(min_size=40, max_size=40, 
                            alphabet='0123456789abcdef')),
        'message': draw(st.text(min_size=1, max_size=200)),
        'author': draw(st.text(min_size=1, max_size=50)),
        'date': draw(st.datetimes()),
        'files': draw(st.lists(st.text(), min_size=0, max_size=20))
    }

@st.composite
def malformed_json_strategy(draw):
    # Generate subtly broken JSON for testing tolerance
    pass
```

### 3.4 Parallel and Random Execution

```python
# pytest.ini configuration
[tool.pytest.ini_options]
addopts = """
    --random-order
    --random-order-bucket=module
    --random-order-seed=12345  # For reproducibility during debugging
    -n auto  # Parallel execution
    --dist loadscope  # Group by module for efficiency
    --timeout=15
    --timeout-method=thread
"""
```

## 4. Coverage Strategy

### 4.1 Coverage Requirements

- **Target:** 100% core functionality coverage
- **Branch Coverage:** 100% for critical paths
- **Exception Coverage:** All error paths tested

### 4.2 Coverage Configuration

```ini
[tool.coverage.run]
source = ["src/git_reporter"]
branch = true
parallel = true
omit = [
    "*/tests/*",
    "*/__init__.py",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
fail_under = 100  # For core functionality
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

### 4.3 Coverage Verification

```bash
# Run with coverage
uv run pytest --cov=src/git_reporter --cov-report=term-missing  # Target 100% core functionality

# Generate HTML report for analysis
uv run pytest --cov=src/git_reporter --cov-report=html

# Check branch coverage
uv run pytest --cov=src/git_reporter --cov-branch
```

## 5. Test Execution Strategy

### 5.1 Test Markers

```python
# Custom markers for selective execution
@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.requires_api_key
@pytest.mark.hypothesis
```

### 5.2 Execution Profiles

```bash
# Fast unit tests only (for rapid feedback)
uv run pytest -m "not slow and not integration" --timeout=5

# Integration tests (with mocked external services)
uv run pytest -m integration --timeout=30

# Full suite with real API calls
uv run pytest --timeout=60

# Property tests with more examples
uv run pytest -m hypothesis --hypothesis-show-statistics
```

## 6. Continuous Integration

### 6.1 GitHub Actions Workflow

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        python: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
      - name: Run lint check
        run: ./scripts/lint.sh
      - name: Run tests
        run: uv run pytest
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 7. Special Testing Considerations

### 7.1 Snapshot Testing

- Use pytest-snapshot for output validation
- Store expected outputs in fixtures/snapshots/
- Update snapshots with: `pytest --snapshot-update`

### 7.2 VCR Recording Management

```python
@pytest.mark.vcr
def test_gemini_api_call():
    """Test with recorded API response."""
    pass

# Re-record cassettes when API changes
# pytest --record-mode=rewrite
```

### 7.3 Error Path Testing

Every function must have tests for:
- Happy path
- Invalid input
- Empty input
- Null/None handling
- Exception propagation
- Resource cleanup (context managers)

### 7.4 Async Testing

```python
@pytest.mark.asyncio
async def test_async_file_operations():
    """Test aiofiles operations."""
    async with aiofiles.open('test.txt', 'w') as f:
        await f.write('test')
```

## 8. Test Quality Metrics

### 8.1 Mutation Testing

```bash
# Use mutmut for mutation testing
mutmut run --paths-to-mutate=src/git_reporter
mutmut results
```

### 8.2 Complexity Analysis

- McCabe complexity < 10 for all functions
- Test complexity should be lower than code complexity
- Use pytest-testmon for test impact analysis

## 9. Test Data Management

### 9.1 Using sample_git_data.jsonl

```python
@pytest.fixture
def real_world_commits():
    """Load real repository data for integration tests."""
    with open('tests/extracts/sample_git_data.jsonl') as f:
        return [json.loads(line) for line in f]
```

### 9.2 Test Data Generation

```python
# Generate diverse test scenarios
def generate_test_repository(tmp_path, scenario='standard'):
    """Create git repo with specific characteristics."""
    scenarios = {
        'empty': [],
        'single_commit': [create_commit('Initial')],
        'feature_branch': create_branch_scenario(),
        'merge_conflicts': create_merge_scenario(),
        'large_history': create_commits(1000),
    }
```

## 10. Lint-Free Test Code

All test code must pass `./scripts/lint.sh`:
- Black formatting (line length 130)
- Ruff linting
- isort import sorting
- Flake8 style checking
- MyPy type checking
- Pylint with all extensions

## 11. Performance Benchmarks

```python
@pytest.mark.benchmark
def test_large_repo_performance(benchmark):
    """Ensure performance doesn't degrade."""
    result = benchmark(analyze_large_repository)
    assert benchmark.stats['mean'] < 5.0  # seconds
```

## 12. Security Testing

- Test for injection attacks in git commands
- Verify no secrets in logs or cache
- Test API key handling
- Validate file path sanitization

## Implementation Priority

1. **Phase 1: Core Unit Tests**
   - Models, JSON helpers, utils
   - 100% coverage of core utility functions

2. **Phase 2: Integration Tests**
   - Git analyzer with sample data
   - Orchestrator with mocked Gemini

3. **Phase 3: Property Tests**
   - JSON robustness
   - Model invariants

4. **Phase 4: BDD Scenarios**
   - User-facing workflows
   - Error scenarios

5. **Phase 5: E2E with Real API**
   - Snapshot testing
   - Performance benchmarks

This comprehensive test suite ensures the Git AI Reporter project is robust, maintainable, and production-ready while achieving 100% core functionality coverage and following Python testing best practices.