# CLI Options Reference

Complete reference for all Git AI Reporter command-line options, parameters, and flags. This guide covers every available option with examples and use cases.

## Command Syntax

```bash
git-ai-reporter [OPTIONS] [COMMAND]
```

## Global Options

### Repository and Path Options

#### `--repo-path PATH`
**Type:** Path  
**Default:** Current directory  
**Description:** Specify the Git repository to analyze

```bash
# Analyze a different repository
git-ai-reporter --repo-path /path/to/project

# Analyze remote repository (must be cloned locally)
git clone https://github.com/user/repo.git temp-repo
git-ai-reporter --repo-path ./temp-repo

# Use absolute paths
git-ai-reporter --repo-path /home/user/projects/my-app
```

#### `--output-dir PATH`
**Type:** Path  
**Default:** Repository root directory  
**Description:** Directory where output files will be written

```bash
# Write outputs to a specific directory
git-ai-reporter --output-dir ./reports

# Create timestamped report directory
git-ai-reporter --output-dir "./reports/$(date +%Y-%m-%d)"

# Use absolute path
git-ai-reporter --output-dir /var/log/git-ai-reporter
```

### Date Range Options

#### `--weeks INTEGER`
**Type:** Integer (1-52)  
**Default:** 4  
**Description:** Number of weeks to analyze from the current date

```bash
# Analyze last 2 weeks
git-ai-reporter --weeks 2

# Analyze last 6 months (approximately)
git-ai-reporter --weeks 24

# Single week analysis
git-ai-reporter --weeks 1
```

#### `--start-date DATE`
**Type:** Date (YYYY-MM-DD format)  
**Default:** Calculated from `--weeks`  
**Description:** Start date for analysis period

```bash
# Specific start date
git-ai-reporter --start-date "2025-01-01"

# Combine with end date for precise range
git-ai-reporter --start-date "2025-01-01" --end-date "2025-01-31"

# ISO 8601 format also supported
git-ai-reporter --start-date "2025-01-01T00:00:00"
```

#### `--end-date DATE`
**Type:** Date (YYYY-MM-DD format)  
**Default:** Current date  
**Description:** End date for analysis period

```bash
# Specific end date
git-ai-reporter --end-date "2025-01-31"

# Analyze up to a specific point in time
git-ai-reporter --start-date "2024-12-01" --end-date "2024-12-31"
```

#### `--since-tag TAG`
**Type:** String  
**Default:** None  
**Description:** Analyze commits since the specified Git tag

```bash
# Analyze since last release
git-ai-reporter --since-tag v1.2.0

# Analyze since last stable version
git-ai-reporter --since-tag stable

# Combined with other options
git-ai-reporter --since-tag v1.0.0 --end-date "2025-01-31"
```

### Output Control Options

#### `--news-file PATH`
**Type:** Path  
**Default:** `NEWS.md`  
**Description:** Custom path for the news/narrative output file

```bash
# Custom filename
git-ai-reporter --news-file RELEASE_NOTES.md

# Custom directory and filename
git-ai-reporter --news-file docs/releases/NEWS.md

# Disable news file generation
git-ai-reporter --news-file ""
```

#### `--changelog-file PATH`
**Type:** Path  
**Default:** `CHANGELOG.txt`  
**Description:** Custom path for the technical changelog file

```bash
# Custom filename
git-ai-reporter --changelog-file CHANGES.md

# Follow conventional changelog naming
git-ai-reporter --changelog-file CHANGELOG.md

# Use reStructuredText format
git-ai-reporter --changelog-file CHANGELOG.rst
```

#### `--daily-updates-file PATH`
**Type:** Path  
**Default:** `DAILY_UPDATES.md`  
**Description:** Custom path for the daily development log

```bash
# Custom filename
git-ai-reporter --daily-updates-file development-log.md

# Project management directory
git-ai-reporter --daily-updates-file project-management/daily-log.md

# Disable daily updates
git-ai-reporter --daily-updates-file ""
```

### AI Model Configuration

#### `--model-tier-1 MODEL`
**Type:** String  
**Default:** `gemini-2.5-flash`  
**Description:** AI model for Tier 1 (commit analysis)

```bash
# Use different model for commit analysis
git-ai-reporter --model-tier-1 "gemini-2.5-pro"

# Performance optimization
git-ai-reporter --model-tier-1 "gemini-2.5-flash"
```

#### `--model-tier-2 MODEL`
**Type:** String  
**Default:** `gemini-2.5-pro`  
**Description:** AI model for Tier 2 (synthesis)

```bash
# Quality optimization
git-ai-reporter --model-tier-2 "gemini-2.5-pro"

# Speed optimization
git-ai-reporter --model-tier-2 "gemini-2.5-flash"
```

#### `--model-tier-3 MODEL`
**Type:** String  
**Default:** `gemini-2.5-pro`  
**Description:** AI model for Tier 3 (final narratives)

```bash
# Maximum quality for final output
git-ai-reporter --model-tier-3 "gemini-2.5-pro"

# Consistent model across all tiers
git-ai-reporter \
  --model-tier-1 "gemini-2.5-pro" \
  --model-tier-2 "gemini-2.5-pro" \
  --model-tier-3 "gemini-2.5-pro"
```

#### `--temperature FLOAT`
**Type:** Float (0.0-1.0)  
**Default:** 0.5  
**Description:** AI creativity/randomness parameter

```bash
# More deterministic output
git-ai-reporter --temperature 0.2

# More creative output
git-ai-reporter --temperature 0.8

# Balanced (default)
git-ai-reporter --temperature 0.5
```

#### `--max-tokens INTEGER`
**Type:** Integer  
**Default:** Model-specific  
**Description:** Maximum tokens for AI responses

```bash
# Longer, more detailed responses
git-ai-reporter --max-tokens 32768

# Shorter, more concise responses
git-ai-reporter --max-tokens 4096

# Tier-specific token limits
git-ai-reporter \
  --max-tokens-tier-1 8192 \
  --max-tokens-tier-2 16384 \
  --max-tokens-tier-3 32768
```

### Filtering and Processing Options

#### `--trivial-types TYPES`
**Type:** Comma-separated list  
**Default:** `style,chore`  
**Description:** Commit types to exclude from analysis

```bash
# More aggressive filtering
git-ai-reporter --trivial-types "style,chore,docs,test"

# Less filtering (track more changes)
git-ai-reporter --trivial-types "style"

# No filtering (analyze everything)
git-ai-reporter --trivial-types ""
```

#### `--include-trivial`
**Type:** Boolean flag  
**Default:** False  
**Description:** Include trivial commits in analysis

```bash
# Include all commits regardless of type
git-ai-reporter --include-trivial

# Combined with specific types
git-ai-reporter --include-trivial --trivial-types "style"
```

#### `--author AUTHOR`
**Type:** String  
**Default:** All authors  
**Description:** Filter commits by specific author

```bash
# Single author
git-ai-reporter --author "jane.doe@example.com"

# Author name (partial match)
git-ai-reporter --author "Jane Doe"

# Multiple authors (requires multiple runs)
git-ai-reporter --author "jane.doe@example.com"
git-ai-reporter --author "john.smith@example.com"
```

### Performance and Caching Options

#### `--cache / --no-cache`
**Type:** Boolean flag  
**Default:** `--cache`  
**Description:** Enable or disable caching

```bash
# Force fresh analysis (no cache)
git-ai-reporter --no-cache

# Explicitly enable caching (default)
git-ai-reporter --cache

# Combined with other options
git-ai-reporter --no-cache --weeks 1 --debug
```

#### `--cache-dir PATH`
**Type:** Path  
**Default:** `.git-ai-reporter-cache`  
**Description:** Custom cache directory location

```bash
# Custom cache location
git-ai-reporter --cache-dir ./custom-cache

# System-wide cache directory
git-ai-reporter --cache-dir /var/cache/git-ai-reporter

# User-specific cache
git-ai-reporter --cache-dir ~/.cache/git-ai-reporter
```

#### `--timeout SECONDS`
**Type:** Integer  
**Default:** 300  
**Description:** API request timeout in seconds

```bash
# Shorter timeout for faster failure
git-ai-reporter --timeout 120

# Longer timeout for large repositories
git-ai-reporter --timeout 600

# Very patient timeout
git-ai-reporter --timeout 1200
```

#### `--concurrent INTEGER`
**Type:** Integer (1-20)  
**Default:** 5  
**Description:** Maximum concurrent API requests

```bash
# Conservative concurrency (slower, more stable)
git-ai-reporter --concurrent 2

# Aggressive concurrency (faster, may hit rate limits)
git-ai-reporter --concurrent 10

# Single-threaded processing
git-ai-reporter --concurrent 1
```

### Debugging and Development Options

#### `--debug / --no-debug`
**Type:** Boolean flag  
**Default:** `--no-debug`  
**Description:** Enable verbose debug output

```bash
# Enable debug mode
git-ai-reporter --debug

# Debug with specific options
git-ai-reporter --debug --weeks 1 --no-cache

# Pipe debug output to file
git-ai-reporter --debug --weeks 2 2>&1 | tee debug.log
```

#### `--dry-run`
**Type:** Boolean flag  
**Default:** False  
**Description:** Show what would be analyzed without making API calls

```bash
# Preview analysis scope
git-ai-reporter --dry-run --weeks 4

# Check configuration
git-ai-reporter --dry-run --debug

# Validate date ranges
git-ai-reporter --dry-run --start-date "2025-01-01" --end-date "2025-01-31"
```

#### `--verbose / --quiet`
**Type:** Boolean flag  
**Default:** Normal verbosity  
**Description:** Control output verbosity level

```bash
# Verbose output (more information)
git-ai-reporter --verbose

# Quiet mode (minimal output)
git-ai-reporter --quiet

# Debug mode implies verbose
git-ai-reporter --debug  # Same as --verbose --debug-mode
```

### Validation and Testing Options

#### `--validate-config`
**Type:** Boolean flag  
**Default:** False  
**Description:** Validate configuration without running analysis

```bash
# Check configuration validity
git-ai-reporter --validate-config

# Validate with specific options
git-ai-reporter --validate-config --model-tier-1 "custom-model"

# Combined with debug for detailed validation
git-ai-reporter --validate-config --debug
```

#### `--test-api`
**Type:** Boolean flag  
**Default:** False  
**Description:** Test API connectivity and authentication

```bash
# Test API connection
git-ai-reporter --test-api

# Test with specific models
git-ai-reporter --test-api --model-tier-1 "gemini-2.5-pro"

# Test with debug output
git-ai-reporter --test-api --debug
```

#### `--show-config`
**Type:** Boolean flag  
**Default:** False  
**Description:** Display current configuration and exit

```bash
# Show all configuration values
git-ai-reporter --show-config

# Show configuration with specific options applied
git-ai-reporter --show-config --temperature 0.3 --max-tokens 16384
```

### Cache Management Options

#### `--clear-cache [TYPE]`
**Type:** Optional string  
**Default:** All cache types  
**Description:** Clear cached data

```bash
# Clear all cache
git-ai-reporter --clear-cache

# Clear specific cache types
git-ai-reporter --clear-cache commits
git-ai-reporter --clear-cache daily
git-ai-reporter --clear-cache responses

# Clear multiple types
git-ai-reporter --clear-cache commits,daily
```

#### `--cache-stats`
**Type:** Boolean flag  
**Default:** False  
**Description:** Display cache statistics

```bash
# Basic cache statistics
git-ai-reporter --cache-stats

# Detailed cache statistics
git-ai-reporter --cache-stats --verbose

# Cache stats with cleanup
git-ai-reporter --cache-stats --cache-cleanup
```

#### `--cache-cleanup`
**Type:** Boolean flag  
**Default:** False  
**Description:** Remove expired cache entries

```bash
# Clean expired entries
git-ai-reporter --cache-cleanup

# Cleanup with statistics
git-ai-reporter --cache-cleanup --cache-stats

# Force cleanup regardless of TTL
git-ai-reporter --cache-cleanup --force
```

## Option Combinations and Patterns

### Common Usage Patterns

#### Quick Development Analysis
```bash
git-ai-reporter --weeks 1 --debug --no-cache
```

#### Production Release Analysis
```bash
git-ai-reporter \
  --since-tag v1.0.0 \
  --output-dir ./release-docs \
  --temperature 0.3 \
  --cache
```

#### Performance Optimized
```bash
git-ai-reporter \
  --model-tier-1 "gemini-2.5-flash" \
  --model-tier-2 "gemini-2.5-flash" \
  --model-tier-3 "gemini-2.5-pro" \
  --concurrent 10 \
  --cache
```

#### Quality Optimized
```bash
git-ai-reporter \
  --model-tier-1 "gemini-2.5-pro" \
  --model-tier-2 "gemini-2.5-pro" \
  --model-tier-3 "gemini-2.5-pro" \
  --temperature 0.2 \
  --max-tokens 32768 \
  --no-cache
```

#### Comprehensive Analysis
```bash
git-ai-reporter \
  --weeks 8 \
  --include-trivial \
  --output-dir "./analysis-$(date +%Y-%m-%d)" \
  --verbose \
  --cache
```

### Environment-Specific Configurations

#### Development Environment
```bash
git-ai-reporter \
  --weeks 1 \
  --debug \
  --no-cache \
  --timeout 600 \
  --model-tier-2 "gemini-2.5-flash"
```

#### CI/CD Pipeline
```bash
git-ai-reporter \
  --weeks 1 \
  --quiet \
  --cache \
  --cache-dir /tmp/git-ai-cache \
  --timeout 300 \
  --concurrent 3
```

#### Stakeholder Reporting
```bash
git-ai-reporter \
  --weeks 4 \
  --temperature 0.4 \
  --max-tokens-tier-3 32768 \
  --trivial-types "style,chore,test" \
  --output-dir ./stakeholder-reports
```

## Environment Variable Equivalents

Most CLI options have environment variable equivalents:

| CLI Option | Environment Variable | Example |
|-----------|---------------------|---------|
| `--repo-path` | `GIT_AI_REPO_PATH` | `export GIT_AI_REPO_PATH="/path/to/repo"` |
| `--weeks` | `GIT_AI_WEEKS` | `export GIT_AI_WEEKS=2` |
| `--model-tier-1` | `MODEL_TIER_1` | `export MODEL_TIER_1="gemini-2.5-pro"` |
| `--temperature` | `TEMPERATURE` | `export TEMPERATURE=0.3` |
| `--debug` | `DEBUG` | `export DEBUG=true` |
| `--cache-dir` | `CACHE_DIR` | `export CACHE_DIR="./custom-cache"` |

**Priority Order:** CLI options override environment variables override `.env` file values override defaults.

## Exit Codes

Git AI Reporter uses standard exit codes to indicate success or failure:

| Exit Code | Meaning | Description |
|-----------|---------|-------------|
| `0` | Success | Analysis completed successfully |
| `1` | General Error | Unspecified error occurred |
| `2` | Configuration Error | Invalid configuration or options |
| `3` | Authentication Error | API key invalid or missing |
| `4` | Repository Error | Git repository not found or inaccessible |
| `5` | Network Error | Unable to connect to API services |
| `6` | Rate Limit Error | API rate limit exceeded |
| `7` | Cache Error | Cache corruption or access issues |
| `8` | Validation Error | Input validation failed |

### Exit Code Usage

```bash
# Check exit code in scripts
git-ai-reporter --weeks 2
if [ $? -eq 0 ]; then
    echo "Analysis successful"
else
    echo "Analysis failed with exit code $?"
fi

# Use in conditional execution
git-ai-reporter --test-api && git-ai-reporter --weeks 4

# Handle specific error codes
git-ai-reporter --weeks 2
case $? in
    0) echo "Success" ;;
    3) echo "Check your API key" ;;
    4) echo "Not a Git repository" ;;
    6) echo "Rate limited - try again later" ;;
    *) echo "Unknown error" ;;
esac
```

## Advanced Option Usage

### Complex Date Range Analysis

```bash
# Analyze specific months
for month in 01 02 03; do
    git-ai-reporter \
      --start-date "2025-${month}-01" \
      --end-date "2025-${month}-$(cal ${month} 2025 | awk 'NF {DAYS = $NF}; END {print DAYS}')" \
      --output-dir "./monthly-reports/2025-${month}"
done

# Analyze between releases
git-ai-reporter \
  --since-tag $(git describe --tags --abbrev=0 HEAD~1) \
  --end-date $(git show -s --format=%ci $(git describe --tags --abbrev=0)) \
  --output-dir "./release-analysis"
```

### Model A/B Testing

```bash
# Compare model performance
mkdir -p comparison/{fast,pro}

# Fast model analysis
git-ai-reporter \
  --model-tier-1 "gemini-2.5-flash" \
  --model-tier-2 "gemini-2.5-flash" \
  --model-tier-3 "gemini-2.5-flash" \
  --output-dir ./comparison/fast \
  --weeks 2

# Pro model analysis  
git-ai-reporter \
  --model-tier-1 "gemini-2.5-pro" \
  --model-tier-2 "gemini-2.5-pro" \
  --model-tier-3 "gemini-2.5-pro" \
  --output-dir ./comparison/pro \
  --weeks 2
```

### Automated Analysis Scripts

```bash
#!/bin/bash
# weekly-analysis.sh

# Configuration
REPO_PATH="${1:-$(pwd)}"
OUTPUT_BASE="/var/reports/git-ai-reporter"
DATE_STR=$(date +%Y-%m-%d)

# Create timestamped output directory
OUTPUT_DIR="${OUTPUT_BASE}/${DATE_STR}"
mkdir -p "${OUTPUT_DIR}"

# Run analysis with error handling
git-ai-reporter \
  --repo-path "${REPO_PATH}" \
  --weeks 1 \
  --output-dir "${OUTPUT_DIR}" \
  --cache \
  --verbose \
  --timeout 900

# Check results
if [ $? -eq 0 ]; then
    echo "Analysis completed: ${OUTPUT_DIR}"
    ls -la "${OUTPUT_DIR}"
else
    echo "Analysis failed - check logs"
    exit 1
fi
```

## Troubleshooting Common Option Issues

### Option Validation

??? failure "Invalid model name"

    **Error:** `Invalid model name: custom-model`
    
    **Solution:**
    ```bash
    # Use valid model names
    git-ai-reporter --model-tier-1 "gemini-2.5-flash"  # ✅
    git-ai-reporter --model-tier-1 "gemini-2.5-pro"   # ✅
    
    # Test model availability
    git-ai-reporter --test-api --debug
    ```

??? failure "Date range errors"

    **Error:** `Invalid date range: start date after end date`
    
    **Solution:**
    ```bash
    # Ensure proper date order
    git-ai-reporter \
      --start-date "2025-01-01" \
      --end-date "2025-01-31"    # ✅
    
    # Use ISO format for clarity
    git-ai-reporter \
      --start-date "2025-01-01T00:00:00" \
      --end-date "2025-01-31T23:59:59"
    ```

??? failure "Path not found errors"

    **Error:** `Repository not found: /invalid/path`
    
    **Solution:**
    ```bash
    # Verify path exists
    ls -la /path/to/repo/.git
    
    # Use absolute paths
    git-ai-reporter --repo-path "$(pwd)/my-project"
    
    # Check Git repository status
    cd /path/to/repo && git status
    ```

### Performance Tuning

??? warning "Slow analysis"

    **Issue:** Analysis takes too long
    
    **Solutions:**
    ```bash
    # Increase concurrency
    git-ai-reporter --concurrent 8
    
    # Use faster models
    git-ai-reporter --model-tier-2 "gemini-2.5-flash"
    
    # Reduce scope
    git-ai-reporter --weeks 2 --trivial-types "style,chore,docs"
    ```

??? warning "API rate limits"

    **Issue:** Rate limit exceeded errors
    
    **Solutions:**
    ```bash
    # Reduce concurrency
    git-ai-reporter --concurrent 2
    
    # Increase timeout
    git-ai-reporter --timeout 600
    
    # Enable caching
    git-ai-reporter --cache
    ```

## Related Resources

- **[CLI Commands Guide →](commands.md)** - Detailed command explanations
- **[CLI Examples →](examples.md)** - Real-world usage examples  
- **[Configuration Guide →](../installation/configuration.md)** - Environment variables and settings
- **[Troubleshooting →](../guide/troubleshooting.md)** - Solve common CLI issues