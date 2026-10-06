"""Quotes to Scrape: quote text, author, tags. All selectors for this site live here."""
from __future__ import annotations

import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from http_client import FetchError
from models import QUOTES_SOURCE
from scrapers.base import ScrapeResult, text_of, utc_now

log = logging.getLogger(__name__)

SOURCE = QUOTES_SOURCE
START_URL = "https://quotes.toscrape.com/"


def parse_listing(html: str, page_url: str):
    soup = BeautifulSoup(html, "html.parser")
    records, errors = [], 0
    for quote in soup.select("div.quote"):
        try:
            records.append({
                "source": SOURCE,
                # Quotes have no page of their own; the page they were found on is the origin.
                "source_url": page_url,
                "name_or_title": text_of(quote.select_one("span.text")),
                "author": text_of(quote.select_one("small.author")),
                "tags": [text_of(t) for t in quote.select("div.tags a.tag")],
                "price": None,
                "rating": None,
                "category": None,
                "description": None,
                "availability": None,
                "scraped_at": utc_now(),
            })
        except Exception:
            errors += 1
            log.exception("Could not parse a quote on %s", page_url)
    next_a = soup.select_one("li.next a")
    next_url = urljoin(page_url, next_a["href"]) if next_a and next_a.get("href") else None
    return records, next_url, errors


def scrape(client, config) -> ScrapeResult:
    result = ScrapeResult(source=SOURCE)
    url, seen = START_URL, set()
    while url and url not in seen:
        if config.max_pages and result.pages_scraped >= config.max_pages:
            log.info("[quotes] max_pages=%s reached", config.max_pages)
            break
        seen.add(url)
        try:
            html = client.get(url)
            records, next_url, errors = parse_listing(html, url)
        except FetchError as exc:
            log.error("[quotes] page failed, stopping pagination: %s", exc)
            result.failed_pages.append(url)
            break
        except Exception:
            log.exception("[quotes] unexpected error on %s, stopping pagination", url)
            result.failed_pages.append(url)
            break
        result.records.extend(records)
        result.parse_errors += errors
        result.pages_scraped += 1
        log.info("[quotes] page %d: %d quotes (%s)", result.pages_scraped, len(records), url)
        url = next_url
    return result
