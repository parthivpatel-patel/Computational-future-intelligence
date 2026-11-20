# Computational Future Intelligence — Research Prototype 0

A **small, runnable, offline Python baseline** for the first Portfolio Blind Spot Intelligence workflow. This is a research starting point for the engineering team—not a production app, a trained model, or a customer-ready financial recommendation.

## What it demonstrates

1. Load a tiny portfolio and four **clearly synthetic** example documents.
2. Reconstruct which documents were available at a requested historical time.
3. Find a candidate operational disruption using an intentionally narrow keyword baseline.
4. Join it to a **source-quoted, manually curated** supplier relationship.
5. Output a possible indirect portfolio exposure with exact quote spans and provenance.
6. **Abstain** if the relationship quote is missing, source timing is invalid, or evidence is unavailable.

No third-party packages, API keys, or GPU are required. No external network calls occur.

## Run

From this folder with Python 3.10+:

```bash
python prototype.py
python prototype.py --as-of 2026-02-09T12:00:00Z
python -m unittest discover -s tests -v
```

The first command should produce **one synthetic possible-exposure finding** (Acme Components → Northstar Pumps). The earlier as-of query should produce **zero findings**. This is **not a real-world risk alert**.

## Data contract

- `data/documents.json`: document ID, original-looking synthetic text, `published_at`, **`available_at`**, source URI, and data kind.
- `data/relationships.json`: directed `supplies` relation with a quote that must match its source exactly.
- `data/portfolio.json`: fictional portfolio holdings.
- Output: source-backed findings, exact quote offsets, as-of cutoff, uncertainty disclaimer, and rejected unsupported claims.

## Next engineering tasks

1. Replace keyword-only extraction with a **precision-tested** NLP pipeline (entity recognition, event detection and relation extraction); keep rule baseline as comparator.
2. Add **real, rights-reviewed** SEC filings and other public sources as **separate datasets**, with ingestion metadata and publication/availability timestamps. Never claim Apple or another real company was affected by an unrelated event without a sourced path.
3. Add typed Pydantic schemas, SQLite/PostgreSQL persistence, immutable source hashes, claim versioning, evidence review, and event deduplication.
4. Add FastAPI endpoints only after the underlying extraction and evidence path are reproducible.
5. Add evaluation sets with precision, false-positive rate, abstention, historical time-split performance, and manually reviewed errors.
6. Extend the shared evidence schema for **prediction-market contract rules and settlement evidence**, keeping stock and event-contract products first-class.

## Known limitations

The example companies, relationships, and incidents are fictional. Keyword rules can miss valid events, misunderstand negation, and produce false positives; synthetic relation quotes are not independent verification. The current program does not discover arbitrary supplier links, infer causality, calculate probabilities, or offer real investing recommendations. Do **not** use outputs to trade. A genuine pilot requires real-source acquisition, licensed use checks, entity resolution, evaluation, and human review.

See [`docs/REAL_DOCUMENTS.md`](docs/REAL_DOCUMENTS.md) for verified public filing examples and source access guidance. Repository is public: **do not commit customer portfolios, API keys, non-public evidence, or confidential internal business plans.**
