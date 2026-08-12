# Changelog

All notable changes to Web Scraper Pro are documented here.

## [2.3.1] — 2026-08-12 — Stability Patch

### Fixed
- **Rate limiting** no longer blocks job status polling, health probes, stats, or selector hints
- **Localhost** gets a higher effective rate limit (3×) for dashboard demo usage
- **Try example** now disables robots.txt for demo runs and shows a clear toast
- **Hero overlay** dismisses with Escape key
- **start.ps1 / start.bat** stops stale processes on port 8000 before launch (fixes old v2.1 server serving outdated API)
- Default rate limit raised to **120/min**; `.env.example` user agent updated to 2.3.1

### Added
- `tests/test_try_example_modes.py` — validates all 11 Try example configs end-to-end
- `tests/test_rate_limit.py` — rate limit exemption coverage
- `scripts/test_all_modes.py` — manual API smoke test for all modes
- README **Troubleshooting** section

## [2.3.0] — 2026-08-12 — The Revolutionary Release

### Added — Viral-Ready UI
- **Full-screen hero overlay** on first visit — *"Extract the web. Instantly."*
- **Mode grid** — 11 visual mode cards with glow selection (replaces dropdown-first UX)
- **Floating particles & iridescent glass** — screenshot-worthy liquid glass aesthetic
- **Confetti pulse** on successful job completion
- **Price compare bar chart** — animated CSS visualization of price rankings
- **Share buttons** — Copy results + Share on Twitter with pre-filled tweet
- **Open Graph meta tags** and inline SVG favicon for social sharing
- **"Powered by open source"** footer badge

### Added — Documentation & Identity
- **PRODUCT.md** — vision statement and revolutionary positioning
- **docs/SOCIAL.md** — share-ready tweets, Instagram captions, HN/Reddit posts
- **docs/HOW_TO_COMPARE_PRICES.md** — polished price compare guide
- **.github/SOCIAL_PREVIEW.md** — link preview spec for GitHub and OG
- README completely rewritten — ASCII hero, comparison table, star history CTA
- **OPEN_SOURCE.md** rewritten as inspiring manifesto

### Changed
- Tagline unified everywhere: **Extract the web. Instantly.**
- Version bumped to 2.3.0 across all modules
- `docs/WHY_DIFFERENT.md` — punchier comparison-focused rewrite
- Root `v2/README.md` — professional pointer to web-scraper

### Fixed
- UI micro-interactions: button ripple/glow, skeleton shimmer, view morphing
- Mobile-first responsive improvements for hero and mode grid

## [2.2.0] — 2026-08-12

### Added — Revolutionary Scrape Modes
- **SITEMAP** — crawl sitemap.xml and sitemap indexes
- **EMAIL_EXTRACT** — extract emails from page text and mailto links
- **JSON_LD** — schema.org structured data
- **SOCIAL_META** — Open Graph and Twitter Card metadata
- **READABILITY** — heuristic main article content extraction

### Added — Features & API
- Bulk CSV URL import, smart selector hints, performance stats, health probes

### Added — UI & UX
- CSV import, keyboard shortcuts, loading skeletons, error boundaries

## [2.1.0] — Previous Release
- Liquid glass UI overhaul
- Price compare mode
- Security hardening (SSRF, rate limiting, API key auth)
- Job retry, health dashboard, webhook notifications
