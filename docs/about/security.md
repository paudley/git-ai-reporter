# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security of Git AI Reporter seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please DO NOT:
- Open a public GitHub issue for security vulnerabilities
- Post about the vulnerability on social media or forums

### Please DO:
- Email us directly at [secure@blackcat.ca](mailto:secure@blackcat.ca)
- Include the word "SECURITY" in the subject line
- Provide detailed steps to reproduce the vulnerability
- Include the impact and potential exploit scenarios

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Assessment**: We will investigate and validate the reported vulnerability within 7 days
- **Resolution**: We aim to release a patch within 30 days of validation
- **Disclosure**: We will coordinate public disclosure with you after the patch is released

## Security Best Practices for Users

### API Key Management

- **Never commit API keys** to version control
- Store API keys in environment variables or `.env` files
- Use different API keys for development and production
- Rotate API keys regularly
- Monitor API key usage for anomalies

### Safe Usage

1. **Input Validation**: The tool validates repository paths and date ranges
2. **Output Sanitization**: Generated content is sanitized to prevent injection
3. **Cache Security**: Cache files contain sensitive data - protect the cache directory
4. **Network Security**: All API calls use HTTPS

### Dependencies

We regularly update dependencies to address known vulnerabilities:

```bash
# Check for outdated packages
uv pip list --outdated

# Update all dependencies
uv pip install --upgrade -e .[dev]
```

## Package Attestations & Supply Chain Security

Git AI Reporter implements state-of-the-art supply chain security through PyPI's digital attestations system:

### What Are Package Attestations?

Package attestations provide cryptographic proof that:
- ✅ The package was built directly from this GitHub repository
- ✅ The package has not been tampered with since publication
- ✅ The exact source code and commit hash that produced the package
- ✅ The build environment and workflow used for creation

### How to Verify Package Attestations

**Method 1: PyPI Web Interface**
1. Visit https://pypi.org/project/git-ai-reporter/
2. Click on the version you want to verify
3. Look for 🛡️ attestation badges next to download files
4. Click on the files to view detailed attestation information
5. Verify the source repository matches `https://github.com/paudley/git-ai-reporter`

**Method 2: PyPI Integrity API**
```bash
# Check for attestations using curl
curl "https://pypi.org/simple/git-ai-reporter/" | grep "data-provenance-attestation"

# Verify attestations programmatically
pip install pypi-attestations
python -m pypi_attestations verify git-ai-reporter==0.1.0
```

**Method 3: Sigstore Verification**
```bash
# Install sigstore tools
pip install sigstore

# Verify package provenance (when available)
python -m sigstore verify --certificate <cert-file> --signature <sig-file> <package-file>
```

### Attestation Security Benefits

- **Provenance Tracking**: Verify packages come from this exact repository
- **Tamper Detection**: Detect any modifications to packages post-publication
- **Supply Chain Integrity**: End-to-end verification from source to installation
- **Automated Security**: No manual verification steps required for basic protection
- **Transparency**: Public ledger of all build and publish activities

### What's Attested

For each package release, attestations provide proof of:
1. **Source Repository**: `https://github.com/paudley/git-ai-reporter`
2. **Exact Commit Hash**: SHA that was used to build the package
3. **Build Environment**: GitHub Actions runner and workflow details
4. **Build Timestamp**: When the package was built and published
5. **Workflow Details**: Exact GitHub Actions workflow that performed the build

### Trusted Publishing

Git AI Reporter uses PyPI's Trusted Publishing mechanism:
- 🔐 **No Long-Lived API Tokens**: Uses OpenID Connect for secure authentication
- 🤖 **Automated Publishing**: Direct from GitHub Actions with no manual intervention
- 🔍 **Audit Trail**: Complete logging of all publishing activities
- 🛡️ **Environment Protection**: Manual approval required for production releases

## Security Features

Git AI Reporter includes several security features:

- **No Secret Logging**: API keys and sensitive data are never logged
- **Input Validation**: All user inputs are validated and sanitized
- **Secure Defaults**: Security-conscious default configurations
- **Error Handling**: Errors don't expose sensitive information
- **Token Limits**: Automatic prompt truncation prevents token overflow attacks
- **Supply Chain Security**: Digital attestations verify package provenance
- **Secure Publishing**: Trusted Publishing eliminates long-lived API tokens

## Vulnerability Disclosure Policy

We follow responsible disclosure practices:

1. Security vulnerabilities are privately reported
2. We work with reporters to understand and validate issues
3. Patches are developed and tested
4. Updates are released with security advisories
5. Public disclosure follows after users have time to update

## Security Updates

Stay informed about security updates:

- Watch the repository for releases
- Subscribe to security advisories

## Hall of Fame

We thank the following security researchers for responsibly disclosing vulnerabilities:

*This list will be updated as vulnerabilities are reported and fixed.*

## Contact

For security concerns, contact:
- Email: [secure@blackcat.ca](mailto:secure@blackcat.ca)
- PGP Key:

-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v2

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
=fCTf
-----END PGP PUBLIC KEY BLOCK-----


For general questions, use:
- GitHub Issues: [https://github.com/paudley/git-ai-reporter/issues](https://github.com/paudley/git-ai-reporter/issues)
- Email: [paudley@blackcat.ca](mailto:paudley@blackcat.ca)
