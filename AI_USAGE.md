# AI_USAGE

> **Candidate: review and complete the [FILL IN] parts before submitting.** Everything below
> marked [FILL IN] must reflect what you actually did and found.

## Tools used

| Tool | Used for |
|---|---|
| Claude (Anthropic) | Generating the initial project structure and code (scrapers, cleaning, validation, deduplication, pipeline, CLI), unit/integration tests, README drafting |
| [FILL IN: any other tool] | [FILL IN] |

## Representative prompts

1. Provided the assignment PDF and asked for the complete project as a ZIP file.
2. [FILL IN: your follow-up prompts, e.g. "why does the price show 'Â£'?", "add flag mode for duplicates"]

## AI-assisted parts

Essentially all of the code was AI-generated in the first draft: `scrapers/`, `processing/`,
`http_client.py`, `pipeline.py`, `main.py`, `tests/`, and the README. [FILL IN: which parts you
then rewrote or changed yourself.]

## Changes made after reviewing AI output

- [FILL IN: e.g. selector changes after inspecting the live HTML, retry settings, schema changes]

## Incorrect or incomplete AI suggestions found

- [FILL IN: be honest; list real problems you hit when running against the live sites.]
- Known at hand-over: the AI could not reach the two websites while building (network was
  blocked), so selectors were written from knowledge of the sites' structure and verified only
  against HTML fixtures that imitate it. They must be verified against the live sites.

## Verification

- `python -m pytest -q`: 23 tests pass (cleaning, validation, deduplication, parsers,
  pagination, failure handling, end-to-end in both dedupe modes, retry logic).
- The real `HttpClient` and CLI were smoke-tested against a local HTTP server serving fixture pages.
- [FILL IN: full live run `python main.py`: record counts, comparison of the number of pages and
  records with what the websites show, manual spot-check of N sample records.]
