---
title: Frequently Asked Questions
description: Common questions about Git AI Reporter
---

# Frequently Asked Questions

Find answers to common questions about Git AI Reporter.

## General Questions

### What is Git AI Reporter?

Git AI Reporter is an AI-powered tool that analyzes Git repository history and generates human-readable documentation. It creates three types of outputs:

- **NEWS.md**: Executive summaries for stakeholders
- **CHANGELOG.txt**: Technical change logs for developers
- **DAILY_UPDATES.md**: Daily development activity reports

### How does it work?

Git AI Reporter uses a three-tier AI architecture:

1. **Tier 1 (Analyzer)**: Analyzes individual commits using Gemini Flash
2. **Tier 2 (Synthesizer)**: Identifies patterns and creates daily summaries using Gemini Pro
3. **Tier 3 (Narrator)**: Generates final documentation using Gemini Pro

The tool examines commits through three lenses: individual commits, daily consolidation, and weekly overview.

### What makes it different from other changelog generators?

Unlike traditional changelog generators that simply format commit messages, Git AI Reporter:

- **Understands context**: AI analyzes code changes, not just messages
- **Generates narratives**: Creates human-readable stories, not just lists
- **Filters noise**: Automatically excludes trivial changes
- **Multi-audience**: Produces both technical and non-technical documentation
- **Intelligent caching**: Minimizes API costs through smart caching

### Which Git providers are supported?

Git AI Reporter works with any Git repository, including:

- GitHub
- GitLab
- Bitbucket
- Azure DevOps
- Self-hosted Git servers
- Local repositories

The tool operates directly on the Git repository, not through provider APIs.

## Installation & Setup

### What are the system requirements?

- **Python**: 3.12 or higher
- **Git**: 2.25 or higher
- **Operating System**: Windows, macOS, Linux
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Disk Space**: 500MB for cache (configurable)

### How do I get a Gemini API key?

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and set it as an environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

### Can I use it without an API key?

No, Git AI Reporter requires a Gemini API key to function. The AI analysis is core to its functionality and cannot be disabled.

### Is there a Docker image available?

Not officially, but you can create one:

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y git
RUN pip install git-ai-reporter
ENTRYPOINT ["git-ai-reporter"]
```

## Usage Questions

### How often should I run it?

It depends on your team's needs:

- **Active development**: Daily or every few days
- **Regular development**: Weekly
- **Maintenance mode**: Monthly
- **Before releases**: Always

### Can I analyze specific branches?

Currently, Git AI Reporter analyzes the currently checked out branch. To analyze different branches, check them out first:
```bash
git checkout feature/new-ui
git-ai-reporter
```

### Can I analyze multiple repositories at once?

Not directly, but you can script it:
```bash
for repo in repo1 repo2 repo3; do
  cd $repo
  git-ai-reporter --days 7 --output-dir ../reports/$repo/
  cd ..
done
```

### How do I exclude certain commits?

Currently, filtering is handled automatically by the tool's built-in logic. Advanced filtering options like author and path filtering are planned for future releases.

### Can I customize the output format?

Currently, Git AI Reporter generates three fixed formats: NEWS.md, CHANGELOG.txt, and DAILY_UPDATES.md. Templates and custom output formats are planned for future releases.

## Cost & Performance

### How much does it cost to run?

Costs depend on repository size and model selection:

Costs depend on repository size and usage patterns. Use caching to minimize API calls and reduce costs.
| Medium | 500 | $0.50 - $1.00 |
| Large | 5000 | $5.00 - $10.00 |

Use caching and the Flash model to reduce costs.

### How can I reduce API costs?

1. **Enable caching** (70% cost reduction):
   ```bash
   git-ai-reporter --cache-dir .cache
   ```

2. **Use Flash model** (10x cheaper):
   ```bash
   git-ai-reporter --model-tier1 gemini-2.5-flash
   ```

3. **Filter noise**:
   ```bash
   git-ai-reporter --exclude-merge-commits
   ```

4. **Process less frequently**: Weekly instead of daily

### How long does analysis take?

Typical processing times:

| Commits | Cached | Uncached |
|---------|--------|----------|
| 100 | 30s | 2m |
| 1,000 | 2m | 15m |
| 10,000 | 10m | 2h |

### Can I speed up processing?

Yes, several optimization options:

```bash
# Increase parallel workers
export GIT_AI_MAX_WORKERS=10

# Use faster model
git-ai-reporter --model-tier1 gemini-2.5-flash

# Enable streaming
git-ai-reporter --stream
```

## Output & Integration

### Where are the files saved?

By default, files are saved in the current directory:
- `NEWS.md`
- `CHANGELOG.txt`
- `DAILY_UPDATES.md`

Specify a different directory:
```bash
git-ai-reporter --output-dir docs/updates/
```

### Can I commit the generated files?

Yes, but consider:

- **Pros**: Version history, easy access, PR reviews
- **Cons**: Repository size, merge conflicts

Recommended approach:
```bash
# Add to .gitignore for regular runs
echo "DAILY_UPDATES.md" >> .gitignore

# Commit only for releases
git add NEWS.md CHANGELOG.txt
git commit -m "docs: Update release documentation"
```

### How do I integrate with CI/CD?

See the [Integration Guide](integration.md) for detailed examples. Quick GitHub Actions example:

```yaml
- name: Generate Report
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  run: |
    pip install git-ai-reporter
    git-ai-reporter --days 7
```

### Can I send reports to Slack/Email?

Not built-in, but you can script it. See [Integration Guide](integration.md) for examples.

## Troubleshooting

### Why are my outputs empty?

Common causes:
1. No commits in date range
2. All commits filtered out
3. API key issues
4. Network problems

Debug with:
```bash
git-ai-reporter --verbose --days 30
```

### Why is it skipping commits?

Git AI Reporter filters out:
- Commits with prefixes: `chore:`, `docs:`, `style:`, `test:`, `ci:`
- Files matching patterns: `*.md`, `*.lock`, `*.log`
- Documentation directories: `docs/`, `.github/`

Override with configuration.

### How do I handle large repositories?

For repositories with >10,000 commits:

1. Process in chunks:
   ```bash
   git-ai-reporter --days 7  # Instead of --days 365
   ```

2. Use configuration optimizations:
   ```json
   {
     "performance": {
       "max_workers": 10,
       "stream_mode": true
     }
   }
   ```

3. Enable aggressive caching

### What if the API is down?

Git AI Reporter will retry with exponential backoff. If the API remains unavailable:

1. Check [Google Cloud Status](https://status.cloud.google.com/)
2. Verify your API key
3. Try again later
4. Use cached results if available

## Advanced Questions

### Can I use different AI models?

Currently, only Google Gemini models are supported:
- `gemini-2.5-flash` (fast, cheap)
- `gemini-2.5-pro` (slower, higher quality)

### Is there a Python API?

Yes, you can use it programmatically:

```python
from git_ai_reporter import AnalysisOrchestrator
from git_ai_reporter.config import Settings

settings = Settings(gemini_api_key="your-key")
orchestrator = AnalysisOrchestrator(settings)

# Run analysis
result = await orchestrator.analyze_repository(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31)
)
```

### Can I extend it with plugins?

Not officially supported, but you can:
1. Fork the repository
2. Modify the code
3. Use the Python API
4. Create wrapper scripts

### Does it support monorepos?

Yes, use path filtering:

```bash
# Analyze specific package
git-ai-reporter --path "packages/frontend/"

# Analyze multiple packages
git-ai-reporter --path "packages/api/" --path "packages/web/"
```

### Can I analyze private repositories?

Yes, Git AI Reporter works with any Git repository you have local access to. It doesn't require repository hosting provider APIs.

## Security & Privacy

### Is my code sent to Google?

Only the following is sent to Gemini API:
- Commit messages
- Commit diffs (code changes)
- File paths

Your full codebase is never uploaded.

### How is sensitive data handled?

Git AI Reporter doesn't automatically filter sensitive data. You should:

1. Review generated outputs before sharing
2. Use `.gitignore` patterns to exclude sensitive files
3. Configure filters for sensitive paths
4. Never commit API keys

### Is the API key stored securely?

The API key is only stored in environment variables. Never commit it to version control. Use secret management tools in CI/CD.

### Can I use it with proprietary code?

Yes, but review Google's [Gemini API Terms of Service](https://ai.google.dev/terms) regarding data usage and retention.

## Common Errors

### "GEMINI_API_KEY environment variable not set"

Set your API key:
```bash
export GEMINI_API_KEY="your-key-here"
```

### "Not a git repository"

Ensure you're in a Git repository:
```bash
git status
```

Or specify the repository path:
```bash
git-ai-reporter --repo /path/to/repo
```

### "No commits found in the specified date range"

Check for commits:
```bash
git log --since="7 days ago" --oneline
```

Try a wider date range:
```bash
git-ai-reporter --days 30
```

### "API rate limit exceeded"

Wait for rate limit reset or:
1. Use caching
2. Process smaller date ranges
3. Use multiple API keys

## Getting Help

### Where can I report bugs?

Report issues on [GitHub Issues](https://github.com/poissonconsulting/git-ai-reporter/issues)

### How can I contribute?

See [CONTRIBUTING.md](https://github.com/poissonconsulting/git-ai-reporter/blob/main/CONTRIBUTING.md)

### Is there community support?

- GitHub Discussions
- Stack Overflow tag: `git-ai-reporter`
- Discord server (if available)

### Can I get commercial support?

Contact the maintainers through GitHub for commercial support options.

## Future Development

### What features are planned?

Check the [project roadmap](https://github.com/poissonconsulting/git-ai-reporter/projects) for planned features.

### Will other AI providers be supported?

Potentially. OpenAI, Anthropic, and local models are being considered.

### Will there be a GUI?

A web interface is under consideration but not currently planned.

## Next Steps

- Read the [Basic Usage Guide](basic-usage.md)
- Explore [Advanced Features](advanced-usage.md)
- Review [Configuration Options](configuration.md)
- Check [Troubleshooting Guide](troubleshooting.md)