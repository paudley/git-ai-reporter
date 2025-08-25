# Prompt Fitting Module

## Purpose

The `prompt_fitting` module is a dedicated system for fitting large content into LLM token limits while maintaining **100% data integrity**. This is a critical requirement for git-ai-reporter's commitment to complete commit analysis without data loss.

## Architecture

```
src/git_ai_reporter/prompt_fitting/
├── __init__.py              # Module exports and public API
├── prompt_fitting.py        # Core implementation with all strategies
├── README.md               # Module overview (this file)
└── PROMPT_FITTING.md       # Detailed documentation and usage guide
```

## Core Components

### 1. **PromptFitter** - Main Interface
The primary class for fitting content using optimal strategies based on content type.

### 2. **Strategy Implementations**
- **OverlappingChunksFitter**: For summaries and narratives
- **DiffTruncationFitter**: For git diffs with structure preservation  
- **LogCompressionFitter**: For commit logs with overlapping chunk preservation

### 3. **Configuration & Results**
- **PromptFittingConfig**: Configurable parameters for all strategies
- **FittingResult**: Comprehensive metrics and validation results

## Key Features

- **Zero Data Loss**: All strategies preserve 100% of original information
- **Validation Built-in**: Automatic verification of data preservation
- **Research-Based**: Implements current best practices in prompt engineering
- **Extensible**: Easy to add new strategies for different content types
- **Production-Ready**: Comprehensive error handling and monitoring

## Quick Start

```python
from git_ai_reporter.prompt_fitting import PromptFitter, PromptFittingConfig, ContentType

# Basic usage
config = PromptFittingConfig(max_tokens=100000)
fitter = PromptFitter(config, token_counter)

result = await fitter.fit_content(
    content=large_content,
    content_type=ContentType.GIT_DIFF,
    target_tokens=80000
)

print(f"Strategy: {result.strategy_used}")
print(f"Compression: {result.compression_ratio:.2f}")
print(f"Data preserved: {result.data_preserved}")
```

## Integration Points

This module is designed to replace all existing ad-hoc token management throughout the codebase:

- **GeminiClient**: Replace chunking and truncation logic
- **Orchestrator**: Replace diff size limits and any data-losing optimizations
- **Any service**: That needs to fit content into token limits

## Data Integrity Guarantee

This module enforces the mandatory project requirement:

> **CRITICAL: NO DATA LOSS OPTIMIZATIONS ALLOWED**
> 
> **ABSOLUTE REQUIREMENT:** Every single commit MUST be analyzed in all cases

All strategies are designed and validated to meet this requirement while efficiently working within LLM constraints.

## Documentation

See `PROMPT_FITTING.md` for detailed documentation, usage examples, and integration guidelines.