# Portfolio Blind Spot Intelligence: research baseline

This directory contains the first executable research component of Computational Future Intelligence. It demonstrates an evidence-backed portfolio exposure workflow with fictional companies, synthetic documents and deterministic extraction rules. The code is deliberately small enough to inspect end to end.

It is not a trained machine learning model, a real-world risk monitor or a production service.

## Run locally or in Google Colab

Python 3.10 or newer is sufficient. The baseline requires no third-party libraries, paid APIs, cloud credentials or GPU.

From `research/prototype_0`:

```bash
python prototype.py
python prototype.py --as-of 2026-02-09T12:00:00Z
python -m unittest discover -s tests -v
python evaluate_baseline.py
```

The standard query produces one possible exposure from the fictional supplier Acme Components to the fictional portfolio company Northstar Pumps. The historical replay produces no finding because the incident document was not yet available. The third command runs automated tests. The final command checks the extraction rules against a small synthetic collection of labeled sentences.

## Data and output

`data/documents.json` contains versioned document metadata, source text and separate publication and availability times. `data/relationships.json` contains manually curated supplier relationships with exact source quotes. `data/portfolio.json` contains fictional holdings. `data/sentence_cases.json` contains synthetic regression examples. None of these inputs contains verified investment research.

For each finding the output records the source document, exact quote boundaries, publication and availability times, a SHA-256 fingerprint of the text, and the proposed relationship path. A fingerprint identifies the text processed during a run; it is not an independent guarantee that the publisher is authentic.

Relationship quotations must explicitly support the declared direction of supply. An unsupported, conditional or negated relationship does not produce a finding. Candidate events use conservative disruption verbs, explicit company attribution patterns, and historical availability checks. A company merely commenting on another company's disruption is not enough to create an exposure finding. Duplicate candidate paths are suppressed. The engine does not calculate financial impact or infer causality.

## Engineering priorities

1. Establish a licensed, reproducible ingestion process for actual SEC filings, including source identity, availability time, revisions and original document hashes.
2. Build an independently labeled set of event and relationship examples. Measure false alerts, missed events and evidence errors against a simple baseline before introducing NLP models.
3. Add typed data contracts, database persistence, verified entity identities and reviewable claim states.
4. Expose the engine through FastAPI after the extraction and evidence contracts stabilize.
5. Extend the shared evidence and time model to prediction-market contract definitions and resolution sources.

The research baseline currently rejects non-synthetic document inputs by design. A real-source ingestion adapter should perform separate rights checks and provenance validation rather than weakening that boundary.

See [Engineering notes](docs/ENGINEERING_NOTES.md) and [Candidate public source documents](docs/REAL_DOCUMENTS.md).

This is a public repository. Do not commit customer portfolios, account credentials, unpublished business plans or confidential datasets.

## Real document experiments

The [real document collection](real_documents/README.md) contains original source links, acquisition instructions, historical metadata and a separate local download utility. Keep these experiments separate from the synthetic regression fixtures.
