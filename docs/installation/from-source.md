# Installing from Source

Source installation is ideal for developers, contributors, and users who want access to the latest features before they're released. This guide covers development environment setup and contributing workflows.

## When to Install from Source

Choose source installation if you:

- ✨ Want the latest unreleased features
- 🐛 Need to test bug fixes before release
- 🔧 Plan to contribute to the project
- 📚 Want to study the implementation
- 🎯 Need custom modifications for your environment

## Prerequisites

### Required Software

Ensure you have the following installed:

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.12+ | Runtime environment |
| **Git** | 2.0+ | Version control and repository access |
| **uv** | Latest | Fast Python package manager (recommended) |

### Optional Tools (Development)

For full development environment:

| Tool | Purpose |
|------|---------|
| **Make** | Build automation |
| **Docker** | Containerized testing |
| **Node.js** | Documentation building |

## Quick Source Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/paudley/git-ai-reporter.git
cd git-ai-reporter

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in development mode
uv pip install -e .
```

### Using pip

```bash
# Clone and navigate
git clone https://github.com/paudley/git-ai-reporter.git
cd git-ai-reporter

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in editable mode
pip install -e .
```

## Development Environment Setup

### Full Development Installation

For contributing to the project:

=== "Using uv (Fast)"

    ```bash
    # Clone repository
    git clone https://github.com/paudley/git-ai-reporter.git
    cd git-ai-reporter
    
    # Setup development environment
    uv venv
    source .venv/bin/activate
    
    # Install with all development dependencies
    uv pip install -e .[dev]
    
    # Install pre-commit hooks
    pre-commit install
    ```

=== "Using pip"

    ```bash
    # Clone repository
    git clone https://github.com/paudley/git-ai-reporter.git
    cd git-ai-reporter
    
    # Create environment
    python -m venv .venv
    source .venv/bin/activate
    
    # Install development dependencies
    pip install -e .[dev]
    
    # Setup pre-commit hooks
    pre-commit install
    ```

### Development Dependencies

The `[dev]` extra includes:

```toml title="pyproject.toml excerpt"
[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-recording>=0.13.0",
    "pytest-snapshot>=0.9.0",
    "hypothesis>=6.90.0",
    
    # Code Quality
    "ruff>=0.3.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
    
    # Documentation
    "mkdocs-material>=9.5.0",
    "mkdocstrings[python]>=0.24.0",
    
    # Development Tools
    "rich>=13.7.0",
    "ipython>=8.20.0",
    "jupyter>=1.0.0"
]
```

## Project Structure Overview

Understanding the codebase layout:

```
git-ai-reporter/
├── src/
│   └── git_ai_reporter/           # Main package
│       ├── analysis/              # Git repository analysis
│       ├── cache/                 # Intelligent caching
│       ├── orchestration/         # Workflow coordination  
│       ├── services/              # External APIs (Gemini)
│       ├── summaries/             # AI prompt logic
│       ├── utils/                 # Common utilities
│       └── writing/               # Output generation
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   ├── bdd/                       # BDD scenarios
│   ├── cassettes/                 # VCR API recordings
│   └── fixtures/                  # Test data
├── docs/                          # Documentation
└── scripts/                       # Development scripts
```

## Development Workflow

### Code Quality Checks

Git AI Reporter enforces strict code quality standards:

#### Linting and Formatting

!!! warning "Critical: Use Project Lint Script"

    **Always use `./scripts/lint.sh`** - never run linters directly:
    
    ```bash
    # ✅ Correct - use the project script
    ./scripts/lint.sh
    
    # ❌ Wrong - will cause issues
    ruff check .
    ruff format .
    mypy src/
    ```

The lint script ensures consistent configuration and prevents commit failures.

#### Pre-commit Hooks

Automatic quality checks on commit:

```bash
# Install hooks (one-time setup)
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Skip hooks if needed (discouraged)
git commit --no-verify
```

### Testing

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/git_ai_reporter

# Run specific test categories
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/bdd/              # BDD scenarios

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_git_analyzer.py::TestGitAnalyzer::test_commit_filtering
```

#### Test Categories

| Category | Purpose | Speed |
|----------|---------|-------|
| **Unit** | Individual component testing | ⚡ Fast |
| **Integration** | Multi-component workflows | 🐌 Slower |
| **BDD** | User scenario validation | 🐌 Slower |
| **Property** | Edge case discovery | 🔄 Variable |

#### VCR Testing for API Calls

Git AI Reporter uses VCR.py for deterministic API testing:

```bash
# Record new API interactions
pytest --record-mode=once tests/integration/

# Replay existing recordings (default)
pytest tests/integration/

# Update existing recordings
rm tests/cassettes/test_gemini_client.yaml
pytest tests/integration/test_gemini_client.py
```

### Allure Test Reporting

Visual test reporting for comprehensive analysis:

```bash
# Generate Allure results
pytest --alluredir=allure-results

# View reports locally (requires Docker)
docker compose up -d
./scripts/send_to_allure.sh
./scripts/view_allure.sh

# Open browser to http://localhost:5252
```

### Documentation Development

#### Local Documentation Server

```bash
# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build

# Deploy to GitHub Pages (maintainers only)
mkdocs gh-deploy
```

#### API Documentation

Auto-generated from docstrings using mkdocstrings:

```python
def analyze_commit(commit: Commit) -> CommitAnalysis | None:
    """Analyzes a single commit for changes.
    
    Args:
        commit: The Git commit to analyze
        
    Returns:
        Analysis result or None if trivial
        
    Raises:
        GitAnalyzerError: If commit cannot be analyzed
    """
```

## Environment Configuration

### API Keys for Development

Create a `.env` file in the project root:

```bash
# Copy example configuration
cp .env.example .env

# Edit with your API key
cat > .env << EOF
# Google Gemini API Configuration
GEMINI_API_KEY="your-development-api-key"

# Development Settings
DEBUG=true
CACHE_ENABLED=false

# Model Configuration (optional)
MODEL_TIER_1="gemini-2.5-flash"
MODEL_TIER_2="gemini-2.5-pro"
MODEL_TIER_3="gemini-2.5-pro"
EOF
```

### Development vs Production Settings

| Setting | Development | Production |
|---------|-------------|------------|
| `DEBUG` | `true` | `false` |
| `CACHE_ENABLED` | `false` | `true` |
| `LOG_LEVEL` | `DEBUG` | `INFO` |
| `API_TIMEOUT` | `600` | `300` |

## Building and Packaging

### Local Package Building

```bash
# Install build dependencies
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*

# Test local installation
pip install dist/git_ai_reporter-*.whl
```

### Development Installation Verification

```bash
# Verify development installation
git-ai-reporter --version
git-ai-reporter --help

# Run development test
git-ai-reporter --debug --dry-run

# Test with sample repository
git-ai-reporter --repo-path . --weeks 1 --debug
```

## Contributing Workflow

### Setting Up Contributions

1. **Fork the repository** on GitHub
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/git-ai-reporter.git
   cd git-ai-reporter
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/paudley/git-ai-reporter.git
   ```

4. **Install development environment:**
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e .[dev]
   pre-commit install
   ```

### Development Branch Management

```bash
# Create feature branch
git checkout -b feature/awesome-improvement

# Keep up to date with upstream
git fetch upstream
git rebase upstream/main

# Run quality checks before committing
./scripts/lint.sh
pytest

# Commit with conventional format
git commit -m "feat: add awesome improvement"

# Push to your fork
git push origin feature/awesome-improvement
```

### Commit Message Standards

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New features
- `fix`: Bug fixes  
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `ci`: CI/CD changes

**Examples:**
```
feat(analysis): add commit categorization by file patterns
fix(cache): resolve race condition in concurrent access
docs(api): update GitAnalyzer docstring examples
test(integration): add VCR recordings for Gemini API
```

## Troubleshooting Source Installation

### Common Development Issues

??? failure "Import errors after installation"

    **Problem:** Python cannot find the installed package.
    
    **Solutions:**
    ```bash
    # Verify development installation
    pip show -f git-ai-reporter
    
    # Reinstall in development mode
    pip install -e .
    
    # Check Python path
    python -c "import git_ai_reporter; print(git_ai_reporter.__file__)"
    ```

??? failure "Pre-commit hooks failing"

    **Problem:** Code quality checks prevent commits.
    
    **Solutions:**
    ```bash
    # Run linting to fix issues
    ./scripts/lint.sh
    
    # Check specific hook issues
    pre-commit run --all-files
    
    # Update hook versions
    pre-commit autoupdate
    ```

??? failure "Test failures with API calls"

    **Problem:** Tests fail due to API connectivity or rate limits.
    
    **Solutions:**
    ```bash
    # Use recorded API responses
    pytest --record-mode=none
    
    # Check VCR cassettes exist
    ls tests/cassettes/
    
    # Re-record if API changed
    rm tests/cassettes/problematic_test.yaml
    pytest tests/path/to/test.py --record-mode=once
    ```

??? failure "Documentation build errors"

    **Problem:** MkDocs fails to build documentation.
    
    **Solutions:**
    ```bash
    # Install documentation dependencies
    pip install -e .[docs]
    
    # Check for syntax errors
    mkdocs build --strict
    
    # Serve with live reload for debugging
    mkdocs serve --dev-addr=127.0.0.1:8000
    ```

### Performance Issues

??? warning "Slow test execution"

    **Optimizations:**
    ```bash
    # Run tests in parallel
    pytest -n auto
    
    # Skip slow integration tests
    pytest -m "not integration"
    
    # Use test categories
    pytest tests/unit/  # Fastest tests only
    ```

### IDE Configuration

#### VS Code

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "ruff",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/allure-results": true
    }
}
```

#### PyCharm

1. **Set Python Interpreter:** File → Settings → Project → Python Interpreter
2. **Configure Pytest:** Run → Edit Configurations → Add pytest configuration
3. **Enable Ruff:** File → Settings → Tools → External Tools → Add Ruff

## Advanced Development Topics

### Custom Model Configuration

For testing with different AI models:

```python title="Local configuration override"
# Create local_config.py (gitignored)
from git_ai_reporter.config import Settings

class DevSettings(Settings):
    MODEL_TIER_1: str = "gemini-1.5-flash"  # Faster for development
    MODEL_TIER_2: str = "gemini-1.5-pro"   # Different model testing
    TEMPERATURE: float = 0.1                # More deterministic
    DEBUG: bool = True
```

### Plugin Development

Git AI Reporter supports plugin architecture:

```python title="example_plugin.py"
from git_ai_reporter.writing.artifact_writer import ArtifactWriter
from git_ai_reporter.models import AnalysisResult

class CustomFormatWriter(ArtifactWriter):
    """Example custom output format plugin."""
    
    def write_artifact(self, analysis: AnalysisResult, output_path: str) -> None:
        # Custom format implementation
        pass
```

## Next Steps

After setting up your development environment:

1. **[Coding Guidelines →](../development/coding-guidelines.md)** - Project standards and practices
2. **[Testing Strategy →](../development/testing.md)** - Understanding the test suite
3. **[Contributing Guide →](../development/contributing.md)** - How to contribute effectively
4. **[Architecture Overview →](../architecture/overview.md)** - Understanding the system design

## Getting Help

- **[GitHub Discussions](https://github.com/paudley/git-ai-reporter/discussions)** - Ask questions and share ideas
- **[GitHub Issues](https://github.com/paudley/git-ai-reporter/issues)** - Report bugs or request features  
- **[Development Documentation](../development/index.md)** - Comprehensive development guides