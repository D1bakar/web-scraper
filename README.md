# Web Scraper

> **Precision-engineered CLI for polite, structured web data extraction.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4.12%2B-orange.svg)](https://www.crummy.com/software/BeautifulSoup/)

A production-minded Python command-line tool for extracting structured data from the web. Built with deliberate architecture, clean separation of concerns, and responsible crawling defaults — engineered by an elite AI scientist & programmer for reliability, clarity, and extensibility.

**About:** A polite, multi-mode CLI web scraper for quotes, page metadata, and link extraction — designed for learning, prototyping, and production-ready data pipelines.

---

## Overview

Web Scraper provides three focused extraction modes behind a single, intuitive CLI:

| Mode | Purpose |
|------|---------|
| **`quotes`** | Paginated quote scraping from [quotes.toscrape.com](https://quotes.toscrape.com) with author and tag metadata |
| **`meta`** | Page-level metadata — title, description, and heading structure from any public URL |
| **`links`** | Anchor link extraction with same-domain or cross-domain filtering |

Each mode returns clean, exportable data in JSON or CSV. Requests are throttled by default, headers are set responsibly, and errors surface with actionable messages.

---

## Features

- **Three extraction modes** — quotes, page metadata, and link harvesting
- **Structured output** — JSON and CSV export with predictable schemas
- **Polite crawling** — configurable inter-request delay and proper `User-Agent`
- **Modular architecture** — scraping logic, export layer, and CLI cleanly separated
- **Zero configuration** — works out of the box against [quotes.toscrape.com](https://quotes.toscrape.com), a site designed for scraping practice
- **Type-safe internals** — dataclass models and explicit error handling throughout

---

## Installation

**Requirements:** Python 3.10 or later

```bash
git clone https://github.com/D1bakar/web-scraper.git
cd web-scraper

# Recommended: use a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

---

## Usage

### Scrape quotes

```bash
# First 3 pages (default output: output/quotes.json)
python main.py quotes --pages 3

# Export as CSV with custom delay
python main.py quotes --pages 5 --format csv --output output/quotes.csv --delay 1.5
```

### Extract page metadata

```bash
python main.py meta --url https://quotes.toscrape.com

# Save structured JSON
python main.py meta --url https://quotes.toscrape.com --output output/meta.json
```

### Extract links

```bash
# Same-domain links only
python main.py links --url https://quotes.toscrape.com

# Include external links
python main.py links --url https://quotes.toscrape.com --all-domains --output output/links.json
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `quotes` | Scrape paginated quotes from quotes.toscrape.com |
| `meta` | Extract title, description, and headings from a URL |
| `links` | Extract anchor links from a page |

### `quotes` options

| Flag | Default | Description |
|------|---------|-------------|
| `--pages` | all | Maximum number of pages to scrape |
| `--delay` | `1.0` | Seconds between page requests |
| `--format` | `json` | Output format: `json` or `csv` |
| `--output` | `output/quotes.json` | Output file path |

### `meta` / `links` options

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | *(required)* | Target page URL |
| `--output` | stdout only | Optional JSON output file |
| `--all-domains` | off | *(links only)* Include external links |

---

## Project Structure

```
web-scraper/
├── main.py                 # CLI entry point and argument parsing
├── requirements.txt        # Runtime dependencies
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Core scraping engine (quotes, meta, links)
│   └── exporters.py        # JSON / CSV serialization
├── output/                 # Generated artifacts (gitignored)
├── LICENSE
└── README.md
```

---

## Ethics & Responsible Scraping

Web scraping carries real responsibility. This tool is built with polite defaults, but **you** are accountable for how it is used.

- **Check `robots.txt` and Terms of Service** before scraping any site
- **Use `--delay`** to avoid overloading servers; default is 1 second between requests
- **Respect rate limits** and back off on errors
- **Do not scrape** authenticated, paywalled, or explicitly prohibited content
- This project defaults to [quotes.toscrape.com](https://quotes.toscrape.com), which explicitly permits scraping for educational use

Scrape ethically. Extract responsibly.

---

## License

This project is released under the [MIT License](LICENSE).

---

<p align="center">
  <sub>Crafted with precision — engineered for clarity, reliability, and responsible data extraction.</sub>
</p>
