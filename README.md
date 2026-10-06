# Multi-Source Web Scraping & Data Consolidation

A Python web scraping project that collects data from **Books to Scrape** and **Quotes to Scrape**, cleans and validates the data, removes duplicates, and generates consolidated CSV and JSON reports.

## Workflow

```text
Books / Quotes
      ↓
   Scraping
      ↓
   Cleaning
      ↓
  Validation
      ↓
 Deduplication
      ↓
CSV + JSON Reports
```

## Tech Stack

* Python
* Requests
* BeautifulSoup4
* Pytest

## Setup

```bash
python -m venv .venv
```

Activate the environment:

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

Run the complete scraper:

```bash
python main.py
```

Quick test run:

```bash
python main.py --max-pages 2
```

Run tests:

```bash
python -m pytest -q
```

View available options:

```bash
python main.py --help
```

## Output

Files are generated inside the `output/` directory.

| File                   | Description                        |
| ---------------------- | ---------------------------------- |
| `final_dataset.csv`    | Cleaned and consolidated dataset   |
| `summary_report.json`  | Scraping and validation statistics |
| `rejected_records.csv` | Records that failed validation     |
| `duplicates.csv`       | Records identified as duplicates   |

Logs are stored in:

```text
logs/scrape.log
```

## Project Structure

```text
main.py                 CLI and application entry point
pipeline.py             Scraping pipeline and output handling
config.py               Configuration and CLI settings
http_client.py          HTTP requests, retries, rate limiting
models.py               Common data model
scrapers/
    books_scraper.py
    quotes_scraper.py
processing/
    cleaning.py
    validation.py
    deduplication.py
tests/                  Unit and end-to-end tests
```

## Data Processing

### Scraping

* Handles pagination automatically using the site's `next` links.
* Uses `urljoin` to resolve relative URLs.
* Respects `robots.txt`.
* Includes request timeouts, retries and rate limiting.

### Cleaning

The pipeline:

* Normalises Unicode and whitespace.
* Converts prices to numeric values.
* Converts star ratings to numbers.
* Normalises URLs.
* Cleans and removes duplicate tags.
* Converts empty or null-like values to `null`.

### Validation

Invalid records are rejected when:

* Required fields are missing.
* URLs are invalid.
* Prices are invalid or negative.
* Ratings are outside the 1–5 range.
* Data cleaning issues are detected.

Rejected records and their reasons are saved in `rejected_records.csv`.

### Deduplication

Records are matched using normalised:

```text
source + title/quote + author
```

Normalisation handles differences in:

* Case
* Whitespace
* Punctuation
* Accents

By default, duplicate records are removed and stored in `duplicates.csv`.

## Error Handling

The scraper includes:

* Request timeouts
* Retries for connection errors, timeouts, `429` and `5xx` responses
* Exponential backoff
* Rate limiting
* `robots.txt` support
* Logging of failed pages and individual records

If a book detail page fails, the book is still retained with missing detail fields.

## Assumptions

* Only Books to Scrape and Quotes to Scrape are used.
* Book prices remain in GBP.
* Missing values are kept as `null` rather than being invented.
* Duplicate detection uses normalised exact matching.

## Limitations

* The scraper starts from the beginning on every run.
* No checkpoint/resume functionality.
* Fuzzy matching is not implemented.
* Author detail pages are not scraped.
* A failed listing page stops pagination for that source.

## Future Improvements

* Add checkpoint and resume support.
* Store data in a database instead of CSV.
* Add scheduled scraping.
* Add monitoring and failure alerts.
* Add fuzzy duplicate matching.
