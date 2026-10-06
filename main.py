"""CLI entry point:  python main.py [--max-pages N] [--dedupe-mode flag] ..."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from config import Config
from pipeline import run_pipeline


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    file_handler = logging.FileHandler(log_dir / "scrape.log", mode="w", encoding="utf-8")
    console = logging.StreamHandler()
    for handler in (file_handler, console):
        handler.setFormatter(fmt)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console)


def parse_args(argv=None) -> argparse.Namespace:
    d = Config()
    p = argparse.ArgumentParser(description="Multi-source web scraping & consolidation pipeline")
    p.add_argument("--sources", nargs="+", choices=["books", "quotes"], default=list(d.sources))
    p.add_argument("--max-pages", type=int, default=None, help="limit pages per source (testing)")
    p.add_argument("--delay", type=float, default=d.request_delay, help="seconds between requests")
    p.add_argument("--workers", type=int, default=d.workers, help="threads for book detail pages")
    p.add_argument("--retries", type=int, default=d.max_retries)
    p.add_argument("--timeout", type=float, default=d.timeout)
    p.add_argument("--no-book-details", action="store_true",
                   help="skip detail pages (faster, but category/description stay empty)")
    p.add_argument("--dedupe-mode", choices=["remove", "flag"], default=d.dedupe_mode)
    p.add_argument("--ignore-robots", action="store_true", help="not recommended")
    p.add_argument("--output-dir", type=Path, default=d.output_dir)
    p.add_argument("--log-dir", type=Path, default=d.log_dir)
    return p.parse_args(argv)


def main(argv=None) -> int:
    a = parse_args(argv)
    config = Config(
        sources=tuple(a.sources), max_pages=a.max_pages, request_delay=a.delay,
        workers=a.workers, max_retries=a.retries, timeout=a.timeout,
        fetch_book_details=not a.no_book_details, dedupe_mode=a.dedupe_mode,
        respect_robots=not a.ignore_robots, output_dir=a.output_dir, log_dir=a.log_dir,
    )
    setup_logging(config.log_dir)
    summary = run_pipeline(config)
    print(f"\nFinal records: {summary['totals']['final_record_count']} "
          f"(see {config.output_dir}/)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
