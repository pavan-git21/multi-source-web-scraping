"""Orchestration: scrape -> clean -> validate -> deduplicate -> write outputs."""
from __future__ import annotations

import csv
import json
import logging
import time
from collections import Counter
from datetime import datetime, timezone

from config import Config
from http_client import HttpClient
from models import FIELDS
from processing.cleaning import clean_record
from processing.deduplication import deduplicate
from processing.validation import validate_record
from scrapers import books_scraper, quotes_scraper
from scrapers.base import ScrapeResult

log = logging.getLogger(__name__)

SCRAPERS = {"books": books_scraper, "quotes": quotes_scraper}


def _csv_row(rec: dict, columns: list[str]) -> dict:
    row = {c: rec.get(c) for c in columns}
    if isinstance(row.get("tags"), list):
        row["tags"] = "|".join(row["tags"])
    return row


def write_csv(path, records, columns) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:  # BOM: Excel-friendly
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(_csv_row(r, columns) for r in records)


def run_pipeline(config: Config, client=None) -> dict:
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    client = client or HttpClient(config)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Scrape (a failing source never stops the others)
    results: list[ScrapeResult] = []
    for key in config.sources:
        module = SCRAPERS[key]
        log.info("=== Scraping %s ===", module.SOURCE)
        try:
            results.append(module.scrape(client, config))
        except Exception as exc:
            log.exception("Source %s failed completely", module.SOURCE)
            results.append(ScrapeResult(source=module.SOURCE, fatal_error=repr(exc)))

    # 2. Clean + 3. Validate
    valid, rejected = [], []
    per_source = {}
    for res in results:
        stats = Counter()
        stats["collected"] = len(res.records)
        for raw in res.records:
            try:
                rec, issues = clean_record(raw)
            except Exception as exc:
                log.exception("Cleaning failed for %s", raw.get("source_url"))
                rejected.append({**raw, "rejection_reasons": f"cleaning_exception:{exc!r}"})
                continue
            stats["cleaned"] += 1
            errors = validate_record(rec, issues)
            if errors:
                stats["rejected"] += 1
                rejected.append({**rec, "rejection_reasons": ";".join(errors)})
            else:
                valid.append(rec)
        per_source[res.source] = {
            "pages_scraped": res.pages_scraped,
            "failed_pages": res.failed_pages,
            "failed_detail_pages": len(res.failed_details),
            "parse_errors": res.parse_errors,
            "fatal_error": res.fatal_error,
            "records_collected": stats["collected"],
            "records_after_cleaning": stats["cleaned"],
            "rejected_in_validation": stats["rejected"] + (stats["collected"] - stats["cleaned"]),
        }

    # 4. Deduplicate
    final, duplicates = deduplicate(valid, mode=config.dedupe_mode)
    dup_by_source = Counter(d["source"] for d in duplicates)
    final_by_source = Counter(r["source"] for r in final if not r.get("is_duplicate"))
    for source, info in per_source.items():
        info["duplicates_detected"] = dup_by_source[source]
        info["final_records"] = (final_by_source[source] if config.dedupe_mode == "remove"
                                 else final_by_source[source] + dup_by_source[source])

    # 5. Write outputs
    columns = FIELDS + (["is_duplicate", "duplicate_of"] if config.dedupe_mode == "flag" else [])
    write_csv(config.output_dir / "final_dataset.csv", final, columns)
    write_csv(config.output_dir / "rejected_records.csv", rejected,
              FIELDS + ["rejection_reasons"])
    write_csv(config.output_dir / "duplicates.csv", duplicates,
              FIELDS + ["is_duplicate", "duplicate_of"])

    reasons = Counter(r for row in rejected for r in row["rejection_reasons"].split(";"))
    missing = {
        source: {f: sum(1 for r in final if r["source"] == source and r.get(f) in (None, "", []))
                 for f in FIELDS}
        for source in per_source
    }
    summary = {
        "started_at_utc": started_at,
        "execution_time_seconds": round(time.perf_counter() - started, 2),
        "dedupe_mode": config.dedupe_mode,
        "totals": {
            "records_collected": sum(i["records_collected"] for i in per_source.values()),
            "records_after_cleaning": sum(i["records_after_cleaning"] for i in per_source.values()),
            "rejected_in_validation": len(rejected),
            "duplicates_detected": len(duplicates),
            "duplicates_removed": len(duplicates) if config.dedupe_mode == "remove" else 0,
            "duplicates_flagged": len(duplicates) if config.dedupe_mode == "flag" else 0,
            "final_record_count": len(final),
        },
        "rejection_reasons": dict(reasons),
        "by_source": per_source,
        "missing_values_in_final_dataset": missing,
    }
    with open(config.output_dir / "summary_report.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    log.info("Done in %.1fs: %s", summary["execution_time_seconds"], summary["totals"])
    return summary
