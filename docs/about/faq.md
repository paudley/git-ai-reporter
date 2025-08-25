# Frequently Asked Questions

Common questions and answers about Git AI Reporter, its features, and usage.

## Getting Started

??? question "What is Git AI Reporter and what does it do?"

    Git AI Reporter is an AI-driven tool that automatically generates comprehensive documentation from your Git repository history. It analyzes commits, identifies patterns, and creates professional reports including:
    
    - **NEWS.md** - Narrative development summaries for stakeholders
    - **CHANGELOG.txt** - Structured changelog entries with emoji categorization
    - **DAILY_UPDATES.md** - Daily development activity summaries
    
    It uses Google's Gemini AI models with a three-tier architecture to transform technical Git activity into human-readable documentation.

??? question "How is this different from automated changelog generators?"

    Git AI Reporter goes beyond simple changelog generation:
    
    **Traditional Tools:**
    - Parse commit messages for formatting
    - Generate basic lists of changes
    - Limited context and categorization
    
    **Git AI Reporter:**
    - **AI Analysis** - Understands code changes and context
    - **Multi-Level Processing** - Individual commits, daily patterns, weekly narratives
    - **Professional Output** - Stakeholder-friendly narratives and documentation
    - **Pattern Recognition** - Identifies trends and development focus areas
    - **Intelligent Categorization** - Context-aware change classification

??? question "Do I need programming experience to use Git AI Reporter?"

    **Basic Usage** - No programming required:
    - Install via `pip install git-ai-reporter`
    - Set your API key: `export GEMINI_API_KEY="your-key"`
    - Run: `git-ai-reporter --weeks 1`
    
    **Advanced Usage** - Some technical knowledge helpful for:
    - Custom configuration and filtering
    - Integration with CI/CD pipelines
    - API usage and programmatic integration
    
    The tool is designed to be accessible to both technical and non-technical users.

## Installation & Setup

??? question "What are the system requirements?"

    **Minimum Requirements:**
    - **Python 3.12+** (required for modern type hints)
    - **Git repository** to analyze
    - **Internet connection** for AI API calls
    - **Google Gemini API key** (free tier available)
    
    **Recommended:**
    - 4GB RAM for large repositories
    - SSD storage for better performance
    - Stable internet connection for API reliability

??? question "How do I get a Google Gemini API key?"

    1. **Visit Google AI Studio** - Go to [ai.google.dev](https://ai.google.dev/)
    2. **Sign in** with your Google account
    3. **Create API Key** - Click "Get API Key" and create new key
    4. **Copy the key** - Save it securely
    5. **Set environment variable:**
       ```bash
       export GEMINI_API_KEY="your-api-key-here"
       ```
    
    **Free Tier Limits:**
    - 15 requests per minute
    - 1 million tokens per minute
    - 1,500 requests per day
    
    This is sufficient for most repositories and usage patterns.

??? question "Can I run this without an internet connection?"

    No, Git AI Reporter requires an internet connection to:
    - Access Google's Gemini API for AI analysis
    - Download model updates and improvements
    - Validate API responses and rate limits
    
    However, **caching reduces API calls** by 60-80% for subsequent runs, minimizing bandwidth usage.

??? question "What operating systems are supported?"

    Git AI Reporter supports all platforms where Python 3.12+ runs:
    
    **Fully Supported:**
    - ✅ Linux (Ubuntu, CentOS, Debian, etc.)
    - ✅ macOS (Intel and Apple Silicon)
    - ✅ Windows 10/11
    
    **Installation Methods:**
    - **PyPI** - `pip install git-ai-reporter`
    - **Docker** - Cross-platform containerized execution
    - **Source** - Build from source on any Python 3.12+ platform

## Usage & Configuration

??? question "How much does it cost to analyze my repository?"

    **Costs depend on repository size and usage:**
    
    **Free Tier (Google Gemini):**
    - 1,500 requests per day
    - Suitable for small-medium repositories
    - Personal projects and experimentation
    
    **Typical Analysis Costs:**
    - **Small repo** (<100 commits): Free tier sufficient
    - **Medium repo** (100-1000 commits): $0.10-1.00 per analysis
    - **Large repo** (1000+ commits): $1.00-5.00 per analysis
    
    **Cost Optimization:**
    - **Enable caching** - Reduces repeat costs by 60-80%
    - **Use date ranges** - Analyze specific periods only
    - **Configure model tiers** - Use faster/cheaper models when appropriate

??? question "How long does analysis take?"

    **Analysis time varies by repository size:**
    
    **Small Repository** (<50 commits):
    - Initial run: 30 seconds - 2 minutes
    - Cached runs: 5-15 seconds
    
    **Medium Repository** (50-500 commits):
    - Initial run: 2-10 minutes
    - Cached runs: 30 seconds - 2 minutes
    
    **Large Repository** (500+ commits):
    - Initial run: 10-30 minutes
    - Cached runs: 2-5 minutes
    
    **Factors affecting speed:**
    - Internet connection speed
    - API response times
    - Repository complexity
    - Concurrent processing limits

??? question "Can I customize the output format?"

    **Current Customization Options:**
    
    **File Paths:**
    ```bash
    export NEWS_FILE="reports/development-summary.md"
    export CHANGELOG_FILE="releases/CHANGELOG.md"
    ```
    
    **Content Filtering:**
    - Configure trivial commit types
    - Set file pattern filters
    - Adjust date ranges and scope
    
    **AI Parameters:**
    - Temperature settings for creativity vs consistency
    - Model tier selection for speed vs quality
    
    **Future Customization** (planned):
    - Custom output templates
    - Additional format support (HTML, PDF)
    - Plugin system for extended customization

??? question "How do I analyze only specific branches or authors?"

    **Branch Analysis:**
    Git AI Reporter analyzes all branches by default. For specific branches:
    
    ```bash
    # Checkout the branch first
    git checkout feature-branch
    git-ai-reporter --weeks 1
    ```
    
    **Author Filtering:**
    Use git filtering before analysis:
    
    ```bash
    # Filter by author in date range
    git log --author="John Doe" --since="1 week ago" --oneline
    ```
    
    **Future Enhancement:**
    Direct branch and author filtering support is planned for future releases.

??? question "What file types and languages are supported?"

    Git AI Reporter analyzes **any Git repository** regardless of programming language:
    
    **Language-Agnostic:**
    - All programming languages (Python, JavaScript, Java, C++, etc.)
    - Markup languages (HTML, XML, Markdown)
    - Configuration files (JSON, YAML, TOML)
    - Documentation (README, docs, wikis)
    
    **File Type Intelligence:**
    - Recognizes file extensions and content types
    - Provides context-aware analysis
    - Identifies language-specific patterns
    
    **Special Handling:**
    - Binary files are noted but content not analyzed
    - Generated files can be filtered out
    - Test files receive appropriate categorization

## AI Models & Accuracy

??? question "Which AI models does Git AI Reporter use?"

    **Three-Tier Architecture:**
    
    **Tier 1** - Fast Analysis (default: `gemini-2.5-flash`):
    - Individual commit analysis
    - High-volume processing
    - Categorization and filtering
    
    **Tier 2** - Pattern Recognition (default: `gemini-2.5-pro`):
    - Daily summary synthesis
    - Trend identification
    - Context building
    
    **Tier 3** - Narrative Generation (default: `gemini-2.5-pro`):
    - Weekly narratives
    - Professional documentation
    - Stakeholder communication
    
    **Model Configuration:**
    ```bash
    export MODEL_TIER_1="gemini-2.5-flash"   # Speed optimized
    export MODEL_TIER_2="gemini-2.5-pro"     # Balance
    export MODEL_TIER_3="gemini-2.5-pro"     # Quality optimized
    ```

??? question "How accurate is the AI analysis?"

    **Analysis Accuracy Factors:**
    
    **High Accuracy Areas:**
    - Commit categorization (90%+ accuracy)
    - File change detection
    - Pattern recognition
    - Technical detail extraction
    
    **Context-Dependent Areas:**
    - Intent interpretation (depends on commit message quality)
    - Business impact assessment
    - Priority determination
    
    **Quality Factors:**
    - **Good commit messages** improve analysis quality
    - **Clear file organization** enhances categorization
    - **Consistent naming** helps pattern recognition
    
    **Validation:**
    - Manual review recommended for critical documentation
    - AI provides suggestions, human judgment for final decisions

??? question "Can I use different AI models or providers?"

    **Current Support:**
    - Only Google Gemini models currently supported
    - Multiple model tiers within Gemini family
    - Configurable model selection per tier
    
    **Future Support (planned):**
    - OpenAI GPT models integration
    - Additional AI model support
    - Local model support (Ollama, etc.)
    - Custom model endpoint configuration
    
    **Architecture Design:**
    - Built with model-agnostic architecture
    - Plugin system supports future integrations
    - API abstraction layer ready for extensions

## Performance & Optimization

??? question "My analysis is slow. How can I improve performance?"

    **Performance Optimization Strategies:**
    
    **1. Enable Caching:**
    ```bash
    # Ensure caching is enabled (default)
    export CACHE_ENABLED=true
    ```
    
    **2. Optimize Concurrency:**
    ```bash
    # Adjust concurrent operations
    export MAX_CONCURRENT_GIT_COMMANDS=10
    ```
    
    **3. Use Date Ranges:**
    ```bash
    # Analyze specific periods
    git-ai-reporter --start-date 2025-01-01 --end-date 2025-01-31
    ```
    
    **4. Model Configuration:**
    ```bash
    # Use faster models for development
    export MODEL_TIER_2="gemini-2.5-flash"
    ```
    
    **5. Reduce Timeout:**
    ```bash
    # Shorter timeouts for faster failure
    export GEMINI_API_TIMEOUT=300
    ```

??? question "How does the caching system work?"

    **Multi-Level Caching:**
    
    **Level 1 - Commit Analysis Cache:**
    - **Key:** Git commit SHA (immutable)
    - **Duration:** Permanent (commits never change)
    - **Benefit:** 90%+ cache hit rate for repeated analysis
    
    **Level 2 - Daily Summary Cache:**
    - **Key:** Date + repository state hash
    - **Duration:** Invalidated when new commits added to date
    - **Benefit:** Avoids re-processing unchanged days
    
    **Level 3 - AI Response Cache:**
    - **Key:** Content hash of prompt + model + parameters
    - **Duration:** 24-48 hours (configurable)
    - **Benefit:** Reuses identical AI requests
    
    **Cache Statistics:**
    ```bash
    git-ai-reporter --cache-stats
    ```

??? question "Can I run analysis on very large repositories?"

    **Large Repository Support:**
    
    **Scalability Features:**
    - Concurrent processing with configurable limits
    - Memory-efficient streaming operations
    - Intelligent prompt fitting for large diffs
    - Progressive analysis with checkpointing
    
    **Optimization for Large Repos:**
    
    **1. Date Range Analysis:**
    ```bash
    # Analyze recent activity only
    git-ai-reporter --weeks 4
    git-ai-reporter --start-date 2025-01-01
    ```
    
    **2. Increased Resources:**
    ```bash
    # More concurrent operations
    export MAX_CONCURRENT_GIT_COMMANDS=20
    export GEMINI_API_TIMEOUT=900
    ```
    
    **3. Caching Strategy:**
    ```bash
    # Larger cache with longer retention
    export CACHE_MAX_SIZE_MB=500
    export CACHE_TTL_DAYS=60
    ```
    
    **Successfully Tested:**
    - Repositories with 10,000+ commits
    - Monorepos with complex structure
    - Multi-year analysis periods

## Troubleshooting

??? question "I'm getting API errors. What should I check?"

    **Common API Issues:**
    
    **1. Invalid API Key:**
    ```bash
    # Verify API key is set
    echo $GEMINI_API_KEY
    
    # Test API key validity
    curl -H "Authorization: Bearer $GEMINI_API_KEY" \
         https://generativelanguage.googleapis.com/v1beta/models
    ```
    
    **2. Rate Limiting:**
    - Free tier: 15 requests/minute, 1,500/day
    - Solution: Enable caching, use date ranges
    - Wait and retry, or upgrade to paid tier
    
    **3. Timeout Issues:**
    ```bash
    # Increase timeout for large repositories
    export GEMINI_API_TIMEOUT=600
    ```
    
    **4. Network Connectivity:**
    ```bash
    # Test internet connection
    ping ai.google.dev
    ```

??? question "The analysis output seems incorrect. How can I improve it?"

    **Improving Analysis Quality:**
    
    **1. Commit Message Quality:**
    - Use conventional commit format: `feat: add user authentication`
    - Provide clear, descriptive messages
    - Include context about why changes were made
    
    **2. Repository Organization:**
    - Clear file and directory structure
    - Consistent naming conventions
    - Separate features into logical commits
    
    **3. Configuration Tuning:**
    ```bash
    # Lower temperature for more consistent results
    export TEMPERATURE=0.3
    
    # Filter out noise commits
    export TRIVIAL_COMMIT_TYPES='["style", "chore", "docs"]'
    ```
    
    **4. Model Selection:**
    ```bash
    # Use higher quality models for better analysis
    export MODEL_TIER_1="gemini-2.5-pro"
    ```

??? question "Git AI Reporter won't start. What's wrong?"

    **Startup Issues:**
    
    **1. Python Version:**
    ```bash
    # Check Python version (requires 3.12+)
    python --version
    ```
    
    **2. Installation Issues:**
    ```bash
    # Reinstall if corrupted
    pip uninstall git-ai-reporter
    pip install git-ai-reporter
    ```
    
    **3. Dependencies:**
    ```bash
    # Install in clean environment
    python -m venv venv
    source venv/bin/activate  # or `venv\Scripts\activate` on Windows
    pip install git-ai-reporter
    ```
    
    **4. Git Repository:**
    ```bash
    # Must be run in Git repository
    git status  # Should not error
    ```
    
    **5. Debug Mode:**
    ```bash
    # Enable debug output
    git-ai-reporter --debug --weeks 1
    ```

## Integration & Advanced Usage

??? question "Can I integrate Git AI Reporter with CI/CD pipelines?"

    **CI/CD Integration Examples:**
    
    **GitHub Actions:**
    ```yaml
    name: Generate Documentation
    on:
      schedule:
        - cron: '0 9 * * 1'  # Weekly on Monday
    
    jobs:
      docs:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
            with:
              fetch-depth: 0
          
          - name: Generate Reports
            env:
              GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
            run: |
              pip install git-ai-reporter
              git-ai-reporter --weeks 1
    ```
    
    **GitLab CI:**
    ```yaml
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
    ```
    
    **Docker Integration:**
    ```bash
    docker run --rm -v $(pwd):/repo \
      -e GEMINI_API_KEY=$GEMINI_API_KEY \
      git-ai-reporter --weeks 1
    ```

??? question "Can I use the Python API directly?"

    **Python API Usage:**
    
    ```python
    from git_ai_reporter import AnalysisOrchestrator
    from git_ai_reporter.config import Settings
    from datetime import datetime, timedelta
    
    # Configure settings
    settings = Settings(gemini_api_key="your-key")
    
    # Create orchestrator
    orchestrator = AnalysisOrchestrator(settings)
    
    # Run analysis
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    await orchestrator.run(start_date, end_date)
    ```
    
    **Advanced Usage:**
    - Custom analysis workflows
    - Integration with existing Python applications
    - Batch processing multiple repositories
    - Custom output formatting
    
    See **[API Reference →](../api/index.md)** for complete documentation.

??? question "Is there a plugin system for extending functionality?"

    **Current Plugin Support:**
    The plugin system architecture is implemented for future extensibility.
    
    **Planned Plugin Features:**
    - Custom output formats (HTML, PDF, JSON)
    - Integration with project management tools (Jira, Linear)
    - Notification systems (Slack, Discord, email)
    - Custom analysis filters and processors
    
    **Plugin Development:**
    ```python
    from git_ai_reporter.plugins.base import BasePlugin
    
    class CustomPlugin(BasePlugin):
        async def after_analysis_complete(self, result):
            # Custom post-processing
            pass
    ```
    
    **Current Extensibility:**
    - Configuration-based customization
    - Environment variable overrides
    - Custom model configurations
    - Scriptable workflows

## Security & Privacy

??? question "What data does Git AI Reporter collect or store?"

    **Data Handling Policy:**
    
    **Analyzed Locally:**
    - Git commit history and diffs
    - Repository metadata and structure
    - Generated analysis results
    
    **Sent to AI Service:**
    - Commit messages and code diffs
    - Repository file paths and names
    - Analysis prompts and context
    
    **Never Collected:**
    - Personal identifiers or credentials
    - Complete source code repositories
    - Analysis results or outputs
    - Usage statistics or telemetry
    
    **Data Protection:**
    - API keys stored as environment variables only
    - Local caching with proper file permissions
    - No data persistence beyond local cache
    - Secure HTTPS communication with AI services

??? question "Is my source code secure when using Git AI Reporter?"

    **Security Measures:**
    
    **Local Processing:**
    - Git analysis happens locally
    - Only diffs sent to AI service, not full code
    - No permanent storage of code on external servers
    
    **API Communication:**
    - Secure HTTPS encryption for all API calls
    - Google's enterprise-grade security infrastructure
    - No code storage in AI service logs or cache
    
    **Best Practices:**
    - Use API keys with minimal required permissions
    - Review generated diffs before analysis of sensitive code
    - Consider using date ranges to limit analyzed content
    - Test with non-sensitive repositories first
    
    **For Sensitive Repositories:**
    - Use self-hosted AI models when available
    - Implement custom filtering for sensitive file patterns
    - Consider airgapped environments for maximum security

??? question "Can I use this with private/confidential repositories?"

    **Private Repository Considerations:**
    
    **Technical Compatibility:**
    - ✅ Works with private GitHub, GitLab, Bitbucket repositories
    - ✅ Local Git repositories (no remote required)
    - ✅ Enterprise Git hosting solutions
    
    **Security Considerations:**
    - Code diffs are sent to Google's Gemini API
    - Commit messages and file paths are included
    - Consider data sensitivity and organizational policies
    
    **Risk Mitigation:**
    - Use specific date ranges to limit exposure
    - Configure file pattern filters for sensitive files
    - Review and validate analysis prompts
    - Implement organizational API key management
    
    **Alternative Approaches:**
    - Analyze only public-facing components
    - Use for open source portions of projects
    - Wait for self-hosted AI model support

## Support & Community

??? question "How do I report bugs or request features?"

    **Bug Reports:**
    1. **Check existing issues** - [GitHub Issues](https://github.com/paudley/git-ai-reporter/issues)
    2. **Create detailed bug report** with:
       - Steps to reproduce
       - Expected vs actual behavior
       - Environment details (OS, Python version, etc.)
       - Debug output if available
    3. **Use bug report template** for consistency
    
    **Feature Requests:**
    1. **Search existing requests** to avoid duplicates
    2. **Describe the use case** and benefit
    3. **Provide implementation ideas** if you have them
    4. **Use feature request template**
    
    **Community Support:**
    - **[GitHub Discussions](https://github.com/paudley/git-ai-reporter/discussions)** for questions
    - **[Documentation →](../index.md)** for guides and examples
    - **Response time:** Typically 24-48 hours

??? question "How can I contribute to the project?"

    **Ways to Contribute:**
    
    **Code Contributions:**
    - Bug fixes and feature implementations
    - Performance improvements and optimizations
    - Test coverage expansion
    - Documentation improvements
    
    **Non-Code Contributions:**
    - Bug reports and testing
    - Documentation improvements
    - Feature suggestions and use cases
    - Community support and discussions
    
    **Getting Started:**
    1. **Read** [Contributing Guide →](../development/contributing.md)
    2. **Fork** the repository
    3. **Set up** development environment
    4. **Make changes** following coding standards
    5. **Submit** pull request
    
    **Development Standards:**
    - Python 3.12 with type hints
    - Comprehensive test coverage
    - Documentation updates required
    - Clean Architecture principles

??? question "Is commercial support available?"

    **Current Support Model:**
    - Community-driven support through GitHub
    - Documentation and guides for self-service
    - Responsive issue management and resolution
    
    **Professional Services (Future):**
    - Custom integration and deployment assistance
    - Priority support and feature development
    - Training and consultation services
    - Enterprise hosting and management
    
    **Current Enterprise Features:**
    - Self-hosted deployment options
    - Advanced configuration and customization
    - API integration capabilities
    - Comprehensive documentation and examples

---

**Still have questions?** 

- **[Browse Documentation →](../index.md)**
- **[Ask in Discussions →](https://github.com/paudley/git-ai-reporter/discussions)**
- **[Open an Issue →](https://github.com/paudley/git-ai-reporter/issues)**
- **[Check Troubleshooting Guide →](../guide/troubleshooting.md)**