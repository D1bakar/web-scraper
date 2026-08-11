# Web Scraper

A polite, CLI-based Python web scraper with three modes: **quotes**, **page metadata**, and **link extraction**.

Built for learning and demo purposes. Uses [quotes.toscrape.com](https://quotes.toscrape.com) — a site designed specifically for scraping practice.

## Features

- **Quotes scraper** — paginated scraping with author and tags
- **Page metadata** — title, description, and headings from any public URL
- **Link extractor** — collect same-domain or all links from a page
- **Export** — JSON and CSV output
- **Polite crawling** — configurable delay between requests and proper User-Agent

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Scrape quotes (first 3 pages)
python main.py quotes --pages 3

# Export as CSV
python main.py quotes --pages 5 --format csv --output output/quotes.csv

# Extract metadata from a page
python main.py meta --url https://quotes.toscrape.com

# Extract links
python main.py links --url https://quotes.toscrape.com --output output/links.json
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `quotes` | Scrape quotes from quotes.toscrape.com |
| `meta` | Extract title, description, headings from a URL |
| `links` | Extract anchor links from a URL |

### Options (quotes)

| Flag | Default | Description |
|------|---------|-------------|
| `--pages` | all | Max pages to scrape |
| `--delay` | 1.0 | Seconds between page requests |
| `--format` | json | Output format: `json` or `csv` |
| `--output` | output/quotes.json | Output file path |

## Project Structure

```
web-scraper/
├── main.py              # CLI entry point
├── requirements.txt
├── src/
│   ├── scraper.py       # Core scraping logic
│   └── exporters.py     # JSON / CSV export
└── output/              # Generated files (gitignored)
```

## Ethics & Best Practices

- Always check a site's `robots.txt` and Terms of Service before scraping
- Use delays between requests (`--delay`) to avoid overloading servers
- This project uses quotes.toscrape.com, which explicitly allows scraping
- Do not scrape sites that prohibit it or require authentication

## License

MIT
