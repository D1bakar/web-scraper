#!/usr/bin/env python3
"""CLI for the web scraper."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.exporters import export_csv, export_json
from src.scraper import ScraperError, WebScraper


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Polite web scraper — quotes, page metadata, and link extraction.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py quotes --pages 3
  python main.py quotes --format csv --output output/quotes.csv
  python main.py meta --url https://quotes.toscrape.com
  python main.py links --url https://quotes.toscrape.com
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

    return parser


def cmd_quotes(args: argparse.Namespace) -> int:
    scraper = WebScraper(delay=args.delay)
    print(f"Scraping quotes (max pages: {args.pages or 'all'})...")

    quotes = scraper.scrape_quotes(max_pages=args.pages)
    rows = scraper.quotes_to_dicts(quotes)

    output = Path(args.output)
    if args.format == "json":
        path = export_json(rows, output)
    else:
        if not output.suffix:
            output = output.with_suffix(".csv")
        path = export_csv(rows, output)

    print(f"Scraped {len(quotes)} quotes -> {path}")
    if quotes:
        sample = quotes[0]
        print(f"\nSample: \"{sample.text[:60]}...\" — {sample.author}")
    return 0


def cmd_meta(args: argparse.Namespace) -> int:
    scraper = WebScraper(delay=0)
    meta = scraper.scrape_page_meta(args.url)
    data = scraper.meta_to_dict(meta)

    print(f"Title:       {meta.title}")
    print(f"Description: {meta.description or '(none)'}")
    print(f"Headings:    {len(meta.headings)} found")
    for h in meta.headings[:5]:
        print(f"  - {h}")

    if args.output:
        path = export_json(data, args.output)
        print(f"\nSaved -> {path}")
    return 0


def cmd_links(args: argparse.Namespace) -> int:
    scraper = WebScraper(delay=0)
    links = scraper.scrape_links(args.url, same_domain=not args.all_domains)

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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "quotes":
            return cmd_quotes(args)
        if args.command == "meta":
            return cmd_meta(args)
        if args.command == "links":
            return cmd_links(args)
    except ScraperError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
