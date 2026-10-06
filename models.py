"""Common output schema shared by every source."""

FIELDS = [
    "source",
    "source_url",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "availability",
    "scraped_at",
]

BOOKS_SOURCE = "Books to Scrape"
QUOTES_SOURCE = "Quotes to Scrape"
KNOWN_SOURCES = {BOOKS_SOURCE, QUOTES_SOURCE}
