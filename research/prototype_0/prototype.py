"""Offline, evidence-backed baseline for potential indirect portfolio exposure.

This module accepts synthetic research fixtures only. It deliberately does not
estimate financial impact, discover unseen supplier links, or make predictions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILES = ("documents.json", "relationships.json", "portfolio.json")

EVENT_VERBS = re.compile(r"\b(?:disrupted|halted|suspended|closed|shut\s+down)\b", re.IGNORECASE)
# A keyword match is not evidence that an incident took place. These deliberately
# conservative filters sacrifice recall to avoid obvious false assertions.
NON_ASSERTIVE = re.compile(
    r"\b(?:no|not|never|without|denied|false|unconfirmed|unverified|"
    r"hypothetical|hypothetically|scenario|rumou?r|alleged|"
    r"if|would|could|might|may|possibly|potentially|planned|planning|"
    r"forecast|forecasted|forecasting)\b",
    re.IGNORECASE,
)
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def when(value: str) -> datetime:
    """Parse an offset-aware ISO timestamp and return the corresponding UTC time."""
    if not isinstance(value, str):
        raise ValueError("Timestamp must be an ISO-8601 string with an explicit offset")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid ISO-8601 timestamp: {value!r}") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("All timestamps must include a UTC offset")
    return timestamp.astimezone(timezone.utc)


def _required_string(record: dict[str, Any], field: str, context: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}: {field} must be a nonempty string")
    return value


def _entity_pattern(name: str) -> re.Pattern[str]:
    return re.compile(
        r"(?<!\w)" + re.escape(name)
        + r"(?!\w|\s+(?:Inc\.?|Incorporated|LLC|Ltd\.?|Corp\.?|Corporation)\b)",
        re.IGNORECASE,
    )


def _includes_entity(text: str, name: str) -> bool:
    return bool(_entity_pattern(name).search(text))


def _relation_is_asserted(quote: str, supplier: str, buyer: str) -> bool:
    """Require a narrow, directional supplier statement in the cited quotation.

    This is a precision-first rule, not general relation extraction. Unknown
    grammar should be reviewed rather than converted into a verified edge.
    """
    if NON_ASSERTIVE.search(quote):
        return False
    buyer_first = (
        _entity_pattern(buyer).pattern
        + r"[^.;!?]{0,100}\b(?:purchases?|buys?|sources?|procures?|obtains?|receives?)\b"
        + r"[^.;!?]{0,100}\bfrom\s+"
        + _entity_pattern(supplier).pattern
    )
    supplier_first = (
        _entity_pattern(supplier).pattern
        + r"[^.;!?]{0,100}\b(?:supplies|provides|delivers|sells)\b"
        + r"[^.;!?]{0,100}\bto\s+"
        + _entity_pattern(buyer).pattern
    )
    return bool(re.search(buyer_first, quote, re.IGNORECASE) or re.search(supplier_first, quote, re.IGNORECASE))


def _document_digest(document: dict[str, Any]) -> str:
    # A fingerprint of the input text, not independent verification of its origin.
    return hashlib.sha256(document["body"].encode("utf-8")).hexdigest()


def read_data(folder: Path = DATA_DIR) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Read the three fixture files without accessing the network."""
    loaded = []
    for filename in DATA_FILES:
        path = folder / filename
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            raise ValueError(f"{filename} must contain a list of JSON objects")
        loaded.append(value)
    return loaded[0], loaded[1], loaded[2]


def visible_documents(documents: list[dict[str, Any]], as_of: datetime) -> dict[str, dict[str, Any]]:
    """Validate fixture provenance before applying the historical availability cutoff."""
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("The historical cutoff must be timezone aware")
    visible: dict[str, dict[str, Any]] = {}
    ids: set[str] = set()
    for document in documents:
        if not isinstance(document, dict):
            raise ValueError("Each document must be an object")
        identifier = _required_string(document, "id", "document")
        if identifier in ids:
            raise ValueError(f"Duplicate document id: {identifier}")
        ids.add(identifier)
        for field in ("title", "url", "body", "data_kind"):
            _required_string(document, field, f"document {identifier}")
        if document["data_kind"] != "synthetic_example" or not document["url"].startswith("synthetic://"):
            raise ValueError(f"document {identifier}: this baseline accepts synthetic sources only")
        published = when(_required_string(document, "published_at", f"document {identifier}"))
        available = when(_required_string(document, "available_at", f"document {identifier}"))
        if published > available:
            raise ValueError(f"document {identifier}: available before publication")
        if available <= as_of:
            visible[identifier] = document
    return visible


def citation(document: dict[str, Any], quote: str) -> dict[str, Any] | None:
    """Return exact text offsets or abstain if the quote is absent or ambiguous."""
    if not isinstance(quote, str) or not quote.strip():
        return None
    body = document["body"]
    start = body.find(quote)
    if start < 0 or body.find(quote, start + 1) >= 0:
        return None
    return {
        "document_id": document["id"],
        "title": document["title"],
        "url": document["url"],
        "published_at": document["published_at"],
        "available_at": document["available_at"],
        "source_sha256": _document_digest(document),
        "quote": quote,
        "start": start,
        "end": start + len(quote),
        "data_kind": document["data_kind"],
    }


def event_sentences(document: dict[str, Any], subject: str) -> list[str]:
    """Find explicitly asserted supplier disruptions using a transparent rule baseline."""
    if not subject.strip():
        raise ValueError("The subject name cannot be empty")
    sentences = SENTENCE_BOUNDARY.split(document["body"].strip())
    return [
        sentence for sentence in sentences
        if _includes_entity(sentence, subject)
        and EVENT_VERBS.search(sentence)
        and not NON_ASSERTIVE.search(sentence)
    ]


def _holdings_by_id(portfolio: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    holdings: dict[str, dict[str, Any]] = {}
    for position in portfolio:
        if not isinstance(position, dict):
            raise ValueError("Each holding must be an object")
        identifier = _required_string(position, "company_id", "portfolio holding")
        for field in ("company_name", "ticker"):
            _required_string(position, field, f"holding {identifier}")
        shares = position.get("shares")
        if (isinstance(shares, bool) or not isinstance(shares, (int, float))
                or not math.isfinite(shares) or shares <= 0):
            raise ValueError(f"holding {identifier}: shares must be a positive number")
        if identifier in holdings:
            raise ValueError(f"Duplicate portfolio company id: {identifier}")
        holdings[identifier] = position
    return holdings


def _validate_relation(relation: dict[str, Any]) -> None:
    if not isinstance(relation, dict):
        raise ValueError("Each relationship must be an object")
    for field in ("supplier_id", "supplier_name", "buyer_id", "relation_type", "source_document_id", "source_quote"):
        _required_string(relation, field, "relationship")


def analyze(
    documents: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    portfolio: list[dict[str, Any]],
    as_of: str,
) -> dict[str, Any]:
    """Create source-quoted findings visible at the requested historical time.

    Every candidate link is checked for both named parties inside the cited
    quotation. The result is a research lead, not a causal or financial claim.
    """
    cutoff = when(as_of)
    source_by_id = visible_documents(documents, cutoff)
    holdings = _holdings_by_id(portfolio)
    findings: list[dict[str, Any]] = []
    emitted: set[tuple[str, str, str, str]] = set()
    rejected = 0

    for relation in relationships:
        _validate_relation(relation)
    ordered_relations = sorted(
        relationships,
        key=lambda r: (r["buyer_id"], r["supplier_id"], r["source_document_id"], r["source_quote"]),
    )
    for relation in ordered_relations:
        if relation["relation_type"] != "supplies" or relation["buyer_id"] not in holdings:
            continue
        source = source_by_id.get(relation["source_document_id"])
        if source is None:
            continue
        position = holdings[relation["buyer_id"]]
        quote = relation["source_quote"]
        # Exact presence is necessary but not sufficient: require the quoted
        # text to actually mention both endpoints of this declared relation.
        relation_citation = citation(source, quote)
        if (
            relation_citation is None
            or not _includes_entity(quote, relation["supplier_name"])
            or not _includes_entity(quote, position["company_name"])
            or not _relation_is_asserted(quote, relation["supplier_name"], position["company_name"])
        ):
            rejected += 1
            continue

        for document in (source_by_id[id_] for id_ in sorted(source_by_id)):
            if document["id"] == source["id"]:
                continue
            for sentence in event_sentences(document, relation["supplier_name"]):
                event_citation = citation(document, sentence)
                if event_citation is None:
                    rejected += 1
                    continue
                identity = (position["company_id"], relation["supplier_id"], document["id"], sentence)
                if identity in emitted:
                    continue
                emitted.add(identity)
                finding_id = hashlib.sha256("\x1f".join(identity).encode("utf-8")).hexdigest()[:20]
                findings.append({
                    "finding_id": finding_id,
                    "finding_type": "potential_indirect_exposure",
                    "portfolio_ticker": position["ticker"],
                    "portfolio_company": position["company_name"],
                    "exposure_path": [relation["supplier_name"], "supplies", position["company_name"]],
                    "event": sentence,
                    "evidence": {"event": event_citation, "relationship": relation_citation},
                    "assessment": "Possible indirect exposure. Real-world relevance and financial impact are unverified.",
                    "next_check": "Confirm whether the reported disruption affects the held company's deliveries.",
                })

    findings.sort(key=lambda finding: (finding["portfolio_ticker"], finding["finding_id"]))
    return {
        "as_of": cutoff.isoformat(),
        "mode": "offline_synthetic_research_baseline",
        "visible_document_count": len(source_by_id),
        "findings": findings,
        "rejected_unverifiable_relationships_or_events": rejected,
        "warning": "Synthetic data only. No forecasts, trading recommendations or causal claims.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline, evidence-backed portfolio research prototype")
    parser.add_argument("--as-of", default="2026-02-12T12:00:00Z", help="ISO-8601 timestamp with UTC offset")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    try:
        documents, relations, holdings = read_data(args.data_dir)
        result = analyze(documents, relations, holdings, args.as_of)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
