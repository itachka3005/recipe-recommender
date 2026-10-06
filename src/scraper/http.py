import logging
import time
from urllib.parse import urlsplit

import httpx
from protego import Protego

logger = logging.getLogger(__name__)

RETRY_STATUSES = {429, 500, 502, 503, 504}


class DisallowedByRobots(Exception):
    """URL is forbidden by the site's robots.txt."""


class FetchError(Exception):
    """URL could not be fetched after all retries."""


class PoliteClient:
    def __init__(
        self,
        user_agent: str,
        delay: float = 1.5,
        timeout: float = 20.0,
        max_retries: int = 3,
    ) -> None:
        self.user_agent = user_agent
        self.delay = delay
        self.max_retries = max_retries
        self._client = httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=timeout,
            follow_redirects=True,
        )
        self._robots: dict[str, Protego | None] = {}
        self._last_request = 0.0

    def __enter__(self) -> "PoliteClient":
        return self

    def __exit__(self, *exc) -> None:
        self._client.close()

    def allowed(self, url: str) -> bool:
        robots = self._robots_for(url)
        if robots is None:
            return False
        return robots.can_fetch(url, self.user_agent)

    def get(self, url: str) -> httpx.Response:
        if not self.allowed(url):
            raise DisallowedByRobots(url)
        return self._send(url)

    def _robots_for(self, url: str) -> Protego | None:
        parts = urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._robots:
            response = self._send(f"{base}/robots.txt")
            if response.status_code == 200:
                robots = Protego.parse(response.text)
                crawl_delay = robots.crawl_delay(self.user_agent)
                if crawl_delay:
                    self.delay = max(self.delay, float(crawl_delay))
            elif response.status_code == 404:
                robots = Protego.parse("")
            else:
                logger.warning(
                    "robots.txt at %s returned %s, treating site as closed",
                    base,
                    response.status_code,
                )
                robots = None
            self._robots[base] = robots
        return self._robots[base]

    def _wait(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request = time.monotonic()

    def _send(self, url: str) -> httpx.Response:
        for attempt in range(1, self.max_retries + 1):
            self._wait()
            try:
                response = self._client.get(url)
            except httpx.TransportError as exc:
                logger.warning("Attempt %d for %s failed: %s", attempt, url, exc)
            else:
                if response.status_code not in RETRY_STATUSES:
                    return response
                logger.warning(
                    "Attempt %d for %s got %d", attempt, url, response.status_code
                )
            time.sleep(2**attempt)
        raise FetchError(url)