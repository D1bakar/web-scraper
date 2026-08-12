# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.1.x   | Yes       |
| 2.0.x   | Yes       |
| < 2.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability, **please do not open a public issue**.

Report it privately via [GitHub Security Advisories](https://github.com/D1bakar/web-scraper/security/advisories/new) or open a minimal issue requesting a private contact channel.

We aim to acknowledge reports within **72 hours** and provide a fix or mitigation plan as quickly as possible.

## Security Model

Web Scraper Pro implements **defense in depth** — no single control is treated as sufficient on its own.

### Authentication

- **Optional API key** via `API_KEY` environment variable
- When set, all `/api/*` routes (except `/api/health`, docs, and OpenAPI schema) require the `X-API-Key` header
- The dashboard static files are served without auth — **do not expose publicly without a reverse proxy and auth layer in production**

### Network & SSRF Protection

- Outbound scrape URLs are validated before fetch
- Private/reserved IP ranges are blocked by default: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, link-local, etc.
- Hostname resolution is checked — URLs resolving to private IPs are blocked
- Set `ALLOW_PRIVATE_URLS=true` only in trusted local/dev environments
- Only `http://` and `https://` schemes are permitted

### Input Validation

- Pydantic models validate all API request bodies
- CSS selectors are sanitized (length limits, blocked injection patterns)
- URL count capped at 50 per price-compare job
- Request body size limited (default 1 MB via `MAX_REQUEST_BODY_BYTES`)

### HTTP Security Headers

Applied to all responses:

| Header | Value |
|--------|-------|
| `Content-Security-Policy` | Restrictive CSP for dashboard |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Restricts camera, microphone, geolocation |
| `Strict-Transport-Security` | Enabled in production (`ENVIRONMENT=production`) |

### Rate Limiting

- In-memory sliding-window rate limiter per client IP
- Default: 60 requests/minute (configurable via `RATE_LIMIT_PER_MINUTE`)
- Returns HTTP 429 with `Retry-After` header when exceeded

### CORS

- Development: permissive (`*`)
- Production: restricted to `CORS_ORIGINS` (comma-separated list)

### Database

- SQLAlchemy ORM with parameterized queries (no raw string interpolation)
- SQLite WAL mode + busy timeout for concurrent job safety
- Commit retry on lock contention

### Logging

- API keys and secrets are never logged
- Failed auth attempts are logged without the provided key value

## Scope

Security reports we prioritize:

- Remote code execution or server-side injection
- Authentication or authorization bypass
- SSRF or unsafe outbound request handling
- Data exposure across jobs or tenants
- SQL injection or database corruption

General scraping ethics questions belong in the README ethics section.

## Deployment Recommendations

1. Set `ENVIRONMENT=production` and configure `CORS_ORIGINS`
2. Set a strong `API_KEY` and require it on all API calls
3. Place the app behind a reverse proxy (nginx, Caddy) with TLS
4. Do not expose the dashboard to the public internet without authentication
5. Restrict outbound network access in sensitive environments
6. Keep dependencies updated (`pip install -U -r requirements.txt`)
7. Mount persistent storage for `DATABASE_URL` in container deployments
8. Monitor `/api/health/detail` for system status

## What We Do Not Claim

This software is **not unhackable**. It provides industry-standard controls appropriate for a self-hosted scraping tool. Operators remain responsible for network placement, access control, and compliant use.
