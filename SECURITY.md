# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security and integrity of StreamPulse and our data engineering pipelines seriously.

If you believe you have found a security vulnerability (such as exposed credentials, unsafe SQL queries, or deserialization bugs):

1. **Do not disclose the issue publicly** (e.g., in public GitHub issues or discussions).
2. Email the maintainers directly or use the GitHub Security Advisory feature.
3. Include detailed steps to reproduce the vulnerability, along with sample payload or code snippets.

### What to Expect
- Acknowledgement of receipt within 48 hours.
- A timeline for mitigation or release of a patch.
- Credit in release notes once resolved (unless anonymity is requested).

### Safe Handling of API Keys & Database Secrets
- Never commit `.env` or plain-text credentials to version control.
- Verify `.gitignore` is active before pushing commits.
- Rotate any API tokens immediately if accidentally pushed.
