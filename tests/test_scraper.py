"""Scraper unit tests."""

import pytest

from app.core.exporters import export_csv_bytes, export_json_bytes, prepare_export
from app.core.scraper import AsyncWebScraper


@pytest.mark.asyncio
async def test_scrape_quotes():
    scraper = AsyncWebScraper(delay=0, check_robots=False)
    quotes = await scraper.scrape_quotes(max_pages=1)
    assert len(quotes) > 0
    assert "text" in quotes[0]
    assert "author" in quotes[0]


@pytest.mark.asyncio
async def test_scrape_page_meta():
    scraper = AsyncWebScraper(delay=0, check_robots=False)
    meta = await scraper.scrape_page_meta("https://quotes.toscrape.com")
    assert meta["title"]
    assert meta["url"] == "https://quotes.toscrape.com"


@pytest.mark.asyncio
async def test_scrape_links():
    scraper = AsyncWebScraper(delay=0, check_robots=False)
    links = await scraper.scrape_links("https://quotes.toscrape.com")
    assert len(links) > 0
    assert "url" in links[0]


def test_export_json():
    data = [{"a": 1, "b": "test"}]
    content = export_json_bytes(data)
    assert b'"a": 1' in content


def test_export_csv():
    data = [{"name": "Alice", "tags": ["a", "b"]}]
    content = export_csv_bytes(data)
    assert b"name" in content
    assert b"Alice" in content


def test_prepare_export_formats():
    data = [{"x": 1}]
    json_bytes, json_type, _ = prepare_export(data, "json")
    assert json_type == "application/json"

    csv_bytes, csv_type, _ = prepare_export(data, "csv")
    assert csv_type == "text/csv"

    xlsx_bytes, xlsx_type, suffix = prepare_export(data, "xlsx")
    assert suffix == "xlsx"
    assert len(xlsx_bytes) > 0
