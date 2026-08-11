# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.x     | Yes       |
| < 2.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability, **please do not open a public issue**.

Instead, report it privately via [GitHub Security Advisories](https://github.com/D1bakar/web-scraper/security/advisories/new) or by opening a minimal issue asking for a private contact channel.

We aim to acknowledge reports within **72 hours** and provide a fix or mitigation plan as quickly as possible.

## Scope

Security reports we prioritize include:

- Remote code execution or server-side injection
- Authentication or authorization bypass (if auth is added in future releases)
- Data exposure across tenants or jobs
- SSRF or unsafe outbound request handling in the scraper

General scraping ethics questions belong in the README ethics section, not security reports.

## Best Practices for Deployments

- Do not expose the dashboard publicly without authentication in production.
- Restrict outbound network access if running in sensitive environments.
- Keep dependencies updated and monitor CI for failing security checks.
