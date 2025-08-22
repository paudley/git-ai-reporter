# Contributing to Git AI Reporter

First off, thank you for considering contributing to Git AI Reporter! It's people like you that make Git AI Reporter such a great tool.

## Code of Conduct

This project follows standard open source collaboration practices. Please be respectful and constructive in all interactions. Please report any unacceptable behavior to [paudley@blackcat.ca](mailto:paudley@blackcat.ca).

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check [existing issues](https://github.com/paudley/git-ai-reporter/issues) as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps to reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed and what you expected**
* **Include logs and error messages**
* **Include your environment details** (OS, Python version, git-ai-reporter version)

### Suggesting Enhancements

Enhancement suggestions are tracked as [GitHub issues](https://github.com/paudley/git-ai-reporter/issues). When creating an enhancement suggestion:

* **Use a clear and descriptive title**
* **Provide a detailed description of the suggested enhancement**
* **Provide specific examples to demonstrate the use case**
* **Describe the current behavior and explain the expected behavior**
* **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repo and create your branch from `main`
2. Follow the setup instructions in the README
3. Make your changes following our coding standards
4. Add or update tests as needed
5. Ensure the test suite passes
6. Update documentation as needed
7. Submit your pull request!

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Git
- [uv](https://github.com/astral-sh/uv) package manager

### Setting Up Your Development Environment

```bash
# Clone your fork
git clone https://github.com/paudley/git-ai-reporter.git
cd git-ai-reporter

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with all dependencies
uv pip install -e .[dev]

# Copy and configure environment file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

## Coding Standards

### Python Style Guide

We use strict coding standards to maintain high code quality:

- **Formatting**: All code MUST be formatted with `ruff format`
- **Linting**: All code MUST pass `ruff check`
- **Type Checking**: All code MUST pass `mypy --strict`
- **Line Length**: 88 characters (Black/Ruff default)
- **Docstrings**: Google-style docstrings for all public APIs

### Running Quality Checks

```bash
# Format code
ruff format .

# Check linting
ruff check . --fix

# Type checking
mypy src/

# Run all tests
pytest

# Run tests with coverage
pytest --cov=src/git_reporter --cov-report=html
```

### Pre-commit Hooks

We recommend using pre-commit hooks:

```bash
# Install pre-commit
uv pip install pre-commit

# Install the git hook scripts
pre-commit install

# Run against all files
pre-commit run --all-files
```

## Testing

### Test Requirements

- **Coverage**: New code must maintain or improve the current comprehensive test coverage
- **Test Types**: Include unit tests, integration tests, and snapshot tests
- **Deterministic**: Tests must be deterministic and not depend on external services

### Writing Tests

```python
# Example test structure
def test_feature_with_clear_name():
    """Test that feature X produces expected output Y."""
    # Arrange
    input_data = create_test_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

### Updating Test Fixtures

When updating cassettes or snapshots:

```bash
# Re-record API mocks
rm tests/cassettes/test_name.yaml
pytest tests/test_file.py::test_name

# Update snapshots
pytest --snapshot-update
```

## Documentation

- Update the README.md if you change functionality
- Update inline documentation and docstrings
- Add entries to PENDING.md for future enhancements
- Follow Google-style docstrings:

```python
def function(param1: str, param2: int) -> bool:
    """Brief description of function.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When invalid input provided.
    """
```

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code change that neither fixes a bug nor adds a feature
- `perf:` Performance improvement
- `test:` Adding or updating tests
- `chore:` Changes to build process or auxiliary tools

Examples:
```
feat: add support for GitLab repositories
fix: handle empty commit messages gracefully
docs: update installation instructions for Windows
test: add integration tests for weekly summaries
```

## Release Process

1. Update version in `pyproject.toml` and `src/git_reporter/__init__.py`
2. Update CHANGELOG.txt (this is auto-generated, do not edit manually)
3. Create a git tag: `git tag -a v0.1.0 -m "Release version 0.1.0"`
4. Push the tag: `git push origin v0.1.0`
5. GitHub Actions will automatically publish to PyPI

## Questions?

Feel free to open an issue with the "question" label or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License (SPDX: MIT).

All source code files should include the SPDX license identifier at the top:
```python
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.
```

## Acknowledgments

Thank you to all contributors who help make Git AI Reporter better!
