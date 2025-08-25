---
title: Core Concepts
description: Understanding how Git AI Reporter works
---

# Core Concepts

This page explains the fundamental concepts behind Git AI Reporter and how it transforms your Git history into intelligent documentation.

## Three-Tier AI Architecture

Git AI Reporter uses a sophisticated three-tier AI architecture that optimizes for both cost and quality:

### Tier 1: Analyzer (gemini-2.5-flash)
- **Purpose**: High-volume, fast commit analysis
- **Function**: Processes individual commits to extract key changes
- **Optimization**: Speed and cost-efficiency
- **Token Usage**: ~1000 tokens per commit

### Tier 2: Synthesizer (gemini-2.5-pro)
- **Purpose**: Pattern recognition and daily consolidation
- **Function**: Identifies themes and patterns across commits
- **Optimization**: Balanced quality and performance
- **Token Usage**: ~5000 tokens per day

### Tier 3: Narrator (gemini-2.5-pro)
- **Purpose**: Final document generation
- **Function**: Creates polished, audience-aware narratives
- **Optimization**: Maximum quality and coherence
- **Token Usage**: ~10000 tokens per week

## Three-Lens Analysis Strategy

Git AI Reporter analyzes your repository through three complementary perspectives:

### 1. Micro View (Commit-Level)
Individual commit analysis with intelligent filtering:
- Filters out noise (docs, style changes)
- Preserves meaningful changes
- Maintains commit context
- Each commit analyzed independently

### 2. Mezzo View (Daily Consolidation)
Net changes per 24-hour period:
- Groups commits by date
- Calculates net changes between days
- Reduces redundancy
- Identifies daily patterns

### 3. Macro View (Weekly Overview)
Complete context for narrative generation:
- Single diff for entire period
- Big-picture perspective
- Strategic insights
- Comprehensive understanding

## Intelligent Filtering

Not all commits are created equal. Git AI Reporter intelligently filters out noise:

### Filtered Commit Prefixes
- `chore:` - Maintenance tasks
- `docs:` - Documentation updates
- `style:` - Code formatting
- `test:` - Test-only changes
- `ci:` - CI/CD configuration

### Filtered File Patterns
- `*.md` - Markdown documentation
- `docs/` - Documentation directories
- `.github/` - GitHub configuration
- `*.lock` - Lock files
- `*.log` - Log files

## Caching Strategy

Smart caching minimizes API costs while ensuring fresh results:

### Cache Layers
1. **Commit Analysis Cache**
   - Key: SHA + prompt hash
   - TTL: 30 days
   - Hit rate: ~70%

2. **Daily Summary Cache**
   - Key: Date range + commits hash
   - TTL: 7 days
   - Hit rate: ~50%

3. **Weekly Narrative Cache**
   - Key: Week identifier + content hash
   - TTL: 3 days
   - Hit rate: ~30%

### Cache Benefits
- **Cost Reduction**: 70% fewer API calls
- **Speed**: 5-10x faster for cached content
- **Consistency**: Reproducible results
- **Flexibility**: Manual cache clearing available

## Output Generation

Git AI Reporter generates three complementary documentation types:

### NEWS.md - Development Narrative
- **Audience**: Stakeholders, non-technical readers
- **Style**: Story-driven, accessible prose
- **Content**: Major features, improvements, impact
- **Update**: Overwrites existing file

### CHANGELOG.txt - Structured Changes
- **Audience**: Developers, technical users
- **Style**: Keep a Changelog format
- **Content**: Categorized changes with emojis
- **Update**: Merges with existing [Unreleased] section

### DAILY_UPDATES.md - Activity Summary
- **Audience**: Team members, managers
- **Style**: Chronological, detailed
- **Content**: Day-by-day development activity
- **Update**: Appends new days

## Async Processing

Performance optimization through concurrent processing:

### Parallel Operations
- Multiple commits analyzed simultaneously
- Concurrent API calls with semaphore control
- Async file I/O operations
- Batch processing for efficiency

### Resource Management
- Maximum 5 concurrent workers (configurable)
- Automatic rate limit handling
- Exponential backoff with retry
- Memory-efficient streaming

## Error Handling

Robust error handling ensures reliability:

### Retry Strategy
- Exponential backoff for API errors
- Maximum 3 retry attempts
- Automatic rate limit detection
- Graceful degradation

### Recovery Mechanisms
- Cache fallback for API failures
- Partial analysis on Git errors
- Alternative paths for file errors
- User-friendly error messages

## Best Practices

To get the most out of Git AI Reporter:

### Commit Messages
- Use conventional commits format
- Write descriptive messages
- Include context and rationale
- Group related changes

### Repository Organization
- Maintain clean Git history
- Use meaningful branch names
- Tag releases appropriately
- Keep commits atomic

### Usage Patterns
- Run weekly for best results
- Use date ranges for specific periods
- Let caching work automatically
- Review generated content

## Advanced Concepts

### Prompt Engineering
Git AI Reporter uses carefully crafted prompts:
- Role-specific instructions
- Context-aware generation
- Audience targeting
- Style consistency

### JSON Handling
The "Airlock" pattern for robust LLM output:
- Tolerant parsing for imperfect JSON
- Safe serialization for all types
- Graceful error recovery
- Format validation

### Changelog Merging
Intelligent merging preserves existing content:
- Parses existing CHANGELOG.txt
- Identifies [Unreleased] section
- Merges new changes by category
- Maintains format compliance

## Next Steps

- Learn about [Basic Usage](basic-usage.md)
- Explore [Advanced Features](advanced-usage.md)
- Configure [Settings](configuration.md)
- Understand [Architecture](../architecture/index.md)