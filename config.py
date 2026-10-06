"""Central, overridable settings (all can be changed from the CLI in main.py)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    sources: tuple = ("books", "quotes")
    max_pages: int | None = None      # None = follow pagination to the end
    timeout: float = 15.0             # seconds per request
    max_retries: int = 3              # retries after the first attempt
    backoff_factor: float = 1.0       # sleeps 1s, 2s, 4s ... between retries
    request_delay: float = 0.3        # minimum seconds between any two requests
    workers: int = 4                  # threads for book detail pages
    fetch_book_details: bool = True   # needed for category + description
    dedupe_mode: str = "remove"       # "remove" or "flag"
    respect_robots: bool = True
    output_dir: Path = Path("output")
    log_dir: Path = Path("logs")
    user_agent: str = "Mozilla/5.0 (compatible; AssignmentScraper/1.0; educational use)"
