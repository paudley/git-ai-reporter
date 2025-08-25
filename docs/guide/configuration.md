---
title: Configuration Guide
description: Comprehensive configuration options for Git AI Reporter
---

# Configuration Guide

This guide covers all configuration options for Git AI Reporter, from basic settings to advanced customization.

## Configuration Methods

Git AI Reporter can be configured through multiple methods (in order of precedence):

1. **Command-line arguments** (highest priority)
2. **Configuration file** (TOML format)
3. **Environment variables**
4. **Default values** (lowest priority)

## Environment Variables

### Required Variables

#### `GEMINI_API_KEY`
Your Google Gemini API key for AI processing.

```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Security Note**: Never commit API keys to version control.

### Optional Variables

#### Model Selection

Control which Gemini models are used for each tier:

```bash
export MODEL_TIER_1="gemini-2.5-flash"  # Fast, cheaper for commit analysis
export MODEL_TIER_2="gemini-2.5-pro"    # Higher quality for daily summaries  
export MODEL_TIER_3="gemini-2.5-pro"    # Higher quality for narratives
```

#### Token Limits

Configure token limits for each tier:

```bash
export GEMINI_INPUT_TOKEN_LIMIT_TIER1="30000"
export GEMINI_INPUT_TOKEN_LIMIT_TIER2="30000"  
export GEMINI_INPUT_TOKEN_LIMIT_TIER3="30000"

export MAX_TOKENS_TIER_1="4096"
export MAX_TOKENS_TIER_2="4096"
export MAX_TOKENS_TIER_3="4096"
```

#### API Configuration

```bash
export GEMINI_TIMEOUT="60"              # API timeout in seconds
export GEMINI_MAX_RETRIES="3"           # Maximum retry attempts
export GEMINI_BATCH_SIZE="10"           # Batch size for concurrent requests
```

## Configuration File

### TOML Format

Create a TOML configuration file to set default values:

```toml
# config.toml

# Model configuration
MODEL_TIER_1 = "gemini-2.5-flash"
MODEL_TIER_2 = "gemini-2.5-pro"
MODEL_TIER_3 = "gemini-2.5-pro"

# Token limits
GEMINI_INPUT_TOKEN_LIMIT_TIER1 = 30000
GEMINI_INPUT_TOKEN_LIMIT_TIER2 = 30000
GEMINI_INPUT_TOKEN_LIMIT_TIER3 = 30000

MAX_TOKENS_TIER_1 = 4096
MAX_TOKENS_TIER_2 = 4096
MAX_TOKENS_TIER_3 = 4096

# API settings
GEMINI_TIMEOUT = 60
GEMINI_MAX_RETRIES = 3
GEMINI_BATCH_SIZE = 10
```

Use the configuration file:

```bash
git-ai-reporter --config-file config.toml
```

## Command Line Options

### Basic Options

```bash
# Repository and time range
git-ai-reporter --repo-path /path/to/repo --weeks 4
git-ai-reporter --start-date 2025-01-01 --end-date 2025-01-31

# Cache control
git-ai-reporter --cache-dir /custom/cache --no-cache

# Configuration
git-ai-reporter --config-file custom.toml

# Debug and output
git-ai-reporter --debug --pre-release 1.0.0
```

### Show Current Configuration

Display all current settings:

```bash
git-ai-reporter config --show
```

## Cache Configuration

The caching system can be configured through environment variables or configuration files:

```bash
# Cache directory
export CACHE_DIR="/custom/cache/location"

# The cache stores API responses to reduce costs
# Cache files are automatically managed
```

## Advanced Settings

### Three-Tier Model System

The tool uses a three-tier AI architecture:

1. **Tier 1 (Commit Analysis)**: Fast analysis using `gemini-2.5-flash` by default
2. **Tier 2 (Daily Summaries)**: Quality synthesis using `gemini-2.5-pro` 
3. **Tier 3 (Narratives)**: Final document generation using `gemini-2.5-pro`

### Performance Tuning

```bash
# Batch processing configuration
export GEMINI_BATCH_SIZE="10"           # Number of concurrent API requests
export GEMINI_MAX_RETRIES="3"           # Retry failed requests
export GEMINI_TIMEOUT="60"              # Timeout for API calls
```

## Development Configuration

For development and testing:

```bash
# Enable debug mode for detailed logging
git-ai-reporter --debug

# Use shorter time ranges for faster testing
git-ai-reporter --weeks 1

# Clear cache to test fresh analysis
git-ai-reporter cache --clear
```

## Production Configuration

Recommended settings for production use:

```toml
# production.toml

# Use balanced model selection for cost/quality
MODEL_TIER_1 = "gemini-2.5-flash"      # Fast and cheap for volume
MODEL_TIER_2 = "gemini-2.5-pro"        # Quality for synthesis
MODEL_TIER_3 = "gemini-2.5-pro"        # Quality for narratives

# Conservative token limits
MAX_TOKENS_TIER_1 = 2048
MAX_TOKENS_TIER_2 = 4096
MAX_TOKENS_TIER_3 = 4096

# Robust error handling
GEMINI_MAX_RETRIES = 5
GEMINI_TIMEOUT = 120
GEMINI_BATCH_SIZE = 5
```

## Configuration Validation

The system validates configuration on startup:

- **API Key**: Validates that GEMINI_API_KEY is set
- **Repository**: Checks that the repository path exists and is a valid Git repo
- **Models**: Validates that specified models are available
- **Paths**: Ensures cache and output directories are accessible

## Environment-Specific Settings

### CI/CD Environments

```bash
# CI optimized settings
export GEMINI_BATCH_SIZE="3"            # Lower concurrency in CI
export GEMINI_TIMEOUT="120"             # Longer timeout for CI
export CACHE_DIR="/tmp/git-ai-cache"    # Temporary cache in CI
```

### Local Development

```bash
# Development settings
export CACHE_DIR="$HOME/.cache/git-ai-reporter"  # Persistent local cache
export GEMINI_BATCH_SIZE="10"                    # Higher concurrency locally
```

## Troubleshooting Configuration

### Common Issues

1. **Missing API Key**: Set `GEMINI_API_KEY` environment variable
2. **Permission Errors**: Check cache directory permissions
3. **Network Issues**: Adjust `GEMINI_TIMEOUT` for slow connections
4. **Rate Limiting**: Reduce `GEMINI_BATCH_SIZE` to avoid rate limits

### Debug Configuration

```bash
# Show all configuration values
git-ai-reporter config --show

# Debug mode shows configuration loading
git-ai-reporter --debug
```

## Security Considerations

### API Key Security

1. **Never commit API keys** to version control
2. **Use environment variables** or secure configuration files
3. **Restrict file permissions** on configuration files containing secrets
4. **Use secrets management** in production environments

### Example Secure Setup

```bash
# Set restrictive permissions on config file
chmod 600 .git-ai-reporter.toml

# Use environment variables for secrets
export GEMINI_API_KEY="$(cat /secure/path/to/api-key)"

# Use configuration file for non-sensitive settings
git-ai-reporter --config-file .git-ai-reporter.toml
```

## Next Steps

- Set up [Basic Usage](basic-usage.md) patterns
- Learn [Advanced Features](advanced-usage.md)
- Optimize [Performance](performance.md)
- Review [Troubleshooting](troubleshooting.md)