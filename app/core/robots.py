"""robots.txt compliance checker."""

from __future__ import annotations

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

logger = logging.getLogger(__name__)


class RobotsChecker:
    """Cache robots.txt parsers per origin."""

    def __init__(self, user_agent: str, timeout: int = 10):
        self.user_agent = user_agent
        self.timeout = timeout
        self._parsers: dict[str, RobotFileParser | None] = {}

    async def _load_parser(self, origin: str) -> RobotFileParser | None:
        if origin in self._parsers:
            return self._parsers[origin]

        robots_url = f"{origin}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(robots_url, follow_redirects=True)
                if response.status_code == 404:
                    self._parsers[origin] = None
                    return None
                response.raise_for_status()
                parser.parse(response.text.splitlines())
        except Exception as exc:
            logger.warning("Could not fetch robots.txt for %s: %s", origin, exc)
            self._parsers[origin] = None
            return None

        self._parsers[origin] = parser
        return parser

    async def is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        origin = f"{parsed.scheme}://{parsed.netloc}"
        parser = await self._load_parser(origin)
        if parser is None:
            return True

        return parser.can_fetch(self.user_agent, url)
