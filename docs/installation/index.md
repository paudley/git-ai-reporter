# Installation Guide

Git AI Reporter is designed for easy installation across multiple platforms and environments. Choose the installation method that best fits your workflow.

## Quick Installation

For most users, the PyPI installation is recommended:

```bash
pip install git-ai-reporter
```

## Installation Methods

We support multiple installation methods to accommodate different development workflows:

=== "📦 From PyPI"

    **Recommended for most users**
    
    - Stable, tested releases
    - Automatic dependency management
    - Supply chain security with attestations
    - Regular updates via pip/uv
    
    [**📦 PyPI Installation Guide →**](from-pypi.md)

=== "🔧 From Source"

    **For developers and contributors**
    
    - Latest development features
    - Development environment setup
    - Contributing to the project
    - Custom modifications
    
    [**🔧 Source Installation Guide →**](from-source.md)

=== "🐳 Using Docker"

    **For containerized environments**
    
    - Isolated environment
    - Consistent across platforms
    - CI/CD integration
    - No local Python setup required
    
    [**🐳 Docker Installation Guide →**](docker.md)

## Prerequisites

All installation methods require:

!!! info "System Requirements"

    - **Python:** 3.12 or higher
    - **Git:** Installed and accessible via command line
    - **API Key:** Google Gemini API key (free tier available)
    - **Operating System:** Windows, macOS, or Linux

### Python Version Check

Verify your Python version:

```bash
python --version
# Should output: Python 3.12.x or higher
```

If you need to upgrade Python:

=== "Windows"

    Download from [python.org](https://www.python.org/downloads/) or use:
    
    ```powershell
    winget install Python.Python.3.12
    ```

=== "macOS"

    ```bash
    # Using Homebrew
    brew install python@3.12
    
    # Using pyenv
    pyenv install 3.12.0
    pyenv global 3.12.0
    ```

=== "Linux"

    ```bash
    # Ubuntu/Debian
    sudo apt update
    sudo apt install python3.12 python3.12-pip
    
    # CentOS/RHEL/Fedora
    sudo dnf install python3.12 python3.12-pip
    
    # Using pyenv
    pyenv install 3.12.0
    pyenv global 3.12.0
    ```

### Git Installation Check

Verify Git is installed:

```bash
git --version
# Should output: git version 2.x.x or higher
```

If Git is not installed, visit [git-scm.com](https://git-scm.com/downloads) for installation instructions.

## Getting an API Key

Git AI Reporter requires a Google Gemini API key:

1. **Visit Google AI Studio:** [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

2. **Create API Key:**
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy the generated key

3. **Secure Storage:**
   - Store in environment variable
   - Never commit to version control
   - Use `.env` file for local development

!!! warning "API Key Security"

    Your API key provides access to Google's services. Keep it secure:
    
    - ✅ Store in environment variables
    - ✅ Use `.env` files (add to `.gitignore`)
    - ❌ Never commit to version control
    - ❌ Never share in plain text

## Quick Start After Installation

Once installed, configure your API key and run your first analysis:

1. **Set up API key:**
   ```bash
   # Create .env file in your project directory
   echo 'GEMINI_API_KEY="your-api-key-here"' > .env
   ```

2. **Run first analysis:**
   ```bash
   # Analyze current repository for last 4 weeks
   git-ai-reporter
   
   # Or specify a different repository
   git-ai-reporter --repo-path /path/to/your/repo
   ```

3. **Check output files:**
   ```bash
   ls -la NEWS.md CHANGELOG.txt DAILY_UPDATES.md
   ```

## Verification

Verify your installation works correctly:

```bash
# Check version
git-ai-reporter --version

# Check help
git-ai-reporter --help

# Run with debug mode (safe test)
git-ai-reporter --debug --dry-run
```

Expected output:
```
Git AI Reporter v1.x.x
✅ Python 3.12.x detected
✅ Git repository found
✅ API key configured
✅ All dependencies satisfied
```

## Next Steps

After successful installation:

- **[Configuration Guide →](configuration.md)** - Customize behavior and settings
- **[Quick Start Guide →](../guide/quick-start.md)** - Your first Git AI Reporter analysis
- **[CLI Reference →](../cli/index.md)** - Complete command line documentation

## Troubleshooting

### Common Installation Issues

??? failure "ModuleNotFoundError: No module named 'git_ai_reporter'"

    **Problem:** Python cannot find the installed package.
    
    **Solutions:**
    ```bash
    # Verify installation
    pip list | grep git-ai-reporter
    
    # Reinstall if missing
    pip install --upgrade git-ai-reporter
    
    # Check Python path
    python -c "import sys; print('\n'.join(sys.path))"
    ```

??? failure "Permission denied when installing"

    **Problem:** Insufficient permissions for system-wide installation.
    
    **Solutions:**
    ```bash
    # Use user installation
    pip install --user git-ai-reporter
    
    # Or use virtual environment (recommended)
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install git-ai-reporter
    ```

??? failure "API key errors"

    **Problem:** Authentication or API key issues.
    
    **Solutions:**
    ```bash
    # Verify API key is set
    echo $GEMINI_API_KEY
    
    # Test API key validity
    git-ai-reporter --debug --dry-run
    
    # Check .env file format
    cat .env
    # Should be: GEMINI_API_KEY="your-key-without-quotes"
    ```

??? failure "Git repository not found"

    **Problem:** Git AI Reporter cannot find or access the repository.
    
    **Solutions:**
    ```bash
    # Verify you're in a Git repository
    git status
    
    # Or specify repository path explicitly
    git-ai-reporter --repo-path /full/path/to/repo
    
    # Check repository permissions
    ls -la .git/
    ```

For more troubleshooting help, see our [FAQ](../about/faq.md) or [open an issue](https://github.com/paudley/git-ai-reporter/issues) on GitHub.

## Advanced Installation Topics

- **[Virtual Environments](from-source.md)** - Isolated Python environments
- **[Development Installation](from-source.md)** - Setting up for contributing
- **[Docker Deployment](docker.md)** - Container-based installations
- **[CI/CD Integration](../guide/integration.md)** - Automated analysis in pipelines