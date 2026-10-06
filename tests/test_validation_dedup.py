from processing.deduplication import deduplicate, normalize_key
from processing.validation import validate_record

BOOK = {"source": "Books to Scrape", "name_or_title": "T", "source_url": "https://a.com/1",
        "price": 10.0, "rating": 3, "tags": [], "author": None}


def test_valid_record():
    assert validate_record(BOOK) == []


def test_validation_reasons():
    assert "unknown_source" in validate_record({**BOOK, "source": "Foo"})
    assert "missing_price" in validate_record({**BOOK, "price": None})
    assert "rating_out_of_range" in validate_record({**BOOK, "rating": 6})
    assert "invalid_price" in validate_record({**BOOK, "price": -1})
    assert "missing_source_url" in validate_record({**BOOK, "source_url": None})
    assert "invalid_url" in validate_record({**BOOK, "source_url": "bad"})
    assert validate_record(BOOK, ["unparseable_rating"]) == ["unparseable_rating"]


def test_normalize_key():
    variants = ["Example Book Title", " Example Book Title ", "EXAMPLE BOOK TITLE", "Example Book Title!"]
    assert len({normalize_key(v) for v in variants}) == 1
    assert normalize_key("Café") == normalize_key("cafe")


def _rec(title, author=None, source="Books to Scrape", url="u"):
    return {"source": source, "name_or_title": title, "author": author, "source_url": url}


def test_dedupe_remove_and_flag():
    data = [_rec("Example Book", url="1"), _rec("EXAMPLE  book", url="2"), _rec("Other", url="3")]
    final, dups = deduplicate([dict(r) for r in data], "remove")
    assert [r["source_url"] for r in final] == ["1", "3"] and dups[0]["duplicate_of"] == "1"
    final, dups = deduplicate([dict(r) for r in data], "flag")
    assert len(final) == 3 and [r["is_duplicate"] for r in final] == [False, True, False]


def test_same_title_different_author_or_source_is_not_duplicate():
    data = [_rec("Same", "A"), _rec("Same", "B"), _rec("Same", "A", source="Quotes to Scrape")]
    final, dups = deduplicate(data)
    assert len(final) == 3 and not dups
