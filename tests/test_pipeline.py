import csv
import json

import pytest

from config import Config
from http_client import FetchError, HttpClient
from pipeline import run_pipeline
from tests.fixtures import FakeClient, site_pages


def _run(tmp_path, **kw):
    cfg = Config(output_dir=tmp_path, request_delay=0, **kw)
    return cfg, run_pipeline(cfg, FakeClient(site_pages()))


def test_end_to_end_remove_mode(tmp_path):
    _, s = _run(tmp_path)
    t = s["totals"]
    assert t["records_collected"] == 8                  # 4 books + 4 quotes
    assert t["rejected_in_validation"] == 2             # broken price book, quote without text
    assert t["duplicates_detected"] == 2                # book title variant + einstein quote variant
    assert t["final_record_count"] == 4
    rows = list(csv.DictReader(open(tmp_path / "final_dataset.csv", encoding="utf-8-sig")))
    assert len(rows) == 4 and {r["source"] for r in rows} == {"Books to Scrape", "Quotes to Scrape"}
    assert all(r["source_url"].startswith("http") for r in rows)
    assert json.load(open(tmp_path / "summary_report.json"))["totals"] == t
    assert "unparseable_price" in s["rejection_reasons"]


def test_end_to_end_flag_mode(tmp_path):
    _, s = _run(tmp_path, dedupe_mode="flag")
    rows = list(csv.DictReader(open(tmp_path / "final_dataset.csv", encoding="utf-8-sig")))
    assert len(rows) == 6 and sum(r["is_duplicate"] == "True" for r in rows) == 2
    assert s["totals"]["duplicates_flagged"] == 2


def test_one_source_failing_completely_does_not_stop_the_other(tmp_path):
    pages = {k: v for k, v in site_pages().items() if "quotes" in k}
    cfg = Config(output_dir=tmp_path, request_delay=0)
    s = run_pipeline(cfg, FakeClient(pages))
    assert s["by_source"]["Books to Scrape"]["failed_pages"]
    assert s["totals"]["final_record_count"] == 2   # both quotes kept


# ---- HttpClient retry behaviour (no network: session is stubbed) ----
class _Resp:
    def __init__(self, status, text="ok"):
        self.status_code, self.text, self.encoding = status, text, None

    def raise_for_status(self):
        import requests
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def _client(responses, retries=2):
    cfg = Config(request_delay=0, backoff_factor=0, max_retries=retries, respect_robots=False)
    c = HttpClient(cfg)
    seq = iter(responses)

    def fake_get(url, timeout=None):
        item = next(seq)
        if isinstance(item, Exception):
            raise item
        return item
    c.session.get = fake_get
    return c


def test_retry_then_success():
    import requests
    c = _client([requests.ConnectionError("boom"), _Resp(503), _Resp(200, "page")])
    assert c.get("https://x.com/") == "page"


def test_gives_up_after_retries():
    import requests
    c = _client([requests.Timeout("t")] * 3)
    with pytest.raises(FetchError):
        c.get("https://x.com/")


def test_404_is_not_retried():
    c = _client([_Resp(404)])
    with pytest.raises(FetchError):
        c.get("https://x.com/")
