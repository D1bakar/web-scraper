"""Tests for v2.2 scrape modes and API endpoints."""

import time

import pytest

from app.core.scraper import AsyncWebScraper, ScraperError


@pytest.mark.asyncio
async def test_scrape_emails():
    scraper = AsyncWebScraper(delay=0, check_robots=False)
    emails = await scraper.scrape_emails("https://quotes.toscrape.com")
    assert isinstance(emails, list)


@pytest.mark.asyncio
async def test_scrape_json_ld():
    scraper = AsyncWebScraper(delay=0, check_robots=False)
    data = await scraper.scrape_json_ld(
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    )
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_scrape_social_meta():
    scraper = AsyncWebScraper(delay=0, check_robots=False)
    meta = await scraper.scrape_social_meta("https://quotes.toscrape.com")
    assert meta["url"] == "https://quotes.toscrape.com"
    assert "open_graph" in meta
    assert "twitter" in meta


@pytest.mark.asyncio
async def test_scrape_readability():
    scraper = AsyncWebScraper(delay=0, check_robots=False)
    article = await scraper.scrape_readability("https://quotes.toscrape.com")
    assert article["word_count"] > 0
    assert len(article["text"]) > 0


@pytest.mark.asyncio
async def test_scrape_sitemap():
    scraper = AsyncWebScraper(delay=0, check_robots=False, retries=1)
    # Use a minimal inline sitemap-like test via direct XML URL or accept empty-error
    try:
        urls = await scraper.scrape_sitemap("https://quotes.toscrape.com", max_urls=10)
        assert isinstance(urls, list)
    except ScraperError as exc:
        assert "No URLs found" in str(exc) or "sitemap" in str(exc).lower()


@pytest.mark.asyncio
async def test_suggest_selectors():
    scraper = AsyncWebScraper(delay=0, check_robots=False)
    hints = await scraper.suggest_selectors(
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    )
    assert hints["recommended_price"] == ".price_color"
    assert len(hints["price_selectors"]) > 0


def test_stats_endpoint(client):
    client.post("/api/jobs", json={"mode": "quotes", "max_pages": 1, "check_robots": False})
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "success_rate" in data
    assert "avg_job_duration_seconds" in data
    assert "by_mode" in data


def test_health_probes(client):
    live = client.get("/api/health/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"

    ready = client.get("/api/health/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_selector_hints_endpoint(client):
    response = client.get(
        "/api/selector-hints",
        params={"url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_price"]


def test_csv_import_endpoint(client):
    csv_content = (
        "url\n"
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html\n"
        "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html\n"
    )
    response = client.post(
        "/api/jobs/import-csv?mode=price_compare",
        files={"file": ("urls.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    job = None
    for _ in range(40):
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("completed", "failed"):
            break
        time.sleep(0.5)

    assert job["status"] == "completed"


def test_email_extract_job_lifecycle(client):
    create = client.post(
        "/api/jobs",
        json={
            "mode": "email_extract",
            "url": "https://quotes.toscrape.com",
            "check_robots": False,
        },
    )
    assert create.status_code == 202
    job_id = create.json()["job_id"]

    for _ in range(30):
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("completed", "failed"):
            break
        time.sleep(0.5)

    assert job["status"] == "completed"
