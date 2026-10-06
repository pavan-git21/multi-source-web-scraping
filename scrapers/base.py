from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ScrapeResult:
    source: str
    records: list = field(default_factory=list)
    pages_scraped: int = 0
    failed_pages: list = field(default_factory=list)
    failed_details: list = field(default_factory=list)
    parse_errors: int = 0
    fatal_error: str | None = None


def text_of(element) -> str | None:
    """Text of a BeautifulSoup element, or None when the element is missing."""
    return element.get_text(" ", strip=True) if element is not None else None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
