---
title: Getting Started
description: Quick start guide for Git AI Reporter
---

# Getting Started with Git AI Reporter

Welcome to Git AI Reporter! This guide will help you get up and running in minutes.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.12 or higher** installed ([Download Python](https://www.python.org/downloads/))
- **Git** installed and configured ([Download Git](https://git-scm.com/))
- **A Gemini API key** from Google ([Get API Key](https://aistudio.google.com/app/apikey))
- A Git repository you want to analyze

## Installation

### Install from PyPI (Recommended)

The simplest way to install Git AI Reporter is via pip:

```bash
pip install git-ai-reporter
```

!!! success "Supply Chain Security"
    Our PyPI packages include digital attestations for provenance verification.
    See our [Security Policy](about/security.md) for details.

### Install from Source

For the latest development version or to contribute:

```bash
# Clone the repository
git clone https://github.com/paudley/git-ai-reporter.git
cd git-ai-reporter

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"
```

## Configuration

### Step 1: Set Your API Key

Git AI Reporter requires a Gemini API key to analyze commits:

=== "Linux/macOS"
    ```bash
    export GEMINI_API_KEY="your-api-key-here"
    ```

=== "Windows"
    ```cmd
    set GEMINI_API_KEY=your-api-key-here
    ```

=== "PowerShell"
    ```powershell
    $env:GEMINI_API_KEY="your-api-key-here"
    ```

!!! tip "Permanent Configuration"
    Add the export command to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.) 
    to make it permanent.

### Step 2: Verify Installation

Check that Git AI Reporter is installed correctly:

```bash
$ git-ai-reporter --version
Git AI Reporter v0.1.0
```

## Your First Analysis

### Basic Usage

Navigate to any Git repository and run:

```bash
$ cd /path/to/your/repository
$ git-ai-reporter

Git AI Reporter v0.1.0
Analyzing repository: /path/to/your/repository
Date range: 2025-01-17 to 2025-01-24
Processing 42 commits...

[████████████████████████] 100% Complete

Analysis complete!
Generated files:
   - NEWS.md (development narrative)
   - CHANGELOG.txt (structured changes)
   - DAILY_UPDATES.md (daily summaries)
```

### Analyzing Specific Date Ranges

To analyze commits from a specific time period:

```bash
# Last 7 days (default)
git-ai-reporter

# Last 30 days
git-ai-reporter --days 30

# Specific date range
git-ai-reporter --since 2025-01-01 --until 2025-01-31

# Since a specific date
git-ai-reporter --since 2025-01-15
```

### Output Files

Git AI Reporter generates three complementary documentation files:

#### 📰 NEWS.md
A narrative, stakeholder-friendly summary that tells the story of your development:
- Written in plain English for non-technical audiences
- Highlights major features and improvements
- Provides context and impact of changes

#### 📋 CHANGELOG.txt
A structured, Keep a Changelog compliant list with emoji categorization:
- Organized by version and date
- Categorized (Added, Changed, Fixed, etc.)
- Technical but readable format
- Emoji indicators for quick scanning

#### 📅 DAILY_UPDATES.md
Daily development activity summaries:
- Day-by-day breakdown of progress
- Useful for sprint reviews and standups
- Tracks development velocity

## Common Use Cases

### Sprint Retrospectives
Generate comprehensive sprint summaries:
```bash
# Two-week sprint
git-ai-reporter --days 14
```

### Release Documentation
Create release notes for a new version:
```bash
# Since last release tag
git-ai-reporter --since v1.2.0
```

### Monthly Reports
Generate monthly development reports:
```bash
# Current month
git-ai-reporter --since 2025-01-01 --until 2025-01-31
```

### Team Updates
Create weekly team updates:
```bash
# Weekly update (every Monday)
git-ai-reporter --days 7
```

## Tips for Best Results

### 1. Write Descriptive Commit Messages
The AI analyzes your commit messages and diffs. Clear, descriptive messages lead to better summaries:

```bash
# Good commit messages
feat: Add user authentication with OAuth2
fix: Resolve memory leak in data processor
docs: Update API documentation with examples

# Less helpful messages
fix: Bug fix
update: Changes
wip: Stuff
```

### 2. Use Conventional Commits
Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for best results:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Maintenance tasks

### 3. Manage API Costs
Git AI Reporter uses intelligent caching to minimize API calls:
- Cached results are reused for identical commits
- Clear cache with `--clear-cache` if needed
- Monitor usage in your [Google AI Studio](https://aistudio.google.com/)

### 4. Large Repositories
For repositories with many commits:
- Use date ranges to limit scope
- The tool automatically handles rate limiting
- Progress bars show real-time status

## Troubleshooting

### API Key Issues
```
Error: GEMINI_API_KEY environment variable not set
```
**Solution:** Ensure your API key is set correctly (see Configuration above)

### Git Repository Not Found
```
Error: Current directory is not a git repository
```
**Solution:** Run the command from within a Git repository

### Rate Limiting
```
Warning: Rate limit reached, waiting...
```
**Solution:** The tool automatically handles rate limits with exponential backoff

### Cache Issues
```bash
# Clear the cache if you encounter stale results
git-ai-reporter --clear-cache
```

## Next Steps

- 📖 Read the [User Guide](guide/index.md) for advanced features
- 🎯 Explore [CLI Reference](cli/index.md) for all command options
- 🏗️ Learn about the [Architecture](architecture/index.md)
- 🤝 [Contribute](development/contributing.md) to the project

## Getting Help

- 📋 [GitHub Issues](https://github.com/paudley/git-ai-reporter/issues) - Report bugs or request features
- 💬 [Discussions](https://github.com/paudley/git-ai-reporter/discussions) - Ask questions and share ideas
- 📧 [Email Support](mailto:paudley@blackcat.ca) - Direct support