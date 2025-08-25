---
title: Development Guide
description: Contributing guidelines and development setup for Git AI Reporter
---

# Development Guide

Welcome to the Git AI Reporter development guide. This section covers everything you need to contribute to the project.

## Quick Links

<div class="grid cards">
  <div class="card">
    <h3>🤝 Contributing</h3>
    <p>Guidelines for contributing to the project</p>
    <a href="contributing/" class="md-button">Contribute →</a>
  </div>
  
  <div class="card">
    <h3>📝 Coding Guidelines</h3>
    <p>Code style and best practices</p>
    <a href="coding-guidelines/" class="md-button">Guidelines →</a>
  </div>
  
  <div class="card">
    <h3>🧪 Testing</h3>
    <p>Test suite and testing practices</p>
    <a href="testing/" class="md-button">Testing →</a>
  </div>
  
  <div class="card">
    <h3>📦 Releasing</h3>
    <p>Release process and versioning</p>
    <a href="releasing/" class="md-button">Releases →</a>
  </div>
</div>

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Git
- uv (recommended) or pip
- A Gemini API key for testing

### Environment Setup

1. **Clone the repository**:
```bash
git clone https://github.com/paudley/git-ai-reporter.git
cd git-ai-reporter
```

2. **Create virtual environment**:
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate

# Or using standard Python
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

3. **Install dependencies**:
```bash
# Install all development dependencies
uv pip sync pyproject.toml
# or
pip install -e ".[dev]"
```

4. **Set up pre-commit hooks**:
```bash
pre-commit install
```

5. **Configure environment**:
```bash
# Create .env file
cp .env.example .env

# Edit .env and add your Gemini API key
echo 'GEMINI_API_KEY="your-api-key"' >> .env
```

## Project Structure

```
git-ai-reporter/
├── src/git_ai_reporter/     # Source code
│   ├── __init__.py
│   ├── cli.py               # CLI entry point
│   ├── config.py            # Configuration
│   ├── models.py            # Data models
│   ├── analysis/            # Git analysis
│   ├── cache/               # Caching
│   ├── orchestration/       # Workflow
│   ├── services/            # External services
│   ├── summaries/           # AI prompts
│   ├── utils/               # Utilities
│   └── writing/             # Output generation
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── fixtures/           # Test data
│   └── conftest.py         # Pytest configuration
├── docs/                    # Documentation
├── scripts/                 # Development scripts
│   └── lint.sh             # Linting script
├── .github/                 # GitHub configuration
│   └── workflows/          # CI/CD workflows
├── pyproject.toml          # Project configuration
└── README.md               # Project overview
```

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
Follow our [coding guidelines](coding-guidelines.md) and ensure:
- Code is properly typed (Python 3.12 syntax)
- All functions have docstrings
- Tests are written for new functionality

### 3. Run Linting
```bash
# MANDATORY: Use the project lint script
./scripts/lint.sh

# This runs:
# - ruff format (formatting)
# - ruff check (linting)
# - mypy (type checking)
# - pylint (additional checks)
```

!!! warning "Critical Requirement"
    NEVER run linters directly. Always use `./scripts/lint.sh`.
    All code must be lint-free before committing.

### 4. Run Tests
```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest -v --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_analyzer.py -v

# Run with markers
uv run pytest -m "not slow" -v
```

### 5. Update Documentation
- Update relevant documentation
- Add docstrings to new functions
- Update CHANGELOG.txt if applicable

### 6. Commit Changes
```bash
# Use conventional commits
git commit -m "feat: Add new analysis feature"
git commit -m "fix: Resolve caching issue"
git commit -m "docs: Update API documentation"
```

### 7. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Testing

### Test Organization

```
tests/
├── unit/                    # Unit tests
│   ├── analysis/           # Git analysis tests
│   ├── services/           # Service tests
│   └── utils/              # Utility tests
├── integration/            # Integration tests
│   ├── test_pipeline.py    # Full pipeline tests
│   └── test_cli.py         # CLI tests
├── fixtures/               # Test data
│   ├── sample_repo/        # Sample Git repository
│   └── responses/          # Sample API responses
└── conftest.py             # Shared fixtures
```

### Writing Tests

Example unit test:
```python
import pytest
from git_ai_reporter.analysis import GitAnalyzer

class TestGitAnalyzer:
    def test_commit_filtering(self, sample_repo):
        analyzer = GitAnalyzer(sample_repo)
        commits = analyzer.get_commit_diffs(
            since=datetime(2025, 1, 1),
            until=datetime(2025, 1, 31)
        )
        assert len(commits) > 0
        assert all(c.sha for c in commits)
```

### Test Coverage

We maintain high test coverage:
- Core functionality: >90%
- Overall coverage: >80%
- All new code must include tests

## Code Style

### Python Style Guide

We follow PEP 8 with these specifications:
- Line length: 88 characters (Black default)
- Quotes: Double quotes for strings
- Imports: Sorted with isort
- Type hints: Required for all public functions

### Type Hints

Use Python 3.12+ syntax:
```python
# Good
def process_commits(commits: list[Commit]) -> dict[str, Any]:
    ...

# Bad (old style)
from typing import List, Dict, Any
def process_commits(commits: List[Commit]) -> Dict[str, Any]:
    ...
```

### Docstrings

Use Google-style docstrings:
```python
def analyze_repository(
    repo_path: str,
    start_date: datetime,
    end_date: datetime
) -> AnalysisResult:
    """Analyze a Git repository over a date range.
    
    Args:
        repo_path: Path to the Git repository.
        start_date: Start date for analysis.
        end_date: End date for analysis.
    
    Returns:
        AnalysisResult containing the analysis data.
    
    Raises:
        GitRepositoryError: If repo_path is not a valid Git repository.
        ValueError: If date range is invalid.
    """
```

## Dependencies

### Adding Dependencies

1. Add to `pyproject.toml`:
```toml
[project]
dependencies = [
    "new-package>=1.0.0",
]
```

2. Update lock file:
```bash
uv pip sync pyproject.toml
```

3. Document why the dependency is needed

### Dependency Groups

- **Core**: Required for basic functionality
- **Dev**: Development and testing tools
- **Docs**: Documentation generation
- **Optional**: Enhanced features

## CI/CD Pipeline

### GitHub Actions Workflows

- **CI** (`ci.yml`): Runs on every push
  - Linting and formatting checks
  - Type checking
  - Unit tests
  - Integration tests
  - Coverage reporting

- **Release** (`release.yml`): Runs on tags
  - Build package
  - Generate attestations
  - Publish to PyPI
  - Create GitHub release

- **Docs** (`docs.yml`): Documentation deployment
  - Build MkDocs site
  - Deploy to GitHub Pages

### Pre-commit Hooks

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
```

## Debugging

### Debug Mode

Run with debug logging:
```bash
GIT_AI_LOG_LEVEL=DEBUG git-ai-reporter --debug
```

### Using pdb

```python
import pdb; pdb.set_trace()  # Breakpoint
```

### VS Code Configuration

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug CLI",
      "type": "python",
      "request": "launch",
      "module": "git_ai_reporter.cli",
      "args": ["--days", "7"],
      "env": {
        "GEMINI_API_KEY": "your-key"
      }
    }
  ]
}
```

## Performance Profiling

### Using cProfile

```bash
python -m cProfile -o profile.stats -m git_ai_reporter
```

### Analyzing Results

```python
import pstats
stats = pstats.Stats('profile.stats')
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## Documentation

### Building Docs

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Serve locally
mkdocs serve

# Build static site
mkdocs build
```

### Writing Documentation

- Use Markdown with Material for MkDocs extensions
- Include code examples with syntax highlighting
- Add diagrams using Mermaid
- Keep navigation structure consistent

## Release Process

See [Releasing Guide](releasing.md) for detailed instructions.

### Quick Release

```bash
# Update version in pyproject.toml
# Update CHANGELOG.txt

# Create and push tag
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# GitHub Actions handles the rest
```

## Getting Help

### Resources

- [GitHub Issues](https://github.com/paudley/git-ai-reporter/issues)
- [Discussions](https://github.com/paudley/git-ai-reporter/discussions)
- [Contributing Guide](contributing.md)

### Maintainers

- Patrick Audley ([@paudley](https://github.com/paudley))

## License

This project is licensed under the MIT License. See [LICENSE](../about/license.md) for details.