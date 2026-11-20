"""Reproducible synthetic sentence-level checks for the event rule baseline.

These fixtures detect regressions. They cannot establish accuracy on real filings.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prototype import event_sentences

CASES = Path(__file__).resolve().parent / "data" / "sentence_cases.json"


def evaluate(path: Path = CASES) -> dict[str, object]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("The synthetic evaluation dataset must contain at least one case")
    tp = fp = tn = fn = 0
    failures: list[dict[str, object]] = []
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "subject", "sentence", "expected"}:
            raise ValueError("Each case must have id, subject, sentence and expected")
        if not all(isinstance(case[key], str) and case[key] for key in ("id", "subject", "sentence")):
            raise ValueError("Case id, subject and sentence must be nonempty strings")
        if type(case["expected"]) is not bool or case["id"] in seen:
            raise ValueError("Case labels must be boolean and case ids must be unique")
        seen.add(case["id"])
        observed = bool(event_sentences({"body": case["sentence"]}, case["subject"]))
        expected = case["expected"]
        if observed and expected:
            tp += 1
        elif observed:
            fp += 1
        elif expected:
            fn += 1
        else:
            tn += 1
        if observed != expected:
            failures.append({"id": case["id"], "expected": expected, "observed": observed})
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {
        "dataset": "synthetic_sentence_regression_cases",
        "total_cases": len(cases),
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision_on_synthetic_cases": precision,
        "recall_on_synthetic_cases": recall,
        "failures": failures,
        "warning": "Synthetic hand-authored cases are regression checks, not evidence of real-world model performance.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the deterministic baseline against synthetic cases")
    parser.add_argument("--cases", type=Path, default=CASES)
    arguments = parser.parse_args()
    result = evaluate(arguments.cases)
    print(json.dumps(result, indent=2))
    if result["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
