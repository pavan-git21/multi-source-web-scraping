"""Tiny HTML pages that mimic the structure of the two practice sites."""

def book_pod(title, href, price, rating, stock="In stock"):
    return f"""<article class="product_pod"><div class="image_container"></div>
    <p class="star-rating {rating}"></p>
    <h3><a href="{href}" title="{title}">{title[:20]}...</a></h3>
    <div class="product_price"><p class="price_color">{price}</p>
    <p class="instock availability"> {stock} </p></div></article>"""

BOOKS_PAGE_1 = ("<html><body><ol>" +
    book_pod("Example Book Title", "catalogue/example-book_1/index.html", "£51.77", "Three") +
    book_pod("Another Book", "catalogue/another-book_2/index.html", "£12.00", "Five") +
    "</ol><ul class='pager'><li class='next'><a href='catalogue/page-2.html'>next</a></li></ul></body></html>")

BOOKS_PAGE_2 = ("<html><body><ol>" +
    book_pod("  EXAMPLE   BOOK TITLE ", "../example-book-copy_3/index.html", "£51.77", "Three") +
    book_pod("Broken Price Book", "../broken_4/index.html", "N/A?", "Two") +
    "</ol></body></html>")

def book_detail(category, desc):
    d = f'<div id="product_description" class="sub-header"><h2>Product Description</h2></div><p>{desc}</p>' if desc else ""
    return f"""<html><body><ul class="breadcrumb"><li><a href="/">Home</a></li>
    <li><a href="/c">Books</a></li><li><a href="/c/x">{category}</a></li><li class="active">T</li></ul>{d}</body></html>"""

QUOTES_PAGE_1 = """<html><body>
<div class="quote"><span class="text">“The world as we have created it.”</span>
 <span>by <small class="author">Albert Einstein</small><a href="/author/Albert-Einstein">(about)</a></span>
 <div class="tags"><a class="tag">change</a><a class="tag">Deep-thoughts</a><a class="tag">change</a></div></div>
<div class="quote"><span class="text">“A quote without tags.”</span>
 <small class="author">Jane Austen</small><div class="tags"></div></div>
<ul class="pager"><li class="next"><a href="/page/2/">Next</a></li></ul></body></html>"""

QUOTES_PAGE_2 = """<html><body>
<div class="quote"><span class="text">“The   world as we have created it!”</span>
 <small class="author">albert einstein</small><div class="tags"><a class="tag">x</a></div></div>
<div class="quote"><small class="author">No Text Author</small></div>
</body></html>"""

class FakeClient:
    """Stands in for HttpClient: serves pages from a dict, raises FetchError otherwise."""
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def get(self, url):
        from http_client import FetchError
        self.calls.append(url)
        if url not in self.pages:
            raise FetchError(f"{url}: HTTP 404")
        return self.pages[url]

def site_pages():
    return {
        "https://books.toscrape.com/": BOOKS_PAGE_1,
        "https://books.toscrape.com/catalogue/page-2.html": BOOKS_PAGE_2,
        "https://books.toscrape.com/catalogue/example-book_1/index.html": book_detail("Poetry", "A  great\n book."),
        "https://books.toscrape.com/catalogue/another-book_2/index.html": book_detail("Travel", None),
        # example-book-copy_3 detail page intentionally missing -> simulates a failed request
        "https://books.toscrape.com/broken_4/index.html": book_detail("Fiction", "x"),
        "https://quotes.toscrape.com/": QUOTES_PAGE_1,
        "https://quotes.toscrape.com/page/2/": QUOTES_PAGE_2,
    }
