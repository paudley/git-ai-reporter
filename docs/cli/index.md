---
title: CLI Reference
description: Complete command-line interface documentation for Git AI Reporter
---

# CLI Reference

Complete reference for the Git AI Reporter command-line interface.

## Synopsis

```bash
git-ai-reporter [OPTIONS]
```

## Description

Git AI Reporter analyzes Git repository history and generates intelligent documentation using AI. It processes commits within a specified date range and produces three types of documentation: NEWS.md (narrative summaries), CHANGELOG.txt (structured changes), and DAILY_UPDATES.md (daily activity).

## Options

### Core Options

#### `--repo PATH`
- **Description**: Path to the Git repository to analyze
- **Default**: Current directory (`.`)
- **Example**: `git-ai-reporter --repo /path/to/project`

#### `--since DATE`
- **Description**: Start date for analysis (inclusive)
- **Format**: `YYYY-MM-DD`
- **Default**: 7 days ago
- **Example**: `git-ai-reporter --since 2025-01-01`

#### `--until DATE`
- **Description**: End date for analysis (inclusive)
- **Format**: `YYYY-MM-DD`
- **Default**: Today
- **Example**: `git-ai-reporter --until 2025-01-31`

#### `--days INTEGER`
- **Description**: Number of days to analyze (backwards from today or --until)
- **Default**: 7
- **Range**: 1-365
- **Example**: `git-ai-reporter --days 30`

### Cache Management

#### `--clear-cache`
- **Description**: Clear the cache before running analysis
- **Default**: False
- **Example**: `git-ai-reporter --clear-cache`
- **Use Case**: Force fresh analysis when cache may be stale

#### `--cache-dir PATH`
- **Description**: Custom cache directory location
- **Default**: `~/.cache/git-ai-reporter`
- **Example**: `git-ai-reporter --cache-dir /tmp/cache`

### Output Control

#### `--output-dir PATH`
- **Description**: Directory for generated documentation files
- **Default**: Repository root
- **Example**: `git-ai-reporter --output-dir docs/generated`

#### `--no-news`
- **Description**: Skip generating NEWS.md
- **Default**: False
- **Example**: `git-ai-reporter --no-news`

#### `--no-changelog`
- **Description**: Skip generating CHANGELOG.txt
- **Default**: False
- **Example**: `git-ai-reporter --no-changelog`

#### `--no-daily`
- **Description**: Skip generating DAILY_UPDATES.md
- **Default**: False
- **Example**: `git-ai-reporter --no-daily`

### Filtering Options

#### `--branch NAME`
- **Description**: Analyze specific branch only
- **Default**: Current branch
- **Example**: `git-ai-reporter --branch main`

#### `--author EMAIL`
- **Description**: Filter commits by author email
- **Default**: All authors
- **Example**: `git-ai-reporter --author "dev@example.com"`

#### `--exclude-merge-commits`
- **Description**: Exclude merge commits from analysis
- **Default**: False
- **Example**: `git-ai-reporter --exclude-merge-commits`

### AI Configuration

#### `--model-tier1 MODEL`
- **Description**: Gemini model for Tier 1 (commit analysis)
- **Default**: `gemini-2.5-flash`
- **Example**: `git-ai-reporter --model-tier1 gemini-2.5-flash`

#### `--model-tier2 MODEL`
- **Description**: Gemini model for Tier 2 (synthesis)
- **Default**: `gemini-2.5-pro`
- **Example**: `git-ai-reporter --model-tier2 gemini-2.5-pro`

#### `--model-tier3 MODEL`
- **Description**: Gemini model for Tier 3 (narration)
- **Default**: `gemini-2.5-pro`
- **Example**: `git-ai-reporter --model-tier3 gemini-2.5-pro`

#### `--max-retries INTEGER`
- **Description**: Maximum API retry attempts
- **Default**: 3
- **Range**: 0-10
- **Example**: `git-ai-reporter --max-retries 5`

### Logging & Debugging

#### `--verbose` / `-v`
- **Description**: Enable verbose output
- **Default**: False
- **Example**: `git-ai-reporter --verbose`
- **Stack**: Use multiple times for more verbosity (`-vv`, `-vvv`)

#### `--quiet` / `-q`
- **Description**: Suppress non-error output
- **Default**: False
- **Example**: `git-ai-reporter --quiet`

#### `--log-file PATH`
- **Description**: Write logs to file
- **Default**: None (console only)
- **Example**: `git-ai-reporter --log-file analysis.log`

#### `--debug`
- **Description**: Enable debug mode with detailed tracing
- **Default**: False
- **Example**: `git-ai-reporter --debug`

### Utility Options

#### `--version`
- **Description**: Show version information and exit
- **Example**: `git-ai-reporter --version`
- **Output**: `Git AI Reporter v0.1.0`

#### `--help`
- **Description**: Show help message and exit
- **Example**: `git-ai-reporter --help`

#### `--config FILE`
- **Description**: Load configuration from file
- **Format**: JSON or YAML
- **Example**: `git-ai-reporter --config settings.json`

## Environment Variables

Git AI Reporter can be configured using environment variables:

### Required

#### `GEMINI_API_KEY`
- **Description**: Google Gemini API key for AI processing
- **Required**: Yes
- **Example**: `export GEMINI_API_KEY="your-key-here"`

### Optional

#### `GIT_AI_CACHE_DIR`
- **Description**: Override default cache directory
- **Default**: `~/.cache/git-ai-reporter`
- **Example**: `export GIT_AI_CACHE_DIR="/tmp/cache"`

#### `GIT_AI_LOG_LEVEL`
- **Description**: Set logging level
- **Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Default**: `INFO`
- **Example**: `export GIT_AI_LOG_LEVEL="DEBUG"`

#### `GIT_AI_OUTPUT_DIR`
- **Description**: Default output directory for generated files
- **Default**: Repository root
- **Example**: `export GIT_AI_OUTPUT_DIR="docs"`

#### `GIT_AI_MAX_WORKERS`
- **Description**: Maximum concurrent workers for async processing
- **Default**: 5
- **Range**: 1-20
- **Example**: `export GIT_AI_MAX_WORKERS="10"`

## Configuration File

You can use a configuration file to set default options:

### JSON Format
```json
{
  "days": 14,
  "output_dir": "docs/generated",
  "model_tier1": "gemini-2.5-flash",
  "model_tier2": "gemini-2.5-pro",
  "model_tier3": "gemini-2.5-pro",
  "verbose": true,
  "exclude_merge_commits": true
}
```

### YAML Format
```yaml
days: 14
output_dir: docs/generated
model_tier1: gemini-2.5-flash
model_tier2: gemini-2.5-pro
model_tier3: gemini-2.5-pro
verbose: true
exclude_merge_commits: true
```

Load with: `git-ai-reporter --config config.yaml`

## Examples

### Basic Usage

```bash
# Analyze last 7 days (default)
$ git-ai-reporter

# Analyze last 30 days
$ git-ai-reporter --days 30

# Analyze specific date range
$ git-ai-reporter --since 2025-01-01 --until 2025-01-31
```

### Advanced Usage

```bash
# Analyze specific branch with verbose output
$ git-ai-reporter --branch feature/new-ui --verbose

# Clear cache and analyze with custom output directory
$ git-ai-reporter --clear-cache --output-dir reports/

# Filter by author and exclude merge commits
$ git-ai-reporter --author "jane@example.com" --exclude-merge-commits

# Use configuration file with overrides
$ git-ai-reporter --config settings.json --days 7
```

### Debugging

```bash
# Enable debug mode with log file
$ git-ai-reporter --debug --log-file debug.log

# Verbose output with specific cache directory
$ git-ai-reporter -vv --cache-dir /tmp/git-ai-cache

# Dry run (analyze but don't write files)
$ git-ai-reporter --dry-run
```

## Exit Codes

Git AI Reporter uses standard exit codes:

- **0**: Success - Analysis completed successfully
- **1**: General error - Unspecified error occurred
- **2**: Usage error - Invalid command-line arguments
- **3**: Git error - Repository not found or Git operation failed
- **4**: API error - Gemini API key missing or API call failed
- **5**: Permission error - Cannot write to output directory
- **6**: Cache error - Cache operations failed
- **7**: Configuration error - Invalid configuration file

## File Output

Git AI Reporter generates three files in the output directory:

### NEWS.md
- **Format**: Markdown with narrative prose
- **Audience**: Stakeholders, non-technical readers
- **Content**: Story-driven development summary
- **Update**: Overwrites existing file

### CHANGELOG.txt
- **Format**: Keep a Changelog compliant
- **Audience**: Developers, technical users
- **Content**: Categorized changes with emoji indicators
- **Update**: Merges with existing [Unreleased] section

### DAILY_UPDATES.md
- **Format**: Markdown with daily sections
- **Audience**: Team members, project managers
- **Content**: Day-by-day activity summary
- **Update**: Appends new days, updates existing

## Performance Considerations

### Cache Usage
- Cache is automatically managed
- Cached results expire after 30 days
- Clear cache if experiencing stale results
- Cache size typically 10-50MB per repository

### API Rate Limits
- Gemini API has rate limits (varies by tier)
- Tool automatically handles rate limiting with exponential backoff
- Use cache to minimize API calls

### Large Repositories
- Repositories with >1000 commits may take longer
- Use date ranges to limit scope
- Progress bar shows real-time status
- Async processing provides 5-10x speedup

## Troubleshooting

### Common Issues

#### No API Key
```
Error: GEMINI_API_KEY environment variable not set
```
Solution: Set your API key with `export GEMINI_API_KEY="your-key"`

#### Git Repository Not Found
```
Error: Not a git repository
```
Solution: Run from within a Git repository or use `--repo` option

#### Permission Denied
```
Error: Permission denied writing to output directory
```
Solution: Check write permissions or use `--output-dir` with writable location

#### Rate Limit Exceeded
```
Warning: Rate limit reached, waiting...
```
Solution: Tool handles automatically, or wait and retry

## See Also

- [User Guide](../guide/index.md) - Comprehensive usage guide
- [Getting Started](../getting-started.md) - Quick start tutorial
- [Architecture](../architecture/index.md) - Technical details
- [API Reference](../api/index.md) - Python API documentation