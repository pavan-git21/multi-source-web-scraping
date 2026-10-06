"""Duplicate detection on normalised content, not on raw strings."""
from __future__ import annotations

import re
import unicodedata


def normalize_key(value) -> str:
    """'  Example  Book Title ', 'EXAMPLE BOOK TITLE', 'Example Book Title!' -> same key.

    Steps: NFKD + strip accents -> casefold -> punctuation to space -> collapse spaces.
    """
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^\w]+", " ", text.casefold())
    return re.sub(r"\s+", " ", text).strip()


def duplicate_key(rec: dict) -> tuple:
    """Same source + same normalised title/quote + same normalised author."""
    return (rec.get("source"), normalize_key(rec.get("name_or_title")),
            normalize_key(rec.get("author")))


def deduplicate(records: list[dict], mode: str = "remove"):
    """Return (final_records, duplicate_records).

    The first occurrence is the original. mode="remove": later ones are dropped and
    returned in `duplicate_records`. mode="flag": every record is kept and later ones get
    is_duplicate=True / duplicate_of=<url of the original>.
    """
    if mode not in ("remove", "flag"):
        raise ValueError("mode must be 'remove' or 'flag'")
    first_seen: dict[tuple, dict] = {}
    final, duplicates = [], []
    for rec in records:
        key = duplicate_key(rec)
        if not key[1]:                      # no usable title: cannot compare, keep it
            final.append(rec)
            continue
        original = first_seen.get(key)
        if original is None:
            first_seen[key] = rec
            if mode == "flag":
                rec["is_duplicate"], rec["duplicate_of"] = False, None
            final.append(rec)
            continue
        dup = dict(rec, is_duplicate=True, duplicate_of=original.get("source_url"))
        duplicates.append(dup)
        if mode == "flag":
            final.append(dup)
    return final, duplicates
