# Roadmap

Future work is tracked as [GitHub Issues](https://github.com/D1bakar/web-scraper/issues). This document summarizes planned directions.

---

## Shipped (v2.1)

- [x] Liquid glass dashboard UI
- [x] REST API with OpenAPI docs
- [x] Job queue with SQLite persistence and retry
- [x] Price Compare mode (multi-URL)
- [x] SSRF protection, rate limiting, optional API key auth
- [x] JSON / CSV / Excel export
- [x] robots.txt compliance
- [x] Docker + docker-compose
- [x] GitHub Actions CI
- [x] Health check endpoints

---

## Planned

| Priority | Feature | Issue |
|----------|---------|-------|
| High | Bulk URL import from CSV | [#1](https://github.com/D1bakar/web-scraper/issues/1) |
| High | Scheduled / recurring scrape jobs | [#2](https://github.com/D1bakar/web-scraper/issues/2) |
| High | JavaScript-rendered pages (Playwright) | [#4](https://github.com/D1bakar/web-scraper/issues/4) |
| Medium | Proxy rotation support | [#3](https://github.com/D1bakar/web-scraper/issues/3) |
| Medium | User authentication & multi-tenant | [#5](https://github.com/D1bakar/web-scraper/issues/5) |
| Medium | AI-powered selector detection | [#9](https://github.com/D1bakar/web-scraper/issues/9) |
| Medium | Price comparison at scale (1000+ sites) | [#7](https://github.com/D1bakar/web-scraper/issues/7) |
| Low | Cloud deployment guides (AWS / GCP) | [#6](https://github.com/D1bakar/web-scraper/issues/6) |
| Low | Mobile app / PWA | [#8](https://github.com/D1bakar/web-scraper/issues/8) |
| Low | Performance benchmarking suite | [#10](https://github.com/D1bakar/web-scraper/issues/10) |

Browse all open issues: [github.com/D1bakar/web-scraper/issues](https://github.com/D1bakar/web-scraper/issues)

---

## How to influence the roadmap

1. Open a [feature request issue](https://github.com/D1bakar/web-scraper/issues/new) with your use case.
2. Comment on existing issues with 👍 or detailed requirements.
3. Submit a pull request — see [CONTRIBUTING.md](../CONTRIBUTING.md).

Contributions that align with **API-first design**, **security defaults**, and **polite scraping** are especially welcome.
