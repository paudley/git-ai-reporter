# Docker Installation

Docker provides an isolated, reproducible environment for Git AI Reporter, perfect for containerized deployments, CI/CD pipelines, and systems where you prefer not to install Python dependencies locally.

## Why Use Docker?

Docker installation offers several advantages:

- 🔒 **Isolation** - No impact on host system Python environment
- 📦 **Reproducibility** - Identical environment across all systems
- 🚀 **Quick Setup** - No dependency management required
- 🔄 **CI/CD Ready** - Perfect for automated pipelines
- 🧹 **Clean Removal** - Complete uninstall with container deletion

## Quick Start

### Using Pre-built Images

!!! info "Coming Soon"

    Pre-built Docker images will be available on Docker Hub and GitHub Container Registry in an upcoming release. For now, use the build-from-source method below.

```bash
# Coming soon - pre-built image usage
docker run --rm -v $(pwd):/workspace -e GEMINI_API_KEY="your-key" \
  ghcr.io/paudley/git-ai-reporter:latest
```

### Building from Source

```bash
# Clone the repository
git clone https://github.com/paudley/git-ai-reporter.git
cd git-ai-reporter

# Build the Docker image
docker build -t git-ai-reporter:local .

# Run on current directory
docker run --rm \
  -v $(pwd):/workspace \
  -e GEMINI_API_KEY="your-api-key-here" \
  git-ai-reporter:local
```

## Docker Image Variants

### Production Image (Default)

Optimized for size and security:

```dockerfile title="Dockerfile"
FROM python:3.12-slim

# Minimal system dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Install git-ai-reporter
RUN pip install --no-cache-dir git-ai-reporter

USER appuser
WORKDIR /workspace
```

### Development Image

Includes development tools and dependencies:

```dockerfile title="Dockerfile.dev"
FROM python:3.12

# Development system dependencies
RUN apt-get update && apt-get install -y \
    git \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create development user
RUN useradd --create-home --shell /bin/bash --groups sudo dev

# Copy source and install in development mode
COPY . /app
WORKDIR /app
RUN pip install -e .[dev]

USER dev
WORKDIR /workspace
```

## Usage Patterns

### Basic Analysis

Analyze the current directory:

```bash
# Simple analysis
docker run --rm \
  -v $(pwd):/workspace \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  git-ai-reporter:local

# With custom options
docker run --rm \
  -v $(pwd):/workspace \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  git-ai-reporter:local \
  --weeks 2 --debug
```

### Using Environment File

Create a `.env` file and mount it:

```bash
# Create environment file
cat > .env << EOF
GEMINI_API_KEY=your-api-key-here
MODEL_TIER_1=gemini-2.5-flash
MODEL_TIER_2=gemini-2.5-pro
MODEL_TIER_3=gemini-2.5-pro
TEMPERATURE=0.5
DEBUG=false
EOF

# Run with environment file
docker run --rm \
  -v $(pwd):/workspace \
  --env-file .env \
  git-ai-reporter:local
```

### Analyzing External Repositories

```bash
# Clone and analyze external repository
git clone https://github.com/example/repo.git temp-repo

docker run --rm \
  -v $(pwd)/temp-repo:/workspace \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  git-ai-reporter:local \
  --repo-path /workspace

# Cleanup
rm -rf temp-repo
```

### Output File Handling

```bash
# Ensure output files are created with correct permissions
docker run --rm \
  -v $(pwd):/workspace \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -u $(id -u):$(id -g) \
  git-ai-reporter:local

# Check created files
ls -la NEWS.md CHANGELOG.txt DAILY_UPDATES.md
```

## Docker Compose

For more complex setups with multiple services:

```yaml title="docker-compose.yml"
version: '3.8'

services:
  git-ai-reporter:
    build: .
    volumes:
      - ./:/workspace
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DEBUG=false
    user: "${UID:-1000}:${GID:-1000}"
    working_dir: /workspace
    
  # Optional: Allure reporting service
  allure:
    image: frankescobar/allure-docker-service
    ports:
      - "5252:5252"
    volumes:
      - ./allure-results:/app/allure-results
    environment:
      CHECK_RESULTS_EVERY_SECONDS: 1
      KEEP_HISTORY: 1

  # Optional: Development environment
  dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./:/workspace
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    ports:
      - "8000:8000"  # For documentation server
    tty: true
    stdin_open: true
```

Usage with Docker Compose:

```bash
# Run analysis
docker-compose run --rm git-ai-reporter

# Start development environment
docker-compose up dev

# View Allure reports
docker-compose up -d allure
```

## Multi-Architecture Support

Build for multiple platforms:

```bash
# Enable buildx for multi-platform builds
docker buildx create --use

# Build for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t git-ai-reporter:multi \
  --push .

# Run on ARM-based systems (Apple Silicon, ARM servers)
docker run --rm \
  -v $(pwd):/workspace \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  git-ai-reporter:multi
```

## CI/CD Integration

### GitHub Actions

```yaml title=".github/workflows/analyze.yml"
name: Git Analysis
on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for analysis
          
      - name: Analyze repository
        run: |
          docker run --rm \
            -v ${{ github.workspace }}:/workspace \
            -e GEMINI_API_KEY="${{ secrets.GEMINI_API_KEY }}" \
            ghcr.io/paudley/git-ai-reporter:latest \
            --weeks 1 --no-cache
            
      - name: Commit results
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add NEWS.md CHANGELOG.txt DAILY_UPDATES.md
          git diff --staged --quiet || git commit -m "docs: update development summaries"
          git push
```

### GitLab CI

```yaml title=".gitlab-ci.yml"
analyze:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t git-ai-reporter .
    - docker run --rm
        -v $CI_PROJECT_DIR:/workspace
        -e GEMINI_API_KEY="$GEMINI_API_KEY"
        git-ai-reporter
        --weeks 1
  artifacts:
    paths:
      - NEWS.md
      - CHANGELOG.txt
      - DAILY_UPDATES.md
    expire_in: 1 week
  only:
    - schedules
```

### Jenkins Pipeline

```groovy title="Jenkinsfile"
pipeline {
    agent any
    
    environment {
        GEMINI_API_KEY = credentials('gemini-api-key')
    }
    
    stages {
        stage('Analyze') {
            steps {
                script {
                    docker.build('git-ai-reporter').inside("-v ${WORKSPACE}:/workspace") {
                        sh '''
                            git-ai-reporter --weeks 1 --no-cache
                        '''
                    }
                }
            }
        }
        
        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'NEWS.md,CHANGELOG.txt,DAILY_UPDATES.md'
            }
        }
    }
}
```

## Security Considerations

### API Key Security

Never include API keys in Docker images:

```bash
# ❌ Wrong - embeds key in image
docker build --build-arg GEMINI_API_KEY="secret" .

# ✅ Correct - runtime environment variable
docker run -e GEMINI_API_KEY="secret" git-ai-reporter:local
```

### File Permissions

Ensure proper file ownership:

```bash
# Run as current user to avoid permission issues
docker run --rm \
  -v $(pwd):/workspace \
  -u $(id -u):$(id -g) \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  git-ai-reporter:local
```

### Network Security

For enhanced security in restricted environments:

```bash
# Run without network access (use pre-downloaded models only)
docker run --rm --network=none \
  -v $(pwd):/workspace \
  -v /path/to/model/cache:/cache \
  git-ai-reporter:local
```

## Performance Optimization

### Build Optimization

Multi-stage build for smaller images:

```dockerfile title="Dockerfile.optimized"
# Build stage
FROM python:3.12 AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy only installed packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY src/ /app/src/
ENV PYTHONPATH=/app/src:$PYTHONPATH

WORKDIR /workspace
ENTRYPOINT ["python", "-m", "git_ai_reporter.cli"]
```

### Runtime Optimization

```bash
# Use memory limits to prevent OOM issues
docker run --rm \
  --memory=1g \
  --memory-swap=1g \
  -v $(pwd):/workspace \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  git-ai-reporter:local

# Use CPU limits for shared environments
docker run --rm \
  --cpus="0.5" \
  -v $(pwd):/workspace \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  git-ai-reporter:local
```

## Troubleshooting

### Common Docker Issues

??? failure "Permission denied errors"

    **Problem:** Output files created with wrong permissions.
    
    **Solution:**
    ```bash
    # Run as current user
    docker run --rm \
      -u $(id -u):$(id -g) \
      -v $(pwd):/workspace \
      -e GEMINI_API_KEY="$GEMINI_API_KEY" \
      git-ai-reporter:local
    ```

??? failure "Git repository not found"

    **Problem:** Git history not accessible in container.
    
    **Solution:**
    ```bash
    # Ensure .git directory is included in volume mount
    docker run --rm \
      -v $(pwd):/workspace \
      -e GEMINI_API_KEY="$GEMINI_API_KEY" \
      git-ai-reporter:local
    
    # Check git status inside container
    docker run --rm -it \
      -v $(pwd):/workspace \
      git-ai-reporter:local \
      sh -c "cd /workspace && git status"
    ```

??? failure "API connectivity issues"

    **Problem:** Container cannot reach Google's API endpoints.
    
    **Solution:**
    ```bash
    # Check network connectivity
    docker run --rm \
      git-ai-reporter:local \
      sh -c "ping -c 1 generativelanguage.googleapis.com"
    
    # Use host network if needed
    docker run --rm --network=host \
      -v $(pwd):/workspace \
      -e GEMINI_API_KEY="$GEMINI_API_KEY" \
      git-ai-reporter:local
    ```

### Performance Issues

??? warning "Slow build times"

    **Optimization:**
    ```bash
    # Use Docker buildkit for faster builds
    export DOCKER_BUILDKIT=1
    docker build -t git-ai-reporter .
    
    # Use build cache
    docker build --cache-from git-ai-reporter:latest -t git-ai-reporter .
    
    # Multi-stage builds for smaller final image
    docker build -f Dockerfile.optimized -t git-ai-reporter:optimized .
    ```

## Image Management

### Cleanup

```bash
# Remove containers
docker container prune

# Remove unused images
docker image prune

# Remove everything (careful!)
docker system prune -a

# Remove specific image
docker rmi git-ai-reporter:local
```

### Version Management

```bash
# Tag with version
docker build -t git-ai-reporter:1.2.3 .
docker tag git-ai-reporter:1.2.3 git-ai-reporter:latest

# List all versions
docker images git-ai-reporter

# Use specific version
docker run git-ai-reporter:1.2.3
```

## Advanced Docker Usage

### Custom Entrypoints

```bash
# Custom analysis script
docker run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/scripts:/scripts \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  git-ai-reporter:local \
  sh /scripts/custom-analysis.sh
```

### Development Container

```bash
# Interactive development session
docker run -it --rm \
  -v $(pwd):/workspace \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  git-ai-reporter:local \
  bash

# Inside container:
# git-ai-reporter --help
# python -c "import git_ai_reporter; print('OK')"
```

## Next Steps

After setting up Docker:

1. **[Configuration →](configuration.md)** - Environment variables and settings
2. **[Quick Start →](../guide/quick-start.md)** - Run your first analysis
3. **[CLI Reference →](../cli/options.md)** - All available command options
4. **[CI/CD Integration →](../guide/integration.md)** - Automated analysis workflows

## Related Resources

- **[Docker Hub]()** - Pre-built images (coming soon)
- **[GitHub Container Registry]()** - Alternative image source
- **[Security Guide →](../about/security.md)** - Container security best practices