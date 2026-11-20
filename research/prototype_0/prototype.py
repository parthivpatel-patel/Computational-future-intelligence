"""Offline evidence-first research prototype for indirect equity exposure.

This is a deterministic baseline, not an ML model or an investment signal.
All bundled company names, documents and events are synthetic.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).with_name("data")
TRIGGERS = re.compile(r"\b(?:disrupted|halted|suspended|closed|shut down)\b", re.IGNORECASE)
NEGATED = re.compile(r"\b(?:no|not|never)\s+(?:\w+\s+){0,4}(?:disrupted|halted|suspended|closed)\b", re.IGNORECASE)


def when(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("All timestamps must include a UTC offset")
    return result.astimezone(timezone.utc)


def read_data(folder: Path = DATA_DIR) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    return tuple(json.loads((folder / file).read_text(encoding="utf-8")) for file in
                 ("documents.json", "relationships.json", "portfolio.json"))


def visible_documents(documents: list[dict[str, Any]], as_of: datetime) -> dict[str, dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for doc in documents:
        if doc["id"] in seen:
            raise ValueError(f"duplicate document id: {doc['id']}")
        if when(doc["published_at"]) > when(doc["available_at"]):
            raise ValueError(f"document {doc['id']} available before publication")
        # Every event and relation must be supported by evidence actually available at as_of.
        if when(doc["available_at"]) <= as_of:
            seen[doc["id"]] = doc
    return seen


def citation(doc: dict[str, Any], quote: str) -> dict[str, Any] | None:
    # Reject relationship statements that cannot be found verbatim in their declared source.
    start = doc["body"].find(quote)
    if start < 0:
        return None
    return {
        "document_id": doc["id"], "title": doc["title"], "url": doc["url"],
        "available_at": doc["available_at"], "quote": quote,
        "start": start, "end": start + len(quote),
        "data_kind": doc["data_kind"],
    }


def event_sentences(document: dict[str, Any], subject: str) -> list[str]:
    # Very small, transparent baseline: keyword + explicit entity name in the same sentence.
    # No semantic inference, no implicit supplier matching, no event deduplication yet.
    sentences = re.split(r"(?<=[.!?])\s+", document["body"].strip())
    return [sentence for sentence in sentences if subject.casefold() in sentence.casefold()
            and TRIGGERS.search(sentence) and not NEGATED.search(sentence)]


def analyze(
    documents: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    portfolio: list[dict[str, Any]],
    as_of: str,
) -> dict[str, Any]:
    cutoff = when(as_of)
    source_by_id = visible_documents(documents, cutoff)
    holdings = {position["company_id"]: position for position in portfolio}
    findings: list[dict[str, Any]] = []
    rejected = 0

    for relation in relationships:
        if relation["relation_type"] != "supplies" or relation["buyer_id"] not in holdings:
            continue
        evidence_doc = source_by_id.get(relation["source_document_id"])
        if evidence_doc is None:
            continue
        relation_cite = citation(evidence_doc, relation["source_quote"])
        if relation_cite is None:
            rejected += 1
            continue
        supplier_name = relation["supplier_name"]
        for doc in source_by_id.values():
            # Do not reuse the supplier declaration itself as evidence of a new event.
            if doc["id"] == evidence_doc["id"]:
                continue
            for sentence in event_sentences(doc, supplier_name):
                event_cite = citation(doc, sentence)
                if event_cite is None:
                    rejected += 1
                    continue
                position = holdings[relation["buyer_id"]]
                findings.append({
                    "finding_type": "potential_indirect_exposure",
                    "portfolio_ticker": position["ticker"],
                    "portfolio_company": position["company_name"],
                    "exposure_path": [supplier_name, "supplies", position["company_name"]],
                    "event": sentence,
                    "evidence": {"event": event_cite, "relationship": relation_cite},
                    "assessment": "Possible indirect exposure; financial impact is unverified.",
                    "next_check": "Confirm whether this disruption affects deliveries to the held company.",
                })

    return {
        "as_of": cutoff.isoformat(), "mode": "offline_synthetic_research_baseline",
        "visible_document_count": len(source_by_id), "findings": findings,
        "rejected_unverifiable_relationships_or_events": rejected,
        "warning": "Synthetic data only. No forecasts, trading recommendations or causal claims.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline, evidence-first portfolio blind-spot prototype")
    parser.add_argument("--as-of", default="2026-02-12T12:00:00Z", help="ISO-8601 timestamp; with UTC offset")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    docs, relations, holdings = read_data(args.data_dir)
    print(json.dumps(analyze(docs, relations, holdings, args.as_of), indent=2))


if __name__ == "__main__":
    main()
