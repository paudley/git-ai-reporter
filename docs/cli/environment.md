# Environment Variables

Git AI Reporter uses environment variables for configuration, allowing you to customize behavior without modifying command-line arguments. All settings can be configured through environment variables following the `pydantic-settings` pattern.

## Configuration Loading

Environment variables are loaded with the following priority:

1. **Environment variables** (highest priority)
2. **.env file** in the current working directory
3. **Default values** (lowest priority)

## Core Environment Variables

### API Configuration

**`GEMINI_API_KEY`** (Required)
: Your Google Gemini API key for AI analysis

```bash
export GEMINI_API_KEY="your-api-key-here"
```

!!! warning "Security Notice"
    
    Never commit API keys to version control. Use environment variables or `.env` files that are excluded from git.

### AI Model Configuration

Configure which Gemini models to use for each processing tier:

**`MODEL_TIER_1`** (Default: `gemini-2.5-flash`)
: Fast model for individual commit analysis

**`MODEL_TIER_2`** (Default: `gemini-2.5-pro`)
: Advanced model for daily synthesis and pattern recognition

**`MODEL_TIER_3`** (Default: `gemini-2.5-pro`)
: Advanced model for final artifact generation

```bash
# Use different model configurations
export MODEL_TIER_1="gemini-2.5-flash"
export MODEL_TIER_2="gemini-2.5-pro"
export MODEL_TIER_3="gemini-2.5-pro"
```

### Output File Configuration

**`NEWS_FILE`** (Default: `NEWS.md`)
: Path for narrative development summary output

**`CHANGELOG_FILE`** (Default: `CHANGELOG.txt`)
: Path for structured changelog output

**`DAILY_UPDATES_FILE`** (Default: `DAILY_UPDATES.md`)
: Path for daily activity summaries

```bash
export NEWS_FILE="docs/development-summary.md"
export CHANGELOG_FILE="releases/CHANGELOG.txt"
export DAILY_UPDATES_FILE="reports/daily-activity.md"
```

## Advanced Configuration

### Commit Filtering

Control which commits are considered "trivial" and filtered from analysis:

**`TRIVIAL_COMMIT_TYPES`**
: JSON array of commit type prefixes to filter

**`TRIVIAL_FILE_PATTERNS`**
: JSON array of regex patterns for files to ignore

```bash
# Filter additional commit types (JSON format)
export TRIVIAL_COMMIT_TYPES='["style", "chore", "docs"]'

# Filter additional file patterns
export TRIVIAL_FILE_PATTERNS='["\.gitignore$", "\.editorconfig$", "\.prettierrc"]'
```

!!! note "Default Filtering"
    
    By default, only `style` and `chore` commits are filtered. Documentation changes, test commits, and CI commits are **not** filtered as they represent meaningful development work.

### AI Processing Parameters

**`GEMINI_INPUT_TOKEN_LIMIT_TIER1`** (Default: `1000000`)
: Input token limit for Tier 1 model

**`GEMINI_INPUT_TOKEN_LIMIT_TIER2`** (Default: `1000000`)
: Input token limit for Tier 2 model

**`GEMINI_INPUT_TOKEN_LIMIT_TIER3`** (Default: `1000000`)
: Input token limit for Tier 3 model

**`MAX_TOKENS_TIER_1`** (Default: `8192`)
: Output token limit for Tier 1 model

**`MAX_TOKENS_TIER_2`** (Default: `8192`)
: Output token limit for Tier 2 model

**`MAX_TOKENS_TIER_3`** (Default: `16384`)
: Output token limit for Tier 3 model

**`TEMPERATURE`** (Default: `0.5`)
: AI model temperature for response generation

```bash
# Adjust AI model parameters
export TEMPERATURE="0.7"
export MAX_TOKENS_TIER_3="32768"
```

### Performance and Reliability

**`GEMINI_API_TIMEOUT`** (Default: `300`)
: Timeout in seconds for Gemini API calls

**`GIT_COMMAND_TIMEOUT`** (Default: `30`)
: Timeout in seconds for individual git commands

**`MAX_CONCURRENT_GIT_COMMANDS`** (Default: `5`)
: Maximum concurrent asyncio tasks for git operations

```bash
# Increase timeouts for large repositories
export GEMINI_API_TIMEOUT="600"
export GIT_COMMAND_TIMEOUT="60"
export MAX_CONCURRENT_GIT_COMMANDS="3"
```

## Environment File Configuration

### .env File Format

Create a `.env` file in your project root for persistent configuration:

```bash
# .env file example
GEMINI_API_KEY=your-api-key-here

# Model Configuration
MODEL_TIER_1=gemini-2.5-flash
MODEL_TIER_2=gemini-2.5-pro
MODEL_TIER_3=gemini-2.5-pro

# Output Files
NEWS_FILE=docs/development-summary.md
CHANGELOG_FILE=CHANGELOG.md
DAILY_UPDATES_FILE=reports/daily-updates.md

# Performance Tuning
TEMPERATURE=0.3
GEMINI_API_TIMEOUT=600
MAX_CONCURRENT_GIT_COMMANDS=3
```

### Multiple Environment Support

=== "Development"

    ```bash
    # .env.development
    GEMINI_API_KEY=dev-api-key
    TEMPERATURE=0.7
    MODEL_TIER_1=gemini-2.5-flash
    MODEL_TIER_2=gemini-2.5-flash  # Use faster model for dev
    MODEL_TIER_3=gemini-2.5-flash
    ```

=== "Production"

    ```bash
    # .env.production
    GEMINI_API_KEY=prod-api-key
    TEMPERATURE=0.3
    MODEL_TIER_1=gemini-2.5-flash
    MODEL_TIER_2=gemini-2.5-pro
    MODEL_TIER_3=gemini-2.5-pro
    GEMINI_API_TIMEOUT=600
    ```

=== "CI/CD"

    ```bash
    # .env.ci
    GEMINI_API_KEY=${GEMINI_API_KEY_SECRET}
    NEWS_FILE=artifacts/news.md
    CHANGELOG_FILE=artifacts/changelog.txt
    DAILY_UPDATES_FILE=artifacts/daily.md
    GEMINI_API_TIMEOUT=900  # Longer timeout for CI
    ```

## Integration Examples

### GitHub Actions

```yaml
name: Generate Documentation
on: [push]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Generate Reports
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          MODEL_TIER_2: gemini-2.5-pro
          TEMPERATURE: 0.3
          GEMINI_API_TIMEOUT: 600
        run: |
          git-ai-reporter --weeks 1
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.12
WORKDIR /app

# Install git-ai-reporter
RUN pip install git-ai-reporter

# Set environment variables
ENV MODEL_TIER_1=gemini-2.5-flash
ENV MODEL_TIER_2=gemini-2.5-pro
ENV TEMPERATURE=0.3
ENV GEMINI_API_TIMEOUT=600

# API key provided at runtime
ENV GEMINI_API_KEY=""

ENTRYPOINT ["git-ai-reporter"]
```

```bash
# Run with environment variables
docker run --rm \
  -e GEMINI_API_KEY="your-api-key" \
  -e TEMPERATURE="0.7" \
  -v $(pwd):/app \
  your-image --weeks 2
```

### Shell Scripts

```bash
#!/bin/bash
# weekly-report.sh

# Load environment from file
set -a
source .env.production
set +a

# Override specific settings
export NEWS_FILE="reports/weekly-$(date +%Y%m%d).md"
export TEMPERATURE="0.3"

# Generate weekly report
git-ai-reporter --weeks 1 --debug

echo "Weekly report generated: $NEWS_FILE"
```

## Environment Validation

### Checking Configuration

Use Python to validate your environment setup:

```python
from git_ai_reporter.config import Settings

# Load and validate settings
settings = Settings()

# Check required values
if not settings.GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY is required")
else:
    print("✅ GEMINI_API_KEY configured")

# Display current configuration
print(f"Model Tier 1: {settings.MODEL_TIER_1}")
print(f"Model Tier 2: {settings.MODEL_TIER_2}")
print(f"Model Tier 3: {settings.MODEL_TIER_3}")
print(f"Temperature: {settings.TEMPERATURE}")
```

### Configuration Debugging

Enable debug mode to see configuration loading:

```bash
# Show configuration loading
git-ai-reporter --debug --weeks 1

# This will display:
# - Which .env file was loaded
# - Final configuration values
# - Model selection rationale
```

## Security Best Practices

### API Key Management

!!! danger "Never Commit Secrets"
    
    - Add `.env` files to `.gitignore`
    - Use environment variables in production
    - Rotate API keys regularly
    - Use different keys for different environments

### Environment Isolation

```bash
# Use different .env files per environment
cp .env.example .env.development
cp .env.example .env.production

# Load environment-specific configuration
export ENV_FILE=".env.${ENVIRONMENT:-development}"
```

### Access Control

```bash
# Restrict .env file permissions
chmod 600 .env
chown $(whoami):$(whoami) .env

# Verify permissions
ls -la .env
# Should show: -rw------- 1 user user
```

## Troubleshooting

### Common Issues

??? failure "API Key Not Found"
    
    **Error**: `GEMINI_API_KEY is not set`
    
    **Solutions**:
    ```bash
    # Check if variable is set
    echo $GEMINI_API_KEY
    
    # Set for current session
    export GEMINI_API_KEY="your-key-here"
    
    # Add to .env file
    echo "GEMINI_API_KEY=your-key-here" >> .env
    ```

??? failure "Invalid Model Name"
    
    **Error**: `Invalid model specified`
    
    **Solutions**:
    ```bash
    # Check available models
    echo "Available models:"
    echo "- gemini-2.5-flash"
    echo "- gemini-2.5-pro"
    
    # Reset to defaults
    unset MODEL_TIER_1 MODEL_TIER_2 MODEL_TIER_3
    ```

??? failure "Permission Denied"
    
    **Error**: `Permission denied reading .env file`
    
    **Solutions**:
    ```bash
    # Fix file permissions
    chmod 600 .env
    
    # Check file ownership
    ls -la .env
    
    # Fix ownership if needed
    chown $(whoami) .env
    ```

### Environment Debugging

```bash
# List all environment variables with GIT_AI prefix
env | grep -E "^(GEMINI|MODEL|NEWS|CHANGELOG|DAILY|TEMPERATURE|MAX_)" | sort

# Test configuration loading
python -c "
from git_ai_reporter.config import Settings
settings = Settings()
print('Configuration loaded successfully')
print(f'API Key configured: {bool(settings.GEMINI_API_KEY)}')
"
```

## Related Documentation

- **[Configuration Guide →](../installation/configuration.md)** - Complete configuration reference
- **[CLI Options →](options.md)** - Command-line argument reference  
- **[Examples →](examples.md)** - Real-world usage examples
- **[AI Models →](../guide/ai-models.md)** - Model selection strategies