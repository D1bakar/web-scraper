# Changelog

All notable changes to Web Scraper Pro are documented here.

## [2.5.0] — 2026-08-12 — Premium Fluid UI

### Added — Design System
- **Design tokens** — spacing scale, typography scale, color palette, shadows, blur levels
- **Page load fade-in** — subtle entrance animation on dashboard load
- **Staggered reveals** — mode grid, results rows/cards, price chart bars, job cards
- **View transitions** — smooth enter/exit between Scrape, Jobs, History, Settings, More
- **Bottom nav indicator** — animated sliding pill for active tab
- **Mode grid descriptions** — icon + label + short desc on each of 11 mode cards
- **Job card status coding** — color-coded left border (running/completed/failed/pending)
- **`@prefers-reduced-motion`** — respects accessibility settings across all animations

### Changed — UI/UX Polish
- **Refined glass panels** — gradient fill, stronger borders, hover elevation
- **Fluid buttons** — animated gradient, loading shimmer, press feedback
- **Progress bars** — flowing multi-color gradient animation
- **Toasts** — slide-in + fade-out with spring easing
- **Price chart** — cheapest bar highlighted green with glow
- **Section headers** — consistent icon + title + subtitle layout across all views
- **Hero overlay** — SVG gradient lightning icon with pulse glow
- **Form focus rings** — accent glow on all inputs
- **Smooth scroll to results** after job completion

### Fixed
- Confetti skipped when reduced motion is preferred

## [2.4.0] — 2026-08-12 — Mobile-First Release

### Added — Mobile UI
- **Bottom navigation** on screens <768px: New Scrape, Jobs, History, Settings, More
- **Mobile dashboard** with NEW SCRAPE CTA, active/total job stats
- **Results & history cards** on mobile; tables remain on desktop
- **Touch targets** minimum 44px; 16px input font (prevents iOS zoom)
- **Job monitoring** with elapsed time, progress, expandable status sections
- **Form draft** persistence in sessionStorage
- **Network reconnect** toasts; offline awareness
- **Copy button** per result field on mobile cards
- **Raw JSON** expandable section
- **Collapsible icon sidebar** on tablet (768–1024px)

### Added — PWA
- `manifest.json` with standalone display and theme color
- Service worker for **static asset caching only**
- Install prompt banner on mobile
- Apple mobile web app meta tags
- PWA icons (192/512)

### Added — Backend MVP
- **Optional admin login** (`ADMIN_USER`/`ADMIN_PASSWORD`) with secure session cookie
- **Schedules CRUD** — hourly/daily interval-based job scheduling
- **Webhooks CRUD** — test endpoint + delivery log
- **API Keys** — generate/revoke, shown once on create
- **`/api/dashboard/summary`** endpoint for mobile dashboard
- **Job pagination** — `offset`, `mobile=true` (limit 10)

### Added — Docs & Tests
- `docs/MOBILE_AUDIT.md` — full mobile audit report
- `docs/MOBILE.md` — phone usage and PWA install guide
- `tests/test_mobile_api.py` — 11 new tests (66 total passing)

### Changed
- GZip compression middleware for API responses
- Webhook dispatch supports DB-registered hooks + env `WEBHOOK_URL`
- Version bumped to **2.4.0** across all modules

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
