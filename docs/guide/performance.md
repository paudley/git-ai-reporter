---
title: Performance Optimization
description: Optimizing Git AI Reporter for speed and efficiency
---

# Performance Optimization

Learn how to optimize Git AI Reporter for better performance and lower costs.

## Performance Overview

Git AI Reporter's performance depends on several factors:

- **Repository size**: Number of commits, files, and contributors
- **Date range**: Days of history to analyze
- **AI model selection**: Trade-offs between speed and quality
- **Caching strategy**: Reuse of previous analyses
- **Network latency**: API response times
- **System resources**: CPU, memory, and disk I/O

## Optimization Strategies

### 1. Intelligent Caching

#### Enable Persistent Cache

```bash
# Use cache directory (default: .git-report-cache)
git-ai-reporter --cache-dir ~/.cache/git-ai-reporter

# The cache stores API responses to avoid repeated calls
# for the same commits
```

#### Cache Management

```bash
# Show cache statistics
git-ai-reporter cache --show

# Clear cache when needed
git-ai-reporter cache --clear

# Force re-analysis without cache
git-ai-reporter --no-cache
```

### 2. Model Optimization

#### Choose Appropriate Models

The tool uses a three-tier model system:
- **Tier 1 (Commit Analysis)**: Uses gemini-2.5-flash by default for speed
- **Tier 2 (Daily Summaries)**: Uses gemini-2.5-pro for quality
- **Tier 3 (Narrative Generation)**: Uses gemini-2.5-pro for quality

You can configure these via environment variables:

```bash
export MODEL_TIER_1="gemini-2.5-flash"  # Fast, cheaper
export MODEL_TIER_2="gemini-2.5-pro"    # Balanced
export MODEL_TIER_3="gemini-2.5-pro"    # Quality
```

### 3. Date Range Optimization

#### Analyze Smaller Time Periods

```bash
# Analyze 1 week instead of 4 (default)
git-ai-reporter --weeks 1

# Analyze specific date range
git-ai-reporter --start-date 2025-01-01 --end-date 2025-01-07
```

### 4. Debug Mode

Use debug mode to understand what's happening:

```bash
# Enable verbose logging to see what's being processed
git-ai-reporter --debug
```

## Cost Optimization

### API Cost Reduction Strategies

1. **Use Caching**: The cache prevents redundant API calls for unchanged commits
2. **Reduce Time Range**: Analyze shorter periods when possible
3. **Use Flash Model for Tier 1**: The default configuration already optimizes for cost

### Cost Considerations

- **Gemini 2.5 Flash**: Lower cost, faster response, suitable for high-volume analysis
- **Gemini 2.5 Pro**: Higher quality, more expensive, used for summaries and narratives
- **Caching**: Significantly reduces costs by avoiding repeated API calls

## Monitoring Performance

### Built-in Features

```bash
# Debug mode shows timing information
git-ai-reporter --debug

# Cache statistics show hit/miss rates
git-ai-reporter cache --show
```

## Best Practices

### 1. Development vs Production

```bash
# Development: Quick iteration with short time ranges
git-ai-reporter --weeks 1 --debug

# Production: Full analysis with caching
git-ai-reporter --weeks 4
```

### 2. Large Repository Strategy

For repositories with thousands of commits:

1. **Start with shorter time ranges** to test configuration
2. **Use caching** to avoid re-analyzing unchanged commits
3. **Monitor memory usage** with system tools
4. **Consider analyzing in chunks** if memory is limited

### 3. CI/CD Optimization

```yaml
# GitHub Actions with caching
- name: Cache Git AI Reporter
  uses: actions/cache@v4
  with:
    path: .git-report-cache
    key: ${{ runner.os }}-git-ai-${{ hashFiles('**/*.py') }}
    restore-keys: |
      ${{ runner.os }}-git-ai-

- name: Generate Report
  run: |
    git-ai-reporter --weeks 1
```

## Performance Troubleshooting

### Slow Analysis

1. **Check cache usage**: Ensure cache is enabled and working
2. **Reduce time range**: Start with 1 week and increase gradually
3. **Enable debug mode**: See where time is being spent
4. **Check network**: API calls may be slow due to network issues

### High Memory Usage

1. **Reduce time range**: Process fewer commits at once
2. **Monitor with system tools**: Use `top` or `htop` to watch memory
3. **Close other applications**: Free up system memory

### API Errors

1. **Check API key**: Ensure GEMINI_API_KEY is set correctly
2. **Check rate limits**: You may be hitting API rate limits
3. **Enable debug mode**: See detailed error messages
4. **Use cache**: Reduce API calls with caching

## Next Steps

- Review [Troubleshooting Guide](troubleshooting.md)
- Read [Frequently Asked Questions](faq.md)
- Learn about [Configuration](configuration.md)