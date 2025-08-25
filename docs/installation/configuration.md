# Post-Installation Configuration

After installing Git AI Reporter, you'll need to configure it for optimal performance in your environment. This guide covers all configuration options, from basic API setup to advanced customization.

## Quick Setup

### 1. API Key Configuration

Git AI Reporter requires a Google Gemini API key:

=== "Environment Variable (Recommended)"

    ```bash
    # Set for current session
    export GEMINI_API_KEY="your-api-key-here"
    
    # Add to shell profile for persistence
    echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
    source ~/.bashrc
    ```

=== ".env File (Local Development)"

    ```bash
    # Create .env file in your project directory
    echo 'GEMINI_API_KEY="your-api-key-here"' > .env
    
    # Ensure .env is in .gitignore
    echo '.env' >> .gitignore
    ```

=== "System Environment (Production)"

    ```bash
    # Linux/macOS system service
    sudo systemctl edit git-ai-reporter --force
    # Add: Environment=GEMINI_API_KEY=your-key-here
    
    # Docker environment
    docker run -e GEMINI_API_KEY="your-key" git-ai-reporter
    
    # Kubernetes secret
    kubectl create secret generic git-ai-reporter-config \
      --from-literal=GEMINI_API_KEY="your-key"
    ```

### 2. Verify Configuration

```bash
# Test configuration
git-ai-reporter --debug --dry-run

# Expected output:
# ✅ API key configured
# ✅ Git repository detected
# ✅ All dependencies satisfied
```

## Configuration Methods

Git AI Reporter supports multiple configuration approaches, listed in order of precedence:

1. **Command-line arguments** (highest priority)
2. **Environment variables**  
3. **`.env` file**
4. **Default values** (lowest priority)

### Command-Line Override

```bash
# Override any setting via command line
git-ai-reporter \
  --repo-path /path/to/repo \
  --weeks 3 \
  --output-dir ./reports \
  --debug
```

### Environment Variables

All configuration can be set via environment:

```bash
export GEMINI_API_KEY="your-api-key"
export MODEL_TIER_1="gemini-2.5-flash"
export MODEL_TIER_2="gemini-2.5-pro"  
export MODEL_TIER_3="gemini-2.5-pro"
export DEBUG="true"
export CACHE_ENABLED="false"
```

### .env File Format

```bash title=".env"
# API Configuration
GEMINI_API_KEY="your-api-key-here"

# Model Selection
MODEL_TIER_1="gemini-2.5-flash"
MODEL_TIER_2="gemini-2.5-pro"
MODEL_TIER_3="gemini-2.5-pro"

# Output Configuration
NEWS_FILE="NEWS.md"
CHANGELOG_FILE="CHANGELOG.txt"
DAILY_UPDATES_FILE="DAILY_UPDATES.md"

# Performance Settings
GEMINI_API_TIMEOUT=300
GIT_COMMAND_TIMEOUT=30
MAX_CONCURRENT_GIT_COMMANDS=5

# AI Model Parameters
MAX_TOKENS_TIER_1=8192
MAX_TOKENS_TIER_2=8192
MAX_TOKENS_TIER_3=16384
TEMPERATURE=0.5

# Filtering Configuration
TRIVIAL_COMMIT_TYPES="style,chore"

# Development Settings
DEBUG=false
CACHE_ENABLED=true
```

## Configuration Reference

### API & Authentication

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| API Key | `GEMINI_API_KEY` | `None` | **Required.** Google Gemini API key |

!!! danger "Security Warning"

    Never commit API keys to version control. Always use environment variables or `.env` files that are excluded from Git.

### AI Model Configuration

Control which Gemini models are used for each processing tier:

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Tier 1 Model | `MODEL_TIER_1` | `gemini-2.5-flash` | Fast commit analysis |
| Tier 2 Model | `MODEL_TIER_2` | `gemini-2.5-pro` | Pattern synthesis |  
| Tier 3 Model | `MODEL_TIER_3` | `gemini-2.5-pro` | Final narratives |

**Model Selection Guide:**

=== "Performance Optimized"

    ```bash
    MODEL_TIER_1="gemini-2.5-flash"  # Fastest, most cost-effective
    MODEL_TIER_2="gemini-2.5-flash"  # Trade quality for speed
    MODEL_TIER_3="gemini-2.5-pro"    # Quality where it matters
    ```

=== "Quality Optimized"

    ```bash
    MODEL_TIER_1="gemini-2.5-pro"    # Best quality everywhere
    MODEL_TIER_2="gemini-2.5-pro"    # Consistent high quality
    MODEL_TIER_3="gemini-2.5-pro"    # Maximum narrative quality
    ```

=== "Balanced (Default)"

    ```bash
    MODEL_TIER_1="gemini-2.5-flash"  # Efficient bulk processing
    MODEL_TIER_2="gemini-2.5-pro"    # Quality synthesis
    MODEL_TIER_3="gemini-2.5-pro"    # Polished narratives
    ```

### AI Generation Parameters

Fine-tune AI behavior:

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Max Tokens (Tier 1) | `MAX_TOKENS_TIER_1` | `8192` | Token limit for commit analysis |
| Max Tokens (Tier 2) | `MAX_TOKENS_TIER_2` | `8192` | Token limit for synthesis |
| Max Tokens (Tier 3) | `MAX_TOKENS_TIER_3` | `16384` | Token limit for narratives |
| Temperature | `TEMPERATURE` | `0.5` | Randomness (0.0-1.0) |

**Temperature Guide:**
- `0.0-0.3`: Deterministic, factual output
- `0.4-0.6`: Balanced creativity and consistency  
- `0.7-1.0`: Creative, varied output

### Output File Configuration

Customize generated file names and locations:

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| News File | `NEWS_FILE` | `NEWS.md` | Stakeholder narratives |
| Changelog File | `CHANGELOG_FILE` | `CHANGELOG.txt` | Technical change log |
| Daily Updates | `DAILY_UPDATES_FILE` | `DAILY_UPDATES.md` | Daily development logs |

**Custom Paths:**
```bash
# Custom file names
NEWS_FILE="RELEASE_NOTES.md"
CHANGELOG_FILE="CHANGES.rst"
DAILY_UPDATES_FILE="dev-log.md"

# Custom directories  
NEWS_FILE="docs/releases/NEWS.md"
CHANGELOG_FILE="docs/CHANGELOG.md"
DAILY_UPDATES_FILE="logs/daily-updates.md"
```

### Commit Filtering Configuration

Control which commits are considered trivial:

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Trivial Types | `TRIVIAL_COMMIT_TYPES` | `["style", "chore"]` | Commit type prefixes to exclude |
| Trivial Patterns | `TRIVIAL_FILE_PATTERNS` | See below | File patterns to exclude |

**Default File Patterns:**
```python
TRIVIAL_FILE_PATTERNS = [
    r"\.gitignore$",
    r"\.editorconfig$", 
    r"\.prettierrc",
    # Note: .md and .toml files are NOT excluded by default
    # Documentation and config changes are important!
]
```

**Custom Filtering:**
```bash
# More aggressive filtering
TRIVIAL_COMMIT_TYPES="style,chore,docs,test"

# Less filtering (track more changes)
TRIVIAL_COMMIT_TYPES="style"

# Custom file patterns (JSON array format)
TRIVIAL_FILE_PATTERNS='["\.gitignore$", "\.vscode/"]'
```

### Performance & Timeout Settings

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| API Timeout | `GEMINI_API_TIMEOUT` | `300` | Seconds for API calls |
| Git Timeout | `GIT_COMMAND_TIMEOUT` | `30` | Seconds for Git operations |
| Max Concurrent | `MAX_CONCURRENT_GIT_COMMANDS` | `5` | Parallel Git operations |

**Performance Tuning:**
```bash
# High-performance setup (faster hardware)
GEMINI_API_TIMEOUT=600
MAX_CONCURRENT_GIT_COMMANDS=10

# Conservative setup (limited resources)
GEMINI_API_TIMEOUT=120
MAX_CONCURRENT_GIT_COMMANDS=2
```

### Development & Debugging

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| Debug Mode | `DEBUG` | `false` | Enable verbose logging |
| Cache Enabled | `CACHE_ENABLED` | `true` | Enable response caching |
| Log Level | `LOG_LEVEL` | `INFO` | Logging verbosity |

## Environment-Specific Configuration

### Development Environment

```bash title=".env.development"
# Development-friendly settings
DEBUG=true
CACHE_ENABLED=false
LOG_LEVEL=DEBUG

# Faster models for development
MODEL_TIER_1="gemini-2.5-flash"
MODEL_TIER_2="gemini-2.5-flash"
MODEL_TIER_3="gemini-2.5-pro"

# More permissive timeouts
GEMINI_API_TIMEOUT=600
GIT_COMMAND_TIMEOUT=60

# Less aggressive filtering
TRIVIAL_COMMIT_TYPES="style"
```

### Production Environment

```bash title=".env.production"
# Production-optimized settings
DEBUG=false
CACHE_ENABLED=true
LOG_LEVEL=INFO

# Balanced model selection
MODEL_TIER_1="gemini-2.5-flash"
MODEL_TIER_2="gemini-2.5-pro"
MODEL_TIER_3="gemini-2.5-pro"

# Standard timeouts
GEMINI_API_TIMEOUT=300
GIT_COMMAND_TIMEOUT=30

# Standard filtering
TRIVIAL_COMMIT_TYPES="style,chore"
```

### CI/CD Environment

```bash title=".env.ci"
# CI-optimized settings
DEBUG=false
CACHE_ENABLED=true
LOG_LEVEL=WARNING

# Cost-effective models
MODEL_TIER_1="gemini-2.5-flash"
MODEL_TIER_2="gemini-2.5-flash"
MODEL_TIER_3="gemini-2.5-pro"

# Conservative timeouts for stability
GEMINI_API_TIMEOUT=180
MAX_CONCURRENT_GIT_COMMANDS=3
```

## Advanced Configuration

### Custom Prompt Templates

For advanced users who want to customize AI prompts:

```python title="custom_config.py"
# Custom prompt overrides (advanced usage)
CUSTOM_PROMPTS = {
    "commit_analysis": """
    Analyze this commit with focus on business impact:
    {diff}
    
    Return JSON with business_value field.
    """,
    
    "weekly_narrative": """
    Create an executive summary focusing on:
    1. Key deliverables completed
    2. Business value delivered  
    3. Risk mitigation achieved
    """
}
```

### Multi-Repository Configuration

```yaml title="multi-repo-config.yml"
repositories:
  - name: "frontend"
    path: "./frontend"
    config:
      MODEL_TIER_1: "gemini-2.5-flash"
      TRIVIAL_COMMIT_TYPES: "style,chore,test"
      
  - name: "backend" 
    path: "./backend"
    config:
      MODEL_TIER_1: "gemini-2.5-pro"  # Higher quality for backend
      TRIVIAL_COMMIT_TYPES: "style,chore"  # Include tests
      
  - name: "docs"
    path: "./documentation"
    config:
      TRIVIAL_COMMIT_TYPES: "style"  # Track all doc changes
```

### Container Configuration

For Docker/Kubernetes deployments:

=== "Docker Compose"

    ```yaml title="docker-compose.yml"
    services:
      git-ai-reporter:
        image: git-ai-reporter:latest
        environment:
          GEMINI_API_KEY: ${GEMINI_API_KEY}
          MODEL_TIER_1: "gemini-2.5-flash"
          DEBUG: "false"
          CACHE_ENABLED: "true"
        volumes:
          - ./:/workspace
          - cache-volume:/cache
    
    volumes:
      cache-volume:
    ```

=== "Kubernetes ConfigMap"

    ```yaml title="configmap.yml"
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: git-ai-reporter-config
    data:
      MODEL_TIER_1: "gemini-2.5-flash"
      MODEL_TIER_2: "gemini-2.5-pro"
      MODEL_TIER_3: "gemini-2.5-pro"
      DEBUG: "false"
      CACHE_ENABLED: "true"
      GEMINI_API_TIMEOUT: "300"
    ```

## Configuration Validation

### Verify Your Configuration

```bash
# Check all configuration values
git-ai-reporter --show-config

# Validate configuration without running analysis
git-ai-reporter --validate-config

# Test API connectivity
git-ai-reporter --test-api
```

### Configuration Troubleshooting

??? failure "API key not found"

    **Problem:** `GEMINI_API_KEY` environment variable not set.
    
    **Solutions:**
    ```bash
    # Check if variable is set
    echo $GEMINI_API_KEY
    
    # Check .env file exists and has correct format
    cat .env | grep GEMINI_API_KEY
    
    # Verify no quotes in environment variable
    export GEMINI_API_KEY=your-key-without-quotes
    ```

??? failure "Invalid model name"

    **Problem:** Specified model doesn't exist or isn't accessible.
    
    **Solutions:**
    ```bash
    # Use valid model names
    MODEL_TIER_1="gemini-2.5-flash"    # ✅ Valid
    MODEL_TIER_2="gemini-2.5-pro"     # ✅ Valid
    MODEL_TIER_3="gemini-1.5-pro"     # ❌ May not be available
    
    # Test model availability
    git-ai-reporter --test-models
    ```

??? failure "File path errors"

    **Problem:** Custom output paths don't exist or aren't writable.
    
    **Solutions:**
    ```bash
    # Create directories first
    mkdir -p docs/releases
    NEWS_FILE="docs/releases/NEWS.md"
    
    # Check permissions
    ls -la docs/
    
    # Use absolute paths if needed
    NEWS_FILE="/full/path/to/NEWS.md"
    ```

### Performance Monitoring

Monitor configuration impact on performance:

```bash
# Time analysis with different configurations
time git-ai-reporter --weeks 1

# Monitor API usage
git-ai-reporter --debug 2>&1 | grep "API call"

# Check cache effectiveness  
git-ai-reporter --cache-stats
```

## Configuration Best Practices

### Security

1. **Never commit API keys** - Use `.env` files and add to `.gitignore`
2. **Use environment variables in production** - More secure than files
3. **Rotate keys regularly** - Google AI Studio allows key management
4. **Limit key permissions** - Restrict to necessary services only

### Performance

1. **Use appropriate models** - Balance cost, speed, and quality
2. **Enable caching in production** - Significantly reduces API calls
3. **Tune concurrency** - Match your system's capabilities
4. **Monitor API usage** - Track costs and rate limits

### Maintainability

1. **Document custom settings** - Explain why settings were changed
2. **Use version control for configs** - Track configuration changes
3. **Test configuration changes** - Verify before deploying
4. **Keep configs environment-specific** - Different settings per environment

## Next Steps

After configuring Git AI Reporter:

1. **[Quick Start Guide →](../guide/quick-start.md)** - Run your first analysis
2. **[CLI Reference →](../cli/options.md)** - Explore all available options
3. **[Troubleshooting →](../guide/troubleshooting.md)** - Solve common issues
4. **[Integration Guide →](../guide/integration.md)** - Set up automated workflows

## Configuration Examples

### Example: Large Repository

```bash title=".env.large-repo"
# Configuration for large repositories (1000+ commits)
GEMINI_API_KEY="your-api-key"

# Fast models for bulk processing
MODEL_TIER_1="gemini-2.5-flash"
MODEL_TIER_2="gemini-2.5-flash"
MODEL_TIER_3="gemini-2.5-pro"

# Increased timeouts for large operations
GEMINI_API_TIMEOUT=900
GIT_COMMAND_TIMEOUT=120

# Higher concurrency for faster processing
MAX_CONCURRENT_GIT_COMMANDS=8

# Enable caching to avoid re-processing
CACHE_ENABLED=true

# More aggressive filtering to focus on important changes
TRIVIAL_COMMIT_TYPES="style,chore,docs,test"
```

### Example: Quality-Focused

```bash title=".env.quality-focused"
# Configuration prioritizing output quality over speed/cost
GEMINI_API_KEY="your-api-key"

# Use best models everywhere
MODEL_TIER_1="gemini-2.5-pro"
MODEL_TIER_2="gemini-2.5-pro"
MODEL_TIER_3="gemini-2.5-pro"

# Higher token limits for detailed analysis
MAX_TOKENS_TIER_1=16384
MAX_TOKENS_TIER_2=16384
MAX_TOKENS_TIER_3=32768

# Lower temperature for consistent output
TEMPERATURE=0.3

# Minimal filtering to capture all changes
TRIVIAL_COMMIT_TYPES="style"

# Generous timeouts for thorough processing
GEMINI_API_TIMEOUT=600
```