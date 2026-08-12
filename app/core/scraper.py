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
from app.core.security import SecurityError, validate_url_ssrf

logger = logging.getLogger(__name__)

DEFAULT_PRICE_SELECTORS = [
    ".price",
    '[itemprop="price"]',
    ".a-price .a-offscreen",
    ".a-price-whole",
    ".price_color",
    "#priceblock_ourprice",
    ".product-price",
    "[data-price]",
    ".sale-price",
    ".current-price",
]

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


@dataclass
class PriceCompareResult:
    url: str
    site_name: str
    price_text: str | None
    price_numeric: float | None
    status: str
    error: str | None
    product_label: str | None = None


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
        allow_private_urls: bool = False,
    ):
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.user_agent = user_agent or (
            "Mozilla/5.0 (compatible; WebScraperPro/2.1; "
            "+https://github.com/D1bakar/web-scraper)"
        )
        self.check_robots = check_robots
        self.allow_private_urls = allow_private_urls
        self._robots = RobotsChecker(self.user_agent, timeout=timeout)
        self._headers = {**DEFAULT_HEADERS, "User-Agent": self.user_agent}

    async def fetch(self, url: str, client: httpx.AsyncClient | None = None) -> BeautifulSoup:
        try:
            url = validate_url_ssrf(url, allow_private=self.allow_private_urls)
        except SecurityError as exc:
            raise ScraperError(str(exc)) from exc

        if self.check_robots:
            allowed = await self._robots.is_allowed(url)
            if not allowed:
                raise ScraperError(
                    "ROBOTS_BLOCKED: This site's robots.txt disallows automated scraping. "
                    "Try the Quotes demo mode, use https://quotes.toscrape.com, or disable "
                    "'Check robots.txt' in Settings and retry."
                )

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
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    status = exc.response.status_code
                    if status == 403:
                        raise ScraperError(
                            "ACCESS_DENIED: This site blocked the request (HTTP 403). "
                            "The server may forbid scrapers. Try Quotes demo or a scraper-friendly site."
                        ) from exc
                    if status == 429:
                        raise ScraperError(
                            "RATE_LIMITED: The site returned HTTP 429 (too many requests). "
                            "Increase delay in Settings and retry later."
                        ) from exc
                    if status == 404:
                        raise ScraperError(
                            f"NOT_FOUND: Page not found (HTTP 404) at {url}"
                        ) from exc
                    logger.warning(
                        "HTTP %d on attempt %d/%d for %s",
                        status, attempt, self.retries, url,
                    )
                    if attempt < self.retries:
                        await asyncio.sleep(min(attempt * 0.5, 2.0))
                except httpx.HTTPError as exc:
                    last_error = exc
                    logger.warning(
                        "Fetch attempt %d/%d failed for %s: %s",
                        attempt, self.retries, url, exc,
                    )
                    if attempt < self.retries:
                        await asyncio.sleep(min(attempt * 0.5, 2.0))
        finally:
            if owns_client and client is not None:
                await client.aclose()

        err_msg = str(last_error)
        if "403" in err_msg:
            raise ScraperError(
                "ACCESS_DENIED: This site blocked the request (HTTP 403). "
                "The server may forbid scrapers. Try Quotes demo or a scraper-friendly site."
            ) from last_error
        if "timeout" in err_msg.lower():
            raise ScraperError(
                f"TIMEOUT: Request timed out after {self.timeout}s. "
                "Try increasing timeout in Settings."
            ) from last_error
        raise ScraperError(
            f"Failed to fetch {url} after {self.retries} attempts: {last_error}"
        ) from last_error

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

    def _site_name_from_url(self, url: str) -> str:
        netloc = urlparse(url).netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc or url

    def _build_price_selectors(self, price_selector: str | None) -> list[str]:
        selectors: list[str] = []
        if price_selector:
            selectors.append(price_selector)
        for selector in DEFAULT_PRICE_SELECTORS:
            if selector not in selectors:
                selectors.append(selector)
        return selectors

    def _parse_price_numeric(self, text: str) -> float | None:
        if not text:
            return None

        cleaned = re.sub(r"[^\d.,]", "", text.strip())
        if not cleaned:
            return None

        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            parts = cleaned.split(",")
            if len(parts[-1]) == 2:
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")

        try:
            return float(cleaned)
        except ValueError:
            return None

    def _extract_price_from_soup(
        self,
        soup: BeautifulSoup,
        selectors: list[str],
    ) -> str | None:
        for selector in selectors:
            for element in soup.select(selector):
                text = (
                    element.get("content")
                    or element.get("data-price")
                    or element.get_text(strip=True)
                )
                if text and re.search(r"\d", text):
                    return text.strip()
        return None

    async def scrape_price_compare(
        self,
        urls: list[str],
        price_selector: str | None = None,
        product_label: str | None = None,
        progress_callback: Any | None = None,
    ) -> list[dict[str, Any]]:
        selectors = self._build_price_selectors(price_selector)
        results: list[dict[str, Any]] = []

        async with httpx.AsyncClient(
            headers=self._headers,
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            for index, url in enumerate(urls, start=1):
                result = PriceCompareResult(
                    url=url,
                    site_name=self._site_name_from_url(url),
                    price_text=None,
                    price_numeric=None,
                    status="error",
                    error=None,
                    product_label=product_label,
                )

                try:
                    soup = await self.fetch(url, client=client)
                    price_text = self._extract_price_from_soup(soup, selectors)
                    if price_text:
                        result.price_text = price_text
                        result.price_numeric = self._parse_price_numeric(price_text)
                        result.status = "ok"
                    else:
                        result.error = (
                            "No price found. Try a different CSS selector "
                            "(right-click the price → Inspect → copy class)."
                        )
                except ScraperError as exc:
                    result.error = str(exc)
                except Exception as exc:
                    logger.exception("Price compare failed for %s", url)
                    result.error = f"Unexpected error: {exc}"

                results.append(asdict(result))

                if progress_callback:
                    await progress_callback(index, len(results))

                if index < len(urls) and self.delay:
                    await asyncio.sleep(self.delay)

        return results
