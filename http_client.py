"""HTTP layer: rate limiting, robots.txt check, retries with exponential backoff."""
from __future__ import annotations

import logging
import threading
import time
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit

import requests

from config import Config

log = logging.getLogger(__name__)

RETRY_STATUS = {429, 500, 502, 503, 504}


class FetchError(Exception):
    """Raised when a URL could not be fetched after all retries."""


class _Retryable(Exception):
    pass


class HttpClient:
    def __init__(self, config: Config):
        self.cfg = config
        self.session = requests.Session()
        self.session.headers["User-Agent"] = config.user_agent
        self._lock = threading.Lock()
        self._last_request = 0.0
        self._robots: dict[str, RobotFileParser] = {}

    def _throttle(self) -> None:
        """Global rate limit, safe to call from several threads."""
        with self._lock:
            wait = self._last_request + self.cfg.request_delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()

    def _allowed(self, url: str) -> bool:
        if not self.cfg.respect_robots:
            return True
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            parser = RobotFileParser()
            try:
                resp = self.session.get(origin + "/robots.txt", timeout=self.cfg.timeout)
                parser.parse(resp.text.splitlines() if resp.status_code == 200 else [])
            except requests.RequestException:
                parser.parse([])  # robots.txt unreachable -> no restrictions known
            self._robots[origin] = parser
        return self._robots[origin].can_fetch(self.cfg.user_agent, url)

    def get(self, url: str) -> str:
        if not self._allowed(url):
            raise FetchError(f"{url}: disallowed by robots.txt")

        last_error = "unknown error"
        for attempt in range(1, self.cfg.max_retries + 2):
            self._throttle()
            try:
                resp = self.session.get(url, timeout=self.cfg.timeout)
                if resp.status_code in RETRY_STATUS:
                    raise _Retryable(f"HTTP {resp.status_code}")
                resp.raise_for_status()
                resp.encoding = "utf-8"  # sites omit charset; avoids 'Â£' mojibake
                return resp.text
            except (requests.ConnectionError, requests.Timeout, _Retryable) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt > self.cfg.max_retries:
                    break
                delay = self.cfg.backoff_factor * 2 ** (attempt - 1)
                log.warning("Attempt %d failed for %s (%s); retrying in %.1fs",
                            attempt, url, last_error, delay)
                time.sleep(delay)
            except requests.RequestException as exc:  # 4xx, invalid URL, ...
                raise FetchError(f"{url}: {exc}") from exc
        raise FetchError(f"{url}: gave up after {self.cfg.max_retries + 1} attempts ({last_error})")
