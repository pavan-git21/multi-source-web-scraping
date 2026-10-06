"""Reusable cleaning helpers. No scraping or HTTP code in here."""
from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

from models import FIELDS

NULL_TOKENS = {"", "n/a", "na", "none", "null", "nan", "-", "--", "unknown"}
RATING_WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}


def clean_text(value) -> str | None:
    """Unicode-normalise, collapse all whitespace, map null-like tokens to None."""
    if value is None or not isinstance(value, str):
        return None
    text = unicodedata.normalize("NFKC", value)
    text = re.sub(r"\s+", " ", text).strip()
    return None if text.lower() in NULL_TOKENS else text


def parse_price(value) -> float | None:
    """'£51.77' -> 51.77, '1,299.00' -> 1299.0. None if no number is found."""
    text = clean_text(value) if isinstance(value, str) else None
    if text is None:
        return None
    match = re.search(r"\d[\d,]*\.?\d*", text)
    if not match:
        return None
    try:
        return round(float(match.group().replace(",", "")), 2)
    except ValueError:
        return None


def parse_rating(value) -> float | None:
    """'Three' -> 3, '4' -> 4, '4 out of 5' -> 4. Range is checked in validation."""
    text = clean_text(value) if isinstance(value, str) else None
    if text is None:
        return None
    if text.lower() in RATING_WORDS:
        return RATING_WORDS[text.lower()]
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def normalize_url(value) -> str | None:
    """Absolute http(s) URL with lower-case scheme/host and no fragment, else None."""
    text = clean_text(value)
    if text is None:
        return None
    parts = urlsplit(text)
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        return None
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


def clean_tags(values) -> list[str]:
    """Trim, lower-case and de-duplicate tags while keeping their order."""
    seen, tags = set(), []
    for item in values or []:
        tag = clean_text(item)
        if tag and tag.lower() not in seen:
            seen.add(tag.lower())
            tags.append(tag.lower())
    return tags


def clean_record(raw: dict) -> tuple[dict, list[str]]:
    """Raw scraped dict -> (record in the common schema, list of issues found).

    Missing values become None; nothing is invented.
    """
    issues: list[str] = []
    rec = {field: None for field in FIELDS}

    for field in ("source", "name_or_title", "category", "author", "description",
                  "availability", "scraped_at"):
        rec[field] = clean_text(raw.get(field))

    rec["source_url"] = normalize_url(raw.get("source_url"))
    if clean_text(raw.get("source_url")) and rec["source_url"] is None:
        issues.append("invalid_url")

    if clean_text(raw.get("price")) is not None:
        rec["price"] = parse_price(raw["price"])
        if rec["price"] is None:
            issues.append("unparseable_price")

    if clean_text(raw.get("rating")) is not None:
        rec["rating"] = parse_rating(raw["rating"])
        if rec["rating"] is None:
            issues.append("unparseable_rating")

    rec["tags"] = clean_tags(raw.get("tags"))
    return rec, issues
