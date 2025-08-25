---
title: Basic Usage
description: Common usage patterns and examples
---

# Basic Usage

This guide covers the most common usage patterns for Git AI Reporter.

## Basic Commands

### Default Analysis

Analyze the last 4 weeks of repository history:

```bash
# Run in your repository directory
git-ai-reporter

# Or specify the repository path
git-ai-reporter --repo-path /path/to/repo
```

### Custom Time Ranges

#### Using Weeks

Analyze a different number of weeks:

```bash
# Last week only
git-ai-reporter --weeks 1

# Last 8 weeks
git-ai-reporter --weeks 8

# Maximum: 52 weeks
git-ai-reporter --weeks 52
```

#### Using Specific Dates

Analyze a specific date range:

```bash
# Specific date range
git-ai-reporter --start-date 2025-01-01 --end-date 2025-01-31

# From a date to now
git-ai-reporter --start-date 2025-01-01

# Both --start-date and --end-date override --weeks
```

## Output Files

Git AI Reporter generates three files:

### NEWS.md
- **Purpose**: Human-readable narrative summary
- **Audience**: Stakeholders, team members, non-technical readers
- **Format**: Markdown with sections for each week
- **Location**: Repository root

### CHANGELOG.txt
- **Purpose**: Structured change log following "Keep a Changelog" format
- **Audience**: Developers, technical users
- **Format**: Plain text with categorized changes
- **Location**: Repository root

### DAILY_UPDATES.md
- **Purpose**: Day-by-day development activity
- **Audience**: Project managers, team leads
- **Format**: Markdown with daily sections
- **Location**: Repository root

## Cache Management

### Using Cache

The tool automatically caches API responses to reduce costs:

```bash
# Default cache location: .git-report-cache
git-ai-reporter

# Custom cache location
git-ai-reporter --cache-dir ~/.cache/git-ai

# Bypass cache (force re-analysis)
git-ai-reporter --no-cache
```

### Managing Cache

```bash
# Show cache statistics
git-ai-reporter cache --show

# Clear all cached data
git-ai-reporter cache --clear
```

## Debug Mode

Enable verbose output for troubleshooting:

```bash
# Enable debug logging
git-ai-reporter --debug

# Debug mode shows:
# - Detailed progress information
# - API call details
# - Processing steps
# - Error traces
```

## Configuration

### Using Configuration Files

Load settings from a TOML configuration file:

```bash
# Use custom configuration
git-ai-reporter --config-file config.toml
```

### Environment Variables

Set environment variables for configuration:

```bash
# Required: Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Optional: Model selection
export MODEL_TIER_1="gemini-2.5-flash"
export MODEL_TIER_2="gemini-2.5-pro"
export MODEL_TIER_3="gemini-2.5-pro"

# Run with environment configuration
git-ai-reporter
```

### Show Current Configuration

Display the current settings:

```bash
# Show all configuration values
git-ai-reporter config --show
```

## Pre-Release Documentation

Generate documentation for a specific version:

```bash
# Generate release notes for version 1.2.3
git-ai-reporter --pre-release 1.2.3

# This formats the output as if the release has already happened
```

## Common Workflows

### Daily Updates

Generate daily development summaries:

```bash
# Analyze yesterday's work
git-ai-reporter --weeks 1
```

### Weekly Reports

Generate weekly team updates:

```bash
# Standard weekly report
git-ai-reporter --weeks 1
```

### Monthly Summaries

Generate monthly progress reports:

```bash
# Last 4 weeks (approximately 1 month)
git-ai-reporter --weeks 4
```

### Release Preparation

Generate documentation for a release:

```bash
# Analyze since last release
LAST_TAG=$(git describe --tags --abbrev=0)
LAST_DATE=$(git log -1 --format=%ai $LAST_TAG | cut -d' ' -f1)
git-ai-reporter --start-date $LAST_DATE

# Or generate pre-release documentation
git-ai-reporter --pre-release 2.0.0
```

## Best Practices

### Performance

1. **Use caching**: Don't use `--no-cache` unless necessary
2. **Reasonable time ranges**: Start with shorter periods for large repos
3. **Debug judiciously**: Only use `--debug` when troubleshooting

### Repository Setup

1. **Full history**: Ensure your clone has full history (`git clone` without `--depth`)
2. **Clean working directory**: Commit or stash changes before analysis
3. **API key security**: Never commit your GEMINI_API_KEY

### CI/CD Integration

1. **Cache between runs**: Preserve cache directory in CI
2. **Use secrets**: Store API key as encrypted secret
3. **Scheduled runs**: Set up weekly or daily generation

## Troubleshooting

### Common Issues

**No output generated:**
- Check that GEMINI_API_KEY is set
- Verify the repository has commits in the specified range
- Use `--debug` to see detailed errors

**Analysis is slow:**
- Use cache (avoid `--no-cache`)
- Reduce the time range with `--weeks 1`
- Check network connectivity to Google APIs

**Cache issues:**
- Clear cache with `git-ai-reporter cache --clear`
- Check disk space for cache directory
- Verify cache directory permissions

## Examples

### Quick Examples

```bash
# Analyze current directory for last week
git-ai-reporter --weeks 1

# Analyze specific repo for last month
git-ai-reporter --repo-path ~/projects/myapp --weeks 4

# Debug mode with custom cache
git-ai-reporter --debug --cache-dir /tmp/cache

# Generate release documentation
git-ai-reporter --pre-release 1.0.0 --start-date 2025-01-01
```

## Next Steps

- Learn about [Advanced Features](advanced-usage.md)
- Set up [Configuration](configuration.md)
- Optimize [Performance](performance.md)
- Review [Troubleshooting](troubleshooting.md)