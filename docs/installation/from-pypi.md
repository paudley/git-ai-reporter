# Installing from PyPI

The Python Package Index (PyPI) installation is the recommended method for most users. Git AI Reporter is available as a pre-built package with all dependencies included.

## 🔒 Supply Chain Security

Git AI Reporter provides **industry-leading supply chain security** through PyPI's attestation system:

!!! success "Cryptographic Verification Available"

    All Git AI Reporter packages on PyPI include **digital attestations** that provide cryptographic proof of:
    
    - **Source Authenticity** - Verified origin from our GitHub repository
    - **Build Integrity** - Tamper-evident build process via GitHub Actions
    - **Transparency** - Complete audit trail from source code to package
    - **Trust** - Tokenless publishing directly from our verified GitHub workflow

### Verifying Package Authenticity

You can verify package authenticity using PyPI's attestation system:

```bash
# Install pip-audit with attestation support (Python 3.11+)
pip install pip-audit

# Verify the package attestation
pip-audit --desc --require-hashes git-ai-reporter

# Alternative: Check attestations on PyPI web interface
# Visit: https://pypi.org/project/git-ai-reporter/
# Look for the "🔒 Provenance" section
```

For more details, see our [Security Documentation](../about/security.md).

## Basic Installation

### Using pip

The standard Python package manager:

```bash
# Install latest stable version
pip install git-ai-reporter

# Install specific version
pip install git-ai-reporter==1.2.3

# Install with user permissions (no sudo required)
pip install --user git-ai-reporter
```

### Using uv (Recommended)

For faster, more reliable installations:

```bash
# Install uv if not already installed
pip install uv

# Install git-ai-reporter with uv
uv pip install git-ai-reporter

# Much faster dependency resolution and installation
# Especially beneficial for complex dependency trees
```

## Advanced Installation Options

### Installing with Optional Dependencies

Git AI Reporter supports optional feature sets:

```bash
# Development dependencies (for contributors)
pip install git-ai-reporter[dev]

# All optional dependencies
pip install git-ai-reporter[all]

# Specific feature groups
pip install git-ai-reporter[testing,docs]
```

Available optional dependency groups:

| Group | Purpose | Includes |
|-------|---------|----------|
| `dev` | Development environment | All testing, docs, and development tools |
| `testing` | Test execution | pytest, coverage tools, test utilities |
| `docs` | Documentation building | mkdocs, material theme, plugins |
| `all` | Everything | All optional dependencies |

### Version Management

#### Pinning to Specific Versions

For reproducible environments:

```bash
# Pin to exact version
pip install git-ai-reporter==1.2.3

# Pin to compatible version (allows patch updates)
pip install "git-ai-reporter~=1.2.0"

# Pin to major version (allows minor updates)  
pip install "git-ai-reporter>=1.0.0,<2.0.0"
```

#### Requirements Files

Create a `requirements.txt` for project dependency management:

```text title="requirements.txt"
# Git AI Reporter with version constraints
git-ai-reporter>=1.2.0,<2.0.0

# Optional: Lock other dependencies
python-dotenv>=1.0.0
rich>=13.0.0
```

Install from requirements file:
```bash
pip install -r requirements.txt
```

## Virtual Environment Installation

### Why Use Virtual Environments?

Virtual environments provide:
- **Isolation** - Separate dependencies per project
- **Reproducibility** - Consistent environments across systems  
- **Conflict Prevention** - Avoid dependency version conflicts
- **Clean Uninstall** - Easy removal without affecting system Python

### Using venv (Built-in)

```bash
# Create virtual environment
python -m venv git-ai-reporter-env

# Activate virtual environment
# On Linux/macOS:
source git-ai-reporter-env/bin/activate
# On Windows:
git-ai-reporter-env\Scripts\activate

# Install in virtual environment
pip install git-ai-reporter

# Verify installation
git-ai-reporter --version

# Deactivate when done
deactivate
```

### Using uv (Modern Alternative)

```bash
# Create and manage environment with uv
uv venv git-ai-reporter-env
source git-ai-reporter-env/bin/activate  # Linux/macOS
# git-ai-reporter-env\Scripts\activate  # Windows

# Install with uv (much faster)
uv pip install git-ai-reporter
```

### Using conda/mamba

For data science environments:

```bash
# Create conda environment
conda create -n git-ai-reporter python=3.12
conda activate git-ai-reporter

# Install from conda-forge (if available) or PyPI
conda install -c conda-forge git-ai-reporter
# OR
pip install git-ai-reporter
```

## Installation Verification

### Basic Verification

```bash
# Check version
git-ai-reporter --version

# Verify command availability
which git-ai-reporter

# Display help
git-ai-reporter --help
```

Expected output:
```
Git AI Reporter v1.x.x
Built with Python 3.12.x
```

### Comprehensive Health Check

```bash
# Run diagnostic check
git-ai-reporter --debug --dry-run

# Should report:
# ✅ Python 3.12+ detected
# ✅ All dependencies satisfied  
# ✅ Git executable found
# ✅ API configuration ready
```

### Dependency Verification

```bash
# List all installed packages
pip list | grep -E "(git-ai-reporter|pydantic|gitpython|google-genai)"

# Check for potential conflicts
pip check
```

## Configuration After Installation

### API Key Setup

Create a `.env` file in your project directory:

```bash
# Option 1: Create .env file
echo 'GEMINI_API_KEY="your-api-key-here"' > .env

# Option 2: Set environment variable
export GEMINI_API_KEY="your-api-key-here"

# Option 3: Add to shell profile (persistent)
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Verify Configuration

```bash
# Test configuration
git-ai-reporter --debug --dry-run

# Should show:
# ✅ API key configured
# ✅ All systems ready
```

## Updating Git AI Reporter

### Regular Updates

```bash
# Update to latest version
pip install --upgrade git-ai-reporter

# Update using uv (faster)
uv pip install --upgrade git-ai-reporter

# Check what would be updated (dry run)
pip list --outdated | grep git-ai-reporter
```

### Version History

```bash
# View available versions
pip index versions git-ai-reporter

# View installed version details
pip show git-ai-reporter
```

### Rollback if Needed

```bash
# Rollback to previous version
pip install git-ai-reporter==1.1.0 --force-reinstall

# Or uninstall and reinstall specific version
pip uninstall git-ai-reporter
pip install git-ai-reporter==1.1.0
```

## Uninstallation

### Clean Removal

```bash
# Uninstall package
pip uninstall git-ai-reporter

# Remove virtual environment (if used)
rm -rf git-ai-reporter-env

# Clean pip cache
pip cache purge
```

### Verify Removal

```bash
# Should show "command not found"
git-ai-reporter --version

# Verify package removed
pip list | grep git-ai-reporter
```

## Troubleshooting PyPI Installation

### Common Issues

??? failure "Package not found or outdated"

    **Problem:** PyPI package is not available or outdated.
    
    **Solutions:**
    ```bash
    # Update pip to latest version
    pip install --upgrade pip
    
    # Clear pip cache
    pip cache purge
    
    # Try with explicit index
    pip install --index-url https://pypi.org/simple/ git-ai-reporter
    ```

??? failure "Dependency conflicts"

    **Problem:** Conflicting package versions.
    
    **Solutions:**
    ```bash
    # Check for conflicts
    pip check
    
    # Use virtual environment (recommended)
    python -m venv clean-env
    source clean-env/bin/activate
    pip install git-ai-reporter
    
    # Or force reinstall all dependencies
    pip install --force-reinstall git-ai-reporter
    ```

??? failure "SSL/Certificate errors"

    **Problem:** Network connectivity or certificate issues.
    
    **Solutions:**
    ```bash
    # Upgrade certificates
    pip install --upgrade certifi
    
    # Use trusted hosts (temporary workaround)
    pip install --trusted-host pypi.org --trusted-host pypi.python.org git-ai-reporter
    
    # Update pip with certificates
    pip install --upgrade pip
    ```

??? failure "Permission denied errors"

    **Problem:** Insufficient permissions for installation.
    
    **Solutions:**
    ```bash
    # Use user installation
    pip install --user git-ai-reporter
    
    # Or use virtual environment (recommended)
    python -m venv ~/.local/venvs/git-ai-reporter
    source ~/.local/venvs/git-ai-reporter/bin/activate
    pip install git-ai-reporter
    
    # On Windows, run as Administrator if necessary
    ```

## Performance Optimization

### Installation Speed

For faster installations:

```bash
# Use uv instead of pip (10-100x faster)
pip install uv
uv pip install git-ai-reporter

# Use pip with no-cache for clean installs
pip install --no-cache-dir git-ai-reporter

# Parallel installations (for multiple packages)
pip install git-ai-reporter package2 package3 --upgrade --no-deps
```

### Minimal Installation

For CI/CD or minimal environments:

```bash
# Skip optional dependencies
pip install --no-deps git-ai-reporter

# Then install only required dependencies
pip install pydantic gitpython google-genai rich typer
```

## Next Steps

After successful PyPI installation:

1. **[Configuration →](configuration.md)** - Set up API keys and customize settings
2. **[Quick Start →](../guide/quick-start.md)** - Run your first analysis
3. **[CLI Reference →](../cli/options.md)** - Learn all available options
4. **[Troubleshooting →](../guide/troubleshooting.md)** - Solve common issues

## Related Resources

- **[Security Guide →](../about/security.md)** - Package verification and security best practices
- **[Contributing →](../development/contributing.md)** - Help improve Git AI Reporter
- **[Source Installation →](from-source.md)** - Development and contribution setup