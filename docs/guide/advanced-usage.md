---
title: Advanced Features
description: Power user capabilities and advanced features
---

# Advanced Features

This guide covers advanced features and power user capabilities of Git AI Reporter.

## Time Range Configuration

### Custom Date Ranges

Instead of using the default weeks parameter, you can specify exact date ranges:

```bash
# Analyze specific date range
git-ai-reporter --start-date 2025-01-01 --end-date 2025-01-31

# Analyze from a start date to now
git-ai-reporter --start-date 2025-01-01

# Analyze last 52 weeks (maximum)
git-ai-reporter --weeks 52
```

## Configuration Files

### TOML Configuration

You can use a TOML configuration file to set default values:

```bash
# Use custom configuration file
git-ai-reporter --config-file config.toml
```

The configuration file can contain settings like model choices and API parameters. Check the Settings class in the source code for available options.

## Cache Management

### Cache Operations

Control the analysis cache:

```bash
# Use custom cache directory
git-ai-reporter --cache-dir /path/to/cache

# Bypass cache and re-analyze everything
git-ai-reporter --no-cache

# Clear cache
git-ai-reporter cache --clear

# Show cache statistics
git-ai-reporter cache --show
```

## Debug Mode

### Verbose Logging

Enable debug mode for detailed output:

```bash
# Enable debug logging
git-ai-reporter --debug

# Debug mode disables progress bars and shows detailed logs
git-ai-reporter --debug --weeks 1
```

## Pre-Release Documentation

### Generate Release Notes

Generate documentation formatted as if a release has already happened:

```bash
# Generate release documentation for version 1.2.3
git-ai-reporter --pre-release 1.2.3
```

This formats the output as historical documentation for the specified version.

## Integration with CI/CD

### GitHub Actions

```yaml
name: Weekly Documentation Update

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  generate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install Git AI Reporter
        run: pip install git-ai-reporter
      
      - name: Generate Documentation
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          git-ai-reporter --weeks 1
      
      - name: Commit Documentation
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add NEWS.md CHANGELOG.txt DAILY_UPDATES.md
          git diff --staged --quiet || \
            git commit -m "docs: Update development documentation [skip ci]"
      
      - name: Push changes
        uses: ad-m/github-push-action@master
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          branch: ${{ github.ref }}
```

### GitLab CI

```yaml
# .gitlab-ci.yml
generate-docs:
  stage: documentation
  image: python:3.12
  script:
    - pip install git-ai-reporter
    - git-ai-reporter --weeks 1
  artifacts:
    paths:
      - NEWS.md
      - CHANGELOG.txt
      - DAILY_UPDATES.md
    expire_in: 1 month
  only:
    - schedules
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    triggers {
        cron('0 9 * * 1')  // Weekly on Monday
    }
    
    environment {
        GEMINI_API_KEY = credentials('gemini-api-key')
    }
    
    stages {
        stage('Generate Documentation') {
            steps {
                sh '''
                    pip install git-ai-reporter
                    git-ai-reporter --weeks 1
                '''
            }
        }
        
        stage('Archive Artifacts') {
            steps {
                archiveArtifacts artifacts: '*.md,*.txt'
            }
        }
    }
}
```

## Automation Scripts

### Automated Release Notes

```bash
#!/bin/bash
# release-notes.sh

VERSION=$1
LAST_VERSION=$(git describe --tags --abbrev=0)
LAST_DATE=$(git log -1 --format=%ai $LAST_VERSION | cut -d' ' -f1)

git-ai-reporter --start-date $LAST_DATE
```

## API Usage

### Python Integration

```python
from git_ai_reporter import AnalysisOrchestrator
from git_ai_reporter.config import Settings
import asyncio
from datetime import datetime, timedelta

async def analyze_custom():
    settings = Settings()  # Loads from environment
    
    # Initialize services (see cli.py for full setup)
    # This is a simplified example
    
    # The orchestrator requires proper service initialization
    # Refer to the source code for complete setup
    
    pass  # Implementation details in source

# For actual usage, see how cli.py sets up the orchestrator
```

## Environment Variables

The following environment variables are supported:

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `MODEL_TIER_1`: Model for commit analysis (default: gemini-2.5-flash)
- `MODEL_TIER_2`: Model for daily summaries (default: gemini-2.5-pro)  
- `MODEL_TIER_3`: Model for narrative generation (default: gemini-2.5-pro)

## Next Steps

- Review [Configuration](configuration.md) for detailed settings
- Set up [Integration](integration.md) with your workflow
- Check [Troubleshooting](troubleshooting.md) for common issues