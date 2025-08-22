# Release Process

This document describes the process for releasing new versions of git-ai-reporter to PyPI.

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0) - Incompatible API changes
- **MINOR** version (0.X.0) - New functionality, backwards compatible
- **PATCH** version (0.0.X) - Bug fixes, backwards compatible

## Pre-Release Checklist

Before creating a release, ensure:

1. **All tests pass with comprehensive core functionality coverage**
   ```bash
   uv run pytest -v --cov=src
   ```

2. **No linting warnings**
   ```bash
   ./scripts/lint.sh
   ```

3. **Documentation is up to date**
   - README.md reflects current features
   - CHANGELOG.txt has been updated
   - API documentation is current

4. **Dependencies are reviewed**
   - No security vulnerabilities
   - Versions are appropriately pinned

## Release Steps

### 1. Update Version

Update the version in `src/git_reporter/__init__.py`:
```python
__version__ = "X.Y.Z"  # New version number
```

### 2. Update CHANGELOG

Add a new section to CHANGELOG.txt:
```
## [X.Y.Z] - YYYY-MM-DD
### Added
- New features...
### Changed
- Changes...
### Fixed
- Bug fixes...
```

### 3. Commit Changes

```bash
git add -A
git commit -m "chore: release version X.Y.Z"
git push origin main
```

### 4. Create Git Tag

```bash
git tag -a vX.Y.Z -m "Release version X.Y.Z"
git push origin vX.Y.Z
```

### 5. Create GitHub Release

1. Go to https://github.com/paudley/git-ai-reporter/releases
2. Click "Draft a new release"
3. Select the tag `vX.Y.Z`
4. Title: `v.X.Y.Z`
5. Generate release notes
6. Add highlights from CHANGELOG.txt
7. Publish release

The GitHub Actions workflow will automatically:
- Build the package
- Upload to PyPI
- Verify installation on multiple platforms

## Testing on TestPyPI

To test a release before publishing to PyPI:

1. Run the publish workflow manually with TestPyPI option:
   - Go to Actions → Publish to PyPI
   - Click "Run workflow"
   - Check "Publish to TestPyPI"

2. Test the package:
   ```bash
   pip install -i https://test.pypi.org/simple/ git-ai-reporter
   ```

## Post-Release

After a successful release:

1. **Verify PyPI package**
   ```bash
   pip install git-ai-reporter==X.Y.Z
   git-ai-reporter --version
   ```

2. **Update development version**
   ```python
   __version__ = "X.Y.Z.dev0"  # Next development version
   ```

3. **Announce the release**
   - Update project website if applicable
   - Notify users through appropriate channels

## Troubleshooting

### Build Failures

If the build fails:
1. Check GitHub Actions logs
2. Verify all dependencies are specified
3. Ensure MANIFEST.in includes all necessary files

### PyPI Upload Issues

If upload fails:
1. Check PyPI API tokens are configured
2. Verify package metadata is valid
3. Ensure version number is unique

### Installation Problems

If users report installation issues:
1. Test on clean environments
2. Verify Python version compatibility
3. Check for missing dependencies

## Security Releases

For security fixes:
1. Follow responsible disclosure practices
2. Release patch version immediately
3. Update SECURITY.md with details
4. Notify users through security advisory