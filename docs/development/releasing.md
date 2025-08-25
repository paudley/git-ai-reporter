# Release Process for git-ai-reporter

This document provides comprehensive instructions for releasing new versions of git-ai-reporter to PyPI with full supply chain security via digital attestations.

## 🔒 Security & Attestations Overview

**git-ai-reporter** uses PyPI's digital attestations and Trusted Publishing to provide cryptographic proof that published packages come directly from this GitHub repository. This ensures:

- ✅ **Package Provenance**: Cryptographic link between PyPI packages and source code
- ✅ **Supply Chain Security**: Protection against package tampering or substitution
- ✅ **Automated Security**: No long-lived API tokens, automatic attestation generation
- ✅ **User Verification**: Users can verify package authenticity using PyPI's tools

## 📋 Prerequisites

### One-Time Setup: Trusted Publishing Configuration

Before making your first release, configure Trusted Publishing on PyPI:

1. **PyPI Production Setup**:
   - Visit https://pypi.org/manage/account/publishing/
   - Click "Add a new pending publisher"
   - Fill in:
     - **PyPI Project Name**: `git-ai-reporter`
     - **Owner**: `paudley`
     - **Repository name**: `git-ai-reporter`
     - **Workflow filename**: `publish.yml`
     - **Environment name**: `pypi`
   - Click "Add"

2. **TestPyPI Setup** (for testing):
   - Visit https://test.pypi.org/manage/account/publishing/
   - Repeat the same process with environment name: `testpypi`

3. **Verify GitHub Environment Protection**:
   - Go to GitHub → Settings → Environments
   - Ensure `pypi` environment has protection rules (manual approval recommended)
   - Ensure `testpypi` environment exists for testing

## 📏 Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0) - Incompatible API changes
- **MINOR** version (0.X.0) - New functionality, backwards compatible  
- **PATCH** version (0.0.X) - Bug fixes, backwards compatible

## ✅ Pre-Release Checklist

Before creating any release, ensure all quality gates pass:

### 1. Code Quality Verification
```bash
# All tests must pass with comprehensive core functionality coverage
uv run pytest -v --cov=src

# No linting warnings allowed (CRITICAL)
./scripts/lint.sh

# Security scan
./scripts/security-scan.sh
```

### 2. Documentation Updates
- [ ] README.md reflects current features and capabilities
- [ ] Run `git-ai-reporter --repo-path . --pre-release X.Y.Z` to generate release-ready documentation
- [ ] Review generated documentation - should show version as "released" not "preparing"
- [ ] Verify CHANGELOG.txt moved [Unreleased] entries to [vX.Y.Z] section with current date
- [ ] API documentation is current and complete
- [ ] All module documentation files are updated

### 3. Dependency Review
- [ ] No known security vulnerabilities in dependencies
- [ ] Dependency versions are appropriately pinned
- [ ] `uv.lock` is up to date

### 4. Version Consistency
- [ ] Version updated in `src/git_ai_reporter/__init__.py`
- [ ] Version matches what will be tagged
- [ ] No development suffixes (`.dev0`) in production releases

## 🚀 Fully Automated Release Process

The release process is now **fully automated**. Simply push a version tag and everything else happens automatically!

### Step 1: Update Version

Update the version in `src/git_ai_reporter/__init__.py`:
```python
__version__ = "X.Y.Z"  # New version number
```

### Step 2: Generate Pre-Release Documentation

Use git-reporter itself to update the project's documentation for the upcoming release:

```bash
# Generate updated documentation with release formatting
git-ai-reporter --repo-path . --pre-release X.Y.Z

# Review the generated files:
# - NEWS.md: Will show "Released vX.Y.Z 🚀" in the header
# - CHANGELOG.txt: Will move [Unreleased] changes to [vX.Y.Z] - YYYY-MM-DD
# - DAILY_UPDATES.md: Will include recent daily activity
```

**Important**: 
- Replace `X.Y.Z` with your actual version number (e.g., `1.2.3`)
- The `--pre-release` flag formats documentation as if the release has already happened
- Review the generated content for accuracy and edit if necessary
- This documentation will be committed as part of the release

### Step 3: Commit Changes

```bash
git add -A
git commit -m "chore: release version X.Y.Z"
git push origin main
```

### Step 4: Create and Push Git Tag

```bash
git tag -a vX.Y.Z -m "Release version X.Y.Z"
git push origin vX.Y.Z
```

**That's it!** The rest is completely automated.

### Step 5: Automated Release Process

The GitHub Actions workflow will automatically:
- ✅ Create a GitHub release with generated release notes
- ✅ Build the package distribution
- ✅ Generate build provenance attestations  
- ✅ Upload to PyPI with digital attestations
- ✅ Verify installation across multiple platforms
- ✅ Create cryptographic proof linking the package to this exact commit

The release will include:
- Automatic release notes generated from commit messages
- Links to CHANGELOG.txt and NEWS.md for detailed changes
- Installation instructions for the specific version
- Security information about digital attestations

## 🧪 Testing Releases

### Test with TestPyPI

To test a release before publishing to production PyPI:

1. **Trigger TestPyPI Workflow**:
   - Go to GitHub Actions → "Publish to PyPI"
   - Click "Run workflow"
   - ✅ Check "Publish to TestPyPI instead of PyPI"
   - Click "Run workflow"

2. **Test Installation**:
   ```bash
   # Install from TestPyPI
   pip install -i https://test.pypi.org/simple/ git-ai-reporter==X.Y.Z
   
   # Verify functionality
   git-ai-reporter --version
   git-ai-reporter --help
   ```

3. **Verify Attestations on TestPyPI**:
   - Visit https://test.pypi.org/project/git-ai-reporter/
   - Look for attestation badges on the release files
   - Click on files to see attestation details

## 🔍 Post-Release Verification

### 1. Verify PyPI Package

```bash
# Install the released package
pip install git-ai-reporter==X.Y.Z

# Verify functionality
git-ai-reporter --version
git-ai-reporter --help
```

### 2. Verify Attestations

**Web Interface Verification**:
1. Visit https://pypi.org/project/git-ai-reporter/
2. Click on the release version
3. Look for attestation badges next to download files
4. Click on files to view attestation details

**API Verification**:
```bash
# Using PyPI's Integrity API (example for version 0.1.0)
curl "https://pypi.org/simple/git-ai-reporter/" | grep "data-provenance-attestation"

# Or using pypi-attestations tool (if installed)
pip install pypi-attestations  
python -m pypi_attestations verify git-ai-reporter==X.Y.Z
```

### 3. Update Development Version

After successful release, update to next development version:
```python
# In src/git_ai_reporter/__init__.py
__version__ = "X.Y.Z.dev0"  # Next development version
```

### 4. Announce Release

- [ ] Update project website if applicable
- [ ] Notify users through appropriate channels
- [ ] Share release highlights on social media

## 🚨 Troubleshooting

### Attestation Issues

**Problem**: Attestations not appearing on PyPI
- **Check**: Ensure Trusted Publishing is configured correctly
- **Check**: Verify `id-token: write` permission in workflow
- **Check**: Confirm using `pypa/gh-action-pypi-publish@release/v1` (v1.11.0+)
- **Solution**: Re-run the workflow or check GitHub Actions logs

**Problem**: "Trusted publishing not configured" error
- **Check**: PyPI project must exist and have Trusted Publisher configured
- **Solution**: Follow the Prerequisites section to set up Trusted Publishing

### Build Failures

**Problem**: Build fails during package creation
- **Check**: All dependencies specified correctly in `pyproject.toml`
- **Check**: `uv.lock` is synchronized with dependencies
- **Check**: All required files included in `MANIFEST.in`
- **Check**: Version number is valid and doesn't already exist on PyPI

**Manual Build Testing**: To test the build process locally:
```bash
# Clean any previous builds
rm -rf dist/

# Build with uv (same command used in GitHub Actions)
uv build

# Verify the build
uv tool run twine check dist/*
```

### Upload Failures  

**Problem**: Upload to PyPI fails
- **Check**: Version number is unique (not already published)
- **Check**: Package metadata is valid
- **Check**: Trusted Publishing is correctly configured
- **Check**: GitHub environment protection rules aren't blocking

### Installation Issues

**Problem**: Users report installation problems
- **Test**: Install in clean virtual environments
- **Check**: Python version compatibility in `pyproject.toml`  
- **Check**: All runtime dependencies are correctly specified
- **Verify**: Package works on different operating systems

## 🛡️ Security Releases

For security-related releases:

1. **Follow Responsible Disclosure**: Coordinate with security researchers if applicable
2. **Priority Release**: Release patch version immediately for critical security fixes
3. **Update SECURITY.md**: Document the security issue after release  
4. **Security Advisory**: Create GitHub Security Advisory
5. **User Notification**: Notify users through security advisory and release notes
6. **CVE Coordination**: Work with CVE coordinators if necessary

## 📚 Additional Resources

- [PyPI Trusted Publishing Documentation](https://docs.pypi.org/trusted-publishers/)
- [PyPI Attestations Documentation](https://docs.pypi.org/attestations/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)

## 📞 Need Help?

If you encounter issues during the release process:

- **GitHub Issues**: Open an issue for release process problems
- **Security Concerns**: Email [secure@blackcat.ca](mailto:secure@blackcat.ca)
- **PyPI Issues**: Contact PyPI support for platform-specific problems