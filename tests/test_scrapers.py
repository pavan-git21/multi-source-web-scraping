from config import Config
from scrapers import books_scraper, quotes_scraper
from tests.fixtures import BOOKS_PAGE_1, QUOTES_PAGE_1, FakeClient, site_pages


def test_books_parse_listing():
    recs, nxt, errors = books_scraper.parse_listing(BOOKS_PAGE_1, "https://books.toscrape.com/")
    assert len(recs) == 2 and errors == 0
    assert recs[0]["name_or_title"] == "Example Book Title" and recs[0]["rating"] == "Three"
    assert recs[0]["source_url"] == "https://books.toscrape.com/catalogue/example-book_1/index.html"
    assert nxt == "https://books.toscrape.com/catalogue/page-2.html"


def test_books_missing_elements_do_not_crash():
    html = '<article class="product_pod"><h3><a href="x.html" title="T"></a></h3></article>'
    recs, nxt, errors = books_scraper.parse_listing(html, "https://books.toscrape.com/")
    assert recs[0]["price"] is None and recs[0]["rating"] is None and nxt is None


def test_quotes_parse_listing():
    recs, nxt, _ = quotes_scraper.parse_listing(QUOTES_PAGE_1, "https://quotes.toscrape.com/")
    assert recs[0]["author"] == "Albert Einstein" and recs[0]["tags"][0] == "change"
    assert recs[1]["tags"] == [] and nxt == "https://quotes.toscrape.com/page/2/"


def test_pagination_follows_next_links_and_survives_failed_detail():
    client = FakeClient(site_pages())
    res = books_scraper.scrape(client, Config())
    assert res.pages_scraped == 2 and len(res.records) == 4
    assert len(res.failed_details) == 1            # the intentionally missing detail page
    assert res.records[0]["category"] == "Poetry"


def test_failed_page_stops_that_source_only():
    pages = site_pages()
    del pages["https://quotes.toscrape.com/page/2/"]
    res = quotes_scraper.scrape(FakeClient(pages), Config())
    assert res.pages_scraped == 1 and res.failed_pages == ["https://quotes.toscrape.com/page/2/"]
    assert len(res.records) == 2


def test_max_pages():
    res = quotes_scraper.scrape(FakeClient(site_pages()), Config(max_pages=1))
    assert res.pages_scraped == 1
