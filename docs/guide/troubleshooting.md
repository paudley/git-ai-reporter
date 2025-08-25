---
title: Troubleshooting Guide
description: Solutions to common issues with Git AI Reporter
---

# Troubleshooting Guide

This guide helps you resolve common issues when using Git AI Reporter.

## Installation Issues

### Python Version Error

**Problem**: `ERROR: Git AI Reporter requires Python 3.12 or higher`

**Solution**:
```bash
# Check your Python version
python --version

# Install Python 3.12 using pyenv
pyenv install 3.12.0
pyenv local 3.12.0

# Or using conda
conda create -n git-ai python=3.12
conda activate git-ai
```

### Dependency Conflicts

**Problem**: `ERROR: pip's dependency resolver does not currently take into account all the packages`

**Solution**:
```bash
# Create a fresh virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install with clean dependencies
pip install git-ai-reporter --no-cache-dir
```

### GitPython Installation Fails

**Problem**: `ERROR: Failed building wheel for GitPython`

**Solution**:
```bash
# Install system dependencies
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install git python3-dev

# macOS
brew install git

# Windows
# Install Git for Windows from https://git-scm.com/

# Then retry installation
pip install git-ai-reporter
```

## Configuration Issues

### API Key Not Found

**Problem**: `ERROR: GEMINI_API_KEY environment variable not set`

**Solution**:
```bash
# Set the environment variable
export GEMINI_API_KEY="your-api-key-here"

# Or add to your shell profile
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# Verify it's set
echo $GEMINI_API_KEY
```

### Invalid API Key

**Problem**: `ERROR: Invalid API key provided`

**Solution**:
1. Verify your API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Check for extra spaces or quotes in the key
3. Ensure the key has proper permissions
4. Try regenerating the key if issues persist

### Configuration File Not Loading

**Problem**: Configuration file `.git-ai-reporter.json` is ignored

**Solution**:
```bash
# Check file location (must be in project root)
ls -la .git-ai-reporter.json

# Validate JSON syntax
python -m json.tool < .git-ai-reporter.json

# Check for typos in configuration
cat .git-ai-reporter.json

# Use explicit config flag
git-ai-reporter --config .git-ai-reporter.json
```

## Git Repository Issues

### Not a Git Repository

**Problem**: `ERROR: Not a git repository`

**Solution**:
```bash
# Initialize git if needed
git init

# Or specify repository path
git-ai-reporter --repo /path/to/repo

# Verify git status
git status
```

### No Commits Found

**Problem**: `WARNING: No commits found in the specified date range`

**Solution**:
```bash
# Check if commits exist in range
git log --since="7 days ago" --oneline

# Try different date range
git-ai-reporter --days 30

# Check current branch
git branch --show-current

# Specify branch explicitly
git-ai-reporter --branch main
```

### Shallow Clone Issues

**Problem**: `ERROR: Shallow repository detected`

**Solution**:
```bash
# Convert shallow clone to full clone
git fetch --unshallow

# Or clone with full history
git clone --depth=0 https://github.com/user/repo.git

# For GitHub Actions
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Full history
```

## API and Network Issues

### Rate Limiting

**Problem**: `ERROR: API rate limit exceeded`

**Solution**:
```bash
# Wait for rate limit reset
sleep 3600  # Wait 1 hour

# Use cache to reduce API calls
git-ai-reporter --cache-dir .cache/git-ai

# Process smaller date ranges
git-ai-reporter --days 1  # Instead of --days 30

# Use different model tier
git-ai-reporter --model-tier1 gemini-2.5-flash
```

### Connection Timeout

**Problem**: `ERROR: Connection timeout to Gemini API`

**Solution**:
```bash
# Increase timeout
export GIT_AI_TIMEOUT=120  # 120 seconds

# Or use command line
git-ai-reporter --timeout 120

# Check network connectivity
ping google.com

# Use proxy if needed
export HTTPS_PROXY=http://proxy.example.com:8080
```

### SSL Certificate Error

**Problem**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution**:
```bash
# Update certificates
# macOS
brew install ca-certificates

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ca-certificates

# Python certificates
pip install --upgrade certifi

# Temporary workaround (NOT recommended for production)
export PYTHONHTTPSVERIFY=0
```

## Performance Issues

### Slow Processing

**Problem**: Analysis takes too long

**Solution**:
```bash
# Reduce scope
git-ai-reporter --days 7  # Instead of --days 30

# Use faster model
git-ai-reporter --model-tier1 gemini-2.5-flash

# Enable caching
git-ai-reporter --cache-dir .cache

# Increase workers
export GIT_AI_MAX_WORKERS=10
```

### Out of Memory

**Problem**: `MemoryError` during processing

**Solution**:
```bash
# Process in smaller chunks
git-ai-reporter --days 1

# Use debug mode to identify bottlenecks
git-ai-reporter --debug

# Reduce time range for large repos
git-ai-reporter --weeks 1

# Clear cache if corrupted
git-ai-reporter cache --clear
```

### High API Costs

**Problem**: Excessive API usage charges

**Solution**:
```bash
# Use caching (enabled by default)
git-ai-reporter --cache-dir ~/.cache/git-ai

# Use shorter time ranges
git-ai-reporter --weeks 1

# Configure cheaper models via environment
export MODEL_TIER_1="gemini-2.5-flash"
export MODEL_TIER_2="gemini-2.5-flash"
export MODEL_TIER_3="gemini-2.5-pro"

# Process less frequently
# Weekly instead of daily
```

## Output Issues

### Empty Output Files

**Problem**: Generated files are empty

**Solution**:
```bash
# Check for commits in range
git log --since="7 days ago" --oneline

# Enable verbose mode
git-ai-reporter --verbose

# Check API responses
git-ai-reporter --debug

# Verify write permissions
touch NEWS.md
ls -la NEWS.md
```

### Encoding Issues

**Problem**: Special characters appear corrupted

**Solution**:
```bash
# Set UTF-8 encoding
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# For Windows
chcp 65001

# Specify encoding in config
{
  "output": {
    "encoding": "utf-8"
  }
}
```

### Incorrect Formatting

**Problem**: Markdown formatting is broken

**Solution**:
```bash
# Validate markdown
npm install -g markdownlint-cli
markdownlint NEWS.md

# Use different template
# Templates are not yet implemented
# Use the default output formats

# Check for template errors
git-ai-reporter --validate-templates
```

## Cache Issues

### Stale Cache

**Problem**: Old results being returned

**Solution**:
```bash
# Clear cache
git-ai-reporter --clear-cache

# Or manually
rm -rf ~/.cache/git-ai-reporter

# Bypass cache
git-ai-reporter --no-cache

# Reduce cache TTL
git-ai-reporter --cache-ttl 3600  # 1 hour
```

### Cache Corruption

**Problem**: `ERROR: Failed to load cache`

**Solution**:
```bash
# Remove corrupted cache
rm -rf ~/.cache/git-ai-reporter

# Recreate cache directory
mkdir -p ~/.cache/git-ai-reporter

# Verify permissions
chmod 755 ~/.cache/git-ai-reporter
```

## Common Error Messages

### "No module named 'git_ai_reporter'"

```bash
# Reinstall package
pip uninstall git-ai-reporter
pip install git-ai-reporter

# Check installation
pip show git-ai-reporter
```

### "Permission denied"

```bash
# Fix file permissions
chmod 644 NEWS.md CHANGELOG.txt DAILY_UPDATES.md

# Fix directory permissions
chmod 755 .

# Run with sudo (not recommended)
sudo git-ai-reporter
```

### "JSON decode error"

```bash
# Fix config file
python -m json.tool < .git-ai-reporter.json > temp.json
mv temp.json .git-ai-reporter.json

# Check for BOM
file .git-ai-reporter.json

# Remove BOM if present
sed -i '1s/^\xEF\xBB\xBF//' .git-ai-reporter.json
```

## Debugging Techniques

### Enable Debug Mode

```bash
# Maximum verbosity
git-ai-reporter -vv

# Debug logging
export GIT_AI_LOG_LEVEL=DEBUG
git-ai-reporter

# Save debug output
git-ai-reporter --debug 2>&1 | tee debug.log
```

### Check Git History

```bash
# Verify commits exist
git log --since="7 days ago" --oneline

# Check file changes
git diff --stat HEAD~7

# Inspect specific commit
git show <commit-hash>
```

### Test API Connection

```python
#!/usr/bin/env python3
import os
import google.generativeai as genai

# Test API key
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    exit(1)

# Configure and test
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

try:
    response = model.generate_content("Hello, test")
    print("SUCCESS: API connection working")
    print(f"Response: {response.text[:100]}...")
except Exception as e:
    print(f"ERROR: {e}")
```

### Validate Installation

```bash
# Check Python version
python --version

# Check package installation
pip list | grep git-ai-reporter

# Check dependencies
pip check

# Run self-test
python -m git_ai_reporter --version
```

## Getting Help

### Resources

1. **Documentation**: Check the [official documentation](https://github.com/poissonconsulting/git-ai-reporter)
2. **Issues**: Search [GitHub Issues](https://github.com/poissonconsulting/git-ai-reporter/issues)
3. **Discussions**: Join [GitHub Discussions](https://github.com/poissonconsulting/git-ai-reporter/discussions)

### Reporting Bugs

When reporting issues, include:

1. **System Information**:
```bash
git-ai-reporter --version
python --version
git --version
uname -a  # or systeminfo on Windows
```

2. **Error Message**: Complete error output
3. **Steps to Reproduce**: Exact commands run
4. **Configuration**: Sanitized config file
5. **Debug Log**: Output from `--debug` flag

### Example Bug Report

```markdown
## Description
Git AI Reporter fails with "KeyError: 'summary'" when processing large repositories.

## Environment
- Git AI Reporter: 0.1.0
- Python: 3.12.0
- Git: 2.43.0
- OS: Ubuntu 22.04

## Steps to Reproduce
1. Clone large repository (>10k commits)
2. Run `git-ai-reporter --days 30`
3. Error occurs during weekly summary generation

## Error Output
```
Traceback (most recent call last):
  File "orchestrator.py", line 245, in generate_weekly_summary
    summary = result['summary']
KeyError: 'summary'
```

## Configuration
```json
{
  "days": 30,
  "model_tier1": "gemini-2.5-flash"
}
```

## Debug Log
[Attached debug.log]
```

## Next Steps

- Review [Performance Optimization](performance.md)
- Read [FAQ](faq.md)
- Explore [Advanced Usage](advanced-usage.md)
- Learn about [Configuration](configuration.md)