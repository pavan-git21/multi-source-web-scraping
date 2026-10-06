from processing.cleaning import (clean_record, clean_tags, clean_text, normalize_url,
                                 parse_price, parse_rating)


def test_clean_text():
    assert clean_text("  a \n\t b\u00a0c ") == "a b c"
    assert clean_text("N/A") is None and clean_text("   ") is None and clean_text(None) is None


def test_parse_price():
    assert parse_price("£51.77") == 51.77
    assert parse_price("$1,299.00") == 1299.0
    assert parse_price("free") is None and parse_price(None) is None


def test_parse_rating():
    assert parse_rating("Three") == 3 and parse_rating("4 out of 5") == 4
    assert parse_rating("lots") is None


def test_normalize_url():
    assert normalize_url("HTTPS://Books.ToScrape.com/a#frag") == "https://books.toscrape.com/a"
    assert normalize_url("/relative") is None and normalize_url("ftp://x.com") is None


def test_clean_tags():
    assert clean_tags([" Love ", "love", None, "Life"]) == ["love", "life"]


def test_clean_record_flags_bad_values_without_inventing():
    rec, issues = clean_record({"source": "Books to Scrape", "name_or_title": " X ",
                                "price": "abc", "rating": "Five", "source_url": "nope"})
    assert issues == ["invalid_url", "unparseable_price"]
    assert rec["price"] is None and rec["rating"] == 5 and rec["author"] is None
