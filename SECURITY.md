# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 8.x     | :white_check_mark: |
| < 8.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in xuansto, please report it responsibly.

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities.
2. Use the [GitHub Security Advisory](https://github.com/xuanyuanchumo/xuansto/security/advisories/new) to report privately.
3. Alternatively, send an email to the maintainers with details about the vulnerability.

### What to Include

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact and affected versions
- Suggested fix (if available)

### Response Timeline

- **Acknowledgment**: Within 48 hours of receiving the report
- **Initial Assessment**: Within 5 business days
- **Resolution**: Depends on severity, critical issues will be prioritized

### Disclosure Policy

- We follow responsible disclosure practices
- Vulnerabilities will be disclosed after a fix is available
- We will credit reporters (unless anonymity is requested)

## Security Best Practices

When using xuansto:

- Never commit `.env` files or secrets to the repository
- Use environment variables for sensitive configuration
- Keep dependencies up to date
- Review code changes before merging
- Run security audits regularly with `pip audit`
