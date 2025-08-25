---
title: API Reference
description: Python API documentation for Git AI Reporter
---

# API Reference

Complete Python API documentation for Git AI Reporter. All documentation is automatically generated from the source code using mkdocstrings.

## Overview

Git AI Reporter provides a comprehensive Python API for integrating repository analysis into your applications. The API is organized into several key modules:

| Module | Description |
|--------|------------|
| [**Core**](core.md) | Data models, configuration, and constants |
| [**Analysis**](analysis.md) | Git repository analysis engine |
| [**Services**](services.md) | AI service integration (Gemini) |
| [**Orchestration**](orchestration.md) | Workflow coordination and pipeline |
| [**Summaries**](summaries.md) | AI prompt templates and strategies |
| [**Writing**](writing.md) | Document generation and output |
| [**Utils**](utils.md) | Utility functions and helpers |
| [**Cache**](cache.md) | Caching system for API responses |
| [**Plugins**](plugins.md) | Plugin system and extensions |

## Quick Start

```python
from git_ai_reporter import AnalysisOrchestrator
from git_ai_reporter.config import Settings
from datetime import datetime, timedelta

# Configure settings
settings = Settings(
    gemini_api_key="your-api-key",
    repo_path="/path/to/repo"
)

# Create orchestrator
orchestrator = AnalysisOrchestrator(settings)

# Run analysis
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

await orchestrator.analyze_repository(
    repo_path="/path/to/repo",
    start_date=start_date,
    end_date=end_date
)
```

## Module Structure

```
git_ai_reporter/
├── __init__.py          # Package exports
├── cli.py               # CLI application
├── config.py            # Configuration management
├── models.py            # Data models
├── analysis/
│   └── git_analyzer.py  # Git analysis
├── cache/
│   └── manager.py       # Cache management
├── orchestration/
│   └── orchestrator.py  # Workflow coordination
├── services/
│   └── gemini.py        # AI services
├── summaries/
│   ├── commit.py        # Commit prompts
│   ├── daily.py         # Daily prompts
│   └── weekly.py        # Weekly prompts
├── utils/
│   ├── file_helpers.py  # File utilities
│   ├── git_command_runner.py  # Git commands
│   └── json_helpers.py  # JSON handling
└── writing/
    └── artifact_writer.py  # Document generation
```

## Import Guide

### Main Entry Points

```python
# High-level orchestration
from git_ai_reporter import AnalysisOrchestrator

# Configuration
from git_ai_reporter.config import Settings

# Data models
from git_ai_reporter.models import (
    CommitAnalysis,
    DailySummary,
    WeeklySummary,
    Change,
    CommitCategory
)

# Git analysis
from git_ai_reporter.analysis import GitAnalyzer

# AI services
from git_ai_reporter.services import GeminiClient

# Document writing
from git_ai_reporter.writing import ArtifactWriter
```

## See Also

- [CLI Reference](../cli/index.md) - Command-line interface documentation
- [Architecture](../architecture/index.md) - System design and patterns
- [User Guide](../guide/index.md) - Usage tutorials and examples
- [Development](../development/index.md) - Contributing and development setup