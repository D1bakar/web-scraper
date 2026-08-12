# Changelog

All notable changes to Web Scraper Pro are documented here.

## [2.2.0] — 2026-08-12

### Added — Revolutionary Scrape Modes
- **SITEMAP** — crawl sitemap.xml and sitemap indexes to extract all URLs
- **EMAIL_EXTRACT** — extract emails from page text and mailto: links
- **JSON_LD** — extract schema.org structured data (products, prices, ratings)
- **SOCIAL_META** — Open Graph and Twitter Card metadata extraction
- **READABILITY** — heuristic main article content extraction

### Added — Features & API
- **Bulk CSV URL import** — upload CSV for price_compare and meta batch jobs (`POST /api/jobs/import-csv`)
- **Smart selector hints** — heuristic CSS selector suggestions (`GET /api/selector-hints`)
- **Performance stats** — job benchmarks (`GET /api/stats`) with success rate and avg duration
- **Health probes** — Kubernetes-ready liveness (`/api/health/live`) and readiness (`/api/health/ready`)

### Added — UI & UX
- New modes in dropdown with icons and descriptions
- CSV import buttons for price compare and batch meta
- Smart selector hint chips with confidence scores
- Keyboard shortcut: Ctrl+Enter to submit
- Loading skeletons for history and health views
- Smooth page transitions between views
- Error boundaries for frontend resilience
- Performance stats panel in System Health view

### Added — Deployment & Open Source
- `render.yaml` and `railway.toml` for one-click deploy
- `OPEN_SOURCE.md` — project philosophy and contribution guide
- `.github/CODE_OF_CONDUCT.md` — community standards
- GitHub issue templates (bug report, feature request)
- 10 new roadmap issues (#11–#20)

### Changed
- Version bumped to 2.2.0 across all modules
- README redesigned with feature matrix and architecture diagram
- `docs/WHY_DIFFERENT.md` updated with new mode comparisons
- `docs/DEPLOYMENT.md` expanded with probe and env var documentation

### Fixed
- Batch meta scrape supports multiple URLs via CSV or textarea
- Improved retry backoff in scraper fetch loop
- Mobile responsive improvements for new UI components

## [2.1.0] — Previous Release
- Liquid glass UI overhaul
- Price compare mode
- Security hardening (SSRF, rate limiting, API key auth)
- Job retry, health dashboard, webhook notifications
- 28 tests with CI pipeline
