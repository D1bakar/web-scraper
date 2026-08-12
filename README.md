<p align="center">
  <strong>⚡ Web Scraper Pro</strong><br>
  <em>Enterprise-grade web data extraction — API, dashboard, job queue, and exports in one deployable platform.</em>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg" alt="FastAPI"></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Ready-2496ED.svg" alt="Docker"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License"></a>
  <a href="https://github.com/D1bakar/web-scraper/actions/workflows/ci.yml"><img src="https://github.com/D1bakar/web-scraper/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#api-reference">API</a> ·
  <a href="docs/HOW_TO_COMPARE_PRICES.md">Compare Prices Guide</a> ·
  <a href="docs/WHY.md">Why Web Scraper Pro</a> ·
  <a href="/api/docs">Live API Docs</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

Web Scraper Pro transforms polite, structured web extraction into a **deployment-ready product**. Launch scrape jobs from a premium liquid-glass dashboard or REST API, track progress in real time, export results as JSON/CSV/Excel, and persist job history in SQLite — with robots.txt compliance, SSRF protection, rate limiting, and optional API key auth built in.

> **v2.1** — Liquid glass UI overhaul, defense-in-depth security, job retry, health dashboard, webhook notifications, and SQLite concurrency hardening.

---

## Features

| Category | Highlights |
|----------|------------|
| **API** | Async FastAPI REST endpoints with OpenAPI at [`/api/docs`](#live-api-documentation) |
| **UI** | Premium **liquid glass** dashboard — animated mesh background, frosted panels, fluid micro-animations |
| **Modes** | **Price Compare** (featured), quotes demo, page metadata, links, tables, custom CSS selectors |
| **Jobs** | Async queue with SQLite WAL persistence, retry failed jobs, optional webhook on complete |
| **Security** | SSRF protection, optional API key auth, rate limiting, CSP headers, input sanitization |
| **Compliance** | Automatic robots.txt checks with graceful 403/429 error messages |
| **Export** | JSON, CSV, Excel (openpyxl) download endpoints |
| **Ops** | Health dashboard, Docker, env-based config, CI/CD pipeline |
| **CLI** | Optional scripting interface via `cli.py` |

---

## Architecture

```mermaid
flowchart TB
    subgraph Client
        UI[Dashboard UI]
        CLI[CLI Tool]
        API_Client[API Clients]
    end

    subgraph FastAPI["FastAPI Application"]
        Routes[API Routes]
        Static[Static Files]
        Jobs[Job Manager]
        Scraper[Async Scraper]
    end

    subgraph Storage
        SQLite[(SQLite DB)]
    end

    subgraph External
        Web[Target Websites]
        Robots[robots.txt]
    end

    UI --> Routes
    CLI --> Scraper
    API_Client --> Routes
    Routes --> Jobs
    Jobs --> Scraper
    Jobs --> SQLite
    Scraper --> Web
    Scraper --> Robots
    Static --> UI
```

---

## Quick Start

### Windows (PowerShell)

Run from the `web-scraper` folder:

```powershell
cd web-scraper
.\start.ps1
```

Or manually:

```powershell
cd web-scraper
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Linux / macOS

```bash
git clone https://github.com/D1bakar/web-scraper.git
cd web-scraper

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://127.0.0.1:8000** for the dashboard, or **http://127.0.0.1:8000/api/docs** for interactive API documentation.

> **Compare product prices?** See the step-by-step guide: [docs/HOW_TO_COMPARE_PRICES.md](docs/HOW_TO_COMPARE_PRICES.md)

> **Note:** Run `uvicorn` from inside the virtual environment. `requirements.txt` lives in `web-scraper/`, not the parent workspace.

### Docker

```bash
docker compose up --build -d
# Health: GET http://localhost:8000/api/health
```

### CLI (Optional)

```bash
python cli.py quotes --pages 3
python cli.py meta --url https://quotes.toscrape.com
python cli.py links --url https://quotes.toscrape.com
python cli.py tables --url https://example.com
```

---

## Dashboard Preview

The built-in SPA features a **liquid glass** aesthetic with animated gradient mesh backgrounds, floating orbs, frosted glass panels with refractive highlights, and fluid micro-animations throughout.

| View | Description |
|------|-------------|
| **New Scrape** | Price Compare prominently featured; configure mode, URLs, selectors, and launch jobs |
| **Job History** | Browse past jobs — view results, inspect errors, **retry failed jobs** |
| **System Health** | Real-time status: uptime, active jobs, SSRF protection, rate limits, database |
| **Settings** | Configure delay, timeout, retries, user-agent, robots.txt compliance |
| **Results Export** | Download completed jobs as JSON, CSV, or Excel with search/filter |

---

## Live API Documentation

| Endpoint | Description |
|----------|-------------|
| `/api/docs` | Swagger UI (interactive) |
| `/api/redoc` | ReDoc reference |
| `/api/openapi.json` | OpenAPI 3 schema |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check for deployment |
| `GET` | `/api/health/detail` | Detailed system status dashboard |
| `GET` | `/api/settings` | Default scraping settings |
| `POST` | `/api/jobs` | Create a scrape job |
| `POST` | `/api/jobs/{id}/retry` | Retry a failed job |
| `GET` | `/api/jobs` | List job history |
| `GET` | `/api/jobs/{id}` | Get job status |
| `GET` | `/api/jobs/{id}/results` | Get scrape results |
| `GET` | `/api/jobs/{id}/export?format=json\|csv\|xlsx` | Download export |

### Create a Job

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"mode": "meta", "url": "https://quotes.toscrape.com"}'
```

### Scrape Modes

| Mode | Description | Required Fields |
|------|-------------|-----------------|
| `price_compare` | Compare product prices across multiple URLs (up to 50) | `urls`, optional `price_selector`, `product_label` |
| `quotes` | Paginated quotes from quotes.toscrape.com | — |
| `meta` | Page title, description, headings | `url` |
| `links` | Anchor link extraction | `url` |
| `tables` | HTML table extraction | `url` |
| `selectors` | Custom CSS selector extraction | `url`, `selectors` |

---

## Cloud Deployment

### Railway / Render

Use the included `Procfile`:

```
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Set environment variables from `.env.example`. Mount persistent storage for `DATABASE_URL` if you need durable job history.

### Docker (Production)

```bash
docker build -t web-scraper-pro .
docker run -p 8000:8000 -v scraper-data:/app/data web-scraper-pro
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Set to `production` for HSTS and strict CORS |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `DATABASE_URL` | `sqlite:///./data/scraper.db` | SQLite database path |
| `DEFAULT_DELAY` | `1.0` | Seconds between requests |
| `DEFAULT_TIMEOUT` | `15` | Request timeout (seconds) |
| `DEFAULT_RETRIES` | `3` | Retry attempts on failure |
| `CHECK_ROBOTS_TXT` | `true` | Enforce robots.txt compliance |
| `ALLOW_PRIVATE_URLS` | `false` | Allow scraping localhost/private IPs (dev only) |
| `API_KEY` | — | Optional API key (requires `X-API-Key` header) |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins (production) |
| `RATE_LIMIT_PER_MINUTE` | `60` | API rate limit per IP |
| `MAX_REQUEST_BODY_BYTES` | `1048576` | Max request body size (1 MB) |
| `WEBHOOK_URL` | — | Optional webhook POST on job complete/fail |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## Security

Web Scraper Pro implements defense-in-depth security appropriate for a self-hosted scraping tool. See [SECURITY.md](SECURITY.md) for the full security model.

| Control | Description |
|---------|-------------|
| **SSRF Protection** | Blocks private/reserved IP ranges unless `ALLOW_PRIVATE_URLS=true` |
| **API Key Auth** | Optional via `API_KEY` env — requires `X-API-Key` header |
| **Rate Limiting** | Per-IP sliding window (default 60 req/min) |
| **Security Headers** | CSP, X-Frame-Options, nosniff, HSTS in production |
| **Input Validation** | URL, selector, and body size validation on all inputs |
| **CORS** | Restricted to configured origins in production |
| **SQLite WAL** | WAL mode + busy timeout for concurrent job safety |

**Production checklist:**
1. Set `ENVIRONMENT=production`
2. Set a strong `API_KEY`
3. Configure `CORS_ORIGINS` to your domain
4. Place behind a reverse proxy with TLS
5. Do not expose the dashboard publicly without auth

---

## Project Structure

```
web-scraper/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/routes.py        # REST API endpoints
│   ├── core/
│   │   ├── scraper.py       # Async scraping engine
│   │   ├── jobs.py          # Job queue manager
│   │   ├── robots.py        # robots.txt checker
│   │   ├── exporters.py     # JSON/CSV/Excel export
│   │   └── config.py        # Environment config
│   ├── models/schemas.py    # Pydantic models
│   ├── db/                  # SQLAlchemy models & session
│   └── static/              # Dashboard UI (HTML/CSS/JS)
├── docs/WHY.md              # Enterprise value proposition
├── cli.py                   # Optional CLI
├── tests/                   # pytest suite
├── Dockerfile
├── docker-compose.yml
├── Procfile
├── .github/workflows/ci.yml
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
├── .env.example
└── requirements.txt
```

---

## Development

```bash
pip install -r requirements-dev.txt
ruff check app/ cli.py tests/
pytest tests/ -v
```

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for setup, testing, and pull request guidelines.

---

## Ethics & Responsible Scraping

Web scraping carries real responsibility. This platform includes robots.txt compliance and polite defaults, but **you** are accountable for how it is used.

- Check `robots.txt` and Terms of Service before scraping any site
- Use configurable delays to avoid overloading servers
- Respect rate limits and back off on errors
- Do not scrape authenticated, paywalled, or prohibited content

---

## License

This project is released under the [MIT License](LICENSE).

---

<p align="center">
  <sub>Web Scraper Pro — enterprise-ready data extraction, engineered for clarity and responsible use.</sub><br>
  <sub><a href="https://github.com/D1bakar/web-scraper">github.com/D1bakar/web-scraper</a></sub>
</p>
