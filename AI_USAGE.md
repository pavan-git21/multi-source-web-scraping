# AI_USAGE

## Tools used

| Tool    | Used for                                                                     |
| ------- | ---------------------------------------------------------------------------- |
| ChatGPT | Project planning, code implementation, debugging, testing, and documentation |

## Representative prompts

* Design a Python web scraping pipeline for Books to Scrape and Quotes to Scrape.
* Implement pagination and separate the scraper logic for both websites.
* Create common cleaning, validation, and deduplication functions.
* Add retry and error handling for failed requests and pages.
* Review the code and suggest edge cases and improvements.
* Create pytest tests for the scraping and processing pipeline.

## AI-assisted parts

ChatGPT was used during the development of most parts of the project, including the scrapers, processing modules, HTTP client, pipeline, tests, and README.

I provided the requirements and project structure, reviewed the generated code, and made changes based on testing and the assignment requirements.

## Changes made after reviewing AI output

* Adjusted the scraping and parsing logic.
* Updated cleaning and validation rules.
* Improved duplicate detection and normalization.
* Added retry and failure handling.
* Added and updated tests for different edge cases.
* Updated the README based on the final implementation.

## Incorrect or incomplete AI suggestions found

The AI could not access the live websites while developing the initial implementation because network access was unavailable. The selectors were therefore initially based on the known website structure and tested using HTML fixtures.

The live selectors should be verified against the websites before running the scraper in production.

## Verification

* `python -m pytest -q` — **23 tests passed**
* Tested cleaning, validation, deduplication, parsing, pagination, retry logic, and failure handling.
* Smoke-tested the complete pipeline using a local HTTP server with fixture pages.
