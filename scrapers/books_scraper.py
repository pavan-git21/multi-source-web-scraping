"""Books to Scrape: listing pages (title, price, rating, stock) + detail pages
(category, description). All selectors for this site live in this file."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from http_client import FetchError
from models import BOOKS_SOURCE
from scrapers.base import ScrapeResult, text_of, utc_now

log = logging.getLogger(__name__)

SOURCE = BOOKS_SOURCE
START_URL = "https://books.toscrape.com/"


def parse_listing(html: str, page_url: str):
    """Return (raw_records, next_page_url, parse_error_count) for one listing page."""
    soup = BeautifulSoup(html, "html.parser")
    records, errors = [], 0
    for pod in soup.select("article.product_pod"):
        try:
            link = pod.select_one("h3 a")
            href = link.get("href") if link else None
            rating_tag = pod.select_one("p.star-rating")
            rating = None
            if rating_tag is not None:
                words = [c for c in rating_tag.get("class", []) if c != "star-rating"]
                rating = words[0] if words else None
            records.append({
                "source": SOURCE,
                "source_url": urljoin(page_url, href) if href else None,
                "name_or_title": (link.get("title") or text_of(link)) if link else None,
                "price": text_of(pod.select_one("p.price_color")),
                "rating": rating,
                "availability": text_of(pod.select_one("p.availability")),
                "category": None,
                "description": None,
                "author": None,
                "tags": [],
                "scraped_at": utc_now(),
            })
        except Exception:  # one broken product must not kill the page
            errors += 1
            log.exception("Could not parse a product on %s", page_url)
    next_a = soup.select_one("li.next a")
    next_url = urljoin(page_url, next_a["href"]) if next_a and next_a.get("href") else None
    return records, next_url, errors


def parse_detail(html: str) -> dict:
    """Category (breadcrumb) and description from a product page; missing -> None."""
    soup = BeautifulSoup(html, "html.parser")
    crumbs = soup.select("ul.breadcrumb li a")
    category = text_of(crumbs[2]) if len(crumbs) >= 3 else None
    desc_header = soup.select_one("#product_description")
    description = text_of(desc_header.find_next_sibling("p")) if desc_header else None
    return {"category": category, "description": description}


def _enrich(client, record: dict, result: ScrapeResult) -> None:
    url = record.get("source_url")
    if not url:
        return
    try:
        record.update(parse_detail(client.get(url)))
    except FetchError as exc:
        result.failed_details.append(url)
        log.warning("Detail page failed, category/description left empty: %s", exc)
    except Exception:
        result.failed_details.append(url)
        log.exception("Unexpected error parsing detail page %s", url)


def scrape(client, config) -> ScrapeResult:
    result = ScrapeResult(source=SOURCE)
    url, seen = START_URL, set()
    while url and url not in seen:
        if config.max_pages and result.pages_scraped >= config.max_pages:
            log.info("[books] max_pages=%s reached", config.max_pages)
            break
        seen.add(url)
        try:
            html = client.get(url)
            records, next_url, errors = parse_listing(html, url)
        except FetchError as exc:
            log.error("[books] listing page failed, stopping pagination: %s", exc)
            result.failed_pages.append(url)
            break
        except Exception:
            log.exception("[books] unexpected error on %s, stopping pagination", url)
            result.failed_pages.append(url)
            break
        result.records.extend(records)
        result.parse_errors += errors
        result.pages_scraped += 1
        log.info("[books] page %d: %d books (%s)", result.pages_scraped, len(records), url)
        url = next_url

    if config.fetch_book_details and result.records:
        log.info("[books] fetching %d detail pages with %d workers",
                 len(result.records), config.workers)
        with ThreadPoolExecutor(max_workers=config.workers) as pool:
            list(pool.map(lambda r: _enrich(client, r, result), result.records))
    return result
