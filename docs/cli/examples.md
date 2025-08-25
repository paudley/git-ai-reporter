# CLI Examples

Real-world examples and usage patterns for Git AI Reporter. Learn through practical scenarios and copy-paste solutions for common use cases.

## Quick Start Examples

### Basic Analysis

```bash
# Analyze current repository for last 4 weeks (default)
git-ai-reporter

# Quick 1-week analysis with debug output
git-ai-reporter --weeks 1 --debug

# Analyze without using cache (fresh results)
git-ai-reporter --weeks 2 --no-cache
```

### Different Repositories

```bash
# Analyze a different repository
git-ai-reporter --repo-path ~/projects/my-app

# Analyze cloned remote repository
git clone https://github.com/example/project.git temp-analysis
git-ai-reporter --repo-path ./temp-analysis --weeks 4
rm -rf temp-analysis

# Multiple repositories in sequence
for repo in ~/projects/*/; do
    echo "Analyzing $(basename "$repo")"
    git-ai-reporter --repo-path "$repo" --weeks 2 --quiet
done
```

## Date Range Examples

### Specific Date Ranges

```bash
# Analyze January 2025
git-ai-reporter \
  --start-date "2025-01-01" \
  --end-date "2025-01-31"

# Analyze last quarter
git-ai-reporter \
  --start-date "2024-10-01" \
  --end-date "2024-12-31"

# Analyze year-to-date
git-ai-reporter \
  --start-date "2025-01-01" \
  --end-date "$(date +%Y-%m-%d)"
```

### Release-Based Analysis

```bash
# Analyze since last release tag
git-ai-reporter --since-tag v1.2.0

# Analyze between two specific releases
PREV_TAG=$(git describe --tags --abbrev=0 HEAD~1)
CURR_TAG=$(git describe --tags --abbrev=0)
git-ai-reporter \
  --since-tag "$PREV_TAG" \
  --end-date "$(git show -s --format=%ci $CURR_TAG | cut -d' ' -f1)"

# Analyze all releases this year
for tag in $(git tag -l --sort=-version:refname | head -10); do
    echo "Analyzing since $tag"
    git-ai-reporter --since-tag "$tag" --output-dir "releases/$tag" --quiet
done
```

### Time-Based Patterns

```bash
# Weekly analysis (run every Monday)
git-ai-reporter --weeks 1 --output-dir "weekly/$(date +%Y-W%U)"

# Monthly comprehensive analysis
git-ai-reporter --weeks 4 --output-dir "monthly/$(date +%Y-%m)"

# Sprint analysis (2-week sprints)
git-ai-reporter --weeks 2 --output-dir "sprints/sprint-$(date +%Y-%m)"
```

## Output Customization Examples

### Custom File Names and Locations

```bash
# Custom output filenames
git-ai-reporter \
  --news-file "RELEASE_NOTES.md" \
  --changelog-file "CHANGES.md" \
  --daily-updates-file "dev-log.md"

# Organize outputs in directories
mkdir -p reports/$(date +%Y-%m-%d)
git-ai-reporter \
  --output-dir "reports/$(date +%Y-%m-%d)" \
  --weeks 2

# Project-specific organization
git-ai-reporter \
  --news-file "docs/releases/NEWS.md" \
  --changelog-file "docs/CHANGELOG.md" \
  --daily-updates-file "project-management/daily-updates.md"
```

### Timestamped Reports

```bash
# Timestamped filenames
DATE_STR=$(date +%Y-%m-%d)
git-ai-reporter \
  --news-file "NEWS-${DATE_STR}.md" \
  --changelog-file "CHANGELOG-${DATE_STR}.txt" \
  --daily-updates-file "DAILY-${DATE_STR}.md"

# Weekly reports with week numbers
WEEK_NUM=$(date +%Y-W%U)
git-ai-reporter \
  --weeks 1 \
  --output-dir "weekly-reports/${WEEK_NUM}"

# Release candidate documentation
RC_VERSION="v2.1.0-rc1"
git-ai-reporter \
  --since-tag "v2.0.0" \
  --news-file "releases/${RC_VERSION}-NEWS.md" \
  --changelog-file "releases/${RC_VERSION}-CHANGELOG.md"
```

## AI Model Configuration Examples

### Performance-Optimized Setup

```bash
# Fast analysis for development
git-ai-reporter \
  --model-tier-1 "gemini-2.5-flash" \
  --model-tier-2 "gemini-2.5-flash" \
  --model-tier-3 "gemini-2.5-pro" \
  --temperature 0.6 \
  --concurrent 8 \
  --weeks 2

# Maximum speed (use with caution - lower quality)
git-ai-reporter \
  --model-tier-1 "gemini-2.5-flash" \
  --model-tier-2 "gemini-2.5-flash" \
  --model-tier-3 "gemini-2.5-flash" \
  --concurrent 10 \
  --cache \
  --weeks 1
```

### Quality-Optimized Setup

```bash
# Maximum quality for important releases
git-ai-reporter \
  --model-tier-1 "gemini-2.5-pro" \
  --model-tier-2 "gemini-2.5-pro" \
  --model-tier-3 "gemini-2.5-pro" \
  --temperature 0.3 \
  --max-tokens 32768 \
  --concurrent 3 \
  --no-cache

# High-quality stakeholder reports
git-ai-reporter \
  --model-tier-3 "gemini-2.5-pro" \
  --temperature 0.2 \
  --max-tokens-tier-3 32768 \
  --since-tag v1.0.0 \
  --output-dir "./stakeholder-reports"
```

### Balanced Configuration

```bash
# Balanced approach (recommended)
git-ai-reporter \
  --model-tier-1 "gemini-2.5-flash" \
  --model-tier-2 "gemini-2.5-pro" \
  --model-tier-3 "gemini-2.5-pro" \
  --temperature 0.5 \
  --concurrent 5 \
  --cache \
  --weeks 4
```

## Filtering and Scope Examples

### Author-Specific Analysis

```bash
# Analyze specific developer's contributions
git-ai-reporter \
  --author "jane.doe@company.com" \
  --weeks 4 \
  --output-dir "author-reports/jane-doe"

# Team-specific analysis
for author in "alice@team.com" "bob@team.com" "carol@team.com"; do
    git-ai-reporter \
      --author "$author" \
      --weeks 2 \
      --output-dir "team-reports/$(echo $author | cut -d@ -f1)" \
      --quiet
done
```

### Commit Type Filtering

```bash
# Include only substantial changes
git-ai-reporter \
  --trivial-types "style,chore,docs,test" \
  --weeks 4

# Focus on features and bugs only
git-ai-reporter \
  --trivial-types "style,chore,docs,test,refactor,ci" \
  --weeks 2

# Include everything (no filtering)
git-ai-reporter \
  --include-trivial \
  --weeks 2
```

### Repository Scope Examples

```bash
# Large monorepo analysis (selective)
git-ai-reporter \
  --weeks 2 \
  --trivial-types "style,chore,test" \
  --concurrent 3 \
  --timeout 900 \
  --cache

# Small project (comprehensive)
git-ai-reporter \
  --weeks 8 \
  --include-trivial \
  --temperature 0.4 \
  --verbose
```

## Development Workflow Examples

### Daily Development

```bash
#!/bin/bash
# daily-check.sh - Run this every morning
echo "📊 Daily Git Analysis for $(date +%A, %B %d)"

git-ai-reporter \
  --weeks 1 \
  --debug \
  --no-cache \
  --output-dir "./daily-reports/$(date +%Y-%m-%d)" \
  --quiet

echo "✅ Analysis complete. Check daily-reports/ for results."
```

### Sprint Planning

```bash
#!/bin/bash
# sprint-summary.sh - Run at end of each sprint

SPRINT_NAME="${1:-Sprint-$(date +%Y-%U)}"
START_DATE="${2:-$(date -d '2 weeks ago' +%Y-%m-%d)}"

echo "📈 Generating sprint summary: $SPRINT_NAME"

git-ai-reporter \
  --start-date "$START_DATE" \
  --end-date "$(date +%Y-%m-%d)" \
  --output-dir "sprints/$SPRINT_NAME" \
  --model-tier-3 "gemini-2.5-pro" \
  --temperature 0.4 \
  --cache

echo "📝 Sprint summary available in: sprints/$SPRINT_NAME"
```

### Release Preparation

```bash
#!/bin/bash
# release-docs.sh - Generate documentation for releases

RELEASE_TAG="${1:-$(git describe --tags --abbrev=0)}"
PREVIOUS_TAG="${2:-$(git describe --tags --abbrev=0 $RELEASE_TAG^)}"

echo "🚀 Generating release documentation"
echo "   From: $PREVIOUS_TAG"
echo "   To:   $RELEASE_TAG"

# Create release directory
RELEASE_DIR="releases/$RELEASE_TAG"
mkdir -p "$RELEASE_DIR"

# Generate comprehensive analysis
git-ai-reporter \
  --since-tag "$PREVIOUS_TAG" \
  --output-dir "$RELEASE_DIR" \
  --model-tier-1 "gemini-2.5-pro" \
  --model-tier-2 "gemini-2.5-pro" \
  --model-tier-3 "gemini-2.5-pro" \
  --temperature 0.3 \
  --no-cache \
  --verbose

# Copy to standard locations
cp "$RELEASE_DIR/NEWS.md" ./NEWS.md
cp "$RELEASE_DIR/CHANGELOG.txt" ./CHANGELOG.txt

echo "✅ Release documentation ready:"
echo "   📁 Detailed: $RELEASE_DIR/"
echo "   📄 NEWS.md and CHANGELOG.txt updated"
```

## CI/CD Integration Examples

### GitHub Actions

```yaml
# .github/workflows/weekly-analysis.yml
name: Weekly Git Analysis
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for analysis

      - name: Install Git AI Reporter
        run: pip install git-ai-reporter

      - name: Generate weekly analysis
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          git-ai-reporter \
            --weeks 1 \
            --output-dir "reports/week-$(date +%Y-%U)" \
            --cache \
            --quiet

      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: weekly-analysis
          path: reports/
          retention-days: 90

      - name: Create Pull Request
        if: github.event_name == 'schedule'
        uses: peter-evans/create-pull-request@v5
        with:
          title: "docs: weekly development summary $(date +%Y-%U)"
          body: |
            Automated weekly development summary generated by Git AI Reporter.
            
            **Analysis Period:** $(date -d '1 week ago' +%Y-%m-%d) to $(date +%Y-%m-%d)
            **Reports:** Available in the `reports/` directory
          branch: weekly-analysis-$(date +%Y-%U)
          add-paths: |
            NEWS.md
            CHANGELOG.txt
            DAILY_UPDATES.md
            reports/
```

### GitLab CI

```yaml
# .gitlab-ci.yml
weekly-analysis:
  stage: analysis
  image: python:3.12-slim
  before_script:
    - apt-get update && apt-get install -y git
    - pip install git-ai-reporter
  script:
    - |
      git-ai-reporter \
        --weeks 1 \
        --output-dir "reports/$(date +%Y-%U)" \
        --cache \
        --quiet
  artifacts:
    paths:
      - reports/
      - NEWS.md
      - CHANGELOG.txt
      - DAILY_UPDATES.md
    expire_in: 3 months
  only:
    - schedules
    - web
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    triggers {
        cron('0 9 * * 1') // Weekly on Monday
    }
    
    environment {
        GEMINI_API_KEY = credentials('gemini-api-key')
    }
    
    stages {
        stage('Install') {
            steps {
                sh 'pip install git-ai-reporter'
            }
        }
        
        stage('Analyze') {
            steps {
                script {
                    def weekNum = new Date().format('yyyy-ww')
                    sh """
                        git-ai-reporter \\
                            --weeks 1 \\
                            --output-dir reports/week-${weekNum} \\
                            --cache \\
                            --concurrent 3
                    """
                }
            }
        }
        
        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
                archiveArtifacts artifacts: 'NEWS.md,CHANGELOG.txt,DAILY_UPDATES.md'
            }
        }
        
        stage('Notify') {
            steps {
                emailext (
                    subject: "Weekly Git Analysis - Week ${new Date().format('yyyy-ww')}",
                    body: readFile('NEWS.md'),
                    to: "${STAKEHOLDER_EMAILS}"
                )
            }
        }
    }
}
```

## Caching Examples

### Cache Management

```bash
# View cache statistics
git-ai-reporter --cache-stats

# Clear specific cache types
git-ai-reporter --clear-cache commits
git-ai-reporter --clear-cache daily

# Clean expired cache entries
git-ai-reporter --cache-cleanup

# Analysis with fresh cache
git-ai-reporter --clear-cache --weeks 2
```

### Cache Optimization

```bash
# Preload cache with historical data
git-ai-reporter --weeks 8 --cache  # Initial slow run
git-ai-reporter --weeks 1 --cache  # Subsequent fast runs

# Custom cache directory for CI/CD
git-ai-reporter \
  --cache-dir /tmp/git-ai-cache \
  --weeks 2 \
  --cache

# Share cache between team members (network storage)
git-ai-reporter \
  --cache-dir /shared/git-ai-cache \
  --weeks 2 \
  --cache
```

## Advanced Scripting Examples

### Multi-Repository Analysis

```bash
#!/bin/bash
# analyze-all-projects.sh - Analyze multiple repositories

PROJECTS_DIR="$HOME/projects"
REPORTS_BASE="$HOME/git-reports"
DATE_STR=$(date +%Y-%m-%d)

# Create reports directory
mkdir -p "$REPORTS_BASE/$DATE_STR"

# Analyze each repository
for repo_dir in "$PROJECTS_DIR"/*/.git; do
    repo_path=$(dirname "$repo_dir")
    repo_name=$(basename "$repo_path")
    
    echo "📊 Analyzing $repo_name..."
    
    # Skip if not a git repository
    if [ ! -d "$repo_dir" ]; then
        echo "⚠️  Skipping $repo_name (not a git repository)"
        continue
    fi
    
    # Run analysis
    git-ai-reporter \
        --repo-path "$repo_path" \
        --weeks 2 \
        --output-dir "$REPORTS_BASE/$DATE_STR/$repo_name" \
        --quiet \
        --cache \
        --timeout 300
    
    if [ $? -eq 0 ]; then
        echo "✅ $repo_name analysis complete"
    else
        echo "❌ $repo_name analysis failed"
    fi
done

echo "📁 All reports available in: $REPORTS_BASE/$DATE_STR"
```

### Automated Quality Monitoring

```bash
#!/bin/bash
# quality-monitor.sh - Monitor development quality trends

OUTPUT_DIR="quality-reports/$(date +%Y-%m)"
mkdir -p "$OUTPUT_DIR"

# Generate analysis with quality focus
git-ai-reporter \
  --weeks 4 \
  --output-dir "$OUTPUT_DIR" \
  --model-tier-3 "gemini-2.5-pro" \
  --temperature 0.3 \
  --include-trivial \
  --verbose

# Extract metrics for monitoring
CHANGELOG="$OUTPUT_DIR/CHANGELOG.txt"
if [ -f "$CHANGELOG" ]; then
    # Count different types of changes
    FEATURES=$(grep -c "### ✨ Added" "$CHANGELOG" || echo 0)
    FIXES=$(grep -c "### 🐛 Fixed" "$CHANGELOG" || echo 0)
    SECURITY=$(grep -c "### 🔒 Security" "$CHANGELOG" || echo 0)
    
    # Generate metrics report
    cat > "$OUTPUT_DIR/metrics.json" <<EOF
{
    "date": "$(date -I)",
    "period": "4_weeks",
    "features_added": $FEATURES,
    "bugs_fixed": $FIXES,
    "security_improvements": $SECURITY,
    "quality_trend": "$([ $FIXES -lt $FEATURES ] && echo 'positive' || echo 'needs_attention')"
}
EOF
    
    echo "📊 Quality metrics saved to: $OUTPUT_DIR/metrics.json"
fi
```

### Performance Benchmarking

```bash
#!/bin/bash
# benchmark-models.sh - Compare different model configurations

BENCHMARK_DIR="benchmarks/$(date +%Y-%m-%d)"
mkdir -p "$BENCHMARK_DIR"

echo "🏃 Benchmarking different model configurations..."

# Configuration 1: All Flash (Fast)
echo "Testing: All Flash models"
time git-ai-reporter \
  --model-tier-1 "gemini-2.5-flash" \
  --model-tier-2 "gemini-2.5-flash" \
  --model-tier-3 "gemini-2.5-flash" \
  --output-dir "$BENCHMARK_DIR/all-flash" \
  --weeks 1 \
  --no-cache \
  --quiet 2>&1 | tee "$BENCHMARK_DIR/all-flash-timing.txt"

# Configuration 2: Mixed (Balanced)
echo "Testing: Mixed models (default)"
time git-ai-reporter \
  --model-tier-1 "gemini-2.5-flash" \
  --model-tier-2 "gemini-2.5-pro" \
  --model-tier-3 "gemini-2.5-pro" \
  --output-dir "$BENCHMARK_DIR/mixed" \
  --weeks 1 \
  --no-cache \
  --quiet 2>&1 | tee "$BENCHMARK_DIR/mixed-timing.txt"

# Configuration 3: All Pro (Quality)
echo "Testing: All Pro models"
time git-ai-reporter \
  --model-tier-1 "gemini-2.5-pro" \
  --model-tier-2 "gemini-2.5-pro" \
  --model-tier-3 "gemini-2.5-pro" \
  --output-dir "$BENCHMARK_DIR/all-pro" \
  --weeks 1 \
  --no-cache \
  --quiet 2>&1 | tee "$BENCHMARK_DIR/all-pro-timing.txt"

echo "📊 Benchmark results available in: $BENCHMARK_DIR"
echo "Compare the timing.txt files and output quality to choose optimal configuration."
```

## Troubleshooting Examples

### Debugging Failed Runs

```bash
# Maximum debug information
git-ai-reporter \
  --weeks 1 \
  --debug \
  --verbose \
  --no-cache \
  --timeout 600 \
  2>&1 | tee debug.log

# Test configuration before full run
git-ai-reporter --validate-config --debug

# Test API connectivity
git-ai-reporter --test-api --debug

# Check specific date range
git-ai-reporter \
  --dry-run \
  --start-date "2025-01-01" \
  --end-date "2025-01-31" \
  --debug
```

### Handling Large Repositories

```bash
# Large repository strategy
git-ai-reporter \
  --weeks 2 \
  --trivial-types "style,chore,docs,test,ci" \
  --concurrent 3 \
  --timeout 900 \
  --cache \
  --model-tier-1 "gemini-2.5-flash" \
  --model-tier-2 "gemini-2.5-flash" \
  --verbose

# Break down analysis into smaller chunks
for week in {1..4}; do
    start_date=$(date -d "${week} weeks ago" +%Y-%m-%d)
    end_date=$(date -d "$((week-1)) weeks ago" +%Y-%m-%d)
    
    git-ai-reporter \
      --start-date "$start_date" \
      --end-date "$end_date" \
      --output-dir "weekly/week-$week" \
      --cache \
      --quiet
done
```

### Error Recovery

```bash
# Retry with different configuration on failure
git-ai-reporter --weeks 2 || {
    echo "Primary analysis failed, trying with reduced scope..."
    git-ai-reporter \
      --weeks 1 \
      --trivial-types "style,chore,docs,test,ci,refactor" \
      --concurrent 2 \
      --timeout 1200
}

# Graceful fallback for rate limits
git-ai-reporter --weeks 2 --concurrent 5 || {
    echo "Rate limited, retrying with lower concurrency..."
    sleep 60
    git-ai-reporter \
      --weeks 2 \
      --concurrent 2 \
      --timeout 600
}
```

## Integration with Other Tools

### Slack Integration

```bash
#!/bin/bash
# slack-weekly-report.sh
WEBHOOK_URL="$SLACK_WEBHOOK_URL"

# Generate analysis
git-ai-reporter --weeks 1 --output-dir "./temp-analysis"

# Extract key information
if [ -f "./temp-analysis/NEWS.md" ]; then
    SUMMARY=$(head -20 "./temp-analysis/NEWS.md" | tail -10)
    
    # Send to Slack
    curl -X POST -H 'Content-type: application/json' \
      --data "{
        \"text\": \"📊 Weekly Development Summary\",
        \"blocks\": [{
          \"type\": \"section\",
          \"text\": {
            \"type\": \"mrkdwn\",
            \"text\": \"$SUMMARY\"
          }
        }]
      }" \
      "$WEBHOOK_URL"
fi

# Cleanup
rm -rf "./temp-analysis"
```

### Jira Integration

```bash
#!/bin/bash
# jira-sprint-summary.sh

SPRINT_ID="$1"
JIRA_BASE_URL="$JIRA_BASE_URL"
JIRA_TOKEN="$JIRA_TOKEN"

# Generate sprint analysis
git-ai-reporter --weeks 2 --output-dir "./sprint-$SPRINT_ID"

# Update Jira epic with development summary
if [ -f "./sprint-$SPRINT_ID/NEWS.md" ]; then
    SUMMARY=$(cat "./sprint-$SPRINT_ID/NEWS.md")
    
    curl -X PUT \
      -H "Authorization: Bearer $JIRA_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"fields\": {
          \"description\": \"$SUMMARY\"
        }
      }" \
      "$JIRA_BASE_URL/rest/api/2/issue/$SPRINT_ID"
fi
```

## Best Practices from Examples

### Performance Optimization

1. **Use caching for regular runs** - Significant speed improvement after initial run
2. **Choose appropriate models** - Balance cost, speed, and quality
3. **Adjust concurrency** - Match your system capabilities and API limits
4. **Filter trivial commits** - Focus on meaningful changes

### Reliability Patterns

1. **Always use timeouts** - Prevent hanging on network issues
2. **Implement error handling** - Graceful fallback strategies
3. **Validate configuration first** - Use `--validate-config` and `--test-api`
4. **Use dry-run for testing** - Validate scope before expensive operations

### Automation Guidelines

1. **Use quiet mode in scripts** - Reduce noise in automated runs
2. **Store outputs with timestamps** - Track historical analysis
3. **Implement retry logic** - Handle transient failures
4. **Monitor exit codes** - Proper error handling in scripts

## Related Resources

- **[CLI Options Reference →](options.md)** - Complete options documentation
- **[CLI Commands Guide →](commands.md)** - Detailed command explanations
- **[Configuration Guide →](../installation/configuration.md)** - Environment configuration
- **[Integration Guide →](../guide/integration.md)** - CI/CD and workflow integration