# UI Redesign Plan — Web Scraper Pro v2.6

## Audit Summary (Phase 1)

### Architecture
- **Stack:** Vanilla HTML/CSS/JS — no framework. FastAPI serves `app/static/`.
- **Entry:** `index.html` — hero overlay, sidebar nav (desktop), bottom nav (mobile), 6 views.
- **Styles:** `css/style.css` (~2250 lines) — liquid glass v2.5, orbs, mode grid, responsive breakpoints.
- **Logic:** `js/app.js` (~1800 lines) — IIFE, `MODE_CONFIG` (11 modes), polling, exports, PWA, settings tabs.
- **PWA:** `manifest.json`, `sw.js` (static cache only).

### Views & IDs (preserved)
| View | Section ID | Key hooks |
|------|-----------|-----------|
| New Scrape | `view-scrape` | `#scrape-form`, `#mode-grid`, `#live-status`, `#results-section` |
| Job History | `view-history` | `#history-table`, `#history-cards` |
| Jobs (mobile) | `view-jobs` | `#jobs-dashboard` |
| System Health | `view-health` | `#health-dashboard`, `#stats-dashboard` |
| Settings | `view-settings` | `#settings-form`, schedules/webhooks/apikeys panels |
| More (mobile) | `view-more` | `#more-grid`, PWA install |

### API contracts (unchanged)
- `POST /api/jobs`, `GET /api/jobs/{id}`, `/results`, `/export`
- `/api/health`, `/api/health/detail`, `/api/stats`, `/api/dashboard/summary`
- Schedules, webhooks, API keys, auth — all untouched

### Pain points addressed
1. Heavy neon gradients — toned to Linear/Vercel restraint
2. No light theme — added Dark / Light / System with tokens
3. Form complexity upfront — progressive disclosure via advanced panel
4. Scrape flow order — URL hero → modes → advanced → CTA
5. Missing appearance settings — theme + motion prefs in Settings

## Implementation (Phases 2–9)

- `css/design-tokens.css` — semantic tokens, dark/light/system
- `css/style.css` — imports tokens, refined components, nav indicator, empty states
- `index.html` — restructured scrape flow, appearance settings, semantic markup
- `js/app.js` — theme switcher, nav indicator, advanced panel, empty-state CTAs

## Phase 10
- pytest (66+ tests), version 2.6.0, CHANGELOG, commit & push
