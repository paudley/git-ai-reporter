# Quick Start Guide

Get up and running with Git AI Reporter in 5 minutes. This guide walks you through your first analysis from installation to reviewing the generated documentation.

## 🚀 5-Minute Setup

### Step 1: Install Git AI Reporter

Choose your preferred installation method:

=== "PyPI (Recommended)"

    ```bash
    pip install git-ai-reporter
    ```

=== "uv (Faster)"

    ```bash
    pip install uv
    uv pip install git-ai-reporter
    ```

=== "Docker"

    ```bash
    git clone https://github.com/paudley/git-ai-reporter.git
    cd git-ai-reporter
    docker build -t git-ai-reporter .
    ```

### Step 2: Get Your API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the generated key

!!! tip "Free Tier Available"

    Google Gemini offers a generous free tier that's perfect for getting started. You can analyze small to medium repositories without any cost.

### Step 3: Configure Your API Key

=== "Environment Variable"

    ```bash
    export GEMINI_API_KEY="your-api-key-here"
    ```

=== ".env File"

    ```bash
    # Create .env file in your project directory
    echo 'GEMINI_API_KEY="your-api-key-here"' > .env
    ```

=== "Shell Profile (Persistent)"

    ```bash
    echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
    source ~/.bashrc
    ```

### Step 4: Run Your First Analysis

Navigate to any Git repository and run:

```bash
# Analyze the current repository for the last 4 weeks
git-ai-reporter

# Or specify a different repository
git-ai-reporter --repo-path /path/to/your/project

# For a quick test with minimal output
git-ai-reporter --weeks 1 --debug
```

### Step 5: Review Generated Files

After processing completes, you'll find three new files:

```bash
ls -la NEWS.md CHANGELOG.txt DAILY_UPDATES.md
```

- **📰 `NEWS.md`** - Stakeholder-friendly development narrative
- **📋 `CHANGELOG.txt`** - Technical changelog following Keep a Changelog format  
- **📅 `DAILY_UPDATES.md`** - Day-by-day development chronology

## Understanding Your Results

### NEWS.md - Development Narrative

This file tells the story of your development week in human-readable form:

```markdown
# Development News

## Week of January 13-19, 2025

### 🚀 Major Achievements

This week marked a significant milestone in our platform's security 
infrastructure. The development team successfully implemented a 
comprehensive authentication system that enhances user experience 
while maintaining enterprise-grade security standards.

**Key Accomplishments:**
- ✨ Launched OAuth2 integration with major providers
- 🔒 Deployed advanced session management  
- 📊 Enhanced user analytics capabilities

**Technical Highlights:**
The authentication system leverages industry-standard protocols and 
provides seamless integration with existing user workflows. Performance 
testing shows 40% improvement in login response times.

### 📈 Development Velocity
- **Commits Analyzed:** 47 commits across 8 contributors
- **Files Changed:** 156 files with 2,340 lines added
- **Major Features:** 3 completed, 2 in progress
```

### CHANGELOG.txt - Technical Changes

Structured technical documentation following [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [Unreleased]

### ✨ Added
- OAuth2 authentication integration with Google and GitHub providers
- JWT token validation middleware for secure API access
- Redis-based session management for improved scalability
- User profile management endpoints with avatar support

### 🐛 Fixed  
- Resolved memory leak in user session cleanup process
- Fixed race condition in concurrent authentication requests
- Corrected timezone handling in user activity logs

### ♻️ Changed
- Upgraded authentication library to v2.1.4 for security patches
- Improved error handling in login flow with user-friendly messages
- Optimized database queries for user lookup operations

### 🗑️ Deprecated
- Legacy password reset endpoint (use /api/v2/auth/reset instead)

### ❌ Removed
- Deprecated social login providers (Facebook, Twitter legacy APIs)
```

### DAILY_UPDATES.md - Development Log

Day-by-day development activities:

```markdown
# Daily Development Updates

## January 15, 2025

**Focus Area:** Authentication System Implementation

### Morning Session (9:00 AM - 12:00 PM)
- Integrated OAuth2 client library with Google provider
- Configured callback URL routing and error handling
- Set up development environment OAuth app credentials

### Afternoon Session (1:00 PM - 5:00 PM)
- Implemented JWT token generation and validation logic
- Added middleware for protecting authenticated API routes
- Created user session models with Redis backend integration
- Updated API documentation for new authentication endpoints

**Files Modified:** 12 files (+287 lines, -45 lines)
**Tests Added:** 8 new test cases for authentication flows
**Documentation:** Updated API reference and integration guide

**Tomorrow's Priorities:**
- Complete user profile management endpoints
- Implement password reset functionality  
- Add comprehensive integration tests for full auth flow

---

## January 14, 2025

**Focus Area:** Project Setup and Planning

### Development Activities
- Initialized authentication module structure
- Researched OAuth2 integration patterns and security considerations
- Set up development database with user tables
- Created initial authentication service interfaces

**Planning Session:**
- Defined authentication system requirements with product team
- Selected technology stack: OAuth2 + JWT + Redis
- Established security review checkpoints
- Planned integration with existing user management system

**Files Modified:** 6 files (+156 lines, -12 lines)
```

## Common First-Run Scenarios

### Scenario 1: Small Project (< 50 commits)

```bash
# Perfect for small projects - quick and comprehensive
git-ai-reporter --weeks 2

# Typical output:
# ✅ Found 23 commits across 2 weeks
# ✅ Analyzing commits (Tier 1): 23/23 complete
# ✅ Generating daily summaries (Tier 2): 14/14 days
# ✅ Creating final narratives (Tier 3): Complete
# 📝 Generated: NEWS.md, CHANGELOG.txt, DAILY_UPDATES.md
```

### Scenario 2: Medium Project (50-200 commits)

```bash
# Good balance of depth and processing time
git-ai-reporter --weeks 4

# Expected processing: 2-5 minutes
# Focus on meaningful changes with intelligent filtering
```

### Scenario 3: Large Project (200+ commits)

```bash
# Start with shorter timeframe for initial test
git-ai-reporter --weeks 1

# Then expand to full analysis
git-ai-reporter --weeks 4 --no-cache  # Force fresh analysis
```

## Customizing Your First Analysis

### Focus on Specific Time Periods

```bash
# Specific date range
git-ai-reporter --start-date "2025-01-01" --end-date "2025-01-31"

# Last N weeks
git-ai-reporter --weeks 6

# Since last release tag
git-ai-reporter --since-tag v1.0.0
```

### Adjusting Output Detail

```bash
# More detailed analysis (slower, higher quality)
git-ai-reporter --weeks 2 --temperature 0.3

# Faster analysis (less detail)
git-ai-reporter --weeks 2 --temperature 0.7
```

### Debug Mode for Troubleshooting

```bash
# See what's happening under the hood
git-ai-reporter --weeks 1 --debug

# Dry run - see what would be analyzed without making API calls
git-ai-reporter --weeks 1 --dry-run
```

## Troubleshooting First Run

### Common Issues and Solutions

??? failure "API Key Not Found"

    **Error:** `GEMINI_API_KEY environment variable not set`
    
    **Solutions:**
    ```bash
    # Check if variable is set
    echo $GEMINI_API_KEY
    
    # Set for current session
    export GEMINI_API_KEY="your-key-here"
    
    # Or create .env file
    echo 'GEMINI_API_KEY="your-key"' > .env
    ```

??? failure "No Git Repository"

    **Error:** `Not a git repository or no commits found`
    
    **Solutions:**
    ```bash
    # Verify you're in a Git repository
    git status
    
    # Or specify repository path
    git-ai-reporter --repo-path /path/to/your/repo
    
    # Check if repository has commits
    git log --oneline -n 5
    ```

??? failure "Permission Denied"

    **Error:** `Permission denied when writing output files`
    
    **Solutions:**
    ```bash
    # Check directory permissions
    ls -la .
    
    # Use different output directory
    git-ai-reporter --output-dir ~/git-reports
    
    # Or run with appropriate permissions
    sudo git-ai-reporter  # Not recommended
    ```

??? failure "API Rate Limits"

    **Error:** `API rate limit exceeded`
    
    **Solutions:**
    ```bash
    # Use smaller time window
    git-ai-reporter --weeks 1
    
    # Enable caching to avoid re-processing
    git-ai-reporter --cache-enabled
    
    # Wait and retry (rate limits reset)
    sleep 60 && git-ai-reporter
    ```

### Performance Expectations

| Repository Size | Commits | Processing Time | API Calls |
|----------------|---------|-----------------|-----------|
| Small | 1-50 | 30-90 seconds | 50-70 |
| Medium | 51-200 | 2-5 minutes | 200-250 |
| Large | 201-500 | 5-15 minutes | 500-600 |
| Very Large | 500+ | 15+ minutes | 500+ |

!!! tip "First Run is Slowest"

    The first analysis takes the longest because nothing is cached. Subsequent runs on the same repository are much faster due to intelligent caching.

## Next Steps After First Run

### 1. Review and Understand Output

Take time to read through each generated file:

- **📰 NEWS.md** - Share with stakeholders and project managers
- **📋 CHANGELOG.txt** - Include in release notes and documentation  
- **📅 DAILY_UPDATES.md** - Use for team retrospectives and planning

### 2. Customize Configuration

Create a `.env` file to customize behavior:

```bash
cat > .env << EOF
GEMINI_API_KEY="your-key"
MODEL_TIER_1="gemini-2.5-flash"
MODEL_TIER_2="gemini-2.5-pro"
MODEL_TIER_3="gemini-2.5-pro"
TEMPERATURE=0.5
TRIVIAL_COMMIT_TYPES="style,chore"
EOF
```

### 3. Set Up Regular Analysis

Add to your workflow:

```bash
# Weekly analysis (recommended)
git-ai-reporter --weeks 1

# Monthly comprehensive review
git-ai-reporter --weeks 4

# Release preparation
git-ai-reporter --since-tag $(git describe --tags --abbrev=0)
```

### 4. Integrate with Your Workflow

Consider automation options:

- **Git Hooks** - Automatic analysis on push
- **CI/CD Integration** - Analysis in your pipeline  
- **Scheduled Jobs** - Weekly automated reports
- **Release Process** - Include in release preparation

## Example Workflows

### Development Team Workflow

```bash
# Monday morning: Review last week
git-ai-reporter --weeks 1

# Before releases: Complete analysis  
git-ai-reporter --since-tag v1.2.0

# Monthly retrospective: Comprehensive review
git-ai-reporter --weeks 4
```

### Product Manager Workflow

```bash
# Focus on stakeholder narrative
git-ai-reporter --weeks 2
# -> Share NEWS.md with stakeholders

# Track specific features
git-ai-reporter --start-date "2025-01-01" --keywords "authentication,api"
```

### DevOps Integration

```bash
# Automated in CI/CD
git-ai-reporter --weeks 1 --output-dir ./reports
# -> Archive reports as build artifacts
```

## Learning Resources

After your successful first run:

1. **[Configuration Guide →](../installation/configuration.md)** - Customize behavior and settings
2. **[CLI Reference →](../cli/options.md)** - Explore all available options
3. **[Advanced Usage →](advanced-usage.md)** - Power user features
4. **[Integration Guide →](integration.md)** - Automate with CI/CD

## Getting Help

If you encounter issues:

- **[FAQ →](../about/faq.md)** - Common questions and solutions
- **[Troubleshooting →](troubleshooting.md)** - Detailed problem solving
- **[GitHub Discussions](https://github.com/paudley/git-ai-reporter/discussions)** - Community support
- **[GitHub Issues](https://github.com/paudley/git-ai-reporter/issues)** - Bug reports

---

!!! success "Congratulations!"

    You've successfully completed your first Git AI Reporter analysis! The generated documentation provides valuable insights into your project's development story.

!!! tip "Pro Tip"

    Run Git AI Reporter regularly (weekly or bi-weekly) to maintain up-to-date documentation and track development progress over time.