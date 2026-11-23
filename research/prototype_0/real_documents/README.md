# Real document research

This collection supports the next extraction experiments with original SEC filings and Federal Register notices. The synthetic prototype remains a separate regression baseline.

## Source documents

| Document | Format | Original source |
| --- | --- | --- |
| CrowdStrike Holdings, Inc. Form 8-K | HTML | [Document](https://www.sec.gov/Archives/edgar/data/1535527/000110465924081571/tm2419936d1_8k.htm) · [Source record](https://www.sec.gov/Archives/edgar/data/1535527/000110465924081571/0001104659-24-081571-index.html) |
| Delta Air Lines, Inc. Form 8-K | HTML | [Document](https://www.sec.gov/Archives/edgar/data/27904/000168316824005369/delta_8k.htm) · [Source record](https://www.sec.gov/Archives/edgar/data/27904/0001683168-24-005369-index.htm) |
| Delta Air Lines, Inc. 2024 Form 10-K | HTML | [Document](https://www.sec.gov/Archives/edgar/data/27904/000002790425000004/dal-20241231.htm) · [Source record](https://www.sec.gov/Archives/edgar/data/27904/000002790425000004/0000027904-25-000004-index.htm) |
| CrowdStrike Holdings, Inc. fiscal 2025 annual report to security holders | PDF | [Document](https://www.sec.gov/Archives/edgar/data/1535527/000110465925045058/tm254459d2_ars.pdf) · [Source record](https://www.sec.gov/Archives/edgar/data/1535527/000110465925045058/0001104659-25-045058-index.htm) |
| USTR Section 301 modification notice, 89 FR 76581 | PDF | [Document](https://www.govinfo.gov/content/pkg/FR-2024-09-18/pdf/2024-21217.pdf) · [Source record](https://www.govinfo.gov/app/details/FR-2024-09-18/2024-21217) |
| USTR Section 301 modification notice, 89 FR 101682 | PDF | [Document](https://www.govinfo.gov/content/pkg/FR-2024-12-16/pdf/2024-29462.pdf) · [Source record](https://www.govinfo.gov/app/details/FR-2024-12-16/2024-29462) |

The files are hosted by the original publishers or their official repositories. This repository contains the source catalog, not copies of the original documents. Download the files directly from the links or use the command below.

## Retrieve the files

Python 3.10 or later is sufficient. No model account or paid service is needed. From this directory:

```bash
python download_documents.py --user-agent "Your organization your-contact@example.com"
```

Replace the example identity with a genuine contact. To retrieve only PDF files, add `--format pdf`. To retrieve a specific document, add `--source dal_2024_8k`. The program saves original bytes and retrieval metadata in `local_documents/`, which is excluded from Git. It does not retry blocked requests or bypass source access controls. If an official source rejects a request, use its ordinary browser download option.

SEC access guidance: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data

The SEC FAQ describes public filing access and reuse: https://www.sec.gov/about/webmaster-frequently-asked-questions. Review rights and vendor terms before redistributing documents, sending them to external models, or using them for training. Local download does not establish unrestricted permission for every use.

## First experiments

Start with the CrowdStrike current report and the Delta current report. Extract each issuer, the reported event, the affected service, the named organizations, and the supporting passage. Determine whether the second report supports a reported connection to the first event. Do not treat the issuer's legal or financial assertions as independently verified facts.

Next, process the annual report PDF and compare the later disclosures against the earlier reports. Retain the exact PDF page number or HTML text offsets, original document reference, and extracted quotation. Record the parser version and the SHA-256 digest of the source file. For the trade notices, distinguish publication, effective dates, proposed actions and final determinations. Do not invent company exposure merely because a product category appears in a notice.

Use the acceptance timestamps in the catalog as source metadata, not proof of first public availability. Keep exact availability unknown unless supported by independent records. In historical evaluation, do not admit later filings into an earlier information set.

## Extraction interface

For each candidate statement, return a structured record containing the document identifier, entity names, claim type, event date when supported, exact source passage, locator, and uncertainty or abstention reason. Keep extraction separate from source verification. Model output is a candidate until validated against the source.

Compare the existing rules against one approved hosted language model on the same manually reviewed examples. Measure entity and event extraction quality, unsupported claims, evidence accuracy, latency and actual cost. Keep a held out evaluation set. Neither model calls nor paid services are part of this collection. Approval is required before incurring expenses or transmitting source text to a provider.

This is a small research collection, not an annotated benchmark or a production data feed.
