---
title: Development Setup
description: Setting up your development environment for Git AI Reporter
---

# Development Setup

This guide walks you through setting up a complete development environment for contributing to Git AI Reporter.

## Prerequisites

### Required Software

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.12+ | Core runtime |
| **Git** | 2.0+ | Version control |
| **uv** | Latest | Fast package manager |

### Recommended Tools

| Tool | Purpose |
|------|---------|
| **Make** | Build automation |
| **Docker** | Container testing |
| **VS Code** | IDE with Python support |

## Quick Setup

### 1. Clone the Repository

```bash
git clone https://github.com/paudley/git-ai-reporter.git
cd git-ai-reporter
```

### 2. Create Virtual Environment

```bash
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```bash
# Install package in development mode with all dependencies
uv pip install -e ".[dev,docs]"
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your-api-key-here
```

### 5. Verify Installation

```bash
# Run linting
./scripts/lint.sh

# Run tests
uv run pytest

# Build documentation
uv run mkdocs build --config-file docs/mkdocs.yml
```

## IDE Configuration

### VS Code

Recommended extensions:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "ms-python.mypy-type-checker",
    "littlefoxteam.vscode-python-test-adapter"
  ]
}
```

Settings for `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

1. Open project root directory
2. Configure interpreter: **Settings → Project → Python Interpreter**
3. Select `.venv/bin/python`
4. Enable pytest: **Settings → Tools → Python Integrated Tools**
5. Set test runner to pytest

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the project's coding standards:
- Use type hints for all functions
- Write Google-style docstrings
- Maintain test coverage above 80%

### 3. Run Quality Checks

```bash
# Format and lint code
./scripts/lint.sh

# Run tests
uv run pytest

# Check test coverage
uv run pytest --cov=src --cov-report=html
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: Add your feature description"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Testing
- `refactor:` Code refactoring
- `chore:` Maintenance

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Testing

### Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_specific.py

# With coverage
uv run pytest --cov=src

# Parallel execution
uv run pytest -n auto
```

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── fixtures/       # Test data
└── conftest.py     # Shared fixtures
```

### Writing Tests

```python
import pytest
from git_ai_reporter.models import CommitAnalysis

def test_commit_analysis():
    """Test CommitAnalysis model validation."""
    analysis = CommitAnalysis(
        sha="abc123",
        message="feat: Add new feature",
        changes=[],
        summary="Added new feature"
    )
    assert analysis.sha == "abc123"
```

## Documentation

### Building Docs

```bash
# Serve locally
uv run mkdocs serve --config-file docs/mkdocs.yml

# Build static site
uv run mkdocs build --config-file docs/mkdocs.yml
```

### Writing Docs

- API docs are auto-generated from docstrings
- User guides go in `docs/guide/`
- Architecture docs go in `docs/architecture/`

## Debugging

### Using VS Code Debugger

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug CLI",
      "type": "python",
      "request": "launch",
      "module": "git_ai_reporter.cli",
      "args": ["--repo-path", ".", "--weeks", "1"],
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      }
    }
  ]
}
```

### Using pdb

```python
import pdb; pdb.set_trace()  # Add breakpoint
```

## Troubleshooting

### Common Issues

**Issue**: Import errors
```bash
# Solution: Reinstall in development mode
uv pip install -e .
```

**Issue**: Linting failures
```bash
# Solution: Use the lint script
./scripts/lint.sh
```

**Issue**: Test failures
```bash
# Solution: Update test snapshots
uv run pytest --snapshot-update
```

## Resources

- [Contributing Guide](contributing.md)
- [Coding Guidelines](coding-guidelines.md)
- [Testing Strategy](testing.md)
- [API Documentation](../api/index.md)

## Getting Help

- [GitHub Issues](https://github.com/paudley/git-ai-reporter/issues)
- [Discussions](https://github.com/paudley/git-ai-reporter/discussions)
- [FAQ](../about/faq.md)