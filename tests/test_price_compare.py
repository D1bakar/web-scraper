"""Price compare mode tests."""

import time

import pytest

from app.core.scraper import AsyncWebScraper


@pytest.mark.asyncio
async def test_scrape_price_compare_demo():
    scraper = AsyncWebScraper(delay=0, check_robots=False)
    urls = [
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
    ]
    results = await scraper.scrape_price_compare(urls, price_selector=".price_color")

    assert len(results) == 2
    assert all(r["status"] == "ok" for r in results)
    assert all(r["price_text"] for r in results)
    assert all(r["price_numeric"] is not None for r in results)
    assert results[0]["site_name"] == "books.toscrape.com"


@pytest.mark.asyncio
async def test_scrape_price_compare_partial_failure():
    scraper = AsyncWebScraper(delay=0, check_robots=False, retries=1)
    urls = [
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "https://example.invalid/product",
    ]
    results = await scraper.scrape_price_compare(urls, price_selector=".price_color")

    assert len(results) == 2
    assert results[0]["status"] == "ok"
    assert results[1]["status"] == "error"
    assert results[1]["error"]


def test_price_compare_requires_urls(client):
    response = client.post("/api/jobs", json={"mode": "price_compare", "urls": []})
    assert response.status_code == 422


def test_price_compare_job_lifecycle(client):
    create = client.post(
        "/api/jobs",
        json={
            "mode": "price_compare",
            "urls": [
                "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
            ],
            "price_selector": ".price_color",
            "check_robots": False,
            "delay": 0,
        },
    )
    assert create.status_code == 202
    job_id = create.json()["job_id"]

    job = None
    for _ in range(40):
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("completed", "failed"):
            break
        time.sleep(0.5)

    assert job["status"] == "completed"

    results = client.get(f"/api/jobs/{job_id}/results").json()
    assert results["item_count"] == 2
    assert all(row["status"] == "ok" for row in results["data"])
