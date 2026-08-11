#!/usr/bin/env python3
"""CLI for Web Scraper Pro — optional command-line interface."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from app.core.exporters import export_csv, export_json
from app.core.scraper import AsyncWebScraper, ScraperError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Web Scraper Pro CLI — polite web data extraction.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py quotes --pages 3
  python cli.py quotes --format csv --output output/quotes.csv
  python cli.py meta --url https://quotes.toscrape.com
  python cli.py links --url https://quotes.toscrape.com
  python cli.py tables --url https://example.com
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    quotes = sub.add_parser("quotes", help="Scrape quotes from quotes.toscrape.com")
    quotes.add_argument("--pages", type=int, default=None, help="Max pages to scrape")
    quotes.add_argument("--delay", type=float, default=1.0, help="Delay between pages (seconds)")
    quotes.add_argument("--format", choices=["json", "csv"], default="json")
    quotes.add_argument("--output", default="output/quotes.json", help="Output file path")

    meta = sub.add_parser("meta", help="Extract title, description, and headings from a URL")
    meta.add_argument("--url", required=True, help="Page URL to scrape")
    meta.add_argument("--output", default=None, help="Optional JSON output file")

    links = sub.add_parser("links", help="Extract links from a page")
    links.add_argument("--url", required=True, help="Page URL to scrape")
    links.add_argument("--all-domains", action="store_true", help="Include external links")
    links.add_argument("--output", default=None, help="Optional JSON output file")

    tables = sub.add_parser("tables", help="Extract HTML tables from a page")
    tables.add_argument("--url", required=True, help="Page URL to scrape")
    tables.add_argument("--output", default=None, help="Optional JSON output file")

    return parser


async def cmd_quotes(args: argparse.Namespace) -> int:
    scraper = AsyncWebScraper(delay=args.delay, check_robots=False)
    print(f"Scraping quotes (max pages: {args.pages or 'all'})...")

    rows = await scraper.scrape_quotes(max_pages=args.pages)
    output = Path(args.output)

    if args.format == "json":
        path = export_json(rows, output)
    else:
        if not output.suffix:
            output = output.with_suffix(".csv")
        path = export_csv(rows, output)

    print(f"Scraped {len(rows)} quotes -> {path}")
    if rows:
        sample = rows[0]
        print(f"\nSample: \"{sample['text'][:60]}...\" — {sample['author']}")
    return 0


async def cmd_meta(args: argparse.Namespace) -> int:
    scraper = AsyncWebScraper(delay=0)
    data = await scraper.scrape_page_meta(args.url)

    print(f"Title:       {data['title']}")
    print(f"Description: {data['description'] or '(none)'}")
    print(f"Headings:    {len(data['headings'])} found")
    for h in data["headings"][:5]:
        print(f"  - {h}")

    if args.output:
        path = export_json(data, args.output)
        print(f"\nSaved -> {path}")
    return 0


async def cmd_links(args: argparse.Namespace) -> int:
    scraper = AsyncWebScraper(delay=0)
    links = await scraper.scrape_links(args.url, same_domain=not args.all_domains)

    print(f"Found {len(links)} links on {args.url}")
    for link in links[:10]:
        label = link["text"] or "(no text)"
        print(f"  {label}: {link['url']}")
    if len(links) > 10:
        print(f"  ... and {len(links) - 10} more")

    if args.output:
        path = export_json(links, args.output)
        print(f"\nSaved -> {path}")
    return 0


async def cmd_tables(args: argparse.Namespace) -> int:
    scraper = AsyncWebScraper(delay=0)
    tables = await scraper.scrape_tables(args.url)

    print(f"Found {len(tables)} tables on {args.url}")
    for t in tables:
        print(f"  Table {t['table_index']}: {t['row_count']} rows")

    if args.output:
        path = export_json(tables, args.output)
        print(f"\nSaved -> {path}")
    return 0


async def async_main(args: argparse.Namespace) -> int:
    if args.command == "quotes":
        return await cmd_quotes(args)
    if args.command == "meta":
        return await cmd_meta(args)
    if args.command == "links":
        return await cmd_links(args)
    if args.command == "tables":
        return await cmd_tables(args)
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        return asyncio.run(async_main(args))
    except ScraperError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
