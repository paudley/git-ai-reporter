# Allure Test Reporting Guide

## Overview

Git AI Reporter uses Allure Framework for comprehensive test reporting and documentation. Allure provides rich test reports with detailed execution information, categorization, history tracking, and integration with CI/CD pipelines.

## What is Allure Framework?

Allure Framework is a flexible lightweight multi-language test report tool that not only shows a very concise representation of what has been tested in a neat web report form, but allows everyone participating in the development process to extract maximum of useful information from everyday execution of tests.

### Key Benefits
- **Rich visualization**: Beautiful, interactive web reports
- **Detailed test information**: Steps, attachments, parameters, and timing
- **Historical trends**: Test execution history and trend analysis
- **Integration support**: CI/CD pipeline integration with GitHub Actions
- **Multi-language support**: Works with Python, Java, JavaScript, and more
- **Test categorization**: Organize tests by features, stories, and severity levels

## Allure Integration in Git AI Reporter

### Installation and Setup

Allure is integrated into the project's development dependencies:

```toml
# In pyproject.toml
[project.optional-dependencies]
dev = [
    "allure-pytest>=2.13.0",  # Allure pytest integration
    # ... other dev dependencies
]
```

### Decorator Patterns

Every test method in the Git AI Reporter test suite uses comprehensive Allure decorators:

#### Class-Level Decorators
```python
import allure

@allure.feature("Git Analysis")
class TestGitAnalyzer:
    """Test class for Git analysis functionality."""
```

#### Method-Level Decorators
```python
@allure.story("Commit Filtering")
@allure.title("Filter commits by message prefixes")
@allure.description(
    "Tests that commits with non-meaningful prefixes (chore:, docs:, style:) "
    "are properly filtered out during analysis"
)
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("git", "filtering", "commits", "analysis")
def test_filter_commits_by_prefix(self):
    """Test commit filtering by message prefixes."""
```

### Severity Level Guidelines

#### BLOCKER
- **Definition**: Critical functionality that prevents system operation
- **Examples**: 
  - Core CLI command execution
  - Essential configuration loading
  - Primary git repository access
  - Critical AI service communication

#### CRITICAL  
- **Definition**: Core functionality essential for primary use cases
- **Examples**:
  - Commit analysis and summarization
  - Report generation (NEWS.md, CHANGELOG.txt)
  - Cache management for API calls
  - Error handling for primary workflows

#### NORMAL
- **Definition**: Standard functionality with moderate impact
- **Examples**:
  - File I/O operations
  - Configuration validation
  - Secondary analysis features
  - Helper utility functions

#### MINOR
- **Definition**: Secondary functionality with limited impact
- **Examples**:
  - Optional formatting features
  - Non-essential configuration options
  - Convenience utilities
  - Edge case handling

#### TRIVIAL
- **Definition**: Edge cases or cosmetic functionality
- **Examples**:
  - Input validation for unusual cases
  - Cosmetic output formatting
  - Development-only features
  - Rarely used utility functions

### Step-by-Step Test Documentation

Use `allure.step()` context managers to create detailed test execution documentation:

```python
def test_comprehensive_git_analysis(self):
    """Test complete git analysis workflow."""
    
    with allure.step("Initialize test repository with sample commits"):
        repo = self.create_test_repository()
        self.add_sample_commits(repo)
    
    with allure.step("Configure analysis parameters"):
        config = AnalysisConfig(
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now()
        )
    
    with allure.step("Execute git analysis"):
        analyzer = GitAnalyzer(repo.working_dir)
        results = analyzer.analyze_commits(config)
    
    with allure.step("Verify analysis results completeness"):
        assert len(results.commits) > 0
        assert results.summary is not None
        
    with allure.step("Validate commit categorization"):
        categories = [commit.category for commit in results.commits]
        assert "feature" in categories
        assert "bugfix" in categories
```

### Test Data Attachments

Attach relevant test data and results to Allure reports for debugging and documentation:

```python
def test_ai_analysis_response(self):
    """Test AI analysis response processing."""
    
    sample_response = {
        "analysis": "Feature addition for user authentication",
        "category": "feature",
        "impact": "high"
    }
    
    # Attach test input data
    allure.attach(
        json.dumps(sample_response, indent=2),
        name="AI Response Sample Data",
        attachment_type=allure.attachment_type.JSON
    )
    
    # Execute test logic
    result = process_ai_response(sample_response)
    
    # Attach test results
    allure.attach(
        str(result),
        name="Processed Result",
        attachment_type=allure.attachment_type.TEXT
    )
    
    # Assertions
    assert result.category == "feature"
    assert result.impact == "high"
```

### Tag Organization Strategy

Use consistent tagging to enable powerful test filtering and organization:

#### Primary Categories
- **Component tags**: `git`, `ai`, `cache`, `config`, `cli`
- **Operation tags**: `analysis`, `generation`, `filtering`, `validation`
- **Data type tags**: `commits`, `summaries`, `reports`, `files`
- **Test type tags**: `unit`, `integration`, `e2e`, `performance`

#### Example Tag Usage
```python
@allure.tag("git", "analysis", "commits", "unit")           # Unit test for git commit analysis
@allure.tag("ai", "generation", "summaries", "integration") # Integration test for AI summary generation  
@allure.tag("cache", "validation", "performance")           # Performance test for cache validation
@allure.tag("cli", "e2e", "reports", "workflow")           # End-to-end CLI workflow test
```

## Running Tests with Allure

### Using Makefile Commands (Recommended)

The project includes convenient Makefile targets for Allure operations:

```bash
# Run tests and generate Allure results
make test-allure

# Generate static HTML report (may have CORS issues when opened directly)
make allure-report

# Start development server at http://localhost:5050 (recommended)
make allure-serve
```

### Manual Commands

If you prefer to run commands directly:

```bash
# Run tests with Allure result generation
uv run pytest tests/ -v --alluredir=allure-results/

# Run specific test categories with Allure
uv run pytest tests/unit/ -v --alluredir=allure-results/
uv run pytest tests/integration/ -v --alluredir=allure-results/
```

### Generate and View Allure Reports

#### Local Development
```bash
# Install Allure CLI (requires Java)
# macOS: brew install allure
# Linux: Download from https://github.com/allure-framework/allure2/releases

# Generate HTML report
allure generate allure-results/ --output allure-report/ --clean

# Open interactive report in browser
allure open allure-report/
```

#### Allure Docker Service UI (Recommended)

**The project includes a complete Docker Compose setup with Allure Docker Service UI for the best viewing experience:**

```bash
# Start Allure Docker Service + UI (automatically runs tests if needed)
make allure-ui-up

# Send test results to Allure Docker Service
./scripts/send_to_allure.sh

# View Allure reports in browser
./scripts/view_allure.sh

# View service status and URLs
make allure-ui-status

# Stop services when done
make allure-ui-down
```

**Helper Scripts:**
- `scripts/send_to_allure.sh`: Sends test results from `allure-results/` to the Allure Docker Service for processing
- `scripts/view_allure.sh`: Opens the Allure UI in your default browser at the correct project URL

**Service URLs:**
- **📊 Allure UI (Recommended):** http://localhost:5252/allure-docker-service-ui
- **🔧 Allure API:** http://localhost:5050

**Additional Docker UI Commands:**
```bash
make allure-ui-restart    # Restart both services
make allure-ui-logs       # View service logs
make allure-ui-status     # Check service health
```

#### Docker Alternative (Manual Setup)

**Static Report Generation:**
```bash
# Using Docker for Allure report generation (with proper user permissions)
docker run --rm \
    --user $(id -u):$(id -g) \
    -v $(pwd)/allure-results:/allure-results \
    -v $(pwd)/allure-report:/allure-report \
    frankescobar/allure-docker-service:latest \
    allure generate /allure-results --output /allure-report --clean
```

**Development Server:**
```bash
# Using Docker for Allure development server (avoids CORS issues)
docker run --rm \
    --user $(id -u):$(id -g) \
    -p 5050:5050 \
    -v $(pwd)/allure-results:/app/allure-results \
    -e CHECK_RESULTS_EVERY_SECONDS=3 \
    -e KEEP_HISTORY=1 \
    frankescobar/allure-docker-service:latest
```

**Important Notes:**
- The `--user $(id -u):$(id -g)` flag ensures the container runs with your user permissions, preventing permission issues with generated files
- The Docker Compose UI setup is recommended because it provides both the service and a user-friendly web interface
- The UI avoids CORS issues that occur when opening static HTML files directly in browsers
- Services automatically restart and include health checks for reliability

## Docker Compose Configuration

The project includes a `docker-compose.yml` file that sets up both Allure Docker Service and Allure Docker Service UI with proper configuration for local development.

### Architecture

```yaml
services:
  allure:           # Core Allure Docker Service (API + Report Generation)
    - Port: 5050
    - API endpoints for report management
    - Automatic result processing
    - History preservation
    
  allure-ui:        # User-friendly web interface
    - Port: 5252
    - Modern React-based UI
    - Connects to Allure service
    - Enhanced user experience
```

### Key Features

**User Permission Handling:**
- Uses `UID` and `GID` environment variables to run containers as current user
- Prevents permission issues with generated files and directories
- Maintains proper file ownership for host system integration

**Health Monitoring:**
- Built-in health checks for both services
- Automatic dependency management (UI waits for service to be healthy)
- Status monitoring via `make allure-ui-status`

**Data Persistence:**
- Persistent volume for test execution history
- Automatic cleanup of old results (configurable)
- Result sharing between host and containers

**Development Optimization:**
- Auto-refresh every 3 seconds for new test results
- History preservation for trend analysis
- Proper network isolation with custom bridge network

### Configuration Options

The Docker Compose setup can be customized by modifying `docker-compose.yml`:

```yaml
# Allure Service Configuration
CHECK_RESULTS_EVERY_SECONDS: 3    # How often to check for new results
KEEP_HISTORY: "1"                  # Enable history preservation
KEEP_HISTORY_LATEST: "25"          # Number of executions to keep

# UI Configuration
ALLURE_DOCKER_PUBLIC_API_URL: "http://localhost:5050"  # Service connection
```

### Workflow Integration

The Docker Compose setup integrates seamlessly with the existing test workflow:

1. **Automatic Test Execution:** `make allure-ui-up` runs tests if no results exist
2. **Real-time Updates:** Services monitor for new test results automatically
3. **Easy Access:** Single command provides both API and UI access
4. **Clean Shutdown:** `make allure-ui-down` stops all services cleanly

## GitHub Actions Integration

### Automated Report Generation

The project includes GitHub Actions workflows for automated Allure report generation:

#### CI Integration (`.github/workflows/ci.yml`)
```yaml
- name: Test with pytest and generate Allure results
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  run: |
    uv run pytest tests/ -v --cov=src/git_ai_reporter --cov-report=xml --cov-report=term --alluredir=allure-results
    
- name: Upload Allure results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: allure-results-${{ matrix.os }}-${{ matrix.python-version }}
    path: allure-results/
    retention-days: 30
```

#### Dedicated Allure Workflow (`.github/workflows/allure-report.yml`)
- **Triggers**: After CI completion or manual dispatch
- **Features**: 
  - Downloads test results from all matrix combinations
  - Installs Allure CLI and Java dependencies
  - Generates comprehensive HTML reports
  - Deploys to GitHub Pages for easy access
  - Comments on PRs with report links

### Viewing Reports Online

#### GitHub Pages Deployment
- **URL Pattern**: `https://{username}.github.io/{repo-name}/`
- **Automatic updates**: Reports regenerated on every main branch push
- **Historical data**: Maintains test execution history and trends

#### PR Integration
- **Automatic comments**: Bot comments on PRs with Allure report links
- **Test status**: Clear visibility of test results in PR discussions
- **Team collaboration**: Shared access to detailed test execution information

## Best Practices for Allure Usage

### Writing Effective Test Documentation

#### Clear Titles and Descriptions
```python
@allure.title("Validate cache hit ratio for repeated API calls")
@allure.description(
    "Verifies that the cache manager properly caches AI API responses "
    "and returns cached results for identical requests, achieving "
    "expected cache hit ratios for cost optimization."
)
```

#### Meaningful Step Names
```python
with allure.step("Configure cache with 1-hour TTL"):
    cache_config = CacheConfig(ttl_seconds=3600)
    
with allure.step("Make initial API call and verify cache miss"):
    result1 = ai_service.analyze_commit(commit_data)
    assert cache_manager.cache_stats.misses == 1
    
with allure.step("Make identical API call and verify cache hit"):
    result2 = ai_service.analyze_commit(commit_data)
    assert cache_manager.cache_stats.hits == 1
    assert result1 == result2
```

### Test Organization Guidelines

#### Feature Hierarchy
1. **@allure.feature()**: High-level functionality (e.g., "Git Analysis", "AI Processing", "Report Generation")
2. **@allure.story()**: Specific user scenarios (e.g., "Commit Filtering", "Summary Generation", "Cache Management")
3. **@allure.title()**: Detailed test description (e.g., "Filter commits by non-meaningful prefixes")

#### Consistent Naming Conventions
- **Features**: Match major system components or modules
- **Stories**: Correspond to user stories or specific behaviors
- **Titles**: Clear, action-oriented descriptions
- **Tags**: Consistent vocabulary for filtering and organization

### Performance Considerations

#### Attachment Size Management
```python
# Good: Attach relevant excerpts
allure.attach(
    json.dumps(result_summary, indent=2),
    name="Analysis Summary",
    attachment_type=allure.attachment_type.JSON
)

# Avoid: Attaching large raw data
# allure.attach(entire_repository_data)  # Too large
```

#### Step Granularity Balance
```python
# Good: Meaningful logical steps
with allure.step("Prepare test data"):
    # Multiple related setup operations
    pass

with allure.step("Execute analysis"):
    # Core test logic
    pass

# Avoid: Too granular
# with allure.step("Create variable x"):  # Too detailed
#     x = 1
# with allure.step("Create variable y"):  # Too detailed  
#     y = 2
```

## Troubleshooting Allure Issues

### Common Problems and Solutions

#### Missing Allure Results
```bash
# Problem: No allure-results directory created
# Solution: Ensure pytest-allure plugin is installed
uv pip install allure-pytest

# Verify plugin is loaded
uv run pytest --markers | grep allure
```

#### Empty or Incomplete Reports
```bash
# Problem: Allure report shows no tests
# Solution: Check allure-results directory contents
ls -la allure-results/

# Ensure JSON files are present
# If missing, check pytest execution for errors
```

#### CORS Issues with Static Reports
```bash
# Problem: Browser console shows CORS errors when opening index.html
# Error: "Access to XMLHttpRequest blocked by CORS policy"
# Solution: Use development server instead of opening static files
make allure-serve  # Opens at http://localhost:5050

# Alternative: Use Allure CLI serve command
allure serve allure-results/
```

#### Docker Permission Issues
```bash
# Problem: "Permission denied" or files owned by root after Docker commands
# Solution: Ensure Docker runs with correct user ID
docker run --rm --user $(id -u):$(id -g) ...

# For Docker Compose (handled automatically by Makefile)
UID=$(id -u) GID=$(id -g) docker-compose up -d

# Fix existing permission issues
sudo chown -R $USER:$USER allure-report/ allure-results/
```

#### Docker Compose Issues
```bash
# Problem: "docker-compose command not found"
# Solution: Install Docker Compose or use Docker Compose V2
docker compose version  # Check if Docker Compose V2 is available

# Problem: Services fail to start
# Solution: Check service logs
make allure-ui-logs

# Problem: Port conflicts (5050 or 5252 already in use)
# Solution: Stop conflicting services or modify docker-compose.yml ports
lsof -i :5050  # Check what's using port 5050
lsof -i :5252  # Check what's using port 5252

# Problem: Services start but UI shows connection errors
# Solution: Verify service health and wait for startup
make allure-ui-status
# Wait 30-60 seconds for services to fully initialize

# Problem: No test results visible in UI
# Solution: Ensure allure-results directory has content
ls -la allure-results/
make test-allure  # Generate fresh test results
```

#### Java/Allure CLI Issues
```bash
# Problem: "allure command not found"
# Solution: Install Allure CLI with Java 8+

# macOS
brew install allure

# Linux/Manual installation
wget https://github.com/allure-framework/allure2/releases/latest/download/allure-{version}.tgz
tar -zxvf allure-{version}.tgz
export PATH=$PATH:$(pwd)/allure-{version}/bin
```

### GitHub Actions Debugging

#### Workflow Failures
- **Check Java installation**: Ensure Java 11+ is available for Allure CLI
- **Verify artifact uploads**: Confirm allure-results artifacts are created
- **Review permissions**: Ensure GitHub Pages permissions are configured
- **Check report generation logs**: Review Allure CLI output for errors

#### Missing Historical Data
- **GitHub Pages setup**: Ensure gh-pages branch is configured
- **History preservation**: Verify history copying steps in workflow
- **Branch protection**: Ensure gh-pages branch allows force pushes from Actions

## Advanced Allure Features

### Custom Allure Properties
Create `allure.properties` file for custom configuration:
```properties
allure.results.directory=allure-results
allure.link.pattern=https://github.com/username/git-ai-reporter/issues/{}
allure.link.tms.pattern=https://jira.company.com/browse/{}
```

### Environment Information
Add environment details to reports:
```python
# In conftest.py
@pytest.fixture(scope="session", autouse=True)
def environment_setup():
    allure.environment(
        platform=platform.system(),
        python_version=platform.python_version(),
        git_branch=subprocess.check_output(["git", "branch", "--show-current"]).decode().strip(),
        commit_hash=subprocess.check_output(["git", "rev-parse", "HEAD"]).decode()[:8]
    )
```

### Custom Categories
Define test categories in `categories.json`:
```json
[
  {
    "name": "Critical Path Tests",
    "matchedStatuses": ["failed"],
    "matchedTags": ["critical"]
  },
  {
    "name": "Integration Failures",
    "matchedStatuses": ["failed"],
    "matchedTags": ["integration"]
  }
]
```

This comprehensive Allure integration provides Git AI Reporter with professional-grade test reporting, enabling better quality assurance, debugging capabilities, and team collaboration through detailed test documentation and visualization.