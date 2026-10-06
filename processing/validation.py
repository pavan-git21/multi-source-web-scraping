"""Record-level validation. Returns reasons; the caller decides what to do with them."""
from __future__ import annotations

import math

from models import BOOKS_SOURCE, KNOWN_SOURCES, QUOTES_SOURCE
from processing.cleaning import normalize_url

REQUIRED_FIELDS = {
    BOOKS_SOURCE: ("name_or_title", "source_url", "price"),
    QUOTES_SOURCE: ("name_or_title", "source_url", "author"),
}


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isnan(value)


def validate_record(rec: dict, cleaning_issues=()) -> list[str]:
    """Empty list = valid. Each reason is a short machine-readable code."""
    errors = list(cleaning_issues)

    source = rec.get("source")
    if source not in KNOWN_SOURCES:
        return errors + ["unknown_source"]

    for field in REQUIRED_FIELDS[source]:
        if rec.get(field) in (None, ""):
            errors.append(f"missing_{field}")

    if rec.get("source_url") and normalize_url(rec["source_url"]) is None:
        errors.append("invalid_url")

    price = rec.get("price")
    if price is not None and (not _is_number(price) or price < 0):
        errors.append("invalid_price")

    rating = rec.get("rating")
    if rating is not None and (not _is_number(rating) or not 1 <= rating <= 5):
        errors.append("rating_out_of_range")

    if not isinstance(rec.get("tags"), list):
        errors.append("invalid_tags")
    return errors
