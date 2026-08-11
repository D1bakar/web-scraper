"""Async web scraping engine."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.robots import RobotsChecker

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]
    source_url: str


@dataclass
class PageMeta:
    title: str
    url: str
    description: str
    headings: list[str]


class ScraperError(Exception):
    """Raised when scraping fails."""


class AsyncWebScraper:
    """Async, polite web scraper with retries and robots.txt support."""

    def __init__(
        self,
        delay: float = 1.0,
        timeout: int = 15,
        retries: int = 3,
        user_agent: str | None = None,
        check_robots: bool = True,
    ):
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.user_agent = user_agent or (
            "Mozilla/5.0 (compatible; WebScraperPro/2.0; "
            "+https://github.com/D1bakar/web-scraper)"
        )
        self.check_robots = check_robots
        self._robots = RobotsChecker(self.user_agent, timeout=timeout)
        self._headers = {**DEFAULT_HEADERS, "User-Agent": self.user_agent}

    async def fetch(self, url: str, client: httpx.AsyncClient | None = None) -> BeautifulSoup:
        if not url.startswith(("http://", "https://")):
            raise ScraperError(f"Invalid URL: {url}")

        if self.check_robots:
            allowed = await self._robots.is_allowed(url)
            if not allowed:
                raise ScraperError(f"Blocked by robots.txt: {url}")

        last_error: Exception | None = None
        owns_client = client is None

        if owns_client:
            client = httpx.AsyncClient(
                headers=self._headers,
                timeout=self.timeout,
                follow_redirects=True,
            )

        try:
            assert client is not None
            for attempt in range(1, self.retries + 1):
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    return BeautifulSoup(response.text, "lxml")
                except httpx.HTTPError as exc:
                    last_error = exc
                    logger.warning("Fetch attempt %d/%d failed for %s: %s", attempt, self.retries, url, exc)
                    if attempt < self.retries:
                        await asyncio.sleep(min(attempt * 0.5, 2.0))
        finally:
            if owns_client and client is not None:
                await client.aclose()

        raise ScraperError(f"Failed to fetch {url} after {self.retries} attempts: {last_error}") from last_error

    async def scrape_quotes(
        self,
        base_url: str = "https://quotes.toscrape.com",
        max_pages: int | None = None,
        progress_callback: Any | None = None,
    ) -> list[dict[str, Any]]:
        quotes: list[Quote] = []
        url: str | None = base_url
        page_count = 0

        async with httpx.AsyncClient(
            headers=self._headers,
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            while url:
                if max_pages is not None and page_count >= max_pages:
                    break

                soup = await self.fetch(url, client=client)
                page_count += 1

                for block in soup.select("div.quote"):
                    text_el = block.select_one("span.text")
                    author_el = block.select_one("small.author")
                    tag_els = block.select("a.tag")

                    if not text_el or not author_el:
                        continue

                    quotes.append(
                        Quote(
                            text=text_el.get_text(strip=True).strip("\u201c\u201d\u2018\u2019\"'"),
                            author=author_el.get_text(strip=True),
                            tags=[t.get_text(strip=True) for t in tag_els],
                            source_url=url,
                        )
                    )

                if progress_callback:
                    await progress_callback(page_count, len(quotes))

                next_link = soup.select_one("li.next a")
                url = urljoin(url, next_link["href"]) if next_link else None

                if url and self.delay:
                    await asyncio.sleep(self.delay)

        return [asdict(q) for q in quotes]

    async def scrape_page_meta(self, url: str) -> dict[str, Any]:
        soup = await self.fetch(url)

        title = soup.title.get_text(strip=True) if soup.title else ""
        description = ""
        desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if desc_tag and desc_tag.get("content"):
            description = desc_tag["content"].strip()

        headings = [
            el.get_text(strip=True)
            for el in soup.find_all(re.compile(r"^h[1-3]$"))
            if el.get_text(strip=True)
        ]

        meta = PageMeta(
            title=title,
            url=url,
            description=description,
            headings=headings[:20],
        )
        return asdict(meta)

    async def scrape_links(self, url: str, same_domain: bool = True) -> list[dict[str, str]]:
        soup = await self.fetch(url)
        base_domain = urlparse(url).netloc
        seen: set[str] = set()
        links: list[dict[str, str]] = []

        for anchor in soup.find_all("a", href=True):
            href = urljoin(url, anchor["href"].strip())
            if not href.startswith(("http://", "https://")):
                continue
            if same_domain and urlparse(href).netloc != base_domain:
                continue
            if href in seen:
                continue
            seen.add(href)
            links.append({"url": href, "text": anchor.get_text(strip=True)[:120]})

        return links

    async def scrape_tables(self, url: str) -> list[dict[str, Any]]:
        soup = await self.fetch(url)
        tables: list[dict[str, Any]] = []

        for idx, table in enumerate(soup.find_all("table")):
            headers: list[str] = []
            header_row = table.find("tr")
            if header_row:
                headers = [
                    th.get_text(strip=True) or f"col_{i}"
                    for i, th in enumerate(header_row.find_all(["th", "td"]))
                ]

            rows: list[dict[str, str]] = []
            data_rows = table.find_all("tr")[1:] if headers else table.find_all("tr")

            for row in data_rows:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                if headers:
                    row_data = {
                        headers[i] if i < len(headers) else f"col_{i}": cell.get_text(strip=True)
                        for i, cell in enumerate(cells)
                    }
                else:
                    row_data = {f"col_{i}": cell.get_text(strip=True) for i, cell in enumerate(cells)}
                rows.append(row_data)

            if rows:
                tables.append({"table_index": idx, "headers": headers, "rows": rows, "row_count": len(rows)})

        return tables

    async def scrape_selectors(self, url: str, selectors: list[str]) -> list[dict[str, Any]]:
        soup = await self.fetch(url)
        results: list[dict[str, Any]] = []

        for selector in selectors:
            elements = soup.select(selector)
            items = [
                {
                    "text": el.get_text(strip=True)[:500],
                    "html": str(el)[:1000],
                }
                for el in elements
            ]
            results.append({
                "selector": selector,
                "count": len(items),
                "items": items,
            })

        return results
