"""Async web scraping engine."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import xml.etree.ElementTree as ET
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

DEFAULT_TITLE_SELECTORS = [
    "h1",
    '[itemprop="name"]',
    ".product-title",
    ".product-name",
    "#productTitle",
    ".title",
]

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

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
            "Mozilla/5.0 (compatible; WebScraperPro/2.3.1; "
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

    async def scrape_sitemap(
        self,
        url: str,
        max_urls: int = 500,
        progress_callback: Any | None = None,
    ) -> list[dict[str, str]]:
        """Crawl sitemap.xml and extract all URLs."""
        parsed = urlparse(url)
        if not parsed.path.endswith(".xml"):
            base = url.rstrip("/")
            candidates = [f"{base}/sitemap.xml", f"{base}/sitemap_index.xml"]
        else:
            candidates = [url]

        seen: set[str] = set()
        urls: list[dict[str, str]] = []
        errors: list[str] = []

        async with httpx.AsyncClient(
            headers=self._headers,
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            to_fetch = list(candidates)

            while to_fetch and len(urls) < max_urls:
                sitemap_url = to_fetch.pop(0)
                if sitemap_url in seen:
                    continue
                seen.add(sitemap_url)

                try:
                    response = await client.get(sitemap_url)
                    response.raise_for_status()
                    root = ET.fromstring(response.text)
                except (httpx.HTTPError, ET.ParseError) as exc:
                    errors.append(f"{sitemap_url}: {exc}")
                    continue

                ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                locs = root.findall(".//sm:loc", ns) or root.findall(".//loc")

                for loc in locs:
                    loc_url = (loc.text or "").strip()
                    if not loc_url:
                        continue
                    if loc_url.endswith(".xml") and "sitemap" in loc_url.lower():
                        if loc_url not in seen:
                            to_fetch.append(loc_url)
                        continue
                    if loc_url not in {u["url"] for u in urls}:
                        urls.append({"url": loc_url, "source_sitemap": sitemap_url})
                        if len(urls) >= max_urls:
                            break

                if progress_callback:
                    await progress_callback(len(urls), len(urls))

                if self.delay:
                    await asyncio.sleep(self.delay)

        if not urls:
            detail = errors[0] if errors else "No sitemap found"
            raise ScraperError(
                f"No URLs found in sitemap. Tried {len(seen)} location(s). Last error: {detail}"
            )

        return urls

    async def scrape_emails(self, url: str) -> list[dict[str, str]]:
        """Extract email addresses from a page."""
        soup = await self.fetch(url)
        found: dict[str, dict[str, str]] = {}

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if href.lower().startswith("mailto:"):
                email = href[7:].split("?")[0].strip()
                if EMAIL_PATTERN.match(email):
                    found.setdefault(email.lower(), {
                        "email": email,
                        "source": "mailto",
                        "context": anchor.get_text(strip=True)[:120] or email,
                    })

        text = soup.get_text(" ", strip=True)
        for match in EMAIL_PATTERN.finditer(text):
            email = match.group()
            key = email.lower()
            if key not in found and not key.endswith((".png", ".jpg", ".gif", ".webp")):
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 40)
                found[key] = {
                    "email": email,
                    "source": "page_text",
                    "context": text[start:end].strip(),
                }

        return list(found.values())

    async def scrape_json_ld(self, url: str) -> list[dict[str, Any]]:
        """Extract JSON-LD structured data (schema.org)."""
        soup = await self.fetch(url)
        results: list[dict[str, Any]] = []

        for idx, script in enumerate(soup.find_all("script", type="application/ld+json")):
            raw = script.string or script.get_text()
            if not raw or not raw.strip():
                continue
            try:
                data = json.loads(raw.strip())
            except json.JSONDecodeError:
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                entry: dict[str, Any] = {
                    "index": idx,
                    "type": item.get("@type", "Unknown"),
                    "name": item.get("name") or item.get("headline"),
                    "url": item.get("url"),
                }
                if "offers" in item:
                    offers = item["offers"]
                    if isinstance(offers, dict):
                        entry["price"] = offers.get("price")
                        entry["price_currency"] = offers.get("priceCurrency")
                    elif isinstance(offers, list) and offers:
                        entry["price"] = offers[0].get("price")
                        entry["price_currency"] = offers[0].get("priceCurrency")
                if "aggregateRating" in item:
                    rating = item["aggregateRating"]
                    if isinstance(rating, dict):
                        entry["rating_value"] = rating.get("ratingValue")
                        entry["review_count"] = rating.get("reviewCount")
                entry["raw_keys"] = list(item.keys())[:20]
                results.append(entry)

        return results

    async def scrape_social_meta(self, url: str) -> dict[str, Any]:
        """Extract Open Graph and Twitter Card metadata."""
        soup = await self.fetch(url)
        og: dict[str, str] = {}
        twitter: dict[str, str] = {}
        standard: dict[str, str] = {}

        for meta in soup.find_all("meta"):
            prop = meta.get("property", "") or meta.get("name", "")
            content = meta.get("content", "")
            if not prop or not content:
                continue
            prop_lower = prop.lower()
            if prop_lower.startswith("og:"):
                og[prop_lower[3:]] = content.strip()
            elif prop_lower.startswith("twitter:"):
                twitter[prop_lower[8:]] = content.strip()
            elif prop_lower in ("description", "keywords", "author", "theme-color"):
                standard[prop_lower] = content.strip()

        title = og.get("title") or twitter.get("title")
        if not title and soup.title:
            title = soup.title.get_text(strip=True)

        return {
            "url": url,
            "title": title,
            "open_graph": og,
            "twitter": twitter,
            "standard_meta": standard,
            "og_image": og.get("image"),
            "twitter_image": twitter.get("image"),
        }

    async def scrape_readability(self, url: str) -> dict[str, Any]:
        """Extract main article content using heuristic content extraction."""
        soup = await self.fetch(url)

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        candidates: list[tuple[int, Any]] = []
        for el in soup.find_all(["article", "main", "div", "section"]):
            text = el.get_text(" ", strip=True)
            word_count = len(text.split())
            if word_count < 50:
                continue
            link_text = sum(len(a.get_text(strip=True)) for a in el.find_all("a"))
            link_density = link_text / max(len(text), 1)
            score = word_count * (1 - link_density)
            candidates.append((score, el))

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            content_el = candidates[0][1]
        else:
            content_el = soup.body or soup

        paragraphs = [
            p.get_text(" ", strip=True)
            for p in content_el.find_all(["p", "h1", "h2", "h3", "li"])
            if len(p.get_text(strip=True)) > 20
        ]
        text = "\n\n".join(paragraphs) if paragraphs else content_el.get_text("\n", strip=True)
        title_el = soup.find("h1") or soup.find("title")
        title = title_el.get_text(strip=True) if title_el else ""

        return {
            "url": url,
            "title": title,
            "text": text[:50000],
            "word_count": len(text.split()),
            "excerpt": text[:300] + ("..." if len(text) > 300 else ""),
        }

    async def suggest_selectors(self, url: str) -> dict[str, Any]:
        """Heuristic CSS selector suggestions for price and title elements."""
        soup = await self.fetch(url)
        suggestions: list[dict[str, Any]] = []

        def score_element(el: Any, selector: str, kind: str) -> None:
            text = el.get_text(strip=True)
            if kind == "price" and not re.search(r"\d", text):
                return
            if kind == "title" and len(text) < 3:
                return
            cls = el.get("class", [])
            el_id = el.get("id", "")
            confidence = 0.5
            if kind == "price":
                if re.search(r"[\$£€₹]", text):
                    confidence += 0.2
                if any(k in str(cls).lower() for k in ("price", "cost", "amount")):
                    confidence += 0.15
                if el.get("itemprop") == "price":
                    confidence += 0.25
            else:
                if el.name == "h1":
                    confidence += 0.3
                if el.get("itemprop") == "name":
                    confidence += 0.2
                if any(k in str(cls).lower() for k in ("title", "product", "name")):
                    confidence += 0.1

            suggestions.append({
                "selector": selector,
                "kind": kind,
                "sample_text": text[:80],
                "confidence": round(min(confidence, 0.99), 2),
                "tag": el.name,
                "class": " ".join(cls) if isinstance(cls, list) else cls,
                "id": el_id or None,
            })

        for selector in DEFAULT_PRICE_SELECTORS:
            for el in soup.select(selector)[:2]:
                score_element(el, selector, "price")

        for selector in DEFAULT_TITLE_SELECTORS:
            for el in soup.select(selector)[:2]:
                score_element(el, selector, "title")

        for el in soup.find_all(attrs={"class": True}):
            classes = el.get("class", [])
            if not isinstance(classes, list):
                continue
            for cls in classes:
                cls_lower = cls.lower()
                if any(k in cls_lower for k in ("price", "cost", "amount")):
                    sel = f".{cls}"
                    if sel not in {s["selector"] for s in suggestions}:
                        score_element(el, sel, "price")
                if any(k in cls_lower for k in ("title", "product-name", "product_title")):
                    sel = f".{cls}"
                    if sel not in {s["selector"] for s in suggestions}:
                        score_element(el, sel, "title")

        suggestions.sort(key=lambda s: s["confidence"], reverse=True)
        unique: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        for s in suggestions:
            key = f"{s['kind']}:{s['selector']}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique.append(s)

        return {
            "url": url,
            "price_selectors": [s for s in unique if s["kind"] == "price"][:8],
            "title_selectors": [s for s in unique if s["kind"] == "title"][:8],
            "recommended_price": next(
                (s["selector"] for s in unique if s["kind"] == "price"), None
            ),
            "recommended_title": next(
                (s["selector"] for s in unique if s["kind"] == "title"), None
            ),
        }
