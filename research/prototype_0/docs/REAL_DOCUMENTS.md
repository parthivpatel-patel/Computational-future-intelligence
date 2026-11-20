# Real example documents for the next iteration

The runnable dataset under `data/` is **fully fictional** and is not extracted from these filings. Use the resources below as candidate source documents, but document data-use restrictions and proper provenance before embedding any full filings in a dataset.

## Real primary-source example

**Apple Inc., 2025 Form 10-K** (SEC EDGAR), useful for testing risk-factor text extraction and supply-chain language.

- SEC filing: https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm
- SEC company submissions API documentation: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC developer resources and access policy: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data

The filing discusses supply concentration and risks from international trade and supply-chain disruptions. **That general risk disclosure is not evidence that any specific supplier incident actually occurred, nor evidence of an exposure path to an invented event.** Extract each asserted relationship only if the relevant sentence actually supports it.

## Suggested experiment

1. Select the risk factors/supply-chain paragraph from the SEC filing and record filing date, first-available timestamp, original URL and content hash.
2. Extract candidate companies, locations, risks and relation phrases with a transparent rule baseline.
3. Human-label a small set of sentences as `supported`, `unsupported`, or `uncertain` with exact text offsets.
4. Compare candidate NLP improvements against the rule baseline and keep a log of false positives.
5. Create a *separate*, time-valid event source if attempting to trace exposure. Do not fabricate supplier relationships or historical visibility.

SEC EDGAR automated access is governed by its fair-access guidance and requires an identifying User-Agent. Free access is not a blanket clearance for every downstream use case; review any redistribution/model-training rights and user privacy expectations.
