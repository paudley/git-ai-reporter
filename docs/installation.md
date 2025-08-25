---
title: Installation Guide
description: Comprehensive installation instructions for Git AI Reporter
---

# Installation Guide

This guide provides detailed installation instructions for Git AI Reporter across different platforms and environments.

## System Requirements

### Minimum Requirements
- **Python:** 3.12 or higher
- **Memory:** 4GB RAM (8GB recommended for large repositories)
- **Disk Space:** 500MB for installation + cache storage
- **Network:** Internet connection for AI API calls
- **Git:** Version 2.0 or higher

### Supported Platforms
- ✅ **Linux** (Ubuntu 20.04+, Debian 10+, RHEL 8+, Fedora 34+)
- ✅ **macOS** (11.0 Big Sur or later)
- ✅ **Windows** (10/11 with WSL2 or native Python)
- ✅ **Docker** (Any platform with Docker support)

## Installation Methods

### Method 1: PyPI (Recommended)

The simplest and most reliable installation method:

```bash
# Install the latest stable version
pip install git-ai-reporter

# Install a specific version
pip install git-ai-reporter==0.1.0

# Upgrade to the latest version
pip install --upgrade git-ai-reporter
```

!!! info "Virtual Environment Recommended"
    We strongly recommend using a virtual environment to avoid dependency conflicts:
    ```bash
    python -m venv git-reporter-env
    source git-reporter-env/bin/activate  # Linux/macOS
    # or
    git-reporter-env\Scripts\activate  # Windows
    pip install git-ai-reporter
    ```

### Method 2: uv (Fast Modern Installer)

Using [uv](https://github.com/astral-sh/uv) for faster installation:

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install git-ai-reporter
uv pip install git-ai-reporter

# Or in a new virtual environment
uv venv
source .venv/bin/activate
uv pip install git-ai-reporter
```

### Method 3: pipx (Isolated Installation)

For isolated global installation:

```bash
# Install pipx if not already installed
python -m pip install --user pipx
python -m pipx ensurepath

# Install git-ai-reporter
pipx install git-ai-reporter

# Upgrade
pipx upgrade git-ai-reporter
```

### Method 4: From Source

For development or latest features:

```bash
# Clone the repository
git clone https://github.com/paudley/git-ai-reporter.git
cd git-ai-reporter

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .

# Or with all development dependencies
pip install -e ".[dev]"
```

### Method 5: Docker

Using the pre-built Docker image:

```bash
# Pull the latest image
docker pull ghcr.io/paudley/git-ai-reporter:latest

# Run in current directory
docker run -it --rm \
  -v $(pwd):/repo \
  -e GEMINI_API_KEY=$GEMINI_API_KEY \
  ghcr.io/paudley/git-ai-reporter

# Or build your own image
git clone https://github.com/paudley/git-ai-reporter.git
cd git-ai-reporter
docker build -t git-ai-reporter .
```

## Platform-Specific Instructions

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python 3.12 if not present
sudo apt install python3.12 python3.12-venv python3-pip

# Install git if not present
sudo apt install git

# Install git-ai-reporter
python3.12 -m pip install git-ai-reporter
```

### macOS

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12
brew install python@3.12

# Install git if not present
brew install git

# Install git-ai-reporter
python3.12 -m pip install git-ai-reporter
```

### Windows

#### Option 1: Native Python

1. Download Python 3.12+ from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Open Command Prompt or PowerShell:

```powershell
# Verify Python installation
python --version

# Install git-ai-reporter
pip install git-ai-reporter
```

#### Option 2: WSL2 (Recommended)

1. Install WSL2 following [Microsoft's guide](https://docs.microsoft.com/en-us/windows/wsl/install)
2. Install Ubuntu from Microsoft Store
3. Follow the Ubuntu/Debian instructions above

### RHEL/CentOS/Fedora

```bash
# Install Python 3.12
sudo dnf install python3.12 python3.12-devel

# Install git if not present
sudo dnf install git

# Install git-ai-reporter
python3.12 -m pip install git-ai-reporter
```

## Dependency Management

### Core Dependencies

Git AI Reporter requires these core packages (automatically installed):

- `gitpython>=3.1.45` - Git repository interaction
- `google-genai>=1.28.0` - Gemini AI integration
- `pydantic>=2.10.0` - Data validation
- `typer>=0.15.0` - CLI framework
- `rich>=13.9.0` - Terminal formatting
- `python-dotenv>=1.0.0` - Environment management
- `aiofiles>=24.1.0` - Async file operations
- `httpx>=0.28.0` - HTTP client
- `tenacity>=9.0.0` - Retry logic

### Optional Dependencies

For enhanced functionality:

```bash
# Development tools
pip install git-ai-reporter[dev]

# Documentation generation
pip install git-ai-reporter[docs]

# All extras
pip install git-ai-reporter[all]
```

## Configuration

### API Key Setup

Git AI Reporter requires a Gemini API key:

1. **Get an API Key:**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Click "Get API Key"
   - Copy your key

2. **Set the Environment Variable:**

=== "Linux/macOS"
    ```bash
    # Temporary (current session)
    export GEMINI_API_KEY="your-api-key-here"
    
    # Permanent (add to ~/.bashrc or ~/.zshrc)
    echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
    source ~/.bashrc
    ```

=== "Windows (CMD)"
    ```cmd
    # Temporary
    set GEMINI_API_KEY=your-api-key-here
    
    # Permanent
    setx GEMINI_API_KEY "your-api-key-here"
    ```

=== "Windows (PowerShell)"
    ```powershell
    # Temporary
    $env:GEMINI_API_KEY="your-api-key-here"
    
    # Permanent
    [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-api-key-here", "User")
    ```

### Using .env File

Create a `.env` file in your project directory:

```bash
# .env
GEMINI_API_KEY=your-api-key-here

# Optional configuration
GIT_AI_CACHE_DIR=/custom/cache/path
GIT_AI_LOG_LEVEL=INFO
```

!!! warning "Security Note"
    Never commit `.env` files to version control. Add `.env` to your `.gitignore`.

## Verification

### Check Installation

Verify the installation was successful:

```bash
$ git-ai-reporter --version
Git AI Reporter v0.1.0

$ git-ai-reporter --help
Usage: git-ai-reporter [OPTIONS]

  Git AI Reporter - Transform git history into intelligent documentation.

Options:
  --repo PATH         Repository path [default: .]
  --since DATE        Start date (YYYY-MM-DD)
  --until DATE        End date (YYYY-MM-DD)
  --days INTEGER      Number of days to analyze
  --clear-cache       Clear the cache before running
  --version           Show version
  --help              Show this message and exit
```

### Test Run

Test with a sample repository:

```bash
# Clone a sample repository
git clone https://github.com/paudley/git-ai-reporter.git /tmp/test-repo
cd /tmp/test-repo

# Run analysis on last 7 days
git-ai-reporter --days 7

# Check generated files
ls -la NEWS.md CHANGELOG.txt DAILY_UPDATES.md
```

## Upgrading

### From PyPI

```bash
# Check current version
git-ai-reporter --version

# Upgrade to latest
pip install --upgrade git-ai-reporter

# Verify upgrade
git-ai-reporter --version
```

### From Source

```bash
cd /path/to/git-ai-reporter
git pull origin main
pip install --upgrade -e .
```

## Uninstallation

### Remove Package

```bash
# If installed with pip
pip uninstall git-ai-reporter

# If installed with pipx
pipx uninstall git-ai-reporter

# Clean up cache (optional)
rm -rf ~/.cache/git-ai-reporter
```

## Troubleshooting

### Common Issues

#### Python Version Error
```
Error: Python 3.12+ required
```
**Solution:** Install Python 3.12 or higher

#### Missing Git
```
Error: Git command not found
```
**Solution:** Install Git for your platform

#### Permission Denied
```
Error: Permission denied: '/usr/local/lib/python3.12/...'
```
**Solution:** Use `--user` flag or virtual environment:
```bash
pip install --user git-ai-reporter
# or
python -m venv venv && source venv/bin/activate
pip install git-ai-reporter
```

#### SSL Certificate Error
```
Error: SSL: CERTIFICATE_VERIFY_FAILED
```
**Solution:** Update certificates:
```bash
# macOS
brew install ca-certificates

# Linux
sudo apt-get install ca-certificates

# Or disable SSL (not recommended)
export PYTHONHTTPSVERIFY=0
```

### Getting Help

If you encounter issues:

1. Check the [FAQ](guide/faq.md)
2. Search [existing issues](https://github.com/paudley/git-ai-reporter/issues)
3. Join our [discussions](https://github.com/paudley/git-ai-reporter/discussions)
4. Report a [new issue](https://github.com/paudley/git-ai-reporter/issues/new)

## Next Steps

- 🚀 Follow the [Getting Started](getting-started.md) guide
- 📖 Read the [User Guide](guide/index.md)
- 🎯 Explore [CLI Options](cli/index.md)
- 🏗️ Understand the [Architecture](architecture/index.md)