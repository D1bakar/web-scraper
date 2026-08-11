# Why Web Scraper Pro?

Most scraping tools are scripts. Web Scraper Pro is a **product** — an industry-ready data extraction platform you can deploy, integrate, and extend.

## Enterprise Value Proposition

| Capability | Benefit |
|------------|---------|
| **REST API + OpenAPI** | Integrate scraping into pipelines, SaaS products, and internal tools without custom glue code |
| **Job queue & persistence** | Track long-running extractions, audit history, and resume operations with SQLite (Redis-ready architecture) |
| **Multi-format export** | Deliver JSON, CSV, or Excel to analysts and downstream systems immediately |
| **Robots.txt compliance** | Reduce legal and operational risk with polite, configurable scraping defaults |
| **Docker & cloud-ready** | Ship to Railway, Render, or any container host in minutes |
| **Premium dashboard** | Give non-technical stakeholders a polished UI without building a frontend |

## Who It's For

- **Data teams** building repeatable extraction workflows
- **Developers** who need a FastAPI backend instead of one-off scripts
- **Startups** prototyping data products with a deployable foundation
- **Engineers** learning production patterns: async I/O, job queues, structured exports, CI/CD

## Design Principles

1. **Polite by default** — delays, retries, robots.txt checks, and clear ethics guidance
2. **API-first** — every UI action maps to a documented REST endpoint
3. **Deployment-ready** — health checks, env-based config, Dockerfile, Procfile
4. **Extensible** — swap SQLite for PostgreSQL, add Redis/Celery, or plug in Playwright when needed

## Live Documentation

Once deployed, interactive API docs are available at:

```
/api/docs      — Swagger UI
/api/redoc     — ReDoc
/api/openapi.json
```

Local default: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
