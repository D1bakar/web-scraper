"""Verify Try-example demo URLs work for every scrape mode."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.scraper import AsyncWebScraper, ScraperError

APP_JS = Path(__file__).resolve().parents[1] / "app" / "static" / "js" / "app.js"


def _load_mode_config() -> dict:
    text = APP_JS.read_text(encoding="utf-8")
    start = text.index("const MODE_CONFIG = ")
    start = text.index("{", start)
    depth = 0
    for idx in range(start, len(text)):
        if text[idx] == "{":
            depth += 1
        elif text[idx] == "}":
            depth -= 1
            if depth == 0:
                block = text[start : idx + 1]
                break
    else:
        raise RuntimeError("MODE_CONFIG block not found")

    # MODE_CONFIG uses JS syntax — normalize for JSON parsing of example fields.
    normalized = block.replace("const MODE_CONFIG = ", "").strip()
    normalized = normalized.replace("'", '"')
    normalized = normalized.replace(",\n  };", "\n  }")
    # Keep only keys we need via regex-free minimal transforms for example URLs.
    import re

    examples: dict[str, dict] = {}
    for mode in (
        "price_compare",
        "quotes",
        "meta",
        "links",
        "tables",
        "selectors",
        "sitemap",
        "email_extract",
        "json_ld",
        "social_meta",
        "readability",
    ):
        section = re.search(rf"{mode}:\s*\{{(.*?)\n\s*\}},", block, re.S)
        assert section, f"Missing MODE_CONFIG entry for {mode}"
        body = section.group(1)
        has_example = "hasExample: true" in body
        examples[mode] = {"hasExample": has_example}
        if m := re.search(r"example:\s*'([^']+)'", body):
            examples[mode]["example"] = m.group(1)
        if m := re.search(r"exampleUrls:\s*\[(.*?)\]\.join", body, re.S):
            urls = re.findall(r"'([^']+)'", m.group(1))
            examples[mode]["exampleUrls"] = urls
        if m := re.search(r"exampleSelectors:\s*'([^']+)'", body):
            examples[mode]["exampleSelectors"] = m.group(1).split("\\n")
        if m := re.search(r"examplePriceSelector:\s*'([^']+)'", body):
            examples[mode]["examplePriceSelector"] = m.group(1)

    return examples


MODE_EXAMPLES = _load_mode_config()


@pytest.mark.parametrize("mode", list(MODE_EXAMPLES.keys()))
@pytest.mark.asyncio
async def test_try_example_mode_works(mode: str):
    cfg = MODE_EXAMPLES[mode]
    assert cfg.get("hasExample"), f"{mode} should expose Try example"
    scraper = AsyncWebScraper(delay=0, check_robots=False, retries=1)

    if mode == "price_compare":
        urls = cfg["exampleUrls"]
        results = await scraper.scrape_price_compare(
            urls, price_selector=cfg["examplePriceSelector"]
        )
        assert len(results) >= 2
        assert any(r.get("status") == "ok" for r in results)
    elif mode == "quotes":
        quotes = await scraper.scrape_quotes(max_pages=1)
        assert len(quotes) > 0
    elif mode == "meta":
        meta = await scraper.scrape_page_meta(cfg["example"])
        assert meta.get("title")
    elif mode == "links":
        links = await scraper.scrape_links(cfg["example"], same_domain=True)
        assert len(links) > 0
    elif mode == "tables":
        tables = await scraper.scrape_tables(cfg["example"])
        assert len(tables) > 0
    elif mode == "selectors":
        data = await scraper.scrape_selectors(cfg["example"], cfg["exampleSelectors"])
        assert len(data) > 0
    elif mode == "sitemap":
        try:
            urls = await scraper.scrape_sitemap(cfg["example"], max_urls=10)
            assert len(urls) > 0
        except ScraperError as exc:
            pytest.fail(f"sitemap example failed: {exc}")
    elif mode == "email_extract":
        emails = await scraper.scrape_emails(cfg["example"])
        assert len(emails) > 0
    elif mode == "json_ld":
        blocks = await scraper.scrape_json_ld(cfg["example"])
        assert len(blocks) > 0
    elif mode == "social_meta":
        meta = await scraper.scrape_social_meta(cfg["example"])
        assert meta.get("url")
    elif mode == "readability":
        article = await scraper.scrape_readability(cfg["example"])
        assert article.get("word_count", 0) > 0


def test_mode_config_has_eleven_modes():
    assert len(MODE_EXAMPLES) == 11
