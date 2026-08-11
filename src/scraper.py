"""Core scraping logic."""

from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass
from typing import Iterator
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; WebScraperBot/1.0; "
        "+https://github.com/web-scraper)"
    ),
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


class WebScraper:
    """Polite web scraper with built-in targets and generic page parsing."""

    def __init__(
        self,
        delay: float = 1.0,
        timeout: int = 15,
        headers: dict[str, str] | None = None,
    ):
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(headers or DEFAULT_HEADERS)

    def fetch(self, url: str) -> BeautifulSoup:
        if not url.startswith(("http://", "https://")):
            raise ScraperError(f"Invalid URL: {url}")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ScraperError(f"Failed to fetch {url}: {exc}") from exc

        return BeautifulSoup(response.text, "lxml")

    def scrape_quotes(
        self,
        base_url: str = "https://quotes.toscrape.com",
        max_pages: int | None = None,
    ) -> list[Quote]:
        """Scrape quotes from quotes.toscrape.com (demo site built for scraping)."""
        quotes: list[Quote] = []
        url: str | None = base_url
        page_count = 0

        while url:
            if max_pages is not None and page_count >= max_pages:
                break

            soup = self.fetch(url)
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

            next_link = soup.select_one("li.next a")
            url = urljoin(url, next_link["href"]) if next_link else None

            if url:
                time.sleep(self.delay)

        return quotes

    def scrape_page_meta(self, url: str) -> PageMeta:
        """Extract title, description, and headings from any public page."""
        soup = self.fetch(url)

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

        return PageMeta(
            title=title,
            url=url,
            description=description,
            headings=headings[:20],
        )

    def scrape_links(self, url: str, same_domain: bool = True) -> list[dict[str, str]]:
        """Extract anchor links from a page."""
        soup = self.fetch(url)
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

    @staticmethod
    def quotes_to_dicts(quotes: list[Quote]) -> list[dict]:
        return [asdict(q) for q in quotes]

    @staticmethod
    def meta_to_dict(meta: PageMeta) -> dict:
        return asdict(meta)
